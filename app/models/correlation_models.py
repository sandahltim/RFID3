"""
Correlation Models for Inventory Integration System
SQLAlchemy models for bridging RFID, POS, and other inventory systems
"""

from app import db
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON
from enum import Enum

class TrackingType(Enum):
    RFID = "RFID"
    QR = "QR"
    BARCODE = "BARCODE"
    BULK = "BULK"
    HYBRID = "HYBRID"

class TrackingStatus(Enum):
    ACTIVE = "ACTIVE"
    MIGRATING = "MIGRATING"
    LEGACY = "LEGACY"
    RETIRED = "RETIRED"

class MigrationPhase(Enum):
    BULK_ONLY = "BULK_ONLY"
    TRANSITIONING = "TRANSITIONING"
    PARTIAL_TAGGED = "PARTIAL_TAGGED"
    FULLY_TAGGED = "FULLY_TAGGED"
    COMPLETE = "COMPLETE"

class ProcessingStatus(Enum):
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    PARTIAL = "PARTIAL"
    ORPHANED = "ORPHANED"
    ERROR = "ERROR"

class InventoryCorrelationMaster(db.Model):
    """Master correlation table linking all inventory systems"""
    __tablename__ = "inventory_correlation_master"
    __table_args__ = (
        db.Index("idx_rfid_tag", "rfid_tag_id"),
        db.Index("idx_pos_item", "pos_item_num", "pos_item_class"),
        db.Index("idx_tracking_type", "tracking_type"),
        db.Index("idx_migration_phase", "migration_phase"),
        db.Index("idx_common_name", "common_name"),
        db.Index("idx_confidence", "confidence_score"),
    )
    
    correlation_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    master_item_id = db.Column(db.String(100), unique=True, nullable=False)
    
    # RFID System identifiers
    rfid_tag_id = db.Column(db.String(255))
    rfid_item_num = db.Column(db.Integer)
    
    # POS System identifiers
    pos_item_num = db.Column(db.String(50))
    pos_item_class = db.Column(db.String(50))
    pos_key = db.Column(db.String(100))
    pos_serial_no = db.Column(db.String(100))
    
    # QR/Barcode identifiers
    qr_code = db.Column(db.String(255))
    barcode = db.Column(db.String(255))
    
    # Common attributes
    common_name = db.Column(db.String(255))
    manufacturer = db.Column(db.String(100))
    model_number = db.Column(db.String(100))
    category = db.Column(db.String(100))
    department = db.Column(db.String(100))
    
    # Tracking type and status
    tracking_type = db.Column(db.Enum(TrackingType), nullable=False)
    tracking_status = db.Column(db.Enum(TrackingStatus), default=TrackingStatus.ACTIVE)
    migration_phase = db.Column(db.Enum(MigrationPhase))
    
    # Quantity management
    is_bulk_item = db.Column(db.Boolean, default=False)
    bulk_quantity_on_hand = db.Column(db.DECIMAL(10, 2))
    tagged_quantity = db.Column(db.Integer, default=0)
    untagged_quantity = db.Column(db.Integer, default=0)
    
    # Data quality
    confidence_score = db.Column(db.DECIMAL(3, 2), default=1.00)
    last_verified_date = db.Column(db.DateTime)
    verification_source = db.Column(db.String(50))
    
    # Metadata
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))
    updated_by = db.Column(db.String(100))
    
    # Relationships
    pos_staging = db.relationship("POSDataStaging", back_populates="correlation", lazy="dynamic")
    rfid_mappings = db.relationship("RFIDPOSMapping", back_populates="correlation", lazy="dynamic")
    migrations = db.relationship("MigrationTracking", back_populates="correlation", lazy="dynamic")
    quality_metrics = db.relationship("DataQualityMetrics", back_populates="correlation", lazy="dynamic")
    intelligence = db.relationship("InventoryIntelligence", back_populates="correlation", uselist=False)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'correlation_id': self.correlation_id,
            'master_item_id': self.master_item_id,
            'rfid_tag_id': self.rfid_tag_id,
            'pos_item_num': self.pos_item_num,
            'common_name': self.common_name,
            'tracking_type': self.tracking_type.value if self.tracking_type else None,
            'tracking_status': self.tracking_status.value if self.tracking_status else None,
            'migration_phase': self.migration_phase.value if self.migration_phase else None,
            'is_bulk_item': self.is_bulk_item,
            'confidence_score': float(self.confidence_score) if self.confidence_score else 0,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }

