#!/usr/bin/env python3
"""
Nightly Database Backup Script for RFID Dashboard
Performs comprehensive MariaDB backup with rotation and monitoring
"""

import os
import sys
import subprocess
import datetime
import json
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from config import DB_CONFIG, LOG_DIR
from app.services.logger import get_logger

# Configure logging
logger = get_logger('backup_system', level=logging.INFO, log_file=str(LOG_DIR / 'backup_system.log'))

# Backup configuration
BACKUP_DIR = project_root / 'backups'
BACKUP_RETENTION_DAYS = 30
MAX_BACKUP_SIZE_GB = 5.0

def ensure_backup_directory():
    """Create backup directory if it doesn't exist."""
    try:
        BACKUP_DIR.mkdir(exist_ok=True, parents=True)
        logger.info(f"Backup directory ready: {BACKUP_DIR}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup directory: {str(e)}")
        return False

def get_database_size():
    """Get current database size in GB."""
    try:
        cmd = [
            'mysql', 
            f'-h{DB_CONFIG["host"]}', 
            f'-u{DB_CONFIG["user"]}', 
            f'-p{DB_CONFIG["password"]}',
            '-e',
            f"""SELECT 
                ROUND(SUM(data_length + index_length) / 1024 / 1024 / 1024, 2) AS 'DB_Size_GB'
                FROM information_schema.tables 
                WHERE table_schema='{DB_CONFIG["database"]}';"""
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Parse the output to get the size
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            size_gb = float(lines[1])
            logger.info(f"Current database size: {size_gb} GB")
            return size_gb
        return 0.0
    except Exception as e:
        logger.warning(f"Could not determine database size: {str(e)}")
        return 0.0

def perform_backup():
    """Perform the actual database backup."""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"rfid_inventory_backup_{timestamp}.sql"
    backup_path = BACKUP_DIR / backup_filename
    compressed_path = BACKUP_DIR / f"{backup_filename}.gz"
    
    try:
        # Check database size before backup
        db_size = get_database_size()
        if db_size > MAX_BACKUP_SIZE_GB:
            logger.warning(f"Database size ({db_size}GB) exceeds maximum ({MAX_BACKUP_SIZE_GB}GB)")
        
        logger.info(f"Starting backup to {backup_path}")
        
        # Perform mysqldump
        dump_cmd = [
            'mysqldump',
            f'-h{DB_CONFIG["host"]}',
            f'-u{DB_CONFIG["user"]}', 
            f'-p{DB_CONFIG["password"]}',
            '--single-transaction',
            '--routines',
            '--triggers',
            '--quick',
            '--lock-tables=false',
            DB_CONFIG["database"]
        ]
        
        # Write to file and compress simultaneously
        with open(backup_path, 'w') as backup_file:
            result = subprocess.run(dump_cmd, stdout=backup_file, stderr=subprocess.PIPE, text=True)
            
        if result.returncode != 0:
            logger.error(f"mysqldump failed with error: {result.stderr}")
            return None
            
        # Compress the backup
        compress_cmd = ['gzip', str(backup_path)]
        compress_result = subprocess.run(compress_cmd, capture_output=True, text=True)
        
        if compress_result.returncode == 0:
            backup_size = compressed_path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"Backup completed successfully: {compressed_path} ({backup_size:.2f} MB)")
            return compressed_path
        else:
            logger.error(f"Compression failed: {compress_result.stderr}")
            return backup_path if backup_path.exists() else None
            
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}", exc_info=True)
        return None

def cleanup_old_backups():
    """Remove backups older than retention period."""
    try:
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=BACKUP_RETENTION_DAYS)
        removed_count = 0
        total_size_freed = 0
        
        for backup_file in BACKUP_DIR.glob('rfid_inventory_backup_*.sql*'):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                file_size = backup_file.stat().st_size
                backup_file.unlink()
                removed_count += 1
                total_size_freed += file_size
                logger.info(f"Removed old backup: {backup_file.name}")
        
        if removed_count > 0:
            size_freed_mb = total_size_freed / (1024 * 1024)
            logger.info(f"Cleanup complete: {removed_count} old backups removed, {size_freed_mb:.2f} MB freed")
        else:
            logger.info("No old backups to clean up")
            
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}", exc_info=True)

def create_backup_manifest(backup_path):
    """Create a manifest file with backup metadata."""
    try:
        manifest_data = {
            'backup_date': datetime.datetime.now().isoformat(),
            'database_name': DB_CONFIG["database"],
            'backup_file': str(backup_path.name) if backup_path else None,
            'backup_size_bytes': backup_path.stat().st_size if backup_path and backup_path.exists() else 0,
            'database_size_gb': get_database_size(),
            'backup_type': 'nightly_full',
            'retention_days': BACKUP_RETENTION_DAYS,
            'status': 'success' if backup_path and backup_path.exists() else 'failed'
        }
        
        manifest_path = BACKUP_DIR / f"backup_manifest_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
            
        logger.info(f"Backup manifest created: {manifest_path}")
        return manifest_data
        
    except Exception as e:
        logger.error(f"Failed to create backup manifest: {str(e)}")
        return None

def verify_backup(backup_path):
    """Perform basic verification of backup file."""
    try:
        if not backup_path or not backup_path.exists():
            logger.error("Backup file does not exist")
            return False
            
        file_size = backup_path.stat().st_size
        if file_size < 1024:  # Less than 1KB is suspicious
            logger.error(f"Backup file too small: {file_size} bytes")
            return False
            
        # Test that the compressed file can be read
        if backup_path.suffix == '.gz':
            test_cmd = ['gunzip', '-t', str(backup_path)]
            result = subprocess.run(test_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Backup file corruption detected: {result.stderr}")
                return False
                
        logger.info(f"Backup verification passed: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"Backup verification failed: {str(e)}")
        return False

def main():
    """Main backup execution function."""
    logger.info("=== Starting Nightly Backup Process ===")
    
    try:
        # Ensure backup directory exists
        if not ensure_backup_directory():
            sys.exit(1)
            
        # Perform the backup
        backup_path = perform_backup()
        
        if backup_path and verify_backup(backup_path):
            # Create manifest
            manifest = create_backup_manifest(backup_path)
            
            # Cleanup old backups
            cleanup_old_backups()
            
            logger.info("=== Backup Process Completed Successfully ===")
            
            # Output summary for cron logs
            if manifest:
                print(f"Backup Success: {backup_path.name} ({manifest['backup_size_bytes']/1024/1024:.2f} MB)")
            
            sys.exit(0)
        else:
            logger.error("=== Backup Process Failed ===")
            print("Backup Failed: Check logs for details")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Critical backup error: {str(e)}", exc_info=True)
        print(f"Backup Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()