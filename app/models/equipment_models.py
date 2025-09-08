"""
Equipment Models for RFID3 Inventory Management System
Created: 2025-09-02
Handles POS equipment rental and sales data import
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Date, Float, Numeric
from app import db

class EquipmentItem(db.Model):
    """Equipment rental/sales items from POS system"""
    __tablename__ = 'equipment_items'
    
    # Primary identification
    id = Column(Integer, primary_key=True)
    item_num = Column(String(50), unique=True, nullable=False, index=True)
    key = Column(String(100))
    name = Column(String(500))
    
    # Location and categorization
    location = Column(String(50))
    category = Column(String(200))
    department = Column(String(200))
    type_desc = Column(String(100))
    
    # Store information
    qty = Column(Integer, default=0)
    home_store = Column(String(10))
    current_store = Column(String(10))
    
    # Equipment details
    equipment_group = Column(String(200))
    manufacturer = Column(String(200))
    model_no = Column(String(200))
    serial_no = Column(String(200))
    part_no = Column(String(200))
    license_no = Column(String(200))
    model_year = Column(String(10))
    
    # Financial data - Turnover
    turnover_mtd = Column(Numeric(15, 2), default=0)
    turnover_ytd = Column(Numeric(15, 2), default=0)  
    turnover_ltd = Column(Numeric(15, 2), default=0)
    
    # Financial data - Repair costs
    repair_cost_mtd = Column(Numeric(15, 2), default=0)
    repair_cost_ltd = Column(Numeric(15, 2), default=0)
    
    # Pricing information
    sell_price = Column(Numeric(15, 2), default=0)
    retail_price = Column(Numeric(15, 2), default=0)
    deposit = Column(Numeric(15, 2), default=0)
    damage_waiver_percent = Column(Float, default=0)
    
    # Rental periods (days)
    period_1 = Column(Integer, default=0)
    period_2 = Column(Integer, default=0)
    period_3 = Column(Integer, default=0)
    period_4 = Column(Integer, default=0)
    period_5 = Column(Integer, default=0)
    period_6 = Column(Integer, default=0)
    period_7 = Column(Integer, default=0)
    period_8 = Column(Integer, default=0)
    period_9 = Column(Integer, default=0)
    period_10 = Column(Integer, default=0)
    
    # Rental rates
    rate_1 = Column(Numeric(10, 2), default=0)
    rate_2 = Column(Numeric(10, 2), default=0)
    rate_3 = Column(Numeric(10, 2), default=0)
    rate_4 = Column(Numeric(10, 2), default=0)
    rate_5 = Column(Numeric(10, 2), default=0)
    rate_6 = Column(Numeric(10, 2), default=0)
    rate_7 = Column(Numeric(10, 2), default=0)
    rate_8 = Column(Numeric(10, 2), default=0)
    rate_9 = Column(Numeric(10, 2), default=0)
    rate_10 = Column(Numeric(10, 2), default=0)
    
    # Inventory management
    reorder_min = Column(Integer, default=0)
    reorder_max = Column(Integer, default=0)
    user_defined_1 = Column(String(200))
    user_defined_2 = Column(String(200))
    
    # Meter readings
    meter_out = Column(Float, default=0)
    meter_in = Column(Float, default=0)
    
    # Depreciation
    depr_method = Column(String(50))
    depr = Column(Numeric(15, 2), default=0)
    
    # Status flags
    non_taxable = Column(Boolean, default=False)
    inactive = Column(Boolean, default=False)
    header_no = Column(String(50))
    
    # Vendor information
    last_purchase_date = Column(Date)
    last_purchase_price = Column(Numeric(15, 2), default=0)
    vendor_no_1 = Column(String(50))
    vendor_no_2 = Column(String(50)) 
    vendor_no_3 = Column(String(50))
    
    # Order information
    order_no_1 = Column(String(50))
    order_no_2 = Column(String(50))
    order_no_3 = Column(String(50))
    qty_on_order = Column(Integer, default=0)
    
    # Additional fields
    sort = Column(String(100))
    expiration_date = Column(Date)
    warranty_date = Column(Date)
    weight = Column(Float, default=0)
    setup_time = Column(Float, default=0)
    income = Column(Numeric(15, 2), default=0)
    
    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    import_batch_id = Column(String(50))

    def __repr__(self):
        return f'<EquipmentItem {self.item_num}: {self.name}>'

class EquipmentImportLog(db.Model):
    """Log equipment import operations"""
    __tablename__ = 'equipment_import_logs'
    
    id = Column(Integer, primary_key=True)
    batch_id = Column(String(50), nullable=False, index=True)
    filename = Column(String(500))
    import_type = Column(String(50))  # 'full', 'incremental'
    
    # Statistics
    records_processed = Column(Integer, default=0)
    records_imported = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Status
    status = Column(String(20))  # 'success', 'failed', 'partial'
    error_message = Column(Text)
    warnings = Column(Text)  # JSON array of warnings
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    def __repr__(self):
        return f'<EquipmentImportLog {self.batch_id}: {self.status}>'

class EquipmentCategory(db.Model):
    """Equipment category master data for analytics"""
    __tablename__ = 'equipment_categories'
    
    id = Column(Integer, primary_key=True)
    category_name = Column(String(200), unique=True, nullable=False)
    department = Column(String(200))
    category_type = Column(String(50))  # 'rental', 'sales', 'service'
    
    # Analytics
    total_items = Column(Integer, default=0)
    active_items = Column(Integer, default=0)
    total_value = Column(Numeric(15, 2), default=0)
    
    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EquipmentCategory {self.category_name}>'