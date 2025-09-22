"""
Contracts API endpoints - Full integration with RFID and POS tables
Version: 1.0.0
Date: 2025-09-20
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from app.database.session import get_manager_db
from app.models.pos_tables import (
    POSTransactions, POSTransactionItems,
    POSCustomers, POSEquipment,
    ItemMaster, Transactions
)

router = APIRouter()

class ContractResponse(BaseModel):
    contract_no: str
    customer_no: Optional[str]
    customer_name: Optional[str]
    status: str
    contract_date: datetime
    delivery_date: Optional[datetime]
    pickup_date: Optional[datetime]
    store_no: str
    items: List[dict]
    rfid_items: List[dict]
    is_manual: bool = False

class ManualContractCreate(BaseModel):
    contract_no: Optional[str]  # Auto-generate if not provided
    customer_name: str
    delivery_date: datetime
    pickup_date: Optional[datetime]
    store_no: str
    notes: Optional[str]
    items: List[dict]  # List of item_numbers and quantities

class TagAssignment(BaseModel):
    contract_no: str
    item_number: str
    tag_id: str
    quantity: int = 1

@router.get("/contracts/open", response_model=List[ContractResponse])
async def get_open_contracts(
    db: Session = Depends(get_manager_db),
    store: Optional[str] = Query(None),
    days_ahead: int = Query(0, le=7)
):
    """Get open contracts for today + days ahead"""

    # Calculate date range
    start_date = datetime.now().date()
    end_date = (datetime.now() + timedelta(days=days_ahead)).date()

    # Query POS transactions
    query = db.query(POSTransactions).filter(
        and_(
            POSTransactions.status.in_(['O', 'Open', 'Pending']),
            POSTransactions.contract_date >= start_date,
            POSTransactions.contract_date <= end_date
        )
    )

    if store:
        query = query.filter(POSTransactions.store_no == store)

    contracts = query.all()
    results = []

    for contract in contracts:
        # Get customer info
        customer = None
        if contract.customer_no:
            customer = db.query(POSCustomers).filter(
                POSCustomers.cnum == contract.customer_no
            ).first()

        # Get contract items from POS
        pos_items = db.query(POSTransactionItems).filter(
            POSTransactionItems.contract_number == contract.contract_no
        ).all()

        # Get RFID items already assigned to this contract
        rfid_items = db.query(ItemMaster).filter(
            ItemMaster.last_contract_num == contract.contract_no
        ).all()

        # Format response
        results.append(ContractResponse(
            contract_no=contract.contract_no,
            customer_no=contract.customer_no,
            customer_name=customer.name if customer else None,
            status=contract.status,
            contract_date=contract.contract_date,
            delivery_date=contract.delivery_date,
            pickup_date=contract.pickup_date,
            store_no=contract.store_no,
            items=[{
                'item_number': item.item_number,
                'description': item.description_field,
                'quantity': item.quantity,
                'checked_out_qty': item.checked_out_qty or 0,
                'returned_qty': item.returned_qty or 0
            } for item in pos_items],
            rfid_items=[{
                'tag_id': item.tag_id,
                'common_name': item.common_name,
                'status': item.status,
                'rental_class_num': item.rental_class_num
            } for item in rfid_items],
            is_manual=contract.is_manual or False
        ))

    return results

@router.post("/contracts/manual", response_model=ContractResponse)
async def create_manual_contract(
    contract: ManualContractCreate,
    db: Session = Depends(get_manager_db)
):
    """Create manual contract (for POS lag situations)"""

    # Generate contract number if not provided
    if not contract.contract_no:
        contract.contract_no = f"M-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Create POS transaction entry
    new_transaction = POSTransactions(
        contract_no=contract.contract_no,
        customer_no=None,  # Will merge when POS updates
        store_no=contract.store_no,
        status='Open',
        contract_date=datetime.now(),
        delivery_date=contract.delivery_date,
        pickup_date=contract.pickup_date,
        is_manual=True,
        temp_id=contract.contract_no  # For merge tracking
    )

    db.add(new_transaction)

    # Add items to contract
    for item in contract.items:
        transaction_item = POSTransactionItems(
            contract_number=contract.contract_no,
            item_number=item['item_number'],
            quantity=item.get('quantity', 1),
            description_field=item.get('description', ''),
            checked_out_qty=0
        )
        db.add(transaction_item)

    db.commit()
    db.refresh(new_transaction)

    return ContractResponse(
        contract_no=new_transaction.contract_no,
        customer_no=None,
        customer_name=contract.customer_name,
        status='Open',
        contract_date=new_transaction.contract_date,
        delivery_date=new_transaction.delivery_date,
        pickup_date=new_transaction.pickup_date,
        store_no=new_transaction.store_no,
        items=contract.items,
        rfid_items=[],
        is_manual=True
    )

@router.post("/contracts/assign-tag")
async def assign_tag_to_contract(
    assignment: TagAssignment,
    db: Session = Depends(get_manager_db)
):
    """Assign RFID/QR tag to contract item"""

    # Check if tag exists
    item = db.query(ItemMaster).filter(
        ItemMaster.tag_id == assignment.tag_id
    ).first()

    if not item:
        # Create new item if doesn't exist
        item = ItemMaster(
            tag_id=assignment.tag_id,
            rental_class_num=assignment.item_number,
            common_name=f"Item {assignment.item_number}",
            status='rented',
            last_contract_num=assignment.contract_no,
            date_created=datetime.now(),
            date_updated=datetime.now(),
            identifier_type='RFID' if len(assignment.tag_id) == 24 else 'QR'
        )
        db.add(item)
    else:
        # Update existing item
        item.last_contract_num = assignment.contract_no
        item.status = 'rented'
        item.date_updated = datetime.now()

    # Create transaction record
    transaction = Transactions(
        contract_number=assignment.contract_no,
        tag_id=assignment.tag_id,
        scan_type='checkout',
        scan_date=datetime.now(),
        common_name=item.common_name,
        status='rented',
        scan_by='operator'  # TODO: Get from auth
    )
    db.add(transaction)

    # Update POS transaction item checked out quantity
    pos_item = db.query(POSTransactionItems).filter(
        and_(
            POSTransactionItems.contract_number == assignment.contract_no,
            POSTransactionItems.item_number == assignment.item_number
        )
    ).first()

    if pos_item:
        pos_item.checked_out_qty = (pos_item.checked_out_qty or 0) + assignment.quantity

    db.commit()

    return {
        "message": f"Tag {assignment.tag_id} assigned to contract {assignment.contract_no}",
        "item": {
            "tag_id": item.tag_id,
            "common_name": item.common_name,
            "contract": assignment.contract_no
        }
    }

@router.post("/contracts/merge-pos")
async def merge_manual_with_pos(
    temp_id: str,
    pos_contract_no: str,
    db: Session = Depends(get_manager_db)
):
    """Merge manual contract with POS update"""

    # Find manual contract
    manual = db.query(POSTransactions).filter(
        and_(
            POSTransactions.temp_id == temp_id,
            POSTransactions.is_manual == True
        )
    ).first()

    if not manual:
        raise HTTPException(status_code=404, detail="Manual contract not found")

    # Update contract number references
    # Update RFID items
    db.query(ItemMaster).filter(
        ItemMaster.last_contract_num == temp_id
    ).update({ItemMaster.last_contract_num: pos_contract_no})

    # Update transactions
    db.query(Transactions).filter(
        Transactions.contract_number == temp_id
    ).update({Transactions.contract_number: pos_contract_no})

    # Update POS transaction items
    db.query(POSTransactionItems).filter(
        POSTransactionItems.contract_number == temp_id
    ).update({POSTransactionItems.contract_number: pos_contract_no})

    # Mark manual contract as merged
    manual.is_manual = False
    manual.contract_no = pos_contract_no

    db.commit()

    return {
        "message": f"Manual contract {temp_id} merged with POS contract {pos_contract_no}",
        "contract_no": pos_contract_no
    }

@router.get("/contracts/{contract_no}/items")
async def get_contract_items_full(
    contract_no: str,
    db: Session = Depends(get_manager_db)
):
    """Get all items for contract - both POS and RFID"""

    # Get POS items
    pos_items = db.query(POSTransactionItems).filter(
        POSTransactionItems.contract_number == contract_no
    ).all()

    # Get RFID items
    rfid_items = db.query(ItemMaster).filter(
        ItemMaster.last_contract_num == contract_no
    ).all()

    # Get equipment details for POS items
    equipment_details = {}
    for item in pos_items:
        if item.item_number:
            equip = db.query(POSEquipment).filter(
                POSEquipment.item_num == item.item_number
            ).first()
            if equip:
                equipment_details[item.item_number] = {
                    'name': equip.name,
                    'category': equip.category,
                    'available_qty': equip.qty,
                    'needs_photo': True  # Bulk items need photo verification
                }

    return {
        "contract_no": contract_no,
        "pos_items": [{
            'item_number': item.item_number,
            'quantity': item.quantity,
            'checked_out': item.checked_out_qty or 0,
            'returned': item.returned_qty or 0,
            'description': item.description_field,
            'equipment': equipment_details.get(item.item_number)
        } for item in pos_items],
        "rfid_items": [{
            'tag_id': item.tag_id,
            'common_name': item.common_name,
            'status': item.status,
            'rental_class': item.rental_class_num,
            'quality': item.quality,
            'identifier_type': item.identifier_type
        } for item in rfid_items],
        "total_pos_items": len(pos_items),
        "total_rfid_tagged": len(rfid_items)
    }