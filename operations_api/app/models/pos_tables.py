"""
POS Table Models for Operations
Version: 1.0.0
Date: 2025-09-20
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, DECIMAL, Boolean, Date, Time, BigInteger
from app.database.session import Base

class POSEquipment(Base):
    """POS Equipment table - bulk items without individual RFID"""
    __tablename__ = "pos_equipment"
    __bind_key__ = 'manager'  # Uses manager database

    id = Column(Integer, primary_key=True)
    item_num = Column(String(50), unique=True)
    name = Column(String(500))
    category = Column(String(100))
    home_store = Column(String(10))
    current_store = Column(String(10))
    qty = Column(Integer, default=0)  # Available quantity

    # Rental periods and rates
    per1 = Column(DECIMAL(10, 2))
    per2 = Column(DECIMAL(10, 2))
    per3 = Column(DECIMAL(10, 2))
    per4 = Column(DECIMAL(10, 2))
    per5 = Column(DECIMAL(10, 2))
    rate1 = Column(DECIMAL(10, 2))
    rate2 = Column(DECIMAL(10, 2))
    rate3 = Column(DECIMAL(10, 2))
    rate4 = Column(DECIMAL(10, 2))
    rate5 = Column(DECIMAL(10, 2))

    # Physical dimensions
    height = Column(DECIMAL(10, 2))
    width = Column(DECIMAL(10, 2))
    length = Column(DECIMAL(10, 2))
    weight = Column(DECIMAL(10, 2))

    # Additional fields
    manf = Column(String(100))
    model_no = Column(String(100))
    serial_no = Column(String(100))
    part_no = Column(String(100))
    department = Column(String(100))
    type_desc = Column(String(100))

class POSCustomers(Base):
    """POS Customers table"""
    __tablename__ = "pos_customers"
    __bind_key__ = 'manager'

    id = Column(Integer, primary_key=True)
    store_code = Column(String(10), default='000')
    key = Column(String(20))
    cnum = Column(String(50), unique=True)  # Customer number
    name = Column(String(255), index=True)
    address = Column(String(255))
    address2 = Column(String(255))
    city = Column(String(255))
    state = Column(String(50))
    zip = Column(String(20))
    zip4 = Column(String(20))
    phone = Column(String(50))
    phone2 = Column(String(50))
    email = Column(String(255))
    driverslicense = Column(String(255))
    birthdate = Column(Date)
    employer = Column(String(255))
    auto_license = Column(String(255))
    contact_person = Column(String(255))

class POSTransactions(Base):
    """POS Transactions table - contracts/reservations"""
    __tablename__ = "pos_transactions"
    __bind_key__ = 'manager'

    id = Column(BigInteger, primary_key=True)
    contract_no = Column(String(50), nullable=False, index=True)
    store_no = Column(String(10), nullable=False, index=True)
    customer_no = Column(String(50), index=True)
    stat = Column(String(5))  # Status code
    status = Column(String(50), index=True)  # Full status
    contract_date = Column(DateTime, index=True)
    contract_time = Column(String(10))
    last_modified_date = Column(DateTime)
    close_date = Column(DateTime)
    billed_date = Column(DateTime)
    completed_date = Column(DateTime)

    # Delivery/pickup info
    delivery_date = Column(DateTime)
    pickup_date = Column(DateTime)
    delivery_address = Column(Text)
    delivery_notes = Column(Text)

    # Financial (included for operations context)
    rent_amt = Column(DECIMAL(12, 2))
    sale_amt = Column(DECIMAL(12, 2))
    deposit_amt = Column(DECIMAL(12, 2))

    # Operations flags
    is_manual = Column(Boolean, default=False)  # Manual entry flag
    temp_id = Column(String(50))  # For POS merge

class POSTransactionItems(Base):
    """POS Transaction Items - items on contracts"""
    __tablename__ = "pos_transaction_items"
    __bind_key__ = 'manager'

    id = Column(Integer, primary_key=True)
    contract_number = Column(String(100), index=True)
    sub_field = Column(String(100))
    item_number = Column(String(100), index=True)
    quantity = Column(Integer)
    hrsc_field = Column(String(100))
    ddt_field = Column(String(100))
    dtm_field = Column(Time)
    txty_field = Column(String(100))
    price_field = Column(DECIMAL(12, 2))
    description_field = Column(Text)
    comments_field = Column(Text)
    damage_waiver = Column(DECIMAL(12, 2))
    item_percentage = Column(DECIMAL(12, 2))

    # Additional operations fields
    checked_out_qty = Column(Integer, default=0)
    returned_qty = Column(Integer, default=0)
    damaged_qty = Column(Integer, default=0)
    missing_qty = Column(Integer, default=0)

class ItemMaster(Base):
    """RFID Item Master table"""
    __tablename__ = "id_item_master"
    __bind_key__ = 'manager'

    tag_id = Column(String(255), primary_key=True)
    item_num = Column(Integer, unique=True)
    uuid_accounts_fk = Column(String(255))
    serial_number = Column(String(255))
    client_name = Column(String(255))
    rental_class_num = Column(String(255), index=True)
    common_name = Column(String(255))
    quality = Column(String(50))
    bin_location = Column(String(255))
    status = Column(String(50), index=True)
    last_contract_num = Column(String(255))
    last_scanned_by = Column(String(255))
    notes = Column(Text)
    status_notes = Column(Text)
    longitude = Column(DECIMAL(9, 6))
    latitude = Column(DECIMAL(9, 6))
    date_last_scanned = Column(DateTime, index=True)
    date_created = Column(DateTime)
    date_updated = Column(DateTime)
    home_store = Column(String(10))
    current_store = Column(String(10), index=True)
    identifier_type = Column(String(10), index=True)
    manufacturer = Column(String(100))

    # Financial fields (operations view)
    turnover_ytd = Column(DECIMAL(10, 2))
    turnover_ltd = Column(DECIMAL(10, 2))
    repair_cost_ltd = Column(DECIMAL(10, 2))
    sell_price = Column(DECIMAL(10, 2))
    retail_price = Column(DECIMAL(10, 2))

class Transactions(Base):
    """RFID Transactions table"""
    __tablename__ = "id_transactions"
    __bind_key__ = 'manager'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_number = Column(String(255))
    tag_id = Column(String(255), nullable=False, index=True)
    scan_type = Column(String(50), nullable=False)
    scan_date = Column(DateTime, nullable=False, index=True)
    client_name = Column(String(255))
    common_name = Column(String(255), nullable=False)
    bin_location = Column(String(255))
    status = Column(String(50))
    scan_by = Column(String(255))
    location_of_repair = Column(String(255))
    quality = Column(String(50))

    # Condition flags
    dirty_or_mud = Column(Boolean, default=False)
    leaves = Column(Boolean, default=False)
    oil = Column(Boolean, default=False)
    mold = Column(Boolean, default=False)
    stain = Column(Boolean, default=False)
    oxidation = Column(Boolean, default=False)
    other = Column(Text)
    rip_or_tear = Column(Boolean, default=False)
    sewing_repair_needed = Column(Boolean, default=False)
    grommet = Column(Boolean, default=False)
    rope = Column(Boolean, default=False)
    buckle = Column(Boolean, default=False)
    wet = Column(Boolean, default=False)
    service_required = Column(Boolean, default=False)

    date_created = Column(DateTime)
    date_updated = Column(DateTime)
    uuid_accounts_fk = Column(String(255))
    serial_number = Column(String(255))
    rental_class_num = Column(String(255))
    longitude = Column(DECIMAL(9, 6))
    latitude = Column(DECIMAL(9, 6))
    notes = Column(Text)