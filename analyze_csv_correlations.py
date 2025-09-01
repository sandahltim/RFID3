#!/usr/bin/env python3
"""
CSV Data Correlation Analysis
Analyzes CSV files to identify data relationships and quality issues
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import re

class CSVCorrelationAnalyzer:
    """Analyze CSV files for data correlations and quality"""
    
    def __init__(self):
        self.csv_path = Path('/home/tim/RFID3/shared/POR')
        self.rfid_path = Path('/home/tim/RFID3/shared')
        self.results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'files_analyzed': []
        }
        
    def analyze_all_csv_files(self) -> Dict:
        """Analyze all CSV files in the system"""
        print("\n" + "="*80)
        print("CSV DATA CORRELATION ANALYSIS")
        print("="*80)
        
        # Load and analyze POS CSV files
        print("\n[Phase 1] Loading POS Data Files...")
        pos_data = self.load_pos_data()
        
        # Load and analyze RFID data
        print("\n[Phase 2] Loading RFID Data Files...")
        rfid_data = self.load_rfid_data()
        
        # Analyze data structures
        print("\n[Phase 3] Analyzing Data Structures...")
        self.results['data_structures'] = self.analyze_data_structures(pos_data, rfid_data)
        
        # Find correlations
        print("\n[Phase 4] Finding Data Correlations...")
        self.results['correlations'] = self.find_correlations(pos_data, rfid_data)
        
        # Assess data quality
        print("\n[Phase 5] Assessing Data Quality...")
        self.results['data_quality'] = self.assess_data_quality(pos_data, rfid_data)
        
        # Generate recommendations
        print("\n[Phase 6] Generating Recommendations...")
        self.results['recommendations'] = self.generate_recommendations()
        
        return self.results
    
    def load_pos_data(self) -> Dict:
        """Load POS CSV files"""
        pos_data = {}
        
        csv_files = {
            'customers': 'customer8.26.25.csv',
            'equipment': 'equip8.26.25.csv',
            'transactions': 'transactions8.26.25.csv',
            'trans_items': 'transitems8.26.25.csv',
            'payroll': 'PayrollTrends8.26.25.csv',
            'pl_data': 'PL8.28.25.csv',
            'scorecard': 'ScorecardTrends9.1.25.csv'
        }
        
        for key, filename in csv_files.items():
            filepath = self.csv_path / filename
            if filepath.exists():
                try:
                    print(f"  Loading {filename}...")
                    df = pd.read_csv(filepath, low_memory=False, nrows=10000)  # Sample for analysis
                    pos_data[key] = df
                    self.results['files_analyzed'].append(str(filepath))
                    print(f"    Loaded {len(df)} rows, {len(df.columns)} columns")
                except Exception as e:
                    print(f"    Error loading {filename}: {e}")
            else:
                print(f"  File not found: {filename}")
        
        return pos_data
    
    def load_rfid_data(self) -> Dict:
        """Load RFID CSV files"""
        rfid_data = {}
        
        csv_files = {
            'rfid_tags': 'rfid_tags.csv',
            'item_list': '../POR/itemlistRFIDpro8.26.25.csv',
            'seed_data': '../POR/seeddataRFIDpro8.29.25.csv',
            'rfid_transactions': '../POR/transactionsRFIDpro8.29.25.csv'
        }
        
        for key, filename in csv_files.items():
            filepath = self.rfid_path / filename
            if filepath.exists():
                try:
                    print(f"  Loading {filename}...")
                    df = pd.read_csv(filepath, low_memory=False, nrows=10000)  # Sample for analysis
                    rfid_data[key] = df
                    self.results['files_analyzed'].append(str(filepath))
                    print(f"    Loaded {len(df)} rows, {len(df.columns)} columns")
                except Exception as e:
                    print(f"    Error loading {filename}: {e}")
            else:
                print(f"  File not found: {filename}")
        
        return rfid_data
    
    def analyze_data_structures(self, pos_data: Dict, rfid_data: Dict) -> Dict:
        """Analyze data structures and schemas"""
        structures = {}
        
        # Analyze POS data structures
        for name, df in pos_data.items():
            if isinstance(df, pd.DataFrame):
                structures[f'pos_{name}'] = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'column_names': df.columns.tolist()[:20],  # First 20 columns
                    'dtypes': {str(k): v for k, v in df.dtypes.value_counts().to_dict().items()},
                    'null_counts': df.isnull().sum().to_dict() if len(df) < 5000 else {},
                    'potential_keys': self.identify_potential_keys(df)
                }
        
        # Analyze RFID data structures
        for name, df in rfid_data.items():
            if isinstance(df, pd.DataFrame):
                structures[f'rfid_{name}'] = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'column_names': df.columns.tolist()[:20],
                    'dtypes': {str(k): v for k, v in df.dtypes.value_counts().to_dict().items()},
                    'null_counts': df.isnull().sum().to_dict() if len(df) < 5000 else {},
                    'potential_keys': self.identify_potential_keys(df)
                }
        
        return structures
    
    def identify_potential_keys(self, df: pd.DataFrame) -> List[str]:
        """Identify potential key columns"""
        potential_keys = []
        
        for col in df.columns:
            col_lower = col.lower()
            # Look for common key patterns
            if any(pattern in col_lower for pattern in ['_id', '_num', '_no', '_key', 'code']):
                # Check uniqueness
                if len(df[col].dropna().unique()) / len(df[col].dropna()) > 0.9:
                    potential_keys.append(col)
        
        return potential_keys[:5]  # Return top 5 potential keys
    
    def find_correlations(self, pos_data: Dict, rfid_data: Dict) -> Dict:
        """Find correlations between datasets"""
        correlations = {
            'exact_matches': [],
            'fuzzy_matches': [],
            'cross_references': []
        }
        
        # Find exact column name matches
        pos_columns = set()
        for df in pos_data.values():
            if isinstance(df, pd.DataFrame):
                pos_columns.update(df.columns)
        
        rfid_columns = set()
        for df in rfid_data.values():
            if isinstance(df, pd.DataFrame):
                rfid_columns.update(df.columns)
        
        # Exact matches
        exact_matches = pos_columns.intersection(rfid_columns)
        correlations['exact_matches'] = list(exact_matches)
        
        # Find fuzzy matches (similar column names)
        for pos_col in pos_columns:
            for rfid_col in rfid_columns:
                similarity = self.calculate_similarity(pos_col.lower(), rfid_col.lower())
                if similarity > 0.7 and pos_col != rfid_col:
                    correlations['fuzzy_matches'].append({
                        'pos_column': pos_col,
                        'rfid_column': rfid_col,
                        'similarity': round(similarity, 2)
                    })
        
        # Identify cross-references
        correlations['cross_references'] = self.identify_cross_references(pos_data, rfid_data)
        
        return correlations
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity"""
        # Simple similarity based on common substrings
        str1_clean = re.sub(r'[^a-z0-9]', '', str1)
        str2_clean = re.sub(r'[^a-z0-9]', '', str2)
        
        if not str1_clean or not str2_clean:
            return 0.0
        
        # Check for common substrings
        common_length = 0
        for i in range(len(str1_clean)):
            for j in range(i + 1, len(str1_clean) + 1):
                substring = str1_clean[i:j]
                if substring in str2_clean:
                    common_length = max(common_length, len(substring))
        
        max_length = max(len(str1_clean), len(str2_clean))
        return common_length / max_length if max_length > 0 else 0.0
    
    def identify_cross_references(self, pos_data: Dict, rfid_data: Dict) -> List:
        """Identify potential cross-references between datasets"""
        cross_refs = []
        
        # Check for contract number references
        if 'transactions' in pos_data and 'rfid_transactions' in rfid_data:
            pos_trans = pos_data['transactions']
            rfid_trans = rfid_data['rfid_transactions']
            
            # Look for contract columns
            pos_contract_cols = [col for col in pos_trans.columns if 'contract' in col.lower()]
            rfid_contract_cols = [col for col in rfid_trans.columns if 'contract' in col.lower()]
            
            if pos_contract_cols and rfid_contract_cols:
                cross_refs.append({
                    'type': 'CONTRACT_REFERENCE',
                    'pos_field': pos_contract_cols[0],
                    'rfid_field': rfid_contract_cols[0],
                    'confidence': 'HIGH'
                })
        
        # Check for customer references
        if 'customers' in pos_data:
            customer_cols = [col for col in pos_data['customers'].columns if 'customer' in col.lower() or 'name' in col.lower()]
            
            for rfid_name, rfid_df in rfid_data.items():
                if isinstance(rfid_df, pd.DataFrame):
                    rfid_customer_cols = [col for col in rfid_df.columns if 'customer' in col.lower() or 'client' in col.lower()]
                    if customer_cols and rfid_customer_cols:
                        cross_refs.append({
                            'type': 'CUSTOMER_REFERENCE',
                            'pos_field': customer_cols[0],
                            'rfid_field': rfid_customer_cols[0],
                            'confidence': 'MEDIUM'
                        })
        
        # Check for equipment/item references
        if 'equipment' in pos_data:
            equip_cols = [col for col in pos_data['equipment'].columns if any(x in col.lower() for x in ['item', 'equip', 'serial'])]
            
            for rfid_name, rfid_df in rfid_data.items():
                if isinstance(rfid_df, pd.DataFrame):
                    rfid_item_cols = [col for col in rfid_df.columns if any(x in col.lower() for x in ['item', 'tag', 'serial'])]
                    if equip_cols and rfid_item_cols:
                        cross_refs.append({
                            'type': 'EQUIPMENT_REFERENCE',
                            'pos_field': equip_cols[0],
                            'rfid_field': rfid_item_cols[0],
                            'confidence': 'HIGH'
                        })
                        break
        
        return cross_refs
    
    def assess_data_quality(self, pos_data: Dict, rfid_data: Dict) -> Dict:
        """Assess data quality across all datasets"""
        quality = {
            'overall_score': 0,
            'issues': [],
            'completeness': {},
            'consistency': {},
            'freshness': {}
        }
        
        all_data = {**{f'pos_{k}': v for k, v in pos_data.items()}, 
                    **{f'rfid_{k}': v for k, v in rfid_data.items()}}
        
        scores = []
        
        for name, df in all_data.items():
            if isinstance(df, pd.DataFrame):
                # Completeness check
                null_percentage = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
                completeness_score = 100 - null_percentage
                quality['completeness'][name] = round(completeness_score, 2)
                scores.append(completeness_score)
                
                if null_percentage > 30:
                    quality['issues'].append({
                        'dataset': name,
                        'type': 'HIGH_NULL_VALUES',
                        'severity': 'HIGH' if null_percentage > 50 else 'MEDIUM',
                        'percentage': round(null_percentage, 2),
                        'recommendation': f'Review and clean null values in {name}'
                    })
                
                # Check for duplicates
                potential_key_cols = self.identify_potential_keys(df)
                for col in potential_key_cols[:1]:  # Check first potential key
                    if col in df.columns:
                        duplicates = df[col].duplicated().sum()
                        if duplicates > 0:
                            quality['issues'].append({
                                'dataset': name,
                                'type': 'DUPLICATE_KEYS',
                                'column': col,
                                'count': duplicates,
                                'severity': 'HIGH' if duplicates > 100 else 'MEDIUM',
                                'recommendation': f'Remove duplicate {col} values in {name}'
                            })
                
                # Check for test/dummy data
                if 'name' in df.columns or 'description' in df.columns:
                    text_col = 'name' if 'name' in df.columns else 'description'
                    test_patterns = ['test', 'demo', 'dummy', 'sample', 'xxx']
                    
                    for pattern in test_patterns:
                        if df[text_col].astype(str).str.lower().str.contains(pattern).any():
                            count = df[df[text_col].astype(str).str.lower().str.contains(pattern)].shape[0]
                            if count > 0:
                                quality['issues'].append({
                                    'dataset': name,
                                    'type': 'TEST_DATA_CONTAMINATION',
                                    'pattern': pattern,
                                    'count': count,
                                    'severity': 'MEDIUM',
                                    'recommendation': f'Remove test data containing "{pattern}" from {name}'
                                })
                                break
        
        quality['overall_score'] = round(np.mean(scores), 2) if scores else 0
        
        return quality
    
    def generate_recommendations(self) -> Dict:
        """Generate actionable recommendations"""
        recommendations = {
            'immediate_actions': [],
            'integration_opportunities': [],
            'data_cleaning': [],
            'ai_readiness': {}
        }
        
        # Based on correlations found
        if 'correlations' in self.results:
            if self.results['correlations']['exact_matches']:
                recommendations['integration_opportunities'].append({
                    'action': 'Create unified view using exact column matches',
                    'columns': self.results['correlations']['exact_matches'][:5],
                    'priority': 'HIGH',
                    'effort': '1-2 days'
                })
            
            for cross_ref in self.results['correlations'].get('cross_references', []):
                if cross_ref['confidence'] == 'HIGH':
                    recommendations['integration_opportunities'].append({
                        'action': f'Link {cross_ref["type"]} between POS and RFID',
                        'pos_field': cross_ref['pos_field'],
                        'rfid_field': cross_ref['rfid_field'],
                        'priority': 'HIGH',
                        'effort': '2-3 days'
                    })
        
        # Based on data quality issues
        if 'data_quality' in self.results:
            for issue in self.results['data_quality'].get('issues', []):
                if issue['severity'] == 'HIGH':
                    recommendations['immediate_actions'].append({
                        'action': issue['recommendation'],
                        'dataset': issue['dataset'],
                        'type': issue['type'],
                        'priority': 'CRITICAL'
                    })
                else:
                    recommendations['data_cleaning'].append({
                        'action': issue['recommendation'],
                        'dataset': issue['dataset'],
                        'type': issue['type'],
                        'priority': 'MEDIUM'
                    })
        
        # AI readiness assessment
        quality_score = self.results.get('data_quality', {}).get('overall_score', 0)
        
        if quality_score >= 80:
            recommendations['ai_readiness'] = {
                'status': 'READY',
                'message': 'Data quality sufficient for ML implementation',
                'next_steps': ['Feature engineering', 'Model selection', 'Training pipeline']
            }
        elif quality_score >= 60:
            recommendations['ai_readiness'] = {
                'status': 'MODERATE',
                'message': 'Some data cleaning required before ML',
                'next_steps': ['Address high-priority issues', 'Improve data completeness', 'Then proceed with ML']
            }
        else:
            recommendations['ai_readiness'] = {
                'status': 'NOT_READY',
                'message': 'Significant data quality improvements needed',
                'next_steps': ['Focus on data cleaning', 'Establish data governance', 'Improve collection processes']
            }
        
        return recommendations
    
    def print_summary(self):
        """Print executive summary"""
        print("\n" + "="*80)
        print("EXECUTIVE SUMMARY")
        print("="*80)
        
        # Files analyzed
        print(f"\nFiles Analyzed: {len(self.results['files_analyzed'])}")
        
        # Data quality score
        if 'data_quality' in self.results:
            score = self.results['data_quality'].get('overall_score', 0)
            print(f"Overall Data Quality Score: {score}%")
            
            issues = self.results['data_quality'].get('issues', [])
            high_priority = [i for i in issues if i.get('severity') == 'HIGH']
            if high_priority:
                print(f"High Priority Issues: {len(high_priority)}")
        
        # Correlations found
        if 'correlations' in self.results:
            exact = len(self.results['correlations'].get('exact_matches', []))
            fuzzy = len(self.results['correlations'].get('fuzzy_matches', []))
            cross = len(self.results['correlations'].get('cross_references', []))
            print(f"\nCorrelations Found:")
            print(f"  - Exact column matches: {exact}")
            print(f"  - Fuzzy matches: {fuzzy}")
            print(f"  - Cross-references: {cross}")
        
        # Key recommendations
        if 'recommendations' in self.results:
            immediate = self.results['recommendations'].get('immediate_actions', [])
            if immediate:
                print(f"\nImmediate Actions Required: {len(immediate)}")
                for action in immediate[:3]:
                    print(f"  - {action.get('action', 'Unknown')}")
            
            ai_status = self.results['recommendations'].get('ai_readiness', {}).get('status', 'Unknown')
            print(f"\nAI/ML Readiness: {ai_status}")
    
    def save_results(self):
        """Save results to JSON file"""
        filename = f"csv_correlation_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert any DataFrame info to serializable format
        def make_serializable(obj):
            if isinstance(obj, pd.DataFrame):
                return {'type': 'DataFrame', 'shape': obj.shape}
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=make_serializable)
        
        print(f"\nResults saved to: {filename}")
        return filename


def main():
    """Main execution"""
    analyzer = CSVCorrelationAnalyzer()
    results = analyzer.analyze_all_csv_files()
    analyzer.print_summary()
    analyzer.save_results()
    
    return results


if __name__ == "__main__":
    main()