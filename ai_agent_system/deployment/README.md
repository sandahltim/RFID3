# Minnesota Equipment Rental AI Agent - Deployment Guide

This guide provides complete deployment instructions for the AI intelligence agent system designed for the Minnesota equipment rental business.

## System Overview

### Architecture Components
- **AI Agent Core**: FastAPI application with LangChain orchestration
- **Local LLM**: Ollama running Qwen3 7B or Mistral 7B model
- **Database Integration**: Read-only access to MariaDB on Pi 5
- **External APIs**: Weather, events, and permits data sources
- **Caching**: Redis for performance optimization
- **Monitoring**: Prometheus + Grafana for comprehensive metrics
- **Security**: JWT authentication, audit logging, rate limiting

### Hardware Requirements
- **GPU**: RTX 4070 with 12GB VRAM minimum
- **RAM**: 32GB (16GB system + 16GB for AI models)
- **Storage**: 1TB NVMe SSD
- **Network**: Gigabit Ethernet for Pi 5 communication
- **OS**: Ubuntu 22.04 LTS

## Pre-Deployment Setup

### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
sudo apt install docker.io docker-compose-v2 -y
sudo usermod -aG docker $USER
newgrp docker

# Install NVIDIA Container Toolkit for GPU support
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update
sudo apt install nvidia-container-toolkit -y
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi
```

### 2. Environment Configuration

```bash
# Clone the repository
cd /opt
sudo git clone https://github.com/your-org/rfid3-ai-agent.git ai-agent
sudo chown -R $USER:$USER ai-agent
cd ai-agent

# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### 3. Required Environment Variables

```bash
# Database Configuration (MariaDB on Pi 5)
DB_HOST=192.168.3.110
DB_USER=rfid_user
DB_PASSWORD=your_secure_database_password
DB_DATABASE=rfid_inventory

# API Keys
OPENWEATHER_API_KEY=your_openweather_api_key
NOAA_API_KEY=your_noaa_api_key
MINNEAPOLIS_API_KEY=your_minneapolis_api_key

# Security
API_SECRET_KEY=generate_secure_random_key_256_bits
JWT_SECRET_KEY=generate_another_secure_random_key

# Pi 5 Integration
PI5_BASE_URL=http://192.168.3.110:5000
PI5_API_KEY=your_pi5_integration_key
PI5_WEBHOOK_URL=http://192.168.3.110:5000/api/ai-insights

# Performance
OLLAMA_MODEL=qwen2.5:7b-instruct
CUDA_VISIBLE_DEVICES=0
```

## Deployment Steps

### 1. Initial Deployment

```bash
# Create necessary directories
sudo mkdir -p /opt/ai-agent/{logs,data,cache,models}
sudo chown -R $USER:$USER /opt/ai-agent

# Deploy the system
cd /opt/ai-agent
docker-compose up -d

# Check service status
docker-compose ps
docker-compose logs -f ai-agent-core
```

### 2. LLM Model Setup

```bash
# Wait for Ollama to be ready
docker-compose logs -f ai-agent-llm

# Pull the AI model (this may take 10-15 minutes)
docker-compose exec ai-agent-llm ollama pull qwen2.5:7b-instruct

# Verify model is loaded
docker-compose exec ai-agent-llm ollama list
```

### 3. Database Connection Setup

```bash
# Test database connectivity
docker-compose exec ai-agent-core python -c "
import os
import pymysql
try:
    conn = pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_DATABASE')
    )
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

### 4. Service Verification

```bash
# Check all services are running
docker-compose ps

# Test AI Agent API
curl -X GET http://localhost/api/v1/health

# Test query endpoint
curl -X POST http://localhost/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{"question": "What equipment is currently on rent?"}'
```

### 5. Monitoring Setup

```bash
# Access Grafana dashboard
open http://localhost:3000
# Default credentials: admin/admin123

# Access Prometheus
open http://localhost:9090

# Check metrics endpoint
curl http://localhost/api/v1/metrics
```

## Pi 5 Integration Setup

### 1. Pi 5 Webhook Configuration

On the Pi 5 system, add webhook configuration:

```python
# In Pi 5 Flask app
AI_AGENT_WEBHOOK_URL = "http://your-rtx-pc-ip/pi5/webhook"
AI_AGENT_API_KEY = "your_api_key"