class POSDataStaging(db.Model):
    """Staging table for POS CSV imports"""
    __tablename__ = "pos_data_staging"
    __table_args__ = (
        db.Index("idx_pos_staging_status", "processing_status"),
        db.Index("idx_pos_staging_batch", "import_batch_id"),
        db.Index("idx_pos_item_key", "item_num", "item_key"),
    )
    
    staging_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    # POS identifiers
    item_num = db.Column(db.String(50))
    item_key = db.Column(db.String(100))
    name = db.Column(db.String(255))
    location = db.Column(db.String(50))
    category = db.Column(db.String(100))
    department = db.Column(db.String(100))
    type_desc = db.Column(db.String(100))
    
    # Quantity and valuation
    quantity = db.Column(db.DECIMAL(10, 2))
    home_store = db.Column(db.String(10))
    current_store = db.Column(db.String(10))
    item_group = db.Column(db.String(50))
    
    # Equipment details
    manufacturer = db.Column(db.String(100))
    model_no = db.Column(db.String(100))
    serial_no = db.Column(db.String(100))
    part_no = db.Column(db.String(100))
    license_no = db.Column(db.String(50))
    model_year = db.Column(db.Integer)
    
    # Financial metrics
    turnover_mtd = db.Column(db.DECIMAL(12, 2))
    turnover_ytd = db.Column(db.DECIMAL(12, 2))
    turnover_ltd = db.Column(db.DECIMAL(12, 2))
    repair_cost_ltd = db.Column(db.DECIMAL(12, 2))
    sell_price = db.Column(db.DECIMAL(10, 2))
    retail_price = db.Column(db.DECIMAL(10, 2))
    
    # Import metadata
    import_batch_id = db.Column(db.String(50))
    import_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_name = db.Column(db.String(255))
    row_number = db.Column(db.Integer)
    
    # Processing status
    processing_status = db.Column(db.Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    correlation_id = db.Column(db.BigInteger, db.ForeignKey('inventory_correlation_master.correlation_id'))
    match_confidence = db.Column(db.DECIMAL(3, 2))
    error_message = db.Column(db.Text)
    
    # Relationships
    correlation = db.relationship("InventoryCorrelationMaster", back_populates="pos_staging")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'staging_id': self.staging_id,
            'item_num': self.item_num,
            'name': self.name,
            'quantity': float(self.quantity) if self.quantity else 0,
            'processing_status': self.processing_status.value if self.processing_status else None,
            'correlation_id': self.correlation_id,
            'match_confidence': float(self.match_confidence) if self.match_confidence else 0,
            'import_batch_id': self.import_batch_id,
            'import_date': self.import_date.isoformat() if self.import_date else None
        }

class RFIDPOSMapping(db.Model):
    """Many-to-many mapping between RFID tags and POS items"""
    __tablename__ = "rfid_pos_mapping"
    __table_args__ = (
        db.UniqueConstraint('rfid_tag_id', 'pos_item_num', 'pos_item_class'),
        db.Index("idx_correlation", "correlation_id"),
        db.Index("idx_active_mappings", "is_active", "effective_date"),
    )
    
    mapping_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    correlation_id = db.Column(db.BigInteger, db.ForeignKey('inventory_correlation_master.correlation_id'), nullable=False)
    
    rfid_tag_id = db.Column(db.String(255), nullable=False)
    pos_item_num = db.Column(db.String(50))
    pos_item_class = db.Column(db.String(50))
    
    # Relationship metadata
    mapping_type = db.Column(db.String(20), default='ONE_TO_ONE')
    confidence_score = db.Column(db.DECIMAL(3, 2), default=1.00)
    
    # Validation
    is_validated = db.Column(db.Boolean, default=False)
    validated_date = db.Column(db.DateTime)
    validated_by = db.Column(db.String(100))
    
    # Active status
    is_active = db.Column(db.Boolean, default=True)
    effective_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime)
    
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    correlation = db.relationship("InventoryCorrelationMaster", back_populates="rfid_mappings")

