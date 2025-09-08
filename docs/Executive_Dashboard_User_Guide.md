# Executive Dashboard User Guide

**RFID3 System - Tab 7: Executive Dashboard**  
**Version:** 2025-08-28-v1  
**Target Audience:** Executive Users, Management, Business Stakeholders  

---

## Overview

The Executive Dashboard (Tab 7) provides Fortune 500-level business intelligence and financial analytics for your rental inventory operations. This comprehensive guide will help you navigate, interpret, and leverage the dashboard for strategic decision-making.

## Quick Start

### Accessing the Executive Dashboard

1. **Login to RFID3 System**
   - Navigate to: `http://your-rfid-system.com:8101`
   - Enter your credentials and login

2. **Navigate to Executive Dashboard**
   - Click on **"Tab 7"** in the navigation menu
   - The Executive Dashboard will load automatically

3. **Dashboard Loading**
   - Initial load may take 5-10 seconds for full data processing
   - You'll see a professional loading screen with real-time updates

---

## Dashboard Components

### 1. Executive Header Section

The top section displays your company's key performance indicators in a visually striking format:

#### Key Metrics Cards
- **Total Revenue**: Current period total revenue with growth indicators
- **Gross Margin**: Profit margin percentage with trend arrows
- **Labor Efficiency**: Revenue per labor hour with performance status
- **Inventory Turnover**: Asset utilization rate and optimization metrics

#### Status Indicators
Each metric includes color-coded performance indicators:
- 🟢 **Excellent**: Performance exceeding targets (Green gradient)
- 🔵 **Good**: Performance meeting expectations (Blue gradient)  
- 🟠 **Warning**: Performance needing attention (Orange gradient)
- 🔴 **Critical**: Performance requiring immediate action (Red gradient)

### 2. Multi-Period Analysis (New Feature)

The Multi-Period Analysis provides advanced analytical capabilities for comprehensive business performance evaluation:

#### 3-Month Moving Averages
- **Trailing 3-Month Average**: Mean of the current month and two prior months
  - Smooths out short-term fluctuations to reveal underlying trends
  - Provides stable baseline for performance evaluation
  - Calculated across revenue, profit, efficiency, and revenue per hour metrics

- **Leading 3-Month Projection**: Forward-looking 3-month average based on trend analysis
  - Uses historical data patterns to project future performance
  - Helps with strategic planning and resource allocation
  - Available when sufficient historical data exists (6+ months)

#### Year-over-Year (YoY) Comparisons
Compare current performance against the same period last year:
- **Revenue Growth**: Absolute and percentage change in total revenue
- **Profit Evolution**: Year-over-year profit changes with margin analysis
- **Efficiency Trends**: Labor efficiency improvements or declines
- **Performance Indicators**: Color-coded arrows showing positive/negative trends

#### Two-Year-over-Two-Year (Yo2Y) Analysis
Extended historical comparison spanning two years:
- **Long-term Trends**: Multi-year performance trajectory analysis
- **Cyclical Patterns**: Identify seasonal or cyclical business patterns
- **Growth Trajectory**: Sustained growth vs. temporary fluctuations
- **Strategic Insights**: Foundation for long-term business planning

#### SQL Algorithm Overview
The multi-period analysis uses sophisticated queries to:
1. **Data Collection**: Retrieve 6+ months of PayrollTrends/ScorecardTrends data
2. **Period Segmentation**: Divide data into current, YoY, and Yo2Y periods
3. **Monthly Aggregation**: Group weekly data into monthly averages
4. **Rolling Calculations**: Compute 3-month trailing/leading averages
5. **Comparison Engine**: Calculate absolute and percentage changes with trend indicators

#### Usage Instructions
1. Click **"Multi-Period Analysis"** button in the dashboard controls
2. Use toggle buttons to switch between analysis views:
   - **Current Period**: Standard dashboard metrics
   - **3-Month Avg**: Trailing and leading average comparisons
   - **YoY Comparison**: Year-over-year and two-year comparison tables
3. View color-coded trend indicators:
   - 🟢 Green: Positive performance improvement
   - 🔴 Red: Performance decline requiring attention
   - ⚪ Gray: Neutral or minimal change

### 3. Revenue & Payroll Trends Chart

**Purpose**: Track financial performance and labor cost optimization over time

#### Chart Features
- **Dual-axis Display**: Revenue (left axis) and Payroll costs (right axis)
- **Time Period**: Last 12 weeks of data (adjustable)
- **Interactive Elements**: Hover over data points for detailed information
- **Trend Analysis**: Automatic calculation of growth rates and patterns

