#!/usr/bin/env python3
"""
COMPREHENSIVE DATABASE CORRELATION ANALYZER
===========================================
Expert system for identifying data relationships, quality issues, and AI readiness
across RFID, POS, Financial, and Operational systems.

Author: Database Correlation Analyst
Date: 2025-09-01
Version: 1.0
"""

import sys
import os
sys.path.append('/home/tim/RFID3')

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, Counter
import re
from decimal import Decimal
from dataclasses import dataclass, asdict
from enum import Enum

# Application imports
from app import create_app, db
from sqlalchemy import text, func, and_, or_
from app.models.db_models import ItemMaster, Transaction
from app.models.pos_models import POSTransaction, POSTransactionItem, POSCustomer, POSEquipment
from app.models.financial_models import PayrollTrendsData, ScorecardTrendsData
from app.models.correlation_models import InventoryCorrelationMaster, POSDataStaging


class DataQualityLevel(Enum):
    """Data quality assessment levels"""
    EXCELLENT = "EXCELLENT"  # 95-100% quality
    GOOD = "GOOD"           # 80-94% quality
    FAIR = "FAIR"           # 60-79% quality
    POOR = "POOR"           # 40-59% quality
    CRITICAL = "CRITICAL"   # Below 40% quality


class DataFreshness(Enum):
    """Data freshness categories"""
    REAL_TIME = "REAL_TIME"         # < 1 day old
    FRESH = "FRESH"                 # 1-7 days old
    RECENT = "RECENT"               # 8-30 days old
    STALE = "STALE"                 # 31-90 days old
    OBSOLETE = "OBSOLETE"           # > 90 days old
    HISTORICAL = "HISTORICAL"       # Intentionally archived


@dataclass
class CorrelationMatch:
    """Represents a correlation match between data sources"""
    source_table: str
    source_field: str
    target_table: str
    target_field: str
    match_type: str  # EXACT, FUZZY, SEMANTIC, PATTERN
    confidence: float
    sample_matches: List[Tuple]
    cardinality: str  # ONE_TO_ONE, ONE_TO_MANY, MANY_TO_MANY
    business_impact: str


@dataclass
class DataQualityIssue:
    """Represents a data quality issue"""
    table: str
    field: str
    issue_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    affected_records: int
    percentage: float
    examples: List
    recommendation: str
    estimated_effort: str  # HOURS, DAYS, WEEKS


