# Items API Endpoints - RFID Items Real-time Operations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models import get_db, Item
from app.schemas.items import ItemResponse, ItemCreate, ItemUpdate, ItemStatusUpdate

router = APIRouter()

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