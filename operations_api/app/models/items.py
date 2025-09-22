"""
Operations Items Models
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, DECIMAL, Boolean, func
from app.database.session import Base
from datetime import datetime

class OpsItem(Base):
    __tablename__ = "ops_items"

    tag_id = Column(String(255), primary_key=True, comment='RFID tag identifier')
    uuid_accounts_fk = Column(String(255), comment='Account foreign key')
    serial_number = Column(String(255), comment='Manufacturer serial number')
    client_name = Column(String(255), comment='Current/last customer')
    rental_class_num = Column(String(255), index=True, comment='Equipment classification')
    common_name = Column(String(255), comment='Human-readable item name')
    quality = Column(String(50), comment='Condition grade')
    bin_location = Column(String(255), comment='Physical storage location')
    status = Column(String(50), index=True, comment='Current item status')
    last_contract_num = Column(String(255), comment='Most recent rental contract')
    last_scanned_by = Column(String(255), comment='Last scanner user ID')
    notes = Column(Text, comment='General notes')
    status_notes = Column(Text, comment='Status-specific notes')
    longitude = Column(DECIMAL(9, 6), comment='GPS longitude')
    latitude = Column(DECIMAL(9, 6), comment='GPS latitude')
    date_last_scanned = Column(DateTime, index=True, comment='Last scan timestamp')
    date_created = Column(DateTime, comment='Item creation date')
    date_updated = Column(DateTime, comment='Last modification date')
    home_store = Column(String(10), comment='Original store assignment')
    current_store = Column(String(10), index=True, comment='Current location store')
    identifier_type = Column(String(10), index=True, comment='RFID, QR, Sticker, Bulk')
    item_num = Column(Integer, unique=True, comment='Sequential item number')
    manufacturer = Column(String(100), comment='Equipment manufacturer')

    # Operations-relevant fields only
    usage_hours = Column(DECIMAL(10, 2), comment='Total usage hours')
    last_maintenance_date = Column(DateTime, comment='Last maintenance performed')
    next_maintenance_due = Column(DateTime, comment='Next scheduled maintenance')

    # Sync metadata
    last_sync_from_manager = Column(DateTime, comment='Last import from manager database')
    manager_db_id = Column(Integer, comment='Reference to manager database record')