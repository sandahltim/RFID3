# app/services/scheduled_snapshots.py
# scheduled_snapshots.py version: 2025-08-24-v1

from datetime import datetime, timezone, timedelta
from .contract_snapshots import ContractSnapshotService
from ..models.db_models import Transaction, ItemMaster
from .. import db
from sqlalchemy import func, distinct
import logging

logger = logging.getLogger(__name__)


class ScheduledSnapshotService:
    """Service to manage automated contract snapshots on schedule."""

    @staticmethod
    def create_weekly_snapshots(max_days_back=7):
        """
        Create snapshots for all active contracts (Wed/Fri 7am automation).

        Args:
            max_days_back (int): How many days back to look for active contracts

        Returns:
            dict: Summary of snapshot creation results
        """
        logger.info("Starting weekly automated contract snapshots...")

        session = None
        results = {
            "total_contracts": 0,
            "successful_snapshots": 0,
            "failed_snapshots": 0,
            "total_items_snapshotted": 0,
            "contracts_processed": [],
            "errors": [],
        }

        try:
            session = db.session()

            # Find all contracts that have had activity in the last week
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_days_back)

            active_contracts = (
                session.query(
                    distinct(Transaction.contract_number), Transaction.client_name
                )
                .filter(
                    Transaction.scan_date >= cutoff_date,
                    Transaction.contract_number.isnot(None),
                    Transaction.contract_number != "",
                )
                .all()
            )

            logger.info(
                f"Found {len(active_contracts)} active contracts in last {max_days_back} days"
            )
            results["total_contracts"] = len(active_contracts)

            for contract_number, client_name in active_contracts:
                try:
                    # Check if contract has items
                    item_count = (
                        session.query(func.count(ItemMaster.tag_id))
                        .filter(ItemMaster.last_contract_num == contract_number)
                        .scalar()
                    )

                    if item_count > 0:
                        # Create snapshot
                        snapshot_count = (
                            ContractSnapshotService.create_contract_snapshot(
                                contract_number=contract_number,
                                snapshot_type="periodic",
                                created_by="scheduled_task",
                            )
                        )

                        results["successful_snapshots"] += 1
                        results["total_items_snapshotted"] += snapshot_count
                        results["contracts_processed"].append(
                            {
                                "contract_number": contract_number,
                                "client_name": client_name,
                                "items_count": snapshot_count,
                                "status": "success",
                            }
                        )

                        logger.info(
                            f"Created snapshot for contract {contract_number}: {snapshot_count} items"
                        )
                    else:
                        logger.warning(
                            f"Skipped contract {contract_number}: No items found"
                        )
                        results["contracts_processed"].append(
                            {
                                "contract_number": contract_number,
                                "client_name": client_name,
                                "items_count": 0,
                                "status": "skipped_no_items",
                            }
                        )

                except Exception as e:
                    error_msg = f"Failed to create snapshot for contract {contract_number}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    results["failed_snapshots"] += 1
                    results["errors"].append(error_msg)
                    results["contracts_processed"].append(
                        {
                            "contract_number": contract_number,
                            "client_name": client_name,
                            "items_count": 0,
                            "status": "error",
                            "error": str(e),
                        }
                    )

            logger.info(
                f"Weekly snapshots completed: {results['successful_snapshots']} successful, "
                f"{results['failed_snapshots']} failed, "
                f"{results['total_items_snapshotted']} total items"
            )

            return results

        except Exception as e:
            logger.error(
                f"Error in weekly snapshot automation: {str(e)}", exc_info=True
            )
            results["errors"].append(f"System error: {str(e)}")
            return results
        finally:
            if session:
                session.close()

    @staticmethod
    def cleanup_old_periodic_snapshots(days_to_keep=30):
        """
        Clean up old periodic snapshots to prevent database bloat.
        Keeps manual and contract lifecycle snapshots.

        Args:
            days_to_keep (int): Number of days of periodic snapshots to keep

        Returns:
            int: Number of records cleaned up
        """
        logger.info(
            f"Starting cleanup of periodic snapshots older than {days_to_keep} days..."
        )

        session = None
        try:
            session = db.session()

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

            from ..models.db_models import ContractSnapshot

            deleted_count = (
                session.query(ContractSnapshot)
                .filter(
                    ContractSnapshot.snapshot_date < cutoff_date,
                    ContractSnapshot.snapshot_type == "periodic",
                )
                .delete()
            )

            session.commit()
            logger.info(f"Cleaned up {deleted_count} old periodic snapshots")
            return deleted_count

        except Exception as e:
            if session:
                session.rollback()
            logger.error(
                f"Error cleaning up periodic snapshots: {str(e)}", exc_info=True
            )
            raise
        finally:
            if session:
                session.close()

    @staticmethod
    def get_snapshot_schedule_info():
        """
        Get information about the snapshot schedule and last runs.

        Returns:
            dict: Schedule information
        """
        session = None
        try:
            session = db.session()

            from ..models.db_models import ContractSnapshot

            # Get last periodic snapshot
            last_periodic = (
                session.query(func.max(ContractSnapshot.snapshot_date))
                .filter(ContractSnapshot.snapshot_type == "periodic")
                .scalar()
            )

            # Get count of periodic snapshots in last 7 days
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            recent_count = (
                session.query(func.count(ContractSnapshot.id))
                .filter(
                    ContractSnapshot.snapshot_type == "periodic",
                    ContractSnapshot.snapshot_date >= week_ago,
                )
                .scalar()
            )

            return {
                "last_periodic_snapshot": (
                    last_periodic.isoformat() if last_periodic else None
                ),
                "recent_periodic_count": recent_count,
                "schedule": "Wednesdays and Fridays at 7:00 AM",
                "next_cleanup": "Periodic snapshots older than 30 days are automatically cleaned",
            }

        except Exception as e:
            logger.error(f"Error getting schedule info: {str(e)}", exc_info=True)
            return {"error": str(e)}
        finally:
            if session:
                session.close()
