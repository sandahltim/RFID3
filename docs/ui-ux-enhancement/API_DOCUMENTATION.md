# RFID3 Enhanced Dashboard API Documentation

**API Version:** 2.0.0  
**Base URL:** `/api/enhanced/`  
**Last Updated:** September 3, 2025

---

## 📋 API OVERVIEW

The Enhanced Dashboard API provides 13 comprehensive endpoints for accessing multi-source equipment rental data, predictive analytics, and data reconciliation features. All endpoints return JSON responses and support role-based access patterns.

### **Authentication & Authorization**
- **Authentication:** Uses existing Flask session management
- **Rate Limiting:** 200 requests/day, 50 requests/hour per IP
- **CORS:** Enabled for cross-origin dashboard access

### **Response Format**
All API endpoints follow a consistent response structure:
```json
{
  "success": true|false,
  "data": { ... },           // Main response data
  "error": "string",         // Error message if success=false
  "timestamp": "ISO8601",    // Response generation timestamp
  "metadata": { ... }        // Additional context information
}
```

---

## 🔄 1. DATA RECONCILIATION ENDPOINT

### **GET** `/api/enhanced/data-reconciliation`

**Purpose:** Compare and reconcile data from POS, RFID, and Financial systems to identify discrepancies and provide transparency.

#### **Query Parameters**
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `start_date` | String | No | Start date for analysis (YYYY-MM-DD) | `2025-08-27` |
| `end_date` | String | No | End date for analysis (YYYY-MM-DD) | `2025-09-03` |
| `store_code` | String | No | Specific store code | `3607`, `6800`, `728`, `8101` |
| `type` | String | No | Type of reconciliation | `revenue`, `utilization`, `inventory`, `comprehensive` |

#### **Response Example**
```json
{
  "success": true,
  "reconciliation": {
    "period": {
      "start_date": "2025-08-27",
      "end_date": "2025-09-03", 
      "days": 7,
      "store_code": "all_stores"
    },
    "revenue_sources": {
      "financial_system": {
        "value": 127500,
        "confidence": "high",
        "source": "scorecard_trends_data",
        "coverage": "100% (all stores)",
        "last_updated": "2025-09-03T10:30:00Z",
        "methodology": "Manager-reported weekly targets vs actual"
      },
      "pos_transactions": {
        "value": 125800,
        "confidence": "high",
        "source": "pos_transactions",
        "coverage": "100% (all transactions)", 
        "last_updated": "2025-09-03T10:15:00Z",
        "methodology": "Sum of completed contract amounts"
      },
      "rfid_correlation": {
        "value": 2245,
        "confidence": "low",
        "source": "combined_inventory",
        "coverage": "1.78% (290 correlated items)",
        "last_updated": "2025-09-03T10:45:00Z",
        "methodology": "Rental rate × RFID on-rent count"
      }
    },
    "variance_analysis": {
      "pos_vs_financial": {
        "absolute": -1700,
        "percentage": -1.33,
        "status": "excellent"
      },
      "rfid_coverage_gap": {
        "covered_revenue": 2245,
        "uncovered_estimated": 123555,
        "coverage_percentage": 1.78
      }
    },
    "recommendation": {
      "primary_source": "financial_system",
      "reasoning": "Financial and POS data closely aligned (<5% variance)",
      "confidence": "high", 
      "action": "Use financial system data (most complete for executive reporting)"
    }
  },
  "timestamp": "2025-09-03T10:45:23Z"
}
```

#### **Error Responses**
- **400:** Invalid date format or parameters
- **500:** Database connection error or service failure

---

## 🔮 2. PREDICTIVE ANALYTICS ENDPOINT

### **GET** `/api/enhanced/predictive-analytics`

**Purpose:** Access predictive models for revenue forecasting, equipment demand, and utilization optimization.

#### **Query Parameters**
| Parameter | Type | Required | Description | Options |
|-----------|------|----------|-------------|---------|
| `type` | String | No | Analytics type | `revenue_forecasts`, `equipment_demand`, `utilization_optimization`, `seasonal_patterns`, `business_trends`, `alerts`, `model_performance`, `comprehensive` |
| `horizon_weeks` | Integer | No | Forecast horizon | Default: 12, Max: 52 |

