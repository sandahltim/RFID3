# Bidirectional RFID Operations API Specification

## Data Flow Architecture

### Core Principle
- **POS Equipment**: Master reference data (updated 1-2x/week via CSV)
- **RFID Item Master**: Real-time operational state (most current)
- **RFID Transactions**: Activity log (most current operational data)

### Bidirectional Operations
Both Manager/Executive interface and Operations interface can:
- Read all data
- Modify item status, location, condition
- Update operational fields
- Create transactions
- Sync changes in real-time

## API Endpoints Design

### 1. EQUIPMENT MASTER DATA (POS-based)
```
GET    /api/v1/equipment                  # List equipment (with filters)
GET    /api/v1/equipment/{item_num}       # Get specific equipment
POST   /api/v1/equipment                  # Add new equipment
PUT    /api/v1/equipment/{item_num}       # Update equipment
PATCH  /api/v1/equipment/{item_num}       # Partial update
DELETE /api/v1/equipment/{item_num}       # Remove equipment

# Filtering examples:
GET /api/v1/equipment?category=Tents&store=3607
GET /api/v1/equipment?inactive=false&department=Party
GET /api/v1/equipment?manufacturer=Coleman&available=true
```

### 2. RFID ITEMS (Real-time operational state)
```
GET    /api/v1/items                      # List RFID items (with filters)
GET    /api/v1/items/{tag_id}             # Get specific item
POST   /api/v1/items                      # Add new RFID item
PUT    /api/v1/items/{tag_id}             # Update item
PATCH  /api/v1/items/{tag_id}             # Partial update (status, location, etc.)
DELETE /api/v1/items/{tag_id}             # Remove item

# Real-time operational updates:
PATCH /api/v1/items/{tag_id}/status       # Update status only
PATCH /api/v1/items/{tag_id}/location     # Update location only
PATCH /api/v1/items/{tag_id}/condition    # Update condition/quality
PATCH /api/v1/items/{tag_id}/contract     # Assign to contract
```

### 3. TRANSACTIONS (Activity logging)
```
GET    /api/v1/transactions               # List transactions (with filters)
GET    /api/v1/transactions/{id}          # Get specific transaction
POST   /api/v1/transactions               # Create new transaction
PUT    /api/v1/transactions/{id}          # Update transaction
PATCH  /api/v1/transactions/{id}          # Partial update
DELETE /api/v1/transactions/{id}          # Remove transaction

# Activity-specific endpoints:
POST   /api/v1/scan                       # Record scan event
POST   /api/v1/checkin                    # Check in item
POST   /api/v1/checkout                   # Check out item
POST   /api/v1/maintenance                # Record maintenance
```

### 4. SYNCHRONIZATION ENDPOINTS
```
# Manager -> Operations sync
POST   /api/v1/sync/from-manager          # Push updates from manager DB
GET    /api/v1/sync/status                # Get sync status
POST   /api/v1/sync/equipment             # Sync equipment data
POST   /api/v1/sync/items                 # Sync RFID items
POST   /api/v1/sync/transactions          # Sync transactions

# Operations -> Manager sync
POST   /api/v1/sync/to-manager            # Push updates to manager DB
GET    /api/v1/sync/changes               # Get pending changes
POST   /api/v1/sync/push-changes          # Push specific changes
```

### 5. REAL-TIME OPERATIONS
```
# Scanning operations
POST   /api/v1/scan/rfid                  # RFID scan
POST   /api/v1/scan/qr                    # QR code scan
POST   /api/v1/scan/barcode               # Barcode scan
GET    /api/v1/scan/lookup/{identifier}   # Lookup by any identifier

# Contract management
GET    /api/v1/contracts                  # List contracts
POST   /api/v1/contracts                  # Create contract
PUT    /api/v1/contracts/{id}             # Update contract
POST   /api/v1/contracts/{id}/items       # Add items to contract
DELETE /api/v1/contracts/{id}/items/{item} # Remove item from contract

# Bulk operations
POST   /api/v1/bulk/status-update         # Bulk status changes
POST   /api/v1/bulk/location-update       # Bulk location changes
POST   /api/v1/bulk/scan                  # Bulk scanning
```

