"""
Advanced Business Analytics Service
Combines RFID tracking data with CSV business data for comprehensive KPI calculations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text, func
from app import db
from app.services.logger import get_logger
from app.models.pos_models import POSCustomer, POSEquipment, POSTransaction, POSTransactionItem
from app.models.config_models import BusinessAnalyticsConfiguration, get_default_business_analytics_config

logger = get_logger(__name__)

class BusinessAnalyticsService:
    """Service for advanced business analytics and KPI calculations"""
    
    def __init__(self):
        self.logger = logger
        self.config = self._get_config()
        
    def calculate_equipment_utilization_analytics(self) -> Dict:
        """Calculate comprehensive equipment utilization metrics"""
        try:
            # Get equipment turnover data from CSV imports
            equipment_query = text("""
                SELECT 
                    item_num,
                    name,
                    category,
                    turnover_ytd,
                    turnover_ltd,
                    sell_price,
                    current_store,
                    inactive
                FROM pos_equipment 
                WHERE inactive = 0
                ORDER BY turnover_ytd DESC
            """)
            
            equipment_df = pd.read_sql(equipment_query, db.engine)
            
            if equipment_df.empty:
                return {"error": "No equipment data available"}
            
            # Calculate utilization metrics
            analytics = {
                "total_active_items": len(equipment_df),
                "high_performers": self._identify_high_performers(equipment_df),
                "underperformers": self._identify_underperformers(equipment_df),
                "category_analysis": self._analyze_by_category(equipment_df),
                "store_performance": self._analyze_by_store(equipment_df),
                "resale_recommendations": self._generate_resale_recommendations(equipment_df),
                "revenue_optimization": self._calculate_revenue_optimization(equipment_df)
            }
            
            logger.info(f"Calculated utilization analytics for {len(equipment_df)} items")
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to calculate utilization analytics: {e}")
            return {"error": str(e)}
    
    def _identify_high_performers(self, df: pd.DataFrame) -> Dict:
        """Identify top performing equipment by turnover"""
        top_20_percent = int(len(df) * 0.2)
        high_performers = df.nlargest(top_20_percent, 'turnover_ytd')
        
        return {
            "count": len(high_performers),
            "total_ytd_revenue": float(high_performers['turnover_ytd'].sum()),
            "avg_ytd_revenue": float(high_performers['turnover_ytd'].mean()),
            "top_categories": high_performers['category'].value_counts().head(5).to_dict(),
            "top_items": high_performers[['item_num', 'name', 'turnover_ytd']].head(10).to_dict('records')
        }
    
    def _identify_underperformers(self, df: pd.DataFrame) -> Dict:
        """Identify underperforming equipment for potential resale"""
        # Items with zero or very low turnover
        # OLD - HARDCODED (WRONG): underperformers = df[df['turnover_ytd'] <= 50]  # Less than $50 YTD
        # NEW - CONFIGURABLE (CORRECT):
        underperformer_threshold = self.config.get_threshold('equipment_underperformer_threshold')
        underperformers = df[df['turnover_ytd'] <= underperformer_threshold]
        
        return {
            "count": len(underperformers),
            "potential_resale_value": float(underperformers['sell_price'].sum()),
            "categories_affected": underperformers['category'].value_counts().to_dict(),
            "zero_turnover_items": len(underperformers[underperformers['turnover_ytd'] == 0]),
            "items_for_review": underperformers[['item_num', 'name', 'category', 'turnover_ytd', 'sell_price']].head(20).to_dict('records')
        }
    
    def _analyze_by_category(self, df: pd.DataFrame) -> Dict:
        """Analyze performance by equipment category"""
        category_stats = df.groupby('category').agg({
            'turnover_ytd': ['sum', 'mean', 'count'],
            'sell_price': 'sum'
        }).round(2)
        
        category_stats.columns = ['total_revenue', 'avg_revenue', 'item_count', 'total_value']
        category_stats['revenue_per_item'] = (category_stats['total_revenue'] / category_stats['item_count']).round(2)
        
        return {
            "category_performance": category_stats.sort_values('total_revenue', ascending=False).to_dict('index'),
            "top_revenue_categories": category_stats.nlargest(5, 'total_revenue')[['total_revenue', 'item_count']].to_dict('index'),
            "most_efficient_categories": category_stats.nlargest(5, 'revenue_per_item')[['revenue_per_item', 'item_count']].to_dict('index')
        }
    
    def _analyze_by_store(self, df: pd.DataFrame) -> Dict:
        """Analyze performance by store location"""
        store_stats = df.groupby('current_store').agg({
            'turnover_ytd': ['sum', 'mean', 'count'],
            'sell_price': 'sum'
        }).round(2)
        
        store_stats.columns = ['total_revenue', 'avg_revenue', 'item_count', 'total_value']
        
        return {
            "store_performance": store_stats.sort_values('total_revenue', ascending=False).to_dict('index'),
            "top_performing_stores": store_stats.nlargest(5, 'total_revenue').to_dict('index'),
            "store_efficiency": store_stats.sort_values('avg_revenue', ascending=False).to_dict('index')
        }
    
    def _generate_resale_recommendations(self, df: pd.DataFrame) -> Dict:
        """Generate intelligent resale recommendations"""
        # Criteria for resale recommendation
        resale_candidates = df[
            (df['turnover_ytd'] == 0) |  # No turnover this year
            # OLD - HARDCODED (WRONG): ((df['turnover_ytd'] < 25) & (df['sell_price'] > 100))  # Low turnover but high value
            # NEW - CONFIGURABLE (CORRECT):
            ((df['turnover_ytd'] < self.config.get_threshold('low_turnover_threshold')) & 
             (df['sell_price'] > 100))  # Keep $100 threshold for now, will make configurable in next phase
        ]
        
        # Priority scoring: higher sell price + lower turnover = higher priority
        resale_candidates['resale_priority'] = (
            resale_candidates['sell_price'] / (resale_candidates['turnover_ytd'] + 1)
        ).round(2)
        
        # OLD - HARDCODED (WRONG): high_priority = resale_candidates[resale_candidates['resale_priority'] > 10].sort_values('resale_priority', ascending=False)
        # NEW - CONFIGURABLE (CORRECT):
        high_priority_threshold = self.config.get_threshold('high_resale_priority_threshold')
        high_priority = resale_candidates[resale_candidates['resale_priority'] > high_priority_threshold].sort_values('resale_priority', ascending=False)
        
        return {
            "total_candidates": len(resale_candidates),
            "potential_resale_value": float(resale_candidates['sell_price'].sum()),
            "high_priority_items": len(high_priority),
            "high_priority_value": float(high_priority['sell_price'].sum()),
            "recommendations": high_priority[['item_num', 'name', 'category', 'turnover_ytd', 'sell_price', 'resale_priority']].head(25).to_dict('records')
        }
    
    def _calculate_revenue_optimization(self, df: pd.DataFrame) -> Dict:
        """Calculate revenue optimization opportunities"""
        total_inventory_value = df['sell_price'].sum()
        total_ytd_revenue = df['turnover_ytd'].sum()
        
        # Calculate ROI by category
        roi_by_category = df.groupby('category').apply(
            lambda x: (x['turnover_ytd'].sum() / x['sell_price'].sum() * 100) if x['sell_price'].sum() > 0 else 0
        ).round(2).sort_values(ascending=False)
        
        return {
            "total_inventory_value": float(total_inventory_value),
            "total_ytd_revenue": float(total_ytd_revenue),
            "overall_roi_percentage": float((total_ytd_revenue / total_inventory_value * 100) if total_inventory_value > 0 else 0),
            "roi_by_category": roi_by_category.to_dict(),
            "optimization_opportunities": {
                # OLD - HARDCODED (WRONG): "underutilized_inventory_value": float(df[df['turnover_ytd'] < 50]['sell_price'].sum()),
                # NEW - CONFIGURABLE (CORRECT):
                "underutilized_inventory_value": float(df[df['turnover_ytd'] < underperformer_threshold]['sell_price'].sum()),
                "zero_revenue_items": len(df[df['turnover_ytd'] == 0]),
                # OLD - HARDCODED (WRONG): "high_value_low_usage": len(df[(df['sell_price'] > 500) & (df['turnover_ytd'] < 100)])
                # NEW - CONFIGURABLE (CORRECT):
                "high_value_low_usage": len(df[(df['sell_price'] > self.config.get_threshold('high_value_equipment_threshold')) & 
                                             (df['turnover_ytd'] < self.config.get_threshold('low_turnover_threshold'))])
            }
        }
    
    def calculate_customer_analytics(self) -> Dict:
        """Calculate customer-focused analytics"""
        try:
            # This would integrate with customer CSV data when imported
            customer_query = text("""
                SELECT 
                    cnum,
                    name,
                    ytd_payments,
                    no_of_contracts
                FROM pos_customers 
                ORDER BY ytd_payments DESC
                LIMIT 1000
            """)
            
            # For now, return structure for future implementation
            return {
                "status": "pending_customer_data_import",
                "structure": {
                    "top_customers": [],
                    "customer_segments": {},
                    "retention_metrics": {},
                    "revenue_concentration": {}
                }
            }
            
        except Exception as e:
            logger.warning(f"Customer analytics not available yet: {e}")
            return {"status": "pending_customer_data_import"}
    
    def generate_executive_dashboard_metrics(self) -> Dict:
        """Generate key metrics for executive dashboard"""
        try:
            utilization_data = self.calculate_equipment_utilization_analytics()
            
            if "error" in utilization_data:
                return utilization_data
            
            # Calculate key executive metrics
            executive_metrics = {
                "inventory_overview": {
                    "total_active_items": utilization_data["total_active_items"],
                    "high_performers_count": utilization_data["high_performers"]["count"],
                    "underperformers_count": utilization_data["underperformers"]["count"],
                    "high_performer_revenue": utilization_data["high_performers"]["total_ytd_revenue"]
                },
                "revenue_optimization": utilization_data["revenue_optimization"],
                "resale_opportunities": {
                    "total_candidates": utilization_data["resale_recommendations"]["total_candidates"],
                    "potential_value": utilization_data["resale_recommendations"]["potential_resale_value"],
                    "high_priority_count": utilization_data["resale_recommendations"]["high_priority_items"]
                },
                "top_categories": utilization_data["category_analysis"]["top_revenue_categories"],
                "generated_at": datetime.now().isoformat()
            }
            
            return executive_metrics
            
        except Exception as e:
            logger.error(f"Failed to generate executive metrics: {e}")
            return {"error": str(e)}
    
    def _get_config(self):
        """Get business analytics configuration with safe defaults"""
        try:
            config = BusinessAnalyticsConfiguration.query.filter_by(
                user_id='default_user', 
                config_name='default'
            ).first()
            
            if config:
                return config
                
            # Create a mock config object with default values if none exists
            class MockConfig:
                def __init__(self):
                    defaults = get_default_business_analytics_config()
                    self.equipment_underperformer_threshold = defaults['equipment_thresholds']['underperformer_ytd']
                    self.high_value_threshold = defaults['equipment_thresholds']['high_value']
                    self.low_turnover_threshold = defaults['equipment_thresholds']['low_turnover']
                    self.low_usage_threshold = defaults['equipment_thresholds']['low_usage']
                    self.resale_priority_threshold = defaults['equipment_thresholds']['resale_priority']
                    self.ar_aging_low_threshold = defaults['financial_risk']['ar_aging_low']
                    self.ar_aging_medium_threshold = defaults['financial_risk']['ar_aging_medium']
                    self.revenue_concentration_risk_threshold = defaults['financial_risk']['concentration_risk']
                    self.declining_trend_threshold = defaults['financial_risk']['declining_trend']
                
                def get_threshold(self, threshold_type: str):
                    """Map threshold type to attribute value"""
                    threshold_map = {
                        'equipment_underperformer_threshold': self.equipment_underperformer_threshold,
                        'high_value_threshold': self.high_value_threshold,
                        'low_turnover_threshold': self.low_turnover_threshold,
                        'low_usage_threshold': self.low_usage_threshold,
                        'resale_priority_threshold': self.resale_priority_threshold,
                        'ar_aging_low_threshold': self.ar_aging_low_threshold,
                        'ar_aging_medium_threshold': self.ar_aging_medium_threshold,
                        'revenue_concentration_risk_threshold': self.revenue_concentration_risk_threshold,
                        'declining_trend_threshold': self.declining_trend_threshold,
                        'high_resale_priority_threshold': self.resale_priority_threshold
                    }
                    return threshold_map.get(threshold_type, 50.0)
            
            return MockConfig()
                
        except Exception as e:
            logger.warning(f"Failed to load business analytics config: {e}. Using defaults.")
            # Create a mock config object with default values
            class MockConfig:
                def __init__(self):
                    self.equipment_underperformer_threshold = 50.0
                    self.high_value_threshold = 500.0
                    self.low_turnover_threshold = 25.0
                    self.low_usage_threshold = 100.0
                    self.resale_priority_threshold = 10.0
                    self.ar_aging_low_threshold = 5.0
                    self.ar_aging_medium_threshold = 15.0
                    self.revenue_concentration_risk_threshold = 0.4
                    self.declining_trend_threshold = -0.1
                
                def get_threshold(self, threshold_type: str):
                    return getattr(self, threshold_type, 50.0)
            
            return MockConfig()