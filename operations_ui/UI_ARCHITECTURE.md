# Operations UI Architecture Document
**Version:** 1.0.0
**Date:** 2025-09-20
**Scanner:** Chainway SR160 + Camera Support

## 📱 PAGE STRUCTURE

### 1. Dashboard (Home)
**Features:**
- Store filter in config (3607, 6800, 728, 8101)
- Real-time WebSocket updates
- KPI Cards:
  - Inventory/Resale metrics
  - Weather widget (Minnesota seasonal)
  - Service queue status
- Recent activity feed with live updates
- Scanner connection status

### 2. Scanning Interface
**Features:**
- Dual input: Chainway SR160 (HID mode) + Camera QR
- Offline mode with local storage
- Required fields from id_item_master & id_transactions
- Scan modes:
  - Check Status
  - Check Out to Contract
  - Check In from Contract
  - Service/Maintenance
  - Laundry Processing
- Batch scanning support
- Audio/visual feedback

### 3. Open Contracts/Reservations
**Tab Structure:**
- Today's Open Contracts
- Currently Active
- Tomorrow (Day +1)
- Day +2
- Day +3
- Custom Date Picker

**Features:**
- Click contract to view details
- Display: Contract items, transactions, customer info
- **TAG ASSIGNMENT:** Select item → Scan RFID/QR to link
- **PHOTO DOCUMENTATION:**
  - Take photos of equipment going out
  - Document quality/condition
  - For POS bulk items: photo to verify quantity
  - Photos stored with contract_id + item_id + timestamp
  - Multiple photos per item allowed
  - Photo comparison (before/after)
- Manual contract entry (for POS lag situations)
- Automatic POS merge when updated
- Signature capture for deliveries

### 4. Returns Processing
**Features:**
- Active returns list
- Scan items for return
- Condition assessment
- **PHOTO DOCUMENTATION:**
  - Return condition photos (mandatory for damage)
  - Compare with checkout photos
  - Damage detail close-ups
  - Full item overview shots
- Photo capture capability with annotations
- Update id_transactions
- Print return receipt with damage notes

### 5. Service Management
**Features:**
- Service queue display
- Status changes (needs service, in service, completed)
- Service notes and history
- **SERVICE PHOTOS:**
  - Before service condition
  - Damaged parts/areas
  - After repair completion
  - Parts used documentation
- Parts/repair tracking
- Technician assignment
- Service completion sign-off

### 6. Laundry Operations
**Features:**
- Create "L" type laundry contracts
- Hand count input interface
- **LAUNDRY PHOTOS:**
  - Pre-wash condition documentation
  - Stain/damage identification
  - Post-wash quality check
- Bulk item processing
- Laundry batch tracking
- Status: Dirty, Washing, Drying, Clean
- Batch completion tracking

### 7. Items Management
**Features:**
- Full CRUD on id_item_master fields
- Bulk operations
- Item number as QR for non-RFID items
- **ITEM PHOTOS:**
  - Master item photo for identification
  - Current condition photo
  - Photo history timeline
- Status updates
- Location tracking
- **Admin PIN (7409):** Required for:
  - Tag assignment to items
  - Item deletion
- Barcode printing (framework only, future implementation)

### 8. Sync & Settings
**Features:**
- Manual sync button with simple progress
- Store selection filter
- Scanner pairing configuration
- Admin PIN management (changeable)
- Audit log for all sync operations
- User preferences
- Offline data queue display
- **Photo storage settings:**
  - Compression quality
  - Auto-upload when online
  - Local storage limits

## 📸 PHOTO DOCUMENTATION SYSTEM

### Photo Storage Structure:
```javascript
// Photo naming convention
{contract_id}_{item_id}_{type}_{timestamp}.jpg

// Types:
- checkout_condition
- checkout_quantity  // For bulk POS items
- return_condition
- damage_detail
- service_before
- service_after
- laundry_before
- laundry_after

// Storage paths:
/home/tim/RFID3/operations_ui/photos/
  ├── contracts/
  │   ├── {contract_id}/
  │   │   ├── checkout/
  │   │   ├── return/
  │   │   └── signatures/
  ├── items/
  │   └── {item_id}/
  └── service/
      └── {service_id}/
```

### Photo Capture Interface:
```javascript
// Photo capture component features
- Camera selection (front/back)
- Flash toggle
- Grid overlay for alignment
- Annotation tools (arrows, circles, text)
- Quantity verification overlay for bulk items
- Side-by-side comparison view
- Thumbnail preview gallery
- Delete/retake options
```

