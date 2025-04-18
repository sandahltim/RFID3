from app import db

class ItemMaster(db.Model):
    __tablename__ = 'id_item_master'
    tag_id = db.Column(db.String(255), primary_key=True)
    uuid_accounts_fk = db.Column(db.String(255))
    serial_number = db.Column(db.String(255))
    client_name = db.Column(db.String(255))
    rental_class_num = db.Column(db.Integer)
    common_name = db.Column(db.String(255))
    quality = db.Column(db.String(50))
    bin_location = db.Column(db.String(255))
    status = db.Column(db.String(50))
    last_contract_num = db.Column(db.String(255))
    last_scanned_by = db.Column(db.String(255))
    notes = db.Column(db.Text)
    status_notes = db.Column(db.Text)
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
    date_last_scanned = db.Column(db.String(50))
    date_created = db.Column(db.String(50))
    date_updated = db.Column(db.String(50))

class RfidTag(db.Model):
    __tablename__ = 'id_rfidtag'
    tag_id = db.Column(db.String(255), primary_key=True)
    item_type = db.Column(db.String(255))
    common_name = db.Column(db.String(255))
    category = db.Column(db.String(255))
    status = db.Column(db.String(50))
    last_contract_num = db.Column(db.String(255))
    date_assigned = db.Column(db.String(50))
    date_sold = db.Column(db.String(50))
    date_discarded = db.Column(db.String(50))
    reuse_count = db.Column(db.Integer)
    last_updated = db.Column(db.String(50))

class Transaction(db.Model):
    __tablename__ = 'id_transactions'
    contract_number = db.Column(db.String(255), primary_key=True)
    tag_id = db.Column(db.String(255), primary_key=True)
    scan_type = db.Column(db.String(50), primary_key=True)
    scan_date = db.Column(db.String(50), primary_key=True)
    client_name = db.Column(db.String(255))
    common_name = db.Column(db.String(255))
    bin_location = db.Column(db.String(255))
    status = db.Column(db.String(50))
    scan_by = db.Column(db.String(255))
    location_of_repair = db.Column(db.String(255))
    quality = db.Column(db.String(50))
    dirty_or_mud = db.Column(db.String(50))
    leaves = db.Column(db.String(50))
    oil = db.Column(db.String(50))
    mold = db.Column(db.String(50))
    stain = db.Column(db.String(50))
    oxidation = db.Column(db.String(50))
    other = db.Column(db.String(255))
    rip_or_tear = db.Column(db.String(50))
    sewing_repair_needed = db.Column(db.String(50))
    grommet = db.Column(db.String(50))
    rope = db.Column(db.String(50))
    buckle = db.Column(db.String(50))
    date_created = db.Column(db.String(50))
    date_updated = db.Column(db.String(50))
    uuid_accounts_fk = db.Column(db.String(255))
    serial_number = db.Column(db.String(255))
    rental_class_num = db.Column(db.Integer)
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
    wet = db.Column(db.String(50))
    service_required = db.Column(db.String(50))
    notes = db.Column(db.Text)

class SeedRentalClass(db.Model):
    __tablename__ = 'seed_rental_classes'
    rental_class_id = db.Column(db.Integer, primary_key=True)
    common_name = db.Column(db.String(255))
    bin_location = db.Column(db.String(255))

class RefreshState(db.Model):
    __tablename__ = 'refresh_state'
    id = db.Column(db.Integer, primary_key=True)
    last_refresh = db.Column(db.String(50))