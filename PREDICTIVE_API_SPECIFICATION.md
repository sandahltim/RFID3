# Predictive Analytics API Specification
**Version**: 1.0  
**Date**: August 31, 2025  
**Base URL**: `/api/predictive`

## 📋 API Overview

This document provides comprehensive specifications for all predictive analytics API endpoints, including request/response formats, authentication, error handling, and usage examples.

### Authentication
All endpoints require authentication via API key or session-based authentication integrated with the existing Flask application.

### Response Format
All responses follow a consistent JSON structure:

```json
{
  "success": true|false,
  "data": {},
  "message": "Human readable message",
  "timestamp": "2025-08-31T10:30:00Z",
  "request_id": "uuid",
  "execution_time_ms": 150
}
```

---

## 🔮 Demand Forecasting APIs

### 1. Generate Demand Forecast

**Endpoint**: `GET /api/predictive/demand/forecast`

**Description**: Generate demand forecast using ensemble ML models with external factors

**Parameters**:
```json
{
  "weeks": 4,                    // Forecast horizon (1-52 weeks)
  "category": "chairs",          // Item category filter
  "store": "all",               // Store filter
  "confidence_level": 0.8,      // Minimum confidence threshold
  "include_external_factors": true,
  "model_type": "ensemble"      // ensemble|prophet|random_forest|linear
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "forecast_period": "4 weeks",
    "store_filter": "all",
    "category_filter": "chairs",
    "model_ensemble": {
      "prophet_weight": 0.5,
      "random_forest_weight": 0.3,
      "linear_weight": 0.2
    },
    "predictions": [
      {
        "week_starting": "2025-09-01",
        "predicted_demand": 125.5,
        "confidence_score": 0.85,
        "confidence_lower": 98.2,
        "confidence_upper": 152.8,
        "key_factors": {
          "seasonal_effect": 1.3,
          "weather_impact": "positive",
          "economic_confidence": "stable",
          "event_calendar_impact": "wedding_season"
        },
        "business_impact": {
          "revenue_opportunity": 5650.0,
          "inventory_requirement": 28,
          "stockout_risk": 0.15
        }
      }
    ],
    "external_factors_considered": [
      "weather_temperature_forecast",
      "economic_consumer_confidence",
      "seasonal_wedding_season",
      "local_event_calendar"
    ],
    "model_performance": {
      "mae": 8.5,
      "rmse": 12.3,
      "mape": 6.8,
      "accuracy_trend": "improving"
    },
    "recommendations": [
      "Increase chair inventory by 15 units for week of 2025-09-01",
      "Consider promotional pricing for optimal revenue capture",
      "Monitor weather forecasts for outdoor event demand"
    ]
  },
  "message": "Demand forecast generated successfully",
  "timestamp": "2025-08-31T10:30:00Z"
}
```

### 2. Get Historical Accuracy

**Endpoint**: `GET /api/predictive/demand/accuracy`

**Description**: Retrieve historical accuracy metrics for demand forecasting models

**Parameters**:
```json
{
  "days_back": 90,              // Historical period to analyze
  "model_type": "ensemble",     // Model type filter
  "category": "all",           // Category filter
  "metric": "mape"             // mae|rmse|mape|accuracy_score
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "accuracy_metrics": {
      "overall_accuracy": 0.82,
      "mae": 8.5,
      "rmse": 12.3,
      "mape": 6.8
    },
    "accuracy_by_category": {
      "chairs": {"accuracy": 0.85, "mae": 7.2},
      "tables": {"accuracy": 0.78, "mae": 9.8},
      "linens": {"accuracy": 0.88, "mae": 5.1}
    },
    "accuracy_trend": {
      "last_30_days": 0.82,
      "previous_30_days": 0.79,
      "trend": "improving"
    },
    "prediction_distribution": {
      "high_confidence": 0.65,      // >0.8 confidence
      "medium_confidence": 0.25,    // 0.6-0.8 confidence  
      "low_confidence": 0.10        // <0.6 confidence
    }
  },
  "message": "Accuracy metrics retrieved successfully"
}
```

### 3. Retrain Demand Models

**Endpoint**: `POST /api/predictive/demand/retrain`

**Description**: Trigger retraining of demand forecasting models

**Request Body**:
```json
{
  "model_types": ["prophet", "random_forest", "linear"],
  "training_period_days": 730,
  "validation_split": 0.2,
  "hyperparameter_tuning": true,
  "force_retrain": false
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "training_job_id": "train_job_20250831_103000",
    "models_scheduled": ["prophet", "random_forest", "linear"],
    "estimated_completion": "2025-08-31T12:00:00Z",
    "training_data_size": 15420,
    "validation_data_size": 3855
  },
  "message": "Model retraining initiated successfully"
}
```

