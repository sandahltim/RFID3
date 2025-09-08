# app/services/pos_correlation_service.py
# POS-RFID Correlation Service
# Created: 2025-08-28

import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from difflib import SequenceMatcher
from sqlalchemy import and_, or_, func, text
from app import db
from app.models.db_models import ItemMaster, Transaction, ContractSnapshot
from app.models.pos_models import (
    POSTransaction, POSTransactionItem, POSRFIDCorrelation,
    POSInventoryDiscrepancy, POSAnalytics
)
from app.services.logger import get_logger

logger = get_logger(__name__)


class POSCorrelationService:
    """Service for correlating POS data with RFID inventory."""
    
    def __init__(self):
        self.correlation_cache = {}
        self.confidence_threshold = 0.7  # Minimum confidence for auto-correlation
        
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        # Remove special characters and extra spaces
        normalized = re.sub(r'[^\w\s]', ' ', text.upper())
        normalized = ' '.join(normalized.split())
        return normalized
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity score between two texts."""
        if not text1 or not text2:
            return 0.0
        
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def extract_item_features(self, text: str) -> Dict:
        """Extract features from item description."""
        features = {
            'size': None,
            'color': None,
            'material': None,
            'type': None,
            'numbers': []
        }
        
        if not text:
            return features
        
        normalized = text.upper()
        
        # Extract size patterns
        size_patterns = [
            r'\b(\d+X\d+)\b',  # 90X156
            r'\b(\d+\s*ROUND)\b',  # 120 ROUND
            r'\b(\d+\s*SQ)\b',  # 60 SQ
        ]
        for pattern in size_patterns:
            match = re.search(pattern, normalized)
            if match:
                features['size'] = match.group(1)
                break
        
        # Extract colors
        colors = ['WHITE', 'BLACK', 'BLUE', 'RED', 'GREEN', 'YELLOW', 'GOLD', 
                 'SILVER', 'NAVY', 'OCEAN', 'PEACH', 'CHOCOLATE', 'DAMASK']
        for color in colors:
            if color in normalized:
                features['color'] = color
                break
        
        # Extract material
        materials = ['LINEN', 'COTTON', 'POLYESTER', 'PLASTIC', 'WOOD', 'METAL']
        for material in materials:
            if material in normalized:
                features['material'] = material
                break
        
        # Extract type
        types = ['TABLE', 'CHAIR', 'TENT', 'LINEN', 'NAPKIN', 'COVER']
        for item_type in types:
            if item_type in normalized:
                features['type'] = item_type
                break
        
        # Extract numbers
        features['numbers'] = re.findall(r'\b\d+\b', normalized)
        
        return features
    
    def find_rfid_matches(self, pos_item: POSTransactionItem) -> List[Tuple[str, float, str]]:
        """Find potential RFID matches for a POS item.
        
        Returns list of tuples: (rental_class_num, confidence, match_type)
        """
        matches = []
        
        # First try exact item number match
        if pos_item.item_num:
            # Check if item_num matches rental_class_num
            rfid_items = ItemMaster.query.filter_by(
                rental_class_num=pos_item.item_num
            ).limit(10).all()
            
            if rfid_items:
                for item in rfid_items:
                    matches.append((item.rental_class_num, 1.0, 'exact'))
                return matches[:1]  # Return best exact match
        
        # Try fuzzy matching on description
        if pos_item.desc:
            pos_features = self.extract_item_features(pos_item.desc)
            
            # Build query based on features
            query = ItemMaster.query
            
            # Filter by features
            if pos_features['size']:
                query = query.filter(ItemMaster.common_name.contains(pos_features['size']))
            if pos_features['color']:
                query = query.filter(ItemMaster.common_name.contains(pos_features['color']))
            if pos_features['material']:
                query = query.filter(ItemMaster.common_name.contains(pos_features['material']))
            
            # Get potential matches
            potential_matches = query.limit(50).all()
            
            for rfid_item in potential_matches:
                similarity = self.calculate_similarity(pos_item.desc, rfid_item.common_name)
                if similarity >= self.confidence_threshold:
                    matches.append((rfid_item.rental_class_num, similarity, 'fuzzy'))
            
            # Sort by confidence
            matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches[:5]  # Return top 5 matches
    
    def correlate_transaction_items(self, contract_no: str) -> Dict:
        """Correlate all items in a POS transaction with RFID inventory."""
        results = {
            'contract_no': contract_no,
            'total_items': 0,
            'correlated': 0,
            'uncorrelated': 0,
            'correlations': [],
            'discrepancies': []
        }
        
        # Get POS transaction items
        pos_items = POSTransactionItem.query.filter_by(contract_no=contract_no).all()
        results['total_items'] = len(pos_items)
        
        for pos_item in pos_items:
            # Check if already correlated
            existing = POSRFIDCorrelation.query.filter_by(
                pos_item_num=pos_item.item_num,
                is_active=True
            ).first()
            
            if existing:
                results['correlated'] += 1
                results['correlations'].append({
                    'pos_item': pos_item.item_num,
                    'rfid_class': existing.rfid_rental_class_num,
                    'confidence': float(existing.confidence_score),
                    'type': existing.correlation_type
                })
                continue
            
            # Find matches
            matches = self.find_rfid_matches(pos_item)
            
            if matches:
                best_match = matches[0]
                rental_class_num, confidence, match_type = best_match
                
                # Get RFID item details
                rfid_item = ItemMaster.query.filter_by(
                    rental_class_num=rental_class_num
                ).first()
                
                # Create correlation
                correlation = POSRFIDCorrelation(
                    pos_item_num=pos_item.item_num or f"UNKNOWN_{pos_item.id}",
                    pos_item_desc=pos_item.desc,
                    rfid_rental_class_num=rental_class_num,
                    rfid_common_name=rfid_item.common_name if rfid_item else None,
                    correlation_type=match_type,
                    confidence_score=Decimal(str(confidence)),
                    match_criteria={'method': match_type, 'score': confidence},
                    created_by='system'
                )
                db.session.add(correlation)
                
                results['correlated'] += 1
                results['correlations'].append({
                    'pos_item': pos_item.item_num,
                    'rfid_class': rental_class_num,
                    'confidence': confidence,
                    'type': match_type
                })
            else:
                results['uncorrelated'] += 1
                
                # Create discrepancy for uncorrelated item
                discrepancy = POSInventoryDiscrepancy(
                    contract_no=contract_no,
                    pos_item_num=pos_item.item_num,
                    discrepancy_type='missing_from_rfid',
                    pos_quantity=pos_item.qty,
                    severity='medium' if pos_item.qty > 5 else 'low',
                    description=f"POS item '{pos_item.desc}' not found in RFID system",
                    detected_by='system'
                )
                db.session.add(discrepancy)
                results['discrepancies'].append({
                    'item': pos_item.item_num,
                    'desc': pos_item.desc,
                    'qty': pos_item.qty
                })
        
        db.session.commit()
        return results
    
    def detect_discrepancies(self, contract_no: str) -> List[Dict]:
        """Detect discrepancies between POS and RFID for a contract."""
        discrepancies = []
        
        # Get POS transaction
        pos_trans = POSTransaction.query.filter_by(contract_no=contract_no).first()
        if not pos_trans:
            return discrepancies
        
        # Get POS items with correlations
        pos_items = db.session.query(
            POSTransactionItem,
            POSRFIDCorrelation
        ).outerjoin(
            POSRFIDCorrelation,
            and_(
                POSTransactionItem.item_num == POSRFIDCorrelation.pos_item_num,
                POSRFIDCorrelation.is_active == True
            )
        ).filter(
            POSTransactionItem.contract_no == contract_no
        ).all()
        
        for pos_item, correlation in pos_items:
            if not correlation:
                # Already handled in correlate_transaction_items
                continue
            
            # Check RFID status for correlated items
            if correlation.rfid_rental_class_num:
                # Get RFID items with this rental class on this contract
                rfid_items = ItemMaster.query.filter(
                    and_(
                        ItemMaster.rental_class_num == correlation.rfid_rental_class_num,
                        ItemMaster.last_contract_num == contract_no
                    )
                ).all()
                
                rfid_count = len(rfid_items)
                pos_count = pos_item.qty or 0
                
                if rfid_count != pos_count:
                    # Quantity mismatch
                    discrepancy = POSInventoryDiscrepancy(
                        contract_no=contract_no,
                        pos_item_num=pos_item.item_num,
                        rfid_rental_class_num=correlation.rfid_rental_class_num,
                        discrepancy_type='quantity_mismatch',
                        pos_quantity=pos_count,
                        rfid_quantity=rfid_count,
                        severity='high' if abs(rfid_count - pos_count) > 10 else 'medium',
                        description=f"POS shows {pos_count} items, RFID shows {rfid_count}",
                        detected_by='system'
                    )
                    db.session.add(discrepancy)
                    discrepancies.append({
                        'type': 'quantity_mismatch',
                        'item': pos_item.item_num,
                        'pos_qty': pos_count,
                        'rfid_qty': rfid_count
                    })
                
                # Check status consistency
                for rfid_item in rfid_items:
                    if pos_item.line_status == 'RR' and rfid_item.status != 'Ready to Rent':
                        # Return status mismatch
                        discrepancy = POSInventoryDiscrepancy(
                            contract_no=contract_no,
                            pos_item_num=pos_item.item_num,
                            rfid_tag_id=rfid_item.tag_id,
                            discrepancy_type='status_mismatch',
                            pos_status='Returned',
                            rfid_status=rfid_item.status,
                            severity='medium',
                            description=f"POS shows returned but RFID status is {rfid_item.status}",
                            detected_by='system'
                        )
                        db.session.add(discrepancy)
                        discrepancies.append({
                            'type': 'status_mismatch',
                            'tag_id': rfid_item.tag_id,
                            'pos_status': 'Returned',
                            'rfid_status': rfid_item.status
                        })
        
        db.session.commit()
        return discrepancies
    
    def analyze_correlation_quality(self) -> Dict:
        """Analyze overall correlation quality and statistics."""
        stats = {
            'total_pos_items': 0,
            'total_correlations': 0,
            'correlation_types': {},
            'confidence_distribution': {
                'high': 0,      # >= 0.9
                'medium': 0,    # >= 0.7
                'low': 0        # < 0.7
            },
            'uncorrelated_items': 0,
            'discrepancies': {
                'total': 0,
                'by_type': {},
                'by_severity': {}
            }
        }
        
        # Count total POS items
        stats['total_pos_items'] = db.session.query(
            func.count(func.distinct(POSTransactionItem.item_num))
        ).scalar() or 0
        
        # Get correlation statistics
        correlations = POSRFIDCorrelation.query.filter_by(is_active=True).all()
        stats['total_correlations'] = len(correlations)
        
        for corr in correlations:
            # Count by type
            corr_type = corr.correlation_type
            stats['correlation_types'][corr_type] = stats['correlation_types'].get(corr_type, 0) + 1
            
            # Count by confidence
            conf = float(corr.confidence_score) if corr.confidence_score else 0
            if conf >= 0.9:
                stats['confidence_distribution']['high'] += 1
            elif conf >= 0.7:
                stats['confidence_distribution']['medium'] += 1
            else:
                stats['confidence_distribution']['low'] += 1
        
        # Count uncorrelated items
        stats['uncorrelated_items'] = stats['total_pos_items'] - stats['total_correlations']
        
        # Get discrepancy statistics
        discrepancies = POSInventoryDiscrepancy.query.filter_by(status='open').all()
        stats['discrepancies']['total'] = len(discrepancies)
        
        for disc in discrepancies:
            # Count by type
            disc_type = disc.discrepancy_type
            stats['discrepancies']['by_type'][disc_type] = \
                stats['discrepancies']['by_type'].get(disc_type, 0) + 1
            
            # Count by severity
            severity = disc.severity
            stats['discrepancies']['by_severity'][severity] = \
                stats['discrepancies']['by_severity'].get(severity, 0) + 1
        
        return stats
    
    def correlate_all_transactions(self, limit: int = 100) -> Dict:
        """Correlate multiple transactions in batch."""
        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'total_correlations': 0,
            'total_discrepancies': 0
        }
        
        # Get uncorrelated transactions
        uncorrelated = db.session.query(POSTransaction.contract_no).outerjoin(
            POSRFIDCorrelation,
            POSTransaction.contract_no == POSTransactionItem.contract_no
        ).filter(
            POSRFIDCorrelation.id == None
        ).limit(limit).all()
        
        for (contract_no,) in uncorrelated:
            try:
                # Correlate items
                corr_result = self.correlate_transaction_items(contract_no)
                results['processed'] += 1
                results['successful'] += 1
                results['total_correlations'] += corr_result['correlated']
                
                # Detect discrepancies
                discrepancies = self.detect_discrepancies(contract_no)
                results['total_discrepancies'] += len(discrepancies)
                
                logger.info(f"Correlated contract {contract_no}: "
                          f"{corr_result['correlated']}/{corr_result['total_items']} items")
                
            except Exception as e:
                results['failed'] += 1
                logger.error(f"Failed to correlate contract {contract_no}: {str(e)}")
                db.session.rollback()
        
        return results
    
    def calculate_inventory_turnover(self, rental_class_num: str, days: int = 30) -> Dict:
        """Calculate inventory turnover metrics for a rental class."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get POS transaction count for this item
        pos_count = db.session.query(func.count(POSTransactionItem.id)).join(
            POSRFIDCorrelation,
            POSTransactionItem.item_num == POSRFIDCorrelation.pos_item_num
        ).filter(
            and_(
                POSRFIDCorrelation.rfid_rental_class_num == rental_class_num,
                POSTransactionItem.due_date >= start_date,
                POSTransactionItem.due_date <= end_date
            )
        ).scalar() or 0
        
        # Get total inventory count
        inventory_count = ItemMaster.query.filter_by(
            rental_class_num=rental_class_num
        ).count()
        
        # Calculate turnover rate
        turnover_rate = (pos_count / inventory_count * 365 / days) if inventory_count > 0 else 0
        
        # Get revenue data
        revenue = db.session.query(func.sum(POSTransactionItem.price)).join(
            POSRFIDCorrelation,
            POSTransactionItem.item_num == POSRFIDCorrelation.pos_item_num
        ).filter(
            and_(
                POSRFIDCorrelation.rfid_rental_class_num == rental_class_num,
                POSTransactionItem.due_date >= start_date,
                POSTransactionItem.due_date <= end_date
            )
        ).scalar() or 0
        
        return {
            'rental_class_num': rental_class_num,
            'period_days': days,
            'transaction_count': pos_count,
            'inventory_count': inventory_count,
            'turnover_rate': round(turnover_rate, 2),
            'total_revenue': float(revenue),
            'revenue_per_item': float(revenue / inventory_count) if inventory_count > 0 else 0
        }


# Initialize service instance
pos_correlation_service = POSCorrelationService()
