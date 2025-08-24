#!/home/tim/RFID3/venv/bin/python3
"""
Weekly Contract Snapshots Script
Version: 2025-08-24-v1

This script creates snapshots of all active contracts for historical preservation.
Designed to run on Wednesdays and Fridays at 7:00 AM via cron.

Usage:
    python3 /home/tim/RFID3/scripts/create_weekly_snapshots.py

Cron entry:
    # Contract snapshots on Wed/Fri at 7 AM
    0 7 * * 3,5 cd /home/tim/RFID3 && /home/tim/RFID3/venv/bin/python3 scripts/create_weekly_snapshots.py >> logs/snapshot_cron.log 2>&1
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timezone
import json
import logging

def setup_logging():
    """Set up logging for the cron job."""
    log_file = '/home/tim/RFID3/logs/snapshot_automation.log'
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    """Main function to run weekly snapshots."""
    logger = setup_logging()
    
    try:
        logger.info("=" * 60)
        logger.info("STARTING WEEKLY CONTRACT SNAPSHOTS")
        logger.info(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 60)
        
        # Set environment flag to skip API client initialization
        os.environ['SNAPSHOT_AUTOMATION'] = '1'
        
        # Import Flask app and services
        from app import create_app
        from app.services.scheduled_snapshots import ScheduledSnapshotService
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            # Run weekly snapshots
            results = ScheduledSnapshotService.create_weekly_snapshots()
            
            # Log results
            logger.info("SNAPSHOT RESULTS:")
            logger.info(f"Total contracts found: {results['total_contracts']}")
            logger.info(f"Successful snapshots: {results['successful_snapshots']}")
            logger.info(f"Failed snapshots: {results['failed_snapshots']}")
            logger.info(f"Total items snapshotted: {results['total_items_snapshotted']}")
            
            if results['errors']:
                logger.error("ERRORS ENCOUNTERED:")
                for error in results['errors']:
                    logger.error(f"  - {error}")
            
            # Log contract details
            logger.info("CONTRACTS PROCESSED:")
            for contract in results['contracts_processed']:
                status_emoji = "✅" if contract['status'] == 'success' else "⚠️" if 'skipped' in contract['status'] else "❌"
                logger.info(f"  {status_emoji} {contract['contract_number']} ({contract['client_name']}) - {contract['items_count']} items - {contract['status']}")
            
            # Run cleanup of old snapshots
            try:
                deleted_count = ScheduledSnapshotService.cleanup_old_periodic_snapshots(days_to_keep=30)
                logger.info(f"Cleaned up {deleted_count} old periodic snapshots")
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")
            
            # Write summary to JSON file for monitoring
            summary_file = '/home/tim/RFID3/logs/last_snapshot_run.json'
            summary = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'results': results,
                'cleanup_deleted': deleted_count if 'deleted_count' in locals() else 0
            }
            
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
        logger.info("=" * 60)
        logger.info("WEEKLY SNAPSHOTS COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR in weekly snapshots: {str(e)}", exc_info=True)
        
        # Write error to summary file
        try:
            error_summary = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e),
                'success': False
            }
            with open('/home/tim/RFID3/logs/last_snapshot_run.json', 'w') as f:
                json.dump(error_summary, f, indent=2)
        except:
            pass
        
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)