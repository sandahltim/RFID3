# Database Connection Management
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging

def get_database_url() -> str:
    """Get database URL from environment"""
    return os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://rfid_user:rfid_password@localhost/rfid_inventory"
    )

def get_manager_database_url() -> str:
    """Get manager database URL from environment"""
    return os.getenv(
        "MANAGER_DATABASE_URL",
        "mysql+pymysql://rfid_user:rfid_password@localhost/rfid_inventory"
    )

async def test_connection() -> bool:
    """Test database connection"""
    try:
        from app.models.base import engine
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return result.fetchone() is not None
    except SQLAlchemyError as e:
        logging.error(f"Database connection test failed: {e}")
        return False

async def create_tables():
    """Create all database tables"""
    try:
        from app.models.base import Base, engine
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables created successfully")
        return True
    except SQLAlchemyError as e:
        logging.error(f"Failed to create tables: {e}")
        return False