#### **Response Example (Revenue Forecasts)**
```json
{
  "success": true,
  "forecasts": {
    "total_revenue": {
      "predicted_values": [128500, 132400, 135800, 129200, 126800],
      "historical_average": 127500,
      "trend_slope": 245.3,
      "r2_score": 0.847,
      "confidence_intervals": [
        [115650, 141350],
        [119160, 145640], 
        [122220, 149380],
        [116280, 142120],
        [114120, 139480]
      ]
    },
    "revenue_3607": {
      "predicted_values": [32800, 34200, 35100, 33600, 32400],
      "historical_average": 33200,
      "trend_slope": 65.2,
      "r2_score": 0.782
    },
    "forecast_metadata": {
      "horizon_weeks": 5,
      "historical_periods": 26,
      "seasonal_factors": {
        "1": 0.95, "2": 0.89, "3": 1.05, "4": 1.12,
        "5": 1.18, "6": 1.25, "7": 1.22, "8": 1.15,
        "9": 1.08, "10": 0.98, "11": 0.85, "12": 0.92
      },
      "confidence_level": 0.8,
      "model_type": "linear_trend_with_seasonality"
    }
  },
  "data_coverage_note": "Forecasts based on financial/POS data. RFID enhancement will improve accuracy as coverage expands beyond 1.78%",
  "timestamp": "2025-09-03T10:45:23Z"
}
```

#### **Equipment Demand Response**
```json
{
  "success": true,
  "demand_predictions": {
    "Generators": {
      "stores": {
        "3607": {
          "utilization": 78.5,
          "revenue": 15400,
          "demand_category": "high_demand",
          "prediction": {
            "trend": "increasing",
            "confidence": "medium"
          }
        }
      },
      "total_revenue": 52800,
      "demand_trend": "increasing"
    }
  },
  "high_demand_items": [
    {
      "category": "Generators",
      "store": "6800", 
      "utilization": 87.3,
      "revenue_impact": 18200,
      "recommendation": "Consider additional inventory or redistribution"
    }
  ],
  "optimization_opportunities": [
    {
      "category": "Tables",
      "store": "728",
      "utilization": 23.1,
      "potential_savings": 4500,
      "recommendation": "Consider inventory reduction or redeployment"
    }
  ]
}
```

---

## ⏰ 3. MULTI-TIMEFRAME DATA ENDPOINT

### **GET** `/api/enhanced/multi-timeframe-data`

**Purpose:** Access financial and operational data across different time periods with comparison capabilities.

#### **Query Parameters**
| Parameter | Type | Required | Description | Options |
|-----------|------|----------|-------------|---------|
| `timeframe` | String | No | Time period type | `daily`, `weekly`, `monthly`, `quarterly`, `yearly`, `custom` |
| `metric` | String | No | Metric to analyze | `revenue`, `profitability`, `utilization`, `contracts`, `availability` |
| `store_code` | String | No | Store filter | `3607`, `6800`, `728`, `8101` |
| `periods` | Integer | No | Number of periods | Default: 26 |
| `start_date` | String | No | Custom start date | Required for `timeframe=custom` |
| `end_date` | String | No | Custom end date | Required for `timeframe=custom` |

#### **Response Example**
```json
{
  "success": true,
  "summary": {
    "current_3wk_avg": 127500,
    "previous_3wk_avg": 123200,
    "change_amount": 4300,
    "change_percentage": 3.49,
    "smoothed_trend": 8.2,
    "trend_direction": "increasing"
  },
  "time_series": [
    {
      "period": "2025-08-06",
      "value": 124500,
      "3wk_avg": 123800,
      "yoy_change": 5.2
    },
    {
      "period": "2025-08-13", 
      "value": 126200,
      "3wk_avg": 125100,
      "yoy_change": 6.8
    }
  ],
  "timeframe_metadata": {
    "timeframe": "weekly",
    "metric": "revenue", 
    "periods": 26,
    "store_code": null,
    "generated_at": "2025-09-03T10:45:23Z"
  }
}
```

---

## 🔗 4. CORRELATION DASHBOARD ENDPOINT

### **GET** `/api/enhanced/correlation-dashboard`

**Purpose:** Provide enhanced dashboard data with RFID correlation transparency and quality metrics.

#### **Query Parameters**
| Parameter | Type | Required | Description | Options |
|-----------|------|----------|-------------|---------|
| `type` | String | No | Dashboard type | `equipment_roi`, `correlation_quality`, `utilization_metrics`, `enhanced_kpis`, `comprehensive` |

#### **Response Example**
```json
{
  "success": true,
  "dashboard_data": {
    "correlation_summary": {
      "total_equipment_items": 16259,
      "rfid_correlated_items": 290,
      "correlation_percentage": 1.78,
      "high_confidence_correlations": 247,
      "medium_confidence_correlations": 32,
      "low_confidence_correlations": 11
    },
    "utilization_metrics": {
      "rfid_tracked_utilization": 67.3,
      "estimated_utilization": 52.1,
      "weighted_utilization": 52.8,
      "confidence_level": "medium"
    },
    "revenue_attribution": {
      "rfid_tracked_revenue": 45600,
      "estimated_revenue": 2234400,
      "total_revenue": 2280000,
      "attribution_accuracy": "low_coverage_high_precision"
    }
  }
}
```