#### How to Read the Chart
1. **Blue Line (Revenue)**: Shows total revenue trends over time
2. **Red Line (Payroll)**: Shows total payroll costs over time
3. **Green Area**: Represents profit margin (revenue minus payroll)
4. **Data Points**: Hover for exact values and percentages

#### Key Insights to Look For
- **Revenue Growth**: Consistent upward trends indicate business growth
- **Labor Efficiency**: Revenue growing faster than payroll costs
- **Seasonal Patterns**: Identify peak and low periods for planning
- **Cost Control**: Monitor payroll costs relative to revenue generation

### 3. Store Performance Comparison

**Purpose**: Compare performance across all store locations to identify top performers and areas needing improvement

#### Pie Chart Analysis
- **Store Segments**: Each slice represents a store location
- **Size Indicator**: Larger slices indicate higher revenue contribution
- **Color Coding**: Professional color scheme for easy differentiation
- **Center Display**: Shows total revenue across all stores

#### Store Performance Table
| Store | Revenue | Growth | Labor Ratio | Efficiency | Status |
|-------|---------|--------|-------------|------------|---------|
| Brooklyn Park | $45,250 | +8.5% | 28.5% | $285/hr | 🟢 Excellent |
| Wayzata | $52,150 | +12.3% | 24.2% | $312/hr | 🟢 Excellent |
| Fridley | $38,750 | +4.2% | 32.1% | $245/hr | 🔵 Good |
| Elk River | $31,200 | -2.1% | 38.5% | $198/hr | 🟠 Warning |

#### Understanding Store Metrics
- **Revenue**: Total revenue for the current period
- **Growth**: Percentage change from previous period
- **Labor Ratio**: Payroll costs as percentage of revenue (lower is better)
- **Efficiency**: Revenue generated per labor hour (higher is better)
- **Status**: Overall performance rating based on multiple factors

### 4. KPI Scorecard

**Purpose**: Monitor key business metrics against established targets

#### Primary KPIs
- **Revenue Per Hour**: Target $275/hour (current performance vs target)
- **Labor Cost Ratio**: Target <30% (lower indicates better efficiency)
- **Inventory Turnover**: Target 3.5x annually (higher indicates better utilization)
- **Customer Satisfaction**: Target >95% (measured through various touchpoints)
- **Equipment Utilization**: Target 65-75% (optimal range for profitability)

#### Reading KPI Status
- **Green Progress Bar**: Performance exceeding target
- **Blue Progress Bar**: Performance meeting target  
- **Orange Progress Bar**: Performance below target but acceptable
- **Red Progress Bar**: Performance requiring immediate attention

### 5. Predictive Analytics Section

**Purpose**: Forecast future performance based on historical trends and patterns

#### Forecast Metrics
- **Next Week Revenue Prediction**: AI-powered revenue forecasting
- **Labor Cost Projections**: Anticipated payroll expenses
- **Inventory Needs**: Predicted inventory requirements
- **Seasonal Adjustments**: Recommendations based on historical patterns

#### Confidence Levels
Each prediction includes a confidence rating:
- **High Confidence (85%+)**: Strong historical data and clear patterns
- **Medium Confidence (65-84%)**: Some variability in historical data
- **Low Confidence (<65%)**: Limited data or high variability

---

## Data Sources and Processing

The dashboard ingests historical data from CSV exports stored in `shared/POR/`. The `load_executive_data.py` script reads files such as `Payroll Trends.csv` and `Scorecard Trends.csv`, cleans currency fields, and derives metrics like labor efficiency (`payroll_cost / total_revenue * 100`) and revenue per hour (`total_revenue / wage_hours`) before inserting records into the database【F:load_executive_data.py†L62-L63】【F:load_executive_data.py†L99-L107】【F:load_executive_data.py†L131-L133】.

Imported values populate three core tables:

| Table | Purpose | Model |
|-------|---------|-------|
| `executive_payroll_trends` | Weekly payroll, revenue, and efficiency metrics | `PayrollTrends`【F:app/models/db_models.py†L501-L520】 |
| `executive_scorecard_trends` | Store scorecard values including contracts and reservations | `ScorecardTrends`【F:app/models/db_models.py†L548-L580】 |
| `executive_kpi` | Calculated key performance indicators and targets | `ExecutiveKPI`【F:app/models/db_models.py†L627-L646】 |