---

## 🔧 Maintenance Prediction APIs

### 4. Get Maintenance Predictions

**Endpoint**: `GET /api/predictive/maintenance/schedule`

**Description**: Get maintenance predictions and optimal scheduling recommendations

**Parameters**:
```json
{
  "days_ahead": 30,             // Prediction horizon
  "equipment_filter": "all",    // Equipment type filter
  "min_failure_probability": 0.3,
  "include_cost_analysis": true,
  "sort_by": "priority"         // priority|date|cost|probability
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "maintenance_schedule": [
      {
        "equipment_id": "CHAIR_001_A",
        "equipment_type": "chair",
        "failure_probability": 0.75,
        "predicted_failure_date": "2025-09-15",
        "optimal_maintenance_date": "2025-09-08",
        "days_until_optimal": 8,
        "maintenance_type": "preventive",
        "estimated_cost": 125.50,
        "downtime_hours": 2,
        "business_impact": {
          "revenue_at_risk": 450.0,
          "replacement_cost": 2500.0,
          "total_cost_avoidance": 2824.50
        },
        "maintenance_factors": {
          "equipment_age_factor": 0.8,
          "usage_intensity_factor": 0.9,
          "quality_degradation_factor": 0.7,
          "last_maintenance_factor": 0.6
        },
        "confidence_score": 0.88,
        "priority": "high"
      }
    ],
    "summary": {
      "total_items_monitored": 1250,
      "high_priority_count": 15,
      "medium_priority_count": 45,
      "total_estimated_cost": 8750.0,
      "total_cost_avoidance": 45200.0,
      "average_confidence": 0.82
    },
    "recommendations": [
      "Schedule immediate inspection for 3 high-priority items",
      "Order replacement parts for items requiring major maintenance",
      "Consider equipment lifecycle replacement for items with repeated issues"
    ]
  },
  "message": "Maintenance predictions generated successfully"
}
```

### 5. Get Equipment Health Score

**Endpoint**: `GET /api/predictive/maintenance/health/{equipment_id}`

**Description**: Get detailed health analysis for specific equipment

**Response**:
```json
{
  "success": true,
  "data": {
    "equipment_id": "CHAIR_001_A",
    "overall_health_score": 0.72,
    "health_trend": "declining",
    "health_factors": {
      "mechanical_condition": 0.75,
      "aesthetic_condition": 0.68,
      "usage_wear": 0.70,
      "maintenance_history": 0.85
    },
    "failure_probability_timeline": {
      "7_days": 0.15,
      "30_days": 0.35,
      "90_days": 0.65,
      "365_days": 0.85
    },
    "maintenance_recommendations": [
      {
        "action": "Replace fabric cushion",
        "urgency": "medium",
        "estimated_cost": 85.0,
        "impact_on_health": 0.15
      }
    ],
    "usage_statistics": {
      "total_rentals": 145,
      "average_rental_duration": 3.2,
      "damage_incidents": 2,
      "last_maintenance": "2025-07-15"
    }
  },
  "message": "Equipment health analysis completed"
}
```

---

## 📊 Quality Analytics APIs

### 6. Quality Degradation Prediction

**Endpoint**: `GET /api/predictive/quality/degradation/{item_id}`

**Description**: Predict quality degradation timeline for specific item

**Response**:
```json
{
  "success": true,
  "data": {
    "item_id": "TABLE_052_B",
    "current_quality_score": 0.78,
    "quality_trend": "stable_decline",
    "degradation_prediction": {
      "30_days": 0.74,
      "90_days": 0.68,
      "180_days": 0.58,
      "365_days": 0.45
    },
    "quality_factors": {
      "usage_intensity": 0.85,
      "environmental_exposure": 0.70,
      "maintenance_quality": 0.90,
      "material_aging": 0.75
    },
    "replacement_recommendations": {
      "optimal_replacement_date": "2026-03-15",
      "replacement_confidence": 0.82,
      "cost_benefit_analysis": {
        "current_market_value": 850.0,
        "replacement_cost": 1200.0,
        "revenue_impact": 2400.0
      }
    },
    "actionable_insights": [
      "Schedule deep cleaning to extend quality lifecycle",
      "Consider protective treatments for outdoor use",
      "Monitor closely - approaching quality threshold"
    ]
  },
  "message": "Quality degradation analysis completed"
}
```

