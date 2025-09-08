"""
Data Validation and Conflict Resolution Service
Handles data quality, validation, and conflict resolution between systems
"""

import re
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal
import difflib
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging

class DataValidationService:
    """Service for data validation and conflict resolution"""
    
    def __init__(self, db_connection, logger=None):
        """
        Initialize Data Validation Service
        
        Args:
            db_connection: SQLAlchemy database connection
            logger: Optional logger instance
        """
        self.db = db_connection
        self.logger = logger or logging.getLogger(__name__)
        
        # Validation rules
        self.validation_rules = {
            'rfid_tag': {
                'pattern': r'^[A-F0-9]{24}$',
                'length': 24,
                'type': 'hex'
            },
            'pos_item_num': {
                'pattern': r'^[A-Z0-9\-]+$',
                'min_length': 3,
                'max_length': 50
            },
            'quantity': {
                'min': 0,
                'max': 999999
            },
            'confidence_score': {
                'min': 0.0,
                'max': 1.0
            }
        }
        
        # Common name variations to handle
        self.name_variations = {
            'table': ['tbl', 'tables'],
            'chair': ['chr', 'chairs', 'seat', 'seats'],
            'linen': ['linens', 'cloth', 'fabric'],
            'tent': ['tents', 'canopy', 'marquee'],
            'round': ['rnd', 'circular'],
            'white': ['wht', 'ivory', 'cream']
        }
    
    def validate_rfid_tag(self, tag_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate RFID tag format
        
        Args:
            tag_id: RFID tag identifier
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not tag_id:
            return False, "RFID tag is required"
        
        # Check pattern
        rule = self.validation_rules['rfid_tag']
        if not re.match(rule['pattern'], tag_id.upper()):
            return False, f"Invalid RFID format. Expected {rule['length']} hex characters"
        
        # Check if exists in database
        try:
            with self.db.begin() as conn:
                exists = conn.execute(text("""
                    SELECT 1 FROM id_item_master 
                    WHERE tag_id = :tag_id
                """), {'tag_id': tag_id}).fetchone()
                
                if not exists:
                    return True, "Valid format but not in database"
                    
        except SQLAlchemyError as e:
            self.logger.error(f"Database error validating RFID: {str(e)}")
            return False, f"Database error: {str(e)}"
        
        return True, None
    
    def validate_pos_item(self, item_num: str) -> Tuple[bool, Optional[str]]:
        """
        Validate POS item number format
        
        Args:
            item_num: POS item number
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not item_num:
            return False, "POS item number is required"
        
        rule = self.validation_rules['pos_item_num']
        
        # Check length
        if len(item_num) < rule.get('min_length', 1):
            return False, f"Item number too short (min {rule['min_length']})"
        
        if len(item_num) > rule.get('max_length', 100):
            return False, f"Item number too long (max {rule['max_length']})"
        
        # Check pattern if specified
        if 'pattern' in rule and not re.match(rule['pattern'], item_num):
            return False, "Invalid item number format"
        
        return True, None
    
    def detect_conflicts(self, correlation_id: int) -> List[Dict[str, Any]]:
        """
        Detect conflicts between RFID and POS data for a correlation
        
        Args:
            correlation_id: Correlation record ID
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        try:
            with self.db.begin() as conn:
                # Get correlation data
                corr = conn.execute(text("""
                    SELECT 
                        icm.*,
                        im.common_name as rfid_name,
                        im.status as rfid_status,
                        im.quality as rfid_quality,
                        pds.name as pos_name,
                        pds.quantity as pos_quantity,
                        pds.turnover_ytd as pos_revenue
                    FROM inventory_correlation_master icm
                    LEFT JOIN id_item_master im ON icm.rfid_tag_id = im.tag_id
                    LEFT JOIN pos_data_staging pds ON icm.correlation_id = pds.correlation_id
                    WHERE icm.correlation_id = :corr_id
                """), {'corr_id': correlation_id}).fetchone()
                
                if not corr:
                    return conflicts
                
                # Check name conflicts
                if corr.rfid_name and corr.pos_name:
                    similarity = self.calculate_name_similarity(corr.rfid_name, corr.pos_name)
                    if similarity < 0.7:  # Less than 70% similar
                        conflicts.append({
                            'type': 'NAME_MISMATCH',
                            'field': 'common_name',
                            'rfid_value': corr.rfid_name,
                            'pos_value': corr.pos_name,
                            'similarity': similarity,
                            'severity': 'MEDIUM' if similarity > 0.5 else 'HIGH'
                        })
                
                # Check quantity conflicts for bulk items
                if corr.is_bulk_item and corr.bulk_quantity_on_hand and corr.pos_quantity:
                    qty_diff = abs(float(corr.bulk_quantity_on_hand) - float(corr.pos_quantity))
                    if qty_diff > 5:  # More than 5 units difference
                        conflicts.append({
                            'type': 'QUANTITY_MISMATCH',
                            'field': 'quantity',
                            'rfid_value': float(corr.bulk_quantity_on_hand),
                            'pos_value': float(corr.pos_quantity),
                            'difference': qty_diff,
                            'severity': 'HIGH' if qty_diff > 20 else 'MEDIUM'
                        })
                
                # Check status conflicts
                if corr.rfid_status and corr.rfid_status != 'Ready to Rent':
                    conflicts.append({
                        'type': 'STATUS_CONFLICT',
                        'field': 'status',
                        'rfid_value': corr.rfid_status,
                        'severity': 'LOW' if corr.rfid_status in ['In Repair', 'Needs Cleaning'] else 'HIGH'
                    })
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error detecting conflicts: {str(e)}")
            conflicts.append({
                'type': 'ERROR',
                'message': str(e),
                'severity': 'CRITICAL'
            })
        
        return conflicts
    
    def resolve_conflict(self, correlation_id: int, conflict: Dict[str, Any], 
                        resolution: str, user: str = 'SYSTEM') -> bool:
        """
        Resolve a data conflict
        
        Args:
            correlation_id: Correlation record ID
            conflict: Conflict details
            resolution: Resolution method (USE_RFID, USE_POS, MANUAL, IGNORE)
            user: User performing resolution
            
        Returns:
            Success status
        """
        try:
            with self.db.begin() as conn:
                if resolution == 'USE_RFID':
                    # Update correlation with RFID values
                    conn.execute(text("""
                        UPDATE inventory_correlation_master icm
                        JOIN id_item_master im ON icm.rfid_tag_id = im.tag_id
                        SET 
                            icm.common_name = im.common_name,
                            icm.confidence_score = 0.90,
                            icm.last_verified_date = NOW(),
                            icm.verification_source = 'RFID_PREFERRED',
                            icm.updated_by = :user
                        WHERE icm.correlation_id = :corr_id
                    """), {'corr_id': correlation_id, 'user': user})
                    
                elif resolution == 'USE_POS':
                    # Update correlation with POS values
                    conn.execute(text("""
                        UPDATE inventory_correlation_master icm
                        JOIN pos_data_staging pds ON icm.correlation_id = pds.correlation_id
                        SET 
                            icm.common_name = pds.name,
                            icm.bulk_quantity_on_hand = pds.quantity,
                            icm.confidence_score = 0.85,
                            icm.last_verified_date = NOW(),
                            icm.verification_source = 'POS_PREFERRED',
                            icm.updated_by = :user
                        WHERE icm.correlation_id = :corr_id
                    """), {'corr_id': correlation_id, 'user': user})
                
                elif resolution == 'IGNORE':
                    # Mark as reviewed but don't change
                    conn.execute(text("""
                        UPDATE inventory_correlation_master
                        SET 
                            confidence_score = confidence_score * 0.95,
                            last_verified_date = NOW(),
                            verification_source = 'CONFLICT_IGNORED',
                            updated_by = :user
                        WHERE correlation_id = :corr_id
                    """), {'corr_id': correlation_id, 'user': user})
                
                # Log resolution in quality metrics
                conn.execute(text("""
                    INSERT INTO data_quality_metrics (
                        correlation_id, issue_type, severity,
                        source_system, field_name,
                        resolution_status, resolution_method,
                        resolved_date, resolved_by
                    ) VALUES (
                        :corr_id, :issue_type, :severity,
                        :source, :field,
                        'RESOLVED', :method,
                        NOW(), :user
                    )
                """), {
                    'corr_id': correlation_id,
                    'issue_type': conflict.get('type', 'UNKNOWN'),
                    'severity': conflict.get('severity', 'MEDIUM'),
                    'source': 'CORRELATION',
                    'field': conflict.get('field', ''),
                    'method': resolution,
                    'user': user
                })
                
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error resolving conflict: {str(e)}")
            return False
    
    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two item names
        
        Args:
            name1: First name
            name2: Second name
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not name1 or not name2:
            return 0.0
        
        # Normalize names
        name1 = self.normalize_name(name1)
        name2 = self.normalize_name(name2)
        
        # Direct match
        if name1 == name2:
            return 1.0
        
        # Use difflib for similarity
        return difflib.SequenceMatcher(None, name1, name2).ratio()
    
    def normalize_name(self, name: str) -> str:
        """
        Normalize item name for comparison
        
        Args:
            name: Original name
            
        Returns:
            Normalized name
        """
        if not name:
            return ""
        
        # Convert to lowercase
        name = name.lower().strip()
        
        # Remove special characters
        name = re.sub(r'[^\w\s]', ' ', name)
        
        # Replace common variations
        for standard, variations in self.name_variations.items():
            for variant in variations:
                name = name.replace(variant, standard)
        
        # Remove extra spaces
        name = ' '.join(name.split())
        
        return name
    
    def validate_bulk_data(self, batch_id: str) -> Dict[str, Any]:
        """
        Validate an entire batch of imported data
        
        Args:
            batch_id: Import batch ID
            
        Returns:
            Validation results
        """
        results = {
            'batch_id': batch_id,
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'warnings': [],
            'errors': []
        }
        
        try:
            with self.db.begin() as conn:
                # Get all records for batch
                records = conn.execute(text("""
                    SELECT * FROM pos_data_staging
                    WHERE import_batch_id = :batch_id
                """), {'batch_id': batch_id}).fetchall()
                
                results['total_records'] = len(records)
                
                for record in records:
                    is_valid = True
                    record_warnings = []
                    record_errors = []
                    
                    # Validate item number
                    if record.item_num:
                        valid, msg = self.validate_pos_item(record.item_num)
                        if not valid:
                            record_errors.append(f"Item {record.item_num}: {msg}")
                            is_valid = False
                    
                    # Validate quantities
                    if record.quantity:
                        if float(record.quantity) < 0:
                            record_errors.append(f"Negative quantity: {record.quantity}")
                            is_valid = False
                        elif float(record.quantity) > 10000:
                            record_warnings.append(f"Unusually high quantity: {record.quantity}")
                    
                    # Check for missing critical fields
                    if not record.name:
                        record_errors.append("Missing item name")
                        is_valid = False
                    
                    # Update record status
                    if not is_valid:
                        conn.execute(text("""
                            UPDATE pos_data_staging
                            SET processing_status = 'ERROR',
                                error_message = :error
                            WHERE staging_id = :id
                        """), {
                            'id': record.staging_id,
                            'error': '; '.join(record_errors)
                        })
                        results['invalid_records'] += 1
                    else:
                        results['valid_records'] += 1
                    
                    results['warnings'].extend(record_warnings)
                    results['errors'].extend(record_errors)
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error validating batch: {str(e)}")
            results['errors'].append(f"Database error: {str(e)}")
        
        return results
    
    def detect_duplicates(self) -> List[Dict[str, Any]]:
        """
        Detect duplicate items across systems
        
        Returns:
            List of duplicate groups
        """
        duplicates = []
        
        try:
            with self.db.begin() as conn:
                # Find RFID duplicates (same tag in multiple correlations)
                rfid_dups = conn.execute(text("""
                    SELECT 
                        rfid_tag_id,
                        COUNT(*) as count,
                        GROUP_CONCAT(correlation_id) as correlation_ids
                    FROM inventory_correlation_master
                    WHERE rfid_tag_id IS NOT NULL
                    GROUP BY rfid_tag_id
                    HAVING COUNT(*) > 1
                """)).fetchall()
                
                for dup in rfid_dups:
                    duplicates.append({
                        'type': 'RFID_DUPLICATE',
                        'identifier': dup.rfid_tag_id,
                        'count': dup.count,
                        'correlation_ids': dup.correlation_ids.split(','),
                        'severity': 'HIGH'
                    })
                
                # Find POS duplicates
                pos_dups = conn.execute(text("""
                    SELECT 
                        pos_item_num,
                        COUNT(*) as count,
                        GROUP_CONCAT(correlation_id) as correlation_ids
                    FROM inventory_correlation_master
                    WHERE pos_item_num IS NOT NULL
                        AND tracking_type != 'BULK'
                    GROUP BY pos_item_num
                    HAVING COUNT(*) > 1
                """)).fetchall()
                
                for dup in pos_dups:
                    duplicates.append({
                        'type': 'POS_DUPLICATE',
                        'identifier': dup.pos_item_num,
                        'count': dup.count,
                        'correlation_ids': dup.correlation_ids.split(','),
                        'severity': 'MEDIUM'
                    })
                
                # Find name duplicates (fuzzy matching)
                name_dups = conn.execute(text("""
                    SELECT 
                        a.correlation_id as id1,
                        b.correlation_id as id2,
                        a.common_name as name1,
                        b.common_name as name2
                    FROM inventory_correlation_master a
                    JOIN inventory_correlation_master b ON 
                        a.correlation_id < b.correlation_id
                        AND SOUNDEX(a.common_name) = SOUNDEX(b.common_name)
                        AND a.common_name != b.common_name
                """)).fetchall()
                
                for dup in name_dups:
                    similarity = self.calculate_name_similarity(dup.name1, dup.name2)
                    if similarity > 0.85:  # High similarity
                        duplicates.append({
                            'type': 'NAME_SIMILAR',
                            'correlation_ids': [dup.id1, dup.id2],
                            'names': [dup.name1, dup.name2],
                            'similarity': similarity,
                            'severity': 'LOW'
                        })
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error detecting duplicates: {str(e)}")
        
        return duplicates
    
    def merge_duplicates(self, correlation_ids: List[int], 
                        master_id: int = None) -> bool:
        """
        Merge duplicate correlations into one
        
        Args:
            correlation_ids: List of correlation IDs to merge
            master_id: ID to use as master (or first in list)
            
        Returns:
            Success status
        """
        if len(correlation_ids) < 2:
            return False
        
        if not master_id:
            master_id = correlation_ids[0]
        
        if master_id not in correlation_ids:
            return False
        
        try:
            with self.db.begin() as conn:
                # Get all data from correlations
                correlations = conn.execute(text("""
                    SELECT * FROM inventory_correlation_master
                    WHERE correlation_id IN :ids
                """), {'ids': tuple(correlation_ids)}).fetchall()
                
                # Merge data into master
                for corr in correlations:
                    if corr.correlation_id == master_id:
                        continue
                    
                    # Update master with non-null values from duplicate
                    update_fields = []
                    params = {'master_id': master_id, 'dup_id': corr.correlation_id}
                    
                    if corr.rfid_tag_id and not correlations[0].rfid_tag_id:
                        update_fields.append("rfid_tag_id = :rfid_tag")
                        params['rfid_tag'] = corr.rfid_tag_id
                    
                    if corr.pos_item_num and not correlations[0].pos_item_num:
                        update_fields.append("pos_item_num = :pos_num")
                        params['pos_num'] = corr.pos_item_num
                    
                    if update_fields:
                        query = f"""
                            UPDATE inventory_correlation_master
                            SET {', '.join(update_fields)},
                                confidence_score = confidence_score * 0.95,
                                updated_by = 'MERGE_OPERATION'
                            WHERE correlation_id = :master_id
                        """
                        conn.execute(text(query), params)
                    
                    # Update references to point to master
                    conn.execute(text("""
                        UPDATE pos_data_staging
                        SET correlation_id = :master_id
                        WHERE correlation_id = :dup_id
                    """), {'master_id': master_id, 'dup_id': corr.correlation_id})
                    
                    # Delete duplicate
                    conn.execute(text("""
                        DELETE FROM inventory_correlation_master
                        WHERE correlation_id = :dup_id
                    """), {'dup_id': corr.correlation_id})
                
                # Log merge operation
                conn.execute(text("""
                    INSERT INTO correlation_audit_log (
                        table_name, record_id, action,
                        new_values, changed_by, change_source
                    ) VALUES (
                        'inventory_correlation_master',
                        :master_id,
                        'MERGE',
                        :details,
                        'SYSTEM',
                        'DUPLICATE_MERGE'
                    )
                """), {
                    'master_id': master_id,
                    'details': f'{{"merged_ids": {correlation_ids}, "kept_id": {master_id}}}'
                })
                
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error merging duplicates: {str(e)}")
            return False
    
    def calculate_confidence_score(self, correlation_id: int) -> float:
        """
        Calculate confidence score for a correlation based on data quality
        
        Args:
            correlation_id: Correlation record ID
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        score = 1.0
        
        try:
            with self.db.begin() as conn:
                # Get correlation data
                corr = conn.execute(text("""
                    SELECT 
                        icm.*,
                        COUNT(DISTINCT rpm.mapping_id) as mapping_count,
                        COUNT(DISTINCT dqm.metric_id) as issue_count
                    FROM inventory_correlation_master icm
                    LEFT JOIN rfid_pos_mapping rpm ON icm.correlation_id = rpm.correlation_id
                    LEFT JOIN data_quality_metrics dqm ON 
                        icm.correlation_id = dqm.correlation_id 
                        AND dqm.resolution_status = 'OPEN'
                    WHERE icm.correlation_id = :corr_id
                    GROUP BY icm.correlation_id
                """), {'corr_id': correlation_id}).fetchone()
                
                if not corr:
                    return 0.0
                
                # Reduce score for missing data
                if not corr.rfid_tag_id:
                    score -= 0.2
                if not corr.pos_item_num:
                    score -= 0.1
                if not corr.common_name:
                    score -= 0.15
                
                # Reduce score for quality issues
                if corr.issue_count > 0:
                    score -= (0.05 * min(corr.issue_count, 5))
                
                # Increase score for validated mappings
                if corr.mapping_count > 0:
                    score += 0.1
                
                # Reduce score for old data
                if corr.last_verified_date:
                    days_old = (datetime.now() - corr.last_verified_date).days
                    if days_old > 90:
                        score -= 0.1
                    elif days_old > 30:
                        score -= 0.05
                
                # Ensure score is within bounds
                score = max(0.0, min(1.0, score))
                
                # Update the score in database
                conn.execute(text("""
                    UPDATE inventory_correlation_master
                    SET confidence_score = :score
                    WHERE correlation_id = :corr_id
                """), {'score': score, 'corr_id': correlation_id})
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error calculating confidence score: {str(e)}")
            score = 0.5
        
        return score