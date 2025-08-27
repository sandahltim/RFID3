# RFID Inventory Management System 🏪

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![MariaDB](https://img.shields.io/badge/MariaDB-11.0+-orange.svg)](https://mariadb.org/)
[![Redis](https://img.shields.io/badge/Redis-7.0+-red.svg)](https://redis.io/)

A comprehensive RFID-based inventory management system with advanced business intelligence, multi-store analytics, and executive dashboards for retail rental operations.

## 🚀 **NEW: Executive Dashboard (Tab 7)**

**Revolutionary business intelligence system with 328+ weeks of historical financial data:**
- **Multi-store payroll trends** with labor efficiency analysis
- **Interactive financial charts** showing revenue vs payroll patterns  
- **Store performance comparison** with profitability rankings
- **Executive KPI dashboard** with targets and variance tracking
- **Real-time analytics** with auto-refresh and store filtering

![Executive Dashboard Preview](docs/images/executive-dashboard-preview.png)

## 📊 **System Overview**

This system provides comprehensive inventory management across 4 store locations with advanced analytics, health monitoring, and executive reporting capabilities.

### **Core Modules**

| Tab | Module | Description | Key Features |
|-----|--------|-------------|--------------|
| 1 | **Rental Inventory** | Main inventory tracking | Item status, bin locations, availability |
| 2 | **Open Contracts** | Active rental contracts | Contract management, customer tracking |
| 3 | **Service** | Repair & maintenance | Service workflows, repair tracking |
| 4 | **Laundry Contracts** | Specialized laundry items | Laundry-specific contract management |
| 5 | **Resale** | Retail sales items | Resale inventory and pricing |
| 6 | **Inventory & Analytics** | 📈 Business intelligence | Activity tracking, health alerts, location analytics |
| 7 | **Executive Dashboard** | 🎯 **NEW** Financial BI | Payroll trends, store comparison, executive KPIs |

### **Advanced Features**

- **🏪 Multi-Store Operations**: 4 locations (Brooklyn Park, Wayzata, Anoka, St. Paul)
- **📊 Real-Time Analytics**: Live inventory health monitoring and business intelligence
- **🔍 Global Filtering**: Store-aware data filtering across all modules
- **📱 Mobile Ready**: Responsive design for mobile and tablet access
- **🚨 Health Alerts**: Automated inventory health monitoring with severity levels
- **📈 Predictive Analytics**: Trend analysis and forecasting capabilities

## 💼 **Business Intelligence Features**

### **Executive Dashboard (Tab 7)**
- **Financial Performance**: Revenue trends, payroll analysis, profit margins
- **Store Analytics**: Multi-location performance comparison and ranking
- **Labor Efficiency**: Productivity metrics and labor cost optimization
- **KPI Tracking**: Configurable key performance indicators with targets
- **Historical Analysis**: 328+ weeks of financial data for trend analysis

### **Inventory Analytics (Tab 6)**  
- **Activity Tracking**: Touch scans, movement patterns, utilization analysis
- **Health Monitoring**: Stale item detection, repair cycle tracking
- **Location Intelligence**: Bin location optimization and movement analytics
- **Alert System**: Automated notifications for inventory issues

## 🛠 **Technical Architecture**

### **Backend Stack**
- **Framework**: Flask 3.0+ with Blueprint architecture
- **Database**: MariaDB 11.0+ with optimized indexing
- **Caching**: Redis 7.0+ for performance optimization
- **ORM**: SQLAlchemy with session management
- **Background Tasks**: APScheduler for automated refreshes

### **Frontend Stack**
- **UI Framework**: Bootstrap 5 + MDB UI Kit
- **Charts**: Chart.js for interactive visualizations
- **JavaScript**: Modern ES6+ with modular architecture
- **Styling**: CSS3 with responsive design patterns

### **Data Sources**
- **Primary**: ItemMaster table with 30+ fields per item
- **Transactions**: Historical transaction data with scan patterns
- **Financial**: Payroll trends and executive KPI data
- **External APIs**: Integration with POS systems and external data sources

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.11+
- MariaDB 11.0+
- Redis 7.0+
- Node.js (for frontend dependencies)

### **Installation**

1. **Clone Repository**
   ```bash
   git clone https://github.com/sandahltim/RFID3.git
   cd RFID3
   ```

2. **Setup Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**
   ```bash
   # Create database
   mysql -u root -p -e "CREATE DATABASE rfid_inventory;"
   
   # Run migrations (tables auto-created on first run)
   python app.py
   ```

5. **Executive Dashboard Setup**
   ```bash
   # Create executive tables
   mysql -u rfid_user -p rfid_inventory < create_executive_tables.sql
   
   # Load sample data (optional)
   python load_executive_data.py
   ```

6. **Start Application**
   ```bash
   # For development (port 5000)
   flask run --host=0.0.0.0 --port=5000
   
   # For production (ports 8101/8102 with nginx)
   gunicorn --workers 1 --threads 4 --bind 0.0.0.0:8102 run:app
   ```

Visit `http://localhost:8101` to access the dashboard (production) or `http://localhost:5000` (development).

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Database Configuration
DB_HOST=localhost
DB_USER=rfid_user  
DB_PASSWORD=your_secure_password
DB_DATABASE=rfid_inventory

# API Configuration  
API_USERNAME=your_api_user
API_PASSWORD=your_api_password

# Application Settings
APP_IP=192.168.1.100
REDIS_URL=redis://localhost:6379/0
```

### **Config File Structure**
```
config.py                 # Main configuration
├── Database settings      # MariaDB connection
├── Redis configuration    # Caching settings  
├── API endpoints         # External integrations
├── Refresh intervals     # Data sync timing
└── Logging setup         # Application logging
```

## 📈 **Analytics & Reporting**

### **Executive Metrics**
- **Revenue Analysis**: Historical trends with YoY growth tracking
- **Labor Efficiency**: Cost per hour and productivity metrics  
- **Store Performance**: Comparative analysis across locations
- **Profit Margins**: Revenue minus payroll calculations
- **KPI Dashboard**: Customizable key performance indicators

### **Inventory Intelligence**
- **Health Alerts**: Automated detection of inventory issues
- **Activity Patterns**: Touch scan analysis and movement tracking
- **Location Optimization**: Bin assignment and retrieval efficiency
- **Utilization Metrics**: Asset performance and turnover analysis

### **Data Export Options**
- **CSV Export**: All data tables with filtering options
- **API Access**: REST endpoints for external integrations
- **Report Generation**: Scheduled reports via email/alerts
- **Dashboard Widgets**: Embeddable analytics components

## 🔐 **Security Features**

- **SQL Injection Protection**: Parameterized queries throughout
- **XSS Prevention**: Input sanitization and output encoding
- **Session Management**: Secure session handling with timeouts
- **Access Control**: Role-based permissions and store-level filtering
- **Audit Logging**: Comprehensive activity tracking and monitoring

## 📱 **Mobile & API Support**

### **Responsive Design**
- Mobile-first approach with responsive breakpoints
- Touch-friendly interfaces for mobile scanning
- Progressive Web App (PWA) capabilities

### **API Endpoints**
```
# Core Inventory APIs
GET  /api/tab/{tab_id}/data      # Tab data with filtering
POST /api/tab/{tab_id}/update    # Update inventory items

# Executive Dashboard APIs  
GET  /api/executive/dashboard_summary     # High-level metrics
GET  /api/executive/payroll_trends       # Financial trend data
GET  /api/executive/store_comparison     # Multi-store analytics
GET  /api/executive/kpi_dashboard        # KPI metrics

# Analytics APIs
GET  /api/analytics/health_alerts        # Inventory health status
GET  /api/analytics/activity_data        # Item activity patterns
GET  /api/analytics/location_data        # Location-based analytics
```

## 🧪 **Testing**

### **Test Suite Structure**
```bash
tests/
├── unit/                 # Unit tests for individual functions
├── integration/          # API endpoint integration tests  
├── security/            # Security vulnerability tests
└── performance/         # Performance and load tests
```

### **Running Tests**
```bash
# Run full test suite
python -m pytest tests/ -v --cov=app

# Run security tests
python -m pytest tests/security/ -v

# Run performance tests  
python -m pytest tests/performance/ -v
```

## 📊 **Database Schema**

### **Core Tables**
- **id_item_master**: Primary inventory data (40+ fields)
- **id_transactions**: Historical transaction records
- **id_categories**: Item categorization and hierarchy

### **Analytics Tables**
- **executive_payroll_trends**: Financial performance data (328+ records)
- **executive_scorecard_trends**: Business metrics and KPIs
- **executive_kpi**: Key performance indicators with targets

### **Health & Monitoring**
- **health_alerts**: Automated inventory health notifications
- **item_usage_history**: Activity tracking and analytics
- **location_analytics**: Bin location and movement data

## 🚀 **Deployment**

### **Production Deployment**
```bash
# Production configuration
export FLASK_ENV=production
export DB_PASSWORD=secure_production_password

# Deploy with gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 app:app

# Or deploy with Docker
docker build -t rfid-system .
docker run -p 5000:5000 rfid-system
```

### **Performance Optimization**
- **Database**: Optimized indexes on frequently queried fields
- **Caching**: Redis caching for expensive queries  
- **CDN**: Static asset delivery via CDN
- **Load Balancing**: Multi-instance deployment support

## 📋 **Roadmap**

### **Phase 1: Security & Performance (Next 30 days)**
- [ ] Fix SQL injection vulnerabilities  
- [ ] Implement proper input validation
- [ ] Add database query optimization
- [ ] Mobile responsiveness improvements

### **Phase 2: Advanced Analytics (Next 60 days)**  
- [ ] Predictive inventory analytics
- [ ] Revenue optimization algorithms
- [ ] Customer behavior analysis
- [ ] Automated reorder point calculations

### **Phase 3: Integration & Automation (Next 90 days)**
- [ ] Mobile app API development
- [ ] External POS system integration  
- [ ] Automated workflow optimization
- [ ] Machine learning-based forecasting

### **Phase 4: Enterprise Features (Next 120 days)**
- [ ] Multi-tenant architecture
- [ ] Advanced reporting suite
- [ ] Audit trail and compliance
- [ ] Enterprise SSO integration

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### **Development Setup**
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)  
3. Make changes and add tests
4. Run test suite (`pytest tests/ -v`)
5. Submit pull request

### **Code Standards**
- Python: PEP 8 compliance with type hints
- JavaScript: ES6+ with consistent formatting
- SQL: Parameterized queries only
- CSS: BEM methodology for naming

## 📞 **Support**

- **Documentation**: [Wiki Pages](https://github.com/sandahltim/RFID3/wiki)
- **Issues**: [GitHub Issues](https://github.com/sandahltim/RFID3/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sandahltim/RFID3/discussions)

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 **Acknowledgments**

- **Chart.js** for excellent data visualization capabilities
- **Bootstrap** and **MDB UI Kit** for responsive design components
- **Flask** community for robust web framework
- **MariaDB** for reliable database performance

---

**Built with ❤️ for inventory management excellence**

*Last updated: 2025-08-27 | Version: 2025-08-27-v1 | Executive Dashboard Release*