#!/usr/bin/env python3
import pandas as pd
import sys
import os
from datetime import datetime
from app import create_app, db
from app.models.financial_models import PLData, PayrollTrendsData, ScorecardTrendsData

def clean_currency_value(value):
    """Clean currency values by removing quotes, commas, and converting to float."""
    if pd.isna(value) or value == '' or value == 0:
        return None
    if isinstance(value, str):
        value = value.replace('"', '').replace(',', '').strip()
        if value == '' or value == '-' or value == '0':
            return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def parse_date_string(date_str):
    """Parse date string from CSV format."""
    if pd.isna(date_str) or date_str == '':
        return None
    
    date_str = str(date_str).strip()
    
    # Handle various date formats
    date_formats = [
        '%m/%d/%Y',  # 1/16/2022
        '%m/%d/%y',  # 1/16/22
        '%Y-%m-%d',  # 2022-01-16
        '%d/%m/%Y',  # 16/1/2022
        '%d/%m/%y'   # 16/1/22
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt).date()
            # Handle 2-digit years
            if parsed_date.year < 1950:
                parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
            return parsed_date
        except ValueError:
            continue
    
    print(f"Warning: Could not parse date: {date_str}")
    return None

def import_payroll_trends():
    """Import PayrollTrends CSV data."""
    file_path = '/home/tim/RFID3/shared/POR/PayrollTrends8.26.25.csv'
    print(f"Importing Payroll Trends data from {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        print(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        print("Columns:", df.columns.tolist())
        
        # Clear existing data
        db.session.query(PayrollTrendsData).delete()
        
        imported_count = 0
        for index, row in df.iterrows():
            try:
                week_ending = parse_date_string(row.iloc[0])  # First column is date
                if not week_ending:
                    continue
                
                # Process each location (6800, 3607, 8101, 728)
                locations = ['6800', '3607', '8101', '728']
                
                for i, location in enumerate(locations):
                    base_col = 1 + (i * 4)  # Each location has 4 columns
                    
                    if base_col + 3 < len(row):
                        rental_revenue = clean_currency_value(row.iloc[base_col])
                        all_revenue = clean_currency_value(row.iloc[base_col + 1])
                        payroll_amount = clean_currency_value(row.iloc[base_col + 2])
                        wage_hours = clean_currency_value(row.iloc[base_col + 3])
                        
                        if any([rental_revenue, all_revenue, payroll_amount, wage_hours]):
                            payroll_record = PayrollTrendsData(
                                week_ending=week_ending,
                                location_code=location,
                                rental_revenue=rental_revenue,
                                all_revenue=all_revenue,
                                payroll_amount=payroll_amount,
                                wage_hours=wage_hours
                            )
                            db.session.add(payroll_record)
                            imported_count += 1
                        
            except Exception as e:
                print(f"Error processing row {index}: {e}")
                continue
        
        db.session.commit()
        print(f"Successfully imported {imported_count} payroll trends records")
        
    except Exception as e:
        print(f"Error importing payroll trends: {e}")
        db.session.rollback()

def import_scorecard_trends():
    """Import ScorecardTrends CSV data."""
    file_path = '/home/tim/RFID3/shared/POR/ScorecardTrends8.26.25.csv'
    print(f"Importing Scorecard Trends data from {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        print(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        
        # Clear existing data
        db.session.query(ScorecardTrendsData).delete()
        
        imported_count = 0
        for index, row in df.iterrows():
            try:
                week_ending = parse_date_string(row.iloc[0])
                if not week_ending:
                    continue
                
                scorecard_record = ScorecardTrendsData(
                    week_ending=week_ending,
                    total_weekly_revenue=clean_currency_value(row.iloc[1]) if len(row) > 1 else None,
                    revenue_3607=clean_currency_value(row.iloc[2]) if len(row) > 2 else None,
                    revenue_6800=clean_currency_value(row.iloc[3]) if len(row) > 3 else None,
                    revenue_728=clean_currency_value(row.iloc[4]) if len(row) > 4 else None,
                    revenue_8101=clean_currency_value(row.iloc[5]) if len(row) > 5 else None,
                    new_contracts_3607=int(clean_currency_value(row.iloc[6]) or 0) if len(row) > 6 else None,
                    new_contracts_6800=int(clean_currency_value(row.iloc[7]) or 0) if len(row) > 7 else None,
                    new_contracts_728=int(clean_currency_value(row.iloc[8]) or 0) if len(row) > 8 else None,
                    new_contracts_8101=int(clean_currency_value(row.iloc[9]) or 0) if len(row) > 9 else None,
                    deliveries_scheduled_8101=int(clean_currency_value(row.iloc[10]) or 0) if len(row) > 10 else None,
                    reservation_next14_3607=clean_currency_value(row.iloc[11]) if len(row) > 11 else None,
                    reservation_next14_6800=clean_currency_value(row.iloc[12]) if len(row) > 12 else None,
                    reservation_next14_728=clean_currency_value(row.iloc[13]) if len(row) > 13 else None,
                    reservation_next14_8101=clean_currency_value(row.iloc[14]) if len(row) > 14 else None,
                    total_reservation_3607=clean_currency_value(row.iloc[15]) if len(row) > 15 else None,
                    total_reservation_6800=clean_currency_value(row.iloc[16]) if len(row) > 16 else None,
                    total_reservation_728=clean_currency_value(row.iloc[17]) if len(row) > 17 else None,
                    total_reservation_8101=clean_currency_value(row.iloc[18]) if len(row) > 18 else None,
                    ar_over_45_days_percent=clean_currency_value(row.iloc[19]) if len(row) > 19 else None,
                    total_discount=clean_currency_value(row.iloc[20]) if len(row) > 20 else None,
                    week_number=int(clean_currency_value(row.iloc[21]) or 0) if len(row) > 21 else None,
                    open_quotes_8101=int(clean_currency_value(row.iloc[22]) or 0) if len(row) > 22 else None,
                    total_ar_cash_customers=clean_currency_value(row.iloc[23]) if len(row) > 23 else None
                )
                
                db.session.add(scorecard_record)
                imported_count += 1
                        
            except Exception as e:
                print(f"Error processing scorecard row {index}: {e}")
                continue
        
        db.session.commit()
        print(f"Successfully imported {imported_count} scorecard trends records")
        
    except Exception as e:
        print(f"Error importing scorecard trends: {e}")
        db.session.rollback()

def import_pl_data():
    """Import P&L CSV data."""
    file_path = '/home/tim/RFID3/shared/POR/PL8.28.25.csv'
    print(f"Importing P&L data from {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        print(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        
        # Clear existing data
        db.session.query(PLData).delete()
        
        imported_count = 0
        current_category = "Unknown"
        
        for index, row in df.iterrows():
            try:
                # First column contains account codes or category names
                first_col = str(row.iloc[0]).strip()
                
                # Skip header rows and empty rows
                if pd.isna(row.iloc[0]) or first_col == '' or 'KVC Companies' in first_col:
                    continue
                
                # Check if this is a category header (no numeric account code)
                if not first_col.isdigit() and first_col not in ['3607', '6800', '728', '8101']:
                    current_category = first_col
                    continue
                
                account_code = first_col
                
                # Process each month's data (columns represent different periods)
                # Based on the CSV structure, columns 1+ contain monthly data
                for col_idx in range(1, len(row)):
                    if col_idx >= len(df.columns):
                        break
                        
                    amount = clean_currency_value(row.iloc[col_idx])
                    if amount is not None:
                        # Try to determine month/year from column header if available
                        col_name = df.columns[col_idx] if col_idx < len(df.columns) else f"Column_{col_idx}"
                        
                        pl_record = PLData(
                            account_code=account_code,
                            account_name=current_category,
                            period_month=col_name,  # Will contain the actual column header
                            period_year=2025,  # Default year, could be parsed from headers
                            amount=amount,
                            category=current_category
                        )
                        
                        db.session.add(pl_record)
                        imported_count += 1
                        
            except Exception as e:
                print(f"Error processing P&L row {index}: {e}")
                continue
        
        db.session.commit()
        print(f"Successfully imported {imported_count} P&L records")
        
    except Exception as e:
        print(f"Error importing P&L data: {e}")
        db.session.rollback()

def main():
    """Main import function."""
    app = create_app()
    
    with app.app_context():
        print("Starting financial CSV imports...")
        
        try:
            print("\n1. Importing Payroll Trends...")
            import_payroll_trends()
            
            print("\n2. Importing Scorecard Trends...")
            import_scorecard_trends()
            
            print("\n3. Importing P&L Data...")
            import_pl_data()
            
            print("\nAll financial CSV imports completed successfully!")
            
        except Exception as e:
            print(f"Error during import: {e}")
            return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())