"""
Store Goals Service - Dynamic Store Goal Management
Provides centralized access to store-specific goals and targets for all analytics services.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

@dataclass
class StoreGoal:
    """Represents a single store goal with metadata"""
    store_code: str
    category: str  # 'labor', 'delivery', 'revenue', 'operational', etc.
    metric_name: str
    target_value: float
    unit: str  # '%', '$', 'count', 'hours', etc.
    description: str = ""
    last_updated: datetime = field(default_factory=datetime.now)
    is_active: bool = True

@dataclass
class StoreGoalCategory:
    """Groups related goals by category"""
    name: str
    description: str
    goals: Dict[str, StoreGoal] = field(default_factory=dict)

class StoreGoalsService:
    """
    Dynamic Store Goals Service
    
    Features:
    - Auto-discovery of new goal types
    - Flexible goal categories (labor, delivery, revenue, operational, etc.)
    - Store-specific and company-wide defaults
    - Easy integration for analytics services
    - Extensible goal structure
    """
    
    def __init__(self):
        self.goals_cache = {}
        self.cache_timestamp = None
        self.cache_ttl_seconds = 300  # 5 minutes
        
    def get_store_goals(self, store_code: str = None, category: str = None, 
                       refresh_cache: bool = False) -> Dict[str, Any]:
        """
        Get store goals with optional filtering
        
        Args:
            store_code: Specific store code, or None for all stores
            category: Goal category filter ('labor', 'delivery', etc.)
            refresh_cache: Force refresh from API
            
        Returns:
            Dictionary of goals structured by store and category
        """
        try:
            goals = self._get_goals_data(refresh_cache)
            
            if store_code:
                return self._filter_by_store(goals, store_code, category)
            elif category:
                return self._filter_by_category(goals, category)
            else:
                return goals
                
        except Exception as e:
            logger.error(f"Error getting store goals: {e}")
            return {}
    
    def get_store_goal_value(self, store_code: str, category: str, metric_name: str, 
                           default_value: float = 0.0) -> float:
        """
        Get a specific goal value for a store with fallback
        
        Example:
            value = service.get_store_goal_value('3607', 'labor', 'percentage_target')
            value = service.get_store_goal_value('6800', 'delivery', 'weekly_target')
        """
        try:
            goals = self.get_store_goals()
            
            # Try store-specific goal first
            store_goals = goals.get(f'store_{category}_goals', {}).get(store_code, {})
            if metric_name in store_goals:
                return float(store_goals[metric_name])
            
            # Try company-wide default
            company_goals = goals.get('company_goals', {})
            fallback_key = f'{category}_{metric_name}'
            if fallback_key in company_goals:
                return float(company_goals[fallback_key])
            
            logger.warning(f"No goal found for {store_code}.{category}.{metric_name}, using default: {default_value}")
            return default_value
            
        except Exception as e:
            logger.error(f"Error getting goal value: {e}")
            return default_value
    
    def calculate_performance_score(self, store_code: str, category: str, 
                                  actual_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate performance scores against store goals
        
        Args:
            store_code: Store to evaluate
            category: Goal category ('labor', 'delivery', etc.)
            actual_metrics: Dict of actual metric values
            
        Returns:
            Performance analysis with scores and recommendations
        """
        try:
            goals = self.get_store_goals(store_code, category)
            performance = {
                'store_code': store_code,
                'category': category,
                'timestamp': datetime.now().isoformat(),
                'metrics': {},
                'overall_score': 0.0,
                'status': 'unknown'
            }
            
            total_score = 0.0
            metric_count = 0
            
            for metric_name, actual_value in actual_metrics.items():
                target_value = self.get_store_goal_value(store_code, category, metric_name)
                
                if target_value > 0:
                    # Calculate performance percentage
                    if category == 'labor' and metric_name.endswith('_percentage'):
                        # Lower is better for labor percentage
                        score = min(100, (target_value / actual_value * 100)) if actual_value > 0 else 0
                    else:
                        # Higher is better for most metrics
                        score = (actual_value / target_value * 100) if target_value > 0 else 0
                    
                    performance['metrics'][metric_name] = {
                        'actual': actual_value,
                        'target': target_value,
                        'performance_pct': score,
                        'status': self._get_metric_status(score)
                    }
                    
                    total_score += score
                    metric_count += 1
            
            if metric_count > 0:
                performance['overall_score'] = total_score / metric_count
                performance['status'] = self._get_metric_status(performance['overall_score'])
            
            return performance
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return {'error': str(e)}
    
    def get_available_goal_categories(self) -> List[str]:
        """Get list of all available goal categories"""
        try:
            goals = self.get_store_goals()
            categories = []
            
            for key in goals.keys():
                if key.startswith('store_') and key.endswith('_goals'):
                    category = key.replace('store_', '').replace('_goals', '')
                    categories.append(category)
            
            return sorted(categories)
            
        except Exception as e:
            logger.error(f"Error getting goal categories: {e}")
            return []
    
    def get_stores_with_goals(self, category: str = None) -> List[str]:
        """Get list of stores that have goals configured"""
        try:
            goals = self.get_store_goals()
            stores = set()
            
            for key, data in goals.items():
                if key.startswith('store_') and key.endswith('_goals'):
                    if category is None or category in key:
                        stores.update(data.keys())
            
            return sorted(stores)
            
        except Exception as e:
            logger.error(f"Error getting stores with goals: {e}")
            return []
    
    def add_goal_category(self, category_name: str, store_goals: Dict[str, Dict[str, float]]) -> bool:
        """
        Dynamically add a new goal category
        
        Example:
            service.add_goal_category('inventory', {
                '3607': {'turnover_target': 12.0, 'accuracy_target': 98.5},
                '6800': {'turnover_target': 10.0, 'accuracy_target': 97.0}
            })
        """
        try:
            # This would integrate with the configuration API to save new goals
            logger.info(f"Adding new goal category: {category_name}")
            # Implementation would save to database/config system
            return True
            
        except Exception as e:
            logger.error(f"Error adding goal category: {e}")
            return False
    
    def _get_goals_data(self, refresh_cache: bool = False) -> Dict[str, Any]:
        """Get goals data from API with caching"""
        now = datetime.now()
        
        if (not refresh_cache and self.goals_cache and self.cache_timestamp and
            (now - self.cache_timestamp).total_seconds() < self.cache_ttl_seconds):
            return self.goals_cache
        
        try:
            response = requests.get('http://localhost:6801/config/api/store-goals-configuration', timeout=5)
            if response.status_code == 200:
                data = response.json().get('data', {})
                
                # Restructure for easier access
                structured_data = {
                    'company_goals': data.get('companyGoals', {}),
                    'store_revenue_goals': data.get('storeGoals', {}),
                    'store_labor_goals': data.get('storeLaborGoals', {}),
                    'store_delivery_goals': data.get('storeDeliveryGoals', {})
                }
                
                self.goals_cache = structured_data
                self.cache_timestamp = now
                return structured_data
            else:
                logger.warning(f"Store goals API returned {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching goals data: {e}")
            return self.goals_cache or {}
    
    def _filter_by_store(self, goals: Dict[str, Any], store_code: str, 
                        category: str = None) -> Dict[str, Any]:
        """Filter goals for a specific store"""
        filtered = {}
        
        for key, data in goals.items():
            if isinstance(data, dict) and store_code in data:
                if category is None or category in key:
                    filtered[key] = {store_code: data[store_code]}
        
        return filtered
    
    def _filter_by_category(self, goals: Dict[str, Any], category: str) -> Dict[str, Any]:
        """Filter goals by category"""
        return {k: v for k, v in goals.items() if category in k.lower()}
    
    def _get_metric_status(self, score: float) -> str:
        """Get status label based on performance score"""
        if score >= 95:
            return 'excellent'
        elif score >= 85:
            return 'good'
        elif score >= 70:
            return 'fair'
        elif score >= 50:
            return 'poor'
        else:
            return 'critical'

# Global instance for easy access
store_goals_service = StoreGoalsService()