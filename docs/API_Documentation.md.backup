# RFID3 System API Documentation

**Version:** 2025-08-28-v1  
**System:** RFID Inventory Management System  
**Author:** Technical Documentation Team  

---

## Overview

The RFID3 system provides comprehensive REST API endpoints for inventory management, analytics, and business intelligence. This documentation covers all available endpoints, parameters, authentication, and integration examples.

## Base Configuration

- **Base URL**: `http://localhost:8101` (production) or `http://localhost:5000` (development)
- **API Version**: v1
- **Authentication**: Session-based authentication (Flask sessions)
- **Content-Type**: `application/json`
- **Response Format**: JSON

---

## Authentication

The RFID3 system uses session-based authentication. All API endpoints require valid session cookies.

### Session Management
```python
import requests

# Create session for API calls
session = requests.Session()

# Session will maintain authentication across requests
response = session.get('http://localhost:8101/api/inventory/dashboard_summary')
```

---

## Core Inventory APIs

### 1. Dashboard Summary
Get high-level dashboard metrics with filtering capabilities.

**Endpoint:** `GET /api/inventory/dashboard_summary`

**Parameters:**
- `store` (string, optional): Store filter ('all', '6800', '3607', '8101', '728')
- `type` (string, optional): Inventory type filter ('all', 'Bulk', 'Serial')

**Response:**
```json
{
  "inventory_overview": {
    "total_items": 15420,
    "items_on_rent": 8750,
    "items_available": 4200,
    "items_in_service": 2470,
    "utilization_rate": 56.75
  },
  "health_metrics": {
    "health_score": 82.5,
    "active_alerts": 23,
    "critical_alerts": 2,
    "high_alerts": 5,
    "medium_alerts": 10,
    "low_alerts": 6
  },
  "activity_metrics": {
    "recent_scans": 1247,
    "scan_rate_per_day": 178.1
  },
  "timestamp": "2025-08-28T10:30:00Z"
}
```

**Example Usage:**
```bash
curl -X GET "http://localhost:8101/api/inventory/dashboard_summary?store=6800&type=Serial" \
  -H "Content-Type: application/json" \
  -b "session_cookie"
```

### 2. Business Intelligence Analytics
Get comprehensive POS business intelligence metrics.

**Endpoint:** `GET /api/inventory/business_intelligence`

**Parameters:**
- `store` (string, optional): Store filter
- `type` (string, optional): Inventory type filter

**Response:**
```json
{
  "store_analysis": {
    "distribution": [
      {
        "store_code": "6800",
        "item_count": 3245,
        "avg_sell_price": 125.50,
        "total_turnover": 45780.25
      }
    ],
    "total_stores": 4
  },
  "inventory_type_analysis": {
    "distribution": [
      {
        "type": "Serial",
        "count": 12450,
        "avg_price": 175.25
      }
    ],
    "total_types": 2
  },
  "financial_insights": {
    "items_with_data": 14250,
    "total_inventory_value": 2847500.75,
    "avg_sell_price": 199.85,
    "total_turnover_ytd": 847250.50,
    "avg_turnover_ytd": 59.45,
    "total_repair_costs": 12750.25,
    "avg_repair_cost": 25.50,
    "high_value_items": 1247,
    "high_value_threshold": 750.00
  },
  "manufacturer_insights": {
    "top_manufacturers": [
      {
        "manufacturer": "Acme Corp",
        "item_count": 2450,
        "avg_price": 225.75
      }
    ]
  },
  "filter_context": {
    "store_filter": "all",
    "type_filter": "all",
    "total_items_in_view": 15420
  },
  "timestamp": "2025-08-28T10:30:00Z"
}
```

### 3. Inventory Health Alerts
Retrieve and manage inventory health alerts with filtering and pagination.

**Endpoint:** `GET /api/inventory/alerts`

**Parameters:**
- `severity` (string, optional): Filter by severity ('critical', 'high', 'medium', 'low')
- `alert_type` (string, optional): Filter by type ('stale_item', 'low_usage', 'high_usage')
- `status` (string, optional): Filter by status ('active', 'resolved', 'dismissed'). Default: 'active'
- `limit` (integer, optional): Results per page (max 200). Default: 50
- `offset` (integer, optional): Pagination offset. Default: 0