### 7. Quality Optimization Recommendations

**Endpoint**: `GET /api/predictive/quality/optimization`

**Description**: Get quality improvement recommendations across inventory

**Parameters**:
```json
{
  "category_filter": "all",
  "quality_threshold": 0.7,
  "optimization_budget": 5000,
  "priority": "roi"              // roi|quality_impact|cost
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "optimization_opportunities": [
      {
        "category": "chairs",
        "items_affected": 25,
        "avg_quality_score": 0.65,
        "recommended_action": "fabric_replacement_program",
        "investment_required": 1850.0,
        "quality_improvement": 0.20,
        "roi_estimate": 3.2,
        "payback_period_months": 4.5
      }
    ],
    "budget_allocation": {
      "total_budget": 5000.0,
      "recommended_allocation": {
        "preventive_maintenance": 2500.0,
        "quality_improvements": 1850.0,
        "emergency_reserve": 650.0
      }
    },
    "expected_outcomes": {
      "avg_quality_improvement": 0.15,
      "extended_lifecycle_months": 8,
      "revenue_protection": 12500.0
    }
  },
  "message": "Quality optimization recommendations generated"
}
```

---

## 💰 Pricing Optimization APIs

### 8. Dynamic Pricing Recommendations

**Endpoint**: `GET /api/predictive/pricing/recommendations`

**Description**: Get dynamic pricing recommendations based on demand, quality, and market conditions

**Parameters**:
```json
{
  "category": "all",
  "time_horizon_days": 30,
  "optimization_goal": "revenue",    // revenue|utilization|profit
  "market_conditions": "auto",       // auto|competitive|premium
  "include_competitor_analysis": true
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "pricing_recommendations": [
      {
        "item_id": "CHAIR_GOLD_001",
        "current_price": 45.0,
        "recommended_price": 52.0,
        "price_change_percent": 15.6,
        "optimization_factors": {
          "demand_elasticity": -0.8,
          "quality_premium": 1.2,
          "seasonal_multiplier": 1.1,
          "competitive_position": "premium"
        },
        "expected_impact": {
          "revenue_change_percent": 8.5,
          "utilization_change_percent": -3.2,
          "profit_margin_improvement": 12.3
        },
        "confidence_score": 0.85,
        "recommendation_validity_days": 14
      }
    ],
    "market_analysis": {
      "competitor_average_pricing": {
        "chairs_standard": 42.0,
        "chairs_premium": 55.0,
        "market_position": "competitive"
      },
      "demand_trends": {
        "current_demand_index": 1.15,
        "predicted_demand_trend": "increasing",
        "seasonality_factor": 1.1
      }
    },
    "portfolio_optimization": {
      "total_revenue_impact": 2850.0,
      "average_price_increase": 8.2,
      "utilization_trade_off": -2.1
    }
  },
  "message": "Pricing recommendations generated successfully"
}
```

### 9. Price Elasticity Analysis

**Endpoint**: `GET /api/predictive/pricing/elasticity/{category}`

**Description**: Analyze price elasticity for specific category

**Response**:
```json
{
  "success": true,
  "data": {
    "category": "chairs",
    "price_elasticity": -1.2,
    "elasticity_interpretation": "elastic",
    "optimal_pricing_zone": {
      "min_price": 38.0,
      "max_price": 58.0,
      "sweet_spot_price": 47.0
    },
    "elasticity_by_quality": {
      "premium": -0.8,
      "standard": -1.2,
      "budget": -1.8
    },
    "revenue_optimization": {
      "current_revenue": 12450.0,
      "optimized_revenue": 14200.0,
      "revenue_improvement": 14.1
    },
    "sensitivity_analysis": [
      {
        "price_change_percent": 5,
        "demand_change_percent": -6,
        "revenue_change_percent": -1.3
      },
      {
        "price_change_percent": 10,
        "demand_change_percent": -12,
        "revenue_change_percent": -2.8
      }
    ]
  },
  "message": "Price elasticity analysis completed"
}
```

---

## 📦 Inventory Automation APIs

### 10. Restock Recommendations

**Endpoint**: `GET /api/predictive/inventory/restock-recommendations`

**Description**: Get intelligent restocking recommendations based on demand predictions

