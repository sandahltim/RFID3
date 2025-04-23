from flask import Blueprint, render_template, current_app
from .. import db, cache
from ..models.db_models import ItemMaster, Transaction, RentalClassMapping, UserRentalClassMapping
from sqlalchemy import func, desc, or_
from time import time

tab3_bp = Blueprint('tab3', __name__)

@tab3_bp.route('/tab/3')
def tab3_view():
    try:
        session = db.session()
        current_app.logger.info("Starting new session for tab3")

        # Define crew categories
        tent_categories = ['Pole Tent Tops', 'Frame Tent Tops']
        laundry_categories = ['Rectangle Linen', 'Round Linen', 'Runners and Drapes']

        # Fetch all rental class mappings
        base_mappings = session.query(RentalClassMapping).all()
        user_mappings = session.query(UserRentalClassMapping).all()

        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

        # Identify items in service
        subquery = session.query(
            Transaction.tag_id,
            Transaction.scan_date,
            Transaction.service_required,
            Transaction.location_of_repair,
            Transaction.dirty_or_mud,
            Transaction.leaves,
            Transaction.oil,
            Transaction.mold,
            Transaction.stain,
            Transaction.oxidation,
            Transaction.rip_or_tear,
            Transaction.sewing_repair_needed,
            Transaction.grommet,
            Transaction.rope,
            Transaction.buckle,
            Transaction.wet,
            Transaction.other
        ).order_by(
            Transaction.scan_date.desc()
        ).subquery()

        items_in_service_query = session.query(
            ItemMaster,
            subquery.c.location_of_repair,
            subquery.c.dirty_or_mud,
            subquery.c.leaves,
            subquery.c.oil,
            subquery.c.mold,
            subquery.c.stain,
            subquery.c.oxidation,
            subquery.c.rip_or_tear,
            subquery.c.sewing_repair_needed,
            subquery.c.grommet,
            subquery.c.rope,
            subquery.c.buckle,
            subquery.c.wet,
            subquery.c.other
        ).outerjoin(
            subquery,
            ItemMaster.tag_id == subquery.c.tag_id
        ).filter(
            or_(
                ItemMaster.status.notin_(['Ready to Rent', 'On Rent', 'Delivered']),
                (subquery.c.service_required == True) & (
                    subquery.c.scan_date == session.query(func.max(Transaction.scan_date)).filter(Transaction.tag_id == ItemMaster.tag_id).correlate(ItemMaster).scalar_subquery()
                )
            )
        ).all()

        # Categorize items by crew
        tent_crew_items = []
        laundry_crew_items = []
        maintenance_crew_items = []

        for item, location_of_repair, dirty_or_mud, leaves, oil, mold, stain, oxidation, rip_or_tear, sewing_repair_needed, grommet, rope, buckle, wet, other in items_in_service_query:
            rental_class_num = str(item.rental_class_num).strip().upper() if item.rental_class_num else None
            category = mappings_dict.get(rental_class_num, {}).get('category', 'Unknown')

            # Determine repair types
            repair_types = []
            if dirty_or_mud: repair_types.append("Dirty/Mud")
            if leaves: repair_types.append("Leaves")
            if oil: repair_types.append("Oil")
            if mold: repair_types.append("Mold")
            if stain: repair_types.append("Stain")
            if oxidation: repair_types.append("Oxidation")
            if rip_or_tear: repair_types.append("Rip/Tear")
            if sewing_repair_needed: repair_types.append("Sewing Repair Needed")
            if grommet: repair_types.append("Grommet")
            if rope: repair_types.append("Rope")
            if buckle: repair_types.append("Buckle")
            if wet: repair_types.append("Wet")
            if other: repair_types.append(f"Other: {other}")

            repair_details = {
                'tag_id': item.tag_id,
                'common_name': item.common_name,
                'status': item.status,
                'bin_location': item.bin_location,
                'last_contract_num': item.last_contract_num,
                'location_of_repair': location_of_repair or 'N/A',
                'repair_types': repair_types if repair_types else ['Unknown']
            }

            # Categorize by crew
            if category in tent_categories:
                tent_crew_items.append(repair_details)
            elif category in laundry_categories:
                laundry_crew_items.append(repair_details)
            else:
                maintenance_crew_items.append(repair_details)

        # Sort items by tag_id for consistency
        tent_crew_items.sort(key=lambda x: x['tag_id'])
        laundry_crew_items.sort(key=lambda x: x['tag_id'])
        maintenance_crew_items.sort(key=lambda x: x['tag_id'])

        current_app.logger.info(f"Fetched {len(tent_crew_items)} items for Tent Crew, {len(laundry_crew_items)} for Laundry Crew, {len(maintenance_crew_items)} for Maintenance Crew")
        session.close()
        return render_template('tab3.html', 
                              tent_crew_items=tent_crew_items,
                              laundry_crew_items=laundry_crew_items,
                              maintenance_crew_items=maintenance_crew_items,
                              cache_bust=int(time()))
    except Exception as e:
        current_app.logger.error(f"Error rendering Tab 3: {str(e)}", exc_info=True)
        return render_template('tab3.html', 
                              tent_crew_items=[],
                              laundry_crew_items=[],
                              maintenance_crew_items=[],
                              cache_bust=int(time()))