#!/usr/bin/env python3
"""
Fix All Analytics Services to Use Centralized Store Mappings
Updates all analytics and predictive algorithms to use app.config.stores
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

# Configuration
PROJECT_ROOT = Path("/home/tim/RFID3")
BACKUP_DIR = PROJECT_ROOT / "backups" / f"analytics_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Services to update
ANALYTICS_SERVICES = [
    "app/services/executive_insights_service.py",
    "app/services/financial_analytics_service.py", 
    "app/services/weather_correlation_service.py",
    "app/services/multi_store_analytics_service.py",
    "app/services/minnesota_seasonal_service.py",
    "app/services/weather_predictive_service.py",
    "app/services/minnesota_industry_analytics.py",
    "app/services/equipment_categorization_service.py",
    "app/services/scorecard_correlation_service.py",
    "app/services/store_correlation_service.py",
    "app/services/cross_system_analytics.py",
    "app/services/bi_analytics.py"
]

# Store mapping corrections based on centralized configuration
STORE_MAPPING_CORRECTIONS = {
    # Correct store codes
    "'3607'": "Wayzata",
    "'6800'": "Brooklyn Park", 
    "'8101'": "Fridley (Broadway Tent & Event)",
    "'728'": "Elk River",
    "'000'": "Legacy/Unassigned",
    
    # Manager assignments
    "TYLER": "3607",
    "ZACK": "6800",
    "TIM": "8101",
    "BRUCE": "728",
    
    # Business types
    "3607_business": "90% DIY/10% Events",
    "6800_business": "100% Construction",
    "8101_business": "100% Events (Broadway Tent & Event)",
    "728_business": "90% DIY/10% Events",
    
    # Opening dates
    "3607_opened": "2008-01-01",
    "6800_opened": "2022-01-01",
    "8101_opened": "2022-01-01",
    "728_opened": "2024-01-01"
}

def create_backup(file_path):
    """Create backup of file before modification"""
    try:
        source = PROJECT_ROOT / file_path
        if source.exists():
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            backup_path = BACKUP_DIR / file_path.replace("/", "_")
            with open(source, 'r') as f:
                content = f.read()
            with open(backup_path, 'w') as f:
                f.write(content)
            print(f"✅ Backed up: {file_path}")
            return True
    except Exception as e:
        print(f"❌ Failed to backup {file_path}: {e}")
        return False

def add_store_import(content):
    """Add import for centralized store configuration"""
    import_line = "from app.config.stores import (\n    STORES, STORE_MAPPING, STORE_MANAGERS,\n    STORE_BUSINESS_TYPES, STORE_OPENING_DATES,\n    get_store_name, get_store_manager, get_store_business_type,\n    get_store_opening_date, get_active_store_codes\n)\n"
    
    # Check if import already exists
    if "from app.config.stores import" in content:
        return content
    
    # Find appropriate place to add import
    import_section_end = 0
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            import_section_end = i + 1
    
    # Insert import after other imports
    lines.insert(import_section_end, import_line)
    return '\n'.join(lines)

def fix_executive_insights_service():
    """Fix executive insights service store mappings"""
    file_path = PROJECT_ROOT / "app/services/executive_insights_service.py"
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    create_backup("app/services/executive_insights_service.py")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add store configuration import
    content = add_store_import(content)
    
    # Replace hardcoded store mappings in _detect_store_anomalies
    old_store_list = """            stores = [
                ('wayzata_revenue', 'Wayzata'),
                ('brooklyn_park_revenue', 'Brooklyn Park'),
                ('fridley_revenue', 'Fridley'),
                ('elk_river_revenue', 'Elk River')
            ]"""
    
    new_store_list = """            # Use centralized store configuration
            stores = []
            for store_code in get_active_store_codes():
                store_name = get_store_name(store_code)
                if store_code == '3607':
                    stores.append(('wayzata_revenue', store_name))
                elif store_code == '6800':
                    stores.append(('brooklyn_park_revenue', store_name))
                elif store_code == '8101':
                    stores.append(('fridley_revenue', store_name))
                elif store_code == '728':
                    stores.append(('elk_river_revenue', store_name))"""
    
    content = content.replace(old_store_list, new_store_list)
    
    # Fix SQL query column mappings
    content = content.replace('revenue_728', 'revenue_8101')  # Fix Fridley
    content = content.replace('revenue_8101', 'revenue_728')  # Fix Elk River
    content = content.replace('new_contracts_728', 'new_contracts_8101')
    content = content.replace('new_contracts_8101', 'new_contracts_728')
    
    # Fix _check_seasonal_correlation to use store configuration
    old_check = 'store != "Elk River"'
    new_check = 'store_code != "728"'  # 728 is Elk River
    content = content.replace(old_check, new_check)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed executive_insights_service.py")
    return True

def fix_financial_analytics_service():
    """Fix financial analytics service store mappings"""
    file_path = PROJECT_ROOT / "app/services/financial_analytics_service.py"
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    create_backup("app/services/financial_analytics_service.py")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add store configuration import
    content = add_store_import(content)
    
    # Replace hardcoded STORE_CODES
    old_store_codes = """    # CORRECTED store codes based on comprehensive CSV analysis and web research
    STORE_CODES = {
        '3607': 'Wayzata',        # A1 Rent It - 90% DIY/10% Events - 3607 Shoreline Dr
        '6800': 'Brooklyn Park',  # A1 Rent It - 100% DIY Construction - Pure commercial
        '728': 'Elk River',       # A1 Rent It - 90% DIY/10% Events - Rural/agricultural
        '8101': 'Fridley'         # Broadway Tent & Event - 100% Events - 8101 Ashton Ave NE
    }"""
    
    new_store_codes = """    # Use centralized store configuration
    STORE_CODES = {code: get_store_name(code) for code in get_active_store_codes()}"""
    
    content = content.replace(old_store_codes, new_store_codes)
    
    # Replace hardcoded STORE_BUSINESS_MIX
    old_business_mix = """    # Business mix profiles for accurate analytics
    STORE_BUSINESS_MIX = {
        '3607': {'construction': 0.90, 'events': 0.10, 'brand': 'A1 Rent It'},
        '6800': {'construction': 1.00, 'events': 0.00, 'brand': 'A1 Rent It'},
        '728': {'construction': 0.90, 'events': 0.10, 'brand': 'A1 Rent It'},
        '8101': {'construction': 0.00, 'events': 1.00, 'brand': 'Broadway Tent & Event'}
    }"""
    
    new_business_mix = """    # Business mix profiles from centralized configuration
    STORE_BUSINESS_MIX = {}
    for store_code in get_active_store_codes():
        business_type = get_store_business_type(store_code)
        if '100% Construction' in business_type:
            STORE_BUSINESS_MIX[store_code] = {'construction': 1.00, 'events': 0.00}
        elif '100% Events' in business_type:
            STORE_BUSINESS_MIX[store_code] = {'construction': 0.00, 'events': 1.00}
        elif '90% DIY/10% Events' in business_type:
            STORE_BUSINESS_MIX[store_code] = {'construction': 0.90, 'events': 0.10}
        else:
            STORE_BUSINESS_MIX[store_code] = {'construction': 0.50, 'events': 0.50}"""
    
    content = content.replace(old_business_mix, new_business_mix)
    
    # Fix column name mappings in SQL queries
    content = content.replace('revenue_728', 'revenue_8101_temp')  # Temporary
    content = content.replace('revenue_8101', 'revenue_728')  # Fix Elk River
    content = content.replace('revenue_8101_temp', 'revenue_8101')  # Fix Fridley
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed financial_analytics_service.py")
    return True

def fix_multi_store_analytics_service():
    """Fix multi-store analytics service store mappings"""
    file_path = PROJECT_ROOT / "app/services/multi_store_analytics_service.py"
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    create_backup("app/services/multi_store_analytics_service.py")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add store configuration import
    content = add_store_import(content)
    
    # Replace hardcoded STORE_GEOGRAPHIC_DATA
    old_geographic_start = "    # Minnesota store geographic and market data\n    STORE_GEOGRAPHIC_DATA = {"
    
    new_geographic = """    # Minnesota store geographic and market data from centralized configuration
    STORE_GEOGRAPHIC_DATA = {}
    
    # Build geographic data from centralized store configuration
    for store_code, store_info in STORES.items():
        if not store_info.active:
            continue
            
        geographic_data = {
            'name': store_info.name,
            'manager': store_info.manager,
            'opened_date': store_info.opened_date,
            'business_type': store_info.business_type
        }
        
        # Add specific geographic data based on store
        if store_code == '3607':  # Wayzata
            geographic_data.update({
                'coordinates': (44.9733, -93.5066),
                'county': 'Hennepin',
                'market_characteristics': {
                    'affluent_suburban': True,
                    'lake_access': True,
                    'high_event_demand': True,
                    'premium_pricing_tolerance': 'high'
                }
            })
        elif store_code == '6800':  # Brooklyn Park
            geographic_data.update({
                'coordinates': (45.0941, -93.3563),
                'county': 'Hennepin',
                'market_characteristics': {
                    'suburban_mixed': True,
                    'construction_demand': True,
                    'premium_pricing_tolerance': 'medium'
                }
            })
        elif store_code == '728':  # Elk River
            geographic_data.update({
                'coordinates': (45.3033, -93.5677),
                'county': 'Sherburne',
                'market_characteristics': {
                    'rural_suburban': True,
                    'agricultural_support': True,
                    'diy_homeowner_base': True,
                    'premium_pricing_tolerance': 'medium'
                }
            })
        elif store_code == '8101':  # Fridley
            geographic_data.update({
                'coordinates': (45.0863, -93.2636),
                'county': 'Anoka',
                'address': '8101 Ashton Ave NE, Fridley, MN',
                'brand': 'Broadway Tent & Event',
                'market_characteristics': {
                    'events_focused': True,
                    'wedding_venues_nearby': True,
                    'corporate_event_demand': True,
                    'premium_pricing_tolerance': 'high'
                }
            })
        
        STORE_GEOGRAPHIC_DATA[store_code] = geographic_data"""
    
    # Find and replace the entire STORE_GEOGRAPHIC_DATA section
    import_end = content.find("class MultiStoreAnalyticsService:")
    if import_end > 0:
        # Insert new geographic data setup before the class
        lines = content[:import_end].split('\n')
        # Remove old STORE_GEOGRAPHIC_DATA if it exists
        new_lines = []
        skip_until_brace = False
        brace_count = 0
        
        for line in lines:
            if "STORE_GEOGRAPHIC_DATA = {" in line:
                skip_until_brace = True
                brace_count = 1
                continue
            
            if skip_until_brace:
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0:
                    skip_until_brace = False
                continue
            
            new_lines.append(line)
        
        content = '\n'.join(new_lines) + '\n' + new_geographic + '\n' + content[import_end:]
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed multi_store_analytics_service.py")
    return True

def fix_weather_correlation_service():
    """Fix weather correlation service"""
    file_path = PROJECT_ROOT / "app/services/weather_correlation_service.py"
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    create_backup("app/services/weather_correlation_service.py")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add store configuration import
    content = add_store_import(content)
    
    # Add store validation in analyze_weather_rental_correlations
    old_analyze_start = "    def analyze_weather_rental_correlations(self, store_code: str = None,"
    
    new_analyze = """    def analyze_weather_rental_correlations(self, store_code: str = None,"""
    
    # Add store code validation
    validation_code = """
            # Validate store code using centralized configuration
            if store_code and store_code != 'all':
                if store_code not in STORES:
                    self.logger.warning(f"Invalid store code {store_code}, using all stores")
                    store_code = None"""
    
    # Find the right place to insert validation
    if "def analyze_weather_rental_correlations" in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "def analyze_weather_rental_correlations" in line:
                # Find the try block
                for j in range(i, min(i+10, len(lines))):
                    if "try:" in lines[j]:
                        # Insert validation after try
                        lines[j] = lines[j] + validation_code
                        break
                break
        content = '\n'.join(lines)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed weather_correlation_service.py")
    return True

def verify_fixes():
    """Verify that all services now import from centralized store configuration"""
    print("\n🔍 Verifying fixes...")
    
    all_good = True
    for service_path in ANALYTICS_SERVICES:
        file_path = PROJECT_ROOT / service_path
        if file_path.exists():
            with open(file_path, 'r') as f:
                content = f.read()
            
            if "from app.config.stores import" in content:
                print(f"✅ {service_path}: Uses centralized store config")
            else:
                print(f"⚠️  {service_path}: May need manual review")
                all_good = False
        else:
            print(f"❌ {service_path}: File not found")
            all_good = False
    
    return all_good

def main():
    """Main execution"""
    print("🚀 Starting Analytics Store Mapping Fix")
    print(f"📁 Project root: {PROJECT_ROOT}")
    print(f"💾 Backup directory: {BACKUP_DIR}")
    print("-" * 50)
    
    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Fix each service
    results = {
        "executive_insights": fix_executive_insights_service(),
        "financial_analytics": fix_financial_analytics_service(),
        "multi_store": fix_multi_store_analytics_service(),
        "weather_correlation": fix_weather_correlation_service()
    }
    
    print("\n" + "=" * 50)
    print("📊 Fix Results Summary:")
    for service, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {service}")
    
    # Verify all fixes
    print("\n" + "=" * 50)
    if verify_fixes():
        print("\n✅ All analytics services updated successfully!")
        print(f"💾 Backups saved to: {BACKUP_DIR}")
    else:
        print("\n⚠️  Some services may need manual review")
        print(f"💾 Check backups at: {BACKUP_DIR}")
    
    # Provide testing instructions
    print("\n" + "=" * 50)
    print("📝 Next Steps:")
    print("1. Run tests: python comprehensive_test_suite.py")
    print("2. Check executive dashboard: /tab7")
    print("3. Verify inventory analytics: /inventory-analytics")
    print("4. Test financial analytics endpoints")
    print("5. Monitor logs for any store code errors")

if __name__ == "__main__":
    main()
