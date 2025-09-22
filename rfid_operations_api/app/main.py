# RFID Operations API - Main Application
# Created: 2025-09-17
# Purpose: FastAPI application for bidirectional RFID operations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from datetime import datetime

# Import API routers (will create these)
from app.api import equipment, items, transactions, sync, auth, contracts
from app.database.connection import get_database_url, test_connection

# Application metadata
app = FastAPI(
    title="RFID Operations API",
    description="Bidirectional RFID operations system supporting manager and field operations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://100.103.67.41:8101",  # Manager interface
        "https://100.103.67.41:443",   # Operations UI
        "https://100.103.67.41:3000", # Operations UI direct
        "http://localhost:3000",       # Development
        "https://localhost:3000",      # Development HTTPS
        "http://localhost:8101",       # Development
        "https://pi5-rfid3:3000",      # Hostname access
        "http://pi5-rfid3:3000",       # Hostname access HTTP
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and add categories and service routers first (more specific routes)
from app.api import categories, service
app.include_router(categories.router, prefix="/api/v1", tags=["categories"])
app.include_router(service.router, prefix="/api/v1/service", tags=["service"])

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(equipment.router, prefix="/api/v1/equipment", tags=["equipment"])
app.include_router(items.router, prefix="/api/v1/items", tags=["items"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])
app.include_router(contracts.router, prefix="/api/v1/contracts", tags=["contracts"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["synchronization"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logging.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Health check endpoints (both for compatibility)
@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db_status = await test_connection()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "database": "connected" if db_status else "disconnected",
            "api_endpoints": [
                "/api/v1/equipment",
                "/api/v1/items",
                "/api/v1/transactions",
                "/api/v1/sync",
                "/api/v1/auth"
            ]
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "RFID Operations API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
        "core_lessons": [
            "Do it well, then do it fast",
            "Trust but verify",
            "We solve root problems, not symptoms"
        ]
    }

# API information endpoint
@app.get("/api/v1/info")
async def api_info():
    """API information and capabilities"""
    return {
        "api_name": "RFID Operations API",
        "version": "1.0.0",
        "capabilities": [
            "Bidirectional equipment/item synchronization",
            "Real-time RFID scanning and updates",
            "Contract and transaction management",
            "Manager and operations interface support"
        ],
        "data_sources": [
            "Manager database (bidirectional sync)",
            "Real-time RFID scanning",
            "POS equipment data (171 columns)",
            "Operational transactions"
        ],
        "authentication": "API key and user-based",
        "supported_operations": [
            "GET, POST, PUT, PATCH, DELETE",
            "Bulk operations",
            "Real-time sync",
            "Filtering and pagination"
        ]
    }

if __name__ == "__main__":
    import uvicorn

    # Development server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8444,
        reload=True,
        # SSL handled by nginx proxy
        log_level="info"
    )