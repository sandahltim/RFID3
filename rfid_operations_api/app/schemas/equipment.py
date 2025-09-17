# Equipment Pydantic Schemas
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

class EquipmentBase(BaseModel):
    """Base equipment schema"""
    item_num: str
    pos_item_num: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    department: Optional[str] = None
    current_store: Optional[str] = None
    home_store: Optional[str] = None
    manf: Optional[str] = None
    model_year: Optional[str] = None
    inactive: Optional[bool] = False

class EquipmentCreate(EquipmentBase):
    """Schema for creating equipment"""
    pass

class EquipmentUpdate(BaseModel):
    """Schema for updating equipment"""
    name: Optional[str] = None
    category: Optional[str] = None
    department: Optional[str] = None
    current_store: Optional[str] = None
    qty: Optional[int] = None
    inactive: Optional[bool] = None

    model_config = ConfigDict(extra='allow')

class EquipmentResponse(EquipmentBase):
    """Schema for equipment responses"""
    # Additional fields for response
    loc: Optional[str] = None
    qty: Optional[int] = None
    type_desc: Optional[str] = None
    serial_number: Optional[str] = None
    weight: Optional[Decimal] = None
    setup_time: Optional[Decimal] = None
    barcode: Optional[str] = None
    retail_price: Optional[Decimal] = None

    # Sync metadata
    last_sync_from_manager: Optional[datetime] = None
    ops_created_at: Optional[datetime] = None
    ops_updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)