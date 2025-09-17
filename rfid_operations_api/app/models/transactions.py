# Transactions Models - Activity logging and scan events
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Text, Index, ForeignKey, Decimal
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class Transaction(Base):
    """Operations transactions - mirrors id_transactions for operations"""
    __tablename__ = "ops_transactions"

    # Primary identifier
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Item and contract references
    tag_id = Column(String(255), ForeignKey('ops_items.tag_id'), nullable=False, comment="Links to ops_items")
    contract_number = Column(String(255), comment="Links to contracts (no financial details)")

    # Transaction details
    scan_type = Column(String(50), nullable=False, comment="scan, checkin, checkout, maintenance, etc.")
    scan_date = Column(DateTime, nullable=False, comment="Transaction timestamp")
    scan_by = Column(String(255), comment="Operations user who performed scan")

    # Item information at time of transaction
    client_name = Column(String(255), comment="Customer name (for operations context)")
    common_name = Column(String(255), nullable=False, comment="Equipment name")
    bin_location = Column(String(255), comment="Location at scan time")
    status = Column(String(50), comment="Status at scan time")
    quality = Column(String(50), comment="Quality assessment")

    # Location information
    location_of_repair = Column(String(255), comment="Repair location if applicable")
    longitude = Column(Decimal(9,6), comment="GPS longitude at scan")
    latitude = Column(Decimal(9,6), comment="GPS latitude at scan")

    # Condition assessment (operations critical)
    dirty_or_mud = Column(Boolean, default=False, comment="Dirty or muddy condition")
    leaves = Column(Boolean, default=False, comment="Has leaves/debris")
    oil = Column(Boolean, default=False, comment="Oil stains present")
    mold = Column(Boolean, default=False, comment="Mold detected")
    stain = Column(Boolean, default=False, comment="General staining")
    oxidation = Column(Boolean, default=False, comment="Rust/oxidation present")
    other = Column(Text, comment="Other condition notes")
    rip_or_tear = Column(Boolean, default=False, comment="Tears or rips detected")
    sewing_repair_needed = Column(Boolean, default=False, comment="Sewing repairs needed")
    grommet = Column(Boolean, default=False, comment="Grommet issues")
    rope = Column(Boolean, default=False, comment="Rope/tie issues")
    buckle = Column(Boolean, default=False, comment="Buckle problems")
    wet = Column(Boolean, default=False, comment="Item is wet")
    service_required = Column(Boolean, default=False, comment="General service required")

    # Additional metadata
    uuid_accounts_fk = Column(String(255), comment="Account foreign key")
    serial_number = Column(String(255), comment="Item serial number at scan time")
    rental_class_num = Column(String(255), comment="Equipment classification at scan time")
    notes = Column(Text, comment="Transaction-specific notes")

    # Operations-specific fields (no financial data)
    repair_estimate = Column(Text, comment="Estimated repair needs (no costs)")
    maintenance_performed = Column(Text, comment="Maintenance work completed")

    # Timestamps
    date_created = Column(DateTime, comment="Transaction creation date")
    date_updated = Column(DateTime, comment="Transaction update date")

    # Operations metadata
    ops_created_at = Column(DateTime, default=func.now())
    ops_updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    item = relationship("Item", back_populates="transactions")

    # Indexes for operations performance
    __table_args__ = (
        Index('ix_ops_trans_tag_id', 'tag_id'),
        Index('ix_ops_trans_scan_date', 'scan_date'),
        Index('ix_ops_trans_scan_type', 'scan_type'),
        Index('ix_ops_trans_scan_by', 'scan_by'),
        Index('ix_ops_trans_contract', 'contract_number'),
        Index('ix_ops_trans_status', 'status'),
    )