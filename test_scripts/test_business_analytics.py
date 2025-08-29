#!/usr/bin/env python3
"""
Test Business Analytics Service directly with database connection
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'user': 'rfid_user', 
    'password': 'rfid_user_password',
    'database': 'rfid_inventory'
}

def test_business_analytics():
    """Test business analytics calculations directly"""
    
    # Create database engine
    db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset=utf8mb4"
    engine = create_engine(db_url)
    
    print("Testing Business Analytics Calculations...")
    print("=" * 50)
    
    try:
        # Get equipment data
        equipment_query = text("""
            SELECT 
                item_num,
                name,
                category,
                turnover_ytd,
                turnover_ltd,
                sell_price,
                current_store,
                inactive
            FROM pos_equipment 
            WHERE inactive = 0
            ORDER BY turnover_ytd DESC
        """)
        
        with engine.connect() as conn:
            equipment_df = pd.read_sql(equipment_query, conn)
        print(f"✓ Loaded {len(equipment_df)} active equipment records")
        
        if equipment_df.empty:
            print("❌ No equipment data available")
            return
        
        # Calculate basic metrics
        total_active_items = len(equipment_df)
        total_inventory_value = equipment_df['sell_price'].sum()
        total_ytd_revenue = equipment_df['turnover_ytd'].sum()
        
        print(f"\n📊 Basic Metrics:")
        print(f"   Total active items: {total_active_items:,}")
        print(f"   Total inventory value: ${total_inventory_value:,.2f}")
        print(f"   Total YTD revenue: ${total_ytd_revenue:,.2f}")
        
        # Identify high performers (top 20%)
        top_20_percent = int(len(equipment_df) * 0.2)
        high_performers = equipment_df.nlargest(top_20_percent, 'turnover_ytd')
        
        print(f"\n🏆 High Performers (Top 20%):")
        print(f"   Count: {len(high_performers)}")
        print(f"   Total revenue: ${high_performers['turnover_ytd'].sum():,.2f}")
        print(f"   Average revenue: ${high_performers['turnover_ytd'].mean():,.2f}")
        
        # Show top categories
        top_categories = high_performers['category'].value_counts().head(3)
        print(f"   Top categories: {dict(top_categories)}")
        
        # Identify underperformers
        underperformers = equipment_df[equipment_df['turnover_ytd'] <= 50]  # Less than $50 YTD
        zero_revenue = equipment_df[equipment_df['turnover_ytd'] == 0]
        
        print(f"\n⚠️  Underperformers (≤$50 YTD):")
        print(f"   Count: {len(underperformers)}")
        print(f"   Zero revenue items: {len(zero_revenue)}")
        print(f"   Potential resale value: ${underperformers['sell_price'].sum():,.2f}")
        
        # Category analysis
        category_stats = equipment_df.groupby('category').agg({
            'turnover_ytd': ['sum', 'mean', 'count'],
            'sell_price': 'sum'
        }).round(2)
        
        category_stats.columns = ['total_revenue', 'avg_revenue', 'item_count', 'total_value']
        category_stats['revenue_per_item'] = (category_stats['total_revenue'] / category_stats['item_count']).round(2)
        category_stats = category_stats.sort_values('total_revenue', ascending=False)
        
        print(f"\n📈 Category Performance:")
        for category, data in category_stats.head(5).iterrows():
            print(f"   {category[:30]:<30}: ${data['total_revenue']:>8,.2f} revenue, {data['item_count']:>3} items")
        
        # Resale recommendations
        resale_candidates = equipment_df[
            (equipment_df['turnover_ytd'] == 0) |  # No turnover this year
            ((equipment_df['turnover_ytd'] < 25) & (equipment_df['sell_price'] > 100))  # Low turnover but high value
        ]
        
        # Priority scoring
        resale_candidates = resale_candidates.copy()
        resale_candidates['resale_priority'] = (
            resale_candidates['sell_price'] / (resale_candidates['turnover_ytd'] + 1)
        ).round(2)
        
        high_priority = resale_candidates[resale_candidates['resale_priority'] > 10].sort_values('resale_priority', ascending=False)
        
        print(f"\n🔄 Resale Opportunities:")
        print(f"   Total candidates: {len(resale_candidates)}")
        print(f"   High priority items: {len(high_priority)}")
        print(f"   Potential resale value: ${resale_candidates['sell_price'].sum():,.2f}")
        
        if not high_priority.empty:
            print(f"\n   Top resale recommendations:")
            for _, item in high_priority.head(5).iterrows():
                print(f"   • {item['name'][:40]:<40} Priority: {item['resale_priority']:>6.1f} Value: ${item['sell_price']:>7.2f}")
        
        # Store performance (if we have store data)
        if equipment_df['current_store'].notna().any():
            store_stats = equipment_df.groupby('current_store').agg({
                'turnover_ytd': ['sum', 'count'],
                'sell_price': 'sum'
            }).round(2)
            
            store_stats.columns = ['total_revenue', 'item_count', 'total_value']
            store_stats = store_stats.sort_values('total_revenue', ascending=False)
            
            print(f"\n🏪 Store Performance:")
            for store, data in store_stats.head(3).iterrows():
                print(f"   Store {store}: ${data['total_revenue']:,.2f} revenue from {data['item_count']} items")
        
        # Overall ROI
        if total_inventory_value > 0:
            overall_roi = (total_ytd_revenue / total_inventory_value * 100)
            print(f"\n💰 Overall ROI: {overall_roi:.2f}%")
        
        print(f"\n✅ Business analytics calculations completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in analytics calculations: {e}")

if __name__ == "__main__":
    test_business_analytics()