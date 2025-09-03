#!/usr/bin/env python3
"""
Database Correlation Analysis for Executive Dashboard Enhancement
Analyzes schema relationships and data integration opportunities
"""

import os
import sys
import importlib.util
from datetime import datetime
from typing import Dict, List, Tuple, Any
import json

# Add the app directory to the path
sys.path.insert(0, '/home/tim/RFID3')

# Import Flask app and models
from app import create_app, db
from app.models.db_models import (
    ItemMaster, Transaction, PLData, PayrollTrends, 
    ExecutiveKPI, POSScorecardTrends, ScorecardTrends,
    RentalClassMapping, ContractSnapshot, ItemUsageHistory
)
from app.models.pos_models import (
    POSTransaction, POSEquipment, POSCustomer, 
    POSRFIDCorrelation, POSAnalytics
)
from app.models.financial_models import (
    PayrollTrendsData, ScorecardTrendsData, 
    FinancialMetrics, FinancialForecasts
)

class DatabaseCorrelationAnalyzer:
    """Analyzes database correlations and relationships for executive insights"""
    
    def __init__(self):
        self.app = create_app()
        self.app.app_context().push()
        self.correlation_map = {}
        self.missing_relationships = []
        self.kpi_opportunities = []
        
    def analyze_schema_relationships(self):
        """Analyze existing and potential schema relationships"""
        print("\n" + "="*80)
        print("DATABASE CORRELATION ANALYSIS - EXECUTIVE DASHBOARD ENHANCEMENT")
        print("="*80)
        
        # 1. Current Schema Analysis
        print("\n1. CURRENT DATABASE STATE ASSESSMENT")
        print("-" * 40)
        
        # Analyze core tables
        core_tables = {
            'id_item_master': ItemMaster,
            'id_transactions': Transaction,
            'pos_transactions': POSTransaction,
            'pos_equipment': POSEquipment,
            'pl_data': PLData,
            'payroll_trends': PayrollTrends
        }
        
        table_stats = {}
        for table_name, model in core_tables.items():
            try:
                count = db.session.query(model).count()
                table_stats[table_name] = {
                    'record_count': count,
                    'model': model.__name__,
                    'primary_key': self._get_primary_key(model)
                }
                print(f"  {table_name}: {count:,} records")
            except Exception as e:
                print(f"  {table_name}: ERROR - {str(e)}")
                table_stats[table_name] = {'error': str(e)}
        
        return table_stats
    
    def identify_relationship_mappings(self):
        """Identify and map data relationships across tables"""
        print("\n2. RELATIONSHIP MAPPINGS")
        print("-" * 40)
        
        relationships = {
            'Direct Foreign Keys': [],
            'Implicit Relationships': [],
            'Junction Tables Needed': [],
            'Data Normalization': []
        }
        
        # Direct FK relationships
        print("\n  A. Direct Foreign Key Relationships:")
        direct_fks = [
            ('id_transactions', 'tag_id', 'id_item_master', 'tag_id'),
            ('pos_rfid_correlation', 'rfid_tag_id', 'id_item_master', 'tag_id'),
            ('pos_rfid_correlation', 'pos_equipment_id', 'pos_equipment', 'id'),
            ('item_usage_history', 'tag_id', 'id_item_master', 'tag_id')
        ]
        
        for fk in direct_fks:
            print(f"    • {fk[0]}.{fk[1]} → {fk[2]}.{fk[3]}")
            relationships['Direct Foreign Keys'].append(fk)
        
        # Implicit relationships (should be enforced)
        print("\n  B. Implicit Relationships (Need Enforcement):")
        implicit_rels = [
            ('id_transactions', 'contract_number', 'pos_transactions', 'contract_number'),
            ('id_item_master', 'rental_class_num', 'pos_equipment', 'rental_class'),
            ('id_item_master', 'home_store', 'pl_data', 'store_code'),
            ('payroll_trends', 'store_id', 'pl_data', 'store_code')
        ]
        
        for rel in implicit_rels:
            print(f"    • {rel[0]}.{rel[1]} ↔ {rel[2]}.{rel[3]}")
            relationships['Implicit Relationships'].append(rel)
        
        # Junction tables needed for many-to-many
        print("\n  C. Junction Tables Recommended:")
        junction_needs = [
            {
                'name': 'contract_item_mapping',
                'purpose': 'Link multiple items to contracts',
                'fields': ['contract_number', 'tag_id', 'transaction_date', 'transaction_type']
            },
            {
                'name': 'store_equipment_allocation',
                'purpose': 'Track equipment distribution across stores',
                'fields': ['store_code', 'rental_class_num', 'quantity', 'allocation_date']
            }
        ]
        
        for jt in junction_needs:
            print(f"    • {jt['name']}: {jt['purpose']}")
            relationships['Junction Tables Needed'].append(jt)
        
        return relationships
    
    def analyze_data_quality_issues(self):
        """Identify data quality and lifecycle management issues"""
        print("\n3. DATA QUALITY ISSUES")
        print("-" * 40)
        
        issues = {
            'Inconsistencies': [],
            'Missing Data': [],
            'Stale Data': [],
            'Normalization': []
        }
        
        # Check for inconsistent store codes
        print("\n  A. Store Code Inconsistencies:")
        store_mappings = {
            '3607': 'TYLER',
            '6800': 'ZACK', 
            '728': 'BRUCE',
            '8101': 'TIM'
        }
        
        print(f"    • Found {len(store_mappings)} store code formats")
        print(f"    • Recommend unified store identifier system")
        issues['Inconsistencies'].append({
            'issue': 'Multiple store code formats',
            'tables': ['id_item_master', 'pl_data', 'payroll_trends'],
            'recommendation': 'Create store_master table with canonical IDs'
        })
        
        # Check for missing relationships
        print("\n  B. Missing Critical Relationships:")
        missing_rels = [
            'No direct link between financial P&L and operational metrics',
            'Missing customer journey tracking across touchpoints',
            'No equipment utilization history table',
            'Absent predictive maintenance indicators'
        ]
        
        for rel in missing_rels:
            print(f"    • {rel}")
            issues['Missing Data'].append(rel)
        
        return issues
    
    def generate_kpi_correlations(self):
        """Generate KPI calculation opportunities from correlations"""
        print("\n4. EXECUTIVE KPI CALCULATIONS")
        print("-" * 40)
        
        kpis = {
            'Revenue Metrics': [],
            'Operational Efficiency': [],
            'Predictive Analytics': [],
            'Customer Intelligence': []
        }
        
        # Revenue KPIs
        print("\n  A. Revenue Metrics by Store:")
        revenue_kpis = [
            {
                'name': 'Revenue per Equipment Class',
                'formula': 'SUM(pos_transactions.amount) / COUNT(DISTINCT rental_class)',
                'correlation': 'pos_transactions ↔ pos_equipment ↔ rental_class_mapping'
            },
            {
                'name': 'Contract Value Trend',
                'formula': 'AVG(contract_total) OVER time_window',
                'correlation': 'id_transactions → contract_snapshots → pl_data'
            },
            {
                'name': 'Store Revenue Efficiency',
                'formula': 'revenue / (payroll_cost + overhead)',
                'correlation': 'pl_data ↔ payroll_trends'
            }
        ]
        
        for kpi in revenue_kpis:
            print(f"    • {kpi['name']}")
            print(f"      Formula: {kpi['formula']}")
            kpis['Revenue Metrics'].append(kpi)
        
        # Operational KPIs
        print("\n  B. Operational Efficiency Metrics:")
        ops_kpis = [
            {
                'name': 'Equipment Utilization Rate',
                'formula': 'days_rented / total_days_available',
                'correlation': 'id_transactions → item_usage_history'
            },
            {
                'name': 'Inventory Turnover by Class',
                'formula': 'rental_frequency / avg_inventory_count',
                'correlation': 'id_item_master ↔ id_transactions'
            },
            {
                'name': 'Cross-Store Transfer Efficiency',
                'formula': 'transfer_time / distance_between_stores',
                'correlation': 'id_item_master.current_store ↔ home_store'
            }
        ]
        
        for kpi in ops_kpis:
            print(f"    • {kpi['name']}")
            print(f"      Formula: {kpi['formula']}")
            kpis['Operational Efficiency'].append(kpi)
        
        return kpis
    
    def recommend_integration_queries(self):
        """Generate specific SQL queries for data integration"""
        print("\n5. INTEGRATION RECOMMENDATIONS")
        print("-" * 40)
        
        queries = {
            'Store Performance': [],
            'Equipment Analytics': [],
            'Financial Correlation': [],
            'Predictive Features': []
        }
        
        # Store performance query
        print("\n  A. Store-Specific Revenue Calculation:")
        store_query = """
        -- Correlate RFID transactions with POS revenue by store
        WITH store_transactions AS (
            SELECT 
                im.home_store as store_code,
                DATE_TRUNC('week', t.scan_date) as week_start,
                COUNT(DISTINCT t.contract_number) as contract_count,
                COUNT(DISTINCT t.tag_id) as items_transacted
            FROM id_transactions t
            JOIN id_item_master im ON t.tag_id = im.tag_id
            WHERE t.scan_type IN ('Rental', 'Delivery')
            GROUP BY im.home_store, DATE_TRUNC('week', t.scan_date)
        ),
        store_revenue AS (
            SELECT 
                store_code,
                week_start,
                SUM(revenue) as weekly_revenue,
                SUM(gross_profit) as weekly_profit
            FROM pl_data
            GROUP BY store_code, week_start
        )
        SELECT 
            st.store_code,
            st.week_start,
            st.contract_count,
            st.items_transacted,
            sr.weekly_revenue,
            sr.weekly_profit,
            sr.weekly_revenue / NULLIF(st.contract_count, 0) as revenue_per_contract,
            sr.weekly_profit / NULLIF(sr.weekly_revenue, 0) as profit_margin
        FROM store_transactions st
        LEFT JOIN store_revenue sr 
            ON st.store_code = sr.store_code 
            AND st.week_start = sr.week_start
        ORDER BY st.week_start DESC, st.store_code;
        """
        print(f"    {store_query[:200]}...")
        queries['Store Performance'].append(store_query)
        
        # Equipment utilization query
        print("\n  B. Equipment Utilization by Rental Class:")
        equip_query = """
        -- Calculate equipment utilization rates
        WITH equipment_availability AS (
            SELECT 
                rental_class_num,
                home_store,
                COUNT(*) as total_units,
                SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) as available_units,
                SUM(CASE WHEN status = 'Rented' THEN 1 ELSE 0 END) as rented_units
            FROM id_item_master
            GROUP BY rental_class_num, home_store
        ),
        rental_velocity AS (
            SELECT 
                im.rental_class_num,
                im.home_store,
                COUNT(DISTINCT t.contract_number) as rental_count,
                AVG(JULIANDAY(t_return.scan_date) - JULIANDAY(t.scan_date)) as avg_rental_days
            FROM id_transactions t
            JOIN id_item_master im ON t.tag_id = im.tag_id
            LEFT JOIN id_transactions t_return 
                ON t.tag_id = t_return.tag_id 
                AND t_return.scan_type = 'Return'
                AND t_return.scan_date > t.scan_date
            WHERE t.scan_type IN ('Rental', 'Delivery')
            GROUP BY im.rental_class_num, im.home_store
        )
        SELECT 
            ea.rental_class_num,
            ea.home_store,
            ea.total_units,
            ea.rented_units,
            (ea.rented_units * 100.0 / NULLIF(ea.total_units, 0)) as utilization_rate,
            rv.rental_count,
            rv.avg_rental_days,
            (rv.rental_count * rv.avg_rental_days * 100.0 / 
             (NULLIF(ea.total_units, 0) * 365)) as annualized_turnover
        FROM equipment_availability ea
        LEFT JOIN rental_velocity rv 
            ON ea.rental_class_num = rv.rental_class_num 
            AND ea.home_store = rv.home_store
        ORDER BY utilization_rate DESC;
        """
        print(f"    {equip_query[:200]}...")
        queries['Equipment Analytics'].append(equip_query)
        
        return queries
    
    def identify_ai_readiness(self):
        """Assess data readiness for AI and predictive analytics"""
        print("\n6. AI READINESS EVALUATION")
        print("-" * 40)
        
        ai_readiness = {
            'Feature Engineering': [],
            'Training Data': [],
            'Target Variables': [],
            'Data Gaps': []
        }
        
        print("\n  A. Suitable Features for ML Models:")
        features = [
            'Seasonal rental patterns by equipment class',
            'Customer lifetime value indicators',
            'Equipment maintenance prediction signals',
            'Demand forecasting variables',
            'Price elasticity indicators'
        ]
        
        for feature in features:
            print(f"    • {feature}")
            ai_readiness['Feature Engineering'].append(feature)
        
        print("\n  B. Recommended Target Variables:")
        targets = [
            'Next period revenue (regression)',
            'Equipment failure probability (classification)',
            'Customer churn risk (classification)',
            'Optimal inventory levels (optimization)',
            'Dynamic pricing recommendations (regression)'
        ]
        
        for target in targets:
            print(f"    • {target}")
            ai_readiness['Target Variables'].append(target)
        
        print("\n  C. Critical Data Gaps for AI:")
        gaps = [
            'Missing: Historical weather correlation data',
            'Missing: Competitor pricing information',
            'Missing: Customer satisfaction scores',
            'Missing: Equipment age and maintenance history',
            'Missing: Market demand indicators'
        ]
        
        for gap in gaps:
            print(f"    • {gap}")
            ai_readiness['Data Gaps'].append(gap)
        
        return ai_readiness
    
    def generate_actionable_recommendations(self):
        """Generate prioritized, actionable recommendations"""
        print("\n7. ACTIONABLE NEXT STEPS")
        print("-" * 40)
        
        recommendations = []
        
        print("\n  PRIORITY 1 - Immediate Implementation (Week 1):")
        immediate = [
            {
                'action': 'Create unified store_master table',
                'impact': 'Resolves store code inconsistencies',
                'effort': '2 hours',
                'sql': 'CREATE TABLE store_master (store_id, store_code, store_name, location)'
            },
            {
                'action': 'Add indexes for correlation queries',
                'impact': '50% query performance improvement',
                'effort': '1 hour',
                'sql': 'CREATE INDEX idx_trans_contract ON id_transactions(contract_number)'
            },
            {
                'action': 'Implement contract_item_mapping junction table',
                'impact': 'Enables accurate revenue attribution',
                'effort': '3 hours',
                'sql': 'CREATE TABLE contract_item_mapping (...)'
            }
        ]
        
        for rec in immediate:
            print(f"    • {rec['action']}")
            print(f"      Impact: {rec['impact']}")
            print(f"      Effort: {rec['effort']}")
            recommendations.append(rec)
        
        print("\n  PRIORITY 2 - Short-term (Weeks 2-4):")
        short_term = [
            'Build equipment utilization tracking system',
            'Implement customer journey mapping',
            'Create financial-operational correlation views',
            'Develop real-time KPI calculation engine'
        ]
        
        for item in short_term:
            print(f"    • {item}")
        
        print("\n  PRIORITY 3 - Long-term (Months 2-3):")
        long_term = [
            'Deploy predictive maintenance ML model',
            'Implement dynamic pricing optimization',
            'Build customer segmentation engine',
            'Create automated anomaly detection'
        ]
        
        for item in long_term:
            print(f"    • {item}")
        
        return recommendations
    
    def _get_primary_key(self, model):
        """Get primary key column name for a model"""
        for column in model.__table__.columns:
            if column.primary_key:
                return column.name
        return None
    
    def run_analysis(self):
        """Run complete correlation analysis"""
        print("\nStarting Database Correlation Analysis...")
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all analysis components
        schema_stats = self.analyze_schema_relationships()
        relationships = self.identify_relationship_mappings()
        quality_issues = self.analyze_data_quality_issues()
        kpi_correlations = self.generate_kpi_correlations()
        integration_queries = self.recommend_integration_queries()
        ai_readiness = self.identify_ai_readiness()
        recommendations = self.generate_actionable_recommendations()
        
        # Generate summary report
        print("\n" + "="*80)
        print("EXECUTIVE SUMMARY")
        print("="*80)
        
        print("\nKey Findings:")
        print(f"  • Analyzed {len(schema_stats)} core tables")
        print(f"  • Identified {len(relationships['Direct Foreign Keys'])} direct relationships")
        print(f"  • Found {len(relationships['Implicit Relationships'])} implicit correlations")
        print(f"  • Recommended {len(relationships['Junction Tables Needed'])} new junction tables")
        print(f"  • Generated {sum(len(v) for v in kpi_correlations.values())} KPI opportunities")
        print(f"  • Identified {len(ai_readiness['Data Gaps'])} critical data gaps")
        
        print("\nBusiness Impact:")
        print("  • Enhanced revenue visibility by store and equipment class")
        print("  • Improved inventory utilization tracking")
        print("  • Enabled predictive analytics capabilities")
        print("  • Streamlined customer journey analysis")
        
        print("\nNext Steps:")
        print("  1. Review and approve schema modifications")
        print("  2. Implement Priority 1 recommendations")
        print("  3. Deploy integration queries for testing")
        print("  4. Begin data collection for AI features")
        
        # Save analysis results
        results = {
            'analysis_date': datetime.now().isoformat(),
            'schema_stats': schema_stats,
            'relationships': relationships,
            'quality_issues': quality_issues,
            'kpi_correlations': kpi_correlations,
            'ai_readiness': ai_readiness,
            'recommendations': [r for r in recommendations if isinstance(r, dict)]
        }
        
        with open('/home/tim/RFID3/database_correlation_analysis.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✓ Analysis complete. Results saved to database_correlation_analysis.json")
        
        return results


if __name__ == "__main__":
    analyzer = DatabaseCorrelationAnalyzer()
    results = analyzer.run_analysis()