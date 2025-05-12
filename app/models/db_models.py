from app import db  # Import db from app/__init__.py
from datetime import datetime

class ItemMaster(db.Model):
    __tablename__ = 'id_item_master'

    tag_id = db.Column(db.String(50), primary_key=True)
    uuid_accounts_fk = db.Column(db.String(50))
    serial_number = db.Column(db.String(50))
    client_name = db.Column(db.String(100))
    rental_class_num = db.Column(db.String(50))
    common_name = db.Column(db.String(255))
    quality = db.Column(db.String(50))
    bin_location = db.Column(db.String(50))
    status = db.Column(db.String(50))
    last_contract_num = db.Column(db.String(50))
    last_scanned_by = db.Column(db.String(50))
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

    contract_number = db.Column(db.String(50))
    tag_id = db.Column(db.String(50), primary_key=True)
    scan_type = db.Column(db.String(50))
    scan_date = db.Column(db.DateTime, primary_key=True)
    client_name = db.Column(db.String(100))
    common_name = db.Column(db.String(255))
    bin_location = db.Column(db.String(50))
    status = db.Column(db.String(50))
    scan_by = db.Column(db.String(50))
    location_of_repair = db.Column(db.String(50))
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
    uuid_accounts_fk = db.Column(db.String(50))
    serial_number = db.Column(db.String(50))
    rental_class_num = db.Column(db.String(50))
    longitude = db.Column(db.DECIMAL(9, 6))
    latitude = db.Column(db.DECIMAL(9, 6))
    wet = db.Column(db.Boolean)
    service_required = db.Column(db.Boolean)
    notes = db.Column(db.Text)

class SeedRentalClass(db.Model):
    __tablename__ = 'seed_rental_classes'

    rental_class_id = db.Column(db.String(50), primary_key=True)
    common_name = db.Column(db.String(255))

class RefreshState(db.Model):
    __tablename__ = 'refresh_state'

    id = db.Column(db.Integer, primary_key=True)
    last_refresh = db.Column(db.String(50))

class RentalClassMapping(db.Model):
    __tablename__ = 'rental_class_mappings'

    rental_class_id = db.Column(db.String(50), primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100), nullable=False)
    short_common_name = db.Column(db.String(50))  # Added for short common name

# Added on 2025-04-21 to track hand-counted items for contracts
class HandCountedItems(db.Model):
    __tablename__ = 'id_hand_counted_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_number = db.Column(db.String(50), nullable=False)  # Links to the contract
    item_name = db.Column(db.String(255), nullable=False)      # e.g., "Napkins"
    quantity = db.Column(db.Integer, nullable=False)           # Number of items
    action = db.Column(db.String(50), nullable=False)          # "Added" or "Removed"
    timestamp = db.Column(db.DateTime, nullable=False)         # When the action occurred
    user = db.Column(db.String(50), nullable=False)            # Who performed the action

# Added on 2025-04-23 to store user-defined rental class mappings
class UserRentalClassMapping(db.Model):
    __tablename__ = 'user_rental_class_mappings'

    rental_class_id = db.Column(db.String(50), primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100), nullable=False)
    short_common_name = db.Column(db.String(50))  # Added for short common name
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)