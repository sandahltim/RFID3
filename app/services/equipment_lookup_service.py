# Equipment Lookup Service - Replaces seed_rental_classes with POS equipment
# Version: 2025-09-17-v1

from sqlalchemy import text
from app import db
from app.services.logger import get_logger

logger = get_logger(__name__)

class EquipmentLookupService:
    """
    Replaces seed_rental_classes lookups with POS equipment data via correlation
    Used when assigning RFID/QR tags to get item names and classifications
    """

    @staticmethod
    def get_equipment_by_rental_class(rental_class_num: str):
        """
        Get equipment info by rental_class_num using POS correlation
        Replaces: SELECT * FROM seed_rental_classes WHERE rental_class_id = rental_class_num
        """
        try:
            session = db.session()

            # NEW: Use correlation to get POS equipment data
            query = text("""
                SELECT
                    c.rfid_rental_class_num as rental_class_num,
                    c.pos_equipment_name as common_name,
                    e.category,
                    e.department,
                    e.current_store as bin_location,
                    e.manf as manufacturer,
                    e.model_no,
                    e.type_desc,
                    c.confidence_score
                FROM equipment_rfid_correlations c
                LEFT JOIN pos_equipment e ON c.pos_item_num = e.item_num
                WHERE c.rfid_rental_class_num = :rental_class_num
                ORDER BY c.confidence_score DESC
                LIMIT 1
            """)

            result = session.execute(query, {"rental_class_num": rental_class_num}).fetchone()

            if result:
                return {
                    "rental_class_id": result.rental_class_num,
                    "common_name": result.common_name,
                    "bin_location": result.bin_location,
                    # Enhanced data from POS equipment (not available in old seed table)
                    "category": result.category,
                    "department": result.department,
                    "manufacturer": result.manufacturer,
                    "model_no": result.model_no,
                    "type_desc": result.type_desc,
                    "source": "pos_equipment_correlation",
                    "confidence": float(result.confidence_score) if result.confidence_score else 100.0
                }
            else:
                # Fallback: Try to find in seed_rental_classes (during transition)
                logger.warning(f"No POS correlation found for rental_class_num {rental_class_num}, checking seed fallback")

                fallback_query = text("""
                    SELECT rental_class_id, common_name, bin_location
                    FROM seed_rental_classes
                    WHERE rental_class_id = :rental_class_num
                """)

                fallback_result = session.execute(fallback_query, {"rental_class_num": rental_class_num}).fetchone()

                if fallback_result:
                    return {
                        "rental_class_id": fallback_result.rental_class_id,
                        "common_name": fallback_result.common_name,
                        "bin_location": fallback_result.bin_location,
                        "source": "seed_rental_classes_fallback",
                        "needs_correlation": True
                    }
                else:
                    return None

        except Exception as e:
            logger.error(f"Error looking up equipment for rental_class {rental_class_num}: {e}")
            return None

    @staticmethod
    def get_all_equipment_classes():
        """
        Get all available equipment classes for selection
        Replaces: SELECT * FROM seed_rental_classes
        """
        try:
            session = db.session()

            # NEW: Get from POS equipment via correlation
            query = text("""
                SELECT DISTINCT
                    c.rfid_rental_class_num as rental_class_id,
                    c.pos_equipment_name as common_name,
                    e.category,
                    e.department,
                    c.rfid_tag_count,
                    c.confidence_score
                FROM equipment_rfid_correlations c
                LEFT JOIN pos_equipment e ON c.pos_item_num = e.item_num
                WHERE c.pos_equipment_name IS NOT NULL
                ORDER BY c.pos_equipment_name
            """)

            results = session.execute(query).fetchall()

            equipment_list = []
            for result in results:
                equipment_list.append({
                    "rental_class_id": result.rental_class_id,
                    "common_name": result.common_name,
                    "category": result.category,
                    "department": result.department,
                    "tag_count": result.rfid_tag_count,
                    "confidence": float(result.confidence_score) if result.confidence_score else 100.0,
                    "source": "pos_equipment_correlation"
                })

            logger.info(f"Found {len(equipment_list)} equipment classes via POS correlation")
            return equipment_list

        except Exception as e:
            logger.error(f"Error getting equipment classes: {e}")
            return []

    @staticmethod
    def search_equipment_by_name(search_term: str, limit: int = 20):
        """
        Search equipment by name using POS data
        Enhanced search with more data than old seed table
        """
        try:
            session = db.session()

            query = text("""
                SELECT
                    c.rfid_rental_class_num as rental_class_id,
                    c.pos_equipment_name as common_name,
                    e.category,
                    e.department,
                    e.manf as manufacturer,
                    c.confidence_score
                FROM equipment_rfid_correlations c
                LEFT JOIN pos_equipment e ON c.pos_item_num = e.item_num
                WHERE c.pos_equipment_name LIKE :search_term
                OR e.category LIKE :search_term
                OR e.department LIKE :search_term
                ORDER BY c.confidence_score DESC, c.pos_equipment_name
                LIMIT :limit
            """)

            results = session.execute(query, {
                "search_term": f"%{search_term}%",
                "limit": limit
            }).fetchall()

            return [{
                "rental_class_id": result.rental_class_id,
                "common_name": result.common_name,
                "category": result.category,
                "department": result.department,
                "manufacturer": result.manufacturer,
                "confidence": float(result.confidence_score) if result.confidence_score else 100.0,
                "source": "pos_equipment_search"
            } for result in results]

        except Exception as e:
            logger.error(f"Error searching equipment: {e}")
            return []

    @staticmethod
    def get_equipment_correlation_stats():
        """Get statistics about POS equipment correlation coverage"""
        try:
            session = db.session()

            stats_query = text("""
                SELECT
                    COUNT(*) as total_correlations,
                    COUNT(DISTINCT c.rfid_rental_class_num) as unique_rfid_classes,
                    COUNT(DISTINCT c.pos_item_num) as unique_pos_items,
                    AVG(c.confidence_score) as avg_confidence,
                    SUM(CASE WHEN c.pos_equipment_name IS NOT NULL THEN 1 ELSE 0 END) as functional_correlations
                FROM equipment_rfid_correlations c
            """)

            result = session.execute(stats_query).fetchone()

            return {
                "total_correlations": result.total_correlations,
                "unique_rfid_classes": result.unique_rfid_classes,
                "unique_pos_items": result.unique_pos_items,
                "avg_confidence": float(result.avg_confidence) if result.avg_confidence else 0,
                "functional_correlations": result.functional_correlations,
                "coverage_percent": round((result.functional_correlations / result.total_correlations * 100), 2) if result.total_correlations > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error getting correlation stats: {e}")
            return {}