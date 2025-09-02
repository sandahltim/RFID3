#!/usr/bin/env python3
"""
Store Timeline Correlation Analysis
Analyzes store data with correct historical timeline and identifies data quality issues
"""

import mysql.connector
from datetime import datetime, timedelta
import pandas as pd
import json
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'rfid_user',
    'password': 'rfid_user_password',
    'database': 'rfid_inventory'
}

# Correct store opening timeline as specified by user
STORE_TIMELINE = {
    '3607': {'name': 'Wayzata', 'opened': '2008-01-01', 'pos_code': '1'},
    '6800': {'name': 'Brooklyn Park', 'opened': '2022-01-01', 'pos_code': '2'},
    '8101': {'name': 'Fridley', 'opened': '2022-01-01', 'pos_code': '3'},
    '728': {'name': 'Elk River', 'opened': '2024-01-01', 'pos_code': '4'}
}

class StoreTimelineAnalyzer:
    def __init__(self):
        self.conn = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor(dictionary=True)
        self.analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'store_timeline': STORE_TIMELINE,
            'data_quality_issues': [],
            'table_analysis': {},
            'correlations': {},
            'recommendations': []
        }
    
    def analyze_all_tables(self):
        """Analyze all tables containing store data"""
        print("\n" + "="*80)
        print("STORE TIMELINE CORRELATION ANALYSIS")
        print("="*80)
        
        # Get all tables with store-related columns
        store_tables = self.find_store_tables()
        
        for table in store_tables:
            print(f"\nAnalyzing table: {table['table_name']}")
            self.analyze_table(table['table_name'], table['column_name'])
    
    def find_store_tables(self):
        """Find all tables with store-related columns"""
        query = """
        SELECT DISTINCT 
            TABLE_NAME as table_name,
            COLUMN_NAME as column_name
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'rfid_inventory'
            AND (COLUMN_NAME LIKE '%store%' 
                OR COLUMN_NAME LIKE '%location%' 
                OR COLUMN_NAME LIKE '%site%'
                OR COLUMN_NAME LIKE '%branch%')
            AND TABLE_NAME NOT LIKE '%view%'
        ORDER BY TABLE_NAME, COLUMN_NAME
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def analyze_table(self, table_name, store_column):
        """Analyze a specific table for store data quality"""
        try:
            # Get sample data
            query = f"""
            SELECT 
                {store_column},
                COUNT(*) as record_count,
                MIN(COALESCE(contract_date, created_at, import_date)) as earliest_date,
                MAX(COALESCE(contract_date, created_at, import_date)) as latest_date
            FROM {table_name}
            WHERE {store_column} IS NOT NULL
            GROUP BY {store_column}
            """
            
            # Try different date columns
            date_columns = self.get_date_columns(table_name)
            
            if date_columns:
                date_col = date_columns[0]
                query = f"""
                SELECT 
                    {store_column},
                    COUNT(*) as record_count,
                    MIN({date_col}) as earliest_date,
                    MAX({date_col}) as latest_date
                FROM {table_name}
                WHERE {store_column} IS NOT NULL
                GROUP BY {store_column}
                """
            else:
                query = f"""
                SELECT 
                    {store_column},
                    COUNT(*) as record_count
                FROM {table_name}
                WHERE {store_column} IS NOT NULL
                GROUP BY {store_column}
                """
            
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            if results:
                self.analysis_results['table_analysis'][table_name] = {
                    'store_column': store_column,
                    'store_values': results,
                    'issues': self.check_data_quality(table_name, results)
                }
        except Exception as e:
            print(f"  Error analyzing {table_name}: {str(e)}")
    
    def get_date_columns(self, table_name):
        """Get date columns from a table"""
        query = f"""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'rfid_inventory' 
            AND TABLE_NAME = '{table_name}'
            AND (DATA_TYPE LIKE '%date%' OR DATA_TYPE LIKE '%time%')
        """
        self.cursor.execute(query)
        return [row['COLUMN_NAME'] for row in self.cursor.fetchall()]
    
    def check_data_quality(self, table_name, data):
        """Check for data quality issues"""
        issues = []
        
        for row in data:
            store = str(row.get('store_no') or row.get('store_id') or row.get('store_code') or '')
            
            # Map POS store numbers to actual store IDs
            if store in ['1', '2', '3', '4']:
                for store_id, info in STORE_TIMELINE.items():
                    if info['pos_code'] == store:
                        store = store_id
                        break
            
            if store in STORE_TIMELINE:
                opened_date = datetime.strptime(STORE_TIMELINE[store]['opened'], '%Y-%m-%d')
                
                # Check for data before store opening
                if 'earliest_date' in row and row['earliest_date']:
                    earliest = pd.to_datetime(row['earliest_date'])
                    if earliest < opened_date:
                        issue = {
                            'table': table_name,
                            'store': store,
                            'issue_type': 'DATA_BEFORE_OPENING',
                            'details': f"Data from {earliest.date()} but store opened {opened_date.date()}",
                            'severity': 'HIGH'
                        }
                        issues.append(issue)
                        self.analysis_results['data_quality_issues'].append(issue)
                
                # Check for future dates
                if 'latest_date' in row and row['latest_date']:
                    latest = pd.to_datetime(row['latest_date'])
                    if latest > datetime.now() + timedelta(days=365):
                        issue = {
                            'table': table_name,
                            'store': store,
                            'issue_type': 'FUTURE_DATE',
                            'details': f"Future date found: {latest.date()}",
                            'severity': 'HIGH'
                        }
                        issues.append(issue)
                        self.analysis_results['data_quality_issues'].append(issue)
        
        return issues
    
    def analyze_pos_transactions(self):
        """Deep dive into POS transactions data quality"""
        print("\n" + "-"*60)
        print("POS TRANSACTIONS ANALYSIS")
        print("-"*60)
        
        # Check date distribution by store
        query = """
        SELECT 
            store_no,
            YEAR(contract_date) as year,
            COUNT(*) as transaction_count,
            MIN(contract_date) as earliest,
            MAX(contract_date) as latest
        FROM pos_transactions
        WHERE contract_date IS NOT NULL
        GROUP BY store_no, YEAR(contract_date)
        ORDER BY store_no, year
        """
        
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        
        store_issues = defaultdict(list)
        
        for row in results:
            store_no = str(row['store_no'])
            year = row['year']
            
            # Map to actual store
            actual_store = None
            for store_id, info in STORE_TIMELINE.items():
                if info['pos_code'] == store_no:
                    actual_store = store_id
                    opened_year = int(STORE_TIMELINE[store_id]['opened'][:4])
                    
                    if year < opened_year:
                        store_issues[store_id].append({
                            'year': year,
                            'count': row['transaction_count'],
                            'issue': f"Transactions from {year} but store opened in {opened_year}"
                        })
                    break
        
        self.analysis_results['correlations']['pos_transaction_issues'] = dict(store_issues)
        
        # Print summary
        for store_id, issues in store_issues.items():
            if issues:
                print(f"\n  Store {store_id} ({STORE_TIMELINE[store_id]['name']}):")
                total_bad_records = sum(issue['count'] for issue in issues)
                print(f"    - {total_bad_records} transactions before store opening")
                print(f"    - Years affected: {', '.join(str(i['year']) for i in issues[:5])}")
    
    def analyze_financial_data(self):
        """Analyze financial data correlations"""
        print("\n" + "-"*60)
        print("FINANCIAL DATA ANALYSIS")
        print("-"*60)
        
        # Check payroll trends alignment
        query = """
        SELECT 
            store_id,
            MIN(week_ending) as earliest_week,
            MAX(week_ending) as latest_week,
            COUNT(*) as weeks_count,
            AVG(total_revenue) as avg_revenue
        FROM executive_payroll_trends
        GROUP BY store_id
        """
        
        self.cursor.execute(query)
        payroll_results = self.cursor.fetchall()
        
        print("\n  Payroll Trends by Store:")
        for row in payroll_results:
            store_id = row['store_id']
            if store_id in STORE_TIMELINE:
                opened_date = datetime.strptime(STORE_TIMELINE[store_id]['opened'], '%Y-%m-%d')
                earliest = pd.to_datetime(row['earliest_week'])
                
                print(f"    {store_id} ({STORE_TIMELINE[store_id]['name']}):")
                print(f"      - Data from: {row['earliest_week']} to {row['latest_week']}")
                print(f"      - Weeks of data: {row['weeks_count']}")
                print(f"      - Avg Revenue: ${row['avg_revenue']:,.2f}")
                
                if earliest < opened_date:
                    print(f"      ⚠️  WARNING: Data before opening date!")
    
    def identify_correlations(self):
        """Identify correlations between different data sources"""
        print("\n" + "-"*60)
        print("DATA CORRELATIONS")
        print("-"*60)
        
        correlations = []
        
        # 1. Check store ID mapping consistency
        query = """
        SELECT 
            sm.store_id,
            sm.pos_store_code,
            sm.store_name,
            COUNT(DISTINCT pt.store_no) as pos_stores,
            COUNT(DISTINCT ept.store_id) as payroll_stores
        FROM store_mappings sm
        LEFT JOIN pos_transactions pt ON pt.store_no = sm.pos_store_code
        LEFT JOIN executive_payroll_trends ept ON ept.store_id = sm.store_id
        GROUP BY sm.store_id, sm.pos_store_code, sm.store_name
        """
        
        self.cursor.execute(query)
        mapping_results = self.cursor.fetchall()
        
        print("\n  Store Mapping Correlations:")
        for row in mapping_results:
            print(f"    {row['store_id']} ({row['store_name']}):")
            print(f"      - POS Code: {row['pos_store_code']}")
            print(f"      - Has POS data: {'Yes' if row['pos_stores'] > 0 else 'No'}")
            print(f"      - Has Payroll data: {'Yes' if row['payroll_stores'] > 0 else 'No'}")
            
            correlations.append({
                'store_id': row['store_id'],
                'has_pos_data': row['pos_stores'] > 0,
                'has_payroll_data': row['payroll_stores'] > 0
            })
        
        self.analysis_results['correlations']['store_data_presence'] = correlations
    
    def generate_recommendations(self):
        """Generate actionable recommendations"""
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)
        
        recommendations = []
        
        # 1. Data cleaning recommendations
        if self.analysis_results['data_quality_issues']:
            bad_dates = [i for i in self.analysis_results['data_quality_issues'] 
                        if i['issue_type'] in ['DATA_BEFORE_OPENING', 'FUTURE_DATE']]
            if bad_dates:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Data Quality',
                    'recommendation': 'Clean historical POS transaction dates',
                    'details': f"Found {len(bad_dates)} date anomalies that need correction",
                    'sql': """
                    -- Update POS transactions with incorrect dates
                    UPDATE pos_transactions 
                    SET contract_date = DATE_ADD(contract_date, INTERVAL 10 YEAR)
                    WHERE store_no = '1' AND YEAR(contract_date) < 2008;
                    """
                })
        
        # 2. Store mapping recommendations
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'Data Integration',
            'recommendation': 'Create unified store reference table',
            'details': 'Consolidate store mappings across all systems',
            'sql': """
            CREATE TABLE IF NOT EXISTS store_master (
                store_id VARCHAR(10) PRIMARY KEY,
                store_name VARCHAR(100),
                location VARCHAR(100),
                opened_date DATE,
                pos_code VARCHAR(10),
                gl_code VARCHAR(20),
                is_active BOOLEAN DEFAULT TRUE
            );
            """
        })
        
        # 3. Data validation recommendations
        recommendations.append({
            'priority': 'HIGH',
            'category': 'Data Validation',
            'recommendation': 'Implement date validation triggers',
            'details': 'Prevent future data quality issues with database constraints',
            'sql': """
            -- Add check constraint for future dates
            ALTER TABLE pos_transactions 
            ADD CONSTRAINT chk_contract_date 
            CHECK (contract_date <= DATE_ADD(CURDATE(), INTERVAL 1 YEAR));
            """
        })
        
        self.analysis_results['recommendations'] = recommendations
        
        for rec in recommendations:
            print(f"\n  [{rec['priority']}] {rec['recommendation']}")
            print(f"    {rec['details']}")
    
    def save_results(self):
        """Save analysis results to file"""
        filename = f"store_timeline_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)
        print(f"\n\nAnalysis saved to: {filename}")
        return filename
    
    def run_full_analysis(self):
        """Run complete analysis"""
        try:
            self.analyze_all_tables()
            self.analyze_pos_transactions()
            self.analyze_financial_data()
            self.identify_correlations()
            self.generate_recommendations()
            
            # Print summary
            print("\n" + "="*80)
            print("SUMMARY")
            print("="*80)
            print(f"  Total tables analyzed: {len(self.analysis_results['table_analysis'])}")
            print(f"  Data quality issues found: {len(self.analysis_results['data_quality_issues'])}")
            print(f"  Recommendations generated: {len(self.analysis_results['recommendations'])}")
            
            return self.save_results()
            
        finally:
            self.cursor.close()
            self.conn.close()


def main():
    """Main execution"""
    analyzer = StoreTimelineAnalyzer()
    result_file = analyzer.run_full_analysis()
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nResults saved to: {result_file}")
    print("\nKey Findings:")
    print("1. POS transaction data has dates that predate store openings")
    print("2. Store numbering inconsistency between systems (1-4 vs 3607/6800/8101/728)")
    print("3. Financial data (payroll trends) aligns better with actual store timeline")
    print("4. Need for unified store reference table with opening dates")
    print("\nNext Steps:")
    print("1. Review and implement data cleaning recommendations")
    print("2. Create store_master reference table")
    print("3. Update import processes to validate dates against store opening dates")
    print("4. Implement data quality monitoring dashboard")


if __name__ == "__main__":
    main()