**Response:**
```json
{
  "alerts": [
    {
      "id": 1247,
      "tag_id": "RT12345",
      "common_name": "Blue Party Tent",
      "category": "Tents",
      "subcategory": "Party Tents",
      "alert_type": "stale_item",
      "severity": "high",
      "days_since_last_scan": 45,
      "last_scan_date": "2025-07-14T08:30:00Z",
      "suggested_action": "Item not scanned in 45 days. Schedule inspection and update location.",
      "status": "active",
      "created_at": "2025-08-28T09:00:00Z"
    }
  ],
  "pagination": {
    "total": 23,
    "limit": 50,
    "offset": 0,
    "has_more": false
  }
}
```

### 4. Stale Items Analysis (Enhanced)
Revolutionary stale items analysis with transaction integration including Touch Scans.

**Endpoint:** `GET /api/inventory/stale_items`

**Parameters:**
- `limit` (integer, optional): Maximum results (max 1000). Default: 1000
- `offset` (integer, optional): Pagination offset. Default: 0

**Response:**
```json
{
  "stale_items": [
    {
      "tag_id": "RT12345",
      "serial_number": "SN789012",
      "client_name": "Party Rental Co",
      "rental_class_num": "101",
      "common_name": "Blue Party Tent",
      "quality": "Good",
      "bin_location": "A-15-C",
      "status": "Ready to Rent",
      "last_contract_num": "C-2024-15678",
      "notes": "Checked 2024-07-10",
      "master_last_scan": "2025-07-14T08:30:00Z",
      "category": "Tents",
      "subcategory": "Party Tents",
      "true_last_activity": "2025-08-15T14:22:00Z",
      "days_since_scan": 45,
      "true_days_stale": 13,
      "latest_scan_type": "Touch Scan",
      "touch_scan_count": 3,
      "status_scan_count": 1,
      "transaction_count": 4,
      "total_scan_count": 4,
      "activity_type": "MIXED_ACTIVITY",
      "activity_level": "MODERATE",
      "has_recent_activity": true,
      "is_touch_managed": true,
      "was_previously_hidden": true,
      "master_vs_transaction_days": {
        "master_days_stale": 45,
        "transaction_days_stale": 13,
        "difference": 32
      }
    }
  ],
  "thresholds_used": {
    "default_days": 30,
    "resale_days": 7,
    "pack_days": 14
  },
  "enhanced_summary": {
    "total_stale_items": 245,
    "items_with_transactions": 198,
    "items_with_touch_scans": 156,
    "items_with_status_scans": 187,
    "previously_hidden_by_old_analysis": 89,
    "activity_breakdown": {
      "MIXED_ACTIVITY": 89,
      "TOUCH_MANAGED": 67,
      "STATUS_ONLY": 42,
      "NO_RECENT_ACTIVITY": 47
    },
    "touch_managed_percentage": 63.7
  },
  "revolution_notes": {
    "enhancement": "Now includes ALL transaction activity including Touch Scans!",
    "impact": "Revealed 89 previously hidden actively managed items",
    "touch_scan_discovery": "156 items show active inventory management via Touch Scans"
  },
  "analysis_upgrade": "REVOLUTIONARY - True activity visibility achieved!"
}
```

### 5. Usage Patterns Analysis
Get comprehensive usage patterns based on transaction history.

**Endpoint:** `GET /api/inventory/usage_patterns`

**Parameters:**
- `days` (integer, optional): Analysis period in days. Default: 90

**Response:**
```json
{
  "usage_patterns": [
    {
      "category": "Tents",
      "subcategory": "Party Tents",
      "total_items": 450,
      "total_transactions": 1247,
      "activity_rate": 2.77,
      "transactions_per_item": 2.77
    }
  ],
  "analysis_period_days": 90,
  "generated_at": "2025-08-28T10:30:00Z"
}
```

### 6. Data Quality Analysis
Identify discrepancies between ItemMaster and Transaction data.

**Endpoint:** `GET /api/inventory/data_discrepancies`

**Response:**
```json
{
  "outdated_master_records": [
    {
      "tag_id": "RT12345",
      "common_name": "Blue Party Tent",
      "master_last_scan": "2025-07-14T08:30:00Z",
      "transaction_last_scan": "2025-08-15T14:22:00Z",
      "days_difference": 32
    }
  ],
  "items_without_transactions": [
    {
      "tag_id": "RT67890",
      "common_name": "Red Canopy",
      "status": "Ready to Rent",
      "created_date": "2024-01-15T00:00:00Z"
    }
  ],
  "orphaned_transactions": [
    {
      "tag_id": "ORPHAN123",
      "latest_scan": "2025-08-20T16:45:00Z",
      "transaction_count": 15
    }
  ]
}
```

