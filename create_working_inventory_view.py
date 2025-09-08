#!/usr/bin/env python3
"""
Create Working Combined Inventory View
Creates a simplified but working version using actual table schemas
"""

import os
os.environ['FLASK_SKIP_SCHEDULER'] = '1'

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("🚀 Creating working combined inventory view...")
    
    # Drop existing view if exists
    try:
        db.session.execute(text("DROP VIEW IF EXISTS combined_inventory"))
        print("✅ Dropped existing view if it existed")
    except Exception as e:
        print(f"⚠️ Note: {e}")
    
    # Create simplified working view
    create_view_sql = text("""
        CREATE VIEW combined_inventory AS
        SELECT 
            -- Primary identifiers
            pe.item_num as equipment_id,
            pe.name as equipment_name,
            pe.category as category,
            pe.current_store as store_code,
            
            -- Equipment details from POS
            pe.qty as pos_quantity,
            pe.rate_1 as rental_rate,
            pe.period_1 as rental_period,
            pe.inactive as is_inactive,
            pe.home_store as home_store_code,
            
            -- RFID correlation data
            erc.confidence_score as correlation_confidence,
            erc.rfid_tag_count as tag_count_from_correlation,
            erc.correlation_type as correlation_method,
            
            -- RFID inventory status (aggregated from individual tags)
            COALESCE(rfid_agg.total_tags, 0) as rfid_tag_count,
            COALESCE(rfid_agg.on_rent_count, 0) as on_rent_count,
            COALESCE(rfid_agg.available_count, 0) as available_count,
            COALESCE(rfid_agg.maintenance_count, 0) as maintenance_count,
            
            -- Calculated availability metrics
            CASE 
                WHEN pe.qty > 0 THEN 
                    GREATEST(0, pe.qty - COALESCE(rfid_agg.on_rent_count, 0))
                ELSE 0 
            END as calculated_available,
            
            -- Status determination logic
            CASE 
                WHEN pe.inactive = 1 THEN 'inactive'
                WHEN COALESCE(rfid_agg.maintenance_count, 0) > 0 THEN 'maintenance'
                WHEN COALESCE(rfid_agg.on_rent_count, 0) >= pe.qty THEN 'fully_rented'
                WHEN COALESCE(rfid_agg.on_rent_count, 0) > 0 THEN 'partially_rented'
                ELSE 'available'
            END as status,
            
            -- Revenue and utilization calculations
            COALESCE(pe.rate_1, 0) * COALESCE(rfid_agg.on_rent_count, 0) as current_rental_revenue,
            CASE 
                WHEN pe.qty > 0 THEN 
                    ROUND((COALESCE(rfid_agg.on_rent_count, 0) / pe.qty) * 100, 1)
                ELSE 0 
            END as utilization_percentage,
            
            -- Data quality flags
            CASE 
                WHEN erc.pos_item_num IS NULL THEN 'no_rfid_correlation'
                WHEN ABS(pe.qty - COALESCE(rfid_agg.total_tags, 0)) > 2 THEN 'quantity_mismatch'
                WHEN erc.confidence_score < 0.8 THEN 'low_confidence_match'
                ELSE 'good_quality'
            END as data_quality_flag,
            
            -- Timestamps for freshness tracking
            erc.created_at as correlation_date,
            NOW() as view_generated_at

        FROM pos_equipment pe

        -- Join with equipment correlations (our 533 correlations)
        LEFT JOIN equipment_rfid_correlations erc 
            ON pe.item_num = erc.pos_item_num

        -- Aggregate RFID data by rental class
        LEFT JOIN (
            SELECT 
                rental_class_num,
                COUNT(*) as total_tags,
                SUM(CASE WHEN status = 'On Rent' THEN 1 ELSE 0 END) as on_rent_count,
                SUM(CASE WHEN status = 'Delivered' OR status = 'Available' THEN 1 ELSE 0 END) as available_count,
                SUM(CASE WHEN status = 'Maintenance' OR status = 'Repair' THEN 1 ELSE 0 END) as maintenance_count
            FROM id_item_master 
            WHERE identifier_type = 'RFID'
            GROUP BY rental_class_num
        ) rfid_agg ON pe.item_num = rfid_agg.rental_class_num

        -- Filter for active equipment categories
        WHERE pe.category NOT IN ('UNUSED', 'NON CURRENT ITEMS', 'Parts - Internal Repair/Maint')
          AND pe.inactive = 0
    """)
    
    try:
        db.session.execute(create_view_sql)
        db.session.commit()
        print("✅ Combined inventory view created successfully")
        
        # Test the view
        result = db.session.execute(text("SELECT COUNT(*) as total FROM combined_inventory")).fetchone()
        print(f"📊 Combined inventory view contains {result[0]} equipment items")
        
        # Sample data quality check
        quality_check = db.session.execute(text("""
            SELECT 
                data_quality_flag,
                COUNT(*) as count
            FROM combined_inventory 
            GROUP BY data_quality_flag
            ORDER BY count DESC
        """)).fetchall()
        
        print("📈 Data Quality Breakdown:")
        for row in quality_check:
            print(f"   {row[0]}: {row[1]} items")
            
        # Show sample data
        sample_data = db.session.execute(text("""
            SELECT 
                equipment_id,
                equipment_name,
                category,
                store_code,
                pos_quantity,
                rfid_tag_count,
                status,
                data_quality_flag
            FROM combined_inventory 
            WHERE data_quality_flag = 'good_quality'
            LIMIT 5
        """)).fetchall()
        
        print("\n🔍 Sample Combined Inventory Data:")
        for row in sample_data:
            print(f"   {row[0]}: {row[1][:30]}... | Store: {row[3]} | POS Qty: {row[4]} | RFID Tags: {row[5]} | Status: {row[6]}")
            
    except Exception as e:
        print(f"❌ Error creating view: {e}")
        db.session.rollback()