# scripts/bulk_update_mappings.py
# bulk_update_mappings.py version: 2025-06-20-v2
import sys
import os
import csv
from datetime import datetime, timezone

# Add the project directory to the Python path
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.models.db_models import UserRentalClassMapping
from config import DB_CONFIG, SQLALCHEMY_ENGINE_OPTIONS
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File handler for script-specific log
log_dir = os.path.join(project_dir, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
file_handler = logging.FileHandler(os.path.join(log_dir, 'bulk_update_mappings.log'))
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Database connection
try:
    db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}&collation={DB_CONFIG['collation']}"
    engine = create_engine(db_url, **SQLALCHEMY_ENGINE_OPTIONS)
    Session = sessionmaker(bind=engine)
    session = Session()
    logger.info("Successfully connected to the database")
except Exception as e:
    logger.error(f"Failed to connect to the database: {str(e)}")
    sys.exit(1)

# Path to the CSV file
csv_file_path = os.path.join(project_dir, 'seeddata_20250425155406.csv')

def bulk_update_mappings():
    try:
        # Verify the CSV file exists
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV file not found at: {csv_file_path}")
            raise FileNotFoundError(f"CSV file not found at: {csv_file_path}")

        # Read the CSV file and deduplicate mappings
        mappings_dict = {}
        row_count = 0
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            logger.info("Starting to read CSV file")
            
            # Verify expected columns
            expected_columns = {'rental_class_id', 'Cat', 'SubCat'}
            if not expected_columns.issubset(reader.fieldnames):
                logger.error(f"CSV file missing required columns. Expected: {expected_columns}, Found: {reader.fieldnames}")
                raise ValueError(f"CSV file missing required columns: {expected_columns}")

            for row in reader:
                row_count += 1
                try:
                    rental_class_id = row.get('rental_class_id', '').strip()
                    category = row.get('Cat', '').strip()
                    subcategory = row.get('SubCat', '').strip()

                    # Skip rows with missing rental_class_id, category, or subcategory
                    if not rental_class_id or not category or not subcategory:
                        logger.debug(f"Skipping row {row_count} with missing data: rental_class_id={rental_class_id}, category={category}, subcategory={subcategory}")
                        continue

                    # Deduplicate: Keep the first occurrence of rental_class_id
                    if rental_class_id in mappings_dict:
                        logger.warning(f"Duplicate rental_class_id found at row {row_count}: {rental_class_id}. Keeping the first occurrence.")
                        continue

                    mappings_dict[rental_class_id] = {
                        'rental_class_id': rental_class_id,
                        'category': category,
                        'subcategory': subcategory
                    }
                    logger.debug(f"Processed valid row {row_count}: {mappings_dict[rental_class_id]}")
                except Exception as row_error:
                    logger.error(f"Error processing row {row_count}: {str(row_error)}", exc_info=True)
                    continue

        mappings = list(mappings_dict.values())
        logger.info(f"Processed {row_count} total rows from CSV, {len(mappings)} unique mappings found")

        # PRESERVE existing user mappings - only update new ones or merge
        logger.info("Preserving existing user mappings, only updating/inserting new ones")
        
        # Get existing user mappings to preserve
        existing_mappings = {m.rental_class_id: m for m in session.query(UserRentalClassMapping).all()}
        logger.info(f"Found {len(existing_mappings)} existing user mappings to preserve")

        # Insert/update user mappings one at a time, preserving existing ones
        inserted_count = 0
        updated_count = 0
        skipped_count = 0
        for mapping in mappings:
            try:
                rental_class_id = mapping['rental_class_id']
                
                # Check if user mapping already exists (preserve it)
                if rental_class_id in existing_mappings:
                    logger.debug(f"Preserving existing user mapping for rental_class_id {rental_class_id}")
                    skipped_count += 1
                    continue
                
                # Insert new mapping only if it doesn't exist
                user_mapping = UserRentalClassMapping(
                    rental_class_id=mapping['rental_class_id'],
                    category=mapping['category'],
                    subcategory=mapping['subcategory'],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                session.add(user_mapping)
                session.commit()  # Commit each insert individually
                inserted_count += 1
                logger.debug(f"Inserted new mapping: {mapping}")
                
            except IntegrityError as integrity_error:
                logger.error(f"Integrity error for mapping {mapping}: {str(integrity_error)}")
                session.rollback()
                continue
            except Exception as insert_error:
                logger.error(f"Error inserting mapping {mapping}: {str(insert_error)}", exc_info=True)
                session.rollback()
                continue

        logger.info(f"Successfully processed {len(mappings)} mappings: {inserted_count} inserted, {skipped_count} preserved existing")

    except Exception as e:
        logger.error(f"Error during bulk update: {str(e)}", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()
        logger.info("Database session closed")

if __name__ == "__main__":
    logger.info("Starting bulk update of rental class mappings")
    try:
        bulk_update_mappings()
        logger.info("Bulk update completed successfully")
    except Exception as main_error:
        logger.error(f"Script failed: {str(main_error)}", exc_info=True)
        sys.exit(1)