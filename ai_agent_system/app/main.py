"""
Main FastAPI Application for Minnesota Equipment Rental AI Agent
Production-ready application with comprehensive middleware and monitoring
"""

import logging
import os
import asyncio
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .core.llm_agent import MinnesotaEquipmentRentalAgent
from .services.feedback_service import FeedbackService
from .services.cache_service import CacheService
from .services.audit_service import AuditService
from .api.endpoints import router, initialize_services

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai-agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Application state
app_state = {
    'agent': None,
    'feedback_service': None,
    'cache_service': None,
    'audit_service': None,
    'startup_time': None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Minnesota Equipment Rental AI Agent...")
    app_state['startup_time'] = datetime.now()
    
    try:
        # Initialize services
        await initialize_app_services()
        logger.info("All services initialized successfully")
        
        yield
        
    finally:
        # Shutdown
        logger.info("Shutting down AI Agent...")
        await cleanup_services()


async def initialize_app_services():
    """Initialize all application services"""
    
    # Configuration from environment
    config = {
        'db_connection_string': _get_db_connection_string(),
        'ollama_host': os.getenv('OLLAMA_HOST', 'http://localhost:11434'),
        'model_name': os.getenv('OLLAMA_MODEL', 'qwen2.5:7b-instruct'),
        'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        'api_keys': {
            'openweather': os.getenv('OPENWEATHER_API_KEY'),
            'noaa': os.getenv('NOAA_API_KEY'),
            'minneapolis': os.getenv('MINNEAPOLIS_API_KEY'),
            'saint_paul': os.getenv('SAINT_PAUL_API_KEY')
        }
    }
    
    # Initialize AI Agent
    logger.info("Initializing AI Agent...")
    app_state['agent'] = MinnesotaEquipmentRentalAgent(
        ollama_host=config['ollama_host'],
        model_name=config['model_name'],
        db_connection_string=config['db_connection_string'],
        api_keys=config['api_keys']
    )
    
    # Initialize services
    logger.info("Initializing services...")
    app_state['feedback_service'] = FeedbackService()
    app_state['cache_service'] = CacheService(redis_url=config['redis_url'])
    app_state['audit_service'] = AuditService()
    
    # Wait a moment for async initialization
    await asyncio.sleep(2)
    
    # Initialize API endpoints with services
    initialize_services(
        agent_instance=app_state['agent'],
        feedback_service_instance=app_state['feedback_service'],
        cache_service_instance=app_state['cache_service'],
        audit_service_instance=app_state['audit_service']
    )


def _get_db_connection_string() -> str:
    """Build database connection string from environment variables"""
    
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'rfid_user')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_DATABASE', 'rfid_inventory')
    db_port = os.getenv('DB_PORT', '3306')
    
    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


async def cleanup_services():
    """Cleanup services on shutdown"""
    
    # Cleanup audit service
    if app_state['audit_service']:
        try:
            await app_state['audit_service'].cleanup_old_records()
        except Exception as e:
            logger.error(f"Error during audit cleanup: {e}")
    
    logger.info("Services cleanup completed")


# Create FastAPI app
app = FastAPI(
    title="Minnesota Equipment Rental AI Agent",
    description="AI-powered business intelligence agent for equipment rental operations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://192.168.3.110:5000').split(','),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Trusted hosts middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,192.168.3.110,ai-agent-core').split(',')
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests for audit purposes"""
    start_time = datetime.now()
    
    # Get client information
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = (datetime.now() - start_time).total_seconds() * 1000
    
    # Log request details
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.2f}ms - "
        f"Client: {client_ip} - "
        f"User-Agent: {user_agent[:100]}"
    )
    
    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Log security-relevant exceptions
    if app_state['audit_service']:
        try:
            await app_state['audit_service'].log_error(
                query_id="system_error",
                error=str(exc),
                user_id="system"
            )
        except:
            pass
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.now().isoformat()
        }
    )


# Include API routes
app.include_router(router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information"""
    
    uptime_seconds = 0
    if app_state['startup_time']:
        uptime_seconds = int((datetime.now() - app_state['startup_time']).total_seconds())
    
    return {
        "service": "Minnesota Equipment Rental AI Agent",
        "version": "1.0.0",
        "status": "online",
        "uptime_seconds": uptime_seconds,
        "agent_available": app_state['agent'] is not None,
        "services_available": {
            "feedback_service": app_state['feedback_service'] is not None,
            "cache_service": app_state['cache_service'] is not None and app_state['cache_service'].is_available(),
            "audit_service": app_state['audit_service'] is not None
        },
        "endpoints": {
            "query": "/api/v1/query",
            "feedback": "/api/v1/feedback",
            "insights": "/api/v1/insights/live",
            "health": "/api/v1/health",
            "capabilities": "/api/v1/capabilities",
            "docs": "/docs"
        },
        "timestamp": datetime.now().isoformat()
    }


# Pi 5 integration endpoints
@app.post("/pi5/webhook")
async def pi5_webhook(request: Request):
    """Webhook endpoint for Pi 5 system notifications"""
    
    try:
        data = await request.json()
        
        # Log webhook receipt
        if app_state['audit_service']:
            await app_state['audit_service'].log_query(
                query_id=f"webhook_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                user_id="pi5_system",
                question=f"Pi5 webhook: {data.get('event_type', 'unknown')}",
                context=data,
                ip_address=request.client.host if request.client else None
            )
        
        # Process webhook data based on type
        event_type = data.get('event_type')
        
        if event_type == 'inventory_update':
            # Handle inventory updates - could trigger cache invalidation
            if app_state['cache_service']:
                await app_state['cache_service'].invalidate_pattern('inventory')
        
        elif event_type == 'new_transaction':
            # Handle new transaction - invalidate financial caches
            if app_state['cache_service']:
                await app_state['cache_service'].invalidate_pattern('financial')
        
        elif event_type == 'system_alert':
            # Handle system alerts
            logger.warning(f"Pi5 system alert: {data.get('message', 'No message')}")
        
        return {
            "success": True,
            "message": "Webhook processed successfully",
            "event_type": event_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Pi5 webhook error: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error": "Failed to process webhook",
                "timestamp": datetime.now().isoformat()
            }
        )


@app.post("/pi5/insights/push")
async def push_insights_to_pi5():
    """Push AI insights to Pi 5 system"""
    
    if not app_state['agent']:
        raise HTTPException(status_code=503, detail="AI agent not available")
    
    try:
        # Generate insights for Pi 5
        insights_query = "Generate current business insights and recommendations for the Pi 5 dashboard"
        
        agent_response = await app_state['agent'].query(
            user_input=insights_query,
            context={"target": "pi5_dashboard", "format": "summary"}
        )
        
        insights_data = {
            "insights": agent_response.insights,
            "recommendations": agent_response.recommendations,
            "confidence": agent_response.confidence,
            "generated_at": datetime.now().isoformat(),
            "data_sources": agent_response.data_sources
        }
        
        # In production, this would push to Pi 5 via HTTP request
        # For now, just return the insights
        
        logger.info("Generated insights for Pi 5 dashboard")
        
        return {
            "success": True,
            "insights_data": insights_data,
            "message": "Insights generated for Pi 5 system",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate Pi5 insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate insights")


# Static files (if needed)
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


def run_server():
    """Run the server"""
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    
    # Server configuration
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    workers = int(os.getenv('WORKERS', 1))
    
    logger.info(f"Starting server on {host}:{port} with {workers} workers")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True,
        reload=os.getenv('ENVIRONMENT', 'production') != 'production'
    )


if __name__ == "__main__":
    run_server()