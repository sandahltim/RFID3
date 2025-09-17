-- Complete equipPOS Schema - ALL 171 columns for Operations Database
-- Based on equipPOS9.08.25.csv header analysis

CREATE TABLE ops_equipment_complete (
    -- Primary identifier
    item_num VARCHAR(50) PRIMARY KEY COMMENT 'KEY field - normalized (remove .0)',
    pos_item_num VARCHAR(50) UNIQUE COMMENT 'Original KEY format from CSV',

    -- Basic item information (columns 1-16)
    name VARCHAR(500) COMMENT 'Name',
    loc VARCHAR(100) COMMENT 'LOC - Location code',
    qty INTEGER COMMENT 'QTY - Quantity',
    qyot INTEGER COMMENT 'QYOT - Quantity on order',
    sell_price DECIMAL(10,2) COMMENT 'SELL - Selling price',
    dep_price DECIMAL(10,2) COMMENT 'DEP - Deposit price',
    dmg_waiver DECIMAL(10,2) COMMENT 'DMG - Damage waiver',
    msg VARCHAR(255) COMMENT 'Msg - Message/notes',
    sdate DATE COMMENT 'SDATE - Service date',
    category VARCHAR(100) COMMENT 'Category',
    type_desc VARCHAR(100) COMMENT 'TYPE - Type description',
    tax_code VARCHAR(50) COMMENT 'TaxCode',
    inst VARCHAR(100) COMMENT 'INST - Installation notes',
    fuel VARCHAR(100) COMMENT 'FUEL - Fuel requirements',
    addt TEXT COMMENT 'ADDT - Additional details',

    -- Rental periods 1-10 (columns 17-26)
    per1 DECIMAL(10,2) COMMENT 'PER1 - Period 1',
    per2 DECIMAL(10,2) COMMENT 'PER2 - Period 2',
    per3 DECIMAL(10,2) COMMENT 'PER3 - Period 3',
    per4 DECIMAL(10,2) COMMENT 'PER4 - Period 4',
    per5 DECIMAL(10,2) COMMENT 'PER5 - Period 5',
    per6 DECIMAL(10,2) COMMENT 'PER6 - Period 6',
    per7 DECIMAL(10,2) COMMENT 'PER7 - Period 7',
    per8 DECIMAL(10,2) COMMENT 'PER8 - Period 8',
    per9 DECIMAL(10,2) COMMENT 'PER9 - Period 9',
    per10 DECIMAL(10,2) COMMENT 'PER10 - Period 10',

    -- Rental rates 1-10 (columns 27-36)
    rate1 DECIMAL(10,2) COMMENT 'RATE1 - Rate 1',
    rate2 DECIMAL(10,2) COMMENT 'RATE2 - Rate 2',
    rate3 DECIMAL(10,2) COMMENT 'RATE3 - Rate 3',
    rate4 DECIMAL(10,2) COMMENT 'RATE4 - Rate 4',
    rate5 DECIMAL(10,2) COMMENT 'RATE5 - Rate 5',
    rate6 DECIMAL(10,2) COMMENT 'RATE6 - Rate 6',
    rate7 DECIMAL(10,2) COMMENT 'RATE7 - Rate 7',
    rate8 DECIMAL(10,2) COMMENT 'RATE8 - Rate 8',
    rate9 DECIMAL(10,2) COMMENT 'RATE9 - Rate 9',
    rate10 DECIMAL(10,2) COMMENT 'RATE10 - Rate 10',

    -- Additional item details (columns 37-48)
    rcod VARCHAR(50) COMMENT 'RCOD - Rental code',
    subr VARCHAR(50) COMMENT 'SUBR - Subrent code',
    part_number VARCHAR(100) COMMENT 'PartNumber',
    num VARCHAR(50) COMMENT 'NUM - Number field',
    manf VARCHAR(100) COMMENT 'MANF - Manufacturer',
    modn VARCHAR(100) COMMENT 'MODN - Model number',
    dstn VARCHAR(100) COMMENT 'DSTN - Description',
    dstp VARCHAR(100) COMMENT 'DSTP - Description part',
    rmin INTEGER COMMENT 'RMIN - Reorder minimum',
    rmax INTEGER COMMENT 'RMAX - Reorder maximum',
    user_defined_1 VARCHAR(100) COMMENT 'UserDefined1',
    user_defined_2 VARCHAR(100) COMMENT 'UserDefined2',

    -- Meter and maintenance (columns 49-62)
    mtot DECIMAL(10,2) COMMENT 'MTOT - Meter total out',
    mtin DECIMAL(10,2) COMMENT 'MTIN - Meter total in',
    call VARCHAR(100) COMMENT 'CALL - Call information',
    resb VARCHAR(100) COMMENT 'RESB - Reserved begin',
    resd VARCHAR(100) COMMENT 'RESD - Reserved end',
    queb VARCHAR(100) COMMENT 'QUEB - Queue begin',
    qued VARCHAR(100) COMMENT 'QUED - Queue end',
    ssn VARCHAR(50) COMMENT 'SSN - Serial service number',
    cusn VARCHAR(100) COMMENT 'CUSN - Customer number',
    cntr VARCHAR(100) COMMENT 'CNTR - Counter',
    purd DATE COMMENT 'PURD - Purchase date',
    purp DECIMAL(10,2) COMMENT 'PURP - Purchase price',
    depm VARCHAR(50) COMMENT 'DEPM - Depreciation method',
    depr DECIMAL(10,2) COMMENT 'DEPR - Depreciation rate',

    -- Financial and accounting (columns 63-79)
    slvg DECIMAL(10,2) COMMENT 'SLVG - Salvage value',
    depa DECIMAL(10,2) COMMENT 'DEPA - Depreciation amount',
    depp DECIMAL(10,2) COMMENT 'DEPP - Depreciation percentage',
    curv DECIMAL(10,2) COMMENT 'CURV - Current value',
    sold BOOLEAN COMMENT 'SOLD - Sold flag',
    samt DECIMAL(10,2) COMMENT 'SAMT - Sale amount',
    inc1 DECIMAL(10,2) COMMENT 'INC1 - Income 1',
    inc2 DECIMAL(10,2) COMMENT 'INC2 - Income 2',
    inc3 DECIMAL(10,2) COMMENT 'INC3 - Income 3',
    repc1 DECIMAL(10,2) COMMENT 'REPC1 - Repair cost 1',
    repc2 DECIMAL(10,2) COMMENT 'REPC2 - Repair cost 2',
    tmot1 DECIMAL(10,2) COMMENT 'TMOT1 - Total meter out 1',
    tmot2 DECIMAL(10,2) COMMENT 'TMOT2 - Total meter out 2',
    tmot3 DECIMAL(10,2) COMMENT 'TMOT3 - Total meter out 3',
    hrot1 DECIMAL(10,2) COMMENT 'HROT1 - Hours out 1',
    hrot2 DECIMAL(10,2) COMMENT 'HROT2 - Hours out 2',
    hrot3 DECIMAL(10,2) COMMENT 'HROT3 - Hours out 3',

    -- Location and identification (columns 80-89)
    ldate DATE COMMENT 'LDATE - Last date',
    lookup VARCHAR(100) COMMENT 'LOOKUP - Lookup field',
    asset VARCHAR(100) COMMENT 'Asset',
    gl_account VARCHAR(50) COMMENT 'GLAccount - General ledger account',
    deprec_account VARCHAR(50) COMMENT 'DeprecAccount - Depreciation account',
    home_store VARCHAR(10) COMMENT 'HomeStore',
    current_store VARCHAR(10) COMMENT 'CurrentStore',
    group_field VARCHAR(100) COMMENT 'Group',
    location VARCHAR(100) COMMENT 'Location',
    serial_number VARCHAR(100) COMMENT 'SerialNumber',

    -- Status and configuration (columns 90-98)
    nontaxable BOOLEAN COMMENT 'Nontaxable',
    header VARCHAR(100) COMMENT 'Header',
    license VARCHAR(100) COMMENT 'License',
    case_qty INTEGER COMMENT 'CaseQty',
    item_percentage DECIMAL(5,2) COMMENT 'ItemPercentage',
    model_year VARCHAR(10) COMMENT 'ModelYear',
    retail_price DECIMAL(10,2) COMMENT 'RetailPrice',
    extra_depreciation DECIMAL(10,2) COMMENT 'ExtraDepreciation',
    inactive BOOLEAN COMMENT 'Inactive',

    -- Pricing and vendor (columns 99-113)
    extra_charges DECIMAL(10,2) COMMENT 'ExtraCharges',
    price_level_a DECIMAL(10,2) COMMENT 'PriceLevelA',
    price_level_b DECIMAL(10,2) COMMENT 'PriceLevelB',
    price_level_c DECIMAL(10,2) COMMENT 'PriceLevelC',
    non_discountable BOOLEAN COMMENT 'NonDiscountable',
    vendor_number_1 VARCHAR(50) COMMENT 'VendorNumber1',
    vendor_number_2 VARCHAR(50) COMMENT 'VendorNumber2',
    vendor_number_3 VARCHAR(50) COMMENT 'VendorNumber3',
    quantity_on_order INTEGER COMMENT 'QuantityOnOrder',
    sort_field VARCHAR(100) COMMENT 'Sort',
    no_print_on_contract BOOLEAN COMMENT 'NoPrintOnContract',
    markup_percentage DECIMAL(5,2) COMMENT 'MarkupPercentage',
    order_number_1 VARCHAR(50) COMMENT 'OrderNumber1',
    order_number_2 VARCHAR(50) COMMENT 'OrderNumber2',
    order_number_3 VARCHAR(50) COMMENT 'OrderNumber3',

    -- Maintenance and cleaning (columns 114-120)
    cleaning_delay INTEGER COMMENT 'CleaningDelay',
    require_cleaning BOOLEAN COMMENT 'RequireCleaning',
    maintenance_file VARCHAR(255) COMMENT 'MaintenanceFile',
    web_link VARCHAR(500) COMMENT 'WebLink',
    subrent_cost_mtd DECIMAL(10,2) COMMENT 'SubrentCostMTD',
    subrent_cost_ytd DECIMAL(10,2) COMMENT 'SubrentCostYTD',
    subrent_pending DECIMAL(10,2) COMMENT 'SubrentPending',

    -- Web and GPS (columns 121-126)
    hide_on_website BOOLEAN COMMENT 'HideOnWebsite',
    gps_unit_no VARCHAR(50) COMMENT 'GPSUnitNo',
    license_expire DATE COMMENT 'LicenseExpire',
    replacement_cost DECIMAL(10,2) COMMENT 'ReplacementCost',
    require_credit_card BOOLEAN COMMENT 'RequireCreditCard',
    warranty_date DATE COMMENT 'WarrantyDate',

    -- Vehicle specific (columns 127-133)
    vehicle_type VARCHAR(100) COMMENT 'VehicleType',
    vehicle_ein VARCHAR(100) COMMENT 'VehicleEIN',
    description_long TEXT COMMENT 'DescriptionLong',
    weight DECIMAL(10,3) COMMENT 'Weight',
    setup_time DECIMAL(10,2) COMMENT 'SetupTime',
    web_group VARCHAR(100) COMMENT 'WebGroup',
    department VARCHAR(100) COMMENT 'Department',

    -- Advanced features (columns 134-151)
    gl_income VARCHAR(50) COMMENT 'GLIncome',
    bulk_item BOOLEAN COMMENT 'BulkItem',
    gvwr DECIMAL(10,2) COMMENT 'GVWR - Gross vehicle weight rating',
    critical_level INTEGER COMMENT 'CriticalLevel',
    rental_case BOOLEAN COMMENT 'RentalCase',
    bought_used BOOLEAN COMMENT 'BoughtUsed',
    income_dmg_wvr DECIMAL(10,2) COMMENT 'IncomeDmgWvr',
    income_item_percent DECIMAL(5,2) COMMENT 'IncomeItemPercent',
    qty_count_difference INTEGER COMMENT 'QtyCountDifference',
    suppress_avail_check BOOLEAN COMMENT 'SuppressAvailCheck',
    fuel_tank_size DECIMAL(10,2) COMMENT 'FuelTankSize',
    no_transfers BOOLEAN COMMENT 'NoTransfers',
    commission_level DECIMAL(5,2) COMMENT 'CommissionLevel',
    barcode VARCHAR(100) COMMENT 'Barcode',
    style_1 VARCHAR(100) COMMENT 'Style1',
    style_2 VARCHAR(100) COMMENT 'Style2',
    style_3 VARCHAR(100) COMMENT 'Style3',
    desired_roi DECIMAL(5,2) COMMENT 'DesiredROI',

    -- Final fields (columns 152-171)
    cubic_size DECIMAL(10,3) COMMENT 'CubicSize',
    bulk_serialized_method VARCHAR(100) COMMENT 'BulkSerializedMethod',
    nonfulfillable BOOLEAN COMMENT 'Nonfulfillable',
    rate_engine_id VARCHAR(50) COMMENT 'RateEngineId',
    base_rate DECIMAL(10,2) COMMENT 'BaseRate',
    rate_engine_id_displayed VARCHAR(50) COMMENT 'RateEngineIdDisplayed',
    accounting_department_id VARCHAR(50) COMMENT 'AccountingDepartmentId',
    accounting_class_id VARCHAR(50) COMMENT 'AccountingClassId',
    item_manufacturer_id VARCHAR(50) COMMENT 'ItemManufacturerId',
    is_part_item BOOLEAN COMMENT 'IsPartItem',
    floor_price DECIMAL(10,2) COMMENT 'FloorPrice',
    fleet_id VARCHAR(50) COMMENT 'FleetID',
    height DECIMAL(10,2) COMMENT 'Height',
    width DECIMAL(10,2) COMMENT 'Width',
    length DECIMAL(10,2) COMMENT 'Length',
    suspense_exempt BOOLEAN COMMENT 'SuspenseExempt',
    sales_tax_code VARCHAR(50) COMMENT 'SalesTaxCode',
    created_date_time DATETIME COMMENT 'CreatedDateTime',
    updated_date_time DATETIME COMMENT 'UpdatedDateTime',
    replaced_meter_lifetime_accum DECIMAL(15,2) COMMENT 'ReplacedMeterLifetimeAccumulation',

    -- Operations database metadata
    last_sync_from_manager DATETIME COMMENT 'Last import from manager database',
    ops_created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ops_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Indexes for operations performance
    INDEX ix_ops_equip_category (category),
    INDEX ix_ops_equip_department (department),
    INDEX ix_ops_equip_home_store (home_store),
    INDEX ix_ops_equip_current_store (current_store),
    INDEX ix_ops_equip_inactive (inactive),
    INDEX ix_ops_equip_manufacturer (manf),
    INDEX ix_ops_equip_barcode (barcode),
    INDEX ix_ops_equip_serial (serial_number)
) ENGINE=InnoDB COMMENT='Complete equipPOS data (all 171 columns) for operations';

-- Field count verification
SELECT COUNT(*) as total_columns
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'ops_equipment_complete'
AND COLUMN_NAME NOT IN ('ops_created_at', 'ops_updated_at', 'last_sync_from_manager');
-- Should return 171 + item_num + pos_item_num = 173 operational columns