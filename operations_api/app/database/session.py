"""
Database session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Operations database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# Manager database engine (for sync)
manager_engine = create_engine(
    settings.MANAGER_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ManagerSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager_engine)

Base = declarative_base()

def get_db():
    """Get operations database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_manager_db():
    """Get manager database session for sync"""
    db = ManagerSessionLocal()
    try:
        yield db
    finally:
        db.close()