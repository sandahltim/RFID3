# Application Startup Configuration
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/tim/RFID3/logs/operations_api.log'),
        logging.StreamHandler()
    ]
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""

    # Startup
    logging.info("RFID Operations API starting up...")

    # Test database connections
    from app.database.connection import test_connection
    if await test_connection():
        logging.info("Database connection successful")
    else:
        logging.error("Database connection failed")

    # Create tables if they don't exist
    from app.database.connection import create_tables
    if await create_tables():
        logging.info("Database tables verified/created")

    logging.info("RFID Operations API startup complete")

    yield

    # Shutdown
    logging.info("RFID Operations API shutting down...")

def get_app_config():
    """Get application configuration"""
    return {
        "title": "RFID Operations API",
        "description": "Bidirectional RFID operations system",
        "version": "1.0.0",
        "lifespan": lifespan
    }