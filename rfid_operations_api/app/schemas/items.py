# Items Pydantic Schemas
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

class ItemBase(BaseModel):
    """Base item schema"""
    tag_id: str
    rental_class_num: Optional[str] = None
    common_name: Optional[str] = None
    status: Optional[str] = None
    current_store: Optional[str] = None
    quality: Optional[str] = None
    identifier_type: Optional[str] = None

class ItemCreate(ItemBase):
    """Schema for creating items"""
    serial_number: Optional[str] = None
    home_store: Optional[str] = None
    manufacturer: Optional[str] = None

class ItemUpdate(BaseModel):
    """Schema for updating items"""
    rental_class_num: Optional[str] = None
    common_name: Optional[str] = None
    status: Optional[str] = None
    current_store: Optional[str] = None
    bin_location: Optional[str] = None
    quality: Optional[str] = None
    client_name: Optional[str] = None
    last_contract_num: Optional[str] = None
    last_scanned_by: Optional[str] = None
    notes: Optional[str] = None
    status_notes: Optional[str] = None

class ItemStatusUpdate(BaseModel):
    """Schema for quick status updates"""
    status: Optional[str] = None
    current_store: Optional[str] = None
    bin_location: Optional[str] = None
    quality: Optional[str] = None
    last_scanned_by: Optional[str] = None
    notes: Optional[str] = None

class ItemResponse(ItemBase):
    """Schema for item responses"""
    # Additional fields for response
    item_num: Optional[int] = None
    serial_number: Optional[str] = None
    client_name: Optional[str] = None
    last_contract_num: Optional[str] = None
    bin_location: Optional[str] = None
    home_store: Optional[str] = None
    last_scanned_by: Optional[str] = None
    date_last_scanned: Optional[datetime] = None
    longitude: Optional[Decimal] = None
    latitude: Optional[Decimal] = None
    notes: Optional[str] = None
    status_notes: Optional[str] = None
    manufacturer: Optional[str] = None

    # Timestamps
    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None

    # Sync metadata
    last_sync_from_manager: Optional[datetime] = None
    ops_created_at: Optional[datetime] = None
    ops_updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)