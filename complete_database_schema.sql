-- ================================================================
-- RFID3 Complete Database Schema Generation
-- Generated from: table info.xlsx
-- Purpose: Create complete schemas for all POS data tables
-- ================================================================

SET FOREIGN_KEY_CHECKS = 0;


-- ================================================================
-- TRANSITEMS TABLE
-- Total columns: 46
-- ================================================================

-- TRANSITEMS Table Schema (46 total columns)
CREATE TABLE IF NOT EXISTS pos_transitems (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Primary key',
    pos_transitems VARCHAR(255) COMMENT 'POS transitems  ',    cntr INT COMMENT 'CNTR',    subf VARCHAR(255) COMMENT 'SUBF',    item VARCHAR(255) COMMENT 'ITEM',    qty INT COMMENT 'QTY',    hrsc VARCHAR(255) COMMENT 'HRSC',    ddt VARCHAR(255) COMMENT 'DDT',    dtm TIME COMMENT 'DTM',    txty VARCHAR(255) COMMENT 'TXTY',    pric VARCHAR(255) COMMENT 'PRIC',    desc VARCHAR(255) COMMENT 'Desc',    comments VARCHAR(500) COMMENT 'Comments',    dmgwvr DECIMAL(12,2) COMMENT 'DmgWvr',    itempercentage DECIMAL(12,2) COMMENT 'ItemPercentage',    discountpercent DECIMAL(12,2) COMMENT 'DiscountPercent',    nontaxable DECIMAL(12,2) COMMENT 'Nontaxable',    nondiscount INT COMMENT 'Nondiscount',    lettersent VARCHAR(255) COMMENT 'LetterSent',    sort VARCHAR(255) COMMENT 'Sort',    discountamount DECIMAL(12,2) COMMENT 'DiscountAmount',    dailyamount DECIMAL(12,2) COMMENT 'DailyAmount',    weeklyamount DECIMAL(12,2) COMMENT 'WeeklyAmount',    monthlyamount DECIMAL(12,2) COMMENT 'MonthlyAmount',    minimumamount DECIMAL(12,2) COMMENT 'MinimumAmount',    readingout VARCHAR(255) COMMENT 'ReadingOut',    readingin VARCHAR(255) COMMENT 'ReadingIn',    rainhours INT COMMENT 'RainHours',    lastmodified DATE COMMENT 'LastModified',    retailprice DECIMAL(12,2) COMMENT 'RetailPrice',    kitfield VARCHAR(255) COMMENT 'KitField',    confirmeddate BOOLEAN COMMENT 'ConfirmedDate',    subrentquantity DECIMAL(12,2) COMMENT 'SubrentQuantity',    substatus VARCHAR(255) COMMENT 'Substatus',    contractlink VARCHAR(500) COMMENT 'ContractLink',    linenumber INT COMMENT 'LineNumber',    rateengineid DECIMAL(12,2) COMMENT 'RateEngineId',    baserate DECIMAL(12,2) COMMENT 'BaseRate',    logisticsout VARCHAR(255) COMMENT 'LogisticsOUT',    logisticsin VARCHAR(255) COMMENT 'LogisticsIN',    archived BOOLEAN COMMENT 'Archived',    outdate DATE COMMENT 'OutDate',    transrelated VARCHAR(255) COMMENT 'TransRelated',    specialratetypeid DECIMAL(12,2) COMMENT 'SpecialRateTypeId',    taxamount DECIMAL(12,2) COMMENT 'TaxAmount',    monthlyratedate DECIMAL(12,2) COMMENT 'MonthlyRateDate',    id VARCHAR(255) COMMENT 'Id',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update time'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='transitems data from POS system';


-- ================================================================
-- TRANSACTIONS TABLE
-- Total columns: 120
-- ================================================================

-- TRANSACTIONS Table Schema (120 total columns)
CREATE TABLE IF NOT EXISTS pos_transactions (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Primary key',
    pos_transactions VARCHAR(255) COMMENT 'POS transactions',    cntr INT COMMENT 'CNTR',    date DATE COMMENT 'DATE',    time TIME COMMENT 'TIME',    opid VARCHAR(255) COMMENT 'OPID',    pymt VARCHAR(255) COMMENT 'PYMT',    dpmt VARCHAR(255) COMMENT 'DPMT',    stat VARCHAR(255) COMMENT 'STAT',    cusn VARCHAR(255) COMMENT 'CUSN',    rdis DECIMAL(12,2) COMMENT 'RDIS',    dmg DECIMAL(12,2) COMMENT 'DMG',    othr DECIMAL(12,2) COMMENT 'OTHR',    rent DECIMAL(12,2) COMMENT 'RENT',    sale DECIMAL(12,2) COMMENT 'SALE',    tax DECIMAL(12,2) COMMENT 'TAX',    totl DECIMAL(12,2) COMMENT 'TOTL',    paid DECIMAL(12,2) COMMENT 'PAID',    depp DECIMAL(12,2) COMMENT 'DEPP',    depr DECIMAL(12,2) COMMENT 'DEPR',    ckn VARCHAR(255) COMMENT 'CKN',    dckn VARCHAR(255) COMMENT 'DCKN',    jobn VARCHAR(255) COMMENT 'JOBN',    jbpo VARCHAR(255) COMMENT 'JBPO',    jbid VARCHAR(255) COMMENT 'JBID',    taxcode DECIMAL(12,2) COMMENT 'TaxCode',    str VARCHAR(255) COMMENT 'STR',    sdis DECIMAL(12,2) COMMENT 'SDIS',    cmdt VARCHAR(255) COMMENT 'CMDT',    cldt VARCHAR(255) COMMENT 'CLDT',    cont VARCHAR(255) COMMENT 'CONT',    day INT COMMENT 'DAY',    delvr VARCHAR(255) COMMENT 'Delvr',    completed BOOLEAN COMMENT 'Completed',    billed BOOLEAN COMMENT 'Billed',    deliveryconfirmed BOOLEAN COMMENT 'DeliveryConfirmed',    deliverydate BOOLEAN COMMENT 'DeliveryDate',    deliverytrip INT COMMENT 'DeliveryTrip',    pickup BOOLEAN COMMENT 'Pickup',    pickupconfirmed BOOLEAN COMMENT 'PickupConfirmed',    pickupdate BOOLEAN COMMENT 'PickupDate',    pickuptrip INT COMMENT 'PickupTrip',    contact VARCHAR(255) COMMENT 'Contact',    contactphone VARCHAR(255) COMMENT 'ContactPhone',    sameaddress BOOLEAN COMMENT 'SameAddress',    deliveryaddress BOOLEAN COMMENT 'DeliveryAddress',    deliverycity BOOLEAN COMMENT 'DeliveryCity',    deliveryzip BOOLEAN COMMENT 'DeliveryZip',    cardswipe VARCHAR(255) COMMENT 'CardSwipe',    nontaxable DECIMAL(12,2) COMMENT 'Nontaxable',    discount INT COMMENT 'Discount',    salesman DECIMAL(12,2) COMMENT 'Salesman',    pickedupby VARCHAR(255) COMMENT 'PickedUpBy',    pickedupdlno VARCHAR(255) COMMENT 'PickedUpDlNo',    itempercentage DECIMAL(12,2) COMMENT 'ItemPercentage',    autolicense VARCHAR(255) COMMENT 'AutoLicense',    damagewaiverexempt DECIMAL(12,2) COMMENT 'DamageWaiverExempt',    itempercentageexempt DECIMAL(12,2) COMMENT 'ItemPercentageExempt',    pricelevel DECIMAL(12,2) COMMENT 'PriceLevel',    modification VARCHAR(255) COMMENT 'Modification',    eventenddate DATE COMMENT 'EventEndDate',    deliverytrucknumber INT COMMENT 'DeliveryTruckNumber',    pickuptrucknumber INT COMMENT 'PickupTruckNumber',    jobsite VARCHAR(255) COMMENT 'JobSite',    delivertocompany VARCHAR(255) COMMENT 'DeliverToCompany',    deliverynotes BOOLEAN COMMENT 'DeliveryNotes',    verifiedaddress BOOLEAN COMMENT 'VerifiedAddress',    deliverysetuptime BOOLEAN COMMENT 'DeliverySetupTime',    pickuploadtime BOOLEAN COMMENT 'PickupLoadTime',    transactiontype VARCHAR(255) COMMENT 'TransactionType',    operation INT COMMENT 'Operation',    deliveryroute BOOLEAN COMMENT 'DeliveryRoute',    pickuproute BOOLEAN COMMENT 'PickupRoute',    deliverydatepromised BOOLEAN COMMENT 'DeliveryDatePromised',    pickupdatepromised BOOLEAN COMMENT 'PickupDatePromised',    lastletter VARCHAR(255) COMMENT 'LastLetter',    letterdate DATE COMMENT 'LetterDate',    postedcash VARCHAR(255) COMMENT 'PostedCash',    postedaccrual VARCHAR(255) COMMENT 'PostedAccrual',    currencynumber INT COMMENT 'CurrencyNumber',    exchangerate DECIMAL(12,2) COMMENT 'ExchangeRate',    discounttable INT COMMENT 'DiscountTable',    orderedby VARCHAR(255) COMMENT 'OrderedBy',    deliverycrewcount INT COMMENT 'DeliveryCrewCount',    pickupcrewcount INT COMMENT 'PickupCrewCount',    deliverysetuptimecomputed BOOLEAN COMMENT 'DeliverySetupTimeComputed',    masterbill VARCHAR(255) COMMENT 'MasterBill',    serviceseq INT COMMENT 'ServiceSeq',    notes VARCHAR(500) COMMENT 'Notes',    parentcontract DECIMAL(12,2) COMMENT 'ParentContract',    pickupsameaddress BOOLEAN COMMENT 'PickupSameAddress',    pickupaddress BOOLEAN COMMENT 'PickupAddress',    pickupcity BOOLEAN COMMENT 'PickupCity',    pickupzip BOOLEAN COMMENT 'PickupZip',    operatorcreated INT COMMENT 'OperatorCreated',    operatorassigned INT COMMENT 'OperatorAssigned',    pickupverifiedaddress BOOLEAN COMMENT 'PickupVerifiedAddress',    pickupfromcompany BOOLEAN COMMENT 'PickupFromCompany',    createddate DATE COMMENT 'CreatedDate',    status VARCHAR(255) COMMENT 'Status',    secondarystatus VARCHAR(255) COMMENT 'SecondaryStatus',    cancelled BOOLEAN COMMENT 'Cancelled',    reviewbilling BOOLEAN COMMENT 'ReviewBilling',    rentdiscount DECIMAL(12,2) COMMENT 'RentDiscount',    salediscount DECIMAL(12,2) COMMENT 'SaleDiscount',    rateengineid DECIMAL(12,2) COMMENT 'RateEngineId',    desireddeposit DECIMAL(12,2) COMMENT 'DesiredDeposit',    pickupcontact BOOLEAN COMMENT 'PickupContact',    pickupcontactphone BOOLEAN COMMENT 'PickupContactPhone',    pickupnotes BOOLEAN COMMENT 'PickupNotes',    archived BOOLEAN COMMENT 'Archived',    accountinglink INT COMMENT 'AccountingLink',    revenuedate DECIMAL(12,2) COMMENT 'RevenueDate',    classid VARCHAR(255) COMMENT 'ClassID',    currentmodifyopno DECIMAL(12,2) COMMENT 'CurrentModifyOpNo',    damagewaivertaxamount DECIMAL(12,2) COMMENT 'DamageWaiverTaxAmount',    itempercentagetaxamount DECIMAL(12,2) COMMENT 'ItemPercentageTaxAmount',    othertaxamount DECIMAL(12,2) COMMENT 'OtherTaxAmount',    accountingtransactionid INT COMMENT 'AccountingTransactionId',    invoicenumber INT COMMENT 'InvoiceNumber',    updateddatetime DATETIME COMMENT 'UpdatedDateTime',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update time'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='transactions data from POS system';


-- ================================================================
-- EQUIPMENT TABLE
-- Total columns: 172
-- ================================================================

-- EQUIPMENT Table Schema (172 total columns)
CREATE TABLE IF NOT EXISTS equipment_items (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Primary key',
    pos_equipment VARCHAR(255) COMMENT 'POS Equipment',    loc VARCHAR(255) COMMENT 'LOC',    qyot INT COMMENT 'QYOT',    sell DECIMAL(12,2) COMMENT 'SELL',    dep VARCHAR(255) COMMENT 'DEP',    dmg DECIMAL(12,2) COMMENT 'DMG',    msg VARCHAR(255) COMMENT 'Msg',    sdate DATE COMMENT 'SDATE',    type VARCHAR(255) COMMENT 'TYPE',    taxcode DECIMAL(12,2) COMMENT 'TaxCode',    inst VARCHAR(255) COMMENT 'INST',    fuel VARCHAR(255) COMMENT 'FUEL',    addt VARCHAR(500) COMMENT 'ADDT',    per1 INT COMMENT 'PER1',    per2 INT COMMENT 'PER2',    per3 INT COMMENT 'PER3',    per4 INT COMMENT 'PER4',    per5 INT COMMENT 'PER5',    per6 INT COMMENT 'PER6',    per7 INT COMMENT 'PER7',    per8 INT COMMENT 'PER8',    per9 INT COMMENT 'PER9',    per10 INT COMMENT 'PER10',    rate1 DECIMAL(12,2) COMMENT 'RATE1',    rate2 DECIMAL(12,2) COMMENT 'RATE2',    rate3 DECIMAL(12,2) COMMENT 'RATE3',    rate4 DECIMAL(12,2) COMMENT 'RATE4',    rate5 DECIMAL(12,2) COMMENT 'RATE5',    rate6 DECIMAL(12,2) COMMENT 'RATE6',    rate7 DECIMAL(12,2) COMMENT 'RATE7',    rate8 DECIMAL(12,2) COMMENT 'RATE8',    rate9 DECIMAL(12,2) COMMENT 'RATE9',    rate10 DECIMAL(12,2) COMMENT 'RATE10',    rcod VARCHAR(255) COMMENT 'RCOD',    subr VARCHAR(255) COMMENT 'SUBR',    partnumber INT COMMENT 'PartNumber',    num INT COMMENT 'NUM',    manf VARCHAR(255) COMMENT 'MANF',    modn VARCHAR(255) COMMENT 'MODN',    dstn VARCHAR(500) COMMENT 'DSTN',    dstp VARCHAR(500) COMMENT 'DSTP',    rmin INT COMMENT 'RMIN',    rmax INT COMMENT 'RMAX',    userdefined1 VARCHAR(255) COMMENT 'UserDefined1',    userdefined2 VARCHAR(255) COMMENT 'UserDefined2',    mtot VARCHAR(255) COMMENT 'MTOT',    mtin VARCHAR(255) COMMENT 'MTIN',    call VARCHAR(255) COMMENT 'CALL',    resb VARCHAR(255) COMMENT 'RESB',    resd VARCHAR(255) COMMENT 'RESD',    queb VARCHAR(255) COMMENT 'QUEB',    qued VARCHAR(255) COMMENT 'QUED',    ssn VARCHAR(255) COMMENT 'SSN',    cusn VARCHAR(255) COMMENT 'CUSN',    cntr INT COMMENT 'CNTR',    purd VARCHAR(255) COMMENT 'PURD',    purp DECIMAL(12,2) COMMENT 'PURP',    depm VARCHAR(255) COMMENT 'DEPM',    slvg DECIMAL(12,2) COMMENT 'SLVG',    depa VARCHAR(255) COMMENT 'DEPA',    depp DECIMAL(12,2) COMMENT 'DEPP',    curv VARCHAR(255) COMMENT 'CURV',    sold VARCHAR(255) COMMENT 'SOLD',    samt VARCHAR(255) COMMENT 'SAMT',    inc1 VARCHAR(255) COMMENT 'INC1',    inc2 VARCHAR(255) COMMENT 'INC2',    inc3 VARCHAR(255) COMMENT 'INC3',    repc1 VARCHAR(255) COMMENT 'REPC1',    repc2 VARCHAR(255) COMMENT 'REPC2',    tmot1 VARCHAR(255) COMMENT 'TMOT1',    tmot2 VARCHAR(255) COMMENT 'TMOT2',    tmot3 VARCHAR(255) COMMENT 'TMOT3',    hrot1 VARCHAR(255) COMMENT 'HROT1',    hrot2 VARCHAR(255) COMMENT 'HROT2',    hrot3 VARCHAR(255) COMMENT 'HROT3',    ldate DATE COMMENT 'LDATE',    lookup VARCHAR(255) COMMENT 'LOOKUP',    asset VARCHAR(255) COMMENT 'Asset',    glaccount INT COMMENT 'GLAccount',    deprecaccount DECIMAL(12,2) COMMENT 'DeprecAccount',    homestore VARCHAR(255) COMMENT 'HomeStore',    currentstore DECIMAL(12,2) COMMENT 'CurrentStore',    group VARCHAR(255) COMMENT 'Group',    serialnumber INT COMMENT 'SerialNumber',    nontaxable DECIMAL(12,2) COMMENT 'Nontaxable',    header BOOLEAN COMMENT 'Header',    license VARCHAR(255) COMMENT 'License',    caseqty INT COMMENT 'CaseQty',    itempercentage DECIMAL(12,2) COMMENT 'ItemPercentage',    modelyear INT COMMENT 'ModelYear',    retailprice DECIMAL(12,2) COMMENT 'RetailPrice',    extradepreciation DECIMAL(12,2) COMMENT 'ExtraDepreciation',    extracharges VARCHAR(255) COMMENT 'ExtraCharges',    pricelevela DECIMAL(12,2) COMMENT 'PriceLevelA',    pricelevelb DECIMAL(12,2) COMMENT 'PriceLevelB',    pricelevelc DECIMAL(12,2) COMMENT 'PriceLevelC',    nondiscountable INT COMMENT 'NonDiscountable',    vendornumber1 INT COMMENT 'VendorNumber1',    vendornumber2 INT COMMENT 'VendorNumber2',    vendornumber3 INT COMMENT 'VendorNumber3',    quantityonorder VARCHAR(255) COMMENT 'QuantityOnOrder',    noprintoncontract VARCHAR(255) COMMENT 'NoPrintOnContract',    markuppercentage DECIMAL(12,2) COMMENT 'MarkupPercentage',    ordernumber1 INT COMMENT 'OrderNumber1',    ordernumber2 INT COMMENT 'OrderNumber2',    ordernumber3 INT COMMENT 'OrderNumber3',    cleaningdelay VARCHAR(255) COMMENT 'CleaningDelay',    requirecleaning BOOLEAN COMMENT 'RequireCleaning',    maintenancefile VARCHAR(255) COMMENT 'MaintenanceFile',    weblink VARCHAR(500) COMMENT 'WebLink',    subrentcostmtd DECIMAL(12,2) COMMENT 'SubrentCostMTD',    subrentcostytd DECIMAL(12,2) COMMENT 'SubrentCostYTD',    subrentpending DECIMAL(12,2) COMMENT 'SubrentPending',    hideonwebsite BOOLEAN COMMENT 'HideOnWebsite',    gpsunitno VARCHAR(255) COMMENT 'GPSUnitNo',    licenseexpire DATE COMMENT 'LicenseExpire',    replacementcost DECIMAL(12,2) COMMENT 'ReplacementCost',    requirecreditcard BOOLEAN COMMENT 'RequireCreditCard',    warrantydate DATE COMMENT 'WarrantyDate',    vehicletype VARCHAR(255) COMMENT 'VehicleType',    vehicleein VARCHAR(255) COMMENT 'VehicleEIN',    descriptionlong TEXT COMMENT 'DescriptionLong',    setuptime TIME COMMENT 'SetupTime',    webgroup VARCHAR(255) COMMENT 'WebGroup',    glincome DECIMAL(12,2) COMMENT 'GLIncome',    bulkitem BOOLEAN COMMENT 'BulkItem',    gvwr INT COMMENT 'GVWR',    criticallevel INT COMMENT 'CriticalLevel',    rentalcase DECIMAL(12,2) COMMENT 'RentalCase',    boughtused BOOLEAN COMMENT 'BoughtUsed',    incomedmgwvr DECIMAL(12,2) COMMENT 'IncomeDmgWvr',    incomeitempercent DECIMAL(12,2) COMMENT 'IncomeItemPercent',    qtycountdifference INT COMMENT 'QtyCountDifference',    suppressavailcheck BOOLEAN COMMENT 'SuppressAvailCheck',    fueltanksize VARCHAR(255) COMMENT 'FuelTankSize',    notransfers VARCHAR(255) COMMENT 'NoTransfers',    commissionlevel DECIMAL(12,2) COMMENT 'CommissionLevel',    barcode VARCHAR(255) COMMENT 'Barcode',    style1 VARCHAR(255) COMMENT 'Style1',    style2 VARCHAR(255) COMMENT 'Style2',    style3 VARCHAR(255) COMMENT 'Style3',    desiredroi DECIMAL(12,2) COMMENT 'DesiredROI',    cubicsize INT COMMENT 'CubicSize',    bulkserializedmethod BOOLEAN COMMENT 'BulkSerializedMethod',    nonfulfillable BOOLEAN COMMENT 'Nonfulfillable',    rateengineid DECIMAL(12,2) COMMENT 'RateEngineId',    baserate DECIMAL(12,2) COMMENT 'BaseRate',    rateengineiddisplayed DECIMAL(12,2) COMMENT 'RateEngineIdDisplayed',    accountingdepartmentid INT COMMENT 'AccountingDepartmentId',    accountingclassid INT COMMENT 'AccountingClassId',    itemmanufacturerid VARCHAR(255) COMMENT 'ItemManufacturerId',    ispartitem VARCHAR(255) COMMENT 'IsPartItem',    floorprice DECIMAL(12,2) COMMENT 'FloorPrice',    fleetid VARCHAR(255) COMMENT 'FleetID',    height VARCHAR(255) COMMENT 'Height',    width VARCHAR(255) COMMENT 'Width',    length VARCHAR(255) COMMENT 'Length',    suspenseexempt BOOLEAN COMMENT 'SuspenseExempt',    salestaxcode DECIMAL(12,2) COMMENT 'SalesTaxCode',    createddatetime DATETIME COMMENT 'CreatedDateTime',    updateddatetime DATETIME COMMENT 'UpdatedDateTime',    replacedmeterlifetimeaccumulation TIME COMMENT 'ReplacedMeterLifetimeAccumulation',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update time'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='equipment data from POS system';


-- ================================================================
-- CUSTOMER TABLE
-- Total columns: 109
-- ================================================================

-- CUSTOMER Table Schema (109 total columns)
CREATE TABLE IF NOT EXISTS pos_customer (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Primary key',
    pos_customer VARCHAR(255) COMMENT 'POS customer',    key VARCHAR(255) COMMENT 'KEY',    name VARCHAR(255) COMMENT 'NAME',    address VARCHAR(500) COMMENT 'Address',    address2 VARCHAR(500) COMMENT 'Address2',    city VARCHAR(255) COMMENT 'CITY',    zip VARCHAR(255) COMMENT 'ZIP',    zip4 VARCHAR(255) COMMENT 'ZIP4',    driverslicense VARCHAR(255) COMMENT 'DriversLicense',    birthdate DATE COMMENT 'Birthdate',    employer VARCHAR(255) COMMENT 'Employer',    autolicense VARCHAR(255) COMMENT 'AutoLicense',    autostate VARCHAR(255) COMMENT 'AutoState',    phone VARCHAR(255) COMMENT 'Phone',    work VARCHAR(255) COMMENT 'WORK',    mobile VARCHAR(255) COMMENT 'MOBILE',    fax VARCHAR(255) COMMENT 'FAX',    pager VARCHAR(255) COMMENT 'PAGER',    cnum INT COMMENT 'CNUM',    opendate DATE COMMENT 'OpenDate',    lastactive VARCHAR(255) COMMENT 'LastActive',    lastcontract VARCHAR(255) COMMENT 'LastContract',    creditlimit DECIMAL(12,2) COMMENT 'CreditLimit',    status VARCHAR(255) COMMENT 'Status',    restrictions VARCHAR(255) COMMENT 'Restrictions',    creditcard VARCHAR(255) COMMENT 'CreditCard',    otherid VARCHAR(255) COMMENT 'OTHERID',    incomeyear DECIMAL(12,2) COMMENT 'IncomeYear',    incomelife DECIMAL(12,2) COMMENT 'IncomeLife',    incomelastyear DECIMAL(12,2) COMMENT 'IncomeLastYear',    numbercontracts INT COMMENT 'NumberContracts',    taxcode DECIMAL(12,2) COMMENT 'TaxCode',    discount INT COMMENT 'Discount',    type VARCHAR(255) COMMENT 'Type',    message VARCHAR(500) COMMENT 'Message',    qtyout INT COMMENT 'QtyOut',    forceinfo BOOLEAN COMMENT 'ForceInfo',    forcepo BOOLEAN COMMENT 'ForcePO',    forcejobid BOOLEAN COMMENT 'ForceJobId',    deletedmgwvr DECIMAL(12,2) COMMENT 'DeleteDmgWvr',    deletefinancecharge DECIMAL(12,2) COMMENT 'DeleteFinanceCharge',    deletestatement BOOLEAN COMMENT 'DeleteStatement',    lastpayamount DECIMAL(12,2) COMMENT 'LastPayAmount',    lastpaydate DATE COMMENT 'LastPayDate',    highbalance DECIMAL(12,2) COMMENT 'HighBalance',    currentbalance DECIMAL(12,2) COMMENT 'CurrentBalance',    email VARCHAR(255) COMMENT 'Email',    salesman DECIMAL(12,2) COMMENT 'Salesman',    deleteitempercentage DECIMAL(12,2) COMMENT 'DeleteItemPercentage',    forcepickedup BOOLEAN COMMENT 'ForcePickedUp',    onlyallowauthorized VARCHAR(255) COMMENT 'OnlyAllowAuthorized',    dlexpire DATE COMMENT 'DLExpire',    billcontact VARCHAR(255) COMMENT 'BillContact',    billphone VARCHAR(255) COMMENT 'BillPhone',    billaddress1 VARCHAR(500) COMMENT 'BillAddress1',    billaddress2 VARCHAR(500) COMMENT 'BillAddress2',    billcitystate VARCHAR(255) COMMENT 'BillCityState',    billzip VARCHAR(255) COMMENT 'BillZip',    billzip4 VARCHAR(255) COMMENT 'BillZip4',    taxid DECIMAL(12,2) COMMENT 'TaxId',    taxexemptnumber DECIMAL(12,2) COMMENT 'TaxExemptNumber',    taxexemptexpire DECIMAL(12,2) COMMENT 'TaxExemptExpire',    insurancenumber INT COMMENT 'InsuranceNumber',    insuranceexpire DATE COMMENT 'InsuranceExpire',    statementformat VARCHAR(255) COMMENT 'StatementFormat',    statementprintto VARCHAR(255) COMMENT 'StatementPrintTo',    terms VARCHAR(255) COMMENT 'Terms',    financechargedays DECIMAL(12,2) COMMENT 'FinanceChargeDays',    socialsecurity VARCHAR(255) COMMENT 'SocialSecurity',    federalid VARCHAR(255) COMMENT 'FederalId',    userdefined1 VARCHAR(255) COMMENT 'UserDefined1',    userdefined2 VARCHAR(255) COMMENT 'UserDefined2',    pricelevel DECIMAL(12,2) COMMENT 'PriceLevel',    contractformat VARCHAR(255) COMMENT 'ContractFormat',    agedate DATE COMMENT 'AgeDate',    noupdatecreditcard DATE COMMENT 'NoUpdateCreditCard',    heardaboutus VARCHAR(255) COMMENT 'HeardAboutUs',    contractprintto VARCHAR(255) COMMENT 'ContractPrintTo',    noemail VARCHAR(255) COMMENT 'NoEmail',    contractorlicense VARCHAR(255) COMMENT 'ContractorLicense',    contractorexpire DATE COMMENT 'ContractorExpire',    websiteportal VARCHAR(255) COMMENT 'WebsitePortal',    monthtomonth VARCHAR(255) COMMENT 'MonthToMonth',    pricingtype VARCHAR(255) COMMENT 'PricingType',    group VARCHAR(255) COMMENT 'Group',    customerprintout VARCHAR(255) COMMENT 'CustomerPrintOut',    language VARCHAR(255) COMMENT 'Language',    commissionlevel DECIMAL(12,2) COMMENT 'CommissionLevel',    nontaxable DECIMAL(12,2) COMMENT 'Nontaxable',    operatorassigned INT COMMENT 'OperatorAssigned',    loyaltylevelid INT COMMENT 'LoyaltyLevelId',    rateengineid DECIMAL(12,2) COMMENT 'RateEngineId',    reviewbilling BOOLEAN COMMENT 'ReviewBilling',    apilink VARCHAR(500) COMMENT 'APILink',    changedby VARCHAR(255) COMMENT 'ChangedBy',    datechanged DATE COMMENT 'DateChanged',    namealias VARCHAR(255) COMMENT 'NameAlias',    accountingcustomerid INT COMMENT 'AccountingCustomerId',    damagewaiver DECIMAL(12,2) COMMENT 'DamageWaiver',    currencynumber INT COMMENT 'CurrencyNumber',    suspense VARCHAR(255) COMMENT 'Suspense',    countrycode INT COMMENT 'CountryCode',    billcountrycode INT COMMENT 'BillCountryCode',    directpayrefno VARCHAR(255) COMMENT 'DirectPayRefNo',    salestaxcode DECIMAL(12,2) COMMENT 'SalesTaxCode',    salestaxclass DECIMAL(12,2) COMMENT 'SalesTaxClass',    entitytype VARCHAR(255) COMMENT 'EntityType',    firstname VARCHAR(255) COMMENT 'FirstName',    lastname VARCHAR(255) COMMENT 'LastName',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update time'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='customer data from POS system';


-- ================================================================
-- SCORECARD TABLE
-- Total columns: 23
-- ================================================================

-- SCORECARD Table Schema (23 total columns)
CREATE TABLE IF NOT EXISTS pos_scorecard (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Primary key',
    scorecard VARCHAR(255) COMMENT 'scorecard',    column_292 VARCHAR(255) COMMENT 'no title',    group_name VARCHAR(255) COMMENT 'Group Name',    status VARCHAR(255) COMMENT 'Status',    title VARCHAR(255) COMMENT 'Title',    description VARCHAR(500) COMMENT 'Description',    owner VARCHAR(255) COMMENT 'Owner',    goal VARCHAR(255) COMMENT 'Goal',    average VARCHAR(255) COMMENT 'Average',    total VARCHAR(255) COMMENT 'Total',    sep_15_sep_21 VARCHAR(255) COMMENT 'Sep 15 - Sep 21',    sep_08_sep_14 VARCHAR(255) COMMENT 'Sep 08 - Sep 14',    sep_01_sep_07 VARCHAR(255) COMMENT 'Sep 01 - Sep 07',    aug_25_aug_31 VARCHAR(255) COMMENT 'Aug 25 - Aug 31',    aug_18_aug_24 VARCHAR(255) COMMENT 'Aug 18 - Aug 24',    aug_11_aug_17 VARCHAR(255) COMMENT 'Aug 11 - Aug 17',    aug_04_aug_10 VARCHAR(255) COMMENT 'Aug 04 - Aug 10',    jul_28_aug_03 VARCHAR(255) COMMENT 'Jul 28 - Aug 03',    jul_21_jul_27 VARCHAR(255) COMMENT 'Jul 21 - Jul 27',    jul_14_jul_20 VARCHAR(255) COMMENT 'Jul 14 - Jul 20',    jul_07_jul_13 VARCHAR(255) COMMENT 'Jul 07 - Jul 13',    jun_30_jul_06 VARCHAR(255) COMMENT 'Jun 30 - Jul 06',    jun_23_jun_29 VARCHAR(255) COMMENT 'Jun 23 - Jun 29',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update time'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='scorecard data from POS system';


-- ================================================================
-- PAYROLL TABLE
-- Total columns: 18
-- ================================================================

-- PAYROLL Table Schema (18 total columns)
CREATE TABLE IF NOT EXISTS pos_payroll (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Primary key',
    payroll VARCHAR(255) COMMENT 'payroll',    2_week_ending_sun VARCHAR(255) COMMENT '2 WEEK ENDING SUN',    rental_revenue_6800 DECIMAL(12,2) COMMENT ' Rental Revenue 6800 ',    all_revenue_6800 DECIMAL(12,2) COMMENT ' All Revenue 6800 ',    payroll_6800 VARCHAR(255) COMMENT ' Payroll 6800 ',    wage_hours_6800 INT COMMENT 'Wage Hours 6800',    rental_revenue_3607 DECIMAL(12,2) COMMENT ' Rental Revenue 3607 ',    all_revenue_3607 DECIMAL(12,2) COMMENT ' All Revenue 3607 ',    payroll_3607 VARCHAR(255) COMMENT ' Payroll 3607 ',    wage_hours_3607 INT COMMENT 'Wage Hours 3607',    rental_revenue_8101 DECIMAL(12,2) COMMENT ' Rental Revenue 8101 ',    all_revenue_8101 DECIMAL(12,2) COMMENT ' All Revenue 8101 ',    payroll_8101 VARCHAR(255) COMMENT ' Payroll 8101 ',    wage_hours_8101 INT COMMENT 'Wage Hours 8101',    rental_revenue_728 DECIMAL(12,2) COMMENT ' Rental Revenue 728 ',    all_revenue_728 DECIMAL(12,2) COMMENT ' All Revenue 728 ',    payroll_728 VARCHAR(255) COMMENT ' Payroll 728 ',    wage_hours_728 INT COMMENT 'Wage Hours 728',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update time'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='payroll data from POS system';


-- ================================================================
-- PL TABLE
-- Total columns: 43
-- ================================================================

-- PL Table Schema (43 total columns)
CREATE TABLE IF NOT EXISTS pos_profit_loss (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Primary key',
    pl VARCHAR(255) COMMENT 'pl',    column_292 VARCHAR(255) COMMENT 'no title',    no_title1 VARCHAR(255) COMMENT 'no title.1',    3607 VARCHAR(255) COMMENT 'Generated column',    6800 VARCHAR(255) COMMENT 'Generated column',    728 VARCHAR(255) COMMENT 'Generated column',    8101 VARCHAR(255) COMMENT 'Generated column',    sales_revenue DECIMAL(12,2) COMMENT 'Sales Revenue',    36071 VARCHAR(255) COMMENT '3607.1',    68001 VARCHAR(255) COMMENT '6800.1',    7281 VARCHAR(255) COMMENT '728.1',    81011 VARCHAR(255) COMMENT '8101.1',    other_revenue DECIMAL(12,2) COMMENT 'Other Revenue',    damage_waiver_fees DECIMAL(12,2) COMMENT 'Damage Waiver Fees',    sale_new_equipment DECIMAL(12,2) COMMENT 'Sale New Equipment',    sale_used_equipment DECIMAL(12,2) COMMENT 'Sale Used Equipment',    total_revenue DECIMAL(12,2) COMMENT 'Total Revenue',    cogs VARCHAR(255) COMMENT 'COGS',    merchandise VARCHAR(255) COMMENT 'Merchandise',    repair_parts VARCHAR(255) COMMENT 'Repair Parts',    shop_supplies VARCHAR(255) COMMENT 'Shop Supplies',    vehicle_fuel VARCHAR(255) COMMENT 'Vehicle Fuel',    shop_oil_gas VARCHAR(255) COMMENT 'Shop Oil & Gas',    subrentleased_equip DECIMAL(12,2) COMMENT 'Subrent/Leased Equip',    employee_uniforms VARCHAR(255) COMMENT 'Employee Uniforms',    freight VARCHAR(255) COMMENT 'Freight',    outside_repairs VARCHAR(255) COMMENT 'Outside Repairs',    new_small_equip VARCHAR(255) COMMENT 'New Small Equip',    direct_costs DECIMAL(12,2) COMMENT 'Direct Costs',    total_cogs VARCHAR(255) COMMENT 'Total COGS',    gross_profit VARCHAR(255) COMMENT 'Gross Profit',    expenses DECIMAL(12,2) COMMENT 'Expenses',    loan_payments VARCHAR(255) COMMENT 'Loan payments',    new_large_equip VARCHAR(255) COMMENT 'New Large Equip',    total_payroll_benefits VARCHAR(255) COMMENT '   Total Payroll & Benefits',    contract_labor VARCHAR(255) COMMENT '   Contract Labor',    accounting_professional INT COMMENT '   Accounting & Professional',    advertising VARCHAR(255) COMMENT '   Advertising',    education_training VARCHAR(255) COMMENT '   Education & Training',    office_expenses DECIMAL(12,2) COMMENT '   Office Expenses',    occupancy_expense DECIMAL(12,2) COMMENT '   Occupancy Expense',    total_expenses DECIMAL(12,2) COMMENT 'Total Expenses',    net_income DECIMAL(12,2) COMMENT 'Net Income',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update time'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='pl data from POS system';


-- ================================================================
-- ALTER TABLE STATEMENTS FOR EXISTING TABLES
-- ================================================================
ALTER TABLE equipment_items ADD COLUMN pos_equipment VARCHAR(255) COMMENT 'POS Equipment';
ALTER TABLE equipment_items ADD COLUMN loc VARCHAR(255) COMMENT 'LOC';
ALTER TABLE equipment_items ADD COLUMN qyot INT COMMENT 'QYOT';
ALTER TABLE equipment_items ADD COLUMN sell DECIMAL(12,2) COMMENT 'SELL';
ALTER TABLE equipment_items ADD COLUMN dep VARCHAR(255) COMMENT 'DEP';
ALTER TABLE equipment_items ADD COLUMN dmg DECIMAL(12,2) COMMENT 'DMG';
ALTER TABLE equipment_items ADD COLUMN msg VARCHAR(255) COMMENT 'Msg';
ALTER TABLE equipment_items ADD COLUMN sdate DATE COMMENT 'SDATE';
ALTER TABLE equipment_items ADD COLUMN type VARCHAR(255) COMMENT 'TYPE';
ALTER TABLE equipment_items ADD COLUMN taxcode DECIMAL(12,2) COMMENT 'TaxCode';
ALTER TABLE equipment_items ADD COLUMN inst VARCHAR(255) COMMENT 'INST';
ALTER TABLE equipment_items ADD COLUMN fuel VARCHAR(255) COMMENT 'FUEL';
ALTER TABLE equipment_items ADD COLUMN addt VARCHAR(500) COMMENT 'ADDT';
ALTER TABLE equipment_items ADD COLUMN per1 INT COMMENT 'PER1';
ALTER TABLE equipment_items ADD COLUMN per2 INT COMMENT 'PER2';
ALTER TABLE equipment_items ADD COLUMN per3 INT COMMENT 'PER3';
ALTER TABLE equipment_items ADD COLUMN per4 INT COMMENT 'PER4';
ALTER TABLE equipment_items ADD COLUMN per5 INT COMMENT 'PER5';
ALTER TABLE equipment_items ADD COLUMN per6 INT COMMENT 'PER6';
ALTER TABLE equipment_items ADD COLUMN per7 INT COMMENT 'PER7';
ALTER TABLE equipment_items ADD COLUMN per8 INT COMMENT 'PER8';
ALTER TABLE equipment_items ADD COLUMN per9 INT COMMENT 'PER9';
ALTER TABLE equipment_items ADD COLUMN per10 INT COMMENT 'PER10';
ALTER TABLE equipment_items ADD COLUMN rate1 DECIMAL(12,2) COMMENT 'RATE1';
ALTER TABLE equipment_items ADD COLUMN rate2 DECIMAL(12,2) COMMENT 'RATE2';
ALTER TABLE equipment_items ADD COLUMN rate3 DECIMAL(12,2) COMMENT 'RATE3';
ALTER TABLE equipment_items ADD COLUMN rate4 DECIMAL(12,2) COMMENT 'RATE4';
ALTER TABLE equipment_items ADD COLUMN rate5 DECIMAL(12,2) COMMENT 'RATE5';
ALTER TABLE equipment_items ADD COLUMN rate6 DECIMAL(12,2) COMMENT 'RATE6';
ALTER TABLE equipment_items ADD COLUMN rate7 DECIMAL(12,2) COMMENT 'RATE7';
ALTER TABLE equipment_items ADD COLUMN rate8 DECIMAL(12,2) COMMENT 'RATE8';
ALTER TABLE equipment_items ADD COLUMN rate9 DECIMAL(12,2) COMMENT 'RATE9';
ALTER TABLE equipment_items ADD COLUMN rate10 DECIMAL(12,2) COMMENT 'RATE10';
ALTER TABLE equipment_items ADD COLUMN rcod VARCHAR(255) COMMENT 'RCOD';
ALTER TABLE equipment_items ADD COLUMN subr VARCHAR(255) COMMENT 'SUBR';
ALTER TABLE equipment_items ADD COLUMN partnumber INT COMMENT 'PartNumber';
ALTER TABLE equipment_items ADD COLUMN num INT COMMENT 'NUM';
ALTER TABLE equipment_items ADD COLUMN manf VARCHAR(255) COMMENT 'MANF';
ALTER TABLE equipment_items ADD COLUMN modn VARCHAR(255) COMMENT 'MODN';
ALTER TABLE equipment_items ADD COLUMN dstn VARCHAR(500) COMMENT 'DSTN';
ALTER TABLE equipment_items ADD COLUMN dstp VARCHAR(500) COMMENT 'DSTP';
ALTER TABLE equipment_items ADD COLUMN rmin INT COMMENT 'RMIN';
ALTER TABLE equipment_items ADD COLUMN rmax INT COMMENT 'RMAX';
ALTER TABLE equipment_items ADD COLUMN userdefined1 VARCHAR(255) COMMENT 'UserDefined1';
ALTER TABLE equipment_items ADD COLUMN userdefined2 VARCHAR(255) COMMENT 'UserDefined2';
ALTER TABLE equipment_items ADD COLUMN mtot VARCHAR(255) COMMENT 'MTOT';
ALTER TABLE equipment_items ADD COLUMN mtin VARCHAR(255) COMMENT 'MTIN';
ALTER TABLE equipment_items ADD COLUMN call VARCHAR(255) COMMENT 'CALL';
ALTER TABLE equipment_items ADD COLUMN resb VARCHAR(255) COMMENT 'RESB';
ALTER TABLE equipment_items ADD COLUMN resd VARCHAR(255) COMMENT 'RESD';
ALTER TABLE equipment_items ADD COLUMN queb VARCHAR(255) COMMENT 'QUEB';
ALTER TABLE equipment_items ADD COLUMN qued VARCHAR(255) COMMENT 'QUED';
ALTER TABLE equipment_items ADD COLUMN ssn VARCHAR(255) COMMENT 'SSN';
ALTER TABLE equipment_items ADD COLUMN cusn VARCHAR(255) COMMENT 'CUSN';
ALTER TABLE equipment_items ADD COLUMN cntr INT COMMENT 'CNTR';
ALTER TABLE equipment_items ADD COLUMN purd VARCHAR(255) COMMENT 'PURD';
ALTER TABLE equipment_items ADD COLUMN purp DECIMAL(12,2) COMMENT 'PURP';
ALTER TABLE equipment_items ADD COLUMN depm VARCHAR(255) COMMENT 'DEPM';
ALTER TABLE equipment_items ADD COLUMN slvg DECIMAL(12,2) COMMENT 'SLVG';
ALTER TABLE equipment_items ADD COLUMN depa VARCHAR(255) COMMENT 'DEPA';
ALTER TABLE equipment_items ADD COLUMN depp DECIMAL(12,2) COMMENT 'DEPP';
ALTER TABLE equipment_items ADD COLUMN curv VARCHAR(255) COMMENT 'CURV';
ALTER TABLE equipment_items ADD COLUMN sold VARCHAR(255) COMMENT 'SOLD';
ALTER TABLE equipment_items ADD COLUMN samt VARCHAR(255) COMMENT 'SAMT';
ALTER TABLE equipment_items ADD COLUMN inc1 VARCHAR(255) COMMENT 'INC1';
ALTER TABLE equipment_items ADD COLUMN inc2 VARCHAR(255) COMMENT 'INC2';
ALTER TABLE equipment_items ADD COLUMN inc3 VARCHAR(255) COMMENT 'INC3';
ALTER TABLE equipment_items ADD COLUMN repc1 VARCHAR(255) COMMENT 'REPC1';
ALTER TABLE equipment_items ADD COLUMN repc2 VARCHAR(255) COMMENT 'REPC2';
ALTER TABLE equipment_items ADD COLUMN tmot1 VARCHAR(255) COMMENT 'TMOT1';
ALTER TABLE equipment_items ADD COLUMN tmot2 VARCHAR(255) COMMENT 'TMOT2';
ALTER TABLE equipment_items ADD COLUMN tmot3 VARCHAR(255) COMMENT 'TMOT3';
ALTER TABLE equipment_items ADD COLUMN hrot1 VARCHAR(255) COMMENT 'HROT1';
ALTER TABLE equipment_items ADD COLUMN hrot2 VARCHAR(255) COMMENT 'HROT2';
ALTER TABLE equipment_items ADD COLUMN hrot3 VARCHAR(255) COMMENT 'HROT3';
ALTER TABLE equipment_items ADD COLUMN ldate DATE COMMENT 'LDATE';
ALTER TABLE equipment_items ADD COLUMN lookup VARCHAR(255) COMMENT 'LOOKUP';
ALTER TABLE equipment_items ADD COLUMN asset VARCHAR(255) COMMENT 'Asset';
ALTER TABLE equipment_items ADD COLUMN glaccount INT COMMENT 'GLAccount';
ALTER TABLE equipment_items ADD COLUMN deprecaccount DECIMAL(12,2) COMMENT 'DeprecAccount';
ALTER TABLE equipment_items ADD COLUMN homestore VARCHAR(255) COMMENT 'HomeStore';
ALTER TABLE equipment_items ADD COLUMN currentstore DECIMAL(12,2) COMMENT 'CurrentStore';
ALTER TABLE equipment_items ADD COLUMN group VARCHAR(255) COMMENT 'Group';
ALTER TABLE equipment_items ADD COLUMN serialnumber INT COMMENT 'SerialNumber';
ALTER TABLE equipment_items ADD COLUMN nontaxable DECIMAL(12,2) COMMENT 'Nontaxable';
ALTER TABLE equipment_items ADD COLUMN header BOOLEAN COMMENT 'Header';
ALTER TABLE equipment_items ADD COLUMN license VARCHAR(255) COMMENT 'License';
ALTER TABLE equipment_items ADD COLUMN caseqty INT COMMENT 'CaseQty';
ALTER TABLE equipment_items ADD COLUMN itempercentage DECIMAL(12,2) COMMENT 'ItemPercentage';
ALTER TABLE equipment_items ADD COLUMN modelyear INT COMMENT 'ModelYear';
ALTER TABLE equipment_items ADD COLUMN retailprice DECIMAL(12,2) COMMENT 'RetailPrice';
ALTER TABLE equipment_items ADD COLUMN extradepreciation DECIMAL(12,2) COMMENT 'ExtraDepreciation';
ALTER TABLE equipment_items ADD COLUMN extracharges VARCHAR(255) COMMENT 'ExtraCharges';
ALTER TABLE equipment_items ADD COLUMN pricelevela DECIMAL(12,2) COMMENT 'PriceLevelA';
ALTER TABLE equipment_items ADD COLUMN pricelevelb DECIMAL(12,2) COMMENT 'PriceLevelB';
ALTER TABLE equipment_items ADD COLUMN pricelevelc DECIMAL(12,2) COMMENT 'PriceLevelC';
ALTER TABLE equipment_items ADD COLUMN nondiscountable INT COMMENT 'NonDiscountable';
ALTER TABLE equipment_items ADD COLUMN vendornumber1 INT COMMENT 'VendorNumber1';
ALTER TABLE equipment_items ADD COLUMN vendornumber2 INT COMMENT 'VendorNumber2';
ALTER TABLE equipment_items ADD COLUMN vendornumber3 INT COMMENT 'VendorNumber3';
ALTER TABLE equipment_items ADD COLUMN quantityonorder VARCHAR(255) COMMENT 'QuantityOnOrder';
ALTER TABLE equipment_items ADD COLUMN noprintoncontract VARCHAR(255) COMMENT 'NoPrintOnContract';
ALTER TABLE equipment_items ADD COLUMN markuppercentage DECIMAL(12,2) COMMENT 'MarkupPercentage';
ALTER TABLE equipment_items ADD COLUMN ordernumber1 INT COMMENT 'OrderNumber1';
ALTER TABLE equipment_items ADD COLUMN ordernumber2 INT COMMENT 'OrderNumber2';
ALTER TABLE equipment_items ADD COLUMN ordernumber3 INT COMMENT 'OrderNumber3';
ALTER TABLE equipment_items ADD COLUMN cleaningdelay VARCHAR(255) COMMENT 'CleaningDelay';
ALTER TABLE equipment_items ADD COLUMN requirecleaning BOOLEAN COMMENT 'RequireCleaning';
ALTER TABLE equipment_items ADD COLUMN maintenancefile VARCHAR(255) COMMENT 'MaintenanceFile';
ALTER TABLE equipment_items ADD COLUMN weblink VARCHAR(500) COMMENT 'WebLink';
ALTER TABLE equipment_items ADD COLUMN subrentcostmtd DECIMAL(12,2) COMMENT 'SubrentCostMTD';
ALTER TABLE equipment_items ADD COLUMN subrentcostytd DECIMAL(12,2) COMMENT 'SubrentCostYTD';
ALTER TABLE equipment_items ADD COLUMN subrentpending DECIMAL(12,2) COMMENT 'SubrentPending';
ALTER TABLE equipment_items ADD COLUMN hideonwebsite BOOLEAN COMMENT 'HideOnWebsite';
ALTER TABLE equipment_items ADD COLUMN gpsunitno VARCHAR(255) COMMENT 'GPSUnitNo';
ALTER TABLE equipment_items ADD COLUMN licenseexpire DATE COMMENT 'LicenseExpire';
ALTER TABLE equipment_items ADD COLUMN replacementcost DECIMAL(12,2) COMMENT 'ReplacementCost';
ALTER TABLE equipment_items ADD COLUMN requirecreditcard BOOLEAN COMMENT 'RequireCreditCard';
ALTER TABLE equipment_items ADD COLUMN warrantydate DATE COMMENT 'WarrantyDate';
ALTER TABLE equipment_items ADD COLUMN vehicletype VARCHAR(255) COMMENT 'VehicleType';
ALTER TABLE equipment_items ADD COLUMN vehicleein VARCHAR(255) COMMENT 'VehicleEIN';
ALTER TABLE equipment_items ADD COLUMN descriptionlong TEXT COMMENT 'DescriptionLong';
ALTER TABLE equipment_items ADD COLUMN setuptime TIME COMMENT 'SetupTime';
ALTER TABLE equipment_items ADD COLUMN webgroup VARCHAR(255) COMMENT 'WebGroup';
ALTER TABLE equipment_items ADD COLUMN glincome DECIMAL(12,2) COMMENT 'GLIncome';
ALTER TABLE equipment_items ADD COLUMN bulkitem BOOLEAN COMMENT 'BulkItem';
ALTER TABLE equipment_items ADD COLUMN gvwr INT COMMENT 'GVWR';
ALTER TABLE equipment_items ADD COLUMN criticallevel INT COMMENT 'CriticalLevel';
ALTER TABLE equipment_items ADD COLUMN rentalcase DECIMAL(12,2) COMMENT 'RentalCase';
ALTER TABLE equipment_items ADD COLUMN boughtused BOOLEAN COMMENT 'BoughtUsed';
ALTER TABLE equipment_items ADD COLUMN incomedmgwvr DECIMAL(12,2) COMMENT 'IncomeDmgWvr';
ALTER TABLE equipment_items ADD COLUMN incomeitempercent DECIMAL(12,2) COMMENT 'IncomeItemPercent';
ALTER TABLE equipment_items ADD COLUMN qtycountdifference INT COMMENT 'QtyCountDifference';
ALTER TABLE equipment_items ADD COLUMN suppressavailcheck BOOLEAN COMMENT 'SuppressAvailCheck';
ALTER TABLE equipment_items ADD COLUMN fueltanksize VARCHAR(255) COMMENT 'FuelTankSize';
ALTER TABLE equipment_items ADD COLUMN notransfers VARCHAR(255) COMMENT 'NoTransfers';
ALTER TABLE equipment_items ADD COLUMN commissionlevel DECIMAL(12,2) COMMENT 'CommissionLevel';
ALTER TABLE equipment_items ADD COLUMN barcode VARCHAR(255) COMMENT 'Barcode';
ALTER TABLE equipment_items ADD COLUMN style1 VARCHAR(255) COMMENT 'Style1';
ALTER TABLE equipment_items ADD COLUMN style2 VARCHAR(255) COMMENT 'Style2';
ALTER TABLE equipment_items ADD COLUMN style3 VARCHAR(255) COMMENT 'Style3';
ALTER TABLE equipment_items ADD COLUMN desiredroi DECIMAL(12,2) COMMENT 'DesiredROI';
ALTER TABLE equipment_items ADD COLUMN cubicsize INT COMMENT 'CubicSize';
ALTER TABLE equipment_items ADD COLUMN bulkserializedmethod BOOLEAN COMMENT 'BulkSerializedMethod';
ALTER TABLE equipment_items ADD COLUMN nonfulfillable BOOLEAN COMMENT 'Nonfulfillable';
ALTER TABLE equipment_items ADD COLUMN rateengineid DECIMAL(12,2) COMMENT 'RateEngineId';
ALTER TABLE equipment_items ADD COLUMN baserate DECIMAL(12,2) COMMENT 'BaseRate';
ALTER TABLE equipment_items ADD COLUMN rateengineiddisplayed DECIMAL(12,2) COMMENT 'RateEngineIdDisplayed';
ALTER TABLE equipment_items ADD COLUMN accountingdepartmentid INT COMMENT 'AccountingDepartmentId';
ALTER TABLE equipment_items ADD COLUMN accountingclassid INT COMMENT 'AccountingClassId';
ALTER TABLE equipment_items ADD COLUMN itemmanufacturerid VARCHAR(255) COMMENT 'ItemManufacturerId';
ALTER TABLE equipment_items ADD COLUMN ispartitem VARCHAR(255) COMMENT 'IsPartItem';
ALTER TABLE equipment_items ADD COLUMN floorprice DECIMAL(12,2) COMMENT 'FloorPrice';
ALTER TABLE equipment_items ADD COLUMN fleetid VARCHAR(255) COMMENT 'FleetID';
ALTER TABLE equipment_items ADD COLUMN height VARCHAR(255) COMMENT 'Height';
ALTER TABLE equipment_items ADD COLUMN width VARCHAR(255) COMMENT 'Width';
ALTER TABLE equipment_items ADD COLUMN length VARCHAR(255) COMMENT 'Length';
ALTER TABLE equipment_items ADD COLUMN suspenseexempt BOOLEAN COMMENT 'SuspenseExempt';
ALTER TABLE equipment_items ADD COLUMN salestaxcode DECIMAL(12,2) COMMENT 'SalesTaxCode';
ALTER TABLE equipment_items ADD COLUMN createddatetime DATETIME COMMENT 'CreatedDateTime';
ALTER TABLE equipment_items ADD COLUMN updateddatetime DATETIME COMMENT 'UpdatedDateTime';
ALTER TABLE equipment_items ADD COLUMN replacedmeterlifetimeaccumulation TIME COMMENT 'ReplacedMeterLifetimeAccumulation';

SET FOREIGN_KEY_CHECKS = 1;