**Parameters**:
```json
{
  "category_filter": "all",
  "urgency_threshold": "medium",     // low|medium|high|critical
  "budget_constraint": 10000,
  "lead_time_days": 7,
  "optimization_goal": "cost_efficiency"  // cost_efficiency|service_level|roi
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "restock_recommendations": [
      {
        "item_category": "chairs_standard",
        "current_inventory": 15,
        "available_inventory": 12,
        "predicted_demand_30d": 45,
        "stockout_probability": 0.85,
        "recommended_order_quantity": 25,
        "optimal_order_date": "2025-09-02",
        "urgency": "high",
        "cost_analysis": {
          "unit_cost": 180.0,
          "total_order_cost": 4500.0,
          "carrying_cost_monthly": 135.0,
          "stockout_cost_risk": 2250.0
        },
        "roi_projection": {
          "revenue_protected": 11250.0,
          "investment_required": 4500.0,
          "roi_ratio": 2.5,
          "payback_period_days": 18
        },
        "supplier_information": {
          "preferred_supplier": "ACME_RENTALS",
          "lead_time_days": 5,
          "bulk_discount_available": true,
          "minimum_order_quantity": 20
        }
      }
    ],
    "optimization_summary": {
      "total_investment_required": 8750.0,
      "total_revenue_protected": 28500.0,
      "overall_roi": 3.26,
      "budget_utilization": 0.875,
      "service_level_improvement": 0.92
    },
    "automation_decisions": [
      {
        "item_category": "chairs_premium",
        "auto_approve_threshold_met": true,
        "order_quantity": 15,
        "scheduled_order_date": "2025-09-01",
        "confidence_score": 0.92
      }
    ]
  },
  "message": "Restock recommendations generated successfully"
}
```

### 11. Automated Restock Approval

**Endpoint**: `POST /api/predictive/inventory/approve-restock`

**Description**: Approve or modify automated restock recommendations

**Request Body**:
```json
{
  "restock_id": "restock_20250831_001",
  "action": "approve",           // approve|modify|reject
  "modifications": {
    "order_quantity": 20,
    "order_date": "2025-09-03"
  },
  "approval_reason": "High confidence prediction with strong ROI",
  "approver_id": "user_001"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "restock_id": "restock_20250831_001",
    "status": "approved",
    "order_details": {
      "item_category": "chairs_standard",
      "order_quantity": 20,
      "order_date": "2025-09-03",
      "estimated_delivery": "2025-09-10"
    },
    "financial_impact": {
      "order_cost": 3600.0,
      "expected_revenue": 9000.0,
      "roi_projection": 2.5
    },
    "next_actions": [
      "Purchase order will be generated automatically",
      "Supplier notification scheduled",
      "Inventory tracking updated"
    ]
  },
  "message": "Restock order approved successfully"
}
```

---

## 📋 Pack Management APIs

### 12. Pack Performance Analysis

**Endpoint**: `GET /api/predictive/packs/performance-analysis`

**Description**: Analyze pack utilization and profitability

**Parameters**:
```json
{
  "time_period_days": 90,
  "pack_type_filter": "all",
  "min_utilization_threshold": 0.3,
  "include_profitability": true
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "pack_performance": [
      {
        "pack_id": "WEDDING_PREMIUM_001",
        "pack_name": "Premium Wedding Package",
        "utilization_rate": 0.75,
        "average_rental_duration": 2.5,
        "rental_frequency": 12,
        "profitability_analysis": {
          "revenue_generated": 8450.0,
          "component_cost_basis": 3200.0,
          "gross_margin": 0.62,
          "roi_annualized": 2.64
        },
        "component_analysis": {
          "high_demand_components": ["chairs", "tables"],
          "low_demand_components": ["specialty_linens"],
          "bottleneck_components": ["centerpieces"]
        },
        "optimization_opportunities": {
          "recommended_action": "expand_pack_quantity",
          "potential_revenue_increase": 2100.0,
          "investment_required": 1600.0
        }
      }
    ],
    "portfolio_summary": {
      "total_packs_analyzed": 45,
      "average_utilization": 0.58,
      "total_revenue_contribution": 125450.0,
      "underperforming_packs": 8,
      "optimization_potential": 15200.0
    }
  },
  "message": "Pack performance analysis completed"
}
```

### 13. Pack Creation Recommendations

**Endpoint**: `GET /api/predictive/packs/creation-recommendations`

**Description**: Get recommendations for creating new packs based on demand patterns

