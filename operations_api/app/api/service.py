"""
Service and Laundry operations API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.database.session import get_db
from app.models.items import OpsItem
import json
import csv
import io

router = APIRouter()

# Pydantic models
class ServiceItemResponse(BaseModel):
    tag_id: str
    common_name: str
    crew: Optional[str]
    status: str
    quality: Optional[str]
    identifier_type: str
    service_required: bool
    dirty_mud: bool = False
    oil: bool = False
    rip_tear: bool = False
    sewing_repair: bool = False
    leaves: bool = False
    mold: bool = False
    stain: bool = False
    oxidation: bool = False
    grommet: bool = False
    rope: bool = False
    buckle: bool = False
    wet: bool = False

class LaundryContractResponse(BaseModel):
    id: int
    contract_number: str
    status: str
    created_at: datetime
    finalized_at: Optional[datetime]
    returned_at: Optional[datetime]
    item_count: int
    hand_counted: int
    items: List[dict] = []

class ServiceCompleteRequest(BaseModel):
    service_types: dict
    notes: Optional[str] = ""

class TagPrintRequest(BaseModel):
    tag_ids: List[str]
    quantity: int = 1

# In-memory storage for laundry contracts (should be in database)
laundry_contracts = {}
next_contract_id = 1

def get_crew_assignment(common_name: str) -> str:
    """Determine crew assignment based on item type"""
    name_lower = common_name.lower() if common_name else ""
    if 'tent' in name_lower or 'pole' in name_lower or 'stake' in name_lower:
        return 'Tent'
    elif 'linen' in name_lower or 'napkin' in name_lower or 'tablecloth' in name_lower:
        return 'Linen'
    else:
        return 'Service Dept'

@router.get("/service/items", response_model=List[ServiceItemResponse])
async def get_service_items(
    db: Session = Depends(get_db),
    crew: Optional[str] = Query(None),
    status: str = Query('service')
):
    """Get items in service queue"""
    query = db.query(OpsItem).filter(OpsItem.status == status)
    items = query.all()

    service_items = []
    for item in items:
        item_crew = get_crew_assignment(item.common_name)

        # Filter by crew if specified
        if crew and item_crew != crew:
            continue

        # Parse service requirements from notes (simplified)
        service_required = bool(item.notes and 'service' in item.notes.lower())

        service_items.append(ServiceItemResponse(
            tag_id=item.tag_id,
            common_name=item.common_name or "Unknown Item",
            crew=item_crew,
            status=item.status,
            quality=item.quality,
            identifier_type=item.identifier_type or "RFID",
            service_required=service_required,
            dirty_mud='mud' in (item.notes or '').lower(),
            oil='oil' in (item.notes or '').lower(),
            rip_tear='tear' in (item.notes or '').lower() or 'rip' in (item.notes or '').lower(),
            sewing_repair='sewing' in (item.notes or '').lower()
        ))

    return service_items

@router.post("/service/{tag_id}/complete")
async def complete_service(
    tag_id: str,
    request: ServiceCompleteRequest,
    db: Session = Depends(get_db)
):
    """Mark service as complete for an item"""
    item = db.query(OpsItem).filter(OpsItem.tag_id == tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Update status to available
    item.status = 'available'
    item.status_notes = f"Service completed: {request.notes}"
    item.date_updated = datetime.utcnow()

    # Clear service flags in notes
    item.notes = f"Service completed on {datetime.utcnow().strftime('%Y-%m-%d')}"

    db.commit()
    return {"message": "Service completed", "tag_id": tag_id}

@router.post("/service/generate-tags")
async def generate_tag_csv(request: TagPrintRequest):
    """Generate CSV file for Zebra printer"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Zebra printer CSV format
    writer.writerow(['TagID', 'ItemName', 'Quantity', 'PrintDate'])

    for tag_id in request.tag_ids:
        for _ in range(request.quantity):
            writer.writerow([
                tag_id,
                f"RFID Tag {tag_id}",
                1,
                datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=rfid_tags_{datetime.utcnow().timestamp()}.csv"}
    )

@router.post("/service/update-synced")
async def update_synced_status(
    data: dict,
    db: Session = Depends(get_db)
):
    """Mark items as synced after tag printing"""
    tag_ids = data.get('tag_ids', [])

    updated = db.query(OpsItem).filter(
        OpsItem.tag_id.in_(tag_ids)
    ).update(
        {OpsItem.last_sync_from_manager: datetime.utcnow()},
        synchronize_session=False
    )

    db.commit()
    return {"message": f"Marked {updated} items as synced"}

# Laundry Contract endpoints
@router.get("/service/laundry-contracts", response_model=List[LaundryContractResponse])
async def get_laundry_contracts(db: Session = Depends(get_db)):
    """Get all laundry contracts"""
    contracts = []

    for contract_id, contract_data in laundry_contracts.items():
        contracts.append(LaundryContractResponse(
            id=contract_id,
            contract_number=contract_data['contract_number'],
            status=contract_data['status'],
            created_at=contract_data['created_at'],
            finalized_at=contract_data.get('finalized_at'),
            returned_at=contract_data.get('returned_at'),
            item_count=len(contract_data.get('scanned_items', [])),
            hand_counted=len(contract_data.get('hand_counted_items', [])),
            items=contract_data.get('all_items', [])
        ))

    return sorted(contracts, key=lambda x: x.created_at, reverse=True)

@router.post("/service/laundry-contract")
async def create_laundry_contract(data: dict):
    """Create a new laundry contract"""
    global next_contract_id

    contract_id = next_contract_id
    next_contract_id += 1

    laundry_contracts[contract_id] = {
        'contract_number': f"L-{datetime.utcnow().strftime('%Y%m%d')}-{contract_id:04d}",
        'status': 'PreWash Count',
        'created_at': datetime.utcnow(),
        'scanned_items': [],
        'hand_counted_items': [],
        'all_items': [],
        'notes': data.get('notes', '')
    }

    return {"id": contract_id, "contract_number": laundry_contracts[contract_id]['contract_number']}

@router.post("/service/laundry-contract/{contract_id}/finalize")
async def finalize_laundry_contract(contract_id: int):
    """Finalize contract and send to laundry"""
    if contract_id not in laundry_contracts:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract = laundry_contracts[contract_id]
    if contract['status'] != 'PreWash Count':
        raise HTTPException(status_code=400, detail="Contract already finalized")

    contract['status'] = 'Sent to Laundry'
    contract['finalized_at'] = datetime.utcnow()

    return {"message": "Contract finalized", "contract_id": contract_id}

@router.post("/service/laundry-contract/{contract_id}/returned")
async def mark_laundry_returned(contract_id: int):
    """Mark contract as returned from laundry"""
    if contract_id not in laundry_contracts:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract = laundry_contracts[contract_id]
    if contract['status'] != 'Sent to Laundry':
        raise HTTPException(status_code=400, detail="Contract not sent to laundry")

    contract['status'] = 'Returned'
    contract['returned_at'] = datetime.utcnow()

    return {"message": "Contract marked as returned", "contract_id": contract_id}

@router.post("/service/laundry-contract/{contract_id}/reactivate")
async def reactivate_laundry_contract(contract_id: int):
    """Reactivate a returned contract"""
    if contract_id not in laundry_contracts:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract = laundry_contracts[contract_id]
    contract['status'] = 'PreWash Count'
    contract['returned_at'] = None
    contract['finalized_at'] = None

    return {"message": "Contract reactivated", "contract_id": contract_id}

@router.post("/service/hand-counted-item")
async def add_hand_counted_item(data: dict):
    """Add hand-counted item to laundry contract"""
    contract_id = data.get('contract_id')

    # Handle 'new' contract ID
    if contract_id == 'new':
        global next_contract_id
        contract_id = next_contract_id
        next_contract_id += 1

        laundry_contracts[contract_id] = {
            'contract_number': f"L-{datetime.utcnow().strftime('%Y%m%d')}-{contract_id:04d}",
            'status': 'PreWash Count',
            'created_at': datetime.utcnow(),
            'scanned_items': [],
            'hand_counted_items': [],
            'all_items': [],
            'notes': ''
        }
    elif contract_id not in laundry_contracts:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract = laundry_contracts[contract_id]

    hand_counted_item = {
        'common_name': data.get('common_name'),
        'quantity': data.get('quantity', 1),
        'notes': data.get('notes', ''),
        'is_hand_counted': True
    }

    contract['hand_counted_items'].append(hand_counted_item)
    contract['all_items'].append(hand_counted_item)

    return {
        "message": "Hand-counted item added",
        "contract_id": contract_id,
        "item": hand_counted_item
    }