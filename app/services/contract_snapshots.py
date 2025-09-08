# app/services/contract_snapshots.py
# contract_snapshots.py version: 2025-08-24-v1

from datetime import datetime, timezone, timedelta
from ..models.db_models import ContractSnapshot, ItemMaster, Transaction
from .. import db
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


class ContractSnapshotService:
    """Service to manage contract snapshots for historical data preservation."""

    @staticmethod
    def create_contract_snapshot(
        contract_number, snapshot_type="manual", created_by="system"
    ):
        """
        Create a snapshot of all items currently on a contract.

        Args:
            contract_number (str): The contract number to snapshot
            snapshot_type (str): Type of snapshot ('contract_start', 'contract_end', 'status_change', 'periodic', 'manual')
            created_by (str): Who created the snapshot

        Returns:
            int: Number of items snapshotted
        """
        session = None
        try:
            session = db.session()

            # Get all items currently on the contract
            items = (
                session.query(ItemMaster)
                .filter(ItemMaster.last_contract_num == contract_number)
                .all()
            )

            if not items:
                logger.warning(f"No items found for contract {contract_number}")
                return 0

            # Get client name from first transaction
            client_info = (
                session.query(Transaction.client_name)
                .filter(Transaction.contract_number == contract_number)
                .first()
            )

            client_name = client_info.client_name if client_info else None
            snapshot_count = 0

            for item in items:
                # Create snapshot record
                snapshot = ContractSnapshot(
                    contract_number=contract_number,
                    tag_id=item.tag_id,
                    client_name=client_name,
                    common_name=item.common_name,
                    rental_class_num=item.rental_class_num,
                    status=item.status,
                    quality=item.quality,
                    bin_location=item.bin_location,
                    serial_number=item.serial_number,
                    notes=item.notes,
                    snapshot_date=datetime.now(timezone.utc),
                    snapshot_type=snapshot_type,
                    created_by=created_by,
                    latitude=item.latitude,
                    longitude=item.longitude,
                )

                session.add(snapshot)
                snapshot_count += 1

            session.commit()
            logger.info(
                f"Created {snapshot_count} snapshots for contract {contract_number}, type: {snapshot_type}"
            )
            return snapshot_count

        except Exception as e:
            if session:
                session.rollback()
            logger.error(
                f"Error creating contract snapshot for {contract_number}: {str(e)}",
                exc_info=True,
            )
            raise
        finally:
            if session:
                session.close()

    @staticmethod
    def get_contract_snapshot(contract_number, snapshot_date=None):
        """
        Get contract snapshot data for a specific contract and date.

        Args:
            contract_number (str): The contract number
            snapshot_date (datetime, optional): Specific snapshot date. If None, gets latest.

        Returns:
            list: List of ContractSnapshot objects
        """
        session = None
        try:
            session = db.session()

            query = session.query(ContractSnapshot).filter(
                ContractSnapshot.contract_number == contract_number
            )

            if snapshot_date:
                query = query.filter(ContractSnapshot.snapshot_date <= snapshot_date)

            # Get the latest snapshot for each item
            snapshots = query.order_by(ContractSnapshot.snapshot_date.desc()).all()

            # Group by tag_id and take the most recent for each item
            latest_snapshots = {}
            for snapshot in snapshots:
                if snapshot.tag_id not in latest_snapshots:
                    latest_snapshots[snapshot.tag_id] = snapshot

            return list(latest_snapshots.values())

        except Exception as e:
            logger.error(
                f"Error getting contract snapshot for {contract_number}: {str(e)}",
                exc_info=True,
            )
            raise
        finally:
            if session:
                session.close()

    @staticmethod
    def cleanup_old_snapshots(days_to_keep=365):
        """
        Clean up old snapshots to prevent database bloat.

        Args:
            days_to_keep (int): Number of days of snapshots to keep

        Returns:
            int: Number of records deleted
        """
        session = None
        try:
            session = db.session()

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

            deleted_count = (
                session.query(ContractSnapshot)
                .filter(
                    ContractSnapshot.snapshot_date < cutoff_date,
                    ContractSnapshot.snapshot_type.in_(
                        ["periodic", "status_change"]
                    ),  # Keep manual and contract start/end
                )
                .delete()
            )

            session.commit()
            logger.info(
                f"Cleaned up {deleted_count} old contract snapshots older than {days_to_keep} days"
            )
            return deleted_count

        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Error cleaning up old snapshots: {str(e)}", exc_info=True)
            raise
        finally:
            if session:
                session.close()

    @staticmethod
    def get_contract_history_with_snapshots(contract_number):
        """
        Get comprehensive contract history using both current data and snapshots.

        Args:
            contract_number (str): The contract number

        Returns:
            dict: Contract history data
        """
        session = None
        try:
            session = db.session()

            # Get current contract items
            current_items = (
                session.query(ItemMaster)
                .filter(ItemMaster.last_contract_num == contract_number)
                .all()
            )

            # Get historical snapshots
            snapshots = ContractSnapshotService.get_contract_snapshot(contract_number)

            # Get contract info
            contract_info = (
                session.query(
                    Transaction.contract_number,
                    Transaction.client_name,
                    db.func.min(Transaction.scan_date).label("start_date"),
                    db.func.max(Transaction.scan_date).label("last_activity"),
                )
                .filter(Transaction.contract_number == contract_number)
                .group_by(Transaction.contract_number, Transaction.client_name)
                .first()
            )

            return {
                "contract_number": contract_number,
                "client_name": contract_info.client_name if contract_info else None,
                "start_date": contract_info.start_date if contract_info else None,
                "last_activity": contract_info.last_activity if contract_info else None,
                "current_items": current_items,
                "historical_snapshots": snapshots,
                "total_current_items": len(current_items),
                "total_historical_items": len(snapshots),
            }

        except Exception as e:
            logger.error(
                f"Error getting contract history with snapshots for {contract_number}: {str(e)}",
                exc_info=True,
            )
            raise
        finally:
            if session:
                session.close()