---

## Enhanced Analytics APIs

### 1. Enhanced KPIs
Get accurate KPI data with proper calculations and trend analysis.

**Endpoint:** `GET /api/enhanced/dashboard/kpis`

**Parameters:**
- `weeks` (integer, optional): Analysis period in weeks. Default: 12
- `store` (string, optional): Store filter ('all' or specific store code)

**Response:**
```json
{
  "success": true,
  "data": {
    "total_items": 15420,
    "items_on_rent": 8750,
    "items_available": 4200,
    "items_in_service": 2470,
    "utilization_rate": 56.75,
    "total_revenue": 125750.50,
    "avg_efficiency": 247.85,
    "revenue_growth": 8.5,
    "utilization_trend": 2.1,
    "efficiency_trend": 5.3,
    "active_alerts": 23,
    "trends": {
      "revenue": [98500.25, 105200.75, 112800.50, 125750.50]
    },
    "period": "2025-06-04 to 2025-08-28",
    "filter_context": {
      "weeks": 12,
      "store": "all",
      "total_items_in_view": 15420
    }
  },
  "timestamp": "2025-08-28T10:30:00Z"
}
```

### 2. Store Performance Comparison
Get accurate store performance data with efficiency calculations.

**Endpoint:** `GET /api/enhanced/dashboard/store-performance`