---

## 🏪 5. ENHANCED STORE COMPARISON ENDPOINT

### **GET** `/api/enhanced/store-comparison`

**Purpose:** Compare store performance with multi-source data reconciliation and variance analysis.

#### **Query Parameters**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `weeks` | Integer | No | Analysis period (default: 26) |
| `reconciliation` | Boolean | No | Include reconciliation data (default: true) |

#### **Response Example**
```json
{
  "success": true,
  "store_performance": {
    "3607": {
      "store_name": "Wayzata",
      "weekly_avg_revenue": 32800,
      "utilization": 68.5,
      "equipment_count": 4205,
      "performance_rank": 2
    },
    "6800": {
      "store_name": "Brooklyn Park", 
      "weekly_avg_revenue": 45200,
      "utilization": 73.2,
      "equipment_count": 5890,
      "performance_rank": 1
    }
  },
  "store_reconciliation": {
    "3607": {
      "revenue_variance": {
        "pos_vs_financial": {
          "absolute": -420,
          "percentage": -1.28,
          "status": "excellent"
        }
      },
      "recommendation": {
        "primary_source": "financial_system",
        "confidence": "high"
      }
    }
  },
  "enhanced_metadata": {
    "analysis_weeks": 26,
    "includes_reconciliation": true,
    "rfid_coverage_note": "Analysis includes 1.78% RFID correlation data with POS estimates"
  }
}
```

---

## ⚙️ 6. DASHBOARD CONFIGURATION ENDPOINT

### **GET/POST** `/api/enhanced/dashboard-config`

**Purpose:** Manage role-based dashboard configurations and user preferences.

#### **GET Query Parameters**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `role` | String | No | User role (default: executive) |

#### **GET Response Example**
```json
{
  "success": true,
  "config": {
    "user_role": "executive",
    "default_timeframe": "monthly",
    "default_metrics": ["revenue", "profitability", "utilization"],
    "show_predictive": true,
    "show_reconciliation": true,
    "refresh_interval": 300,
    "chart_types": ["line", "bar", "scatter"],
    "alert_levels": ["high", "medium"],
    "data_sources": ["financial", "pos", "rfid"],
    "rfid_coverage": 1.78,
    "last_updated": "2025-09-03T10:45:23Z"
  }
}
```

#### **POST Request Body**
```json
{
  "default_timeframe": "weekly",
  "default_metrics": ["revenue", "utilization"],
  "refresh_interval": 180,
  "alert_levels": ["high"]
}
```

---

## 📊 7. YEAR-OVER-YEAR COMPARISON ENDPOINT

### **GET** `/api/enhanced/year-over-year`

**Purpose:** Enhanced YoY analysis with seasonal patterns and multi-source validation.

#### **Query Parameters**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `metric` | String | No | Metric to compare (default: revenue) |
| `store_code` | String | No | Store filter |
| `years` | Integer | No | Years to compare (default: 3) |

#### **Response Example**
```json
{
  "success": true,
  "year_over_year": {
    "2025": {
      "total": 6630000,
      "average_weekly": 127500,
      "growth_rate": 8.3
    },
    "2024": {
      "total": 6120000,
      "average_weekly": 117692,
      "growth_rate": 12.1
    },
    "2023": {
      "total": 5460000,
      "average_weekly": 105000,
      "growth_rate": 15.8
    }
  },
  "seasonal_patterns": {
    "1": {"month_name": "January", "seasonal_factor": 0.95},
    "5": {"month_name": "May", "seasonal_factor": 1.18},
    "7": {"month_name": "July", "seasonal_factor": 1.22}
  },
  "comparison_metadata": {
    "metric": "revenue",
    "comparison_years": 3,
    "data_note": "YoY comparison based on scorecard and P&L data."
  }
}
```

---

## 📋 8. DATA QUALITY REPORT ENDPOINT

### **GET** `/api/enhanced/data-quality-report`

**Purpose:** Comprehensive data quality assessment across all integrated systems.

