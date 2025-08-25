# app/models/db_models.py
# db_models.py version: 2025-06-20-v3
from app import db
from datetime import datetime, timezone

class ItemMaster(db.Model):
    __tablename__ = 'id_item_master'
    __table_args__ = (
        db.Index('ix_item_master_rental_class_num', 'rental_class_num'),
        db.Index('ix_item_master_status', 'status'),
        db.Index('ix_item_master_bin_location', 'bin_location'),
    )

    tag_id = db.Column(db.String(255), primary_key=True)
    uuid_accounts_fk = db.Column(db.String(255))
    serial_number = db.Column(db.String(255))
    client_name = db.Column(db.String(255))
    rental_class_num = db.Column(db.String(255))
    common_name = db.Column(db.String(255))
    quality = db.Column(db.String(50))
    bin_location = db.Column(db.String(255))
    status = db.Column(db.String(50))
    last_contract_num = db.Column(db.String(255))
    last_scanned_by = db.Column(db.String(255))
    notes = db.Column(db.Text)
    status_notes = db.Column(db.Text)
    longitude = db.Column(db.DECIMAL(9, 6))
    latitude = db.Column(db.DECIMAL(9, 6))
    date_last_scanned = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'tag_id': self.tag_id,
            'uuid_accounts_fk': self.uuid_accounts_fk,
            'serial_number': self.serial_number,
            'client_name': self.client_name,
            'rental_class_num': self.rental_class_num,
            'common_name': self.common_name,
            'quality': self.quality,
            'bin_location': self.bin_location,
            'status': self.status,
            'last_contract_num': self.last_contract_num,
            'last_scanned_by': self.last_scanned_by,
            'notes': self.notes,
            'status_notes': self.status_notes,
            'longitude': float(self.longitude) if self.longitude else None,
            'latitude': float(self.latitude) if self.latitude else None,
            'date_last_scanned': self.date_last_scanned.isoformat() if self.date_last_scanned else None,
            'date_created': self.date_created.isoformat() if self.date_created else None,
            'date_updated': self.date_updated.isoformat() if self.date_updated else None
        }

class Transaction(db.Model):
    __tablename__ = 'id_transactions'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    contract_number = db.Column(db.String(255))
    tag_id = db.Column(db.String(255), nullable=False)
    scan_type = db.Column(db.String(50), nullable=False)
    scan_date = db.Column(db.DateTime, nullable=False)
    client_name = db.Column(db.String(255))
    common_name = db.Column(db.String(255), nullable=False)
    bin_location = db.Column(db.String(255))
    status = db.Column(db.String(50))
    scan_by = db.Column(db.String(255))
    location_of_repair = db.Column(db.String(255))
    quality = db.Column(db.String(50))
    dirty_or_mud = db.Column(db.Boolean)
    leaves = db.Column(db.Boolean)
    oil = db.Column(db.Boolean)
    mold = db.Column(db.Boolean)
    stain = db.Column(db.Boolean)
    oxidation = db.Column(db.Boolean)
    other = db.Column(db.Text)
    rip_or_tear = db.Column(db.Boolean)
    sewing_repair_needed = db.Column(db.Boolean)
    grommet = db.Column(db.Boolean)
    rope = db.Column(db.Boolean)
    buckle = db.Column(db.Boolean)
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)
    uuid_accounts_fk = db.Column(db.String(255))
    serial_number = db.Column(db.String(255))
    rental_class_num = db.Column(db.String(255))
    longitude = db.Column(db.DECIMAL(9, 6))
    latitude = db.Column(db.DECIMAL(9, 6))
    wet = db.Column(db.Boolean)
    service_required = db.Column(db.Boolean)
    notes = db.Column(db.Text)