### Quantity Verification (POS Bulk Items):
```javascript
// For items only in POS equipment table (no individual RFID)
- Photo required when checking out bulk quantity
- Overlay shows: Expected qty from POS
- User confirms actual qty in photo
- Photo serves as quantity verification record
```

## 🔄 DATA FLOW

### Real-time Updates (WebSocket)
```javascript
// WebSocket connection for live updates
ws://100.103.67.41:8445/ws
- New scans
- Contract updates
- Inventory changes
- Service queue updates
- Photo upload status
```

### Offline Mode
```javascript
// LocalStorage structure
{
  pendingScans: [],
  pendingContracts: [],
  pendingPhotos: [],  // Base64 encoded
  cachedItems: {},
  lastSync: timestamp
}
```

### Photo Sync Strategy:
```javascript
// When online:
1. Upload photos immediately
2. Get server URL reference
3. Update local record with URL

// When offline:
1. Store photo as base64 in IndexedDB
2. Queue for upload
3. Sync when connection restored
```

### Manual Contract → POS Merge
```sql
-- Manual contract created with temp ID
INSERT INTO ops_contracts (contract_id, is_manual, temp_id, ...)

-- When POS updates, merge logic
UPDATE ops_contracts
SET pos_contract_id = ?, is_manual = false
WHERE temp_id = ?

-- Photos remain linked through item_id
```

## 📊 DATABASE FIELDS MAPPING

### Required Fields from id_item_master:
- tag_id (PRIMARY)
- item_num
- serial_number
- rental_class_num
- common_name
- quality
- bin_location
- status
- current_store
- identifier_type

### Required Fields from id_transactions:
- contract_number
- scan_type
- scan_date
- client_name
- scan_by
- All condition flags (dirty_or_mud, leaves, oil, etc.)

### POS Correlation Fields:
- pos_item_num → rental_class_num
- customer_id → client_name
- contract dates and status
- **qty field for bulk items requiring photo verification**

### New Photo Documentation Table:
```sql
CREATE TABLE ops_photos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id VARCHAR(255),
    contract_id VARCHAR(255),
    photo_type VARCHAR(50),
    photo_path VARCHAR(500),
    thumbnail_path VARCHAR(500),
    quantity_verified INT,  -- For bulk POS items
    notes TEXT,
    taken_by VARCHAR(100),
    taken_at DATETIME,
    uploaded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_item_id (item_id),
    INDEX ix_contract_id (contract_id)
);
```

## 🔐 SECURITY

### Admin Functions (PIN: 7409)
- Tag assignment to items
- Item deletion
- Sync configuration
- Store settings
- Photo deletion

### Audit Logging
- All sync operations
- Tag assignments
- Manual contract creation
- Status changes
- Photo captures with user/timestamp
- User actions with timestamps

## 📱 MOBILE RESPONSIVE DESIGN

### Breakpoints:
- Mobile: < 768px (phone with scanner)
- Tablet: 768px - 1024px (tablet with scanner)
- Desktop: > 1024px (workstation)

### Touch Optimization:
- Minimum button size: 44x44px
- Swipe gestures for tab navigation
- Pull-to-refresh on lists
- Long-press for context menus
- Pinch-to-zoom on photos

### Camera Integration:
- Native camera API for mobile devices
- WebRTC for desktop browsers
- File upload fallback option
- Auto-rotate based on EXIF data

## 🚀 IMPLEMENTATION PRIORITY

1. **Phase 1 (Core):**
   - Scanning Interface
   - Open Contracts with tag assignment
   - Returns Processing
   - Basic photo capture for checkout/return

2. **Phase 2 (Operations):**
   - Service Management with photos
   - Laundry Operations
   - Items Management
   - Full photo documentation system

3. **Phase 3 (Enhancement):**
   - Dashboard with KPIs
   - WebSocket real-time
   - Offline mode with photo sync
   - Signature capture
   - Photo annotations

## 📝 NOTES

- Item numbers can be used as QR codes for bulk items
- Manual contracts must merge smoothly with POS updates
- All operations data visible (no financial filtering needed)
- Weather integration important for Minnesota seasonal patterns
- Service tracking critical for maintenance operations
- Laundry contracts use "L" prefix for identification
- Photos essential for quality documentation and dispute resolution
- Bulk POS items require quantity verification photos