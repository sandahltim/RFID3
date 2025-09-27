#!/usr/bin/env python3
"""
Update Remaining Analytics Services to Use Centralized Store Configuration
"""

import os
import re
from pathlib import Path
from datetime import datetime

# Configuration
PROJECT_ROOT = Path("/home/tim/RFID3-RFID-KVC")
BACKUP_DIR = PROJECT_ROOT / "backups" / f"analytics_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Import statement to add
STORE_IMPORT = """from app.config.stores import (
    STORES, STORE_MAPPING, STORE_MANAGERS,
    STORE_BUSINESS_TYPES, STORE_OPENING_DATES,
    get_store_name, get_store_manager, get_store_business_type,
    get_store_opening_date, get_active_store_codes
)
"""

# Services to update
SERVICES_TO_UPDATE = [
    "app/services/minnesota_seasonal_service.py",
    "app/services/weather_predictive_service.py",
    "app/services/minnesota_industry_analytics.py",
    "app/services/equipment_categorization_service.py",
    "app/services/store_correlation_service.py",
    "app/services/cross_system_analytics.py",
    "app/services/bi_analytics.py"
]

def backup_file(file_path):
    """Create backup of file"""
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

def add_import_statement(content, file_name):
    """Add import statement to file content"""
    # Check if import already exists
    if "from app.config.stores import" in content:
        return content
    
    # Find the right place to add import
    lines = content.split('\n')
    
    # Find last import line
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            last_import_idx = i
    
    # Insert after last import
    lines.insert(last_import_idx + 1, STORE_IMPORT)
    return '\n'.join(lines)