class RFIDTag(db.Model):
    __tablename__ = 'id_rfidtag'
    __table_args__ = (
        db.Index('ix_rfidtag_rental_class_num', 'rental_class_num'),
        db.Index('ix_rfidtag_status', 'status'),
        db.Index('ix_rfidtag_bin_location', 'bin_location'),
    )

    tag_id = db.Column(db.String(255), primary_key=True)
    uuid_accounts_fk = db.Column(db.String(255))
    category = db.Column(db.String(255))
    serial_number = db.Column(db.String(255))
    client_name = db.Column(db.String(255))
    rental_class_num = db.Column(db.String(255))
    common_name = db.Column(db.String(255))
    quality = db.Column(db.String(50))
    bin_location = db.Column(db.String(255))
    status = db.Column(db.String(50))
    last_contract_num = db.Column(db.String(255))
    last_scanned_by = db.Column(db.String(255))
    notes = db.Column(db.Text)
    status_notes = db.Column(db.Text)
    longitude = db.Column(db.DECIMAL(9, 6))
    latitude = db.Column(db.DECIMAL(9, 6))
    date_last_scanned = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'tag_id': self.tag_id,
            'uuid_accounts_fk': self.uuid_accounts_fk,
            'category': self.category,
            'serial_number': self.serial_number,
            'client_name': self.client_name,
            'rental_class_num': self.rental_class_num,
            'common_name': self.common_name,
            'quality': self.quality,
            'bin_location': self.bin_location,
            'status': self.status,
            'last_contract_num': self.last_contract_num,
            'last_scanned_by': self.last_scanned_by,
            'notes': self.notes,
            'status_notes': self.status_notes,
            'longitude': float(self.longitude) if self.longitude else None,
            'latitude': float(self.latitude) if self.latitude else None,
            'date_last_scanned': self.date_last_scanned.isoformat() if self.date_last_scanned else None,
            'date_created': self.date_created.isoformat() if self.date_created else None,
            'date_updated': self.date_updated.isoformat() if self.date_updated else None
        }

class SeedRentalClass(db.Model):
    __tablename__ = 'seed_rental_classes'

    rental_class_id = db.Column(db.String(255), primary_key=True)
    common_name = db.Column(db.String(255))
    bin_location = db.Column(db.String(255))

class RefreshState(db.Model):
    __tablename__ = 'refresh_state'

    id = db.Column(db.Integer, primary_key=True)
    last_refresh = db.Column(db.DateTime)  # Changed to DateTime
    state_type = db.Column(db.String(50))  # Added state_type

class RentalClassMapping(db.Model):
    __tablename__ = 'rental_class_mappings'

    rental_class_id = db.Column(db.String(50), primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100), nullable=False)
    short_common_name = db.Column(db.String(50))

class HandCountedItems(db.Model):
    __tablename__ = 'id_hand_counted_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_number = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    user = db.Column(db.String(50), nullable=False)

class HandCountedCatalog(db.Model):
    __tablename__ = 'hand_counted_catalog'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rental_class_id = db.Column(db.String(50))
    item_name = db.Column(db.String(255), unique=True, nullable=False)
    hand_counted_name = db.Column(db.String(255))  # Custom display name for hand counted items

