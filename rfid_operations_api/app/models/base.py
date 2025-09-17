# Database Base Models
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Any
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://ops_user:ops_password@localhost/rfid_operations_db")
MANAGER_DATABASE_URL = os.getenv("MANAGER_DATABASE_URL", "mysql+pymysql://rfid_user:rfid_password@localhost/rfid_inventory")

# Create engines
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
manager_engine = create_engine(MANAGER_DATABASE_URL, pool_pre_ping=True, echo=False)

# Session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ManagerSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=manager_engine)

# Base class for models
Base = declarative_base()

# Dependency for getting database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_manager_db():
    db = ManagerSessionLocal()
    try:
        yield db
    finally:
        db.close()