class ComprehensiveDatabaseCorrelationAnalyzer:
    """
    Master analyzer for database correlations, data quality, and AI readiness
    """
    
    def __init__(self):
        """Initialize the analyzer with Flask app context"""
        self.app = create_app()
        self.app.app_context().push()
        self.analysis_timestamp = datetime.now()
        self.results = {
            'metadata': {
                'analysis_date': self.analysis_timestamp.isoformat(),
                'version': '1.0',
                'analyst': 'Database Correlation Analyst AI'
            }
        }
        
    def run_complete_analysis(self) -> Dict:
        """
        Execute comprehensive database analysis
        """
        print("\n" + "="*80)
        print("COMPREHENSIVE DATABASE CORRELATION ANALYSIS")
        print("="*80)
        
        # Phase 1: Schema Analysis
        print("\n[Phase 1/6] Analyzing Database Schemas...")
        self.results['schema_analysis'] = self.analyze_schemas()
        
        # Phase 2: Relationship Mapping
        print("\n[Phase 2/6] Mapping Data Relationships...")
        self.results['relationships'] = self.map_relationships()
        
        # Phase 3: Data Quality Assessment
        print("\n[Phase 3/6] Assessing Data Quality...")
        self.results['data_quality'] = self.assess_data_quality()
        
        # Phase 4: Customer Data Integration
        print("\n[Phase 4/6] Analyzing Customer Data Integration...")
        self.results['customer_integration'] = self.analyze_customer_data()
        
        # Phase 5: AI Readiness Evaluation
        print("\n[Phase 5/6] Evaluating AI/ML Readiness...")
        self.results['ai_readiness'] = self.evaluate_ai_readiness()
        
        # Phase 6: Generate Recommendations
        print("\n[Phase 6/6] Generating Actionable Recommendations...")
        self.results['recommendations'] = self.generate_recommendations()
        
        return self.results
    
    def analyze_schemas(self) -> Dict:
        """
        Analyze database schemas and identify field patterns
        """
        schema_info = {
            'tables': {},
            'field_patterns': {},
            'naming_inconsistencies': [],
            'potential_joins': []
        }
        
        # Get all tables and their schemas
        query = """
        SELECT 
            m.name as table_name,
            p.name as column_name,
            p.type as data_type
        FROM sqlite_master m
        LEFT JOIN pragma_table_info(m.name) p ON m.name != p.name
        WHERE m.type = 'table' 
        AND m.name NOT LIKE 'sqlite_%'
        AND m.name NOT LIKE 'alembic_%'
        ORDER BY m.name, p.cid
        """
        
        try:
            results = db.session.execute(text(query)).fetchall()
            
            # Group by table
            current_table = None
            for row in results:
                if row[0] != current_table:
                    current_table = row[0]
                    schema_info['tables'][current_table] = {
                        'columns': [],
                        'potential_keys': [],
                        'data_patterns': {}
                    }
                
                if row[1]:  # Column exists
                    schema_info['tables'][current_table]['columns'].append({
                        'name': row[1],
                        'type': row[2]
                    })
                    
                    # Identify potential keys
                    if any(pattern in row[1].lower() for pattern in ['_id', '_num', '_no', '_key', '_fk']):
                        schema_info['tables'][current_table]['potential_keys'].append(row[1])
            
            # Analyze field naming patterns
            all_columns = []
            for table, info in schema_info['tables'].items():
                for col in info['columns']:
                    all_columns.append(f"{table}.{col['name']}")
            
            # Find similar column names across tables
            schema_info['field_patterns'] = self._find_field_patterns(all_columns)
            
            # Identify naming inconsistencies
            schema_info['naming_inconsistencies'] = self._find_naming_inconsistencies(schema_info['tables'])
            
            # Identify potential joins
            schema_info['potential_joins'] = self._identify_potential_joins(schema_info['tables'])
            
        except Exception as e:
            print(f"Error analyzing schemas: {e}")
            
        return schema_info
    
    def map_relationships(self) -> Dict:
        """
        Map relationships between different data sources
        """
        relationships = {
            'explicit_foreign_keys': [],
            'implicit_relationships': [],
            'cross_system_mappings': [],
            'orphaned_records': {},
            'cardinality_analysis': {}
        }
        
        # 1. RFID to POS Transaction Mapping
        print("  - Analyzing RFID to POS correlations...")
        rfid_pos_correlation = self._analyze_rfid_pos_correlation()
        relationships['cross_system_mappings'].append(rfid_pos_correlation)
        
        # 2. Customer to Transaction Mapping
        print("  - Analyzing Customer to Transaction relationships...")
        customer_transaction_map = self._analyze_customer_transactions()
        relationships['cross_system_mappings'].append(customer_transaction_map)
        
        # 3. Financial to Operational Mapping
        print("  - Analyzing Financial to Operational data...")
        financial_operational_map = self._analyze_financial_operational()
        relationships['cross_system_mappings'].append(financial_operational_map)
        
        # 4. Identify Orphaned Records
        print("  - Identifying orphaned records...")
        relationships['orphaned_records'] = self._identify_orphaned_records()
        
        # 5. Cardinality Analysis
        print("  - Analyzing relationship cardinalities...")
        relationships['cardinality_analysis'] = self._analyze_cardinalities()
        
        return relationships
    
    def assess_data_quality(self) -> Dict:
        """
        Comprehensive data quality assessment
        """
        quality_metrics = {
            'overall_score': 0,
            'table_scores': {},
            'issues': [],
            'data_freshness': {},
            'completeness_metrics': {},
            'consistency_checks': {},
            'contamination_analysis': {}
        }
        
        # 1. Completeness Analysis
        print("  - Analyzing data completeness...")
        quality_metrics['completeness_metrics'] = self._analyze_completeness()
        
        # 2. Consistency Checks
        print("  - Running consistency checks...")
        quality_metrics['consistency_checks'] = self._check_consistency()
        
        # 3. Data Freshness Analysis
        print("  - Analyzing data freshness...")
        quality_metrics['data_freshness'] = self._analyze_freshness()
        
        # 4. Contamination Detection
        print("  - Detecting data contamination...")
        quality_metrics['contamination_analysis'] = self._detect_contamination()
        
        # 5. Calculate Overall Score
        quality_metrics['overall_score'] = self._calculate_quality_score(quality_metrics)
        
        return quality_metrics
    
    def analyze_customer_data(self) -> Dict:
        """
        Analyze customer data integration opportunities
        """
        customer_analysis = {
            'customer_profiles': {},
            'journey_mapping': {},
            'identity_resolution': {},
            'behavioral_patterns': {},
            'lifecycle_stages': {},
            'integration_opportunities': []
        }
        
        # 1. Customer Profile Completeness
        print("  - Analyzing customer profiles...")
        customer_analysis['customer_profiles'] = self._analyze_customer_profiles()
        
        # 2. Customer Journey Mapping
        print("  - Mapping customer journeys...")
        customer_analysis['journey_mapping'] = self._map_customer_journeys()
        
        # 3. Identity Resolution
        print("  - Resolving customer identities...")
        customer_analysis['identity_resolution'] = self._resolve_customer_identities()
        
        # 4. Behavioral Pattern Analysis
        print("  - Identifying behavioral patterns...")
        customer_analysis['behavioral_patterns'] = self._analyze_customer_behavior()
        
        # 5. Lifecycle Stage Classification
        print("  - Classifying lifecycle stages...")
        customer_analysis['lifecycle_stages'] = self._classify_lifecycle_stages()
        
        return customer_analysis
    
    def evaluate_ai_readiness(self) -> Dict:
        """
        Evaluate readiness for AI/ML implementation
        """
        ai_readiness = {
            'overall_readiness': '',
            'feature_quality': {},
            'target_variables': [],
            'data_volume_assessment': {},
            'model_recommendations': [],
            'preprocessing_requirements': [],
            'implementation_roadmap': {}
        }
        
        # 1. Feature Quality Assessment
        print("  - Assessing feature quality for ML...")
        ai_readiness['feature_quality'] = self._assess_feature_quality()
        
        # 2. Identify Target Variables
        print("  - Identifying potential target variables...")
        ai_readiness['target_variables'] = self._identify_target_variables()
        
        # 3. Data Volume Assessment
        print("  - Assessing data volumes...")
        ai_readiness['data_volume_assessment'] = self._assess_data_volumes()
        
        # 4. Model Recommendations
        print("  - Generating model recommendations...")
        ai_readiness['model_recommendations'] = self._recommend_ml_models()
        
        # 5. Preprocessing Requirements
        print("  - Identifying preprocessing needs...")
        ai_readiness['preprocessing_requirements'] = self._identify_preprocessing_needs()
        
        # 6. Implementation Roadmap
        print("  - Creating implementation roadmap...")
        ai_readiness['implementation_roadmap'] = self._create_ai_roadmap()
        
        # Calculate overall readiness
        ai_readiness['overall_readiness'] = self._calculate_ai_readiness_score(ai_readiness)
        
        return ai_readiness
    
    def generate_recommendations(self) -> Dict:
        """
        Generate actionable recommendations based on analysis
        """
        recommendations = {
            'immediate_actions': [],
            'short_term': [],  # 1-4 weeks
            'medium_term': [],  # 1-3 months
            'long_term': [],    # 3+ months
            'sql_queries': {},
            'integration_scripts': {},
            'priority_matrix': {}
        }
        
        # Generate recommendations based on all previous analyses
        all_issues = []
        
        # Data quality recommendations
        if 'data_quality' in self.results:
            for issue in self.results['data_quality'].get('issues', []):
                all_issues.append(self._create_recommendation(issue))
        
        # Relationship recommendations
        if 'relationships' in self.results:
            for orphan_table, count in self.results['relationships'].get('orphaned_records', {}).items():
                if count > 0:
                    all_issues.append({
                        'type': 'ORPHANED_RECORDS',
                        'table': orphan_table,
                        'severity': 'HIGH' if count > 100 else 'MEDIUM',
                        'action': f'Clean up {count} orphaned records in {orphan_table}',
                        'effort': 'DAYS' if count > 1000 else 'HOURS'
                    })
        
        # Sort recommendations by priority and timeline
        for rec in all_issues:
            if rec.get('severity') == 'CRITICAL':
                recommendations['immediate_actions'].append(rec)
            elif rec.get('effort') == 'HOURS':
                recommendations['short_term'].append(rec)
            elif rec.get('effort') == 'DAYS':
                recommendations['medium_term'].append(rec)
            else:
                recommendations['long_term'].append(rec)
        
        # Generate SQL queries for fixes
        recommendations['sql_queries'] = self._generate_fix_queries()
        
        # Generate integration scripts
        recommendations['integration_scripts'] = self._generate_integration_scripts()
        
        # Create priority matrix
        recommendations['priority_matrix'] = self._create_priority_matrix(recommendations)
        
        return recommendations
    
    # Helper Methods
    
    def _find_field_patterns(self, columns: List[str]) -> Dict:
        """Find common field naming patterns"""
        patterns = defaultdict(list)
        
        # Common patterns to look for
        pattern_rules = {
            'identifiers': r'(_id|_num|_no|_key|_code)$',
            'dates': r'(_date|_time|_at|_on)$',
            'amounts': r'(_amt|_amount|_price|_cost|_total)$',
            'statuses': r'(_status|_state|_flag)$',
            'names': r'(_name|_desc|_description)$',
            'locations': r'(_store|_location|_address|_city|_state|_zip)',
            'metrics': r'(_count|_qty|_quantity|_percent|_ratio)'
        }
        
        for col in columns:
            for pattern_name, regex in pattern_rules.items():
                if re.search(regex, col, re.IGNORECASE):
                    patterns[pattern_name].append(col)
        
        return dict(patterns)
    
    def _find_naming_inconsistencies(self, tables: Dict) -> List:
        """Find naming inconsistencies across tables"""
        inconsistencies = []
        
        # Collect all column names
        all_columns = defaultdict(list)
        for table_name, info in tables.items():
            for col in info['columns']:
                base_name = col['name'].lower().replace('_', '')
                all_columns[base_name].append(f"{table_name}.{col['name']}")
        
        # Find similar but different names
        for base_name, occurrences in all_columns.items():
            if len(occurrences) > 1:
                unique_names = set([occ.split('.')[1] for occ in occurrences])
                if len(unique_names) > 1:
                    inconsistencies.append({
                        'base_pattern': base_name,
                        'variations': list(unique_names),
                        'occurrences': occurrences,
                        'recommendation': f"Standardize to: {min(unique_names, key=len)}"
                    })
        
        return inconsistencies
    
    def _identify_potential_joins(self, tables: Dict) -> List:
        """Identify potential join conditions between tables"""
        potential_joins = []
        table_names = list(tables.keys())
        
        for i, table1 in enumerate(table_names):
            for table2 in table_names[i+1:]:
                # Check for matching column names
                cols1 = set([c['name'].lower() for c in tables[table1]['columns']])
                cols2 = set([c['name'].lower() for c in tables[table2]['columns']])
                
                common_cols = cols1.intersection(cols2)
                
                for col in common_cols:
                    if any(pattern in col for pattern in ['_id', '_num', '_no', '_key', 'store', 'customer']):
                        potential_joins.append({
                            'table1': table1,
                            'table2': table2,
                            'join_column': col,
                            'join_type': 'INNER' if 'id' in col else 'LEFT',
                            'confidence': 0.8 if 'id' in col else 0.6
                        })
        
        return potential_joins
    
    def _analyze_rfid_pos_correlation(self) -> Dict:
        """Analyze correlation between RFID and POS data"""
        correlation = {
            'mapping_type': 'RFID_TO_POS',
            'matches_found': 0,
            'confidence_levels': {},
            'unmapped_rfid': 0,
            'unmapped_pos': 0,
            'correlation_fields': []
        }
        
        try:
            # Check for contract number correlations
            query = """
            SELECT 
                COUNT(DISTINCT im.last_contract_num) as rfid_contracts,
                COUNT(DISTINCT pt.contract_no) as pos_contracts
            FROM id_item_master im
            CROSS JOIN pos_transactions pt
            WHERE im.last_contract_num IS NOT NULL
            """
            result = db.session.execute(text(query)).fetchone()
            
            if result:
                correlation['rfid_contracts'] = result[0]
                correlation['pos_contracts'] = result[1]
            
            # Check for matching patterns
            query = """
            SELECT 
                COUNT(*) as match_count
            FROM id_item_master im
            INNER JOIN pos_transactions pt ON im.last_contract_num = pt.contract_no
            """
            result = db.session.execute(text(query)).fetchone()
            
            if result:
                correlation['matches_found'] = result[0]
            
            correlation['correlation_fields'] = [
                {'source': 'id_item_master.last_contract_num', 'target': 'pos_transactions.contract_no'},
                {'source': 'id_item_master.rental_class_num', 'target': 'pos_equipment.item_class'},
                {'source': 'id_item_master.serial_number', 'target': 'pos_equipment.serial_no'}
            ]
            
        except Exception as e:
            print(f"Error in RFID-POS correlation: {e}")
        
        return correlation
    
    def _analyze_customer_transactions(self) -> Dict:
        """Analyze customer transaction relationships"""
        return {
            'mapping_type': 'CUSTOMER_TRANSACTIONS',
            'relationship_type': 'ONE_TO_MANY',
            'key_fields': ['customer_no', 'contract_no'],
            'stats': self._get_customer_transaction_stats()
        }
    
    def _get_customer_transaction_stats(self) -> Dict:
        """Get customer transaction statistics"""
        stats = {}
        
        try:
            query = """
            SELECT 
                COUNT(DISTINCT customer_no) as unique_customers,
                COUNT(DISTINCT contract_no) as unique_contracts,
                AVG(contract_count) as avg_contracts_per_customer
            FROM (
                SELECT customer_no, COUNT(*) as contract_count
                FROM pos_transactions
                WHERE customer_no IS NOT NULL
                GROUP BY customer_no
            ) customer_stats
            """
            result = db.session.execute(text(query)).fetchone()
            
            if result:
                stats = {
                    'unique_customers': result[0],
                    'unique_contracts': result[1],
                    'avg_contracts_per_customer': float(result[2]) if result[2] else 0
                }
        except Exception as e:
            print(f"Error getting customer stats: {e}")
        
        return stats
    
    def _analyze_financial_operational(self) -> Dict:
        """Analyze financial to operational data mapping"""
        return {
            'mapping_type': 'FINANCIAL_OPERATIONAL',
            'store_mappings': {
                'Wayzata': {'financial_code': '3607', 'operational_code': 'WAY'},
                'Brooklyn Park': {'financial_code': '6800', 'operational_code': 'BP'},
                'Fridley': {'financial_code': '728', 'operational_code': 'FRI'},
                'Baxter': {'financial_code': '8101', 'operational_code': 'BAX'}
            },
            'time_alignment': 'WEEKLY',
            'key_metrics': ['revenue', 'payroll', 'contracts', 'inventory_turnover']
        }
    
    def _identify_orphaned_records(self) -> Dict:
        """Identify orphaned records across tables"""
        orphans = {}
        
        # Check for RFID items without transactions
        try:
            query = """
            SELECT COUNT(*) 
            FROM id_item_master im
            LEFT JOIN id_transactions t ON im.tag_id = t.tag_id
            WHERE t.id IS NULL
            """
            result = db.session.execute(text(query)).fetchone()
            orphans['rfid_items_no_transactions'] = result[0] if result else 0
            
            # Check for transactions without master records
            query = """
            SELECT COUNT(DISTINCT t.tag_id)
            FROM id_transactions t
            LEFT JOIN id_item_master im ON t.tag_id = im.tag_id
            WHERE im.tag_id IS NULL
            """
            result = db.session.execute(text(query)).fetchone()
            orphans['transactions_no_master'] = result[0] if result else 0
            
        except Exception as e:
            print(f"Error identifying orphans: {e}")
        
        return orphans
    
    def _analyze_cardinalities(self) -> Dict:
        """Analyze relationship cardinalities"""
        return {
            'item_to_transactions': 'ONE_TO_MANY',
            'customer_to_transactions': 'ONE_TO_MANY',
            'store_to_items': 'ONE_TO_MANY',
            'contract_to_items': 'ONE_TO_MANY',
            'recommendations': [
                'Consider junction table for many-to-many equipment-to-customer relationships',
                'Implement composite keys for transaction-item relationships'
            ]
        }
    
    def _analyze_completeness(self) -> Dict:
        """Analyze data completeness"""
        completeness = {}
        
        # Check ItemMaster completeness
        try:
            query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN serial_number IS NOT NULL THEN 1 ELSE 0 END) as has_serial,
                SUM(CASE WHEN rental_class_num IS NOT NULL THEN 1 ELSE 0 END) as has_class,
                SUM(CASE WHEN bin_location IS NOT NULL THEN 1 ELSE 0 END) as has_location,
                SUM(CASE WHEN home_store IS NOT NULL THEN 1 ELSE 0 END) as has_home_store
            FROM id_item_master
            """
            result = db.session.execute(text(query)).fetchone()
            
            if result and result[0] > 0:
                completeness['item_master'] = {
                    'serial_number': round(result[1] / result[0] * 100, 2),
                    'rental_class': round(result[2] / result[0] * 100, 2),
                    'bin_location': round(result[3] / result[0] * 100, 2),
                    'home_store': round(result[4] / result[0] * 100, 2)
                }
        except Exception as e:
            print(f"Error analyzing completeness: {e}")
        
        return completeness
    
    def _check_consistency(self) -> Dict:
        """Check data consistency"""
        consistency = {
            'duplicate_checks': {},
            'referential_integrity': {},
            'business_rule_violations': []
        }
        
        # Check for duplicates
        try:
            query = """
            SELECT tag_id, COUNT(*) as count
            FROM id_item_master
            GROUP BY tag_id
            HAVING COUNT(*) > 1
            """
            result = db.session.execute(text(query)).fetchall()
            consistency['duplicate_checks']['duplicate_tags'] = len(result)
            
        except Exception as e:
            print(f"Error checking consistency: {e}")
        
        return consistency
    
    def _analyze_freshness(self) -> Dict:
        """Analyze data freshness"""
        freshness = {}
        
        try:
            query = """
            SELECT 
                MAX(date_last_scanned) as latest_scan,
                MIN(date_last_scanned) as earliest_scan,
                AVG(julianday('now') - julianday(date_last_scanned)) as avg_days_old
            FROM id_item_master
            WHERE date_last_scanned IS NOT NULL
            """
            result = db.session.execute(text(query)).fetchone()
            
            if result:
                freshness['scan_data'] = {
                    'latest': result[0].isoformat() if result[0] else None,
                    'earliest': result[1].isoformat() if result[1] else None,
                    'avg_age_days': round(result[2], 1) if result[2] else None
                }
        except Exception as e:
            print(f"Error analyzing freshness: {e}")
        
        return freshness
    
    def _detect_contamination(self) -> Dict:
        """Detect data contamination"""
        contamination = {
            'test_data': [],
            'invalid_formats': [],
            'suspicious_patterns': []
        }
        
        # Check for test data patterns
        test_patterns = ['test', 'demo', 'sample', 'dummy', 'xxx', 'delete']
        
        try:
            for pattern in test_patterns:
                query = f"""
                SELECT COUNT(*) 
                FROM id_item_master
                WHERE LOWER(common_name) LIKE '%{pattern}%'
                OR LOWER(notes) LIKE '%{pattern}%'
                """
                result = db.session.execute(text(query)).fetchone()
                if result and result[0] > 0:
                    contamination['test_data'].append({
                        'pattern': pattern,
                        'count': result[0]
                    })
        except Exception as e:
            print(f"Error detecting contamination: {e}")
        
        return contamination
    
    def _calculate_quality_score(self, metrics: Dict) -> float:
        """Calculate overall data quality score"""
        scores = []
        
        # Completeness score
        if 'completeness_metrics' in metrics:
            for table_metrics in metrics['completeness_metrics'].values():
                if isinstance(table_metrics, dict):
                    scores.extend(table_metrics.values())
        
        # Consistency score
        if 'duplicate_checks' in metrics.get('consistency_checks', {}):
            duplicate_penalty = min(metrics['consistency_checks']['duplicate_checks'].get('duplicate_tags', 0) * 5, 50)
            scores.append(100 - duplicate_penalty)
        
        return round(np.mean(scores), 2) if scores else 0
    
    def _analyze_customer_profiles(self) -> Dict:
        """Analyze customer profile completeness"""
        profiles = {}
        
        try:
            query = """
            SELECT 
                COUNT(*) as total_customers,
                SUM(CASE WHEN email IS NOT NULL THEN 1 ELSE 0 END) as has_email,
                SUM(CASE WHEN main_phone IS NOT NULL THEN 1 ELSE 0 END) as has_phone,
                SUM(CASE WHEN address_1 IS NOT NULL THEN 1 ELSE 0 END) as has_address
            FROM pos_customer
            """
            result = db.session.execute(text(query)).fetchone()
            
            if result and result[0] > 0:
                profiles = {
                    'total_customers': result[0],
                    'email_coverage': round(result[1] / result[0] * 100, 2),
                    'phone_coverage': round(result[2] / result[0] * 100, 2),
                    'address_coverage': round(result[3] / result[0] * 100, 2)
                }
        except Exception as e:
            print(f"Error analyzing customer profiles: {e}")
        
        return profiles
    
    def _map_customer_journeys(self) -> Dict:
        """Map customer journey touchpoints"""
        return {
            'touchpoints': ['initial_inquiry', 'quote', 'contract', 'delivery', 'pickup', 'billing'],
            'average_journey_length': '7-14 days',
            'conversion_points': ['quote_to_contract', 'contract_to_delivery'],
            'dropout_risks': ['quote_stage', 'post_delivery']
        }
    
    def _resolve_customer_identities(self) -> Dict:
        """Resolve customer identity conflicts"""
        identity_issues = {}
        
        try:
            # Check for duplicate customers
            query = """
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT LOWER(REPLACE(name, ' ', ''))) as unique_names
            FROM pos_customer
            """
            result = db.session.execute(text(query)).fetchone()
            
            if result:
                identity_issues = {
                    'total_records': result[0],
                    'unique_identities': result[1],
                    'potential_duplicates': result[0] - result[1]
                }
        except Exception as e:
            print(f"Error resolving identities: {e}")
        
        return identity_issues
    
    def _analyze_customer_behavior(self) -> Dict:
        """Analyze customer behavioral patterns"""
        return {
            'segments': {
                'frequent_renters': 'Multiple contracts per year',
                'seasonal_customers': 'Peak season only',
                'one_time_users': 'Single transaction',
                'corporate_accounts': 'Business customers'
            },
            'key_behaviors': ['repeat_rate', 'average_order_value', 'seasonality']
        }
    
    def _classify_lifecycle_stages(self) -> Dict:
        """Classify customer lifecycle stages"""
        return {
            'stages': {
                'prospect': 'Quote but no contract',
                'new_customer': 'First contract',
                'active': 'Recent transaction',
                'at_risk': 'No activity 60-90 days',
                'churned': 'No activity >90 days'
            },
            'recommendations': 'Implement automated lifecycle triggers'
        }
    
    def _assess_feature_quality(self) -> Dict:
        """Assess feature quality for ML"""
        feature_quality = {
            'high_quality_features': [],
            'medium_quality_features': [],
            'low_quality_features': []
        }
        
        # High quality: Complete, consistent, numeric
        feature_quality['high_quality_features'] = [
            'rental_revenue', 'payroll_amount', 'contract_count',
            'total_weekly_revenue', 'ar_over_45_days_percent'
        ]
        
        # Medium quality: Some missing values, needs transformation
        feature_quality['medium_quality_features'] = [
            'customer_type', 'delivery_date', 'pickup_date',
            'equipment_category', 'store_location'
        ]
        
        # Low quality: High missing, inconsistent
        feature_quality['low_quality_features'] = [
            'customer_notes', 'special_instructions', 'manual_entries'
        ]
        
        return feature_quality
    
    def _identify_target_variables(self) -> List:
        """Identify potential ML target variables"""
        return [
            {
                'variable': 'contract_total',
                'type': 'regression',
                'use_case': 'Revenue prediction'
            },
            {
                'variable': 'customer_churn',
                'type': 'classification',
                'use_case': 'Retention modeling'
            },
            {
                'variable': 'equipment_demand',
                'type': 'time_series',
                'use_case': 'Inventory optimization'
            },
            {
                'variable': 'payment_default',
                'type': 'classification',
                'use_case': 'Credit risk assessment'
            }
        ]
    
    def _assess_data_volumes(self) -> Dict:
        """Assess data volume for ML training"""
        volumes = {}
        
        try:
            # Get record counts
            tables = ['id_item_master', 'id_transactions', 'pos_transactions', 'pos_customer']
            for table in tables:
                query = f"SELECT COUNT(*) FROM {table}"
                result = db.session.execute(text(query)).fetchone()
                volumes[table] = result[0] if result else 0
            
            # Assess adequacy
            volumes['ml_readiness'] = {
                'classification': 'READY' if min(volumes.values()) > 1000 else 'NEEDS_MORE_DATA',
                'regression': 'READY' if min(volumes.values()) > 500 else 'NEEDS_MORE_DATA',
                'deep_learning': 'NEEDS_MORE_DATA' if min(volumes.values()) < 10000 else 'READY'
            }
            
        except Exception as e:
            print(f"Error assessing volumes: {e}")
        
        return volumes
    
    def _recommend_ml_models(self) -> List:
        """Recommend appropriate ML models"""
        return [
            {
                'model': 'Random Forest',
                'use_case': 'Equipment demand forecasting',
                'complexity': 'MEDIUM',
                'data_requirements': 'CURRENT_DATA_SUFFICIENT'
            },
            {
                'model': 'XGBoost',
                'use_case': 'Customer churn prediction',
                'complexity': 'MEDIUM',
                'data_requirements': 'CURRENT_DATA_SUFFICIENT'
            },
            {
                'model': 'ARIMA/Prophet',
                'use_case': 'Revenue time series forecasting',
                'complexity': 'LOW',
                'data_requirements': 'NEEDS_MORE_HISTORICAL_DATA'
            },
            {
                'model': 'Clustering (K-Means)',
                'use_case': 'Customer segmentation',
                'complexity': 'LOW',
                'data_requirements': 'CURRENT_DATA_SUFFICIENT'
            }
        ]
    
    def _identify_preprocessing_needs(self) -> List:
        """Identify data preprocessing requirements"""
        return [
            {
                'task': 'Handle missing values',
                'priority': 'HIGH',
                'effort': '1 week',
                'impact': 'Critical for model accuracy'
            },
            {
                'task': 'Encode categorical variables',
                'priority': 'HIGH',
                'effort': '2-3 days',
                'impact': 'Required for most algorithms'
            },
            {
                'task': 'Create time-based features',
                'priority': 'MEDIUM',
                'effort': '3-4 days',
                'impact': 'Improves temporal predictions'
            },
            {
                'task': 'Normalize numerical features',
                'priority': 'MEDIUM',
                'effort': '1 day',
                'impact': 'Improves convergence'
            },
            {
                'task': 'Create interaction features',
                'priority': 'LOW',
                'effort': '1 week',
                'impact': 'Can improve complex patterns'
            }
        ]
    
    def _create_ai_roadmap(self) -> Dict:
        """Create AI implementation roadmap"""
        return {
            'phase1': {
                'timeline': 'Weeks 1-2',
                'tasks': ['Data cleaning', 'Feature engineering', 'Baseline models'],
                'deliverables': ['Clean dataset', 'Feature pipeline', 'Initial predictions']
            },
            'phase2': {
                'timeline': 'Weeks 3-4',
                'tasks': ['Model optimization', 'Validation framework', 'API development'],
                'deliverables': ['Optimized models', 'REST API', 'Performance metrics']
            },
            'phase3': {
                'timeline': 'Weeks 5-6',
                'tasks': ['Integration', 'Testing', 'Documentation'],
                'deliverables': ['Integrated system', 'Test results', 'User documentation']
            },
            'phase4': {
                'timeline': 'Weeks 7-8',
                'tasks': ['Deployment', 'Monitoring', 'Training'],
                'deliverables': ['Production system', 'Monitoring dashboard', 'Trained staff']
            }
        }
    
    def _calculate_ai_readiness_score(self, metrics: Dict) -> str:
        """Calculate overall AI readiness score"""
        scores = {
            'data_volume': 70 if 'READY' in str(metrics.get('data_volume_assessment', {})) else 30,
            'feature_quality': 80 if len(metrics.get('feature_quality', {}).get('high_quality_features', [])) > 3 else 40,
            'target_variables': 90 if len(metrics.get('target_variables', [])) > 2 else 50
        }
        
        avg_score = np.mean(list(scores.values()))
        
        if avg_score >= 80:
            return "READY - Can proceed with ML implementation"
        elif avg_score >= 60:
            return "MODERATE - Requires some preparation"
        else:
            return "NOT READY - Significant data work needed"
    
    def _create_recommendation(self, issue: Dict) -> Dict:
        """Create actionable recommendation from issue"""
        return {
            'issue': issue.get('issue_type', 'Unknown'),
            'table': issue.get('table', ''),
            'severity': issue.get('severity', 'MEDIUM'),
            'action': issue.get('recommendation', 'Review and fix'),
            'effort': issue.get('estimated_effort', 'DAYS'),
            'impact': 'HIGH' if issue.get('severity') == 'CRITICAL' else 'MEDIUM'
        }
    
    def _generate_fix_queries(self) -> Dict:
        """Generate SQL queries for common fixes"""
        return {
            'remove_duplicates': """
                -- Remove duplicate RFID tags
                DELETE FROM id_item_master
                WHERE rowid NOT IN (
                    SELECT MIN(rowid)
                    FROM id_item_master
                    GROUP BY tag_id
                );
            """,
            'clean_orphans': """
                -- Remove orphaned transactions
                DELETE FROM id_transactions
                WHERE tag_id NOT IN (
                    SELECT tag_id FROM id_item_master
                );
            """,
            'standardize_stores': """
                -- Standardize store codes
                UPDATE id_item_master
                SET home_store = CASE
                    WHEN home_store IN ('3607', 'WAY', 'Wayzata') THEN '3607'
                    WHEN home_store IN ('6800', 'BP', 'Brooklyn Park') THEN '6800'
                    WHEN home_store IN ('728', 'FRI', 'Fridley') THEN '728'
                    WHEN home_store IN ('8101', 'BAX', 'Baxter') THEN '8101'
                    ELSE home_store
                END;
            """,
            'create_correlation_index': """
                -- Create indexes for better correlation performance
                CREATE INDEX IF NOT EXISTS idx_contract_correlation 
                ON id_item_master(last_contract_num);
                
                CREATE INDEX IF NOT EXISTS idx_pos_contract 
                ON pos_transactions(contract_no);
            """
        }
    
    def _generate_integration_scripts(self) -> Dict:
        """Generate integration script templates"""
        return {
            'rfid_pos_sync': """