class UserRentalClassMapping(db.Model):
    __tablename__ = 'user_rental_class_mappings'

    rental_class_id = db.Column(db.String(50), primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100), nullable=False)
    short_common_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ContractSnapshot(db.Model):
    __tablename__ = 'contract_snapshots'
    __table_args__ = (
        db.Index('ix_contract_snapshots_contract_number', 'contract_number'),
        db.Index('ix_contract_snapshots_snapshot_date', 'snapshot_date'),
        db.Index('ix_contract_snapshots_tag_id', 'tag_id'),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    contract_number = db.Column(db.String(255), nullable=False)
    tag_id = db.Column(db.String(255), nullable=False)
    client_name = db.Column(db.String(255))
    common_name = db.Column(db.String(255))
    rental_class_num = db.Column(db.String(255))
    status = db.Column(db.String(50))
    quality = db.Column(db.String(50))
    bin_location = db.Column(db.String(255))
    serial_number = db.Column(db.String(255))
    notes = db.Column(db.Text)
    snapshot_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    snapshot_type = db.Column(db.String(50), nullable=False)  # 'contract_start', 'contract_end', 'status_change', 'periodic'
    created_by = db.Column(db.String(255))
    latitude = db.Column(db.DECIMAL(9, 6))
    longitude = db.Column(db.DECIMAL(9, 6))
    
    def to_dict(self):
        return {
            'id': self.id,
            'contract_number': self.contract_number,
            'tag_id': self.tag_id,
            'client_name': self.client_name,
            'common_name': self.common_name,
            'rental_class_num': self.rental_class_num,
            'status': self.status,
            'quality': self.quality,
            'bin_location': self.bin_location,
            'serial_number': self.serial_number,
            'notes': self.notes,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'snapshot_type': self.snapshot_type,
            'created_by': self.created_by,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None
        }

class LaundryContractStatus(db.Model):
    __tablename__ = 'laundry_contract_status'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_number = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='active')
    finalized_date = db.Column(db.DateTime)
    finalized_by = db.Column(db.String(100))
    returned_date = db.Column(db.DateTime)
    returned_by = db.Column(db.String(100))
    pickup_date = db.Column(db.DateTime)
    pickup_by = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'contract_number': self.contract_number,
            'status': self.status,
            'finalized_date': self.finalized_date.isoformat() if self.finalized_date else None,
            'finalized_by': self.finalized_by,
            'returned_date': self.returned_date.isoformat() if self.returned_date else None,
            'returned_by': self.returned_by,
            'pickup_date': self.pickup_date.isoformat() if self.pickup_date else None,
            'pickup_by': self.pickup_by,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ItemUsageHistory(db.Model):
    __tablename__ = 'item_usage_history'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    tag_id = db.Column(db.String(255), nullable=False, index=True)
    event_type = db.Column(db.Enum('rental', 'return', 'service', 'status_change', 'location_change', 'quality_change'), nullable=False)
    contract_number = db.Column(db.String(255), nullable=True, index=True)
    event_date = db.Column(db.DateTime, nullable=False, index=True)
    duration_days = db.Column(db.Integer, nullable=True)
    previous_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=True)
    previous_location = db.Column(db.String(255), nullable=True)
    new_location = db.Column(db.String(255), nullable=True)
    previous_quality = db.Column(db.String(50), nullable=True)
    new_quality = db.Column(db.String(50), nullable=True)
    utilization_score = db.Column(db.Numeric(5, 2), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tag_id': self.tag_id,
            'event_type': self.event_type,
            'contract_number': self.contract_number,
            'event_date': self.event_date.isoformat() if self.event_date else None,
            'duration_days': self.duration_days,
            'previous_status': self.previous_status,
            'new_status': self.new_status,
            'previous_location': self.previous_location,
            'new_location': self.new_location,
            'previous_quality': self.previous_quality,
            'new_quality': self.new_quality,
            'utilization_score': float(self.utilization_score) if self.utilization_score else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class InventoryHealthAlert(db.Model):
    __tablename__ = 'inventory_health_alerts'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    tag_id = db.Column(db.String(255), nullable=True, index=True)
    rental_class_id = db.Column(db.String(255), nullable=True, index=True)
    common_name = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(100), nullable=True, index=True)
    subcategory = db.Column(db.String(100), nullable=True, index=True)
    alert_type = db.Column(db.Enum('stale_item', 'high_usage', 'low_usage', 'missing', 'quality_decline', 'resale_restock', 'pack_status_review'), nullable=False, index=True)
    severity = db.Column(db.Enum('low', 'medium', 'high', 'critical'), nullable=False, index=True)
    days_since_last_scan = db.Column(db.Integer, nullable=True)
    last_scan_date = db.Column(db.DateTime, nullable=True)
    suggested_action = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum('active', 'acknowledged', 'resolved', 'dismissed'), nullable=False, default='active', index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    acknowledged_by = db.Column(db.String(255), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.String(255), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tag_id': self.tag_id,
            'rental_class_id': self.rental_class_id,
            'common_name': self.common_name,
            'category': self.category,
            'subcategory': self.subcategory,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'days_since_last_scan': self.days_since_last_scan,
            'last_scan_date': self.last_scan_date.isoformat() if self.last_scan_date else None,
            'suggested_action': self.suggested_action,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by
        }

class InventoryConfig(db.Model):
    __tablename__ = 'inventory_config'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    config_key = db.Column(db.String(100), nullable=False, unique=True, index=True)
    config_value = db.Column(db.JSON, nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.config_value,
            'description': self.description,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
