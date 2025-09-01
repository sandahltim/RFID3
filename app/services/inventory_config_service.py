# app/services/inventory_config_service.py
# Inventory Configuration Service - Utilizes database-stored configurations
# Version: 2025-08-31 - Database Configuration Integration

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from flask import current_app
from .. import cache
from ..models.db_models import InventoryConfig
from .logger import get_logger

logger = get_logger(__name__)

class InventoryConfigService:
    """Service to manage and utilize inventory configuration settings from database"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes cache
        
    def get_config(self, config_key: str, default_value: Any = None) -> Any:
        """Get configuration value by key with caching"""
        cache_key = f"inventory_config:{config_key}"
        
        try:
            # Try cache first
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return json.loads(cached_value)
            
            # Query database
            config = InventoryConfig.query.filter_by(config_key=config_key).first()
            if config:
                config_value = json.loads(config.config_value)
                # Cache the result
                cache.set(cache_key, json.dumps(config_value), ex=self.cache_timeout)
                logger.debug(f"Retrieved config {config_key} from database")
                return config_value
            
            logger.warning(f"Config key '{config_key}' not found, using default: {default_value}")
            return default_value
            
        except Exception as e:
            logger.error(f"Error retrieving config {config_key}: {str(e)}")
            return default_value
    
    def get_alert_thresholds(self) -> Dict[str, Any]:
        """Get alert threshold configurations"""
        default_thresholds = {
            "stale_item_days": {"default": 360, "resale": 90, "pack": 120},
            "high_usage_threshold": 0.8,
            "low_usage_threshold": 0.2,
            "quality_decline_threshold": 2
        }
        
        return self.get_config("alert_thresholds", default_thresholds)
    
    def get_business_rules(self) -> Dict[str, Any]:
        """Get business rule configurations"""
        default_rules = {
            "resale_categories": ["Resale"],
            "pack_bin_locations": ["pack"],
            "rental_statuses": ["On Rent", "Delivered"],
            "available_statuses": ["Ready to Rent"],
            "service_statuses": ["Repair", "Needs to be Inspected"]
        }
        
        return self.get_config("business_rules", default_rules)
    
    def get_dashboard_settings(self) -> Dict[str, Any]:
        """Get dashboard display settings"""
        default_settings = {
            "default_date_range": 30,
            "critical_alert_limit": 50,
            "refresh_interval_minutes": 15,
            "show_resolved_alerts": False
        }
        
        return self.get_config("dashboard_settings", default_settings)
    
    def is_stale_item(self, last_transaction_date: datetime, category: str = "default") -> bool:
        """Check if an item is stale based on configuration thresholds"""
        if not last_transaction_date:
            return True
            
        thresholds = self.get_alert_thresholds()
        stale_days = thresholds.get("stale_item_days", {}).get(category, 360)
        
        stale_threshold_date = datetime.now() - timedelta(days=stale_days)
        return last_transaction_date < stale_threshold_date
    
    def is_high_usage_item(self, usage_rate: float) -> bool:
        """Check if item has high usage based on configuration"""
        thresholds = self.get_alert_thresholds()
        return usage_rate >= thresholds.get("high_usage_threshold", 0.8)
    
    def is_low_usage_item(self, usage_rate: float) -> bool:
        """Check if item has low usage based on configuration"""
        thresholds = self.get_alert_thresholds()
        return usage_rate <= thresholds.get("low_usage_threshold", 0.2)
    
    def is_quality_declining(self, quality_score: float) -> bool:
        """Check if item quality is declining based on configuration"""
        thresholds = self.get_alert_thresholds()
        return quality_score <= thresholds.get("quality_decline_threshold", 2)
    
    def is_rental_status(self, status: str) -> bool:
        """Check if status indicates item is on rental"""
        business_rules = self.get_business_rules()
        rental_statuses = business_rules.get("rental_statuses", ["On Rent", "Delivered"])
        return status in rental_statuses
    
    def is_available_status(self, status: str) -> bool:
        """Check if status indicates item is available for rent"""
        business_rules = self.get_business_rules()
        available_statuses = business_rules.get("available_statuses", ["Ready to Rent"])
        return status in available_statuses
    
    def is_service_status(self, status: str) -> bool:
        """Check if status indicates item needs service"""
        business_rules = self.get_business_rules()
        service_statuses = business_rules.get("service_statuses", ["Repair", "Needs to be Inspected"])
        return status in service_statuses
    
    def is_resale_category(self, category: str) -> bool:
        """Check if category is for resale items"""
        business_rules = self.get_business_rules()
        resale_categories = business_rules.get("resale_categories", ["Resale"])
        return category in resale_categories
    
    def is_pack_location(self, bin_location: str) -> bool:
        """Check if bin location is for pack items"""
        if not bin_location:
            return False
        business_rules = self.get_business_rules()
        pack_locations = business_rules.get("pack_bin_locations", ["pack"])
        return any(pack_loc.lower() in bin_location.lower() for pack_loc in pack_locations)
    
    def get_default_date_range(self) -> int:
        """Get default date range for dashboard views"""
        dashboard_settings = self.get_dashboard_settings()
        return dashboard_settings.get("default_date_range", 30)
    
    def get_critical_alert_limit(self) -> int:
        """Get limit for critical alerts displayed"""
        dashboard_settings = self.get_dashboard_settings()
        return dashboard_settings.get("critical_alert_limit", 50)
    
    def should_show_resolved_alerts(self) -> bool:
        """Check if resolved alerts should be shown"""
        dashboard_settings = self.get_dashboard_settings()
        return dashboard_settings.get("show_resolved_alerts", False)
    
    def get_refresh_interval(self) -> int:
        """Get dashboard refresh interval in minutes"""
        dashboard_settings = self.get_dashboard_settings()
        return dashboard_settings.get("refresh_interval_minutes", 15)
    
    def set_config(self, config_key: str, config_value: Dict[str, Any], description: str = None, category: str = None):
        """Set configuration value in database and clear cache"""
        try:
            from .. import db
            
            config = InventoryConfig.query.filter_by(config_key=config_key).first()
            if config:
                config.config_value = json.dumps(config_value)
                config.updated_at = datetime.now()
                if description:
                    config.description = description
            else:
                config = InventoryConfig(
                    config_key=config_key,
                    config_value=json.dumps(config_value),
                    description=description,
                    category=category
                )
                db.session.add(config)
            
            db.session.commit()
            
            # Clear cache
            cache_key = f"inventory_config:{config_key}"
            cache.delete(cache_key)
            
            logger.info(f"Updated inventory config: {config_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting config {config_key}: {str(e)}")
            if 'db' in locals():
                db.session.rollback()
            return False
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate all configuration settings and return status"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "configurations": {}
        }
        
        try:
            # Check alert thresholds
            thresholds = self.get_alert_thresholds()
            if not isinstance(thresholds.get("stale_item_days"), dict):
                validation_results["errors"].append("stale_item_days must be a dictionary")
                validation_results["valid"] = False
            
            # Check business rules
            rules = self.get_business_rules()
            required_rule_keys = ["resale_categories", "rental_statuses", "available_statuses"]
            for key in required_rule_keys:
                if not isinstance(rules.get(key), list):
                    validation_results["errors"].append(f"business_rules.{key} must be a list")
                    validation_results["valid"] = False
            
            # Check dashboard settings
            settings = self.get_dashboard_settings()
            if not isinstance(settings.get("default_date_range"), int):
                validation_results["warnings"].append("default_date_range should be an integer")
            
            validation_results["configurations"] = {
                "alert_thresholds": thresholds,
                "business_rules": rules,
                "dashboard_settings": settings
            }
            
        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Configuration validation error: {str(e)}")
        
        return validation_results

# Global instance
inventory_config = InventoryConfigService()