Route logic in `app/routes/tab7.py` aggregates these tables for API responses. The summary endpoint derives year‑over‑year growth and profit margin using payroll trend data (`(current - last_year) / last_year * 100` and `(revenue - payroll) / revenue * 100`)【F:app/routes/tab7.py†L155-L175】【F:app/routes/tab7.py†L212-L219】.

Derived KPIs include:

- **Labor Efficiency** – payroll cost divided by revenue.
- **Revenue per Hour** – revenue divided by labor hours.
- **Profit Margin** – profit divided by revenue.
- **YoY Growth** – current revenue compared to the same period last year.

---

## Navigation and Filters

### Date Range Selection

#### Time Period Controls
1. **Quick Select Buttons**
   - Last 4 Weeks
   - Last 12 Weeks  
   - Last 26 Weeks
   - Year to Date
   - Custom Range

2. **Custom Date Range**
   - Click "Custom Range" button
   - Select start and end dates from calendar
   - Click "Apply" to update dashboard

#### Best Practices for Date Selection
- **Weekly Analysis**: Use 4-12 weeks for operational decisions
- **Quarterly Reviews**: Use 12-26 weeks for strategic planning
- **Annual Planning**: Use year-to-date or full year data
- **Trend Analysis**: Use consistent periods for accurate comparisons

### Store Filtering

#### Filter Options
- **All Stores**: View combined performance across all locations
- **Individual Stores**: Focus on specific store performance
- **Store Groups**: Compare regional or operational groupings

#### How to Apply Store Filters
1. Click the **"Store Filter"** dropdown in the top right
2. Select desired store(s) from the list:
   - Brooklyn Park (6800)
   - Wayzata (3607)
   - Fridley (8101)
   - Elk River (728)
3. Dashboard automatically updates with filtered data
4. Filter indicator shows active selections

---

## Key Business Metrics Explained

### Financial Performance Indicators

#### Revenue Metrics
- **Total Revenue**: Sum of all rental income for the period
- **Revenue Growth**: Percentage change from previous comparable period
- **Revenue Per Hour**: Total revenue divided by total labor hours
- **Revenue Per Transaction**: Average transaction value

#### Profitability Analysis
- **Gross Margin**: (Revenue - Direct Costs) ÷ Revenue × 100
- **Operating Margin**: (Revenue - All Operating Costs) ÷ Revenue × 100
- **EBITDA**: Earnings Before Interest, Taxes, Depreciation, Amortization
- **Net Profit Margin**: Final profit after all expenses

### Operational Efficiency Metrics

#### Labor Efficiency
- **Labor Cost Ratio**: Payroll costs as percentage of revenue
  - **Excellent**: <25% (highly efficient operations)
  - **Good**: 25-30% (solid operational efficiency)
  - **Acceptable**: 30-35% (room for improvement)
  - **Concerning**: >35% (requires immediate attention)

- **Revenue Per Labor Hour**: Revenue generated per hour of labor
  - **Target Range**: $250-$350 per hour
  - **Factors Affecting**: Staff productivity, pricing, demand patterns

#### Asset Utilization
- **Inventory Turnover Rate**: How frequently inventory items are rented
  - **Formula**: Total Rentals ÷ Average Inventory
  - **Target**: 3-4 times per year
  - **Impact**: Higher turnover = better ROI

- **Equipment Utilization**: Percentage of time equipment is generating revenue
  - **Optimal Range**: 65-75%
  - **Too Low**: <50% indicates excess inventory
  - **Too High**: >85% may indicate inventory shortage

### Customer and Market Metrics

#### Customer Performance
- **Customer Acquisition Rate**: New customers per period
- **Customer Retention Rate**: Percentage of repeat customers
- **Average Order Value**: Mean transaction size
- **Customer Lifetime Value**: Total expected revenue per customer

#### Market Position
- **Market Share**: Your share of local rental market
- **Competitive Position**: Performance relative to competitors
- **Growth Rate**: Business expansion rate
- **Seasonal Patterns**: Understanding demand cycles

---

## Interpreting Dashboard Data

### Performance Analysis Framework

#### Daily Operational Review (5 minutes)
1. **Quick Metrics Check**
   - Review yesterday's revenue vs target
   - Check any critical alerts or notifications
   - Monitor today's booking pipeline

2. **Key Performance Indicators**
   - Labor cost ratio for yesterday
   - Equipment utilization rates
   - Customer satisfaction scores

#### Weekly Business Review (15 minutes)
1. **Trend Analysis**
   - Compare current week to previous week
   - Identify any significant changes or patterns
   - Review store performance differences

