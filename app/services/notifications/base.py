"""Base notifier interface."""
from abc import ABC, abstractmethod
from app.database.models import Execution


class BaseNotifier(ABC):
    """
    Abstract base class for notification implementations.

    All notifiers must implement the send() method.
    """

    @abstractmethod
    async def send(self, execution: Execution) -> bool:
        """
        Send execution notification.

        Args:
            execution: Execution model with complete results

        Returns:
            True if notification sent successfully, False otherwise
        """
        pass

    def _format_execution_summary(self, execution: Execution) -> dict:
        """
        Format execution into notification payload.

        Returns:
            Dictionary suitable for JSON serialization
        """
        return {
            "execution_id": execution.id,
            "broker": execution.broker,
            "status": execution.status.value,
            "summary": {
                "total_orders": execution.total_orders,
                "successful": execution.successful_orders,
                "failed": execution.failed_orders
            },
            "timestamps": {
                "created_at": execution.created_at.isoformat() if execution.created_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            },
            "orders": [
                {
                    "symbol": order.symbol,
                    "action": order.action.value,
                    "quantity": order.quantity,
                    "status": order.status.value,
                    "broker_order_id": order.broker_order_id,
                    "error": order.error_message,
                    "retry_count": order.retry_count
                }
                for order in execution.orders
            ],
            "error_message": execution.error_message
        }
