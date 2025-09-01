# Minnesota Equipment Rental AI Intelligence Agent Architecture

## System Overview

This document outlines the comprehensive AI intelligence agent architecture for the Minnesota equipment rental business, designed to run on RTX 4070 PC with LangChain and local LLM integration.

## Business Context Analysis

### Current System Architecture
- **Main System**: Raspberry Pi 5 with Flask/MariaDB
- **Database**: MariaDB with tables including:
  - `id_item_master`: Core inventory tracking
  - `pos_transactions`: Financial transaction data
  - `pos_equipment`: Equipment details with financials
  - `pos_rfid_correlation`: RFID-POS data mapping
- **Web Interface**: Flask-based with real-time updates
- **Caching**: Redis for performance optimization

### Business Profile
- **A1 Rent It (70%)**: Construction tools, excavators, skid steers
- **Broadway Tent & Event (30%)**: Tents, tables, chairs, staging
- **Locations**: 4 stores (Wayzata, Brooklyn Park, Fridley, Elk River)
- **Target Markets**: Construction, events, residential

## AI Agent System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                RTX 4070 PC AI Agent System             │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  LangChain  │  │ Local LLM   │  │ Web Scraper │    │
│  │ Orchestrator│  │ (Qwen3/     │  │ Scheduler   │    │
│  │             │  │ Mistral 7B) │  │             │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ DB Query    │  │ Analytics   │  │ Learning    │    │
│  │ Engine      │  │ Engine      │  │ Engine      │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Cache Layer │  │ Security    │  │ API Gateway │    │
│  │ (Redis)     │  │ Manager     │  │             │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Secure Network
                          │
┌─────────────────────────────────────────────────────────┐
│              Raspberry Pi 5 Main System                │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Flask App   │  │ MariaDB     │  │ Redis Cache │    │
│  │ (Web UI)    │  │ Database    │  │             │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Technology Stack

#### RTX 4070 PC Components
- **Operating System**: Ubuntu 22.04 LTS
- **Container Platform**: Docker & Docker Compose
- **LLM Runtime**: Ollama (for Qwen3 7B or Mistral 7B)
- **AI Framework**: LangChain
- **Python Runtime**: Python 3.11+
- **Database Client**: PyMySQL for MariaDB connection
- **Caching**: Redis client for distributed caching
- **Web Framework**: FastAPI for API endpoints
- **Background Tasks**: Celery with Redis broker
- **Monitoring**: Prometheus + Grafana

#### GPU Optimization
- **CUDA**: Version 12.1+
- **GPU Memory Management**: Dynamic allocation with fallback to CPU
- **Model Quantization**: 4-bit quantization for memory efficiency
- **Batch Processing**: Optimized for simultaneous query processing

## Detailed Component Specifications

### 1. LangChain Orchestrator

#### Core Responsibilities
- Natural language query parsing and understanding
- Tool selection and execution orchestration
- Response synthesis and validation
- Context management and memory

#### LangChain Tools Implementation
```python
# Database Query Tool
class DatabaseQueryTool:
    - Query id_item_master for inventory insights
    - Access pos_transactions for financial analysis
    - Join operations across multiple tables
    - Parameterized queries for security

# Weather Data Tool
class WeatherDataTool:
    - NOAA API integration
    - OpenWeather API for detailed forecasts
    - Historical weather correlation analysis
    - Weather-based demand prediction

# Event Data Tool
class EventDataTool:
    - Minnesota State Fair API
    - Local festival calendars
    - Corporate event monitoring
    - Event impact analysis

# Permit Data Tool
class PermitDataTool:
    - Minneapolis permit database
    - St. Paul construction permits
    - Building permit trend analysis
    - Construction demand forecasting

# Social Media Tool
class SocialMediaTool:
    - Twitter/X API for event buzz monitoring
    - Hashtag tracking for Minnesota events
    - Sentiment analysis for event planning
    - Social signal correlation
```

### 2. Local LLM Integration

#### Model Selection Criteria
- **Primary**: Qwen3-7B-Instruct (Strong reasoning, multilingual)
- **Secondary**: Mistral-7B-Instruct-v0.3 (Fast inference, good general knowledge)
- **Fallback**: Llama3-8B-Instruct (Reliable, well-tested)

#### Model Configuration
```yaml
model_config:
  primary_model: "qwen2.5:7b-instruct"
  temperature: 0.1  # Low for factual queries
  max_tokens: 4096
  context_length: 8192
  quantization: "Q4_K_M"  # 4-bit quantization
  gpu_layers: 35  # Adjust based on VRAM usage
  batch_size: 8
```

### 3. Database Query Engine

#### Query Capabilities
- **Natural Language to SQL**: Convert business questions to optimized queries
- **Multi-table Joins**: Complex queries across inventory, POS, and financial tables
- **Aggregation Engine**: Revenue, utilization, trend analysis
- **Performance Optimization**: Query caching, index utilization

#### Security Features
- **Read-only Access**: Dedicated read-only database user
- **Query Validation**: SQL injection prevention
- **Rate Limiting**: Per-user query limits
- **Audit Logging**: All queries logged with timestamps

### 4. Web Data Analysis Engine

