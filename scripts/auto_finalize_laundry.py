#!/usr/bin/env python3
"""
Auto-finalization script for laundry contracts
Runs on Tuesday and Thursday at 7am to automatically finalize active contracts
"""

import sys
import os
from datetime import datetime, timedelta
import logging

# Add the project directory to the Python path
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_dir)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.db_models import LaundryContractStatus, ItemMaster, HandCountedItems
from config import DB_CONFIG

# Set up logging
log_dir = os.path.join(project_dir, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'auto_finalize_laundry.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Create database connection"""
    try:
        db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}&collation={DB_CONFIG['collation']}"
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        return Session()
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

def get_contracts_to_finalize(session, min_age_hours=24):
    """
    Get active laundry contracts that should be auto-finalized
    Criteria:
    - Status is 'active' or no status record exists
    - Contract has items (RFID or hand-counted)
    - Contract is at least min_age_hours old
    """
    try:
        # Get current time minus minimum age
        cutoff_time = datetime.now() - timedelta(hours=min_age_hours)
        
        # Find L contracts with items that are old enough
        # First get contracts from ItemMaster
        rfid_contracts = session.execute(text("""
            SELECT DISTINCT im.last_contract_num as contract_number,
                   MIN(t.scan_date) as earliest_scan
            FROM id_item_master im
            LEFT JOIN id_transactions t ON im.last_contract_num = t.contract_number 
                AND t.scan_type = 'Rental'
            WHERE im.last_contract_num IS NOT NULL 
                AND im.last_contract_num != '00000'
                AND UPPER(im.last_contract_num) LIKE 'L%'
                AND im.status IN ('On Rent', 'Delivered')
            GROUP BY im.last_contract_num
            HAVING COUNT(im.tag_id) > 0
                AND MIN(t.scan_date) < :cutoff_time
        """), {'cutoff_time': cutoff_time}).fetchall()
        
        # Get contracts from hand-counted items
        hand_counted_contracts = session.execute(text("""
            SELECT DISTINCT hci.contract_number,
                   MIN(hci.timestamp) as earliest_timestamp
            FROM id_hand_counted_items hci
            WHERE hci.contract_number IS NOT NULL
                AND UPPER(hci.contract_number) LIKE 'L%'
                AND hci.action = 'Added'
                AND hci.timestamp < :cutoff_time
            GROUP BY hci.contract_number
            HAVING SUM(CASE WHEN hci.action = 'Added' THEN hci.quantity ELSE 0 END) - 
                   SUM(CASE WHEN hci.action = 'Removed' THEN hci.quantity ELSE 0 END) > 0
        """), {'cutoff_time': cutoff_time}).fetchall()
        
        # Combine and deduplicate contracts
        all_contracts = set()
        for contract in rfid_contracts:
            all_contracts.add(contract.contract_number)
        for contract in hand_counted_contracts:
            all_contracts.add(contract.contract_number)
        
        # Filter out contracts that are already finalized or returned
        contracts_to_finalize = []
        for contract_number in all_contracts:
            status_record = session.query(LaundryContractStatus).filter(
                LaundryContractStatus.contract_number == contract_number
            ).first()
            
            if not status_record or status_record.status == 'active':
                contracts_to_finalize.append(contract_number)
        
        logger.info(f"Found {len(contracts_to_finalize)} contracts to auto-finalize: {contracts_to_finalize}")
        return contracts_to_finalize
        
    except Exception as e:
        logger.error(f"Error finding contracts to finalize: {str(e)}", exc_info=True)
        return []

def finalize_contract(session, contract_number):
    """Finalize a single contract"""
    try:
        # Check if status record already exists
        status_record = session.query(LaundryContractStatus).filter(
            LaundryContractStatus.contract_number == contract_number
        ).first()
        
        if status_record:
            # Update existing record
            status_record.status = 'finalized'
            status_record.finalized_date = datetime.now()
            status_record.finalized_by = 'auto-system'
            status_record.notes = (status_record.notes or '') + f"\nAuto-finalized on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        else:
            # Create new record
            status_record = LaundryContractStatus(
                contract_number=contract_number,
                status='finalized',
                finalized_date=datetime.now(),
                finalized_by='auto-system',
                notes=f"Auto-finalized on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            session.add(status_record)
        
        session.commit()
        logger.info(f"Successfully auto-finalized contract {contract_number}")
        return True
        
    except Exception as e:
        logger.error(f"Error finalizing contract {contract_number}: {str(e)}", exc_info=True)
        session.rollback()
        return False

def main():
    """Main execution function"""
    logger.info("Starting auto-finalization process")
    
    # Check if today is Wednesday (2) or Friday (4)
    today = datetime.now().weekday()
    if today not in [2, 4]:  # 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, etc.
        logger.info(f"Today is not Wednesday or Friday (weekday={today}). Skipping auto-finalization.")
        return
    
    session = None
    try:
        session = get_database_connection()
        
        # Get contracts to finalize (older than 24 hours)
        contracts_to_finalize = get_contracts_to_finalize(session, min_age_hours=24)
        
        if not contracts_to_finalize:
            logger.info("No contracts found for auto-finalization")
            return
        
        # Finalize each contract
        successful_count = 0
        failed_count = 0
        
        for contract_number in contracts_to_finalize:
            if finalize_contract(session, contract_number):
                successful_count += 1
            else:
                failed_count += 1
        
        logger.info(f"Auto-finalization completed: {successful_count} successful, {failed_count} failed")
        
        # Write summary to file for monitoring
        summary_file = os.path.join(log_dir, 'last_auto_finalize.json')
        import json
        summary = {
            'timestamp': datetime.now().isoformat(),
            'day': datetime.now().strftime('%A'),
            'contracts_processed': len(contracts_to_finalize),
            'successful': successful_count,
            'failed': failed_count,
            'contracts': contracts_to_finalize
        }
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error in auto-finalization process: {str(e)}", exc_info=True)
    finally:
        if session:
            session.close()
        logger.info("Auto-finalization process completed")

if __name__ == "__main__":
    main()