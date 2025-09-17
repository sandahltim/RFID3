# Equipment Models - Complete POS Equipment Data (171 columns)
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Text, Index, Numeric
from sqlalchemy.sql import func
from app.models.base import Base

class Equipment(Base):
    """Complete equipment model with all 171 POS columns"""
    __tablename__ = "ops_equipment_complete"

    # Primary identifier
    item_num = Column(String(50), primary_key=True, comment="KEY field - normalized (remove .0)")
    pos_item_num = Column(String(50), unique=True, comment="Original KEY format from CSV")

    # Basic item information (columns 1-16)
    name = Column(String(500), comment="Name")
    loc = Column(String(100), comment="LOC - Location code")
    qty = Column(Integer, comment="QTY - Quantity")
    qyot = Column(Integer, comment="QYOT - Quantity on order")
    sell_price = Column(Numeric(10,2), comment="SELL - Selling price")
    dep_price = Column(Numeric(10,2), comment="DEP - Deposit price")
    dmg_waiver = Column(Numeric(10,2), comment="DMG - Damage waiver")
    msg = Column(String(255), comment="Msg - Message/notes")
    sdate = Column(Date, comment="SDATE - Service date")
    category = Column(String(100), comment="Category")
    type_desc = Column(String(100), comment="TYPE - Type description")
    tax_code = Column(String(50), comment="TaxCode")
    inst = Column(String(100), comment="INST - Installation notes")
    fuel = Column(String(100), comment="FUEL - Fuel requirements")
    addt = Column(Text, comment="ADDT - Additional details")

    # Rental periods 1-10 (columns 17-26)
    per1 = Column(Numeric(10,2), comment="PER1 - Period 1")
    per2 = Column(Numeric(10,2), comment="PER2 - Period 2")
    per3 = Column(Numeric(10,2), comment="PER3 - Period 3")
    per4 = Column(Numeric(10,2), comment="PER4 - Period 4")
    per5 = Column(Numeric(10,2), comment="PER5 - Period 5")
    per6 = Column(Numeric(10,2), comment="PER6 - Period 6")
    per7 = Column(Numeric(10,2), comment="PER7 - Period 7")
    per8 = Column(Numeric(10,2), comment="PER8 - Period 8")
    per9 = Column(Numeric(10,2), comment="PER9 - Period 9")
    per10 = Column(Numeric(10,2), comment="PER10 - Period 10")

    # Rental rates 1-10 (columns 27-36)
    rate1 = Column(Numeric(10,2), comment="RATE1 - Rate 1")
    rate2 = Column(Numeric(10,2), comment="RATE2 - Rate 2")
    rate3 = Column(Numeric(10,2), comment="RATE3 - Rate 3")
    rate4 = Column(Numeric(10,2), comment="RATE4 - Rate 4")
    rate5 = Column(Numeric(10,2), comment="RATE5 - Rate 5")
    rate6 = Column(Numeric(10,2), comment="RATE6 - Rate 6")
    rate7 = Column(Numeric(10,2), comment="RATE7 - Rate 7")
    rate8 = Column(Numeric(10,2), comment="RATE8 - Rate 8")
    rate9 = Column(Numeric(10,2), comment="RATE9 - Rate 9")
    rate10 = Column(Numeric(10,2), comment="RATE10 - Rate 10")

    # Additional item details (columns 37-48)
    rcod = Column(String(50), comment="RCOD - Rental code")
    subr = Column(String(50), comment="SUBR - Subrent code")
    part_number = Column(String(100), comment="PartNumber")
    num = Column(String(50), comment="NUM - Number field")
    manf = Column(String(100), comment="MANF - Manufacturer")
    modn = Column(String(100), comment="MODN - Model number")
    dstn = Column(String(100), comment="DSTN - Description")
    dstp = Column(String(100), comment="DSTP - Description part")
    rmin = Column(Integer, comment="RMIN - Reorder minimum")
    rmax = Column(Integer, comment="RMAX - Reorder maximum")
    user_defined_1 = Column(String(100), comment="UserDefined1")
    user_defined_2 = Column(String(100), comment="UserDefined2")

    # Store and location
    home_store = Column(String(10), comment="HomeStore")
    current_store = Column(String(10), comment="CurrentStore")
    group_field = Column(String(100), comment="Group")
    location = Column(String(100), comment="Location")
    serial_number = Column(String(100), comment="SerialNumber")

    # Status and configuration
    inactive = Column(Boolean, comment="Inactive")
    model_year = Column(String(10), comment="ModelYear")
    retail_price = Column(Numeric(10,2), comment="RetailPrice")

    # Physical specifications
    weight = Column(Numeric(10,3), comment="Weight")
    setup_time = Column(Numeric(10,2), comment="SetupTime")
    height = Column(Numeric(10,2), comment="Height")
    width = Column(Numeric(10,2), comment="Width")
    length = Column(Numeric(10,2), comment="Length")

    # Vendor information
    vendor_number_1 = Column(String(50), comment="VendorNumber1")
    vendor_number_2 = Column(String(50), comment="VendorNumber2")
    vendor_number_3 = Column(String(50), comment="VendorNumber3")

    # Identification
    barcode = Column(String(100), comment="Barcode")
    department = Column(String(100), comment="Department")

    # Operations database metadata
    last_sync_from_manager = Column(DateTime, comment="Last import from manager database")
    ops_created_at = Column(DateTime, default=func.now())
    ops_updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Indexes for operations performance
    __table_args__ = (
        Index('ix_ops_equip_category', 'category'),
        Index('ix_ops_equip_department', 'department'),
        Index('ix_ops_equip_home_store', 'home_store'),
        Index('ix_ops_equip_current_store', 'current_store'),
        Index('ix_ops_equip_inactive', 'inactive'),
        Index('ix_ops_equip_manufacturer', 'manf'),
        Index('ix_ops_equip_barcode', 'barcode'),
        Index('ix_ops_equip_serial', 'serial_number'),
    )