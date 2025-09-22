"""
Manual sync endpoints for manager database and RFIDpro
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.database.session import get_db, get_manager_db
import httpx
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class SyncRequest(BaseModel):
    source: str  # "manager_db" or "rfidpro"
    table: Optional[str] = None  # specific table or all
    force: bool = False  # force full sync vs incremental

class SyncResponse(BaseModel):
    status: str
    source: str
    records_processed: int
    records_updated: int
    timestamp: datetime
    message: str

@router.post("/sync/manager", response_model=SyncResponse)
async def sync_from_manager(
    sync_req: SyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    manager_db: Session = Depends(get_manager_db)
):
    """Manually sync data from manager database"""

    if sync_req.source != "manager_db":
        raise HTTPException(status_code=400, detail="Invalid source for this endpoint")

    timestamp = datetime.utcnow()
    records_processed = 0
    records_updated = 0

    try:
        # Sync items from id_item_master
        if not sync_req.table or sync_req.table == "items":
            # Get items from manager database (excluding financial fields)
            query = """
                SELECT tag_id, serial_number, client_name, rental_class_num,
                       common_name, quality, bin_location, status,
                       last_contract_num, last_scanned_by, notes, status_notes,
                       longitude, latitude, date_last_scanned, date_created,
                       date_updated, home_store, current_store, identifier_type,
                       item_num, manufacturer
                FROM id_item_master
            """

            if not sync_req.force:
                # Incremental sync - only recent changes
                query += " WHERE date_updated > DATE_SUB(NOW(), INTERVAL 7 DAY)"

            result = manager_db.execute(text(query))
            items = result.fetchall()

            for item in items:
                records_processed += 1

                # Check if item exists in operations database
                existing = db.query(text(
                    "SELECT tag_id FROM ops_items WHERE tag_id = :tag_id"
                )).params(tag_id=item[0]).first()

                if existing:
                    # Update existing item
                    update_query = text("""
                        UPDATE ops_items SET
                            serial_number = :serial_number,
                            client_name = :client_name,
                            rental_class_num = :rental_class_num,
                            common_name = :common_name,
                            quality = :quality,
                            bin_location = :bin_location,
                            status = :status,
                            last_contract_num = :last_contract_num,
                            last_scanned_by = :last_scanned_by,
                            notes = :notes,
                            status_notes = :status_notes,
                            longitude = :longitude,
                            latitude = :latitude,
                            date_last_scanned = :date_last_scanned,
                            date_updated = :date_updated,
                            home_store = :home_store,
                            current_store = :current_store,
                            identifier_type = :identifier_type,
                            item_num = :item_num,
                            manufacturer = :manufacturer,
                            last_sync_from_manager = :sync_time
                        WHERE tag_id = :tag_id
                    """)
                else:
                    # Insert new item
                    update_query = text("""
                        INSERT INTO ops_items (
                            tag_id, serial_number, client_name, rental_class_num,
                            common_name, quality, bin_location, status,
                            last_contract_num, last_scanned_by, notes, status_notes,
                            longitude, latitude, date_last_scanned, date_created,
                            date_updated, home_store, current_store, identifier_type,
                            item_num, manufacturer, last_sync_from_manager
                        ) VALUES (
                            :tag_id, :serial_number, :client_name, :rental_class_num,
                            :common_name, :quality, :bin_location, :status,
                            :last_contract_num, :last_scanned_by, :notes, :status_notes,
                            :longitude, :latitude, :date_last_scanned, :date_created,
                            :date_updated, :home_store, :current_store, :identifier_type,
                            :item_num, :manufacturer, :sync_time
                        )
                    """)

                db.execute(update_query.params(
                    tag_id=item[0],
                    serial_number=item[1],
                    client_name=item[2],
                    rental_class_num=item[3],
                    common_name=item[4],
                    quality=item[5],
                    bin_location=item[6],
                    status=item[7],
                    last_contract_num=item[8],
                    last_scanned_by=item[9],
                    notes=item[10],
                    status_notes=item[11],
                    longitude=item[12],
                    latitude=item[13],
                    date_last_scanned=item[14],
                    date_created=item[15],
                    date_updated=item[16],
                    home_store=item[17],
                    current_store=item[18],
                    identifier_type=item[19],
                    item_num=item[20],
                    manufacturer=item[21],
                    sync_time=timestamp
                ))
                records_updated += 1

            db.commit()

        return SyncResponse(
            status="completed",
            source="manager_db",
            records_processed=records_processed,
            records_updated=records_updated,
            timestamp=timestamp,
            message=f"Successfully synced {records_updated} items from manager database"
        )

    except Exception as e:
        logger.error(f"Sync error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.post("/sync/rfidpro", response_model=SyncResponse)
async def sync_from_rfidpro(
    sync_req: SyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Manually sync data from RFIDpro API"""

    if sync_req.source != "rfidpro":
        raise HTTPException(status_code=400, detail="Invalid source for this endpoint")

    # This is a placeholder for RFIDpro sync
    # You'll need to implement the actual RFIDpro API calls

    return SyncResponse(
        status="not_implemented",
        source="rfidpro",
        records_processed=0,
        records_updated=0,
        timestamp=datetime.utcnow(),
        message="RFIDpro sync not yet implemented"
    )

@router.get("/sync/status")
async def get_sync_status(db: Session = Depends(get_db)):
    """Get last sync status for all sources"""

    # Get last sync times
    query = text("""
        SELECT 'manager_db' as source, MAX(last_sync_from_manager) as last_sync,
               COUNT(*) as total_records
        FROM ops_items
        WHERE last_sync_from_manager IS NOT NULL
    """)

    result = db.execute(query).first()

    return {
        "manager_db": {
            "last_sync": result[1] if result else None,
            "total_records": result[2] if result else 0
        },
        "rfidpro": {
            "last_sync": None,
            "total_records": 0
        }
    }