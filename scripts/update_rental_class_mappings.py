import sys
import os

# Add the project directory to the Python path
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.db_models import RentalClassMapping
from config import DB_CONFIG
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
try:
    db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
except Exception as e:
    logger.error(f"Failed to connect to the database: {str(e)}")
    sys.exit(1)

# Data to upsert (using rental_class_id values from seed data)
data = [
    {"rental_class_id": "61885", "category": "Round Linen", "subcategory": "108 in"},
    {"rental_class_id": "61914", "category": "Round Linen", "subcategory": "108 in"},
    {"rental_class_id": "61890", "category": "Round Linen", "subcategory": "108 in"},
    {"rental_class_id": "61886", "category": "Round Linen", "subcategory": "108 in"},
    {"rental_class_id": "61908", "category": "Round Linen", "subcategory": "108 in"},
]

try:
    for entry in data:
        rental_class_id = entry['rental_class_id']
        category = entry['category']
        subcategory = entry['subcategory']

        # Check if the record exists
        existing_mapping = session.query(RentalClassMapping).filter_by(rental_class_id=rental_class_id).first()

        if existing_mapping:
            # Update existing record
            existing_mapping.category = category
            existing_mapping.subcategory = subcategory
            logger.info(f"Updated rental_class_id {rental_class_id} with category '{category}' and subcategory '{subcategory}'")
        else:
            # Insert new record
            new_mapping = RentalClassMapping(
                rental_class_id=rental_class_id,
                category=category,
                subcategory=subcategory
            )
            session.add(new_mapping)
            logger.info(f"Inserted rental_class_id {rental_class_id} with category '{category}' and subcategory '{subcategory}'")

    # Commit the transaction
    session.commit()
    logger.info("Successfully updated rental class mappings")

except Exception as e:
    logger.error(f"Error updating rental class mappings: {str(e)}")
    session.rollback()
    raise
finally:
    session.close()
    logger.info("Database session closed")