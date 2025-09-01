#!/bin/bash

# Minnesota Equipment Rental AI Agent - Startup Script
# Automated deployment script for RTX 4070 PC

set -e

echo "=========================================="
echo "Minnesota Equipment Rental AI Agent"
echo "RTX 4070 Deployment Script"
echo "=========================================="
echo

# Configuration
AI_AGENT_DIR="/opt/ai-agent"
BACKUP_DIR="/opt/backups/ai-agent"
LOG_FILE="/tmp/ai-agent-deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}SUCCESS: $1${NC}" | tee -a "$LOG_FILE"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root"
fi

# System requirements check
check_requirements() {
    log "Checking system requirements..."
    
    # Check GPU
    if ! command -v nvidia-smi &> /dev/null; then
        error "NVIDIA GPU driver not found. Please install NVIDIA drivers first."
    fi
    
    # Check GPU model
    GPU_MODEL=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
    log "Detected GPU: $GPU_MODEL"
    
    if [[ ! "$GPU_MODEL" == *"RTX 4070"* && ! "$GPU_MODEL" == *"RTX"* ]]; then
        warning "Detected GPU is not RTX 4070. Performance may be reduced."
    fi
    
    # Check memory
    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_MEM" -lt 28 ]; then
        warning "System has ${TOTAL_MEM}GB RAM. 32GB recommended for optimal performance."
    fi
    
    # Check disk space
    AVAILABLE_SPACE=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$AVAILABLE_SPACE" -lt 100 ]; then
        error "Insufficient disk space. Need at least 100GB available."
    fi
    
    success "System requirements check completed"
}

# Install Docker if not present
install_docker() {
    if ! command -v docker &> /dev/null; then
        log "Installing Docker..."
        
        sudo apt update
        sudo apt install -y docker.io docker-compose-v2
        sudo usermod -aG docker $USER
        
        # Install NVIDIA container toolkit
        distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
        curl -fsSL https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
        curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
            sudo tee /etc/apt/sources.list.d/nvidia-docker.list
        
        sudo apt update
        sudo apt install -y nvidia-container-toolkit
        sudo systemctl restart docker
        
        success "Docker installation completed"
    else
        log "Docker already installed"
    fi
}

# Create directory structure
create_directories() {
    log "Creating directory structure..."
    
    sudo mkdir -p "$AI_AGENT_DIR"/{logs,data,cache,models,static}
    sudo mkdir -p "$BACKUP_DIR"
    sudo chown -R $USER:$USER "$AI_AGENT_DIR"
    sudo chown -R $USER:$USER "$BACKUP_DIR"
    
    success "Directory structure created"
}

