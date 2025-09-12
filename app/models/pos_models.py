# app/models/pos_models.py
# POS Integration Models for RFID Inventory System
# Created: 2025-08-28

from app import db
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Index, UniqueConstraint, func
from enum import Enum


class POSTransaction(db.Model):
    """Store POS transaction data imported from external accounting system."""
    __tablename__ = "pos_transactions"
    __table_args__ = (
        db.Index("ix_pos_trans_contract_no", "contract_no"),
        db.Index("ix_pos_trans_customer_no", "customer_no"),
        db.Index("ix_pos_trans_contract_date", "contract_date"),
        db.Index("ix_pos_trans_status", "status"),
        db.Index("ix_pos_trans_store_no", "store_no"),
        UniqueConstraint("contract_no", "store_no", name="uq_contract_store"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    contract_no = db.Column(db.String(50), nullable=False)
    store_no = db.Column(db.String(10), nullable=False)
    customer_no = db.Column(db.String(50))
    stat = db.Column(db.String(5))
    status = db.Column(db.String(50))
    contract_date = db.Column(db.DateTime)
    contract_time = db.Column(db.String(10))
    last_modified_date = db.Column(db.DateTime)
    close_date = db.Column(db.DateTime)
    billed_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    
    # Financial Fields
    rent_amt = db.Column(db.DECIMAL(12, 2))
    sale_amt = db.Column(db.DECIMAL(12, 2))
    tax_amt = db.Column(db.DECIMAL(12, 2))
    dmg_wvr_amt = db.Column(db.DECIMAL(12, 2))
    total = db.Column(db.DECIMAL(12, 2))
    total_paid = db.Column(db.DECIMAL(12, 2))
    payment_method = db.Column(db.String(50))
    total_owed = db.Column(db.DECIMAL(12, 2))
    deposit_paid_amt = db.Column(db.DECIMAL(12, 2))
    
    # Contact Info
    contact = db.Column(db.String(255))
    contact_phone = db.Column(db.String(50))
    ordered_by = db.Column(db.String(255))
    
    # Delivery Info
    delivery_requested = db.Column(db.Boolean, default=False)
    promised_delivery_date = db.Column(db.DateTime)
    actual_delivery_date = db.Column(db.DateTime)
    delivery_truck_no = db.Column(db.String(50))
    delivery_trip_no = db.Column(db.String(50))
    delivered_to = db.Column(db.String(255))
    delivery_address = db.Column(db.String(500))
    delivery_city = db.Column(db.String(100))
    delivery_zipcode = db.Column(db.String(20))
    
    # Pickup Info
    pickup_requested = db.Column(db.Boolean, default=False)
    promised_pickup_date = db.Column(db.DateTime)
    actual_pickup_date = db.Column(db.DateTime)
    pickup_truck_no = db.Column(db.String(50))
    pickup_trip_no = db.Column(db.String(50))
    picked_up_by = db.Column(db.String(255))
    
    # Job Info
    job_po = db.Column(db.String(100))
    job_id = db.Column(db.String(100))
    job_site = db.Column(db.String(255))
    type = db.Column(db.String(50))
    
    # Operator and Management Fields
    operator_id = db.Column(db.String(50))
    operator_created = db.Column(db.String(100))
    operator_assigned = db.Column(db.String(100))
    salesman = db.Column(db.String(100))
    current_modify_op_no = db.Column(db.String(50))
    
    # Transaction Status and Processing
    secondary_status = db.Column(db.String(50))
    cancelled = db.Column(db.Boolean, default=False)
    review_billing = db.Column(db.Boolean, default=False)
    archived = db.Column(db.Boolean, default=False)
    transaction_type = db.Column(db.String(50))
    operation = db.Column(db.String(50))
    
    # Financial Details
    rent_discount = db.Column(db.DECIMAL(10, 2))
    sale_discount = db.Column(db.DECIMAL(10, 2))
    sale_discount_percent = db.Column(db.DECIMAL(5, 2))
    item_percentage = db.Column(db.DECIMAL(5, 2))
    damage_waiver_exempt = db.Column(db.Boolean, default=False)
    item_percentage_exempt = db.Column(db.Boolean, default=False)
    damage_waiver_tax_amount = db.Column(db.DECIMAL(10, 2))
    item_percentage_tax_amount = db.Column(db.DECIMAL(10, 2))
    other_tax_amount = db.Column(db.DECIMAL(10, 2))
    tax_code = db.Column(db.String(20))
    price_level = db.Column(db.String(20))
    rate_engine_id = db.Column(db.String(50))
    desired_deposit = db.Column(db.DECIMAL(12, 2))
    
    # Payment and Accounting
    payment_deposit_paid = db.Column(db.DECIMAL(12, 2))
    payment_deposit_required = db.Column(db.DECIMAL(12, 2))
    card_swipe = db.Column(db.Boolean, default=False)
    posted_cash = db.Column(db.Boolean, default=False)
    posted_accrual = db.Column(db.Boolean, default=False)
    currency_number = db.Column(db.String(10))
    exchange_rate = db.Column(db.DECIMAL(10, 4))
    discount_table = db.Column(db.String(50))
    accounting_link = db.Column(db.String(100))
    accounting_transaction_id = db.Column(db.String(100))
    invoice_number = db.Column(db.String(100))
    revenue_date = db.Column(db.DateTime)
    
    # Delivery Details Enhancement
    delivery_confirmed = db.Column(db.Boolean, default=False)
    delivery_trip = db.Column(db.String(50))
    delivery_route = db.Column(db.String(100))
    delivery_crew_count = db.Column(db.Integer)
    delivery_setup_time = db.Column(db.Integer)  # minutes
    delivery_setup_time_computed = db.Column(db.Integer)  # minutes
    delivery_notes = db.Column(db.Text)
    deliver_to_company = db.Column(db.String(255))
    delivery_verified_address = db.Column(db.Boolean, default=False)
    delivery_same_address = db.Column(db.Boolean, default=False)
    
    # Pickup Details Enhancement
    pickup_confirmed = db.Column(db.Boolean, default=False)
    pickup_trip = db.Column(db.String(50))
    pickup_route = db.Column(db.String(100))
    pickup_crew_count = db.Column(db.Integer)
    pickup_load_time = db.Column(db.Integer)  # minutes
    pickup_notes = db.Column(db.Text)
    pickup_contact = db.Column(db.String(255))
    pickup_contact_phone = db.Column(db.String(50))
    pickup_from_company = db.Column(db.String(255))
    pickup_verified_address = db.Column(db.Boolean, default=False)
    pickup_same_address = db.Column(db.Boolean, default=False)
    pickup_address = db.Column(db.String(500))
    pickup_city = db.Column(db.String(100))
    pickup_zipcode = db.Column(db.String(20))
    picked_up_by_dl_no = db.Column(db.String(50))
    auto_license = db.Column(db.String(50))
    
    # Event and Contract Management
    event_end_date = db.Column(db.DateTime)
    master_bill = db.Column(db.String(50))
    parent_contract = db.Column(db.String(50))
    service_seq = db.Column(db.Integer)
    modification = db.Column(db.String(255))
    notes = db.Column(db.Text)
    class_id = db.Column(db.String(50))
    
    # Communication and Documentation
    last_letter = db.Column(db.String(50))
    letter_date = db.Column(db.DateTime)
    updated_date_time = db.Column(db.DateTime)
    created_date = db.Column(db.DateTime)
    
    # Import metadata
    import_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    import_batch = db.Column(db.String(50))
    
    # Relationship to items
    items = db.relationship("POSTransactionItem", back_populates="transaction", lazy='dynamic')
    
    def to_dict(self):
        return {
            "id": self.id,
            "contract_no": self.contract_no,
            "store_no": self.store_no,
            "customer_no": self.customer_no,
            "status": self.status,
            "contract_date": self.contract_date.isoformat() if self.contract_date else None,
            "rent_amt": float(self.rent_amt) if self.rent_amt else 0,
            "sale_amt": float(self.sale_amt) if self.sale_amt else 0,
            "tax_amt": float(self.tax_amt) if self.tax_amt else 0,
            "total": float(self.total) if self.total else 0,
            "total_paid": float(self.total_paid) if self.total_paid else 0,
            "payment_method": self.payment_method,
            "delivery_date": self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            "pickup_date": self.actual_pickup_date.isoformat() if self.actual_pickup_date else None,
            "import_date": self.import_date.isoformat() if self.import_date else None,
        }


class POSTransactionItem(db.Model):
    """Store individual line items from POS transactions."""
    __tablename__ = "pos_transaction_items"
    __table_args__ = (
        db.Index("ix_pos_items_contract_no", "contract_no"),
        db.Index("ix_pos_items_item_num", "item_num"),
        db.Index("ix_pos_items_due_date", "due_date"),
        db.Index("ix_pos_items_line_status", "line_status"),
        UniqueConstraint("contract_no", "line_number", name="uq_contract_line"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    contract_no = db.Column(db.String(50), db.ForeignKey('pos_transactions.contract_no'), nullable=False)
    item_num = db.Column(db.String(50))
    qty = db.Column(db.Integer)
    hours = db.Column(db.Integer)
    due_date = db.Column(db.DateTime)
    due_time = db.Column(db.String(10))
    line_status = db.Column(db.String(10))  # RX, RR, S, etc.
    price = db.Column(db.DECIMAL(10, 2))
    desc = db.Column(db.String(500))
    dmg_wvr = db.Column(db.DECIMAL(10, 2))
    item_percentage = db.Column(db.DECIMAL(5, 2))
    discount_percent = db.Column(db.DECIMAL(5, 2))
    nontaxable = db.Column(db.Boolean, default=False)
    nondiscount = db.Column(db.Boolean, default=False)
    discount_amt = db.Column(db.DECIMAL(10, 2))
    
    # Rate fields
    daily_amt = db.Column(db.DECIMAL(10, 2))
    weekly_amt = db.Column(db.DECIMAL(10, 2))
    monthly_amt = db.Column(db.DECIMAL(10, 2))
    minimum_amt = db.Column(db.DECIMAL(10, 2))
    
    # Meter fields
    meter_out = db.Column(db.DECIMAL(10, 2))
    meter_in = db.Column(db.DECIMAL(10, 2))
    downtime_hrs = db.Column(db.DECIMAL(10, 2))
    retail_price = db.Column(db.DECIMAL(10, 2))
    
    kit_field = db.Column(db.String(255))
    confirmed_date = db.Column(db.DateTime)
    line_number = db.Column(db.Integer)
    
    # Import metadata
    import_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationship to transaction
    transaction = db.relationship("POSTransaction", back_populates="items")
    
    def to_dict(self):
        return {
            "id": self.id,
            "contract_no": self.contract_no,
            "item_num": self.item_num,
            "qty": self.qty,
            "price": float(self.price) if self.price else 0,
            "desc": self.desc,
            "line_status": self.line_status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "retail_price": float(self.retail_price) if self.retail_price else 0,
        }


class POSEquipment(db.Model):
    """Store POS equipment/inventory data imported from external accounting system."""
    __tablename__ = "pos_equipment"
    __table_args__ = (
        db.Index("ix_pos_equip_item_num", "item_num"),
        db.Index("ix_pos_equip_current_store", "current_store"),
        db.Index("ix_pos_equip_category", "category"),
        db.Index("ix_pos_equip_department", "department"),
        db.Index("ix_pos_equip_inactive", "inactive"),
        UniqueConstraint("item_num", name="uq_item_num"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    item_num = db.Column(db.String(50), nullable=False, unique=True)
    key_field = db.Column('key_field', db.String(50))  # Maps to key_field column
    name = db.Column(db.String(255))
    loc = db.Column('loc', db.String(100))  # Maps to loc column
    category = db.Column(db.String(100))
    department = db.Column(db.String(100))
    type_desc = db.Column(db.String(100))
    qty = db.Column('qty', db.Integer, default=0)  # Maps to qty column
    home_store = db.Column(db.String(10))
    current_store = db.Column(db.String(10))
    group_field = db.Column('group_field', db.String(100))  # Maps to group_field column
    manf = db.Column('manf', db.String(100))  # Maps to manf column
    model_no = db.Column(db.String(100))
    serial_no = db.Column(db.String(100))
    part_no = db.Column(db.String(100))
    license_no = db.Column(db.String(50))
    model_year = db.Column(db.String(10))
    
    # Financial Fields - match database column names
    to_mtd = db.Column('to_mtd', db.DECIMAL(12, 2), default=0)  # Maps to to_mtd
    to_ytd = db.Column('to_ytd', db.DECIMAL(12, 2), default=0)  # Maps to to_ytd
    to_ltd = db.Column('to_ltd', db.DECIMAL(12, 2), default=0)  # Maps to to_ltd
    repair_cost_mtd = db.Column(db.DECIMAL(10, 2), default=0)
    repair_cost_ltd = db.Column(db.DECIMAL(10, 2), default=0)
    sell_price = db.Column(db.DECIMAL(10, 2), default=0)
    retail_price = db.Column(db.DECIMAL(10, 2), default=0)
    deposit = db.Column(db.DECIMAL(10, 2), default=0)
    damage_waiver_percent = db.Column('damage_waiver_percent', db.DECIMAL(5, 2), default=0)  # Maps to damage_waiver_percent
    
    # Rental Rates (10 periods) - match database schema
    period_1 = db.Column(db.DECIMAL(10, 2))
    period_2 = db.Column(db.DECIMAL(10, 2))
    period_3 = db.Column(db.DECIMAL(10, 2))
    period_4 = db.Column(db.DECIMAL(10, 2))
    period_5 = db.Column(db.DECIMAL(10, 2))
    period_6 = db.Column(db.DECIMAL(10, 2))
    period_7 = db.Column(db.DECIMAL(10, 2))
    period_8 = db.Column(db.DECIMAL(10, 2))
    period_9 = db.Column(db.DECIMAL(10, 2))
    period_10 = db.Column(db.DECIMAL(10, 2))
    rate_1 = db.Column(db.DECIMAL(10, 2))
    rate_2 = db.Column(db.DECIMAL(10, 2))
    rate_3 = db.Column(db.DECIMAL(10, 2))
    rate_4 = db.Column(db.DECIMAL(10, 2))
    rate_5 = db.Column(db.DECIMAL(10, 2))
    rate_6 = db.Column(db.DECIMAL(10, 2))
    rate_7 = db.Column(db.DECIMAL(10, 2))
    rate_8 = db.Column(db.DECIMAL(10, 2))
    rate_9 = db.Column(db.DECIMAL(10, 2))
    rate_10 = db.Column(db.DECIMAL(10, 2))
    
    # Inventory Management
    reorder_min = db.Column(db.Integer, default=0)
    reorder_max = db.Column(db.Integer, default=0)
    user_defined_1 = db.Column(db.String(100))
    user_defined_2 = db.Column(db.String(100))
    meter_out = db.Column(db.DECIMAL(10, 2))  # Match database precision
    meter_in = db.Column(db.DECIMAL(10, 2))  # Match database precision
    
    # Purchase/Vendor Info
    last_purchase_date = db.Column(db.Date)  # Date not DateTime
    last_purchase_price = db.Column(db.DECIMAL(10, 2))  # 10,2 to match database
    vendor_no_1 = db.Column(db.String(50))
    vendor_no_2 = db.Column(db.String(50))
    vendor_no_3 = db.Column(db.String(50))
    order_no_1 = db.Column(db.String(50))
    order_no_2 = db.Column(db.String(50))
    order_no_3 = db.Column(db.String(50))
    qty_on_order = db.Column(db.Integer, default=0)
    
    # Other Fields
    sort_field = db.Column('sort_field', db.String(100))  # Maps to sort_field column (not sort_order)
    expiration_date = db.Column(db.Date)  # Date not DateTime
    warranty_date = db.Column(db.Date)  # Date not DateTime
    weight = db.Column(db.DECIMAL(10, 3))  # Note: 3 decimal places in DB
    setup_time = db.Column(db.DECIMAL(10, 2))
    income = db.Column(db.DECIMAL(12, 2))
    depr_method = db.Column(db.String(50))
    depr = db.Column(db.DECIMAL(10, 2))  # 10,2 not 12,2
    non_taxable = db.Column(db.Boolean, default=False)
    header_no = db.Column(db.String(50))
    inactive = db.Column(db.Boolean, default=False)
    
    # RFID-specific fields missing from model
    pos_store_code = db.Column(db.String(10))
    rfid_rental_class_num = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    identifier_type = db.Column(db.Enum('RFID', 'Sticker', 'QR', 'Barcode', 'Bulk', 'None', name='identifier_type_enum'), default='None')
    
    # Note: import_date, import_batch, last_updated columns do not exist in database schema
    
    def to_dict(self):
        return {
            "id": self.id,
            "item_num": self.item_num,
            "key_field": self.key_field,
            "name": self.name,
            "loc": self.loc,
            "category": self.category,
            "department": self.department,
            "qty": self.qty,
            "current_store": self.current_store,
            "group_field": self.group_field,
            "manf": self.manf,
            "to_ytd": float(self.to_ytd) if self.to_ytd else 0,
            "to_ltd": float(self.to_ltd) if self.to_ltd else 0,
            "repair_cost_ltd": float(self.repair_cost_ltd) if self.repair_cost_ltd else 0,
            "sell_price": float(self.sell_price) if self.sell_price else 0,
            "inactive": self.inactive,
        }


class POSCustomer(db.Model):
    """Store POS customer data for correlation."""
    __tablename__ = "pos_customers"
    __table_args__ = (
        db.Index("ix_pos_cust_cnum", "cnum"),
        db.Index("ix_pos_cust_name", "name"),
        UniqueConstraint("key", name="uq_customer_key"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    key = db.Column(db.String(50), nullable=False)
    cnum = db.Column(db.String(50))
    name = db.Column(db.String(255))
    address = db.Column(db.String(500))
    address2 = db.Column(db.String(500))
    city = db.Column(db.String(100))
    zip = db.Column(db.String(20))
    zip4 = db.Column(db.String(10))
    phone = db.Column(db.String(50))
    work_phone = db.Column(db.String(50))
    mobile_phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    
    # Financial info
    credit_limit = db.Column(db.DECIMAL(12, 2))
    ytd_payments = db.Column(db.DECIMAL(12, 2))
    ltd_payments = db.Column(db.DECIMAL(12, 2))
    last_year_payments = db.Column(db.DECIMAL(12, 2))
    no_of_contracts = db.Column(db.Integer)
    current_balance = db.Column(db.DECIMAL(12, 2))
    
    # Activity tracking
    open_date = db.Column(db.DateTime)
    last_active_date = db.Column(db.DateTime)
    last_contract = db.Column(db.String(50))
    
    # Import metadata
    import_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "cnum": self.cnum,
            "name": self.name,
            "city": self.city,
            "email": self.email,
            "phone": self.phone,
            "credit_limit": float(self.credit_limit) if self.credit_limit else 0,
            "current_balance": float(self.current_balance) if self.current_balance else 0,
            "last_active_date": self.last_active_date.isoformat() if self.last_active_date else None,
        }


class POSRFIDCorrelation(db.Model):
    """Map POS items to RFID-tracked items using various correlation strategies."""
    __tablename__ = "pos_rfid_correlations"
    __table_args__ = (
        db.Index("ix_pos_rfid_corr_pos_item", "pos_item_num"),
        db.Index("ix_pos_rfid_corr_rfid_class", "rfid_rental_class_num"),
        db.Index("ix_pos_rfid_corr_tag_id", "rfid_tag_id"),
        db.Index("ix_pos_rfid_corr_confidence", "confidence_score"),
        db.Index("ix_pos_rfid_corr_type", "correlation_type"),
        UniqueConstraint("pos_item_num", "rfid_rental_class_num", "correlation_type", 
                        name="uq_pos_rfid_mapping"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    # POS side
    pos_item_num = db.Column(db.String(50), nullable=False)
    pos_item_desc = db.Column(db.String(500))
    
    # RFID side - can map to either specific item or rental class
    rfid_tag_id = db.Column(db.String(255))  # For individually tracked items
    rfid_rental_class_num = db.Column(db.String(255))  # For bulk/category items
    rfid_common_name = db.Column(db.String(255))
    
    # Correlation metadata
    correlation_type = db.Column(
        db.Enum('exact', 'fuzzy', 'manual', 'barcode', 'qr', 'bulk'),
        nullable=False
    )
    confidence_score = db.Column(db.DECIMAL(3, 2))  # 0.00 to 1.00
    match_criteria = db.Column(db.JSON)  # Store what matched (e.g., {"upc": "123456", "name_similarity": 0.95})
    
    # Tracking
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.String(100))
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            "id": self.id,
            "pos_item_num": self.pos_item_num,
            "pos_item_desc": self.pos_item_desc,
            "rfid_tag_id": self.rfid_tag_id,
            "rfid_rental_class_num": self.rfid_rental_class_num,
            "rfid_common_name": self.rfid_common_name,
            "correlation_type": self.correlation_type,
            "confidence_score": float(self.confidence_score) if self.confidence_score else 0,
            "match_criteria": self.match_criteria,
            "is_active": self.is_active,
        }


class POSInventoryDiscrepancy(db.Model):
    """Track discrepancies between POS sales and RFID inventory tracking."""
    __tablename__ = "pos_inventory_discrepancies"
    __table_args__ = (
        db.Index("ix_pos_discr_contract_no", "contract_no"),
        db.Index("ix_pos_discr_severity", "severity"),
        db.Index("ix_pos_discr_status", "status"),
        db.Index("ix_pos_discr_created", "created_at"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    contract_no = db.Column(db.String(50))
    pos_item_num = db.Column(db.String(50))
    rfid_tag_id = db.Column(db.String(255))
    rfid_rental_class_num = db.Column(db.String(255))
    
    discrepancy_type = db.Column(
        db.Enum(
            'missing_from_rfid',      # POS shows sale but RFID doesn't show item out
            'missing_from_pos',        # RFID shows item out but no POS record
            'quantity_mismatch',       # Different quantities between systems
            'status_mismatch',         # Item status conflicts
            'location_mismatch',       # Item location conflicts
            'return_not_recorded',     # POS shows return but RFID still out
            'double_booked'           # Item appears in multiple active contracts
        ),
        nullable=False
    )
    
    pos_quantity = db.Column(db.Integer)
    rfid_quantity = db.Column(db.Integer)
    pos_status = db.Column(db.String(50))
    rfid_status = db.Column(db.String(50))
    
    severity = db.Column(
        db.Enum('low', 'medium', 'high', 'critical'),
        nullable=False
    )
    
    description = db.Column(db.Text)
    resolution_notes = db.Column(db.Text)
    
    status = db.Column(
        db.Enum('open', 'investigating', 'resolved', 'false_positive'),
        nullable=False,
        default='open'
    )
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    detected_by = db.Column(db.String(100))  # 'system' or username
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            "id": self.id,
            "contract_no": self.contract_no,
            "discrepancy_type": self.discrepancy_type,
            "pos_quantity": self.pos_quantity,
            "rfid_quantity": self.rfid_quantity,
            "severity": self.severity,
            "status": self.status,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class POSAnalytics(db.Model):
    """Store calculated POS analytics and business intelligence metrics."""
    __tablename__ = "pos_analytics"
    __table_args__ = (
        db.Index("ix_pos_analytics_date", "calculation_date"),
        db.Index("ix_pos_analytics_metric", "metric_name"),
        UniqueConstraint("calculation_date", "metric_name", "dimension_value", 
                        name="uq_analytics_date_metric"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    calculation_date = db.Column(db.Date, nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_category = db.Column(db.String(50))  # 'revenue', 'inventory', 'customer', 'efficiency'
    dimension_type = db.Column(db.String(50))   # 'item', 'category', 'store', 'customer'
    dimension_value = db.Column(db.String(255))  # The specific item/category/store/customer
    
    # Metric values
    metric_value = db.Column(db.DECIMAL(15, 2))
    metric_count = db.Column(db.Integer)
    percentage_value = db.Column(db.DECIMAL(5, 2))
    
    # Comparison values
    previous_period_value = db.Column(db.DECIMAL(15, 2))
    year_over_year_value = db.Column(db.DECIMAL(15, 2))
    variance_percent = db.Column(db.DECIMAL(5, 2))
    
    # Metadata
    calculation_timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    data_quality_score = db.Column(db.DECIMAL(3, 2))  # 0.00 to 1.00
    
    def to_dict(self):
        return {
            "id": self.id,
            "date": self.calculation_date.isoformat() if self.calculation_date else None,
            "metric_name": self.metric_name,
            "dimension_value": self.dimension_value,
            "metric_value": float(self.metric_value) if self.metric_value else 0,
            "variance_percent": float(self.variance_percent) if self.variance_percent else 0,
        }


class POSImportLog(db.Model):
    """Track POS data import history and status."""
    __tablename__ = "pos_import_logs"
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    import_batch = db.Column(db.String(50), nullable=False, unique=True)
    import_type = db.Column(db.String(50))  # 'transactions', 'customers', 'items'
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    
    status = db.Column(
        db.Enum('pending', 'processing', 'completed', 'failed', 'partial'),
        nullable=False,
        default='pending'
    )
    
    records_processed = db.Column(db.Integer, default=0)
    records_imported = db.Column(db.Integer, default=0)
    records_failed = db.Column(db.Integer, default=0)
    records_skipped = db.Column(db.Integer, default=0)
    
    error_messages = db.Column(db.JSON)
    import_summary = db.Column(db.JSON)
    
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    imported_by = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            "id": self.id,
            "import_batch": self.import_batch,
            "import_type": self.import_type,
            "file_name": self.file_name,
            "status": self.status,
            "records_processed": self.records_processed,
            "records_imported": self.records_imported,
            "records_failed": self.records_failed,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
