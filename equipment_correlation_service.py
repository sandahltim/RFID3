#!/usr/bin/env python3
"""
Equipment Correlation Service for RFID3
Created: 2025-09-02
Purpose: Establish and manage correlations between POS equipment and RFID tracking systems
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import logging
from difflib import SequenceMatcher
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EquipmentCorrelationService:
    """Service to manage equipment-RFID correlations"""
    
    def __init__(self, db_config: Dict):
        """Initialize the correlation service"""
        self.db_config = db_config
        self.engine = self._create_engine()
        self.Session = sessionmaker(bind=self.engine)
        
    def _create_engine(self):
        """Create database engine"""
        conn_string = (
            f"mysql+pymysql://{self.db_config['user']}:{self.db_config['password']}"
            f"@{self.db_config['host']}/{self.db_config['database']}"
            f"?charset={self.db_config.get('charset', 'utf8mb4')}"
        )
        return create_engine(conn_string, pool_pre_ping=True)
    
    def analyze_correlation_potential(self) -> Dict:
        """Analyze the potential for correlations in the current data"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'statistics': {},
            'recommendations': [],
            'sample_correlations': []
        }
        
        with self.engine.connect() as conn:
            # Get basic statistics
            stats_query = """
            SELECT 
                'equipment_items' as table_name,
                COUNT(*) as total_records,
                COUNT(DISTINCT item_num) as unique_items,
                SUM(CASE WHEN rfid_rental_class_num IS NOT NULL THEN 1 ELSE 0 END) as correlated
            FROM equipment_items
            UNION ALL
            SELECT 
                'id_item_master',
                COUNT(*),
                COUNT(DISTINCT rental_class_num),
                COUNT(DISTINCT rental_class_num)
            FROM id_item_master
            WHERE rental_class_num IS NOT NULL
            UNION ALL
            SELECT 
                'pos_transaction_items',
                COUNT(*),
                COUNT(DISTINCT item_num),
                0
            FROM pos_transaction_items
            WHERE item_num IS NOT NULL
            """
            
            result = conn.execute(text(stats_query))
            for row in result:
                analysis['statistics'][row[0]] = {
                    'total_records': row[1],
                    'unique_items': row[2],
                    'correlated': row[3]
                }
            
            # Calculate correlation rate
            equip_stats = analysis['statistics'].get('equipment_items', {})
            if equip_stats.get('total_records', 0) > 0:
                correlation_rate = (equip_stats.get('correlated', 0) / 
                                  equip_stats.get('total_records', 1)) * 100
                analysis['correlation_rate'] = round(correlation_rate, 2)
            
        return analysis
    
    def normalize_item_number(self, item_num: str) -> str:
        """Normalize item number format"""
        if not item_num:
            return ''
        
        # Remove .0 suffix
        normalized = str(item_num).strip()
        if normalized.endswith('.0'):
            normalized = normalized[:-2]
        
        # Remove leading zeros
        try:
            return str(int(float(normalized)))
        except (ValueError, TypeError):
            return normalized
    
    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names"""
        if not name1 or not name2:
            return 0.0
        
        # Normalize strings
        n1 = re.sub(r'[^a-zA-Z0-9\s]', '', str(name1).upper())
        n2 = re.sub(r'[^a-zA-Z0-9\s]', '', str(name2).upper())
        
        # Exact match
        if n1 == n2:
            return 1.0
        
        # Contains match
        if n1 in n2 or n2 in n1:
            return 0.8
        
        # Sequence matching
        return SequenceMatcher(None, n1, n2).ratio()
    
    def find_correlations_by_name(self, limit: int = 100) -> List[Dict]:
        """Find potential correlations based on name similarity"""
        correlations = []
        
        query = """
        SELECT 
            e.item_num,
            e.name as equipment_name,
            i.rental_class_num,
            i.common_name as rfid_name,
            COUNT(DISTINCT i.tag_id) as tag_count
        FROM equipment_items e
        CROSS JOIN (
            SELECT DISTINCT rental_class_num, common_name, tag_id
            FROM id_item_master
            WHERE rental_class_num IS NOT NULL
            AND common_name IS NOT NULL
        ) i
        WHERE e.rfid_rental_class_num IS NULL
        AND e.name IS NOT NULL
        GROUP BY e.item_num, e.name, i.rental_class_num, i.common_name
        LIMIT :limit
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'limit': limit * 10})
            
            for row in result:
                similarity = self.calculate_name_similarity(row[1], row[3])
                if similarity >= 0.6:  # Minimum threshold
                    correlations.append({
                        'pos_item_num': row[0],
                        'pos_name': row[1],
                        'rfid_rental_class': row[2],
                        'rfid_name': row[3],
                        'tag_count': row[4],
                        'similarity_score': round(similarity, 3),
                        'correlation_type': 'name_match'
                    })
            
        # Sort by similarity score
        correlations.sort(key=lambda x: x['similarity_score'], reverse=True)
        return correlations[:limit]
    
    def find_correlations_by_number(self) -> List[Dict]:
        """Find exact numeric correlations"""
        correlations = []
        
        query = """
        SELECT DISTINCT
            e.item_num,
            e.name as equipment_name,
            i.rental_class_num,
            i.common_name as rfid_name,
            i.tag_count
        FROM equipment_items e
        INNER JOIN (
            SELECT 
                rental_class_num,
                MAX(common_name) as common_name,
                COUNT(DISTINCT tag_id) as tag_count
            FROM id_item_master
            WHERE rental_class_num IS NOT NULL
            GROUP BY rental_class_num
        ) i ON e.item_num = i.rental_class_num
        WHERE e.rfid_rental_class_num IS NULL
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            
            for row in result:
                correlations.append({
                    'pos_item_num': row[0],
                    'pos_name': row[1],
                    'rfid_rental_class': row[2],
                    'rfid_name': row[3],
                    'tag_count': row[4],
                    'similarity_score': 1.0,
                    'correlation_type': 'exact_number'
                })
        
        return correlations
    
    def apply_correlations(self, correlations: List[Dict], 
                          min_confidence: float = 0.8) -> Dict:
        """Apply correlations to the database"""
        results = {
            'applied': 0,
            'skipped': 0,
            'errors': [],
            'details': []
        }
        
        with self.engine.begin() as conn:
            for corr in correlations:
                if corr['similarity_score'] < min_confidence:
                    results['skipped'] += 1
                    continue
                
                try:
                    # Insert into mapping table
                    insert_mapping = """
                    INSERT INTO equipment_rfid_mapping (
                        pos_item_num,
                        rfid_rental_class_num,
                        mapping_type,
                        confidence_score,
                        match_details,
                        created_at
                    ) VALUES (
                        :pos_item,
                        :rfid_class,
                        :map_type,
                        :confidence,
                        :details,
                        NOW()
                    )
                    ON DUPLICATE KEY UPDATE
                        confidence_score = VALUES(confidence_score),
                        match_details = VALUES(match_details)
                    """
                    
                    conn.execute(text(insert_mapping), {
                        'pos_item': corr['pos_item_num'],
                        'rfid_class': corr['rfid_rental_class'],
                        'map_type': corr['correlation_type'],
                        'confidence': corr['similarity_score'],
                        'details': json.dumps({
                            'pos_name': corr['pos_name'],
                            'rfid_name': corr['rfid_name'],
                            'tag_count': corr.get('tag_count', 0)
                        })
                    })
                    
                    # Update equipment_items if high confidence
                    if corr['similarity_score'] >= 0.9:
                        update_equipment = """
                        UPDATE equipment_items
                        SET 
                            rfid_rental_class_num = :rfid_class,
                            correlation_confidence = :confidence,
                            correlation_method = :method,
                            correlation_date = NOW()
                        WHERE 
                            item_num = :pos_item
                            AND rfid_rental_class_num IS NULL
                        """
                        
                        conn.execute(text(update_equipment), {
                            'rfid_class': corr['rfid_rental_class'],
                            'confidence': corr['similarity_score'],
                            'method': corr['correlation_type'],
                            'pos_item': corr['pos_item_num']
                        })
                    
                    results['applied'] += 1
                    results['details'].append({
                        'item': corr['pos_item_num'],
                        'status': 'success'
                    })
                    
                except Exception as e:
                    results['errors'].append({
                        'item': corr['pos_item_num'],
                        'error': str(e)
                    })
        
        return results
    
    def validate_existing_correlations(self) -> Dict:
        """Validate existing correlations for consistency"""
        validation = {
            'timestamp': datetime.now().isoformat(),
            'issues': [],
            'statistics': {}
        }
        
        with self.engine.connect() as conn:
            # Check for orphaned correlations
            orphan_check = """
            SELECT 
                e.item_num,
                e.rfid_rental_class_num,
                'Orphaned correlation - RFID class not found' as issue
            FROM equipment_items e
            LEFT JOIN (
                SELECT DISTINCT rental_class_num
                FROM id_item_master
                WHERE rental_class_num IS NOT NULL
            ) i ON e.rfid_rental_class_num = i.rental_class_num
            WHERE 
                e.rfid_rental_class_num IS NOT NULL
                AND i.rental_class_num IS NULL
            """
            
            result = conn.execute(text(orphan_check))
            for row in result:
                validation['issues'].append({
                    'item_num': row[0],
                    'rfid_class': row[1],
                    'issue': row[2]
                })
            
            # Check for duplicate correlations
            duplicate_check = """
            SELECT 
                rfid_rental_class_num,
                COUNT(DISTINCT item_num) as item_count,
                GROUP_CONCAT(item_num) as items
            FROM equipment_items
            WHERE rfid_rental_class_num IS NOT NULL
            GROUP BY rfid_rental_class_num
            HAVING COUNT(DISTINCT item_num) > 1
            """
            
            result = conn.execute(text(duplicate_check))
            for row in result:
                validation['issues'].append({
                    'rfid_class': row[0],
                    'issue': f'Multiple items ({row[1]}) mapped to same RFID class',
                    'items': row[2]
                })
        
        validation['statistics']['total_issues'] = len(validation['issues'])
        return validation
    
    def generate_correlation_report(self) -> str:
        """Generate a comprehensive correlation report"""
        report_lines = [
            "=" * 80,
            "EQUIPMENT-RFID CORRELATION REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            ""
        ]
        
        # Get analysis
        analysis = self.analyze_correlation_potential()
        
        # Statistics section
        report_lines.append("STATISTICS:")
        report_lines.append("-" * 40)
        for table, stats in analysis['statistics'].items():
            report_lines.append(f"\n{table}:")
            for key, value in stats.items():
                report_lines.append(f"  {key}: {value:,}")
        
        # Correlation rate
        if 'correlation_rate' in analysis:
            report_lines.append(f"\nOverall Correlation Rate: {analysis['correlation_rate']}%")
        
        # Find potential correlations
        report_lines.append("\n" + "=" * 80)
        report_lines.append("POTENTIAL CORRELATIONS:")
        report_lines.append("-" * 40)
        
        # Exact matches
        exact_correlations = self.find_correlations_by_number()
        report_lines.append(f"\nExact Number Matches: {len(exact_correlations)}")
        for corr in exact_correlations[:5]:
            report_lines.append(
                f"  {corr['pos_item_num']} ({corr['pos_name'][:30]}) -> "
                f"{corr['rfid_rental_class']} ({corr['rfid_name'][:30]})"
            )
        
        # Name matches
        name_correlations = self.find_correlations_by_name(limit=20)
        high_confidence = [c for c in name_correlations if c['similarity_score'] >= 0.8]
        report_lines.append(f"\nHigh Confidence Name Matches: {len(high_confidence)}")
        for corr in high_confidence[:5]:
            report_lines.append(
                f"  {corr['pos_item_num']} -> {corr['rfid_rental_class']} "
                f"(similarity: {corr['similarity_score']})"
            )
        
        # Validation issues
        validation = self.validate_existing_correlations()
        if validation['issues']:
            report_lines.append("\n" + "=" * 80)
            report_lines.append("VALIDATION ISSUES:")
            report_lines.append("-" * 40)
            for issue in validation['issues'][:10]:
                report_lines.append(f"  {issue}")
        
        return "\n".join(report_lines)


def main():
    """Main execution function"""
    # Database configuration
    db_config = {
        'host': 'localhost',
        'user': 'rfid_user',
        'password': 'rfid_user_password',
        'database': 'rfid_inventory',
        'charset': 'utf8mb4'
    }
    
    # Initialize service
    service = EquipmentCorrelationService(db_config)
    
    # Generate and print report
    print(service.generate_correlation_report())
    
    # Find and apply correlations
    print("\n" + "=" * 80)
    print("FINDING AND APPLYING CORRELATIONS...")
    print("-" * 40)
    
    # Find exact matches
    exact_correlations = service.find_correlations_by_number()
    if exact_correlations:
        print(f"Found {len(exact_correlations)} exact number matches")
        result = service.apply_correlations(exact_correlations, min_confidence=1.0)
        print(f"Applied: {result['applied']}, Skipped: {result['skipped']}, Errors: {len(result['errors'])}")
    
    # Find name matches
    name_correlations = service.find_correlations_by_name(limit=100)
    high_confidence = [c for c in name_correlations if c['similarity_score'] >= 0.85]
    if high_confidence:
        print(f"Found {len(high_confidence)} high-confidence name matches")
        result = service.apply_correlations(high_confidence, min_confidence=0.85)
        print(f"Applied: {result['applied']}, Skipped: {result['skipped']}, Errors: {len(result['errors'])}")
    
    print("\nCorrelation process complete!")


if __name__ == "__main__":
    main()