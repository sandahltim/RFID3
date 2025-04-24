test_rfidpi/ RFID2
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── home.py
│   │   ├── tabs.py
│   │   ├── tab1.py
│   │   ├── tab2.py
│   │   ├── tab4.py
│   │   ├── tab4.py
│   │   ├── categories.py
│   │   └── health.py
│   ├── services/
│   │   ├── api_client.py
│   │   ├── refresh.py
│   │   └── scheduler.py
│   ├── models/
│   │   └── db_models.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── categories.html
│   │   ├── home.html
│   │   ├── tab1.html
│   │   ├── tab2.html
│   │   ├── tab3.html
│   │   ├── tab4.html
│   │   └── tab.html
├── static/
│   └── css/
│   │   └── style.css
│   └── js/
│   │   ├── tab.js
│   │   └── expand.js
│   └── lib/
│        ├── htmx/
│        │   └── htmx.min.js
│        └── bootstrap/
│            ├── bootstrap.min.css
│            └── bootstrap.bundle.min.js
├── scripts/
│   ├── migrate_db.sql
│   ├── update_rental_class_mappings.py
│   ├── migrate_hand_counted_items.sql
│   └── setup_mariadb.sh
├── run.py
├── config.py
└── logs/


git pull origin RFID2
> /home/tim/test_rfidpi/logs/gunicorn_error.log
> /home/tim/test_rfidpi/logs/gunicorn_access.log
> /home/tim/test_rfidpi/logs/app.log
> /home/tim/test_rfidpi/logs/sync.log
sudo systemctl stop rfid_dash_dev.service
sudo systemctl start rfid_dash_dev.service
sudo systemctl status rfid_dash_dev.service

cat /home/tim/test_rfidpi/logs/gunicorn_error.log
cat /home/tim/test_rfidpi/logs/app.log
cat /home/tim/test_rfidpi/logs/sync.log

source venv/bin/activate

## Database and API Mapping

### Overview

The application integrates with three API databases and maintains two local tables:

- **API Databases**:
  - **Item Master**: Primary dataset of all items.
  - **Transactions**: Transaction history for items.
  - **Seed Rental Classes**: Mapping of rental class IDs to common names and bin locations.
- **Local Tables**:
  - **Hand Counted Items**: Manually counted items for contracts.
  - **Categories/Mappings**: Custom mappings for organizing items by category and subcategory.

### Database Schemas

#### Item Master (`id_item_master`)
- **Purpose**: Master dataset of all items, uniquely identified by `tag_id` (RFID EPC code).
- **Fields**:
  - `tag_id` (String(255), PK): RFID EPC code.
  - `uuid_accounts_fk` (String(255)): Account foreign key.
  - `serial_number` (String(255)): Serial number.
  - `client_name` (String(255)): Client name.
  - `rental_class_num` (String(255)): Rental class ID (links to `seed_rental_classes.rental_class_id`).
  - `common_name` (String(255)): Item name.
  - `quality` (String(50)): Quality.
  - `bin_location` (String(255)): Location (e.g., "resale", "sold").
  - `status` (String(50)): Status (e.g., "On Rent", "Ready to Rent").
  - `last_contract_num` (String(255)): Latest contract number.
  - `last_scanned_by` (String(255)): Who last scanned.
  - `notes` (Text): Notes.
  - `status_notes` (Text): Status notes.
  - `longitude` (Decimal(9,6)): Scan longitude.
  - `latitude` (Decimal(9,6)): Scan latitude.
  - `date_last_scanned` (DateTime): Last scan date.
  - `date_created` (DateTime): Record creation date.
  - `date_updated` (DateTime): Last update date.
- **API Endpoint**: `cs.iot.ptshome.com/api/v1/data/14223767938169344381` (GET/POST/PUT/PATCH)

#### Transactions (`id_transactions`)
- **Purpose**: Transaction history for items.
- **Fields**:
  - `id` (BigInteger, PK, Auto-increment): Unique transaction ID.
  - `contract_number` (String(255)): Contract number.
  - `tag_id` (String(255)): RFID EPC code (links to `id_item_master.tag_id`).
  - `scan_type` (String(50)): "Touch", "Rental", or "Return".
  - `scan_date` (DateTime): Transaction date.
  - `client_name` (String(255)): Client name.
  - `common_name` (String(255)): Item name.
  - `bin_location` (String(255)): Location.
  - `status` (String(50)): Status.
  - `scan_by` (String(255)): Who scanned.
  - `location_of_repair` (String(255)): Repair location.
  - `quality` (String(50)): Quality.
  - `dirty_or_mud`, `leaves`, `oil`, `mold`, `stain`, `oxidation`, `rip_or_tear`, `sewing_repair_needed`, `grommet`, `rope`, `buckle`, `wet` (Boolean): Condition flags.
  - `other` (Text): Condition notes.
  - `rental_class_num` (String(255)): Rental class ID (links to `seed_rental_classes.rental_class_id`).
  - `serial_number` (String(255)): Serial number.
  - `longitude` (Decimal(9,6)): Scan longitude.
  - `latitude` (Decimal(9,6)): Scan latitude.
  - `service_required` (Boolean): Service needed.
  - `date_created` (DateTime): Creation date.
  - `date_updated` (DateTime): Last update.
  - `uuid_accounts_fk` (String(255)): Account foreign key.
  - `notes` (Text): Notes.