# Setup environment file
setup_environment() {
    log "Setting up environment configuration..."
    
    if [ ! -f "$AI_AGENT_DIR/.env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example "$AI_AGENT_DIR/.env"
            log "Environment template copied. Please edit $AI_AGENT_DIR/.env with your configuration."
        else
            # Create basic .env file
            cat > "$AI_AGENT_DIR/.env" << EOL
# AI Agent Configuration
ENVIRONMENT=production
DEBUG=false

# Database Configuration (Pi 5)
DB_HOST=192.168.3.110
DB_USER=rfid_user
DB_PASSWORD=change_me
DB_DATABASE=rfid_inventory

# Redis Configuration  
REDIS_URL=redis://ai-agent-redis:6379/0

# Ollama Configuration
OLLAMA_HOST=http://ai-agent-llm:11434
OLLAMA_MODEL=qwen2.5:7b-instruct

# Security
API_SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# External APIs (add your keys)
OPENWEATHER_API_KEY=
NOAA_API_KEY=
MINNEAPOLIS_API_KEY=

# Pi 5 Integration
PI5_BASE_URL=http://192.168.3.110:5000
PI5_API_KEY=change_me
PI5_WEBHOOK_URL=http://192.168.3.110:5000/api/ai-insights

# Performance
CUDA_VISIBLE_DEVICES=0
GPU_MEMORY_FRACTION=0.8
WORKERS=1

# Business Configuration
BUSINESS_TIMEZONE=America/Chicago
EOL
            warning "Basic .env file created. Please edit $AI_AGENT_DIR/.env with your actual configuration."
        fi
    else
        log "Environment file already exists"
    fi
}

# Deploy services
deploy_services() {
    log "Deploying AI agent services..."
    
    cd "$AI_AGENT_DIR"
    
    # Copy application files if not already present
    if [ ! -f "docker-compose.yml" ]; then
        log "Copying application files..."
        cp -r /home/tim/RFID3/ai_agent_system/* "$AI_AGENT_DIR/"
    fi
    
    # Start services
    log "Starting Docker services..."
    docker-compose up -d
    
    # Wait for services to start
    log "Waiting for services to initialize..."
    sleep 30
    
    success "Services deployed"
}

# Setup LLM model
setup_model() {
    log "Setting up AI model..."
    
    cd "$AI_AGENT_DIR"
    
    # Wait for Ollama to be ready
    log "Waiting for Ollama service to be ready..."
    for i in {1..60}; do
        if docker-compose exec -T ai-agent-llm ollama list &> /dev/null; then
            break
        fi
        sleep 5
        if [ $i -eq 60 ]; then
            error "Ollama service failed to start"
        fi
    done
    
    # Pull the model
    log "Downloading AI model (this may take 10-15 minutes)..."
    if ! docker-compose exec -T ai-agent-llm ollama pull qwen2.5:7b-instruct; then
        warning "Failed to pull qwen2.5:7b-instruct, trying alternative model..."
        docker-compose exec -T ai-agent-llm ollama pull mistral:7b-instruct
    fi
    
    # Verify model
    docker-compose exec -T ai-agent-llm ollama list
    
    success "AI model setup completed"
}

# Test deployment
test_deployment() {
    log "Testing deployment..."
    
    cd "$AI_AGENT_DIR"
    
    # Check service health
    log "Checking service status..."
    docker-compose ps
    
    # Test API endpoints
    log "Testing API endpoints..."
    
    # Health check
    if curl -s -f http://localhost/api/v1/health > /dev/null; then
        success "Health check endpoint working"
    else
        error "Health check endpoint failed"
    fi
    
    # Test capabilities endpoint
    if curl -s -f http://localhost/api/v1/capabilities > /dev/null; then
        success "Capabilities endpoint working"
    else
        warning "Capabilities endpoint not responding"
    fi
    
    success "Deployment testing completed"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Check if Grafana is accessible
    log "Waiting for Grafana to be ready..."
    for i in {1..30}; do
        if curl -s -f http://localhost:3000 > /dev/null; then
            success "Grafana dashboard available at http://localhost:3000"
            log "Default credentials: admin/admin123"
            break
        fi
        sleep 5
    done
    
    # Check Prometheus
    if curl -s -f http://localhost:9090 > /dev/null; then
        success "Prometheus metrics available at http://localhost:9090"
    else
        warning "Prometheus not responding"
    fi
}

# Create systemd service for auto-start
create_systemd_service() {
    log "Creating systemd service..."
    
    sudo tee /etc/systemd/system/ai-agent.service > /dev/null << EOL
[Unit]
Description=Minnesota Equipment Rental AI Agent
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$AI_AGENT_DIR
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=$USER

[Install]
WantedBy=multi-user.target
EOL
    
    sudo systemctl daemon-reload
    sudo systemctl enable ai-agent.service
    
    success "Systemd service created and enabled"
}

# Create maintenance scripts
create_maintenance_scripts() {
    log "Creating maintenance scripts..."
    
    # Health check script
    cat > "$AI_AGENT_DIR/health_check.sh" << 'EOL'
#!/bin/bash
echo "=== AI Agent Health Check ==="
echo "Date: $(date)"
echo

cd /opt/ai-agent

echo "Service Status:"
docker-compose ps

echo -e "\nAPI Health:"
curl -s http://localhost/api/v1/health | jq . 2>/dev/null || curl -s http://localhost/api/v1/health

echo -e "\nGPU Status:"
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits

echo -e "\nDisk Usage:"
df -h /opt/ai-agent

echo -e "\nMemory Usage:"
free -h

echo -e "\nContainer Resource Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
EOL
    
    # Backup script
    cat > "$AI_AGENT_DIR/backup.sh" << 'EOL'
#!/bin/bash
BACKUP_DIR="/opt/backups/ai-agent/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cd /opt/ai-agent

echo "Creating backup at $BACKUP_DIR"

# Backup configuration
cp .env "$BACKUP_DIR/"
cp docker-compose.yml "$BACKUP_DIR/"

# Backup application data
docker-compose exec -T ai-agent-redis redis-cli save
cp -r data "$BACKUP_DIR/"
cp -r cache "$BACKUP_DIR/"

# Backup recent logs
find logs -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/" \;

echo "Backup completed: $BACKUP_DIR"
EOL
    
    # Update script
    cat > "$AI_AGENT_DIR/update.sh" << 'EOL'
#!/bin/bash
echo "Updating AI Agent..."

cd /opt/ai-agent

# Create backup before update
./backup.sh

# Pull latest images
docker-compose pull

# Restart services
docker-compose down
docker-compose up -d

echo "Update completed"
EOL
    
    # Make scripts executable
    chmod +x "$AI_AGENT_DIR"/*.sh
    
    success "Maintenance scripts created"
}

# Main execution
main() {
    log "Starting AI Agent deployment..."
    
    check_requirements
    install_docker
    create_directories
    setup_environment
    deploy_services
    setup_model
    test_deployment
    setup_monitoring
    create_systemd_service
    create_maintenance_scripts
    
    echo
    echo "=========================================="
    echo "DEPLOYMENT COMPLETED SUCCESSFULLY!"
    echo "=========================================="
    echo
    echo "Services:"
    echo "  - AI Agent API: http://localhost"
    echo "  - Grafana Dashboard: http://localhost:3000 (admin/admin123)"
    echo "  - Prometheus Metrics: http://localhost:9090"
    echo
    echo "Configuration:"
    echo "  - Environment file: $AI_AGENT_DIR/.env"
    echo "  - Logs directory: $AI_AGENT_DIR/logs"
    echo "  - Data directory: $AI_AGENT_DIR/data"
    echo
    echo "Maintenance scripts:"
    echo "  - Health check: $AI_AGENT_DIR/health_check.sh"
    echo "  - Backup: $AI_AGENT_DIR/backup.sh"
    echo "  - Update: $AI_AGENT_DIR/update.sh"
    echo
    echo "Next steps:"
    echo "1. Edit $AI_AGENT_DIR/.env with your API keys and configuration"
    echo "2. Restart services: cd $AI_AGENT_DIR && docker-compose restart"
    echo "3. Test the deployment: $AI_AGENT_DIR/health_check.sh"
    echo
    echo "For support, check the logs at $AI_AGENT_DIR/logs/ai-agent.log"
    echo "=========================================="
}

# Run main function
main "$@"