#### **Response Example**
```json
{
  "success": true,
  "data_quality_overview": {
    "rfid_correlation_coverage": 1.78,
    "pos_data_completeness": 98.5,
    "financial_data_coverage": 100.0,
    "overall_quality_score": 85.2
  },
  "system_specific_quality": {
    "rfid_correlations": {
      "total_correlations": 290,
      "high_confidence": 247,
      "accuracy_rate": 94.2
    },
    "cross_system_health": {
      "overall_score": 87,
      "status": "good",
      "issues": ["Low RFID coverage (1.78%)"]
    }
  },
  "improvement_recommendations": [
    "Expand RFID correlation coverage from 1.78% to target 25% within 6 months",
    "Implement automated data validation for CSV imports",
    "Create real-time data quality monitoring dashboard"
  ]
}
```

---

## 📱 9. MOBILE DASHBOARD ENDPOINT

### **GET** `/api/enhanced/mobile-dashboard`

**Purpose:** Mobile-optimized dashboard data with reduced payload and essential metrics.

#### **Query Parameters**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `role` | String | No | User role for data filtering |
| `store_code` | String | No | Store code for manager/operational roles |

#### **Executive Mobile Response**
```json
{
  "success": true,
  "mobile_optimized": true,
  "user_role": "executive",
  "executive_summary": {
    "weekly_revenue": 127500,
    "trend": "up",
    "trend_percentage": 12.3,
    "top_performing_store": "Brooklyn Park",
    "alerts_count": 3
  },
  "quick_actions": [
    {"label": "Refresh Data", "action": "refresh"},
    {"label": "View Alerts", "action": "alerts"},
    {"label": "Search Equipment", "action": "search"}
  ]
}
```

#### **Manager Mobile Response**
```json
{
  "success": true,
  "mobile_optimized": true,
  "user_role": "manager",
  "store_code": "6800",
  "manager_summary": {
    "store_utilization": 73.2,
    "total_items": 5890,
    "revenue_today": 6800,
    "available_equipment": 1574
  },
  "quick_actions": [
    {"label": "Check Inventory", "action": "inventory"},
    {"label": "View Tasks", "action": "tasks"}
  ]
}
```

---

## 🩺 10. HEALTH CHECK ENDPOINT

### **GET** `/api/enhanced/health-check`

**Purpose:** Monitor API and service health status.

#### **Response Example**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-03T10:45:23Z",
  "services": {
    "data_reconciliation": "operational",
    "predictive_analytics": "operational", 
    "enhanced_executive": "operational",
    "financial_analytics": "operational"
  },
  "data_coverage": {
    "rfid_correlation_coverage": 1.78,
    "scorecard_data_weeks": 196,
    "payroll_data_records": 328,
    "pl_data_records": 1818
  },
  "api_version": "2.0.0",
  "last_data_update": "2025-09-03T10:30:15Z"
}
```

---

## 📊 ADDITIONAL ENDPOINTS

### **11. Business Trend Analysis**
```http
GET /api/enhanced/predictive-analytics?type=business_trends
```

### **12. Seasonal Pattern Analysis**
```http
GET /api/enhanced/predictive-analytics?type=seasonal_patterns
```

### **13. Equipment ROI Analysis**
```http
GET /api/enhanced/correlation-dashboard?type=equipment_roi
```

---

## 🔧 ERROR HANDLING

### **Standard Error Response**
```json
{
  "success": false,
  "error": "Detailed error message",
  "error_code": "DATA_RECONCILIATION_FAILED",
  "timestamp": "2025-09-03T10:45:23Z",
  "request_id": "req_abc123"
}
```

### **Common HTTP Status Codes**
- **200:** Successful request
- **400:** Bad request (invalid parameters)
- **401:** Unauthorized (authentication required)
- **403:** Forbidden (insufficient permissions)
- **404:** Endpoint not found
- **429:** Rate limit exceeded
- **500:** Internal server error
- **503:** Service temporarily unavailable

---

## 🚀 RATE LIMITING

### **Default Limits**
- **200 requests per day** per IP address
- **50 requests per hour** per IP address
- **10 requests per minute** for compute-intensive endpoints

### **Rate Limit Headers**
```
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 47
X-RateLimit-Reset: 1693742400
```

---

## 🔒 SECURITY CONSIDERATIONS

### **Data Privacy**
- No PII or sensitive customer data exposed
- Financial data aggregated only
- Equipment-level data anonymized when possible

### **Input Validation**
- SQL injection prevention through parameterized queries
- Date format validation (YYYY-MM-DD)
- Numeric range validation for periods/quantities
- Store code whitelist validation

### **Audit Logging**
All API requests are logged with:
- Timestamp
- IP address
- Endpoint accessed  
- Parameters provided
- Response time
- User role (if authenticated)

---

This API documentation provides complete reference for all 13 enhanced dashboard endpoints, enabling developers to integrate with the RFID3 system effectively while maintaining data transparency and quality standards.