2. **Efficiency Metrics**
   - Analyze revenue per labor hour trends
   - Review inventory turnover rates
   - Check for operational inefficiencies

#### Monthly Strategic Review (30 minutes)
1. **Comprehensive Analysis**
   - Month-over-month performance comparison
   - Quarterly trend identification
   - Annual target progress assessment

2. **Strategic Planning**
   - Identify growth opportunities
   - Plan inventory investments
   - Assess market position and competitive threats

### Red Flags to Watch For

#### Financial Warning Signs
- **Declining Revenue Growth**: Consistent downward trend over 4+ weeks
- **Increasing Labor Ratio**: Rising above 35% consistently
- **Shrinking Margins**: Profit margins decreasing over time
- **Cash Flow Issues**: Revenue not covering operational expenses

#### Operational Concerns
- **Low Utilization**: Equipment sitting idle for extended periods
- **High Service Costs**: Increasing repair and maintenance expenses
- **Customer Complaints**: Rising dissatisfaction indicators
- **Staff Productivity**: Declining revenue per labor hour

#### Market Challenges
- **Competitive Pressure**: Losing market share or pricing power
- **Seasonal Volatility**: Extreme fluctuations in demand
- **Economic Factors**: Local economic conditions affecting business
- **Technology Gaps**: Falling behind in operational efficiency

---

## Action Plans Based on Dashboard Insights

### Revenue Growth Strategies

#### When Revenue Growth is Declining
1. **Immediate Actions (This Week)**
   - Review pricing strategy and competitive position
   - Analyze lost opportunities and cancelled bookings
   - Increase sales and marketing efforts

2. **Short-term Actions (This Month)**
   - Launch targeted promotions or campaigns
   - Expand service offerings or rental categories
   - Improve customer retention programs

3. **Long-term Strategy (This Quarter)**
   - Invest in new inventory categories
   - Expand to new market segments
   - Develop strategic partnerships

#### When Revenue is Growing Strongly
1. **Capitalize on Success**
   - Increase inventory in high-demand categories
   - Expand successful strategies to other stores
   - Invest in staff training and development

2. **Prepare for Scale**
   - Improve operational efficiency
   - Strengthen customer service capabilities
   - Plan for potential capacity constraints

### Labor Cost Optimization

#### When Labor Costs are High (>35% of revenue)
1. **Immediate Efficiency Improvements**
   - Review staffing schedules vs demand patterns
   - Identify and eliminate inefficient processes
   - Cross-train staff for operational flexibility

2. **Technology Solutions**
   - Automate routine tasks where possible
   - Implement better scheduling and dispatch systems
   - Use data analytics for demand forecasting

3. **Process Optimization**
   - Streamline customer check-in/check-out processes
   - Improve inventory management workflows
   - Reduce manual paperwork and data entry

#### When Labor Efficiency is Excellent (<25%)
1. **Maintain Excellence**
   - Document and replicate successful processes
   - Share best practices across all stores
   - Recognize and reward efficient teams

2. **Growth Investment**
   - Use efficiency gains to fund growth initiatives
   - Invest in staff development and retention
   - Expand successful operational models

### Inventory Optimization

#### Low Utilization Scenarios (<50%)
1. **Immediate Assessment**
   - Identify underperforming inventory categories
   - Analyze seasonal and demand patterns
   - Review pricing strategies for idle equipment

2. **Optimization Actions**
   - Redistribute inventory across stores
   - Consider liquidating consistently idle assets
   - Adjust purchasing strategies for new inventory

#### High Utilization Scenarios (>85%)
1. **Capacity Planning**
   - Identify frequently sold-out categories
   - Plan strategic inventory investments
   - Analyze customer wait times and lost sales

2. **Revenue Maximization**
   - Consider premium pricing for high-demand items
   - Improve reservation and scheduling systems
   - Expand inventory in profitable categories

---

## Mobile Dashboard Usage

### Mobile-Optimized Features

#### Responsive Design
- **Automatic Scaling**: Dashboard adapts to screen size
- **Touch-Friendly**: Large buttons and touch targets
- **Readable Text**: Optimized font sizes for mobile viewing
- **Simplified Navigation**: Streamlined interface for small screens

#### Mobile-Specific Features
- **Swipe Navigation**: Swipe between dashboard sections
- **Tap to Expand**: Tap metric cards for detailed information
- **Portrait/Landscape**: Optimized for both orientations
- **Offline Indicators**: Shows when data is cached vs live