**Response**:
```json
{
  "success": true,
  "data": {
    "pack_recommendations": [
      {
        "recommended_pack_name": "Corporate Event Essentials",
        "target_market": "corporate_events",
        "component_suggestions": [
          {"item_type": "conference_chairs", "quantity": 50},
          {"item_type": "presentation_tables", "quantity": 8},
          {"item_type": "av_equipment", "quantity": 1}
        ],
        "demand_analysis": {
          "predicted_monthly_demand": 6,
          "seasonality_factor": 1.2,
          "market_size_potential": "medium"
        },
        "financial_projection": {
          "investment_required": 8500.0,
          "projected_monthly_revenue": 3200.0,
          "estimated_roi": 4.5,
          "break_even_months": 3.2
        },
        "competitive_analysis": {
          "market_gap_identified": true,
          "pricing_advantage": 0.15,
          "differentiation_factors": ["convenience", "cost_savings"]
        }
      }
    ],
    "market_insights": {
      "emerging_trends": ["hybrid_events", "outdoor_corporate"],
      "underserved_segments": ["small_corporate", "nonprofit"],
      "seasonal_opportunities": ["q4_corporate_parties"]
    }
  },
  "message": "Pack creation recommendations generated"
}
```

---

## 📊 System Management APIs

### 14. Model Performance Overview

**Endpoint**: `GET /api/predictive/models/performance`

**Description**: Get comprehensive performance metrics for all ML models

**Response**:
```json
{
  "success": true,
  "data": {
    "model_performance": {
      "demand_forecasting": {
        "accuracy": 0.82,
        "mae": 8.5,
        "last_trained": "2025-08-29T10:00:00Z",
        "prediction_volume_24h": 1250,
        "status": "healthy"
      },
      "maintenance_prediction": {
        "accuracy": 0.78,
        "precision": 0.85,
        "recall": 0.72,
        "last_trained": "2025-08-30T14:30:00Z",
        "prediction_volume_24h": 850,
        "status": "healthy"
      }
    },
    "system_health": {
      "overall_status": "healthy",
      "prediction_latency_avg_ms": 145,
      "cache_hit_rate": 0.85,
      "error_rate_24h": 0.002,
      "uptime_percentage": 99.8
    },
    "usage_statistics": {
      "total_predictions_24h": 2850,
      "api_calls_24h": 1250,
      "unique_users_24h": 45,
      "most_requested_service": "demand_forecasting"
    }
  },
  "message": "Model performance overview retrieved"
}
```

### 15. System Health Check

**Endpoint**: `GET /api/predictive/health`

**Description**: Comprehensive system health check

**Response**:
```json
{
  "success": true,
  "data": {
    "overall_status": "healthy",
    "components": {
      "database_connection": "healthy",
      "redis_cache": "healthy", 
      "ml_models": "healthy",
      "external_apis": "degraded",
      "feature_pipeline": "healthy"
    },
    "performance_metrics": {
      "avg_response_time_ms": 145,
      "memory_usage_percent": 68,
      "cpu_usage_percent": 45,
      "disk_usage_percent": 32
    },
    "alerts": [
      {
        "level": "warning",
        "component": "external_apis",
        "message": "Weather API response time elevated",
        "timestamp": "2025-08-31T10:25:00Z"
      }
    ],
    "recommendations": [
      "Monitor weather API performance",
      "Consider increasing cache TTL for external data"
    ]
  },
  "message": "System health check completed"
}
```

---

## ⚠️ Error Handling

### Standard Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "PREDICTION_FAILED",
    "message": "Unable to generate prediction due to insufficient data",
    "details": {
      "required_features": ["historical_demand", "seasonal_patterns"],
      "missing_features": ["historical_demand"],
      "suggestion": "Ensure item has at least 30 days of historical data"
    }
  },
  "timestamp": "2025-08-31T10:30:00Z",
  "request_id": "req_12345"
}
```

### Error Codes
- `INVALID_PARAMETERS`: Invalid request parameters
- `INSUFFICIENT_DATA`: Not enough data for prediction
- `MODEL_UNAVAILABLE`: ML model not loaded or failed
- `RATE_LIMIT_EXCEEDED`: API rate limit exceeded
- `SYSTEM_ERROR`: Internal system error
- `TIMEOUT`: Request timeout exceeded
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions

---

## 🔐 Rate Limiting

### Rate Limits by Endpoint Type
- **Real-time predictions**: 100 requests/minute
- **Batch operations**: 10 requests/minute  
- **Training operations**: 5 requests/hour
- **System queries**: 200 requests/minute

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1693478400
```

This comprehensive API specification provides the foundation for integrating predictive analytics capabilities into the existing RFID3 system while maintaining consistency with current API patterns and performance requirements.