def notify_ai_agent(event_type, data):
    try:
        response = requests.post(
            AI_AGENT_WEBHOOK_URL,
            json={
                "event_type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            },
            headers={"Authorization": f"Bearer {AI_AGENT_API_KEY}"},
            timeout=10
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to notify AI agent: {e}")
```

### 2. Pi 5 API Integration

```python
# Example Pi 5 route to consume AI insights
@app.route('/api/ai-insights', methods=['POST'])
def receive_ai_insights():
    try:
        insights = request.json
        # Store insights in Pi 5 database
        # Update dashboard with AI recommendations
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 400
```

## External API Setup

### 1. Weather API Configuration

```bash
# OpenWeather API setup
# 1. Sign up at https://openweathermap.org/api
# 2. Get API key
# 3. Add to .env file

# NOAA API setup  
# 1. Register at https://www.weather.gov/documentation/services-web-api
# 2. Add API key to .env file
```

### 2. Minnesota Data Sources

```bash
# Minneapolis Open Data API
# 1. Register at http://opendata.minneapolismn.gov/
# 2. Get API key for building permits
# 3. Add to .env file

# Minnesota State Fair API (if available)
# Contact MN State Fair for API access
```

## Performance Optimization

### 1. GPU Memory Management

```bash
# Monitor GPU usage
nvidia-smi -l 1

# Adjust GPU memory allocation in .env
GPU_MEMORY_FRACTION=0.8
OLLAMA_GPU_LAYERS=35
```

### 2. Cache Optimization

```bash
# Monitor Redis performance
docker-compose exec ai-agent-redis redis-cli info

# Adjust cache settings in .env
REDIS_MAX_MEMORY=2gb
CACHE_TTL_SECONDS=3600
```

### 3. Database Connection Pool

```bash
# Optimize database connections
DB_POOL_SIZE=10
DB_POOL_RECYCLE=3600
DB_POOL_TIMEOUT=20
```

## Security Configuration

### 1. Network Security

```bash
# Configure firewall
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow from 192.168.3.110  # Pi 5 access
```

### 2. SSL/TLS Setup (Production)

```bash
# Install Certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx -y

# Generate SSL certificate
sudo certbot --nginx -d your-ai-agent-domain.com

# Update nginx.conf for HTTPS
# Uncomment HTTPS server block in nginx/nginx.conf
```

### 3. API Key Management

```bash
# Rotate API keys regularly
# Generate new keys
openssl rand -hex 32  # For API_SECRET_KEY
openssl rand -hex 32  # For JWT_SECRET_KEY

# Update .env file and restart services
docker-compose restart
```

## Monitoring and Maintenance

### 1. Log Management

```bash
# View logs
docker-compose logs -f ai-agent-core
docker-compose logs -f ai-agent-llm

# Log rotation (add to crontab)
0 0 * * * docker-compose exec ai-agent-core logrotate /etc/logrotate.conf
```

### 2. Health Monitoring

```bash
# Health check script
#!/bin/bash
# health_check.sh

echo "=== AI Agent Health Check ==="
echo "Date: $(date)"
echo

# Check services
echo "Service Status:"
docker-compose ps

# Check API health
echo -e "\nAPI Health:"
curl -s http://localhost/api/v1/health | jq .

# Check GPU
echo -e "\nGPU Status:"
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits

# Check disk space
echo -e "\nDisk Usage:"
df -h /opt/ai-agent
```

### 3. Performance Monitoring

```bash
# Monitor key metrics
docker-compose exec ai-agent-prometheus promtool query instant 'up{job="ai-agent"}'
docker-compose exec ai-agent-prometheus promtool query instant 'ai_agent_queries_total'
```

## Backup and Recovery

### 1. Data Backup

```bash
# Create backup script
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups/ai-agent/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp -r /opt/ai-agent/.env "$BACKUP_DIR/"
cp -r /opt/ai-agent/docker-compose.yml "$BACKUP_DIR/"

# Backup data
docker-compose exec ai-agent-redis redis-cli save
cp -r /opt/ai-agent/data "$BACKUP_DIR/"

# Backup logs
cp -r /opt/ai-agent/logs "$BACKUP_DIR/"

echo "Backup completed: $BACKUP_DIR"
```

### 2. System Recovery

```bash
# Recovery procedure
cd /opt/ai-agent

# Stop services
docker-compose down

# Restore from backup
cp backup/.env .
cp backup/docker-compose.yml .
cp -r backup/data/* data/

# Restart services
docker-compose up -d

# Verify recovery
curl -X GET http://localhost/api/v1/health
```

## Troubleshooting

### Common Issues

1. **GPU Not Detected**
   ```bash
   # Check NVIDIA drivers
   nvidia-smi
   
   # Reinstall NVIDIA container toolkit
   sudo apt install --reinstall nvidia-container-toolkit
   sudo systemctl restart docker
   ```

2. **Model Loading Fails**
   ```bash
   # Check Ollama logs
   docker-compose logs ai-agent-llm
   
   # Manually pull model
   docker-compose exec ai-agent-llm ollama pull qwen2.5:7b-instruct
   ```

3. **Database Connection Issues**
   ```bash
   # Test network connectivity
   ping 192.168.3.110
   
   # Check database credentials
   mysql -h 192.168.3.110 -u rfid_user -p rfid_inventory
   ```

4. **High Memory Usage**
   ```bash
   # Monitor memory
   free -h
   docker stats
   
   # Adjust model parameters
   # Reduce OLLAMA_GPU_LAYERS in .env
   ```

### Support and Logging

- **Application Logs**: `/opt/ai-agent/logs/ai-agent.log`
- **System Logs**: `journalctl -u docker`
- **Container Logs**: `docker-compose logs [service-name]`
- **Performance Metrics**: Grafana dashboard at `http://localhost:3000`

## Scaling Considerations

For production scaling:

1. **Load Balancing**: Add multiple AI agent instances behind nginx
2. **Database Scaling**: Consider read replicas for MariaDB
3. **Cache Clustering**: Redis cluster for high availability
4. **Model Distribution**: Multiple GPU nodes for model serving
5. **Monitoring**: External Prometheus and Grafana instances

## Business Impact Tracking

The AI agent provides:

- **Demand Forecasting**: Weather and event-based equipment demand predictions
- **Revenue Optimization**: Data-driven pricing and inventory recommendations  
- **Operational Efficiency**: Automated insights for maintenance and logistics
- **Customer Intelligence**: Usage pattern analysis for service improvements
- **Market Analysis**: Competitive positioning and opportunity identification

Expected business improvements:
- 15-25% increase in equipment utilization
- 10-20% improvement in demand forecasting accuracy
- 20-30% reduction in manual analysis time
- Enhanced customer satisfaction through predictive service

For technical support or business optimization questions, contact the AI agent development team.