### Mobile Best Practices

#### Recommended Mobile Workflow
1. **Morning Review (2 minutes)**
   - Check overnight revenue and bookings
   - Review any critical alerts
   - Confirm day's priorities

2. **Midday Check (1 minute)**
   - Monitor real-time performance
   - Check staff productivity metrics
   - Review customer feedback

3. **Evening Summary (3 minutes)**
   - Review daily performance vs targets
   - Plan tomorrow's priorities
   - Check weekly progress

#### Mobile Limitations
- **Complex Charts**: Some detailed charts better viewed on desktop
- **Data Entry**: Extensive filtering easier on larger screens
- **Printing**: Report generation better performed on desktop
- **Multi-tasking**: Desktop better for comparative analysis

---

## Troubleshooting and Support

### Common Issues and Solutions

#### Dashboard Not Loading
1. **Check Network Connection**
   - Ensure stable internet connection
   - Try refreshing the page
   - Clear browser cache if necessary

2. **Browser Compatibility**
   - Use supported browsers: Chrome, Firefox, Safari, Edge
   - Update to latest browser version
   - Disable browser extensions that might interfere

3. **System Status**
   - Check if other users experiencing issues
   - Contact IT support if system-wide problem
   - Try accessing from different device/location

#### Data Appears Incorrect
1. **Verify Filters**
   - Check selected date range
   - Confirm store filters are correct
   - Reset filters to default and retest

2. **Data Synchronization**
   - Wait for next automatic refresh (occurs every 15 minutes)
   - Try manual refresh using F5 or refresh button
   - Check data source systems are operational

3. **Reporting Issues**
   - Document specific numbers that appear incorrect
   - Note the exact time and conditions when issue occurred
   - Contact support with detailed description

#### Slow Performance
1. **Network Optimization**
   - Close unnecessary browser tabs
   - Check network speed and stability
   - Try wired connection instead of WiFi

2. **Browser Optimization**
   - Clear browser cache and cookies
   - Disable unnecessary extensions
   - Try incognito/private browsing mode

3. **System Resources**
   - Close other applications using significant resources
   - Restart browser if issues persist
   - Try different time of day when network less congested

### Getting Help

#### Internal Support
1. **IT Department**
   - Technical issues with access or performance
   - Browser and network connectivity problems
   - Account access and permission issues

2. **Operations Management**
   - Questions about data interpretation
   - Business metric definitions and calculations
   - Process improvement suggestions

3. **Training Resources**
   - User manual and documentation
   - Video training sessions
   - Best practices guides

#### External Support
1. **System Administrator**
   - Database and system configuration issues
   - API connectivity problems
   - Custom report development

2. **Vendor Support**
   - RFID hardware and integration issues
   - Software bugs and feature requests
   - System updates and maintenance

### Feature Requests and Feedback

#### Submitting Enhancement Requests
1. **Document Specific Needs**
   - Clearly describe desired functionality
   - Explain business case and benefits
   - Provide examples of expected outcomes

2. **Follow Proper Channels**
   - Submit through established request process
   - Include priority level and timeline needs
   - Get management approval for significant changes

3. **Collaborate on Solutions**
   - Work with IT team on feasibility assessment
   - Participate in testing of new features
   - Provide feedback during development process

---

## Advanced Features

### Export and Reporting

#### Data Export Options
1. **CSV Export**
   - Download raw data for external analysis
   - Include all visible dashboard data
   - Preserve current filter settings

2. **PDF Reports**
   - Generate executive summary reports
   - Include charts and key metrics
   - Professional formatting for presentations

3. **Email Distribution**
   - Schedule automatic report delivery
   - Set up stakeholder distribution lists
   - Configure custom report formats

#### Custom Report Creation
1. **Report Builder**
   - Select specific metrics and time periods
   - Choose visualization types and layouts
   - Save report templates for reuse

2. **Automated Scheduling**
   - Set up daily, weekly, or monthly reports
   - Configure recipient lists and delivery methods
   - Include conditional formatting and alerts

### Integration Capabilities

#### External System Integration
1. **Accounting Systems**
   - Export financial data for bookkeeping
   - Integrate with QuickBooks, Sage, or other systems
   - Maintain audit trails and compliance

2. **CRM Integration**
   - Customer performance analytics
   - Sales pipeline integration
   - Marketing campaign effectiveness

3. **Business Intelligence Tools**
   - Connect to Tableau, Power BI, or other BI tools
   - Create advanced analytics and visualizations
   - Combine with other business data sources

