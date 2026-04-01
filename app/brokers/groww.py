"""Groww broker adapter (Mock - No Public API)."""
import asyncio
from app.core.logger import logger
from .base import (
    BaseBroker,
    OrderResult,
    Position,
    AuthenticationError,
    BrokerAPIError,
    InvalidSymbolError,
)


class GrowwAdapter(BaseBroker):
    """
    Groww broker adapter.

    NOTE: Groww does not provide a public API for trading.
    This is a MOCK implementation to demonstrate the adapter pattern.

    Credentials format:
    {
        "user_id": "your_user_id",
        "token": "mock_token"
    }

    In a real scenario, this would either:
    1. Wait for Groww to release a public API
    2. Use web scraping (not recommended for production)
    3. Use Groww's internal API (requires partnership)
    """

    async def authenticate(self) -> bool:
        """Mock authentication for Groww."""
        try:
            user_id = self.credentials.get("user_id")
            token = self.credentials.get("token")

            if not user_id or not token:
                raise AuthenticationError("Missing user_id or token")

            await asyncio.sleep(0.1)

            self.authenticated = True
            logger.info("Groww: [MOCK] Authenticated successfully")
            return True

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Groww: Authentication failed - {e}")
            raise AuthenticationError(f"Authentication failed: {e}")

    async def place_order(
        self,
        symbol: str,
        action: str,
        quantity: int
    ) -> OrderResult:
        """
        Mock order placement for Groww.

        This simulates successful order placement.
        In production, this would integrate with Groww's API once available.
        """
        if not self.authenticated:
            raise BrokerAPIError("Not authenticated")

        try:
            await asyncio.sleep(0.2)

            if symbol.startswith("INVALID"):
                raise InvalidSymbolError(f"Symbol {symbol} not found")

            broker_order_id = f"GRW{symbol[:4]}{quantity:06d}"

            logger.info(
                f"Groww: [MOCK] {action} {quantity} {symbol} - Order ID: {broker_order_id}"
            )

            return OrderResult(
                success=True,
                symbol=symbol,
                action=action,
                quantity=quantity,
                broker_order_id=broker_order_id
            )

        except InvalidSymbolError:
            raise
        except Exception as e:
            logger.error(f"Groww: Order failed for {symbol} - {e}")
            return OrderResult(
                success=False,
                symbol=symbol,
                action=action,
                quantity=quantity,
                error_message=str(e)
            )

    async def get_positions(self) -> list[Position]:
        """Mock get positions for Groww."""
        if not self.authenticated:
            raise BrokerAPIError("Not authenticated")

        await asyncio.sleep(0.1)

        logger.info("Groww: [MOCK] Fetching positions")
        return [
            Position(symbol="HDFCBANK", quantity=12, average_price=1600.0),
        ]