def replace_hardcoded_stores(content):
    """Replace hardcoded store references with centralized config"""
    
    # Pattern replacements
    replacements = [
        # Replace hardcoded store lists
        (r"stores\s*=\s*\['3607',\s*'6800',\s*'728',\s*'8101'\]", 
         "stores = get_active_store_codes()"),
        
        (r"store_codes\s*=\s*\['3607',\s*'6800',\s*'728',\s*'8101'\]",
         "store_codes = get_active_store_codes()"),
        
        # Replace hardcoded store names
        (r"'Wayzata'", "get_store_name('3607')"),
        (r"'Brooklyn Park'", "get_store_name('6800')"),
        (r"'Fridley'", "get_store_name('8101')"),
        (r"'Elk River'", "get_store_name('728')"),
        
        # Replace store mappings
        (r"store_mapping\s*=\s*{[^}]+}", 
         "store_mapping = STORE_MAPPING"),
        
        # Replace IN clauses in SQL
        (r"IN\s*\('3607',\s*'6800',\s*'728',\s*'8101'\)",
         "IN ({})'.format(','.join([\"'{}'\".format(s) for s in get_active_store_codes()]))"),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    return content

def update_service_file(file_path):
    """Update a service file to use centralized store config"""
    try:
        full_path = PROJECT_ROOT / file_path
        
        if not full_path.exists():
            print(f"❌ File not found: {file_path}")
            return False
        
        # Backup first
        backup_file(file_path)
        
        # Read content
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Add import
        content = add_import_statement(content, file_path)
        
        # Replace hardcoded references
        content = replace_hardcoded_stores(content)
        
        # Special handling for specific files
        if "minnesota_seasonal_service.py" in file_path:
            content = fix_seasonal_service(content)
        elif "weather_predictive_service.py" in file_path:
            content = fix_weather_predictive(content)
        elif "minnesota_industry_analytics.py" in file_path:
            content = fix_industry_analytics(content)
        elif "equipment_categorization_service.py" in file_path:
            content = fix_equipment_categorization(content)
        elif "store_correlation_service.py" in file_path:
            content = fix_store_correlation(content)
        elif "cross_system_analytics.py" in file_path:
            content = fix_cross_system(content)
        elif "bi_analytics.py" in file_path:
            content = fix_bi_analytics(content)
        
        # Write updated content
        with open(full_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update {file_path}: {e}")
        return False

def fix_seasonal_service(content):
    """Fix Minnesota seasonal service specific issues"""
    # Replace any store-specific seasonal logic
    content = re.sub(
        r"if store_code == '728':",
        "if get_store_business_type(store_code) == '100% Events (Broadway Tent & Event)':",
        content
    )
    
    content = re.sub(
        r"if store_code in \['3607', '6800', '8101'\]:",
        "if 'Construction' in get_store_business_type(store_code) or 'DIY' in get_store_business_type(store_code):",
        content
    )
    
    return content

def fix_weather_predictive(content):
    """Fix weather predictive service"""
    # Update store-specific weather predictions
    content = re.sub(
        r"store_names = {[^}]+}",
        "store_names = {code: get_store_name(code) for code in get_active_store_codes()}",
        content
    )
    
    return content

def fix_industry_analytics(content):
    """Fix industry analytics service"""
    # Update industry mix calculations
    content = re.sub(
        r"for store in \['3607', '6800', '728', '8101'\]:",
        "for store in get_active_store_codes():",
        content
    )
    
    return content

def fix_equipment_categorization(content):
    """Fix equipment categorization service"""
    # Update store categorization logic
    content = re.sub(
        r"valid_stores = \['3607', '6800', '728', '8101'\]",
        "valid_stores = get_active_store_codes()",
        content
    )
    
    return content

def fix_store_correlation(content):
    """Fix store correlation service"""
    # Update correlation calculations
    content = re.sub(
        r"stores_to_analyze = \['3607', '6800', '728', '8101'\]",
        "stores_to_analyze = get_active_store_codes()",
        content
    )
    
    # Fix manager correlations
    content = re.sub(
        r"managers = {'3607': 'TYLER', '6800': 'ZACK', '728': 'BRUCE', '8101': 'TIM'}",
        "managers = {code: get_store_manager(code) for code in get_active_store_codes()}",
        content
    )
    
    return content

def fix_cross_system(content):
    """Fix cross system analytics"""
    # Update cross-system store references
    content = re.sub(
        r"all_stores = \['3607', '6800', '728', '8101'\]",
        "all_stores = get_active_store_codes()",
        content
    )
    
    return content

def fix_bi_analytics(content):
    """Fix BI analytics service"""
    # Update BI store references
    content = re.sub(
        r"store_list = \['3607', '6800', '728', '8101'\]",
        "store_list = get_active_store_codes()",
        content
    )
    
    # Update store performance metrics
    content = re.sub(
        r"store_performance\[store\] = {[^}]+}",
        """store_performance[store] = {
            'name': get_store_name(store),
            'manager': get_store_manager(store),
            'business_type': get_store_business_type(store),
            'opened': get_store_opening_date(store)
        }""",
        content
    )
    
    return content

def verify_updates():
    """Verify all files were updated correctly"""
    print("\n🔍 Verifying updates...")
    
    all_good = True
    for service_path in SERVICES_TO_UPDATE:
        file_path = PROJECT_ROOT / service_path
        if file_path.exists():
            with open(file_path, 'r') as f:
                content = f.read()
            
            if "from app.config.stores import" in content:
                print(f"✅ {service_path}: Successfully updated")
            else:
                print(f"⚠️  {service_path}: May need manual review")
                all_good = False
        else:
            print(f"❌ {service_path}: File not found")
            all_good = False
    
    return all_good

def main():
    """Main execution"""
    print("🚀 Updating Remaining Analytics Services")
    print(f"📁 Project root: {PROJECT_ROOT}")
    print(f"💾 Backup directory: {BACKUP_DIR}")
    print("-" * 50)
    
    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Update each service
    results = {}
    for service_path in SERVICES_TO_UPDATE:
        service_name = Path(service_path).stem
        results[service_name] = update_service_file(service_path)
    
    print("\n" + "=" * 50)
    print("📊 Update Results Summary:")
    for service, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {service}")
    
    # Verify all updates
    print("\n" + "=" * 50)
    if verify_updates():
        print("\n✅ All remaining analytics services updated successfully!")
    else:
        print("\n⚠️  Some services may need manual review")
    
    print(f"\n💾 Backups saved to: {BACKUP_DIR}")
    
    # Summary of changes
    print("\n" + "=" * 50)
    print("📝 Key Changes Made:")
    print("1. Added centralized store configuration imports")
    print("2. Replaced hardcoded store codes with get_active_store_codes()")
    print("3. Updated store name references to use get_store_name()")
    print("4. Fixed manager assignments to use get_store_manager()")
    print("5. Updated business type checks to use get_store_business_type()")
    print("6. Corrected SQL IN clauses to use dynamic store lists")

if __name__ == "__main__":
    main()
