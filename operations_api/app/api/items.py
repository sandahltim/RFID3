"""
Items API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.database.session import get_db
from app.models.items import OpsItem

router = APIRouter()

# Pydantic models
class ItemBase(BaseModel):
    tag_id: str
    common_name: str
    rental_class_num: Optional[str] = None
    status: str = "available"
    bin_location: Optional[str] = None
    current_store: Optional[str] = None
    identifier_type: str = "RFID"

class ItemCreate(ItemBase):
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    notes: Optional[str] = None

class ItemUpdate(BaseModel):
    status: Optional[str] = None
    bin_location: Optional[str] = None
    current_store: Optional[str] = None
    quality: Optional[str] = None
    notes: Optional[str] = None
    status_notes: Optional[str] = None

class ItemResponse(ItemBase):
    item_num: Optional[int]
    last_scanned_by: Optional[str]
    date_last_scanned: Optional[datetime]
    date_created: Optional[datetime]
    date_updated: Optional[datetime]

    class Config:
        from_attributes = True

@router.get("/items", response_model=List[ItemResponse])
async def get_items(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    store: Optional[str] = Query(None),
    identifier_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0)
):
    """Get list of items with optional filters"""
    query = db.query(OpsItem)

    if status:
        query = query.filter(OpsItem.status == status)
    if store:
        query = query.filter(OpsItem.current_store == store)
    if identifier_type:
        query = query.filter(OpsItem.identifier_type == identifier_type)

    items = query.offset(offset).limit(limit).all()
    return items

@router.get("/items/{tag_id}", response_model=ItemResponse)
async def get_item(tag_id: str, db: Session = Depends(get_db)):
    """Get specific item by tag_id"""
    item = db.query(OpsItem).filter(OpsItem.tag_id == tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    """Add new item to system"""
    # Check if item already exists
    existing = db.query(OpsItem).filter(OpsItem.tag_id == item.tag_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Item already exists")

    db_item = OpsItem(
        **item.dict(),
        date_created=datetime.utcnow(),
        date_updated=datetime.utcnow()
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/items/{tag_id}", response_model=ItemResponse)
async def update_item(
    tag_id: str,
    item_update: ItemUpdate,
    db: Session = Depends(get_db)
):
    """Update item details"""
    item = db.query(OpsItem).filter(OpsItem.tag_id == tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = item_update.dict(exclude_unset=True)
    update_data["date_updated"] = datetime.utcnow()

    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item

@router.delete("/items/{tag_id}")
async def delete_item(tag_id: str, db: Session = Depends(get_db)):
    """Remove item from system"""
    item = db.query(OpsItem).filter(OpsItem.tag_id == tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return {"message": "Item deleted successfully"}