class MigrationTracking(db.Model):
    """Track inventory migration from bulk to individual tracking"""
    __tablename__ = "migration_tracking"
    __table_args__ = (
        db.Index("idx_migration_status", "migration_status"),
        db.Index("idx_migration_correlation", "correlation_id"),
    )
    
    migration_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    correlation_id = db.Column(db.BigInteger, db.ForeignKey('inventory_correlation_master.correlation_id'), nullable=False)
    
    # Migration details
    from_tracking_type = db.Column(db.String(20))
    to_tracking_type = db.Column(db.String(20))
    migration_status = db.Column(db.String(20))
    
    # Quantities
    total_items_to_migrate = db.Column(db.Integer)
    items_migrated = db.Column(db.Integer, default=0)
    items_remaining = db.Column(db.Integer)
    
    # Timeline
    planned_start_date = db.Column(db.Date)
    actual_start_date = db.Column(db.DateTime)
    planned_completion_date = db.Column(db.Date)
    actual_completion_date = db.Column(db.DateTime)
    
    # Cost-benefit
    estimated_cost = db.Column(db.DECIMAL(10, 2))
    actual_cost = db.Column(db.DECIMAL(10, 2))
    estimated_roi_months = db.Column(db.Integer)
    
    # Progress
    last_batch_processed = db.Column(db.String(50))
    last_processed_date = db.Column(db.DateTime)
    error_count = db.Column(db.Integer, default=0)
    
    # Notes
    migration_notes = db.Column(db.Text)
    rollback_reason = db.Column(db.Text)
    
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    correlation = db.relationship("InventoryCorrelationMaster", back_populates="migrations")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'migration_id': self.migration_id,
            'correlation_id': self.correlation_id,
            'from_tracking_type': self.from_tracking_type,
            'to_tracking_type': self.to_tracking_type,
            'migration_status': self.migration_status,
            'total_items_to_migrate': self.total_items_to_migrate,
            'items_migrated': self.items_migrated,
            'progress_percentage': round((self.items_migrated / self.total_items_to_migrate * 100) if self.total_items_to_migrate else 0, 2),
            'planned_completion_date': self.planned_completion_date.isoformat() if self.planned_completion_date else None,
            'estimated_roi_months': self.estimated_roi_months
        }

class DataQualityMetrics(db.Model):
    """Track data quality issues and resolutions"""
    __tablename__ = "data_quality_metrics"
    __table_args__ = (
        db.Index("idx_quality_status", "resolution_status"),
        db.Index("idx_quality_severity", "severity"),
        db.Index("idx_quality_correlation", "correlation_id"),
    )
    
    metric_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    correlation_id = db.Column(db.BigInteger, db.ForeignKey('inventory_correlation_master.correlation_id'))
    
    # Issue identification
    issue_type = db.Column(db.String(20))
    severity = db.Column(db.String(20))
    
    # Issue details
    source_system = db.Column(db.String(50))
    field_name = db.Column(db.String(100))
    expected_value = db.Column(db.Text)
    actual_value = db.Column(db.Text)
    
    # Resolution
    resolution_status = db.Column(db.String(20))
    resolution_method = db.Column(db.String(100))
    resolved_date = db.Column(db.DateTime)
    resolved_by = db.Column(db.String(100))
    
    # Impact
    affected_records = db.Column(db.Integer)
    business_impact = db.Column(db.String(255))
    
    # Metadata
    detected_date = db.Column(db.DateTime, default=datetime.utcnow)
    detection_method = db.Column(db.String(100))
    
    # Relationships
    correlation = db.relationship("InventoryCorrelationMaster", back_populates="quality_metrics")

