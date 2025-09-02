#!/usr/bin/env python3
"""Fix the minnesota_industry_analytics.py import issue"""

file_path = "/home/tim/RFID3/app/services/minnesota_industry_analytics.py"

# Read the file
with open(file_path, 'r') as f:
    lines = f.readlines()

# Remove the misplaced import at the end
cleaned_lines = []
for line in lines:
    if line.strip() == "import calendar" and len(cleaned_lines) > 700:
        # Skip the misplaced import at the end
        break
    cleaned_lines.append(line)

# Make sure imports are at the top
import_added = False
final_lines = []

for i, line in enumerate(cleaned_lines):
    if not import_added and (line.startswith('from app.services') or line.startswith('import json')):
        # Add the store import before other app imports
        if 'from app.config.stores import' not in ''.join(cleaned_lines[:i+10]):
            final_lines.append('from app.config.stores import (\n')
            final_lines.append('    STORES, STORE_MAPPING, STORE_MANAGERS,\n')
            final_lines.append('    STORE_BUSINESS_TYPES, STORE_OPENING_DATES,\n')
            final_lines.append('    get_store_name, get_store_manager, get_store_business_type,\n')
            final_lines.append('    get_store_opening_date, get_active_store_codes\n')
            final_lines.append(')\n')
            import_added = True
    final_lines.append(line)

# Write the fixed file
with open(file_path, 'w') as f:
    f.writelines(final_lines)

print("Fixed minnesota_industry_analytics.py")