**Parameters:**
- `weeks` (integer, optional): Analysis period in weeks. Default: 4

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "store_code": "6800",
      "store_name": "Brooklyn Park",
      "avg_revenue": 35750.25,
      "efficiency": 285.75,
      "labor_ratio": 0.28
    },
    {
      "store_code": "3607",
      "store_name": "Wayzata",
      "avg_revenue": 42150.50,
      "efficiency": 312.50,
      "labor_ratio": 0.24
    }
  ],
  "timestamp": "2025-08-28T10:30:00Z"
}
```

### 3. Inventory Distribution Analysis
Get accurate inventory distribution by status and store.

**Endpoint:** `GET /api/enhanced/dashboard/inventory-distribution`

**Parameters:**
- `store` (string, optional): Store filter

**Response:**
```json
{
  "success": true,
  "data": {
    "status_distribution": {
      "labels": ["On Rent", "Ready to Rent", "Repair", "Needs to be Inspected"],
      "values": [8750, 4200, 1850, 620]
    },
    "store_distribution": [
      {
        "store_code": "6800",
        "store_name": "Brooklyn Park",
        "item_count": 3245
      }
    ],
    "type_distribution": {
      "labels": ["Serial", "Bulk"],
      "values": [12450, 2970]
    },
    "totals": {
      "total_items": 15420,
      "unique_stores": 4,
      "unique_types": 2
    }
  },
  "timestamp": "2025-08-28T10:30:00Z"
}
```

### 4. Financial Metrics with POS Integration
Get enhanced financial metrics with POS data integration.

**Endpoint:** `GET /api/enhanced/dashboard/financial-metrics`

**Parameters:**
- `store` (string, optional): Store filter

**Response:**
```json
{
  "success": true,
  "data": {
    "financial_insights": {
      "total_inventory_value": 2847500.75,
      "avg_sell_price": 199.85,
      "items_with_data": 14250,
      "high_value_items": 1247,
      "high_value_inventory": 925750.25,
      "total_repair_costs": 12750.25,
      "total_turnover_ytd": 847250.50
    },
    "manufacturer_insights": {
      "top_manufacturers": [
        {
          "name": "Acme Corp",
          "item_count": 2450,
          "total_value": 425750.50,
          "avg_value": 173.77
        }
      ]
    },
    "coverage_metrics": {
      "data_completeness": 92.4,
      "high_value_percentage": 8.1
    }
  },
  "timestamp": "2025-08-28T10:30:00Z"
}
```

### 5. Utilization Analysis
Get detailed utilization analysis with accurate calculations.

**Endpoint:** `GET /api/enhanced/dashboard/utilization-analysis`

**Parameters:**
- `store` (string, optional): Store filter
- `days` (integer, optional): Analysis period in days. Default: 30

**Response:**
```json
{
  "success": true,
  "data": {
    "overall_utilization": 56.75,
    "category_utilization": [
      {
        "category": "Tents",
        "utilization_rate": 72.5,
        "on_rent": 326,
        "total": 450
      }
    ],
    "summary": {
      "total_items": 15420,
      "items_on_rent": 8750,
      "items_available": 6670,
      "high_utilization_categories": 12,
      "low_utilization_categories": 3
    }
  },
  "timestamp": "2025-08-28T10:30:00Z"
}
```

---

## Executive Dashboard APIs

### 1. Executive KPIs
Get executive-level KPI data for dashboard display.

**Endpoint:** `GET /bi/api/kpis`

**Parameters:**
- `end_date` (string, optional): End date in ISO format. Default: today
- `weeks` (integer, optional): Number of weeks to analyze. Default: 12

**Response:**
```json
{
  "current": {
    "revenue": 125750.50,
    "growth": 8.5,
    "margin": 45.2,
    "labor_ratio": 28.5,
    "turnover": 3.2
  },
  "trends": {
    "revenue": [98500.25, 105200.75, 112800.50, 125750.50],
    "margins": [42.1, 43.8, 44.5, 45.2]
  },
  "period": "2025-08-28"
}
```

### 2. Store Performance Analytics
Get detailed store performance metrics for comparison.

**Endpoint:** `GET /bi/api/store-performance`

**Parameters:**
- `store` (string, optional): Specific store code filter
- `end_date` (string, optional): End date in ISO format
- `periods` (integer, optional): Number of periods to include. Default: 26

**Response:**
```json
[
  {
    "period_ending": "2025-08-28",
    "store_code": "6800",
    "total_revenue": 35750.25,
    "rental_revenue": 32500.75,
    "labor_cost_ratio": 28.5,
    "revenue_per_hour": 285.75,
    "avg_wage_rate": 18.50,
    "revenue_growth_pct": 8.2,
    "new_contracts": 45,
    "pipeline": 12750.50,
    "ar_aging": 2.1
  }
]
```

### 3. Inventory Analytics
Get inventory performance analytics by rental class and store.

**Endpoint:** `GET /bi/api/inventory-analytics`

**Parameters:**
- `store` (string, optional): Store code filter
- `class` (string, optional): Rental class filter
- `end_date` (string, optional): End date in ISO format

**Response:**
```json
[
  {
    "store_code": "6800",
    "rental_class": "101",
    "class_name": "Party Tents",
    "total_units": 450,
    "available_units": 124,
    "on_rent_units": 326,
    "utilization_rate": 72.4,
    "turnover_rate": 3.2,
    "inventory_value": 87500.50,
    "roi_percentage": 15.8,
    "revenue_per_unit": 194.45
  }
]
```

### 4. Labor Analytics
Get labor efficiency and cost analysis.

**Endpoint:** `GET /bi/api/labor-analytics`

**Parameters:**
- `store` (string, optional): Store code filter
- `end_date` (string, optional): End date in ISO format
- `periods` (integer, optional): Number of periods. Default: 26

**Response:**
```json
[
  {
    "period": "2025-08-28",
    "store": "6800",
    "hours": 1250.5,
    "payroll": 23135.25,
    "wage_rate": 18.50,
    "labor_ratio": 28.5,
    "revenue_per_hour": 285.75,
    "contribution": 58115.25
  }
]
```

### 5. Predictive Analytics
Get predictive analytics and forecasting data.

**Endpoint:** `GET /bi/api/predictions`

**Parameters:**
- `metric` (string, optional): Metric to predict ('total_revenue', 'labor_cost', etc.). Default: 'total_revenue'
- `store` (string, optional): Store code filter
- `horizon` (integer, optional): Weeks ahead to predict. Default: 4

**Response:**
```json
[
  {
    "date": "2025-09-04",
    "store": "6800",
    "metric": "total_revenue",
    "prediction": 37250.75,
    "confidence_low": 34500.25,
    "confidence_high": 40125.50,
    "confidence": 85.5,
    "actual": null,
    "variance": null
  }
]
```

---

## Configuration APIs

### 1. Get Configuration
Retrieve current system configuration settings.

**Endpoint:** `GET /api/inventory/configuration`

**Response:**
```json
{
  "alert_thresholds": {
    "stale_item_days": {
      "default": 30,
      "resale": 7,
      "pack": 14
    },
    "high_usage_threshold": 0.8,
    "low_usage_threshold": 0.2,
    "quality_decline_threshold": 2
  },
  "business_rules": {
    "resale_categories": ["Resale"],
    "pack_bin_locations": ["pack"],
    "rental_statuses": ["On Rent", "Delivered"],
    "available_statuses": ["Ready to Rent"],
    "service_statuses": ["Repair", "Needs to be Inspected"]
  },
  "dashboard_settings": {
    "default_date_range": 30,
    "critical_alert_limit": 50,
    "refresh_interval_minutes": 15,
    "show_resolved_alerts": false
  }
}
```

### 2. Update Configuration
Update system configuration settings.

**Endpoint:** `PUT /api/inventory/configuration`

**Request Body:**
```json
{
  "alert_thresholds": {
    "stale_item_days": {
      "default": 45,
      "resale": 14,
      "pack": 21
    }
  },
  "dashboard_settings": {
    "refresh_interval_minutes": 10
  }
}
```

**Response:**
```json
{
  "message": "Configuration updated successfully"
}
```

---

## Alert Management APIs

### 1. Generate Alerts
Trigger automatic generation of inventory health alerts.

**Endpoint:** `POST /api/inventory/generate_alerts`

**Response:**
```json
{
  "success": true,
  "alerts_created": 47,
  "old_alerts_cleared": 23,
  "message": "Generated 47 health alerts"
}
```

---

## Data Import/Export APIs

### 1. Import Payroll Data
Import payroll data from CSV file for executive dashboard.

**Endpoint:** `POST /bi/import/payroll`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file`: CSV file containing payroll data

