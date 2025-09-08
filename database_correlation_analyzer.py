#!/usr/bin/env python3
"""
RFID3 Database Correlation Analyzer
Automated tool for analyzing data relationships and quality metrics
"""

import sys
import os
sys.path.append('/home/tim/RFID3')

from app import create_app, db
from sqlalchemy import text, func
from datetime import datetime, timedelta
import pandas as pd
import json
from typing import Dict, List, Tuple, Optional

class DatabaseCorrelationAnalyzer:
    """Comprehensive database analysis and correlation tool"""
    
    def __init__(self):
        self.app = create_app()
        self.app.app_context().push()
        self.results = {}
        
    def analyze_all(self) -> Dict:
        """Run complete database analysis"""
        print("Starting comprehensive database analysis...")
        
        self.results['timestamp'] = datetime.now().isoformat()
        self.results['basic_stats'] = self.get_basic_statistics()
        self.results['relationships'] = self.analyze_relationships()
        self.results['data_quality'] = self.assess_data_quality()
        self.results['correlations'] = self.find_correlations()
        self.results['recommendations'] = self.generate_recommendations()
        
        return self.results
    
    def get_basic_statistics(self) -> Dict:
        """Gather basic database statistics"""
        stats = {}
        
        # ItemMaster statistics
        query = """
        SELECT 
            COUNT(*) as total_items,
            COUNT(DISTINCT rental_class_num) as unique_rental_classes,
            COUNT(DISTINCT home_store) as unique_home_stores,
            COUNT(DISTINCT current_store) as unique_current_stores,
            COUNT(DISTINCT status) as unique_statuses,
            SUM(CASE WHEN identifier_type = 'None' AND tag_id REGEXP '^[0-9A-F]+$' THEN 1 ELSE 0 END) as rfid_items,
            SUM(CASE WHEN identifier_type = 'QR' THEN 1 ELSE 0 END) as qr_items,
            SUM(CASE WHEN identifier_type = 'Sticker' THEN 1 ELSE 0 END) as sticker_items,
            SUM(CASE WHEN identifier_type = 'Bulk' THEN 1 ELSE 0 END) as bulk_items,
            SUM(CASE WHEN date_last_scanned IS NOT NULL THEN 1 ELSE 0 END) as items_scanned,
            AVG(CASE WHEN turnover_ytd IS NOT NULL THEN turnover_ytd ELSE NULL END) as avg_turnover_ytd
        FROM id_item_master
        """
        
        result = db.session.execute(text(query)).fetchone()
        stats['item_master'] = {
            'total_items': result[0],
            'unique_rental_classes': result[1],
            'unique_home_stores': result[2],
            'unique_current_stores': result[3],
            'unique_statuses': result[4],
            'identifier_distribution': {
                'rfid': result[5],
                'qr': result[6],
                'sticker': result[7],
                'bulk': result[8]
            },
            'scan_coverage': {
                'items_scanned': result[9],
                'scan_percentage': round((result[9] / result[0] * 100), 2) if result[0] > 0 else 0
            },
            'avg_turnover_ytd': float(result[10]) if result[10] else 0
        }
        
        # Transaction statistics
        query = """
        SELECT 
            COUNT(*) as total_transactions,
            COUNT(DISTINCT tag_id) as unique_items,
            COUNT(DISTINCT contract_number) as unique_contracts,
            COUNT(DISTINCT scan_type) as scan_types,
            MIN(scan_date) as earliest_scan,
            MAX(scan_date) as latest_scan
        FROM id_transactions
        """
        
        result = db.session.execute(text(query)).fetchone()
        stats['transactions'] = {
            'total_transactions': result[0],
            'unique_items': result[1],
            'unique_contracts': result[2],
            'scan_types': result[3],
            'date_range': {
                'earliest': result[4].isoformat() if result[4] else None,
                'latest': result[5].isoformat() if result[5] else None
            }
        }
        
        return stats
    
    def analyze_relationships(self) -> Dict:
        """Analyze table relationships and foreign key integrity"""
        relationships = {}
        
        # ItemMaster to Transaction relationship
        query = """
        SELECT 
            'items_in_both' as category,
            COUNT(DISTINCT im.tag_id) as count
        FROM id_item_master im
        INNER JOIN id_transactions t ON im.tag_id = t.tag_id
        
        UNION ALL
        
        SELECT 
            'items_only_master' as category,
            COUNT(DISTINCT im.tag_id) as count
        FROM id_item_master im
        LEFT JOIN id_transactions t ON im.tag_id = t.tag_id
        WHERE t.tag_id IS NULL
        
        UNION ALL
        
        SELECT 
            'orphaned_transactions' as category,
            COUNT(DISTINCT t.tag_id) as count
        FROM id_transactions t
        LEFT JOIN id_item_master im ON t.tag_id = im.tag_id
        WHERE im.tag_id IS NULL
        """
        
        results = db.session.execute(text(query)).fetchall()
        relationships['item_transaction'] = {row[0]: row[1] for row in results}
        
        # Rental class coverage
        query = """
        SELECT 
            (SELECT COUNT(DISTINCT rental_class_num) FROM id_item_master WHERE rental_class_num IS NOT NULL) as used_classes,
            (SELECT COUNT(*) FROM seed_rental_classes) as seed_classes,
            (SELECT COUNT(*) FROM rental_class_mappings) as mapped_classes
        """
        
        result = db.session.execute(text(query)).fetchone()
        relationships['rental_classes'] = {
            'used_in_items': result[0],
            'seed_definitions': result[1],
            'category_mappings': result[2],
            'unmapped_percentage': round(((result[0] - result[2]) / result[0] * 100), 2) if result[0] > 0 else 0
        }
        
        return relationships
    
    def assess_data_quality(self) -> Dict:
        """Assess data quality metrics"""
        quality = {}
        
        # Missing data analysis
        query = """
        SELECT 
            'missing_home_store' as issue,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM id_item_master), 2) as percentage
        FROM id_item_master
        WHERE home_store IS NULL OR home_store = ''
        
        UNION ALL
        
        SELECT 
            'missing_current_store' as issue,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM id_item_master), 2) as percentage
        FROM id_item_master
        WHERE current_store IS NULL OR current_store = ''
        
        UNION ALL
        
        SELECT 
            'missing_rental_class' as issue,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM id_item_master), 2) as percentage
        FROM id_item_master
        WHERE rental_class_num IS NULL OR rental_class_num = ''
        
        UNION ALL
        
        SELECT 
            'never_scanned' as issue,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM id_item_master), 2) as percentage
        FROM id_item_master
        WHERE date_last_scanned IS NULL
        """
        
        results = db.session.execute(text(query)).fetchall()
        quality['missing_data'] = {row[0]: {'count': row[1], 'percentage': float(row[2])} for row in results}
        
        # Data freshness
        query = """
        SELECT 
            CASE 
                WHEN DATEDIFF(NOW(), date_last_scanned) <= 30 THEN 'fresh_0_30_days'
                WHEN DATEDIFF(NOW(), date_last_scanned) <= 90 THEN 'recent_31_90_days'
                WHEN DATEDIFF(NOW(), date_last_scanned) <= 180 THEN 'aging_91_180_days'
                WHEN DATEDIFF(NOW(), date_last_scanned) <= 365 THEN 'stale_181_365_days'
                ELSE 'obsolete_over_365_days'
            END as freshness,
            COUNT(*) as count
        FROM id_item_master
        WHERE date_last_scanned IS NOT NULL
        GROUP BY freshness
        """
        
        results = db.session.execute(text(query)).fetchall()
        quality['data_freshness'] = {row[0]: row[1] for row in results}
        
        # Store consistency
        query = """
        SELECT 
            COUNT(*) as mismatched_stores
        FROM id_item_master
        WHERE home_store != current_store
        AND home_store IS NOT NULL 
        AND current_store IS NOT NULL
        """
        
        result = db.session.execute(text(query)).fetchone()
        quality['store_consistency'] = {
            'mismatched_stores': result[0]
        }
        
        return quality
    
    def find_correlations(self) -> Dict:
        """Find data correlations and patterns"""
        correlations = {}
        
        # Status to identifier type correlation
        query = """
        SELECT 
            status,
            identifier_type,
            COUNT(*) as count
        FROM id_item_master
        WHERE status IS NOT NULL AND identifier_type IS NOT NULL
        GROUP BY status, identifier_type
        ORDER BY count DESC
        LIMIT 20
        """
        
        results = db.session.execute(text(query)).fetchall()
        correlations['status_identifier'] = [
            {'status': row[0], 'identifier_type': row[1], 'count': row[2]} 
            for row in results
        ]
        
        # Store to rental class patterns
        query = """
        SELECT 
            home_store,
            rental_class_num,
            COUNT(*) as item_count
        FROM id_item_master
        WHERE home_store IS NOT NULL AND rental_class_num IS NOT NULL
        GROUP BY home_store, rental_class_num
        HAVING item_count > 10
        ORDER BY home_store, item_count DESC
        """
        
        results = db.session.execute(text(query)).fetchall()
        store_patterns = {}
        for row in results:
            if row[0] not in store_patterns:
                store_patterns[row[0]] = []
            store_patterns[row[0]].append({
                'rental_class': row[1],
                'count': row[2]
            })
        correlations['store_inventory_patterns'] = store_patterns
        
        # Transaction patterns
        query = """
        SELECT 
            scan_type,
            HOUR(scan_date) as hour_of_day,
            COUNT(*) as transaction_count
        FROM id_transactions
        WHERE scan_date > DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY scan_type, hour_of_day
        ORDER BY scan_type, hour_of_day
        """
        
        results = db.session.execute(text(query)).fetchall()
        transaction_patterns = {}
        for row in results:
            if row[0] not in transaction_patterns:
                transaction_patterns[row[0]] = {}
            transaction_patterns[row[0]][row[1]] = row[2]
        correlations['transaction_patterns'] = transaction_patterns
        
        return correlations
    
    def generate_recommendations(self) -> List[Dict]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        # Check for critical data quality issues
        if self.results.get('data_quality', {}).get('missing_data', {}).get('never_scanned', {}).get('percentage', 0) > 50:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Data Quality',
                'issue': 'Majority of inventory never scanned',
                'recommendation': 'Initiate comprehensive inventory count campaign',
                'impact': 'Cannot track or manage unscanned inventory',
                'effort': 'High',
                'sql_fix': """
                UPDATE id_item_master 
                SET date_last_scanned = NOW() 
                WHERE tag_id IN (
                    SELECT DISTINCT tag_id 
                    FROM id_transactions 
                    WHERE scan_date > DATE_SUB(NOW(), INTERVAL 90 DAY)
                )
                AND date_last_scanned IS NULL
                """
            })
        
        # Check for missing store data
        if self.results.get('data_quality', {}).get('missing_data', {}).get('missing_home_store', {}).get('percentage', 0) > 10:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Store Management',
                'issue': 'Significant missing store location data',
                'recommendation': 'Implement store assignment based on transaction history',
                'impact': 'Cannot track inventory location and movement',
                'effort': 'Medium',
                'sql_fix': """
                UPDATE id_item_master im
                SET home_store = '6800', current_store = '6800'
                WHERE (home_store IS NULL OR current_store IS NULL)
                AND EXISTS (
                    SELECT 1 FROM id_transactions t 
                    WHERE t.tag_id = im.tag_id 
                    AND t.scan_date > DATE_SUB(NOW(), INTERVAL 180 DAY)
                )
                """
            })
        
        # Check for orphaned transactions
        orphaned = self.results.get('relationships', {}).get('item_transaction', {}).get('orphaned_transactions', 0)
        if orphaned > 100:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Data Integrity',
                'issue': f'{orphaned} orphaned transactions found',
                'recommendation': 'Clean up orphaned transactions or create missing item records',
                'impact': 'Transaction history incomplete',
                'effort': 'Low',
                'sql_fix': """
                DELETE FROM id_transactions 
                WHERE tag_id NOT IN (SELECT tag_id FROM id_item_master)
                AND scan_date < DATE_SUB(NOW(), INTERVAL 180 DAY)
                """
            })
        
        # Check for missing rental class mappings
        if self.results.get('relationships', {}).get('rental_classes', {}).get('category_mappings', 0) == 0:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Classification',
                'issue': 'No rental class category mappings exist',
                'recommendation': 'Populate rental_class_mappings table',
                'impact': 'Cannot generate category-based reports',
                'effort': 'Low',
                'sql_fix': """
                INSERT INTO rental_class_mappings (rental_class_id, category, subcategory)
                SELECT DISTINCT 
                    rental_class_num,
                    SUBSTRING_INDEX(common_name, ' ', 1),
                    common_name
                FROM id_item_master
                WHERE rental_class_num IS NOT NULL
                """
            })
        
        # Check for stale data
        stale_items = (
            self.results.get('data_quality', {}).get('data_freshness', {}).get('stale_181_365_days', 0) +
            self.results.get('data_quality', {}).get('data_freshness', {}).get('obsolete_over_365_days', 0)
        )
        if stale_items > 1000:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Data Freshness',
                'issue': f'{stale_items} items not scanned in over 6 months',
                'recommendation': 'Archive or verify existence of stale inventory',
                'impact': 'Inventory counts may be inaccurate',
                'effort': 'Medium',
                'action': 'Schedule physical inventory verification for stale items'
            })
        
        return recommendations
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive analysis report"""
        report = []
        report.append("=" * 80)
        report.append("RFID3 DATABASE CORRELATION ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {self.results.get('timestamp', 'Unknown')}")
        report.append("")
        
        # Basic Statistics
        report.append("## BASIC STATISTICS")
        report.append("-" * 40)
        stats = self.results.get('basic_stats', {})
        if 'item_master' in stats:
            im = stats['item_master']
            report.append(f"Total Items: {im['total_items']:,}")
            report.append(f"Scan Coverage: {im['scan_coverage']['scan_percentage']}%")
            report.append(f"Identifier Types:")
            for id_type, count in im['identifier_distribution'].items():
                report.append(f"  - {id_type.upper()}: {count:,}")
        report.append("")
        
        # Data Quality
        report.append("## DATA QUALITY ISSUES")
        report.append("-" * 40)
        quality = self.results.get('data_quality', {})
        if 'missing_data' in quality:
            for issue, data in quality['missing_data'].items():
                report.append(f"{issue.replace('_', ' ').title()}: {data['count']:,} ({data['percentage']}%)")
        report.append("")
        
        # Relationships
        report.append("## TABLE RELATIONSHIPS")
        report.append("-" * 40)
        relationships = self.results.get('relationships', {})
        if 'item_transaction' in relationships:
            it = relationships['item_transaction']
            report.append(f"Items in both tables: {it.get('items_in_both', 0):,}")
            report.append(f"Items only in master: {it.get('items_only_master', 0):,}")
            report.append(f"Orphaned transactions: {it.get('orphaned_transactions', 0):,}")
        report.append("")
        
        # Recommendations
        report.append("## PRIORITY RECOMMENDATIONS")
        report.append("-" * 40)
        for rec in self.results.get('recommendations', []):
            report.append(f"\n[{rec['priority']}] {rec['category']}: {rec['issue']}")
            report.append(f"  Recommendation: {rec['recommendation']}")
            report.append(f"  Impact: {rec['impact']}")
            report.append(f"  Effort: {rec['effort']}")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"Report saved to: {output_file}")
        
        return report_text
    
    def export_to_json(self, output_file: str) -> None:
        """Export analysis results to JSON"""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"JSON results exported to: {output_file}")

def main():
    """Main execution function"""
    print("Initializing Database Correlation Analyzer...")
    analyzer = DatabaseCorrelationAnalyzer()
    
    print("Running comprehensive analysis...")
    results = analyzer.analyze_all()
    
    # Generate reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Text report
    report_file = f"/home/tim/RFID3/analysis_report_{timestamp}.txt"
    report = analyzer.generate_report(report_file)
    print("\n" + report)
    
    # JSON export
    json_file = f"/home/tim/RFID3/analysis_data_{timestamp}.json"
    analyzer.export_to_json(json_file)
    
    # Summary
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Text Report: {report_file}")
    print(f"JSON Data: {json_file}")
    
    # Quick summary of critical issues
    critical_count = sum(1 for r in results.get('recommendations', []) if r['priority'] == 'CRITICAL')
    high_count = sum(1 for r in results.get('recommendations', []) if r['priority'] == 'HIGH')
    
    if critical_count > 0 or high_count > 0:
        print(f"\n⚠️  ATTENTION REQUIRED: {critical_count} critical and {high_count} high priority issues found!")
    else:
        print("\n✓ No critical issues found. System is in good health.")

if __name__ == "__main__":
    main()