"""
Store Correlation Service
Manages correlation between RFID Pro API store codes and POS CSV store numbers
CRITICAL: Correlation fields are NEVER sent to RFID Pro API
"""

from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from .. import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class StoreCorrelationService:
    """
    Handles bidirectional store code correlation between RFID and POS systems.
    
    Store Mapping:
    - RFID 3607 ↔ POS 1 (Wayzata)
    - RFID 6800 ↔ POS 2 (Brooklyn Park)  
    - RFID 728  ↔ POS 3 (Elk River)
    - RFID 8101 ↔ POS 4 (Fridley)
    - RFID 000  ↔ POS 0 (Legacy/Unassigned)
    """
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or db.session
        self._correlation_cache = None
        self._cache_timestamp = None
        self.cache_ttl = 300  # 5 minutes
    
    def _get_correlations(self) -> Dict[str, Dict[str, str]]:
        """Get store correlations with caching."""
        now = datetime.now()
        
        if (self._correlation_cache is None or 
            self._cache_timestamp is None or
            (now - self._cache_timestamp).seconds > self.cache_ttl):
            
            result = self.session.execute(text("""
                SELECT rfid_store_code, pos_store_code, store_name, store_location
                FROM store_correlations 
                WHERE is_active = 1
            """))
            
            self._correlation_cache = {
                'rfid_to_pos': {},
                'pos_to_rfid': {},
                'rfid_info': {},
                'pos_info': {}
            }
            
            for row in result.fetchall():
                rfid_code, pos_code, name, location = row
                
                # Bidirectional mapping
                self._correlation_cache['rfid_to_pos'][rfid_code] = pos_code
                self._correlation_cache['pos_to_rfid'][pos_code] = rfid_code
                
                # Store info
                store_info = {'name': name, 'location': location}
                self._correlation_cache['rfid_info'][rfid_code] = store_info
                self._correlation_cache['pos_info'][pos_code] = store_info
            
            self._cache_timestamp = now
            logger.debug(f"Store correlation cache refreshed: {len(self._correlation_cache['rfid_to_pos'])} mappings")
        
        return self._correlation_cache
    
    def correlate_rfid_to_pos(self, rfid_store_code: str) -> Optional[str]:
        """
        Convert RFID store code to POS store number.
        
        Args:
            rfid_store_code: RFID Pro API store code (e.g., '3607', '6800')
            
        Returns:
            POS store number (e.g., '1', '2') or None if not found
        """
        correlations = self._get_correlations()
        pos_code = correlations['rfid_to_pos'].get(rfid_store_code)
        
        if pos_code:
            logger.debug(f"RFID store {rfid_store_code} → POS store {pos_code}")
        else:
            logger.warning(f"No POS correlation found for RFID store: {rfid_store_code}")
            
        return pos_code
    
    def correlate_pos_to_rfid(self, pos_store_code: str) -> Optional[str]:
        """
        Convert POS store number to RFID store code.
        
        Args:
            pos_store_code: POS system store number (e.g., '1', '2')
            
        Returns:
            RFID store code (e.g., '3607', '6800') or None if not found
        """
        correlations = self._get_correlations()
        rfid_code = correlations['pos_to_rfid'].get(pos_store_code)
        
        if rfid_code:
            logger.debug(f"POS store {pos_store_code} → RFID store {rfid_code}")
        else:
            logger.warning(f"No RFID correlation found for POS store: {pos_store_code}")
            
        return rfid_code
    
    def get_store_info(self, store_code: str, system: str = 'auto') -> Optional[Dict[str, str]]:
        """
        Get store information (name, location) for a store code.
        
        Args:
            store_code: Store code to look up
            system: 'rfid', 'pos', or 'auto' to detect
            
        Returns:
            Dict with 'name', 'location', 'rfid_code', 'pos_code' or None
        """
        correlations = self._get_correlations()
        
        if system == 'auto':
            # Auto-detect system based on code format
            system = 'pos' if store_code in ['0', '1', '2', '3', '4'] else 'rfid'
        
        if system == 'rfid' and store_code in correlations['rfid_info']:
            info = correlations['rfid_info'][store_code].copy()
            info['rfid_code'] = store_code
            info['pos_code'] = correlations['rfid_to_pos'].get(store_code)
            return info
        elif system == 'pos' and store_code in correlations['pos_info']:
            info = correlations['pos_info'][store_code].copy()
            info['pos_code'] = store_code
            info['rfid_code'] = correlations['pos_to_rfid'].get(store_code)
            return info
        
        logger.warning(f"No store info found for {system} store: {store_code}")
        return None
    
    def get_all_mappings(self) -> List[Dict[str, str]]:
        """
        Get all store mappings for display/admin purposes.
        
        Returns:
            List of dicts with rfid_code, pos_code, name, location
        """
        result = self.session.execute(text("""
            SELECT rfid_store_code, pos_store_code, store_name, store_location, is_active
            FROM store_correlations 
            ORDER BY pos_store_code
        """))
        
        mappings = []
        for row in result.fetchall():
            mappings.append({
                'rfid_code': row[0],
                'pos_code': row[1], 
                'name': row[2],
                'location': row[3],
                'is_active': bool(row[4])
            })
        
        return mappings
    
    def get_correlation_health(self) -> Dict[str, Any]:
        """
        Get correlation system health status.
        
        Returns:
            Dict with correlation statistics and health metrics
        """
        try:
            # Check table correlations
            result = self.session.execute(text("""
                SELECT 'pos_transactions' as table_name,
                       COUNT(*) as total_records,
                       COUNT(rfid_store_code) as correlated_records,
                       ROUND(COUNT(rfid_store_code) / COUNT(*) * 100, 2) as correlation_percentage
                FROM pos_transactions
                UNION ALL
                SELECT 'pos_equipment' as table_name,
                       COUNT(*) as total_records,
                       COUNT(pos_store_code) as correlated_records, 
                       ROUND(COUNT(pos_store_code) / COUNT(*) * 100, 2) as correlation_percentage
                FROM pos_equipment
            """))
            
            table_health = []
            for row in result.fetchall():
                table_health.append({
                    'table': row[0],
                    'total_records': row[1],
                    'correlated_records': row[2],
                    'correlation_percentage': float(row[3])
                })
            
            # Check mapping completeness
            mappings = self.get_all_mappings()
            active_mappings = len([m for m in mappings if m['is_active']])
            
            health = {
                'status': 'healthy' if active_mappings >= 4 else 'warning',
                'active_mappings': active_mappings,
                'total_mappings': len(mappings),
                'table_correlations': table_health,
                'cache_status': 'active' if self._correlation_cache else 'empty',
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"Store correlation health check: {health['status']} - {active_mappings} active mappings")
            return health
            
        except Exception as e:
            logger.error(f"Store correlation health check failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }
    
    def update_correlation(self, contract_no: str = None, store_no: str = None, 
                          table_name: str = 'pos_transactions') -> bool:
        """
        Update correlation for a specific record.
        CRITICAL: Only updates correlation fields, never API fields.
        
        Args:
            contract_no: Contract number (for transactions)
            store_no: POS store number to correlate
            table_name: Target table name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not store_no:
                logger.warning("Cannot update correlation: no store_no provided")
                return False
            
            rfid_code = self.correlate_pos_to_rfid(store_no)
            if not rfid_code:
                logger.warning(f"Cannot correlate POS store {store_no} to RFID code")
                return False
            
            if table_name == 'pos_transactions' and contract_no:
                self.session.execute(text("""
                    UPDATE pos_transactions 
                    SET rfid_store_code = :rfid_code
                    WHERE contract_no = :contract_no
                """), {'rfid_code': rfid_code, 'contract_no': contract_no})
                
            elif table_name == 'pos_equipment' and contract_no:
                # For equipment, correlate from RFID current_store to POS code
                rfid_store = self.correlate_pos_to_rfid(store_no)  
                self.session.execute(text("""
                    UPDATE pos_equipment
                    SET pos_store_code = :pos_code
                    WHERE current_store = :current_store
                """), {'pos_code': store_no, 'current_store': rfid_store})
            
            self.session.commit()
            logger.info(f"Updated correlation for {table_name}: store_no={store_no} → rfid_code={rfid_code}")
            
            # Clear cache to force refresh
            self._correlation_cache = None
            return True
            
        except Exception as e:
            logger.error(f"Failed to update correlation: {e}")
            self.session.rollback()
            return False
    
    def validate_api_compatibility(self) -> Dict[str, Any]:
        """
        Validate that correlation system doesn't interfere with RFID Pro API.
        CRITICAL: Ensures API fields are never modified by correlation logic.
        
        Returns:
            Dict with validation results
        """
        try:
            validation = {
                'api_fields_protected': True,
                'correlation_fields_separate': True,
                'issues': [],
                'warnings': []
            }
            
            # Check that RFID Pro API fields are not modified by correlation logic
            api_protected_fields = [
                ('id_item_master', 'current_store'),
                ('id_item_master', 'home_store'), 
                ('id_transactions', 'store'),  # If exists
            ]
            
            for table, field in api_protected_fields:
                try:
                    # Verify the field exists and is not corrupted by correlation logic
                    result = self.session.execute(text(f"""
                        SELECT COUNT(*) FROM {table} 
                        WHERE {field} IS NOT NULL 
                        AND {field} NOT IN ('000', '3607', '6800', '728', '8101')
                    """))
                    
                    unexpected_values = result.scalar()
                    if unexpected_values > 0:
                        validation['issues'].append(
                            f"API field {table}.{field} has {unexpected_values} unexpected values"
                        )
                        validation['api_fields_protected'] = False
                        
                except Exception as e:
                    validation['warnings'].append(f"Could not validate {table}.{field}: {str(e)}")
            
            # Check correlation fields are properly separated
            correlation_fields = [
                ('pos_transactions', 'rfid_store_code'),
                ('pos_equipment', 'pos_store_code')
            ]
            
            for table, field in correlation_fields:
                try:
                    result = self.session.execute(text(f"SELECT COUNT(*) FROM {table} WHERE {field} IS NOT NULL"))
                    correlated_count = result.scalar()
                    
                    if correlated_count == 0:
                        validation['warnings'].append(f"No correlations found in {table}.{field}")
                    else:
                        logger.debug(f"Validated {correlated_count} correlations in {table}.{field}")
                        
                except Exception as e:
                    validation['issues'].append(f"Correlation field {table}.{field} not accessible: {str(e)}")
                    validation['correlation_fields_separate'] = False
            
            validation['status'] = 'pass' if not validation['issues'] else 'fail'
            validation['last_validated'] = datetime.now().isoformat()
            
            logger.info(f"API compatibility validation: {validation['status']}")
            return validation
            
        except Exception as e:
            logger.error(f"API compatibility validation failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'last_validated': datetime.now().isoformat()
            }


# Singleton instance for application use
_store_correlation_service = None

def get_store_correlation_service() -> StoreCorrelationService:
    """Get singleton store correlation service instance."""
    global _store_correlation_service
    if _store_correlation_service is None:
        _store_correlation_service = StoreCorrelationService()
    return _store_correlation_service