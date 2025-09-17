# Equipment API Endpoints - POS Equipment Data
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models import get_db, Equipment
from app.schemas.equipment import EquipmentResponse, EquipmentCreate, EquipmentUpdate

router = APIRouter()

@router.get("/", response_model=List[EquipmentResponse])
async def list_equipment(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    store: Optional[str] = Query(None),
    inactive: Optional[bool] = Query(None),
    manufacturer: Optional[str] = Query(None),
    department: Optional[str] = Query(None)
):
    """List equipment with filtering and pagination"""

    query = db.query(Equipment)

    # Apply filters
    if category:
        query = query.filter(Equipment.category == category)
    if store:
        query = query.filter(Equipment.current_store == store)
    if inactive is not None:
        query = query.filter(Equipment.inactive == inactive)
    if manufacturer:
        query = query.filter(Equipment.manf.ilike(f"%{manufacturer}%"))
    if department:
        query = query.filter(Equipment.department == department)

    # Apply pagination
    equipment = query.offset(skip).limit(limit).all()

    return equipment

@router.get("/{item_num}", response_model=EquipmentResponse)
async def get_equipment(item_num: str, db: Session = Depends(get_db)):
    """Get specific equipment by item number"""

    equipment = db.query(Equipment).filter(Equipment.item_num == item_num).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    return equipment

@router.post("/", response_model=EquipmentResponse, status_code=201)
async def create_equipment(equipment_data: EquipmentCreate, db: Session = Depends(get_db)):
    """Create new equipment"""

    # Check if equipment already exists
    existing = db.query(Equipment).filter(Equipment.item_num == equipment_data.item_num).first()
    if existing:
        raise HTTPException(status_code=400, detail="Equipment with this item number already exists")

    # Create new equipment
    equipment = Equipment(**equipment_data.dict())
    equipment.ops_created_at = datetime.now()

    db.add(equipment)
    db.commit()
    db.refresh(equipment)

    return equipment

@router.put("/{item_num}", response_model=EquipmentResponse)
async def update_equipment(item_num: str, equipment_data: EquipmentUpdate, db: Session = Depends(get_db)):
    """Update equipment"""

    equipment = db.query(Equipment).filter(Equipment.item_num == item_num).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    # Update fields
    for field, value in equipment_data.dict(exclude_unset=True).items():
        setattr(equipment, field, value)

    equipment.ops_updated_at = datetime.now()

    db.commit()
    db.refresh(equipment)

    return equipment

@router.delete("/{item_num}", status_code=204)
async def delete_equipment(item_num: str, db: Session = Depends(get_db)):
    """Delete equipment"""

    equipment = db.query(Equipment).filter(Equipment.item_num == item_num).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    db.delete(equipment)
    db.commit()

@router.get("/categories/list")
async def list_categories(db: Session = Depends(get_db)):
    """Get list of all equipment categories"""

    categories = db.query(Equipment.category).distinct().filter(Equipment.category.isnot(None)).all()
    return [cat[0] for cat in categories if cat[0]]

@router.get("/stores/list")
async def list_stores(db: Session = Depends(get_db)):
    """Get list of all stores"""

    stores = db.query(Equipment.current_store).distinct().filter(Equipment.current_store.isnot(None)).all()
    return [store[0] for store in stores if store[0]]

@router.get("/manufacturers/list")
async def list_manufacturers(db: Session = Depends(get_db)):
    """Get list of all manufacturers"""

    manufacturers = db.query(Equipment.manf).distinct().filter(Equipment.manf.isnot(None)).all()
    return [manf[0] for manf in manufacturers if manf[0]]