**Response:**
```json
{
  "records_imported": 156,
  "records_updated": 23,
  "errors": 2,
  "message": "Import completed successfully"
}
```

### 2. Import Scorecard Data
Import operational scorecard data from CSV file.

**Endpoint:** `POST /bi/import/scorecard`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file`: CSV file containing scorecard data

**Response:**
```json
{
  "records_imported": 89,
  "records_updated": 15,
  "errors": 1,
  "message": "Import completed successfully"
}
```

### 3. Export Executive Report
Export executive dashboard data as CSV file.

**Endpoint:** `GET /bi/export/executive-report`

**Parameters:**
- `end_date` (string, optional): End date for report
- `weeks` (integer, optional): Number of weeks to include. Default: 52

**Response:** CSV file download with executive KPI data

---

## Tab-Specific APIs

### Tab 1 - Rental Inventory
**Endpoint:** `GET /api/tab/1/data`

### Tab 2 - Open Contracts
**Endpoint:** `GET /api/tab/2/data`

### Tab 3 - Service Items
**Endpoint:** `GET /api/tab/3/data`

### Tab 4 - Laundry Contracts
**Endpoint:** `GET /api/tab/4/data`

### Tab 5 - Resale Inventory
**Endpoint:** `GET /api/tab/5/data`

### Tab 6 - Inventory Analytics
**Endpoint:** `GET /api/tab/6/data`  
*(See detailed inventory analytics endpoints above)*

### Tab 7 - Executive Dashboard
**Endpoint:** `GET /api/tab/7/data`  
*(See executive dashboard endpoints above)*

---

## Error Handling

### Standard Error Response Format
```json
{
  "success": false,
  "error": "Error message description",
  "details": "Additional technical details",
  "timestamp": "2025-08-28T10:30:00Z"
}
```

### Common HTTP Status Codes
- `200 OK`: Request successful
- `400 Bad Request`: Invalid parameters or request format
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error occurred

### Error Handling Examples

```python
import requests

try:
    response = requests.get('http://localhost:8101/api/inventory/dashboard_summary')
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except ValueError as e:
    print(f"Invalid JSON response: {e}")
```

---

## Rate Limiting

- **Standard endpoints**: 100 requests per minute per session
- **Heavy analytics endpoints**: 20 requests per minute per session
- **Import endpoints**: 5 requests per minute per session

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1693238400
```

---

## Integration Examples