- **API Endpoint**: `cs.iot.ptshome.com/api/v1/data/14223767938169346196` (GET)

#### Seed Rental Classes (`seed_rental_classes`)
- **Purpose**: Maps rental class IDs to common names and bin locations.
- **Fields**:
  - `rental_class_id` (String(255), PK): Rental class ID (links to `id_item_master.rental_class_num` and `id_transactions.rental_class_num`).
  - `common_name` (String(255)): Common name.
  - `bin_location` (String(255)): Default bin location.
- **API Endpoint**: `cs.iot.ptshome.com/api/v1/data/14223767938169215907` (GET/POST/PUT/PATCH)

#### Hand Counted Items (`id_hand_counted_items`, Local)
- **Purpose**: Tracks manually counted items for contracts.
- **Fields**:
  - `id` (Integer, PK, Auto-increment): Record ID.
  - `contract_number` (String(50)): Contract number.
  - `item_name` (String(255)): Item name.
  - `quantity` (Integer): Quantity.
  - `action` (String(50)): "Added" or "Removed".
  - `timestamp` (DateTime): Action date.
  - `user` (String(50)): Who performed the action.

#### Categories/Mappings (`rental_class_mappings` and `user_rental_class_mappings`, Local)
- **Purpose**: Maps rental class IDs to categories and subcategories.
- **Fields (both tables)**:
  - `rental_class_id` (String(50), PK): Rental class ID (links to `id_item_master.rental_class_num`, `id_transactions.rental_class_num`, and `seed_rental_classes.rental_class_id`).
  - `category` (String(100)): Category.
  - `subcategory` (String(100)): Subcategory.
- **Additional Fields (`user_rental_class_mappings`)**:
  - `created_at` (DateTime): Creation date.
  - `updated_at` (DateTime): Last update date.

### Relationships

- `id_item_master.tag_id` ↔ `id_transactions.tag_id` (one-to-many).
- `id_item_master.last_contract_num` ↔ `id_transactions.contract_number` (many-to-one).
- `id_item_master.rental_class_num` ↔ `seed_rental_classes.rental_class_id` (many-to-one).
- `id_item_master.rental_class_num` ↔ `rental_class_mappings.rental_class_id` (many-to-one).
- `id_transactions.rental_class_num` ↔ `seed_rental_classes.rental_class_id` (many-to-one).
- `id_hand_counted_items.contract_number` ↔ `id_item_master.last_contract_num` (one-to-many).

### API Details

- **Authentication**:
  - Endpoint: `login.cloud.ptshome.com/api/v1/login` (POST)
  - Parameters: `username`, `password`
  - Response: Includes `access_token` (valid for 60 minutes).
- **Item Master**:
  - Endpoint: `cs.iot.ptshome.com/api/v1/data/14223767938169344381`
  - Supports: GET/POST/PUT/PATCH
  - GET Parameters: `filter[]`, `offset`, `limit`, `sort[]`, `returncount`
  - POST/PUT/PATCH: Updates fields like `tag_id`, `bin_location`, `status`.
- **Transactions**:
  - Endpoint: `cs.iot.ptshome.com/api/v1/data/14223767938169346196`
  - Supports: GET
  - GET Parameters: `filter[]`, `offset`, `limit`, `sort[]`, `returncount`
- **Seed Rental Classes**:
  - Endpoint: `cs.iot.ptshome.com/api/v1/data/14223767938169215907`
  - Supports: GET/POST/PUT/PATCH
  - GET Parameters: `filter[]`, `offset`, `limit`, `sort[]`, `returncount`

### Logic

- **Data Sync**:
  - Full refresh: Deletes and re-fetches all data.
  - Incremental refresh: Updates based on `since_date`.
- **Tab 1 (Rental Inventory)**: Groups items by category/subcategory, counts items by status.
- **Tab 2 (Open Contracts)**: Lists items on rent by contract, expandable to common name aggregate and item list.
- **Tab 4 (Laundry Contracts)**: Filters for contracts starting with "L" or "l", same structure as Tab 2.
- **Tab 5 (Resale/Packs)**: Manages items in specific `bin_location` values, updates via API.
- **Categories**: Allows manual mapping of rental classes to categories/subcategories.

