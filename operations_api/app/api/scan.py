"""
Scanning API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.database.session import get_db
from app.models.items import OpsItem

router = APIRouter()

class ScanRequest(BaseModel):
    tag_id: str
    scan_type: str = "check"  # check, checkin, checkout, maintenance
    location: Optional[str] = None
    scanned_by: str
    notes: Optional[str] = None
    quality: Optional[str] = None
    contract_number: Optional[str] = None

class ScanResponse(BaseModel):
    tag_id: str
    common_name: str
    status: str
    message: str
    timestamp: datetime

@router.post("/scan", response_model=ScanResponse)
async def scan_item(scan: ScanRequest, db: Session = Depends(get_db)):
    """Process a scan event"""

    # Find the item
    item = db.query(OpsItem).filter(OpsItem.tag_id == scan.tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Update item based on scan type
    timestamp = datetime.utcnow()
    message = ""

    if scan.scan_type == "checkout":
        if item.status != "available":
            raise HTTPException(status_code=400, detail=f"Item not available for checkout (status: {item.status})")
        item.status = "rented"
        item.last_contract_num = scan.contract_number
        message = "Item checked out successfully"

    elif scan.scan_type == "checkin":
        item.status = "available"
        if scan.quality:
            item.quality = scan.quality
        message = "Item checked in successfully"

    elif scan.scan_type == "maintenance":
        item.status = "maintenance"
        item.last_maintenance_date = timestamp
        message = "Item marked for maintenance"

    else:  # check
        message = f"Item scanned - Status: {item.status}"

    # Update scan metadata
    item.last_scanned_by = scan.scanned_by
    item.date_last_scanned = timestamp
    item.date_updated = timestamp

    if scan.location:
        item.bin_location = scan.location
    if scan.notes:
        item.status_notes = scan.notes

    db.commit()
    db.refresh(item)

    return ScanResponse(
        tag_id=item.tag_id,
        common_name=item.common_name,
        status=item.status,
        message=message,
        timestamp=timestamp
    )

@router.get("/scan/lookup/{identifier}")
async def lookup_item(identifier: str, db: Session = Depends(get_db)):
    """Lookup item by RFID or QR code"""

    # Try to find by tag_id
    item = db.query(OpsItem).filter(OpsItem.tag_id == identifier).first()

    # Try by serial number if not found
    if not item:
        item = db.query(OpsItem).filter(OpsItem.serial_number == identifier).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return {
        "tag_id": item.tag_id,
        "common_name": item.common_name,
        "status": item.status,
        "bin_location": item.bin_location,
        "current_store": item.current_store,
        "last_contract_num": item.last_contract_num,
        "quality": item.quality,
        "identifier_type": item.identifier_type,
        "last_scanned": item.date_last_scanned,
        "last_scanned_by": item.last_scanned_by
    }

@router.post("/scan/batch")
async def batch_scan(
    scans: list[ScanRequest],
    db: Session = Depends(get_db)
):
    """Process multiple scans at once"""
    results = []
    errors = []

    for scan in scans:
        try:
            result = await scan_item(scan, db)
            results.append(result)
        except HTTPException as e:
            errors.append({
                "tag_id": scan.tag_id,
                "error": e.detail
            })

    return {
        "successful": results,
        "failed": errors,
        "total": len(scans),
        "success_count": len(results),
        "error_count": len(errors)
    }