class InventoryIntelligence(db.Model):
    """Aggregated metrics for business intelligence"""
    __tablename__ = "inventory_intelligence"
    __table_args__ = (
        db.Index("idx_intelligence_correlation", "correlation_id"),
        db.Index("idx_utilization", "utilization_rate"),
        db.Index("idx_demand_trend", "demand_trend"),
    )
    
    intelligence_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    correlation_id = db.Column(db.BigInteger, db.ForeignKey('inventory_correlation_master.correlation_id'), nullable=False)
    
    # Utilization metrics
    utilization_rate = db.Column(db.DECIMAL(5, 2))
    days_since_last_use = db.Column(db.Integer)
    total_uses_30d = db.Column(db.Integer)
    total_uses_90d = db.Column(db.Integer)
    total_uses_365d = db.Column(db.Integer)
    
    # Financial metrics
    revenue_30d = db.Column(db.DECIMAL(12, 2))
    revenue_90d = db.Column(db.DECIMAL(12, 2))
    revenue_365d = db.Column(db.DECIMAL(12, 2))
    roi_percentage = db.Column(db.DECIMAL(6, 2))
    
    # Predictive indicators
    demand_trend = db.Column(db.String(20))
    seasonality_factor = db.Column(db.DECIMAL(3, 2))
    recommended_quantity = db.Column(db.Integer)
    reorder_point = db.Column(db.Integer)
    
    # Risk indicators
    damage_frequency = db.Column(db.DECIMAL(5, 2))
    loss_risk_score = db.Column(db.DECIMAL(3, 2))
    obsolescence_risk = db.Column(db.DECIMAL(3, 2))
    
    # Tracking recommendations
    should_add_tracking = db.Column(db.Boolean, default=False)
    recommended_tracking_type = db.Column(db.String(20))
    tracking_roi_estimate = db.Column(db.DECIMAL(10, 2))
    
    # Calculation metadata
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow)
    calculation_version = db.Column(db.String(20))
    
    # Relationships
    correlation = db.relationship("InventoryCorrelationMaster", back_populates="intelligence", uselist=False)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'intelligence_id': self.intelligence_id,
            'correlation_id': self.correlation_id,
            'utilization_rate': float(self.utilization_rate) if self.utilization_rate else 0,
            'demand_trend': self.demand_trend,
            'revenue_365d': float(self.revenue_365d) if self.revenue_365d else 0,
            'roi_percentage': float(self.roi_percentage) if self.roi_percentage else 0,
            'should_add_tracking': self.should_add_tracking,
            'recommended_tracking_type': self.recommended_tracking_type,
            'loss_risk_score': float(self.loss_risk_score) if self.loss_risk_score else 0
        }

class CorrelationAuditLog(db.Model):
    """Audit log for all correlation changes"""
    __tablename__ = "correlation_audit_log"
    __table_args__ = (
        db.Index("idx_audit_table", "table_name"),
        db.Index("idx_audit_date", "changed_date"),
        db.Index("idx_audit_user", "changed_by"),
    )
    
    audit_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    # What changed
    table_name = db.Column(db.String(100))
    record_id = db.Column(db.BigInteger)
    action = db.Column(db.String(20))
    
    # Change details
    old_values = db.Column(JSON)
    new_values = db.Column(JSON)
    changed_fields = db.Column(JSON)
    
    # Who and when
    changed_by = db.Column(db.String(100))
    changed_date = db.Column(db.DateTime, default=datetime.utcnow)
    change_source = db.Column(db.String(50))
    
    # Context
    session_id = db.Column(db.String(100))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))