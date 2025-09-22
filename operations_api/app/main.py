"""
RFID Operations API
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import items, scan, sync
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(items.router, prefix=f"{settings.API_V1_STR}", tags=["items"])
app.include_router(scan.router, prefix=f"{settings.API_V1_STR}", tags=["scanning"])
app.include_router(sync.router, prefix=f"{settings.API_V1_STR}", tags=["sync"])

# Import and add contracts router
from app.api import contracts
app.include_router(contracts.router, prefix=f"{settings.API_V1_STR}", tags=["contracts"])

# Import and add categories and service routers
from app.api import categories, service
app.include_router(categories.router, prefix=f"{settings.API_V1_STR}", tags=["categories"])
app.include_router(service.router, prefix=f"{settings.API_V1_STR}", tags=["service"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "api_url": settings.API_V1_STR,
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        from app.database.session import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")

        return {
            "status": "healthy",
            "api": "operational",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "api": "operational",
            "database": "disconnected",
            "error": str(e)
        }

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info(f"Starting {settings.PROJECT_NAME}")
    logger.info(f"API running on port {settings.API_PORT}")
    logger.info(f"Database: {settings.DB_NAME}")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info(f"Shutting down {settings.PROJECT_NAME}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        ssl_keyfile="/etc/ssl/private/nginx-selfsigned.key",
        ssl_certfile="/etc/ssl/certs/nginx-selfsigned.crt"
    )