"""
Category hierarchy endpoints for rental inventory navigation
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, case
from typing import List, Optional
from pydantic import BaseModel
from app.database.session import get_db
from app.models.items import OpsItem

router = APIRouter()

# Pydantic models for category hierarchy
class CategoryResponse(BaseModel):
    id: str
    name: str
    item_count: int
    available_count: int
    subcategories: Optional[List['SubcategoryResponse']] = None

class SubcategoryResponse(BaseModel):
    id: str
    category_id: str
    name: str
    item_count: int
    available_count: int
    common_names: Optional[List['CommonNameResponse']] = None

class CommonNameResponse(BaseModel):
    name: str
    subcategory_id: str
    item_count: int
    available_count: int

# Update forward references
CategoryResponse.model_rebuild()
SubcategoryResponse.model_rebuild()

def parse_rental_class(rental_class: str):
    """Parse rental_class_num format: 'CATEGORY-SUBCATEGORY-SPECIFIC'"""
    if not rental_class:
        return None, None, None

    parts = rental_class.split('-')
    if len(parts) >= 3:
        return parts[0], parts[1], '-'.join(parts[2:])
    elif len(parts) == 2:
        return parts[0], parts[1], None
    elif len(parts) == 1:
        return parts[0], None, None
    return None, None, None

@router.get("/items/categories", response_model=List[CategoryResponse])
async def get_categories(
    db: Session = Depends(get_db),
    resale_only: bool = Query(False),
    available_only: bool = Query(False)
):
    """Get all item categories with counts"""
    query = db.query(
        func.substr(OpsItem.rental_class_num, 1,
            case(
                (func.instr(OpsItem.rental_class_num, '-') > 0,
                 func.instr(OpsItem.rental_class_num, '-') - 1),
                else_=func.length(OpsItem.rental_class_num)
            )
        ).label('category'),
        func.count(OpsItem.tag_id).label('item_count'),
        func.sum(case((OpsItem.status == 'available', 1), else_=0)).label('available_count')
    ).filter(OpsItem.rental_class_num.isnot(None))

    if resale_only:
        query = query.filter(OpsItem.status.in_(['resale', 'sold']))
    if available_only:
        query = query.filter(OpsItem.status == 'available')

    results = query.group_by('category').all()

    categories = []
    for row in results:
        if row.category:
            categories.append(CategoryResponse(
                id=row.category,
                name=row.category,
                item_count=row.item_count or 0,
                available_count=row.available_count or 0
            ))

    return sorted(categories, key=lambda x: x.name)

@router.get("/items/categories/{category_id}/subcategories", response_model=List[SubcategoryResponse])
async def get_subcategories(
    category_id: str,
    db: Session = Depends(get_db),
    resale_only: bool = Query(False),
    available_only: bool = Query(False)
):
    """Get subcategories for a specific category"""
    # Filter items by category prefix
    query = db.query(OpsItem).filter(
        OpsItem.rental_class_num.like(f"{category_id}-%")
    )

    if resale_only:
        query = query.filter(OpsItem.status.in_(['resale', 'sold']))
    if available_only:
        query = query.filter(OpsItem.status == 'available')

    items = query.all()

    # Extract subcategories
    subcategory_map = {}
    for item in items:
        cat, subcat, _ = parse_rental_class(item.rental_class_num)
        if cat == category_id and subcat:
            if subcat not in subcategory_map:
                subcategory_map[subcat] = {
                    'count': 0,
                    'available': 0
                }
            subcategory_map[subcat]['count'] += 1
            if item.status == 'available':
                subcategory_map[subcat]['available'] += 1

    subcategories = []
    for subcat, counts in subcategory_map.items():
        subcategories.append(SubcategoryResponse(
            id=subcat,
            category_id=category_id,
            name=subcat,
            item_count=counts['count'],
            available_count=counts['available']
        ))

    return sorted(subcategories, key=lambda x: x.name)

@router.get("/items/subcategories/{subcategory_id}/common-names", response_model=List[CommonNameResponse])
async def get_common_names(
    subcategory_id: str,
    category_id: str = Query(..., description="Parent category ID"),
    db: Session = Depends(get_db),
    resale_only: bool = Query(False),
    available_only: bool = Query(False)
):
    """Get common names for a specific subcategory"""
    # Build the rental class prefix
    prefix = f"{category_id}-{subcategory_id}-"

    query = db.query(
        OpsItem.common_name,
        func.count(OpsItem.tag_id).label('item_count'),
        func.sum(case((OpsItem.status == 'available', 1), else_=0)).label('available_count')
    ).filter(
        OpsItem.rental_class_num.like(f"{prefix}%"),
        OpsItem.common_name.isnot(None)
    )

    if resale_only:
        query = query.filter(OpsItem.status.in_(['resale', 'sold']))
    if available_only:
        query = query.filter(OpsItem.status == 'available')

    results = query.group_by(OpsItem.common_name).all()

    common_names = []
    for row in results:
        common_names.append(CommonNameResponse(
            name=row.common_name,
            subcategory_id=subcategory_id,
            item_count=row.item_count or 0,
            available_count=row.available_count or 0
        ))

    return sorted(common_names, key=lambda x: x.name)

@router.get("/items/by-rental-class")
async def get_items_by_rental_class(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None),
    subcategory: Optional[str] = Query(None),
    common_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0)
):
    """Get items filtered by rental class hierarchy"""
    query = db.query(OpsItem)

    # Build rental class filter
    if category and subcategory:
        prefix = f"{category}-{subcategory}-"
        query = query.filter(OpsItem.rental_class_num.like(f"{prefix}%"))
    elif category:
        query = query.filter(OpsItem.rental_class_num.like(f"{category}-%"))

    if common_name:
        query = query.filter(OpsItem.common_name == common_name)
    if status:
        query = query.filter(OpsItem.status == status)
    if location:
        query = query.filter(OpsItem.bin_location == location)

    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return {
        'total': total,
        'items': [
            {
                'tag_id': item.tag_id,
                'common_name': item.common_name,
                'rental_class_num': item.rental_class_num,
                'status': item.status,
                'bin_location': item.bin_location,
                'quality': item.quality,
                'last_contract_num': item.last_contract_num,
                'identifier_type': item.identifier_type
            } for item in items
        ]
    }

@router.patch("/items/{tag_id}/status")
async def update_item_status(
    tag_id: str,
    status_update: dict,
    db: Session = Depends(get_db)
):
    """Update item status"""
    item = db.query(OpsItem).filter(OpsItem.tag_id == tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.status = status_update.get('status', item.status)
    if 'notes' in status_update:
        item.status_notes = status_update['notes']

    db.commit()
    return {"message": "Status updated", "tag_id": tag_id, "new_status": item.status}

@router.patch("/items/{tag_id}/location")
async def update_item_location(
    tag_id: str,
    location_update: dict,
    db: Session = Depends(get_db)
):
    """Update item location"""
    item = db.query(OpsItem).filter(OpsItem.tag_id == tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.bin_location = location_update.get('location', item.bin_location)
    db.commit()
    return {"message": "Location updated", "tag_id": tag_id, "new_location": item.bin_location}

@router.post("/items/bulk-update-status")
async def bulk_update_status(
    update_data: dict,
    db: Session = Depends(get_db)
):
    """Bulk update item statuses"""
    tag_ids = update_data.get('tag_ids', [])
    new_status = update_data.get('status')

    if not tag_ids or not new_status:
        raise HTTPException(status_code=400, detail="tag_ids and status are required")

    updated = db.query(OpsItem).filter(
        OpsItem.tag_id.in_(tag_ids)
    ).update(
        {OpsItem.status: new_status},
        synchronize_session=False
    )

    db.commit()
    return {"message": f"Updated {updated} items", "status": new_status}

# Resale specific endpoints
@router.get("/items/resale")
async def get_resale_items(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    subcategory: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0)
):
    """Get items marked for resale"""
    query = db.query(OpsItem).filter(
        OpsItem.status.in_(['resale', 'sold'])
    )

    if status:
        query = query.filter(OpsItem.status == status)

    if category and subcategory:
        prefix = f"{category}-{subcategory}-"
        query = query.filter(OpsItem.rental_class_num.like(f"{prefix}%"))
    elif category:
        query = query.filter(OpsItem.rental_class_num.like(f"{category}-%"))

    items = query.offset(offset).limit(limit).all()

    # Parse categories from rental_class_num
    result_items = []
    for item in items:
        cat, subcat, _ = parse_rental_class(item.rental_class_num)
        result_items.append({
            'tag_id': item.tag_id,
            'common_name': item.common_name,
            'category': cat or 'Uncategorized',
            'subcategory': subcat or 'Uncategorized',
            'quality': item.quality,
            'status': item.status,
            'resale_price': 25.00  # Default price, should come from pricing table
        })

    return result_items

@router.get("/items/export-sold")
async def export_sold_items(
    db: Session = Depends(get_db)
):
    """Export sold items as CSV"""
    from fastapi.responses import StreamingResponse
    import csv
    import io

    items = db.query(OpsItem).filter(OpsItem.status == 'sold').all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Tag ID', 'Item Name', 'Category', 'Subcategory', 'Sale Date', 'Price'])

    for item in items:
        cat, subcat, _ = parse_rental_class(item.rental_class_num)
        writer.writerow([
            item.tag_id,
            item.common_name,
            cat or '',
            subcat or '',
            item.date_updated.strftime('%Y-%m-%d') if item.date_updated else '',
            '25.00'
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sold_items.csv"}
    )