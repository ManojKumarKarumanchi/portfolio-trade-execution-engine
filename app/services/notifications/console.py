"""Console notification implementation."""
import json
from app.core.logger import logger
from app.database.models import Execution
from .base import BaseNotifier


class ConsoleNotifier(BaseNotifier):
    """
    Console/logging-based notifier.

    Outputs execution results to application logs in structured format.
    This is the default notifier and always works (no external dependencies).
    """

    async def send(self, execution: Execution) -> bool:
        """Send notification via console logging."""
        try:
            summary = self._format_execution_summary(execution)

            # Log as structured JSON for easy parsing
            logger.info("=" * 80)
            logger.info("EXECUTION NOTIFICATION")
            logger.info("=" * 80)
            logger.info(f"Execution ID: {summary['execution_id']}")
            logger.info(f"Broker: {summary['broker']}")
            logger.info(f"Status: {summary['status']}")
            logger.info("-" * 80)
            logger.info("SUMMARY:")
            logger.info(f"  Total Orders: {summary['summary']['total_orders']}")
            logger.info(f"  Successful: {summary['summary']['successful']}")
            logger.info(f"  Failed: {summary['summary']['failed']}")
            logger.info("-" * 80)
            logger.info("ORDERS:")

            for order in summary['orders']:
                status_symbol = "[OK]" if order['status'] == 'success' else "[FAIL]"
                logger.info(
                    f"  {status_symbol} {order['action']} {order['quantity']} {order['symbol']} "
                    f"- Status: {order['status']}"
                )
                if order['error']:
                    logger.info(f"    Error: {order['error']}")
                if order['broker_order_id']:
                    logger.info(f"    Broker Order ID: {order['broker_order_id']}")

            logger.info("=" * 80)

            # Also log as JSON for programmatic parsing
            logger.info(f"Execution JSON: {json.dumps(summary, indent=2)}")

            return True

        except Exception as e:
            logger.error(f"Console notifier failed: {e}", exc_info=True)
            return False
