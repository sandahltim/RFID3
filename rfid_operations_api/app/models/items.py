# RFID Items Models - Real-time operational state
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Text, Index, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class Item(Base):
    """RFID Items - mirrors id_item_master for operations"""
    __tablename__ = "ops_items"

    # Primary identifier
    tag_id = Column(String(255), primary_key=True, comment="RFID tag identifier")

    # Item identification
    uuid_accounts_fk = Column(String(255), comment="Account foreign key")
    serial_number = Column(String(255), comment="Manufacturer serial number")
    item_num = Column(Integer, unique=True, comment="Sequential item number")

    # Customer and rental information
    client_name = Column(String(255), comment="Current/last customer")
    last_contract_num = Column(String(255), comment="Most recent rental contract")

    # Equipment classification
    rental_class_num = Column(String(255), comment="Equipment classification")
    common_name = Column(String(255), comment="Human-readable item name")

    # Condition and quality
    quality = Column(String(50), comment="Condition grade")
    status = Column(String(50), comment="Current item status")

    # Location information
    bin_location = Column(String(255), comment="Physical storage location")
    home_store = Column(String(10), comment="Original store assignment")
    current_store = Column(String(10), comment="Current location store")

    # GPS coordinates
    longitude = Column(Numeric(9,6), comment="GPS longitude")
    latitude = Column(Numeric(9,6), comment="GPS latitude")

    # Identification type
    identifier_type = Column(String(10), comment="RFID, QR, Sticker, Bulk")

    # Operational information
    last_scanned_by = Column(String(255), comment="Last scanner user ID")
    date_last_scanned = Column(DateTime, comment="Last scan timestamp")

    # Notes and documentation
    notes = Column(Text, comment="General notes")
    status_notes = Column(Text, comment="Status-specific notes")

    # Equipment information
    manufacturer = Column(String(100), comment="Equipment manufacturer")

    # Maintenance tracking (operations-relevant, no financial data)
    usage_hours = Column(Numeric(10,2), comment="Total usage hours (if tracked)")
    last_maintenance_date = Column(Date, comment="Last maintenance performed")
    next_maintenance_due = Column(Date, comment="Next scheduled maintenance")

    # Timestamps
    date_created = Column(DateTime, comment="Item creation date")
    date_updated = Column(DateTime, comment="Last modification date")

    # Sync metadata
    last_sync_from_manager = Column(DateTime, comment="Last import from manager database")
    manager_db_id = Column(Integer, comment="Reference to manager database record")

    # Operations metadata
    ops_created_at = Column(DateTime, default=func.now())
    ops_updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    transactions = relationship("Transaction", back_populates="item")

    # Indexes for operations performance
    __table_args__ = (
        Index('ix_ops_items_rental_class', 'rental_class_num'),
        Index('ix_ops_items_status', 'status'),
        Index('ix_ops_items_store', 'current_store'),
        Index('ix_ops_items_identifier_type', 'identifier_type'),
        Index('ix_ops_items_last_scanned', 'date_last_scanned'),
        Index('ix_ops_items_contract', 'last_contract_num'),
        Index('ix_ops_items_quality', 'quality'),
    )