# 🎯 Store Goals Integration Guide
**Dynamic Store Goal System - Easy Extension & Analytics Integration**

## 🌟 Overview
The Store Goals system provides a **dynamic, extensible framework** for managing store-specific targets and automatically integrating them into all analytics services.

## 🏗️ Architecture

### Core Components:
1. **StoreGoalsService** - Central hub for goal management
2. **Store Goals API** - REST endpoint for configuration 
3. **Analytics Integration** - Automatic goal discovery and usage
4. **Dynamic Categories** - Easy addition of new goal types

## 📊 Current Goal Categories

### **Labor Goals**
```python
{
    '3607': {'labor_percentage': 22.0, 'revenue_per_hour': 175},
    '6800': {'labor_percentage': 25.0, 'revenue_per_hour': 145}, 
    '728': {'labor_percentage': 28.0, 'revenue_per_hour': 120},
    '8101': {'labor_percentage': 26.0, 'revenue_per_hour': 160}
}
```

### **Delivery Goals**
```python
{
    '3607': {'weekly_deliveries': 65, 'avg_revenue_per_delivery': 450},
    '6800': {'weekly_deliveries': 45, 'avg_revenue_per_delivery': 380}, 
    '728': {'weekly_deliveries': 25, 'avg_revenue_per_delivery': 320},
    '8101': {'weekly_deliveries': 35, 'avg_revenue_per_delivery': 400}
}
```

## 🚀 How to Add New Goal Categories

### Step 1: Add to Store Goals API
```python
# In /app/routes/configuration_routes.py
'data': {
    'storeInventoryGoals': {  # NEW CATEGORY
        '3607': {'turnover_target': 12.0, 'accuracy_target': 98.5},
        '6800': {'turnover_target': 10.0, 'accuracy_target': 97.0}, 
        '728': {'turnover_target': 8.0, 'accuracy_target': 96.0},
        '8101': {'turnover_target': 11.0, 'accuracy_target': 97.5}
    }
}
```

### Step 2: Analytics Auto-Discovery
**That's it!** Analytics services automatically discover the new category:

```python
from app.services.store_goals_service import store_goals_service

# Get inventory turnover target for Wayzata
target = store_goals_service.get_store_goal_value('3607', 'inventory', 'turnover_target')
# Returns: 12.0

# Calculate performance against goals
performance = store_goals_service.calculate_performance_score('3607', 'inventory', {
    'turnover_actual': 13.2,
    'accuracy_actual': 99.1
})
```

## 💡 Usage Examples

### **For Analytics Services**
```python
# In any analytics service
from app.services.store_goals_service import store_goals_service

class MyAnalyticsService:
    def analyze_store_performance(self, store_code: str):
        # Get labor goals
        labor_target = store_goals_service.get_store_goal_value(
            store_code, 'labor', 'percentage', 25.0
        )
        
        # Get delivery goals  
        delivery_target = store_goals_service.get_store_goal_value(
            store_code, 'delivery', 'weekly_deliveries', 50
        )
        
        # Calculate comprehensive performance
        performance = store_goals_service.calculate_performance_score(
            store_code, 'labor', {
                'percentage': actual_labor_pct,
                'revenue_per_hour': actual_revenue_per_hour
            }
        )
```

### **For Health Scoring**
```python
def calculate_store_health(store_code: str):
    # Get all available goal categories dynamically
    categories = store_goals_service.get_available_goal_categories()
    # Returns: ['labor', 'delivery', 'inventory', 'customer_service', ...]
    
    category_scores = []
    for category in categories:
        # Each category contributes to overall health
        actual_metrics = get_actual_metrics_for_category(store_code, category)
        performance = store_goals_service.calculate_performance_score(
            store_code, category, actual_metrics
        )
        category_scores.append(performance['overall_score'])
    
    overall_health = sum(category_scores) / len(category_scores)
    return overall_health
```

### **For Alert Systems**
```python
def check_store_alerts(store_code: str):
    alerts = []
    
    # Labor performance alert
    labor_performance = store_goals_service.calculate_performance_score(
        store_code, 'labor', get_labor_metrics(store_code)
    )
    
    if labor_performance['overall_score'] < 70:
        alerts.append({
            'type': 'labor_performance',
            'severity': 'warning',
            'message': f'Labor performance below target: {labor_performance["overall_score"]:.1f}%'
        })
    
    return alerts
```

## 🎨 Frontend Integration

### **Configuration UI**
The system automatically populates configuration forms:
```javascript
// JavaScript automatically discovers new goal categories
const categories = await fetch('/api/store-goals-configuration')
    .then(r => r.json())
    .then(data => Object.keys(data.data).filter(k => k.startsWith('store')));

// Dynamically create UI sections for each category
categories.forEach(category => {
    createConfigurationSection(category);
});
```

## 🔄 Benefits

### **1. Zero-Code Goal Addition**
- Add new goal category to API → Analytics automatically use it
- No code changes required in individual services

### **2. Consistent Goal Usage**
- All analytics services use the same goal values
- Single source of truth for store targets

### **3. Performance Standardization**
- Consistent performance scoring across all categories
- Unified health scoring methodology

### **4. Easy Extension**
- Add customer service goals, inventory goals, quality goals, etc.
- System scales automatically

## 🛠️ Current Integrations

### ✅ **Completed**
- Executive Dashboard
- Store Goals API
- Configuration UI
- Financial Analytics Service (partial)

### 🔄 **In Progress**
- Health Scoring Algorithms
- Alert Systems
- Correlation Analytics
- Insights Generation

## 🎯 Future Goal Categories

### **Ready to Add:**
- **Customer Service**: response_time, satisfaction_score, resolution_rate
- **Inventory**: turnover_rate, accuracy_percentage, stockout_frequency
- **Quality**: defect_rate, return_percentage, warranty_claims
- **Efficiency**: transaction_speed, equipment_utilization, space_utilization
- **Growth**: new_customer_rate, upsell_percentage, market_share

### **Adding New Categories:**
1. Define goal structure in API
2. Add UI configuration section
3. Analytics automatically discover and use goals
4. Health scoring includes new category
5. Alerts monitor new targets

## 📈 Example: Adding Customer Service Goals

```python
# Step 1: Add to API (configuration_routes.py)
'storeCustomerServiceGoals': {
    '3607': {
        'response_time_minutes': 15, 
        'satisfaction_target': 4.5,
        'resolution_rate': 95.0
    },
    # ... other stores
}

# Step 2: Use immediately in analytics
customer_performance = store_goals_service.calculate_performance_score('3607', 'customer_service', {
    'response_time_minutes': 12,  # Actual: 12 minutes (better than 15)  
    'satisfaction_target': 4.7,   # Actual: 4.7/5 (better than 4.5)
    'resolution_rate': 97.2       # Actual: 97.2% (better than 95%)
})
# Returns performance scores automatically
```

This creates a **future-proof, extensible system** where new business goals can be added easily and immediately integrated across all analytics and reporting systems.