#### Data Sources
```python
data_sources = {
    "weather": [
        "https://api.weather.gov/",  # NOAA API
        "https://api.openweathermap.org/",  # OpenWeather
    ],
    "events": [
        "https://www.mnstatefair.org/api/",  # State Fair
        "https://www.exploreminnesota.com/api/",  # Tourism events
    ],
    "permits": [
        "http://opendata.minneapolismn.gov/",  # Minneapolis permits
        "https://information.stpaul.gov/",  # St. Paul permits
    ],
    "economic": [
        "https://api.stlouisfed.org/fred/",  # Federal Reserve data
        "https://mn.gov/deed/data/",  # Minnesota economic data
    ]
}
```

#### Continuous Analysis Features
- **Scheduled Updates**: Hourly weather, daily permits, weekly events
- **Change Detection**: Alert on significant data changes
- **Correlation Discovery**: Automated pattern recognition
- **Trend Analysis**: Time-series analysis for demand prediction

### 5. Learning and Feedback System

#### Machine Learning Components
- **Feedback Loop**: User validation of AI insights
- **Accuracy Tracking**: Success rate monitoring per query type
- **Model Fine-tuning**: Continuous improvement based on domain data
- **A/B Testing**: Compare different response strategies

#### Learning Mechanisms
```python
learning_system = {
    "feedback_collection": {
        "thumbs_up_down": "Simple binary feedback",
        "correction_input": "User-provided corrections",
        "usage_patterns": "Query frequency and success rates"
    },
    "improvement_strategies": {
        "prompt_engineering": "Optimize prompts based on successful patterns",
        "retrieval_tuning": "Improve database query generation",
        "response_ranking": "Learn from user preferences"
    }
}
```

### 6. API Gateway and Integration

#### REST API Endpoints
```python
# Core query endpoint
POST /api/v1/query
{
    "question": "What equipment is most profitable in winter?",
    "context": "financial_analysis",
    "confidence_threshold": 0.8
}

# Real-time insights
GET /api/v1/insights/live
{
    "category": "weather_impact",
    "timeframe": "next_7_days"
}

# Learning feedback
POST /api/v1/feedback
{
    "query_id": "uuid",
    "rating": 5,
    "correction": "text",
    "useful": true
}
```

#### Pi 5 Integration Points
- **Webhook Notifications**: Push insights to main system
- **Data Synchronization**: Regular sync of analysis results
- **Cache Sharing**: Distributed cache for performance
- **Health Monitoring**: System status reporting

### 7. Security Framework

#### Multi-layer Security
```python
security_layers = {
    "network": {
        "vpn": "WireGuard VPN between Pi 5 and RTX PC",
        "firewall": "UFW with strict rules",
        "ssl_tls": "All communications encrypted"
    },
    "authentication": {
        "api_keys": "Rotating API keys for external services",
        "jwt_tokens": "JWT for Pi 5 communication",
        "rate_limiting": "Per-IP and per-user limits"
    },
    "data_protection": {
        "encryption_at_rest": "Database and file encryption",
        "secure_logging": "PII redaction in logs",
        "backup_encryption": "Encrypted backup storage"
    }
}
```

### 8. Performance Optimization

#### Response Time Targets
- **Simple Queries**: < 500ms
- **Complex Analysis**: < 2 seconds
- **Real-time Insights**: < 100ms (cached)
- **Bulk Operations**: < 30 seconds

#### Optimization Strategies
```python
optimization_features = {
    "caching": {
        "query_results": "Redis with TTL based on data freshness",
        "model_responses": "Semantic similarity caching",
        "external_api_calls": "Long-term cache for stable data"
    },
    "gpu_optimization": {
        "model_quantization": "4-bit quantization for memory efficiency",
        "batch_processing": "Multiple queries in single inference",
        "memory_management": "Dynamic VRAM allocation"
    },
    "database_optimization": {
        "connection_pooling": "Persistent database connections",
        "query_optimization": "Explain plan analysis",
        "index_management": "Automated index recommendations"
    }
}
```

## Deployment Strategy

### Docker Architecture
```dockerfile
# Multi-stage build for production optimization
# Stage 1: Base environment with CUDA
# Stage 2: Python dependencies
# Stage 3: Model installation
# Stage 4: Application layer
```

### Container Orchestration
- **ai-agent-core**: Main LangChain application
- **ai-agent-llm**: Ollama model server
- **ai-agent-workers**: Celery workers for background tasks
- **ai-agent-redis**: Redis for caching and task queue
- **ai-agent-monitoring**: Prometheus and Grafana
- **ai-agent-proxy**: Nginx reverse proxy

### Hardware Requirements
- **GPU**: RTX 4070 (12GB VRAM minimum)
- **RAM**: 32GB (16GB for system, 16GB for model)
- **Storage**: 1TB NVMe SSD (models, cache, logs)
- **Network**: Gigabit Ethernet for Pi 5 communication

## Expected Capabilities and Performance

### Natural Language Understanding
- **Query Types**: Equipment availability, financial analysis, trend prediction
- **Accuracy Target**: 95%+ intent recognition
- **Response Quality**: Human-like explanations with data backing

### Insight Discovery
- **Correlation Mining**: 5+ new business insights per month
- **Pattern Recognition**: Seasonal trends, weather impacts, event correlations
- **Anomaly Detection**: Unusual rental patterns, maintenance needs

### Business Intelligence
- **Revenue Optimization**: Pricing recommendations, inventory positioning
- **Demand Forecasting**: Weather-based, event-driven predictions
- **Operational Efficiency**: Maintenance scheduling, stock rebalancing

This architecture provides a robust, scalable, and secure foundation for AI-driven business intelligence in the equipment rental industry, specifically optimized for Minnesota's unique market conditions and seasonal patterns.