### Advanced Analytics

#### Predictive Modeling
1. **Revenue Forecasting**
   - AI-powered revenue predictions
   - Seasonal adjustment algorithms
   - Confidence intervals and scenarios

2. **Demand Planning**
   - Inventory optimization recommendations
   - Peak period preparation
   - Capacity planning support

3. **Customer Analytics**
   - Customer lifetime value predictions
   - Churn risk identification
   - Personalized marketing opportunities

---

## Best Practices for Executive Users

### Daily Dashboard Review (5-10 minutes)

#### Morning Routine
1. **Quick Performance Check**
   - Review yesterday's revenue and key metrics
   - Check for any critical alerts or issues
   - Confirm today's priorities align with performance

2. **Team Communication**
   - Share relevant insights with management team
   - Address any immediate concerns or opportunities
   - Set expectations for the day

#### Key Questions to Ask
- Are we on track to meet weekly/monthly targets?
- What factors are driving current performance?
- Are there any emerging trends or concerns?
- What actions should we take today to optimize results?

### Weekly Business Reviews (20-30 minutes)

#### Performance Analysis
1. **Trend Identification**
   - Compare current week to previous weeks
   - Identify patterns and anomalies
   - Assess progress toward monthly goals

2. **Strategic Insights**
   - Analyze store performance differences
   - Review operational efficiency metrics
   - Identify improvement opportunities

#### Action Planning
1. **Short-term Adjustments**
   - Modify staffing or inventory based on trends
   - Implement quick wins for efficiency gains
   - Address emerging issues before they grow

2. **Strategic Initiatives**
   - Plan longer-term improvements
   - Allocate resources for maximum impact
   - Coordinate cross-functional initiatives

### Monthly Executive Reviews (45-60 minutes)

#### Comprehensive Assessment
1. **Performance Evaluation**
   - Monthly performance vs targets and budgets
   - Year-to-date progress assessment
   - Competitive position analysis

2. **Strategic Planning**
   - Quarterly planning and adjustments
   - Budget allocation and investment decisions
   - Market expansion and growth strategies

#### Stakeholder Communication
1. **Board Reporting**
   - Prepare executive summaries
   - Create visual presentations from dashboard data
   - Document key decisions and rationale

2. **Team Development**
   - Share insights and learning across organization
   - Recognize top performers and successful strategies
   - Plan training and development initiatives

---

## Appendix

### Glossary of Terms

**Dashboard**: Interactive business intelligence interface showing key performance metrics

**KPI (Key Performance Indicator)**: Specific measurable values that demonstrate business effectiveness

**Labor Cost Ratio**: Payroll expenses as a percentage of total revenue

**Revenue Per Hour**: Total revenue divided by total labor hours worked

**Utilization Rate**: Percentage of time equipment generates revenue vs total available time

**Turnover Rate**: Frequency at which inventory items are rented over a specific period

**Gross Margin**: Revenue minus direct costs, expressed as percentage of revenue

**EBITDA**: Earnings Before Interest, Taxes, Depreciation, and Amortization

**Customer Lifetime Value**: Total expected revenue from a customer over entire relationship

**Seasonal Adjustment**: Statistical technique to account for regular seasonal patterns

### Store Code Reference

| Store Code | Store Name | Location | Region |
|------------|------------|----------|---------|
| 6800 | Brooklyn Park | Brooklyn Park, MN | North |
| 3607 | Wayzata | Wayzata, MN | West |
| 8101 | Fridley | Fridley, MN | Central |
| 728 | Elk River | Elk River, MN | Northwest |

### Metric Targets and Benchmarks

| Metric | Target Range | Excellent | Good | Needs Improvement |
|--------|--------------|-----------|------|-------------------|
| Labor Cost Ratio | 25-30% | <25% | 25-30% | >30% |
| Revenue Per Hour | $250-350 | >$300 | $250-300 | <$250 |
| Utilization Rate | 65-75% | >75% | 65-75% | <65% |
| Inventory Turnover | 3-4x/year | >4x | 3-4x | <3x |
| Customer Satisfaction | >95% | >98% | 95-98% | <95% |

### Contact Information

**Technical Support**: IT Department - ext. 1234  
**Business Analysis**: Operations Manager - ext. 2345  
**System Administrator**: Database Team - ext. 3456  
**Training Resources**: HR Department - ext. 4567  

---

**Document Version**: 1.0  
**Last Updated**: 2025-08-28  
**Next Review Date**: 2025-11-28  
**Document Owner**: Operations Management Team
