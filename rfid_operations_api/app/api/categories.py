"""
Category hierarchy endpoints for rental inventory navigation
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, case
from typing import List, Optional
from pydantic import BaseModel
from app.models import get_manager_db, Item

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
    db: Session = Depends(get_manager_db),
    resale_only: bool = Query(False),
    available_only: bool = Query(False)
):
    """Get all item categories with counts - uses user mappings when available"""
    from sqlalchemy import text

    # Query using user mappings joined with items
    sql = """
    SELECT
        COALESCE(urm.category,
                 SUBSTRING_INDEX(i.rental_class_num, '-', 1)) as category,
        COUNT(DISTINCT i.tag_id) as item_count,
        SUM(CASE WHEN i.status = 'Ready to Rent' THEN 1 ELSE 0 END) as available_count
    FROM id_item_master i
    LEFT JOIN user_rental_class_mappings urm ON i.rental_class_num = urm.rental_class_id
    WHERE i.rental_class_num IS NOT NULL
    """

    if resale_only:
        sql += " AND i.status IN ('resale', 'sold')"
    if available_only:
        sql += " AND i.status = 'Ready to Rent'"

    sql += " GROUP BY category ORDER BY category"

    results = db.execute(text(sql)).fetchall()

    categories = []
    for row in results:
        if row.category:
            categories.append(CategoryResponse(
                id=row.category,
                name=row.category,
                item_count=row.item_count or 0,
                available_count=row.available_count or 0
            ))

    return categories

@router.get("/items/categories/{category_id}/subcategories", response_model=List[SubcategoryResponse])
async def get_subcategories(
    category_id: str,
    db: Session = Depends(get_manager_db),
    resale_only: bool = Query(False),
    available_only: bool = Query(False)
):
    """Get subcategories for a specific category - uses user mappings when available"""
    from sqlalchemy import text

    sql = """
    SELECT
        urm.subcategory as subcategory,
        COUNT(DISTINCT i.tag_id) as item_count,
        SUM(CASE WHEN i.status = 'Ready to Rent' THEN 1 ELSE 0 END) as available_count
    FROM user_rental_class_mappings urm
    LEFT JOIN id_item_master i ON i.rental_class_num = urm.rental_class_id
    WHERE urm.category = :category
    AND urm.subcategory IS NOT NULL
    """

    params = {"category": category_id}

    if resale_only:
        sql += " AND i.status IN ('resale', 'sold')"
    if available_only:
        sql += " AND i.status = 'Ready to Rent'"

    sql += " GROUP BY subcategory HAVING subcategory IS NOT NULL ORDER BY subcategory"

    results = db.execute(text(sql), params).fetchall()

    subcategories = []
    for row in results:
        if row.subcategory:
            subcategories.append(SubcategoryResponse(
                id=row.subcategory,
                category_id=category_id,
                name=row.subcategory,
                item_count=row.item_count or 0,
                available_count=row.available_count or 0
            ))

    return subcategories

@router.get("/items/subcategories/{subcategory_id}/common-names", response_model=List[CommonNameResponse])
async def get_common_names(
    subcategory_id: str,
    category_id: str = Query(..., description="Parent category ID"),
    db: Session = Depends(get_manager_db),
    resale_only: bool = Query(False),
    available_only: bool = Query(False)
):
    """Get common names for a specific subcategory"""
    # Build the rental class prefix
    prefix = f"{category_id}-{subcategory_id}-"

    query = db.query(
        Item.common_name,
        func.count(Item.tag_id).label('item_count'),
        func.sum(case((Item.status == 'available', 1), else_=0)).label('available_count')
    ).filter(
        Item.rental_class_num.like(f"{prefix}%"),
        Item.common_name.isnot(None)
    )

    if resale_only:
        query = query.filter(Item.status.in_(['resale', 'sold']))
    if available_only:
        query = query.filter(Item.status == 'available')

    results = query.group_by(Item.common_name).all()

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
    db: Session = Depends(get_manager_db),
    category: Optional[str] = Query(None),
    subcategory: Optional[str] = Query(None),
    common_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0)
):
    """Get items filtered by rental class hierarchy - shows RFID tagged items individually or POS quantities"""
    from sqlalchemy import text

    # First check if we have RFID tagged items for this selection
    if category and subcategory:
        # Get items using user mappings
        sql = """
        SELECT
            i.tag_id,
            i.item_num,
            i.common_name,
            i.rental_class_num,
            i.status,
            i.bin_location,
            i.quality,
            i.last_contract_num,
            i.identifier_type,
            i.serial_number
        FROM id_item_master i
        INNER JOIN user_rental_class_mappings urm ON i.rental_class_num = urm.rental_class_id
        WHERE urm.category = :category
        AND urm.subcategory = :subcategory
        """

        params = {"category": category, "subcategory": subcategory}

        if common_name:
            sql += " AND i.common_name = :common_name"
            params["common_name"] = common_name
        if status:
            sql += " AND i.status = :status"
            params["status"] = status
        if location:
            sql += " AND i.bin_location = :location"
            params["location"] = location

        sql += " ORDER BY i.common_name, i.tag_id"
        sql += f" LIMIT {limit} OFFSET {offset}"

        results = db.execute(text(sql), params).fetchall()

        # Count total
        count_sql = """
        SELECT COUNT(*) as total
        FROM id_item_master i
        INNER JOIN user_rental_class_mappings urm ON i.rental_class_num = urm.rental_class_id
        WHERE urm.category = :category
        AND urm.subcategory = :subcategory
        """
        if common_name:
            count_sql += " AND i.common_name = :common_name"
        if status:
            count_sql += " AND i.status = :status"
        if location:
            count_sql += " AND i.bin_location = :location"

        total = db.execute(text(count_sql), params).fetchone()[0]

        # Check if we have RFID items or need POS data
        if results:
            # We have RFID tagged items - return them individually
            items = []
            for row in results:
                items.append({
                    'tag_id': row.tag_id,
                    'item_num': row.item_num,
                    'common_name': row.common_name,
                    'rental_class_num': row.rental_class_num,
                    'status': row.status,
                    'bin_location': row.bin_location,
                    'quality': row.quality,
                    'last_contract_num': row.last_contract_num,
                    'identifier_type': row.identifier_type,
                    'serial_number': row.serial_number,
                    'data_source': 'RFID'
                })
            return {'total': total, 'items': items, 'type': 'individual'}
        else:
            # No RFID items - check POS for quantity data
            pos_sql = """
            SELECT
                pe.item_num,
                pe.name,
                pe.category,
                pe.current_store,
                pe.rate1,
                pe.replacement_cost
            FROM pos_equipment pe
            WHERE pe.category = :category
            """
            if common_name:
                pos_sql += " AND pe.name LIKE :common_name_pattern"
                params["common_name_pattern"] = f"%{common_name}%"

            pos_results = db.execute(text(pos_sql), params).fetchall()

            # If no POS items either, return empty
            if not pos_results:
                return {'total': 0, 'items': [], 'type': 'none'}

            items = []
            for row in pos_results:
                items.append({
                    'item_num': row.item_num,
                    'common_name': row.name,
                    'category': row.category,
                    'current_store': row.current_store,
                    'rate1': float(row.rate1) if row.rate1 else 0,
                    'replacement_cost': float(row.replacement_cost) if row.replacement_cost else 0,
                    'data_source': 'POS'
                })
            return {'total': len(items), 'items': items, 'type': 'quantity'}
    else:
        # Just category filter - simplified query
        query = db.query(Item)
        if category:
            query = query.join(
                text("user_rental_class_mappings urm"),
                Item.rental_class_num == text("urm.rental_class_id")
            ).filter(text(f"urm.category = '{category}'"))

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
                    'identifier_type': item.identifier_type,
                    'data_source': 'RFID'
                } for item in items
            ],
            'type': 'individual'
        }

@router.patch("/items/{tag_id}/status")
async def update_item_status(
    tag_id: str,
    status_update: dict,
    db: Session = Depends(get_manager_db)
):
    """Update item status"""
    item = db.query(Item).filter(Item.tag_id == tag_id).first()
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
    db: Session = Depends(get_manager_db)
):
    """Update item location"""
    item = db.query(Item).filter(Item.tag_id == tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.bin_location = location_update.get('location', item.bin_location)
    db.commit()
    return {"message": "Location updated", "tag_id": tag_id, "new_location": item.bin_location}

@router.post("/items/bulk-update-status")
async def bulk_update_status(
    update_data: dict,
    db: Session = Depends(get_manager_db)
):
    """Bulk update item statuses"""
    tag_ids = update_data.get('tag_ids', [])
    new_status = update_data.get('status')

    if not tag_ids or not new_status:
        raise HTTPException(status_code=400, detail="tag_ids and status are required")

    updated = db.query(Item).filter(
        Item.tag_id.in_(tag_ids)
    ).update(
        {Item.status: new_status},
        synchronize_session=False
    )

    db.commit()
    return {"message": f"Updated {updated} items", "status": new_status}

# Resale specific endpoints
@router.get("/items/resale")
async def get_resale_items(
    db: Session = Depends(get_manager_db),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    subcategory: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0)
):
    """Get items marked for resale"""
    query = db.query(Item).filter(
        Item.status.in_(['resale', 'sold'])
    )

    if status:
        query = query.filter(Item.status == status)

    if category and subcategory:
        prefix = f"{category}-{subcategory}-"
        query = query.filter(Item.rental_class_num.like(f"{prefix}%"))
    elif category:
        query = query.filter(Item.rental_class_num.like(f"{category}-%"))

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
    db: Session = Depends(get_manager_db)
):
    """Export sold items as CSV"""
    from fastapi.responses import StreamingResponse
    import csv
    import io

    items = db.query(Item).filter(Item.status == 'sold').all()

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