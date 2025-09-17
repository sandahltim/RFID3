# Transactions API Endpoints - Scan Events and Activity Logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.models import get_db, Transaction
from app.schemas.transactions import TransactionResponse, TransactionCreate, ScanEventCreate

router = APIRouter()

@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tag_id: Optional[str] = Query(None),
    scan_type: Optional[str] = Query(None),
    scan_by: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """List transactions with filtering and pagination"""

    query = db.query(Transaction)

    # Apply filters
    if tag_id:
        query = query.filter(Transaction.tag_id == tag_id)
    if scan_type:
        query = query.filter(Transaction.scan_type == scan_type)
    if scan_by:
        query = query.filter(Transaction.scan_by == scan_by)
    if start_date:
        query = query.filter(Transaction.scan_date >= start_date)
    if end_date:
        query = query.filter(Transaction.scan_date <= end_date)

    # Order by scan_date descending (most recent first)
    query = query.order_by(Transaction.scan_date.desc())

    # Apply pagination
    transactions = query.offset(skip).limit(limit).all()

    return transactions

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Get specific transaction by ID"""

    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return transaction

@router.post("/", response_model=TransactionResponse, status_code=201)
async def create_transaction(transaction_data: TransactionCreate, db: Session = Depends(get_db)):
    """Create new transaction"""

    # Create new transaction
    transaction = Transaction(**transaction_data.dict())
    transaction.date_created = datetime.now()
    transaction.ops_created_at = datetime.now()

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction

@router.get("/item/{tag_id}", response_model=List[TransactionResponse])
async def get_item_transactions(
    tag_id: str,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=500)
):
    """Get transaction history for specific item"""

    transactions = (
        db.query(Transaction)
        .filter(Transaction.tag_id == tag_id)
        .order_by(Transaction.scan_date.desc())
        .limit(limit)
        .all()
    )

    return transactions

@router.post("/scan", response_model=TransactionResponse, status_code=201)
async def record_scan_event(scan_data: ScanEventCreate, db: Session = Depends(get_db)):
    """Record a scan event (specialized transaction endpoint)"""

    # Create transaction from scan event
    transaction = Transaction(
        tag_id=scan_data.tag_id,
        scan_type=scan_data.scan_type,
        scan_date=datetime.now(),
        scan_by=scan_data.scan_by,
        bin_location=scan_data.location,
        quality=scan_data.quality_assessment.quality if scan_data.quality_assessment else None,
        longitude=scan_data.gps.longitude if scan_data.gps else None,
        latitude=scan_data.gps.latitude if scan_data.gps else None,
        notes=scan_data.quality_assessment.notes if scan_data.quality_assessment else None,

        # Condition flags
        dirty_or_mud=scan_data.quality_assessment.dirty_or_mud if scan_data.quality_assessment else False,
        service_required=scan_data.quality_assessment.service_required if scan_data.quality_assessment else False,

        date_created=datetime.now(),
        ops_created_at=datetime.now()
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # Also update the item's last scan information
    from app.models import Item
    item = db.query(Item).filter(Item.tag_id == scan_data.tag_id).first()
    if item:
        item.date_last_scanned = datetime.now()
        item.last_scanned_by = scan_data.scan_by
        if scan_data.location:
            item.bin_location = scan_data.location
        if scan_data.quality_assessment and scan_data.quality_assessment.quality:
            item.quality = scan_data.quality_assessment.quality
        if scan_data.gps:
            item.longitude = scan_data.gps.longitude
            item.latitude = scan_data.gps.latitude

        item.ops_updated_at = datetime.now()
        db.commit()

    return transaction

@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Delete transaction"""

    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(transaction)
    db.commit()