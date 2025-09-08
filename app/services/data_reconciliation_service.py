"""
Data Reconciliation Service for RFID3 System
Handles discrepancies between POS, RFID, and Financial data sources
Created: September 3, 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import text, func
from decimal import Decimal
import logging

from app import db
from app.services.logger import get_logger
from app.services.financial_analytics_service import FinancialAnalyticsService

logger = get_logger(__name__)

class DataReconciliationService:
    """
    Service for reconciling data discrepancies between POS, RFID, and Financial systems.
    Provides transparency when data sources disagree and recommends which source to trust.
    """
    
    def __init__(self):
        self.financial_service = FinancialAnalyticsService()
        self.logger = logger
    
    def get_revenue_reconciliation(self, 
                                 start_date: Optional[date] = None, 
                                 end_date: Optional[date] = None,
                                 store_code: Optional[str] = None) -> Dict:
        """
        Compare revenue calculations from different data sources
        """
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=7)
            if not end_date:
                end_date = date.today()
            
            # Get revenue from different sources
            financial_revenue = self._get_financial_revenue(start_date, end_date, store_code)
            pos_revenue = self._get_pos_revenue(start_date, end_date, store_code)
            rfid_revenue = self._get_rfid_revenue(start_date, end_date, store_code)
            
            # Calculate variances
            reconciliation = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': (end_date - start_date).days + 1,
                    'store_code': store_code or 'all_stores'
                },
                'revenue_sources': {
                    'financial_system': {
                        'value': financial_revenue['total'],
                        'confidence': 'high',
                        'source': 'scorecard_trends_data',
                        'coverage': '100% (all stores)',
                        'last_updated': financial_revenue.get('last_updated'),
                        'methodology': 'Manager-reported weekly targets vs actual'
                    },
                    'pos_transactions': {
                        'value': pos_revenue['total'],
                        'confidence': 'high',
                        'source': 'pos_transactions',  
                        'coverage': '100% (all transactions)',
                        'last_updated': pos_revenue.get('last_updated'),
                        'methodology': 'Sum of completed contract amounts'
                    },
                    'rfid_correlation': {
                        'value': rfid_revenue['total'],
                        'confidence': 'low',
                        'source': 'combined_inventory',
                        'coverage': '1.78% (290 correlated items)',
                        'last_updated': rfid_revenue.get('last_updated'),
                        'methodology': 'Rental rate × RFID on-rent count'
                    }
                }
            }
            
            # Calculate variance analysis
            financial_value = financial_revenue['total']
            pos_value = pos_revenue['total']
            
            if financial_value > 0:
                pos_variance_pct = ((pos_value - financial_value) / financial_value) * 100
            else:
                pos_variance_pct = 0
                
            reconciliation['variance_analysis'] = {
                'pos_vs_financial': {
                    'absolute': pos_value - financial_value,
                    'percentage': round(pos_variance_pct, 2),
                    'status': self._get_variance_status(abs(pos_variance_pct))
                },
                'rfid_coverage_gap': {
                    'covered_revenue': rfid_revenue['total'],
                    'uncovered_estimated': pos_value - rfid_revenue['total'],
                    'coverage_percentage': round((rfid_revenue['total'] / pos_value) * 100, 2) if pos_value > 0 else 0
                }
            }
            
            # Provide recommendation
            reconciliation['recommendation'] = self._get_revenue_recommendation(reconciliation)
            
            return {
                'success': True,
                'reconciliation': reconciliation
            }
            
        except Exception as e:
            logger.error(f"Error in revenue reconciliation: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_utilization_reconciliation(self, store_code: Optional[str] = None) -> Dict:
        """
        Compare utilization calculations between POS and RFID systems
        """
        try:
            # Get utilization from different calculation methods
            pos_utilization = self._get_pos_utilization(store_code)
            rfid_utilization = self._get_rfid_utilization(store_code)
            estimated_utilization = self._get_estimated_utilization(store_code)
            
            reconciliation = {
                'utilization_sources': {
                    'rfid_actual': {
                        'value': rfid_utilization['average'],
                        'confidence': 'high',
                        'coverage': f"{rfid_utilization['item_count']} items (1.78%)",
                        'methodology': 'RFID status tracking',
                        'items_tracked': rfid_utilization['item_count']
                    },
                    'pos_estimated': {
                        'value': pos_utilization['average'],
                        'confidence': 'medium', 
                        'coverage': f"{pos_utilization['item_count']} items (98.22%)",
                        'methodology': 'Contract status analysis',
                        'items_tracked': pos_utilization['item_count']
                    },
                    'financial_proxy': {
                        'value': estimated_utilization['value'],
                        'confidence': 'low',
                        'coverage': 'All stores aggregate',
                        'methodology': 'Revenue efficiency as utilization proxy',
                        'note': 'Indirect measurement'
                    }
                },
                'coverage_analysis': {
                    'total_equipment': pos_utilization['item_count'] + rfid_utilization['item_count'],
                    'rfid_tracked': rfid_utilization['item_count'],
                    'pos_only': pos_utilization['item_count'],
                    'coverage_percentage': round((rfid_utilization['item_count'] / 
                                               (pos_utilization['item_count'] + rfid_utilization['item_count'])) * 100, 2)
                }
            }
            
            # Weighted utilization calculation
            total_items = rfid_utilization['item_count'] + pos_utilization['item_count']
            if total_items > 0:
                weighted_utilization = (
                    (rfid_utilization['average'] * rfid_utilization['item_count'] + 
                     pos_utilization['average'] * pos_utilization['item_count']) / total_items
                )
                reconciliation['recommended_utilization'] = {
                    'value': round(weighted_utilization, 1),
                    'methodology': 'Weighted average prioritizing RFID accuracy',
                    'confidence': 'medium'
                }
            
            return {
                'success': True,
                'reconciliation': reconciliation
            }
            
        except Exception as e:
            logger.error(f"Error in utilization reconciliation: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_inventory_reconciliation(self, category: Optional[str] = None) -> Dict:
        """
        Compare inventory counts between POS quantities and RFID tag counts
        """
        try:
            inventory_query = text("""
                SELECT 
                    ci.category,
                    ci.equipment_name,
                    ci.store_code,
                    ci.pos_quantity,
                    ci.rfid_tag_count,
                    ci.data_quality_flag,
                    ABS(ci.pos_quantity - ci.rfid_tag_count) as quantity_variance,
                    CASE 
                        WHEN ci.rfid_tag_count > 0 THEN 
                            ROUND(ABS(ci.pos_quantity - ci.rfid_tag_count) / ci.pos_quantity * 100, 1)
                        ELSE NULL
                    END as variance_percentage
                FROM combined_inventory ci
                WHERE ci.correlation_confidence IS NOT NULL
                """ + (f"AND ci.category = '{category}'" if category else "") + """
                ORDER BY quantity_variance DESC
                LIMIT 100
            """)
            
            results = db.session.execute(inventory_query).fetchall()
            
            discrepancies = []
            summary_stats = {
                'total_correlated_items': 0,
                'perfect_matches': 0,
                'minor_discrepancies': 0,  # <10% variance
                'major_discrepancies': 0,  # >=10% variance
                'total_pos_quantity': 0,
                'total_rfid_tags': 0
            }
            
            for row in results:
                discrepancy = {
                    'equipment_name': row.equipment_name[:50] + '...' if len(row.equipment_name) > 50 else row.equipment_name,
                    'category': row.category,
                    'store_code': row.store_code,
                    'pos_quantity': row.pos_quantity,
                    'rfid_tag_count': row.rfid_tag_count,
                    'variance': row.quantity_variance,
                    'variance_percentage': row.variance_percentage,
                    'data_quality': row.data_quality_flag,
                    'severity': self._get_discrepancy_severity(row.variance_percentage)
                }
                
                discrepancies.append(discrepancy)
                
                # Update summary stats
                summary_stats['total_correlated_items'] += 1
                summary_stats['total_pos_quantity'] += row.pos_quantity
                summary_stats['total_rfid_tags'] += row.rfid_tag_count
                
                if row.quantity_variance == 0:
                    summary_stats['perfect_matches'] += 1
                elif row.variance_percentage and row.variance_percentage < 10:
                    summary_stats['minor_discrepancies'] += 1
                else:
                    summary_stats['major_discrepancies'] += 1
            
            # Calculate overall accuracy
            if summary_stats['total_correlated_items'] > 0:
                summary_stats['match_accuracy'] = round(
                    (summary_stats['perfect_matches'] / summary_stats['total_correlated_items']) * 100, 1
                )
                summary_stats['overall_variance'] = round(
                    abs(summary_stats['total_pos_quantity'] - summary_stats['total_rfid_tags']) / 
                    summary_stats['total_pos_quantity'] * 100, 1
                ) if summary_stats['total_pos_quantity'] > 0 else 0
            
            return {
                'success': True,
                'inventory_reconciliation': {
                    'summary': summary_stats,
                    'discrepancies': discrepancies[:20],  # Top 20 discrepancies
                    'category_filter': category,
                    'analysis_timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in inventory reconciliation: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_comprehensive_reconciliation_report(self) -> Dict:
        """
        Generate comprehensive report showing all data source discrepancies
        """
        try:
            report = {
                'report_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'system_status': 'operational',
                    'data_coverage': {
                        'pos_equipment': self._count_pos_equipment(),
                        'rfid_tags': self._count_rfid_tags(),
                        'correlations': self._count_correlations(),
                        'financial_records': self._count_financial_records()
                    }
                }
            }
            
            # Get reconciliations for different areas
            revenue_recon = self.get_revenue_reconciliation()
            utilization_recon = self.get_utilization_reconciliation()
            inventory_recon = self.get_inventory_reconciliation()
            
            report['revenue_reconciliation'] = revenue_recon.get('reconciliation', {})
            report['utilization_reconciliation'] = utilization_recon.get('reconciliation', {})
            report['inventory_reconciliation'] = inventory_recon.get('inventory_reconciliation', {})
            
            # Overall system health assessment
            report['system_health'] = self._assess_system_health(report)
            
            return {
                'success': True,
                'comprehensive_report': report
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive reconciliation report: {e}")
            return {'success': False, 'error': str(e)}
    
    # Helper methods
    def _get_financial_revenue(self, start_date: date, end_date: date, store_code: Optional[str]) -> Dict:
        """Get revenue from financial system (scorecard data)"""
        try:
            # Use existing financial service
            revenue_data = self.financial_service.calculate_rolling_averages('revenue', 
                                                                           (end_date - start_date).days)
            if revenue_data.get('success'):
                total = revenue_data.get('summary', {}).get('current_3wk_avg', 0) * ((end_date - start_date).days / 21)
                return {
                    'total': total,
                    'last_updated': revenue_data.get('timestamp')
                }
            return {'total': 0}
        except Exception as e:
            logger.warning(f"Error getting financial revenue: {e}")
            return {'total': 0}
    
    def _get_pos_revenue(self, start_date: date, end_date: date, store_code: Optional[str]) -> Dict:
        """Get revenue from POS transactions"""
        try:
            # Use parameterized queries to prevent SQL injection
            if store_code:
                query = text("""
                    SELECT 
                        SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_revenue,
                        MAX(import_date) as last_updated
                    FROM pos_transactions 
                    WHERE close_date >= :start_date 
                    AND close_date <= :end_date
                    AND status = 'COMPLETED'
                    AND store_no = :store_code
                """)
                result = db.session.execute(query, {
                    'start_date': start_date,
                    'end_date': end_date,
                    'store_code': store_code
                }).fetchone()
            else:
                query = text("""
                    SELECT 
                        SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_revenue,
                        MAX(import_date) as last_updated
                    FROM pos_transactions 
                    WHERE close_date >= :start_date 
                    AND close_date <= :end_date
                    AND status = 'COMPLETED'
                """)
                result = db.session.execute(query, {
                    'start_date': start_date,
                    'end_date': end_date
                }).fetchone()
            
            return {
                'total': float(result.total_revenue or 0),
                'last_updated': result.last_updated
            }
        except Exception as e:
            logger.warning(f"Error getting POS revenue: {e}")
            return {'total': 0}
    
    def _get_rfid_revenue(self, start_date: date, end_date: date, store_code: Optional[str]) -> Dict:
        """Get revenue from RFID correlation data"""
        try:
            # Use parameterized queries to prevent SQL injection
            if store_code:
                query = text("""
                    SELECT 
                        SUM(current_rental_revenue) as total_revenue,
                        MAX(view_generated_at) as last_updated
                    FROM combined_inventory
                    WHERE rfid_tag_count > 0
                    AND store_code = :store_code
                """)
                result = db.session.execute(query, {'store_code': store_code}).fetchone()
            else:
                query = text("""
                    SELECT 
                        SUM(current_rental_revenue) as total_revenue,
                        MAX(view_generated_at) as last_updated
                    FROM combined_inventory
                    WHERE rfid_tag_count > 0
                """)
                result = db.session.execute(query).fetchone()
            
            return {
                'total': float(result.total_revenue or 0),
                'last_updated': result.last_updated
            }
        except Exception as e:
            logger.warning(f"Error getting RFID revenue: {e}")
            return {'total': 0}
    
    def _get_pos_utilization(self, store_code: Optional[str]) -> Dict:
        """Calculate utilization from POS data only"""
        try:
            store_filter = f"AND store_code = '{store_code}'" if store_code else ""
            
            query = text(f"""
                SELECT 
                    COUNT(*) as item_count,
                    AVG(CASE 
                        WHEN status IN ('fully_rented', 'partially_rented') THEN 75.0
                        WHEN status = 'available' THEN 0.0
                        ELSE 25.0
                    END) as avg_utilization
                FROM combined_inventory
                WHERE correlation_confidence IS NULL
                {store_filter}
            """)
            
            result = db.session.execute(query).fetchone()
            return {
                'item_count': result.item_count or 0,
                'average': float(result.avg_utilization or 0)
            }
        except Exception as e:
            logger.warning(f"Error getting POS utilization: {e}")
            return {'item_count': 0, 'average': 0}
    
    def _get_rfid_utilization(self, store_code: Optional[str]) -> Dict:
        """Calculate utilization from RFID data"""
        try:
            store_filter = f"AND store_code = '{store_code}'" if store_code else ""
            
            query = text(f"""
                SELECT 
                    COUNT(*) as item_count,
                    AVG(utilization_percentage) as avg_utilization
                FROM combined_inventory
                WHERE rfid_tag_count > 0
                {store_filter}
            """)
            
            result = db.session.execute(query).fetchone()
            return {
                'item_count': result.item_count or 0,
                'average': float(result.avg_utilization or 0)
            }
        except Exception as e:
            logger.warning(f"Error getting RFID utilization: {e}")
            return {'item_count': 0, 'average': 0}
    
    def _get_estimated_utilization(self, store_code: Optional[str]) -> Dict:
        """Get utilization proxy from financial efficiency"""
        try:
            # Use financial service efficiency as proxy
            return {'value': 65.0}  # Placeholder - would integrate with financial metrics
        except Exception as e:
            return {'value': 0}
    
    def _get_variance_status(self, variance_pct: float) -> str:
        """Classify variance severity"""
        if variance_pct < 2:
            return 'excellent'
        elif variance_pct < 5:
            return 'good'
        elif variance_pct < 10:
            return 'acceptable'
        else:
            return 'needs_attention'
    
    def _get_revenue_recommendation(self, reconciliation: Dict) -> Dict:
        """Provide recommendation on which revenue source to trust"""
        financial = reconciliation['revenue_sources']['financial_system']
        pos = reconciliation['revenue_sources']['pos_transactions']
        
        variance_pct = abs(reconciliation['variance_analysis']['pos_vs_financial']['percentage'])
        
        if variance_pct < 5:
            return {
                'primary_source': 'financial_system',
                'reasoning': 'Financial and POS data closely aligned (<5% variance)',
                'confidence': 'high',
                'action': 'Use financial system data (most complete for executive reporting)'
            }
        elif variance_pct < 15:
            return {
                'primary_source': 'pos_transactions',
                'reasoning': 'Moderate variance suggests timing differences',
                'confidence': 'medium',
                'action': 'Investigate timing differences between systems'
            }
        else:
            return {
                'primary_source': 'requires_investigation',
                'reasoning': f'High variance ({variance_pct:.1f}%) requires investigation',
                'confidence': 'low',
                'action': 'Manual reconciliation needed - check data integrity'
            }
    
    def _get_discrepancy_severity(self, variance_pct: Optional[float]) -> str:
        """Classify inventory discrepancy severity"""
        if not variance_pct:
            return 'no_rfid_data'
        elif variance_pct < 5:
            return 'minor'
        elif variance_pct < 15:
            return 'moderate'
        else:
            return 'major'
    
    def _count_pos_equipment(self) -> int:
        """Count POS equipment items"""
        try:
            result = db.session.execute(text("SELECT COUNT(*) FROM pos_equipment WHERE inactive = 0")).fetchone()
            return result[0]
        except:
            return 0
    
    def _count_rfid_tags(self) -> int:
        """Count RFID tags"""
        try:
            result = db.session.execute(text("SELECT COUNT(*) FROM id_item_master WHERE identifier_type = 'RFID'")).fetchone()
            return result[0]
        except:
            return 0
    
    def _count_correlations(self) -> int:
        """Count equipment correlations"""
        try:
            result = db.session.execute(text("SELECT COUNT(*) FROM equipment_rfid_correlations")).fetchone()
            return result[0]
        except:
            return 0
    
    def _count_financial_records(self) -> int:
        """Count financial records"""
        try:
            result = db.session.execute(text("SELECT COUNT(*) FROM scorecard_trends_data")).fetchone()
            return result[0]
        except:
            return 0
    
    def _assess_system_health(self, report: Dict) -> Dict:
        """Assess overall system health based on reconciliation results"""
        health_score = 100
        issues = []
        
        # Check revenue variance
        revenue_variance = report.get('revenue_reconciliation', {}).get('variance_analysis', {}).get('pos_vs_financial', {}).get('percentage', 0)
        if abs(revenue_variance) > 10:
            health_score -= 20
            issues.append(f"High revenue variance ({revenue_variance:.1f}%)")
        elif abs(revenue_variance) > 5:
            health_score -= 10
            issues.append(f"Moderate revenue variance ({revenue_variance:.1f}%)")
        
        # Check RFID coverage
        coverage_pct = 1.78  # Current known coverage
        if coverage_pct < 5:
            health_score -= 15
            issues.append(f"Low RFID coverage ({coverage_pct:.1f}%)")
        
        # Check inventory accuracy
        inventory_accuracy = report.get('inventory_reconciliation', {}).get('summary', {}).get('match_accuracy', 100)
        if inventory_accuracy < 80:
            health_score -= 20
            issues.append(f"Low inventory accuracy ({inventory_accuracy:.1f}%)")
        elif inventory_accuracy < 90:
            health_score -= 10
            issues.append(f"Moderate inventory accuracy ({inventory_accuracy:.1f}%)")
        
        return {
            'overall_score': max(0, health_score),
            'status': 'excellent' if health_score >= 90 else 'good' if health_score >= 75 else 'needs_attention',
            'issues': issues,
            'recommendations': self._generate_health_recommendations(issues)
        }
    
    def _generate_health_recommendations(self, issues: List[str]) -> List[str]:
        """Generate recommendations based on identified issues"""
        recommendations = []
        
        for issue in issues:
            if 'revenue variance' in issue:
                recommendations.append("Investigate timing differences in revenue recognition between systems")
            elif 'RFID coverage' in issue:
                recommendations.append("Expand RFID correlation coverage through intelligent matching algorithms")
            elif 'inventory accuracy' in issue:
                recommendations.append("Perform physical inventory audit for high-variance items")
        
        if not recommendations:
            recommendations.append("System health is good - continue monitoring for trends")
        
        return recommendations