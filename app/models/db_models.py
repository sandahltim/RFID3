# app/models/db_models.py
# db_models.py version: 2025-06-20-v3
from app import db
from datetime import datetime

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

class UserRentalClassMapping(db.Model):
    __tablename__ = 'user_rental_class_mappings'

    rental_class_id = db.Column(db.String(50), primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100), nullable=False)
    short_common_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
