# RFID Items Models - Real-time operational state
from sqlalchemy import Column, String, Integer, DateTime, Text, Index, Numeric, Enum
from sqlalchemy.sql import func
from .base import Base

class Item(Base):
    """RFID Items - directly uses id_item_master from manager database"""
    __tablename__ = "id_item_master"

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
    identifier_type = Column(Enum('RFID','Sticker','QR','Barcode','Bulk','None'), comment="Identifier type")

    # Operational information
    last_scanned_by = Column(String(255), comment="Last scanner user ID")
    date_last_scanned = Column(DateTime, comment="Last scan timestamp")

    # Notes and documentation
    notes = Column(Text, comment="General notes")
    status_notes = Column(Text, comment="Status-specific notes")

    # Equipment information
    manufacturer = Column(String(100), comment="Equipment manufacturer")
    department = Column(String(100), comment="Equipment department")
    type_desc = Column(String(50), comment="Type description")

    # Financial information
    turnover_ytd = Column(Numeric(10,2), comment="Year to date turnover")
    turnover_ltd = Column(Numeric(10,2), comment="Life to date turnover")
    repair_cost_ltd = Column(Numeric(10,2), comment="Life to date repair cost")
    sell_price = Column(Numeric(10,2), comment="Selling price")
    retail_price = Column(Numeric(10,2), comment="Retail price")

    # Inventory information
    quantity = Column(Integer, comment="Quantity")
    reorder_min = Column(Integer, comment="Minimum reorder level")
    reorder_max = Column(Integer, comment="Maximum reorder level")

    # Timestamps
    date_created = Column(DateTime, comment="Item creation date")
    date_updated = Column(DateTime, comment="Last modification date")
    pos_last_updated = Column(DateTime, comment="Last POS system update")

    # Data source tracking
    data_source = Column(String(20), comment="Data source identifier")

    # Additional data (JSON)
    rental_rates = Column(Text, comment="Rental rates data")
    vendor_ids = Column(Text, comment="Vendor IDs data")
    tag_history = Column(Text, comment="Tag history data")

    # Note: Relationships to transactions table disabled for now
    # transactions = relationship("Transaction", back_populates="item")

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