"""Webhook notification implementation."""
import aiohttp
from app.core.logger import logger
from app.database.models import Execution
from .base import BaseNotifier


class WebhookNotifier(BaseNotifier):
    """
    Webhook-based notifier.

    Sends execution results to an external HTTP endpoint via POST.
    Useful for integrating with external systems, Slack, Discord, etc.
    """

    def __init__(self, webhook_url: str, timeout: int = 10):
        """
        Initialize webhook notifier.

        Args:
            webhook_url: HTTP(S) URL to send notifications to
            timeout: Request timeout in seconds
        """
        self.webhook_url = webhook_url
        self.timeout = timeout

    async def send(self, execution: Execution) -> bool:
        """Send notification via HTTP webhook."""
        try:
            summary = self._format_execution_summary(execution)

            logger.info(f"Sending webhook notification to {self.webhook_url}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=summary,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status in [200, 201, 202, 204]:
                        logger.info(
                            f"Webhook sent successfully - Status: {response.status}"
                        )
                        return True
                    else:
                        logger.error(
                            f"Webhook failed - Status: {response.status}, "
                            f"Response: {await response.text()}"
                        )
                        return False

        except aiohttp.ClientError as e:
            logger.error(f"Webhook request failed: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Webhook notifier failed: {e}", exc_info=True)
            return False