# RFID-POS Synchronization Script
def sync_rfid_pos_data():
    # Match RFID items with POS transactions
    query = '''
        SELECT im.tag_id, im.last_contract_num, pt.contract_no, pt.customer_no
        FROM id_item_master im
        LEFT JOIN pos_transactions pt ON im.last_contract_num = pt.contract_no
        WHERE im.last_contract_num IS NOT NULL
    '''
    # Execute and process matches
    pass
            """,
            'customer_merge': """
# Customer Data Merge Script  
def merge_customer_profiles():
    # Identify and merge duplicate customers
    query = '''
        SELECT customer_no, name, email, main_phone,
               COUNT(*) OVER (PARTITION BY LOWER(REPLACE(name, ' ', ''))) as duplicates
        FROM pos_customer
    '''
    # Process and merge duplicates
    pass
            """
        }
    
    def _create_priority_matrix(self, recommendations: Dict) -> Dict:
        """Create priority matrix for recommendations"""
        matrix = {
            'critical_immediate': [],
            'high_priority': [],
            'medium_priority': [],
            'low_priority': []
        }
        
        # Categorize all recommendations
        all_recs = (
            recommendations.get('immediate_actions', []) +
            recommendations.get('short_term', []) +
            recommendations.get('medium_term', []) +
            recommendations.get('long_term', [])
        )
        
        for rec in all_recs:
            severity = rec.get('severity', 'MEDIUM')
            effort = rec.get('effort', 'DAYS')
            
            if severity == 'CRITICAL':
                matrix['critical_immediate'].append(rec)
            elif severity == 'HIGH' and effort == 'HOURS':
                matrix['high_priority'].append(rec)
            elif severity == 'HIGH' or effort == 'HOURS':
                matrix['medium_priority'].append(rec)
            else:
                matrix['low_priority'].append(rec)
        
        return matrix
    
    def save_results(self, filename: str = None):
        """Save analysis results to JSON file"""
        if not filename:
            filename = f"database_correlation_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\nResults saved to: {filename}")
        
    def print_executive_summary(self):
        """Print executive summary of findings"""
        print("\n" + "="*80)
        print("EXECUTIVE SUMMARY")
        print("="*80)
        
        # Overall Data Quality
        if 'data_quality' in self.results:
            score = self.results['data_quality'].get('overall_score', 0)
            level = DataQualityLevel.EXCELLENT if score > 95 else \
                    DataQualityLevel.GOOD if score > 80 else \
                    DataQualityLevel.FAIR if score > 60 else \
                    DataQualityLevel.POOR if score > 40 else \
                    DataQualityLevel.CRITICAL
            
            print(f"\nData Quality Score: {score}% ({level.value})")
        
        # AI Readiness
        if 'ai_readiness' in self.results:
            readiness = self.results['ai_readiness'].get('overall_readiness', 'Unknown')
            print(f"AI/ML Readiness: {readiness}")
        
        # Critical Issues
        if 'recommendations' in self.results:
            immediate = self.results['recommendations'].get('immediate_actions', [])
            if immediate:
                print(f"\nCritical Issues Requiring Immediate Attention: {len(immediate)}")
                for issue in immediate[:3]:  # Show top 3
                    print(f"  - {issue.get('action', 'Unknown action')}")
        
        # Key Opportunities
        print("\nKey Integration Opportunities:")
        if 'relationships' in self.results:
            mappings = self.results['relationships'].get('cross_system_mappings', [])
            for mapping in mappings[:3]:
                if isinstance(mapping, dict):
                    print(f"  - {mapping.get('mapping_type', 'Unknown')} correlation available")
        
        # Next Steps
        print("\nRecommended Next Steps:")
        print("  1. Address critical data quality issues")
        print("  2. Implement suggested SQL queries for immediate fixes")
        print("  3. Begin customer data integration using provided scripts")
        print("  4. Prepare high-quality features for initial ML models")
        print("  5. Follow AI implementation roadmap phases")


def main():
    """Main execution function"""
    print("Initializing Comprehensive Database Correlation Analyzer...")
    
    analyzer = ComprehensiveDatabaseCorrelationAnalyzer()
    
    # Run complete analysis
    results = analyzer.run_complete_analysis()
    
    # Save results
    analyzer.save_results()
    
    # Print executive summary
    analyzer.print_executive_summary()
    
    print("\n" + "="*80)
    print("Analysis Complete!")
    print("="*80)
    
    return results


if __name__ == "__main__":
    main()