# app/services/data_merge_strategy.py
"""
Data Merge Strategy Service - Handles RFID API + POS data integration
Ensures RFID API takes precedence while preserving POS financial data
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
from sqlalchemy import text
from .. import db
from ..models.db_models import ItemMaster
from ..models.pos_models import POSEquipment
from .logger import get_logger

logger = get_logger("data_merge_strategy", level=logging.INFO)

class DataMergeStrategy:
    """
    Manages the complex merge between RFID API data (source of truth for tracking)
    and POS data (source of truth for financial/operational data)
    """
    
    def __init__(self):
        self.session = db.session
        
        # RFID API takes precedence for these fields
        self.RFID_AUTHORITY_FIELDS = [
            'tag_id', 'serial_number', 'rental_class_num', 'client_name',
            'common_name', 'quality', 'bin_location', 'status', 
            'last_contract_num', 'last_scanned_by', 'notes', 'status_notes',
            'longitude', 'latitude', 'date_last_scanned', 'date_created', 
            'date_updated', 'current_store', 'home_store'
        ]
        
        # POS takes precedence for these fields
        self.POS_AUTHORITY_FIELDS = [
            'turnover_ytd', 'turnover_ltd', 'repair_cost_ltd', 'sell_price',
            'retail_price', 'manufacturer', 'type_desc', 'department',
            'rental_rates', 'vendor_ids'
        ]
        
        # Fields that require conflict resolution
        self.CONFLICT_FIELDS = [
            'item_num',  # Both systems have this
            'identifier_type'  # Can change over time
        ]
    
    def merge_item_data(self, rfid_data: Dict, pos_data: Dict) -> Dict:
        """
        Merge RFID API data with POS data using authority rules
        
        Args:
            rfid_data: Data from RFID Pro API
            pos_data: Data from POS equipment CSV
            
        Returns:
            Merged data dictionary with conflict resolution
        """
        merged = {}
        
        # RFID fields take precedence
        for field in self.RFID_AUTHORITY_FIELDS:
            if field in rfid_data and rfid_data[field] is not None:
                merged[field] = rfid_data[field]
        
        # POS fields take precedence  
        for field in self.POS_AUTHORITY_FIELDS:
            if field in pos_data and pos_data[field] is not None:
                merged[field] = pos_data[field]
        
        # Handle conflict fields with business logic
        merged.update(self._resolve_conflicts(rfid_data, pos_data))
        
        # Add merge metadata
        merged['data_source'] = 'merged'
        merged['rfid_last_updated'] = rfid_data.get('date_updated')
        merged['pos_last_updated'] = pos_data.get('last_updated')
        merged['merge_timestamp'] = datetime.now()
        
        return merged
    
    def _resolve_conflicts(self, rfid_data: Dict, pos_data: Dict) -> Dict:
        """Resolve conflicts between RFID and POS data using business rules"""
        resolved = {}
        
        # item_num conflict resolution: RFID API wins if present
        if rfid_data.get('item_num'):
            resolved['item_num'] = rfid_data['item_num']
        elif pos_data.get('item_num'):
            resolved['item_num'] = pos_data['item_num']
        
        # identifier_type transition logic
        resolved['identifier_type'] = self._resolve_identifier_type(rfid_data, pos_data)
        
        return resolved
    
    def _resolve_identifier_type(self, rfid_data: Dict, pos_data: Dict) -> str:
        """
        Resolve identifier type with transition support:
        - Sticker → RFID (when tag_id appears)
        - Bulk → Sticker (when serializing) 
        - Bulk → RFID (direct transition)
        """
        # If RFID has tag_id, it's definitely RFID
        if rfid_data.get('tag_id') and len(str(rfid_data['tag_id'])) == 24:
            return 'RFID'
        
        # If POS has serial number but no RFID tag, it's Sticker
        if pos_data.get('serial_no') and not rfid_data.get('tag_id'):
            return 'Sticker'
        
        # If neither has individual tracking, it's Bulk
        if not rfid_data.get('tag_id') and not pos_data.get('serial_no'):
            return 'Bulk'
        
        # Default to existing or None
        return rfid_data.get('identifier_type') or pos_data.get('identifier_type') or 'None'
    
    def identify_duplicates(self) -> List[Dict]:
        """
        Identify items that exist in both RFID and POS systems
        Returns list of duplicate pairs with match confidence
        """
        duplicates = []
        
        # Query for items with same item_num in both systems
        query = text("""
            SELECT 
                im.tag_id as rfid_tag_id,
                im.item_num as rfid_item_num,
                im.common_name as rfid_name,
                im.serial_number as rfid_serial,
                pe.id as pos_id,
                pe.item_num as pos_item_num, 
                pe.name as pos_name,
                pe.serial_no as pos_serial,
                CASE 
                    WHEN im.item_num = pe.item_num AND COALESCE(im.serial_number, '') = COALESCE(pe.serial_no, '') THEN 0.95
                    WHEN im.item_num = pe.item_num THEN 0.80
                    WHEN COALESCE(im.serial_number, '') = COALESCE(pe.serial_no, '') AND LENGTH(COALESCE(im.serial_number, '')) > 0 THEN 0.75
                    ELSE 0.50
                END as match_confidence
            FROM id_item_master im
            INNER JOIN pos_equipment pe ON (
                im.item_num = pe.item_num OR
                (COALESCE(im.serial_number, '') = COALESCE(pe.serial_no, '') AND LENGTH(COALESCE(im.serial_number, '')) > 0)
            )
            WHERE im.item_num IS NOT NULL
            ORDER BY match_confidence DESC
        """)
        
        results = self.session.execute(query).fetchall()
        
        for row in results:
            duplicates.append({
                'rfid_tag_id': row[0],
                'rfid_item_num': row[1], 
                'rfid_name': row[2],
                'rfid_serial': row[3],
                'pos_id': row[4],
                'pos_item_num': row[5],
                'pos_name': row[6], 
                'pos_serial': row[7],
                'match_confidence': float(row[8]),
                'recommended_action': self._recommend_action(float(row[8]))
            })
        
        logger.info(f"Identified {len(duplicates)} potential duplicates")
        return duplicates
    
    def _recommend_action(self, confidence: float) -> str:
        """Recommend action based on match confidence"""
        if confidence >= 0.90:
            return "AUTO_MERGE"
        elif confidence >= 0.75:
            return "REVIEW_MERGE"  
        elif confidence >= 0.60:
            return "MANUAL_REVIEW"
        else:
            return "KEEP_SEPARATE"
    
    def create_identifier_transition_record(self, tag_id: str, 
                                          old_type: str, new_type: str, 
                                          reason: str) -> bool:
        """
        Record identifier type transitions for audit trail
        
        Args:
            tag_id: Item tag ID
            old_type: Previous identifier type
            new_type: New identifier type  
            reason: Reason for transition
        """
        try:
            transition_query = text("""
                INSERT INTO identifier_transitions 
                (tag_id, old_type, new_type, transition_reason, transition_date)
                VALUES (:tag_id, :old_type, :new_type, :reason, NOW())
            """)
            
            # Create table if it doesn't exist
            create_table_query = text("""
                CREATE TABLE IF NOT EXISTS identifier_transitions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tag_id VARCHAR(255) NOT NULL,
                    old_type VARCHAR(50) NOT NULL,
                    new_type VARCHAR(50) NOT NULL, 
                    transition_reason TEXT,
                    transition_date DATETIME NOT NULL,
                    INDEX idx_tag_id (tag_id),
                    INDEX idx_transition_date (transition_date)
                )
            """)
            
            self.session.execute(create_table_query)
            self.session.execute(transition_query, {
                'tag_id': tag_id,
                'old_type': old_type,
                'new_type': new_type,
                'reason': reason
            })
            self.session.commit()
            
            logger.info(f"Recorded transition: {tag_id} {old_type} → {new_type} ({reason})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record transition for {tag_id}: {e}")
            self.session.rollback()
            return False
    
    def clean_contaminated_pos_data(self) -> Dict[str, int]:
        """
        Clean contaminated POS data from current database
        
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            # Count contaminated records before cleanup
            contamination_query = text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN category = 'UNUSED' THEN 1 END) as unused,
                    COUNT(CASE WHEN category = 'NON CURRENT ITEMS' THEN 1 END) as non_current,
                    COUNT(CASE WHEN inactive = 1 THEN 1 END) as inactive
                FROM pos_equipment
            """)
            
            before_stats = self.session.execute(contamination_query).fetchone()
            
            # Create backup table before cleanup
            backup_query = text("""
                CREATE TABLE IF NOT EXISTS pos_equipment_contaminated_backup AS
                SELECT * FROM pos_equipment 
                WHERE category IN ('UNUSED', 'NON CURRENT ITEMS') OR inactive = 1
            """)
            self.session.execute(backup_query)
            
            # Clean contaminated data
            cleanup_query = text("""
                DELETE FROM pos_equipment 
                WHERE category IN ('UNUSED', 'NON CURRENT ITEMS') OR inactive = 1
            """)
            
            result = self.session.execute(cleanup_query)
            deleted_count = result.rowcount
            
            self.session.commit()
            
            cleanup_stats = {
                'total_before': before_stats[0],
                'unused_removed': before_stats[1], 
                'non_current_removed': before_stats[2],
                'inactive_removed': before_stats[3],
                'total_deleted': deleted_count,
                'cleanup_date': datetime.now()
            }
            
            logger.info(f"POS cleanup completed: {deleted_count} contaminated records removed")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"POS cleanup failed: {e}")
            self.session.rollback()
            return {'error': str(e)}


# Global instance
_merge_strategy = None

def get_merge_strategy() -> DataMergeStrategy:
    """Get singleton instance of DataMergeStrategy"""
    global _merge_strategy
    if _merge_strategy is None:
        _merge_strategy = DataMergeStrategy()
    return _merge_strategy