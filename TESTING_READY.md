# RFID Operations System - Ready for Testing
Date: 2025-09-20
Status: UI and API Running

## Access URLs

### Operations UI (React)
- **URL**: https://localhost:3000
- **Tailscale**: https://100.103.67.41:3000
- **Status**: ✅ Running

### Operations API (FastAPI)
- **Internal**: http://localhost:8444
- **External**: https://localhost:8443 (via nginx)
- **Tailscale**: https://100.103.67.41:8443
- **API Docs**: http://localhost:8444/docs
- **Status**: ✅ Running

### Manager App (Executive Dashboard)
- **URL**: http://localhost:8101
- **Status**: Should be running (separate system)

## Current Features Available for Testing

### 1. Dashboard Page (/)
- KPI overview cards
- Quick stats for operations
- Recent activity feed

### 2. Contracts Page (/contracts)
- View open contracts by day (Today, Tomorrow, +2 days, etc.)
- Tag assignment interface
- Manual contract creation
- Item checklist with progress tracking
- Real-time RFID/QR scanner integration

### 3. Scan Page (/scan)
- Multi-mode scanning (Checkout, Return, Service, Laundry)
- HID mode scanner support for Chainway SR160
- Manual tag entry fallback
- Scan history tracking
- Contract selection for checkout mode

### 4. Items Page (/items)
- Inventory search and filtering
- View item status and location
- Tag type identification (RFID vs QR)
- Quality and service status tracking

## Test Scenarios

### Scenario 1: Contract Tag Assignment
1. Navigate to Contracts page
2. Select a contract (or create manual one)
3. Click "Assign Tag" on an item
4. Scan or manually enter a tag ID
5. Verify tag is assigned to contract

### Scenario 2: Bulk Scanning
1. Go to Scan page
2. Select "Checkout" mode
3. Load a contract
4. Start scanning multiple items rapidly
5. Check scan history updates

### Scenario 3: Item Search
1. Navigate to Items page
2. Use search to find specific items
3. Filter by store location
4. Verify status badges are correct

## Known Limitations (Phase 1)

1. **Photo capture not yet implemented** - Planned for next phase
2. **Returns/Service/Laundry pages** - Basic functionality only
3. **Manual RFIDpro sync** - Not automated yet
4. **Offline mode** - Not implemented yet

## Database Status

- Operations DB: `rfid_operations_db` (separate from manager)
- POS Tables: Imported and available
- RFID Tables: Linked with contracts
- Test Data: Empty (need to create test contracts)

## SSL Certificates
- Location: `/home/tim/RFID3/operations_ui/certs/`
- Valid for: localhost, 100.103.67.41
- Self-signed (browser warning expected)

## API Endpoints Working

- GET `/api/v1/contracts/open` - Get open contracts
- POST `/api/v1/contracts/manual` - Create manual contract
- POST `/api/v1/contracts/assign-tag` - Assign RFID/QR to item
- GET `/api/v1/contracts/{contract_no}/items` - Get contract details
- GET `/api/v1/items/search` - Search inventory

## Next Steps After Testing

1. Add photo capture for bulk items
2. Implement offline mode with sync
3. Complete Returns/Service/Laundry workflows
4. Add manual RFIDpro sync button
5. Build production deployment package

## Troubleshooting

If UI doesn't load:
```bash
cd /home/tim/RFID3/operations_ui
npm start
```

If API isn't responding:
```bash
cd /home/tim/RFID3/rfid_operations_api
./venv/bin/python run_api.py
```

Check logs:
```bash
sudo journalctl -u rfid-operations-api -n 50
```