### Python Integration
```python
import requests
import json
from datetime import datetime, timedelta

class RFIDClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_dashboard_summary(self, store='all', type='all'):
        """Get dashboard summary with filtering"""
        params = {'store': store, 'type': type}
        response = self.session.get(
            f"{self.base_url}/api/inventory/dashboard_summary",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_stale_items(self, limit=100):
        """Get stale items analysis"""
        params = {'limit': limit}
        response = self.session.get(
            f"{self.base_url}/api/inventory/stale_items",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_enhanced_kpis(self, weeks=12, store='all'):
        """Get enhanced KPI data"""
        params = {'weeks': weeks, 'store': store}
        response = self.session.get(
            f"{self.base_url}/api/enhanced/dashboard/kpis",
            params=params
        )
        response.raise_for_status()
        return response.json()

# Usage example
client = RFIDClient('http://localhost:8101')
dashboard = client.get_dashboard_summary(store='6800')
print(f"Total items: {dashboard['inventory_overview']['total_items']}")
```

### JavaScript Integration
```javascript
class RFIDAPIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }

    async getDashboardSummary(store = 'all', type = 'all') {
        const params = new URLSearchParams({ store, type });
        const response = await fetch(
            `${this.baseURL}/api/inventory/dashboard_summary?${params}`
        );
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }

    async getEnhancedKPIs(weeks = 12, store = 'all') {
        const params = new URLSearchParams({ weeks: weeks.toString(), store });
        const response = await fetch(
            `${this.baseURL}/api/enhanced/dashboard/kpis?${params}`
        );
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }

    async getStaleItems(limit = 100) {
        const params = new URLSearchParams({ limit: limit.toString() });
        const response = await fetch(
            `${this.baseURL}/api/inventory/stale_items?${params}`
        );
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
}

// Usage example
const client = new RFIDAPIClient('http://localhost:8101');

client.getDashboardSummary('6800')
    .then(data => {
        console.log('Total items:', data.inventory_overview.total_items);
        console.log('Utilization:', data.inventory_overview.utilization_rate);
    })
    .catch(error => {
        console.error('API error:', error);
    });
```

---

## Webhook Support

### Alert Webhooks
The system can send webhooks when critical alerts are generated.

**Configuration:**
```json
{
  "webhook_url": "https://your-system.com/rfid-alerts",
  "webhook_secret": "your-secret-key",
  "alert_types": ["critical", "high"]
}
```

**Webhook Payload:**
```json
{
  "event": "alert_created",
  "timestamp": "2025-08-28T10:30:00Z",
  "alert": {
    "id": 1247,
    "tag_id": "RT12345",
    "severity": "critical",
    "alert_type": "stale_item",
    "suggested_action": "Item not scanned in 60+ days"
  },
  "signature": "sha256=hash_of_payload"
}
```

---

## API Testing

### Postman Collection
A comprehensive Postman collection is available with all endpoints pre-configured.

**Download:** `/docs/RFID3_API_Collection.json`

### Test Data
Sample test data for API validation is available in:
- `/tests/fixtures/sample_inventory.json`
- `/tests/fixtures/sample_transactions.json`
- `/tests/fixtures/sample_alerts.json`

---

## Performance Considerations

### Caching
- Dashboard summary data is cached for 5 minutes
- Business intelligence data is cached for 15 minutes
- Configuration data is cached for 1 hour

### Optimization Tips
1. Use store and type filters to reduce data volume
2. Implement pagination for large result sets
3. Cache frequently accessed data on client side
4. Use webhooks instead of polling for alert updates

### Database Query Optimization
The system includes optimized queries with:
- Proper indexing on frequently queried fields
- Query result caching using Redis
- Materialized views for complex analytics
- Connection pooling for performance

---

## Support and Troubleshooting

### Common Issues

1. **Session Timeout**
   - Renew session cookies regularly
   - Implement session refresh logic

2. **Large Response Times**
   - Use filtering parameters to reduce data volume
   - Check system load and database performance

3. **Invalid Store Codes**
   - Verify store mapping configuration
   - Use the store configuration endpoint to get valid codes

### Debug Endpoints
- `GET /api/health`: System health check
- `GET /api/version`: API version information
- `GET /api/debug/stores`: Available store codes
- `GET /api/debug/config`: Current configuration values

### Logging
API requests are logged with:
- Request timestamp and duration
- Parameters and response size
- Error details and stack traces
- Performance metrics

---

**Documentation Version:** 1.0  
**Last Updated:** 2025-08-28  
**Next Review:** 2025-09-28
