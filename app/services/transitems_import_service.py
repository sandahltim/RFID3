"""
Transaction Items Import Service

Imports transitems CSV files that link Contract Numbers to ItemNum (equipment) 
and provide customer transaction details.
"""

import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text
from app import db

logger = logging.getLogger(__name__)

class TransitemsImportService:
    """Service for importing transaction items data from CSV files"""
    
    def __init__(self):
        self.batch_size = 1000
        self.table_name = 'pos_transaction_items'
        
    def import_transitems_csv(self, file_path: str, import_batch: str = None) -> Dict:
        """
        Import transitems CSV file into the database
        
        Args:
            file_path: Path to the transitems CSV file
            import_batch: Optional batch identifier for tracking
            
        Returns:
            Dict with import results and statistics
        """
        try:
            logger.info(f"Starting transitems import from: {file_path}")
            start_time = datetime.now()
            
            # Generate import batch ID if not provided
            if not import_batch:
                import_batch = f"transitems_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Read CSV file
            logger.info("Reading transitems CSV file...")
            df = pd.read_csv(file_path)
            
            # Validate and clean data
            cleaned_df = self._clean_and_validate_data(df)
            
            # Check if table exists, create if needed
            self._ensure_table_exists()
            
            # Clear existing data for fresh import
            self._clear_existing_data(import_batch)
            
            # Import in batches
            total_rows = len(cleaned_df)
            imported_rows = 0
            
            logger.info(f"Importing {total_rows} transaction items in batches of {self.batch_size}")
            
            for i in range(0, total_rows, self.batch_size):
                batch_df = cleaned_df.iloc[i:i + self.batch_size].copy()
                batch_df['import_batch'] = import_batch
                batch_df['created_at'] = datetime.now()
                
                # Insert batch into database
                batch_df.to_sql(
                    name=self.table_name,
                    con=db.engine,
                    if_exists='append',
                    index=False,
                    method='multi'
                )
                
                imported_rows += len(batch_df)
                if i % (self.batch_size * 10) == 0:  # Log every 10 batches
                    logger.info(f"Imported {imported_rows:,}/{total_rows:,} transaction items...")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Gather statistics
            stats = self._gather_import_statistics(import_batch, total_rows)
            
            logger.info(f"✅ Transitems import completed: {imported_rows:,} rows in {duration:.2f}s")
            
            return {
                'success': True,
                'import_batch': import_batch,
                'file_path': file_path,
                'imported_rows': imported_rows,
                'total_rows': total_rows,
                'duration_seconds': duration,
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"❌ Error importing transitems: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path,
                'imported_rows': 0
            }
    
    def _clean_and_validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate the transitems data"""
        logger.info("Cleaning and validating transitems data...")
        
        # Standardize column names
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
        
        # Map to standard column names if needed
        column_mapping = {
            'contract_no': 'contract_number',
            'itemnum': 'item_number',
            'desc': 'description',
            'due_date': 'due_date',
            'due_time': 'due_time',
            'line_status': 'line_status',
            'price': 'price',
            'qty': 'quantity',
            'hours': 'hours',
            'dmgwvr': 'damage_waiver',
            'retailprice': 'retail_price',
            'linenumber': 'line_number'
        }
        
        # Rename columns to standard names
        df = df.rename(columns=column_mapping)
        
        # Convert data types
        numeric_columns = ['price', 'quantity', 'hours', 'damage_waiver', 'retail_price', 'line_number']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Convert date/time columns
        if 'due_date' in df.columns:
            df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')
        
        # Clean string columns
        string_columns = ['contract_number', 'item_number', 'description', 'line_status']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        # Remove rows with missing critical data
        initial_rows = len(df)
        df = df.dropna(subset=['contract_number', 'item_number'])
        removed_rows = initial_rows - len(df)
        
        if removed_rows > 0:
            logger.warning(f"Removed {removed_rows} rows with missing contract_number or item_number")
        
        logger.info(f"Cleaned data: {len(df):,} valid transaction items")
        return df
    
    def _ensure_table_exists(self):
        """Create the transaction items table if it doesn't exist"""
        create_table_sql = text("""
            CREATE TABLE IF NOT EXISTS pos_transaction_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contract_number VARCHAR(50) NOT NULL,
                item_number VARCHAR(50) NOT NULL,
                quantity DECIMAL(10,2) DEFAULT 0,
                hours DECIMAL(10,2) DEFAULT 0,
                due_date DATETIME NULL,
                due_time VARCHAR(10) NULL,
                line_status VARCHAR(10) NULL,
                price DECIMAL(15,2) DEFAULT 0,
                description TEXT NULL,
                damage_waiver DECIMAL(10,2) DEFAULT 0,
                retail_price DECIMAL(15,2) DEFAULT 0,
                line_number INT DEFAULT 1,
                import_batch VARCHAR(50) NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_contract_number (contract_number),
                INDEX idx_item_number (item_number),
                INDEX idx_due_date (due_date),
                INDEX idx_import_batch (import_batch),
                INDEX idx_contract_item (contract_number, item_number)
            )
        """)
        
        db.session.execute(create_table_sql)
        db.session.commit()
        logger.info("✅ Transaction items table ready")
    
    def _clear_existing_data(self, import_batch: str):
        """Clear existing data for this import batch"""
        delete_sql = text("DELETE FROM pos_transaction_items WHERE import_batch = :batch")
        result = db.session.execute(delete_sql, {'batch': import_batch})
        db.session.commit()
        logger.info(f"Cleared {result.rowcount} existing records for batch: {import_batch}")
    
    def _gather_import_statistics(self, import_batch: str, expected_rows: int) -> Dict:
        """Gather statistics about the import"""
        stats_sql = text("""
            SELECT 
                COUNT(*) as total_items,
                COUNT(DISTINCT contract_number) as unique_contracts,
                COUNT(DISTINCT item_number) as unique_items,
                SUM(price) as total_price,
                MIN(due_date) as earliest_date,
                MAX(due_date) as latest_date
            FROM pos_transaction_items 
            WHERE import_batch = :batch
        """)
        
        result = db.session.execute(stats_sql, {'batch': import_batch}).fetchone()
        
        return {
            'total_items': result.total_items,
            'unique_contracts': result.unique_contracts,
            'unique_items': result.unique_items,
            'total_value': float(result.total_price) if result.total_price else 0,
            'date_range': {
                'earliest': result.earliest_date.isoformat() if result.earliest_date else None,
                'latest': result.latest_date.isoformat() if result.latest_date else None
            },
            'import_success_rate': (result.total_items / expected_rows * 100) if expected_rows > 0 else 0
        }
    
    def get_contract_details(self, contract_number: str) -> List[Dict]:
        """Get all items for a specific contract"""
        query_sql = text("""
            SELECT 
                contract_number,
                item_number,
                quantity,
                hours,
                price,
                description,
                line_status,
                due_date
            FROM pos_transaction_items 
            WHERE contract_number = :contract_number
            ORDER BY line_number
        """)
        
        results = db.session.execute(query_sql, {'contract_number': contract_number}).fetchall()
        
        return [
            {
                'contract_number': row.contract_number,
                'item_number': row.item_number,
                'quantity': float(row.quantity),
                'hours': float(row.hours),
                'price': float(row.price),
                'description': row.description,
                'line_status': row.line_status,
                'due_date': row.due_date.isoformat() if row.due_date else None
            }
            for row in results
        ]
    
    def get_item_contracts(self, item_number: str) -> List[Dict]:
        """Get all contracts for a specific item"""
        query_sql = text("""
            SELECT 
                contract_number,
                quantity,
                hours,
                price,
                line_status,
                due_date
            FROM pos_transaction_items 
            WHERE item_number = :item_number
            ORDER BY due_date DESC
        """)
        
        results = db.session.execute(query_sql, {'item_number': item_number}).fetchall()
        
        return [
            {
                'contract_number': row.contract_number,
                'quantity': float(row.quantity),
                'hours': float(row.hours),
                'price': float(row.price),
                'line_status': row.line_status,
                'due_date': row.due_date.isoformat() if row.due_date else None
            }
            for row in results
        ]