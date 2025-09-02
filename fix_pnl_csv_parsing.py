#!/usr/bin/env python3
"""
Fix P&L CSV Parsing Logic
This script updates the P&L import service with proper CSV parsing logic
"""

# First, let's create a corrected version of the extract_financial_data_from_csv method
corrected_method = '''
    def extract_financial_data_from_csv(self, csv_path: str) -> List[Dict]:
        """Extract and normalize financial data from P&L CSV with corrected structure parsing"""
        logger.info(f"Starting corrected P&L CSV import from: {csv_path}")
        
        try:
            # Read the full CSV
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            logger.info(f"Read full CSV with shape: {df.shape}")
            
            financial_records = []
            
            # Based on CSV analysis:
            # Row 1 (index 0): Headers showing store codes and categories
            # Row 2+ (index 1+): Monthly data with format: Month, Year, Store1_Value, Store2_Value, ...
            # TTM rows should be skipped
            
            for idx, row in df.iterrows():
                # Skip header row (index 0)
                if idx == 0:
                    continue
                
                # Extract month and year from first two columns
                month_str = str(row.iloc[0]).strip() if not pd.isna(row.iloc[0]) else ""
                year_str = str(row.iloc[1]).strip() if len(row) > 1 and not pd.isna(row.iloc[1]) else ""
                
                # Skip TTM (Trailing Twelve Months) and other summary rows
                if not month_str or month_str.upper() in ['TTM', 'TOTAL', ''] or not year_str:
                    continue
                
                # Parse date
                parsed_date = self.parse_month_year(month_str, year_str)
                if not parsed_date:
                    logger.debug(f"Skipping row {idx}: could not parse date from '{month_str}' '{year_str}'")
                    continue
                
                logger.debug(f"Processing row {idx}: {month_str} {year_str} -> {parsed_date}")
                
                # Extract store data from specific columns
                # Based on header analysis: columns 2-5 contain the main store revenue data
                store_data_positions = {
                    2: '3607',  # Wayzata
                    3: '6800',  # Brooklyn Park
                    4: '728',   # Elk River  
                    5: '8101'   # Fridley
                }
                
                for col_pos, store_code in store_data_positions.items():
                    if col_pos < len(row):
                        value = row.iloc[col_pos]
                        cleaned_value = self.clean_currency_value(value)
                        
                        if cleaned_value is not None and cleaned_value != 0:
                            record = {
                                'store_code': store_code,
                                'store_name': get_store_name(store_code),
                                'month_year': parsed_date,
                                'metric_type': 'Rental Revenue',  # Primary revenue metric
                                'actual_amount': cleaned_value,
                                'projected_amount': None,
                                'data_source': 'CSV_IMPORT_PL'
                            }
                            financial_records.append(record)
                            logger.debug(f"Added record: {store_code} {parsed_date} ${cleaned_value}")
                
                # Also extract additional revenue categories from other column groups
                # Columns 7-10 appear to be "Sales Revenue" for each store
                sales_revenue_positions = {
                    7: '3607',   # Wayzata Sales Revenue
                    8: '6800',   # Brooklyn Park Sales Revenue
                    9: '728',    # Elk River Sales Revenue
                    10: '8101'   # Fridley Sales Revenue
                }
                
                for col_pos, store_code in sales_revenue_positions.items():
                    if col_pos < len(row):
                        value = row.iloc[col_pos]
                        cleaned_value = self.clean_currency_value(value)
                        
                        if cleaned_value is not None and cleaned_value != 0:
                            record = {
                                'store_code': store_code,
                                'store_name': get_store_name(store_code),
                                'month_year': parsed_date,
                                'metric_type': 'Sales Revenue',
                                'actual_amount': cleaned_value,
                                'projected_amount': None,
                                'data_source': 'CSV_IMPORT_PL'
                            }
                            financial_records.append(record)
                            logger.debug(f"Added sales record: {store_code} {parsed_date} ${cleaned_value}")
            
            logger.info(f"Extracted {len(financial_records)} financial records from P&L CSV")
            return financial_records
            
        except Exception as e:
            logger.error(f"Error parsing P&L CSV: {e}")
            raise
'''

print("Corrected P&L CSV parsing method:")
print(corrected_method)
