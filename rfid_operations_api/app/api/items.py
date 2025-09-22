# Items API Endpoints - RFID Items Real-time Operations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models import get_db, Item
from app.schemas.items import ItemResponse, ItemCreate, ItemUpdate, ItemStatusUpdate

router = APIRouter()

@router.get("/dashboard-stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics using hybrid approach - RFID live data + POS contracts"""
    from sqlalchemy import text

    # HYBRID APPROACH: Combine live RFID status with POS contract data

    # 1. Check RFID live status first (most current)
    rfid_on_rent_sql = """
    SELECT COUNT(DISTINCT im.tag_id) as count
    FROM id_item_master im
    WHERE im.status = 'On Rent'
    """

    # 2. Also check POS for items on active contracts (may catch items RFID missed)
    pos_on_rent_sql = """
    SELECT COUNT(DISTINCT pti.item_number) as count
    FROM pos_transaction_items pti
    JOIN pos_transactions pt ON pti.contract_number = pt.contract_no
    WHERE pt.contract_date IS NOT NULL
    AND pt.contract_date <= NOW()  -- Contract has started
    AND (pt.completed_date IS NULL OR pt.completed_date > NOW())
    AND (pt.actual_pickup_date IS NULL OR pt.actual_pickup_date > NOW())
    AND pt.status NOT IN ('CANCELLED', 'VOID', 'CLOSED')
    """

    # 3. Get items marked available in RFID but check against POS reservations
    available_sql = """
    SELECT COUNT(DISTINCT im.tag_id) as count
    FROM id_item_master im
    WHERE im.status = 'Ready to Rent'
    AND (im.item_num IS NULL OR im.item_num NOT IN (
        -- Check POS for current rentals
        SELECT DISTINCT pti.item_number
        FROM pos_transaction_items pti
        JOIN pos_transactions pt ON pti.contract_number = pt.contract_no
        WHERE pt.contract_date <= NOW()
        AND (pt.completed_date IS NULL OR pt.completed_date > NOW())
        AND pt.status NOT IN ('CANCELLED', 'VOID', 'CLOSED')
    ))
    AND (im.item_num IS NULL OR im.item_num NOT IN (
        -- Check POS for future reservations
        SELECT DISTINCT pti.item_number
        FROM pos_transaction_items pti
        JOIN pos_transactions pt ON pti.contract_number = pt.contract_no
        WHERE pt.promised_delivery_date > NOW()
        AND (pt.completed_date IS NULL OR pt.completed_date > NOW())
        AND pt.status NOT IN ('CANCELLED', 'VOID', 'CLOSED')
    ))
    """

    # 4. Check both RFID transactions and POS for future reservations
    reserved_sql = """
    SELECT COUNT(*) as total FROM (
        -- Items with future reservations in POS
        SELECT DISTINCT pti.item_number as item_id
        FROM pos_transaction_items pti
        JOIN pos_transactions pt ON pti.contract_number = pt.contract_no
        WHERE pt.promised_delivery_date > NOW()
        AND pt.contract_date > NOW()  -- Not yet started
        AND pt.status NOT IN ('CANCELLED', 'VOID', 'CLOSED')

        UNION

        -- Items with future reservations in RFID transactions
        SELECT DISTINCT it.tag_id as item_id
        FROM id_transactions it
        WHERE it.scan_type = 'reservation'
        AND it.scan_date > NOW()
        AND it.status = 'active'
    ) combined_reservations
    """

    # 5. Service status from RFID (most current for maintenance)
    service_sql = """
    SELECT COUNT(*) as count
    FROM id_item_master
    WHERE status IN ('Repair', 'Needs to be Inspected', 'Wet', 'Missing')
    """

    # 6. Today's RFID scan activity (real-time)
    today_scans_sql = """
    SELECT COUNT(*) as count
    FROM id_transactions
    WHERE DATE(scan_date) = CURDATE()
    """

    # 7. Active contracts from both sources
    active_contracts_sql = """
    SELECT COUNT(*) as total FROM (
        -- POS active contracts
        SELECT DISTINCT contract_no as contract_id
        FROM pos_transactions
        WHERE contract_date <= NOW()
        AND (completed_date IS NULL OR completed_date > NOW())
        AND status NOT IN ('CANCELLED', 'VOID', 'CLOSED')

        UNION

        -- RFID active contracts (if tracked separately)
        SELECT DISTINCT contract_number as contract_id
        FROM id_transactions
        WHERE scan_type IN ('checkout', 'delivery')
        AND status = 'active'
        AND contract_number IS NOT NULL
    ) combined_contracts
    """

    # 8. Pending returns - items overdue
    pending_returns_sql = """
    SELECT COUNT(*) as total FROM (
        -- POS overdue
        SELECT DISTINCT pt.contract_no as contract_id
        FROM pos_transactions pt
        WHERE pt.promised_pickup_date < NOW()
        AND pt.actual_pickup_date IS NULL
        AND pt.completed_date IS NULL
        AND pt.status NOT IN ('CANCELLED', 'VOID', 'CLOSED')

        UNION

        -- RFID overdue (if due dates tracked)
        SELECT DISTINCT im.last_contract_num as contract_id
        FROM id_item_master im
        WHERE im.status = 'On Rent'
        AND im.last_contract_num IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM pos_transactions pt
            WHERE pt.contract_no = im.last_contract_num
            AND pt.promised_pickup_date < NOW()
            AND pt.actual_pickup_date IS NULL
        )
    ) combined_overdue
    """

    # Execute all queries
    rfid_on_rent = db.execute(text(rfid_on_rent_sql)).fetchone()[0] or 0
    pos_on_rent = db.execute(text(pos_on_rent_sql)).fetchone()[0] or 0
    on_rent = max(rfid_on_rent, pos_on_rent)  # Take the higher count (more conservative)

    available = db.execute(text(available_sql)).fetchone()[0] or 0
    reserved = db.execute(text(reserved_sql)).fetchone()[0] or 0
    in_service = db.execute(text(service_sql)).fetchone()[0] or 0
    today_scans = db.execute(text(today_scans_sql)).fetchone()[0] or 0
    active_contracts = db.execute(text(active_contracts_sql)).fetchone()[0] or 0
    pending_returns = db.execute(text(pending_returns_sql)).fetchone()[0] or 0

    # Get data freshness indicators
    pos_freshness_sql = """
    SELECT MAX(last_modified_date) as last_update
    FROM pos_transactions
    """

    rfid_freshness_sql = """
    SELECT MAX(date_last_scanned) as last_scan
    FROM id_item_master
    WHERE date_last_scanned IS NOT NULL
    """

    pos_freshness = db.execute(text(pos_freshness_sql)).fetchone()[0]
    rfid_freshness = db.execute(text(rfid_freshness_sql)).fetchone()[0]

    # Get recent scans from id_item_master (last 50 scanned items)
    recent_scans_sql = """
    SELECT
        im.tag_id,
        im.common_name,
        im.date_last_scanned,
        im.status,
        im.last_contract_num,
        im.last_scanned_by,
        im.current_store
    FROM id_item_master im
    WHERE im.date_last_scanned IS NOT NULL
    ORDER BY im.date_last_scanned DESC
    LIMIT 10
    """

    recent_rows = db.execute(text(recent_scans_sql)).fetchall()
    recent_activity = []
    for row in recent_rows:
        # Calculate relative time
        if row.date_last_scanned:
            time_diff = datetime.now() - row.date_last_scanned
            if time_diff.days > 0:
                time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
            elif time_diff.seconds > 3600:
                hours = time_diff.seconds // 3600
                time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif time_diff.seconds > 60:
                minutes = time_diff.seconds // 60
                time_ago = f"{minutes} min ago"
            else:
                time_ago = "Just now"
        else:
            time_ago = "Unknown"

        # Determine activity type based on status change
        if row.status == 'On Rent':
            activity_type = 'checkout'
        elif row.status == 'Ready to Rent':
            activity_type = 'return'
        elif row.status in ('Repair', 'Needs to be Inspected', 'Wet'):
            activity_type = 'service'
        else:
            activity_type = 'scan'

        recent_activity.append({
            "id": row.tag_id,
            "type": activity_type,
            "item": row.common_name or f"Tag: {row.tag_id[:8]}...",
            "time": time_ago,
            "user": row.last_scanned_by or "System",
            "store": row.current_store,
            "contract": row.last_contract_num
        })

    return {
        "items_on_rent": on_rent,
        "items_available": available,
        "items_reserved": reserved,
        "items_in_service": in_service,
        "today_scans": today_scans,
        "active_contracts": active_contracts,
        "pending_returns": pending_returns,
        "recent_activity": recent_activity,
        "data_freshness": {
            "pos_last_update": pos_freshness.isoformat() if pos_freshness else None,
            "rfid_last_scan": rfid_freshness.isoformat() if rfid_freshness else None
        }
    }

@router.get("/", response_model=List[ItemResponse])
async def list_items(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    store: Optional[str] = Query(None),
    rental_class: Optional[str] = Query(None),
    quality: Optional[str] = Query(None),
    identifier_type: Optional[str] = Query(None),
    contract: Optional[str] = Query(None)
):
    """List RFID items with filtering and pagination"""

    query = db.query(Item)

    # Apply filters
    if status:
        query = query.filter(Item.status == status)
    if store:
        query = query.filter(Item.current_store == store)
    if rental_class:
        query = query.filter(Item.rental_class_num == rental_class)
    if quality:
        query = query.filter(Item.quality == quality)
    if identifier_type:
        query = query.filter(Item.identifier_type == identifier_type)
    if contract:
        query = query.filter(Item.last_contract_num == contract)

    # Apply pagination
    items = query.offset(skip).limit(limit).all()

    return items

@router.get("/{tag_id}", response_model=ItemResponse)
async def get_item(tag_id: str, db: Session = Depends(get_db)):
    """Get specific item by RFID tag ID"""

    item = db.query(Item).filter(Item.tag_id == tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return item

@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(item_data: ItemCreate, db: Session = Depends(get_db)):
    """Create new RFID item"""

    # Check if item already exists
    existing = db.query(Item).filter(Item.tag_id == item_data.tag_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Item with this tag ID already exists")

    # Create new item
    item = Item(**item_data.dict())
    item.date_created = datetime.now()
    item.ops_created_at = datetime.now()

    db.add(item)
    db.commit()
    db.refresh(item)

    return item

@router.put("/{tag_id}", response_model=ItemResponse)
async def update_item(tag_id: str, item_data: ItemUpdate, db: Session = Depends(get_db)):
    """Update RFID item"""

    item = db.query(Item).filter(Item.tag_id == tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Update fields
    for field, value in item_data.dict(exclude_unset=True).items():
        setattr(item, field, value)

    item.date_updated = datetime.now()
    item.ops_updated_at = datetime.now()

    db.commit()
    db.refresh(item)

    return item

@router.patch("/{tag_id}/status", response_model=ItemResponse)
async def update_item_status(tag_id: str, status_data: ItemStatusUpdate, db: Session = Depends(get_db)):
    """Update item status only (for real-time operations)"""

    item = db.query(Item).filter(Item.tag_id == tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Update status fields
    if status_data.status:
        item.status = status_data.status
    if status_data.current_store:
        item.current_store = status_data.current_store
    if status_data.bin_location:
        item.bin_location = status_data.bin_location
    if status_data.quality:
        item.quality = status_data.quality
    if status_data.last_scanned_by:
        item.last_scanned_by = status_data.last_scanned_by
    if status_data.notes:
        item.notes = status_data.notes

    item.date_last_scanned = datetime.now()
    item.date_updated = datetime.now()
    item.ops_updated_at = datetime.now()

    db.commit()
    db.refresh(item)

    return item

@router.patch("/{tag_id}/location", response_model=ItemResponse)
async def update_item_location(
    tag_id: str,
    store: Optional[str] = Query(None),
    bin_location: Optional[str] = Query(None),
    longitude: Optional[float] = Query(None),
    latitude: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    """Update item location only"""

    item = db.query(Item).filter(Item.tag_id == tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Update location fields
    if store:
        item.current_store = store
    if bin_location:
        item.bin_location = bin_location
    if longitude is not None:
        item.longitude = longitude
    if latitude is not None:
        item.latitude = latitude

    item.date_last_scanned = datetime.now()
    item.date_updated = datetime.now()
    item.ops_updated_at = datetime.now()

    db.commit()
    db.refresh(item)

    return item

@router.delete("/{tag_id}", status_code=204)
async def delete_item(tag_id: str, db: Session = Depends(get_db)):
    """Delete RFID item"""

    item = db.query(Item).filter(Item.tag_id == tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()

@router.get("/lookup/{identifier}")
async def lookup_item(identifier: str, db: Session = Depends(get_db)):
    """Lookup item by any identifier (RFID tag, barcode, serial, etc.)"""

    # Try different identifier types
    item = (
        db.query(Item)
        .filter(
            (Item.tag_id == identifier) |
            (Item.serial_number == identifier) |
            (Item.item_num == identifier)
        )
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return item

@router.get("/status/{status_value}")
async def get_items_by_status(status_value: str, db: Session = Depends(get_db)):
    """Get all items with specific status"""

    items = db.query(Item).filter(Item.status == status_value).all()
    return items