## Request/Response Formats

### Standard Item Update (PATCH)
```json
PATCH /api/v1/items/300F4F573AD0004043E86E3D
{
  "status": "rented",
  "current_store": "3607",
  "bin_location": "A-15-3",
  "quality": "good",
  "last_scanned_by": "john_doe",
  "notes": "Checked condition - ready for delivery",
  "updated_by": "manager_interface"
}
```

### Scan Event (POST)
```json
POST /api/v1/scan
{
  "tag_id": "300F4F573AD0004043E86E3D",
  "scan_type": "checkin",
  "scan_by": "field_user_01",
  "location": "warehouse_dock",
  "quality_assessment": {
    "quality": "fair",
    "dirty_or_mud": true,
    "service_required": false,
    "notes": "Needs cleaning before next rental"
  },
  "gps": {
    "latitude": 44.9537,
    "longitude": -93.2650
  }
}
```

### Sync Operations (POST)
```json
POST /api/v1/sync/from-manager
{
  "sync_type": "incremental",
  "tables": ["equipment", "items"],
  "since": "2025-09-17T10:30:00Z",
  "changes": [
    {
      "table": "equipment",
      "operation": "update",
      "item_num": "12345",
      "fields": {
        "qty": 15,
        "current_store": "6800",
        "last_maintenance": "2025-09-15"
      }
    }
  ]
}
```

## Data Synchronization Strategy

### 1. Real-time Sync Triggers
- Item status changes
- Location updates
- Condition assessments
- Contract assignments
- Scan events

### 2. Bidirectional Conflict Resolution
```
Conflict Resolution Priority:
1. Most recent timestamp wins
2. Operations data (RFID scans) takes priority over POS data
3. Manager corrections override automated changes
4. User-initiated changes override system changes
```

### 3. Sync Frequency
- **Real-time**: Status, location, condition changes
- **Hourly**: Bulk synchronization check
- **Daily**: Full integrity verification
- **Weekly**: Complete POS equipment refresh

### 4. Error Handling
```json
{
  "error": {
    "code": "SYNC_CONFLICT",
    "message": "Item status conflict detected",
    "details": {
      "tag_id": "300F4F573AD0004043E86E3D",
      "manager_value": "available",
      "operations_value": "rented",
      "last_manager_update": "2025-09-17T10:15:00Z",
      "last_operations_update": "2025-09-17T10:20:00Z"
    },
    "resolution": "operations_value_used",
    "timestamp": "2025-09-17T10:21:00Z"
  }
}
```

## Authentication & Authorization

### API Keys
- **Manager Interface**: Full read/write access
- **Operations Interface**: Full read/write access
- **Scanner Users**: Limited to scan operations and status updates
- **Read-only Users**: View access only

### Permission Matrix
```
Operation              | Manager | Operations | Scanner | ReadOnly
--------------------- |---------|------------|---------|----------
Read equipment        |   ✓     |     ✓      |    ✓    |    ✓
Update equipment      |   ✓     |     ✓      |    ✗    |    ✗
Read items           |   ✓     |     ✓      |    ✓    |    ✓
Update item status   |   ✓     |     ✓      |    ✓    |    ✗
Update item location |   ✓     |     ✓      |    ✓    |    ✗
Create transactions  |   ✓     |     ✓      |    ✓    |    ✗
Bulk operations      |   ✓     |     ✓      |    ✗    |    ✗
Sync operations      |   ✓     |     ✓      |    ✗    |    ✗
```

## Performance Considerations

### Manager Interface Load Reduction
- Operations API handles all real-time scanning
- Manager only processes analytics queries
- Sync operations are batched and scheduled
- Heavy processing pushed to operations service

### Caching Strategy
- Equipment data cached (updated 1-2x/week)
- Item status cached with TTL
- Correlation data cached
- Real-time data bypasses cache

### Database Optimization
- Separate read/write connection pools
- Async sync operations
- Indexed for common query patterns
- Batch inserts for transactions