# API Endpoints Required for Operations UI

## Summary
The following API endpoints need to be implemented in the FastAPI backend to support the 5 operations tabs ported from the Flask application.

## 1. Rental Inventory Page (Tab 1)

### Categories Hierarchy
- `GET /api/v1/items/categories` - Get all categories with optional filters
  - Query params: `resale_only`, `available_only`

- `GET /api/v1/items/categories/{category_id}/subcategories` - Get subcategories for a category
  - Query params: `resale_only`, `available_only`

- `GET /api/v1/items/subcategories/{subcategory_id}/common-names` - Get common names for a subcategory
  - Query params: `resale_only`, `available_only`

- `GET /api/v1/items/by-rental-class` - Get items filtered by rental class hierarchy
  - Query params: `category`, `subcategory`, `common_name`, `status`, `location`

### Item Operations
- `PATCH /api/v1/items/{tag_id}/status` - Update item status
  - Body: `{ "status": "available|rented|service|laundry|resale|sold" }`

- `PATCH /api/v1/items/{tag_id}/location` - Update item location
  - Body: `{ "location": "string" }`

- `POST /api/v1/items/bulk-update-status` - Bulk update item statuses
  - Body: `{ "tag_ids": ["string"], "status": "string" }`

## 2. Contracts Page (Tab 2) - Already Implemented
- `GET /api/v1/contracts/open` - Get open contracts ✓
- `GET /api/v1/contracts/{contract_no}/items` - Get contract items ✓
- `POST /api/v1/contracts/manual` - Create manual contract ✓
- `POST /api/v1/contracts/assign-tag` - Assign tag to contract ✓
- `POST /api/v1/contracts/merge-pos` - Merge with POS contract ✓

## 3. Service & Maintenance Page (Tab 3)

### Service Items
- `GET /api/v1/service/items` - Get items in service
  - Query params: `crew` (Tent|Linen|Service Dept), `status`

- `POST /api/v1/service/{tag_id}/complete` - Mark service complete
  - Body: `{ "service_types": {}, "notes": "string" }`

### Tag Printing
- `POST /api/v1/service/generate-tags` - Generate CSV for Zebra printer
  - Body: `{ "tag_ids": ["string"], "quantity": number }`

- `POST /api/v1/service/update-synced` - Mark items as synced
  - Body: `{ "tag_ids": ["string"] }`

## 4. Laundry Contracts Page (Tab 4)

### Contract Management
- `GET /api/v1/service/laundry-contracts` - Get all laundry contracts
  - Returns contracts with status (PreWash Count|Sent to Laundry|Returned)

- `POST /api/v1/service/laundry-contract` - Create new laundry contract
  - Body: `{ "notes": "string" }`

- `POST /api/v1/service/laundry-contract/{contract_id}/finalize` - Finalize contract (send to laundry)

- `POST /api/v1/service/laundry-contract/{contract_id}/returned` - Mark contract as returned

- `POST /api/v1/service/laundry-contract/{contract_id}/reactivate` - Reactivate a returned contract

### Hand Counted Items
- `POST /api/v1/service/hand-counted-item` - Add hand-counted item to contract
  - Body: `{ "contract_id": "string", "common_name": "string", "quantity": number, "notes": "string" }`

## 5. Resale Items Page (Tab 5)

### Resale Operations
- `GET /api/v1/items/resale` - Get resale items
  - Query params: `status` (resale|sold), `category`, `subcategory`

- `GET /api/v1/items/export-sold` - Export sold items as CSV
  - Returns: CSV file blob

## Common/Existing Endpoints Used
- `GET /api/v1/items` - Get all items ✓
- `GET /api/v1/items/{tag_id}` - Get single item ✓
- `POST /api/v1/items` - Create item ✓
- `PUT /api/v1/items/{tag_id}` - Update item ✓
- `DELETE /api/v1/items/{tag_id}` - Delete item ✓
- `GET /api/v1/items/search` - Search items ✓
- `POST /api/v1/scan` - Process scan ✓
- `GET /api/v1/scan/lookup/{identifier}` - Lookup by identifier ✓
- `POST /api/v1/scan/batch` - Batch scan ✓
- `GET /api/v1/health` - Health check ✓

## Data Models Needed

### Category Model
```python
{
  "id": "string",
  "name": "string",
  "item_count": number,
  "available_count": number,
  "subcategories": [SubcategoryModel]  # Optional, when expanded
}
```

### Subcategory Model
```python
{
  "id": "string",
  "category_id": "string",
  "name": "string",
  "item_count": number,
  "available_count": number,
  "common_names": [CommonNameModel]  # Optional, when expanded
}
```

### CommonName Model
```python
{
  "name": "string",
  "subcategory_id": "string",
  "item_count": number,
  "available_count": number,
  "items": [ItemModel]  # Optional, when expanded
}
```

### LaundryContract Model
```python
{
  "id": "string",
  "contract_number": "string",
  "status": "PreWash Count|Sent to Laundry|Returned",
  "created_at": "datetime",
  "finalized_at": "datetime",
  "returned_at": "datetime",
  "item_count": number,
  "hand_counted": number,
  "items": [LaundryItemModel]
}
```

### ServiceItem Model
```python
{
  "tag_id": "string",
  "common_name": "string",
  "crew": "Tent|Linen|Service Dept",
  "status": "service|laundry|available",
  "quality": "Good|Fair|Poor",
  "identifier_type": "RFID|QR",
  "service_required": boolean,
  "dirty_mud": boolean,
  "oil": boolean,
  "rip_tear": boolean,
  "sewing_repair": boolean,
  # ... other service flags
}
```

## Implementation Priority
1. **High Priority** - Required for basic functionality:
   - Categories hierarchy endpoints (Tab 1)
   - Service items endpoints (Tab 3)
   - Laundry contract endpoints (Tab 4)
   - Resale items endpoints (Tab 5)

2. **Medium Priority** - Enhanced features:
   - Bulk operations endpoints
   - Export/CSV generation endpoints
   - Tag printing integration

3. **Low Priority** - Can be mocked initially:
   - Statistics aggregation
   - Historical data endpoints