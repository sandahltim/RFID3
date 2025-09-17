# Transactions Pydantic Schemas
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal

class QualityAssessment(BaseModel):
    """Quality assessment sub-schema"""
    quality: Optional[str] = None
    dirty_or_mud: Optional[bool] = False
    service_required: Optional[bool] = False
    notes: Optional[str] = None

class GPS(BaseModel):
    """GPS coordinates sub-schema"""
    latitude: float
    longitude: float

class TransactionBase(BaseModel):
    """Base transaction schema"""
    tag_id: str
    scan_type: str
    scan_by: Optional[str] = None
    common_name: Optional[str] = None

class TransactionCreate(TransactionBase):
    """Schema for creating transactions"""
    contract_number: Optional[str] = None
    scan_date: Optional[datetime] = None
    client_name: Optional[str] = None
    bin_location: Optional[str] = None
    status: Optional[str] = None
    quality: Optional[str] = None
    notes: Optional[str] = None

class ScanEventCreate(BaseModel):
    """Schema for scan events (specialized transaction)"""
    tag_id: str
    scan_type: str
    scan_by: str
    location: Optional[str] = None
    quality_assessment: Optional[QualityAssessment] = None
    gps: Optional[GPS] = None

class TransactionResponse(TransactionBase):
    """Schema for transaction responses"""
    id: int
    contract_number: Optional[str] = None
    scan_date: Optional[datetime] = None
    client_name: Optional[str] = None
    bin_location: Optional[str] = None
    status: Optional[str] = None
    quality: Optional[str] = None
    location_of_repair: Optional[str] = None

    # GPS coordinates
    longitude: Optional[Decimal] = None
    latitude: Optional[Decimal] = None

    # Condition flags
    dirty_or_mud: Optional[bool] = None
    leaves: Optional[bool] = None
    oil: Optional[bool] = None
    mold: Optional[bool] = None
    stain: Optional[bool] = None
    oxidation: Optional[bool] = None
    other: Optional[str] = None
    rip_or_tear: Optional[bool] = None
    sewing_repair_needed: Optional[bool] = None
    grommet: Optional[bool] = None
    rope: Optional[bool] = None
    buckle: Optional[bool] = None
    wet: Optional[bool] = None
    service_required: Optional[bool] = None

    # Additional metadata
    serial_number: Optional[str] = None
    rental_class_num: Optional[str] = None
    notes: Optional[str] = None
    repair_estimate: Optional[str] = None
    maintenance_performed: Optional[str] = None

    # Timestamps
    date_created: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    ops_created_at: Optional[datetime] = None
    ops_updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)