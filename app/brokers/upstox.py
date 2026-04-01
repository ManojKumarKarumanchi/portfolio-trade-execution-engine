"""Upstox broker adapter."""
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


class UpstoxAdapter(BaseBroker):
    """
    Upstox broker adapter.

    Credentials format:
    {
        "api_key": "your_api_key",
        "access_token": "your_access_token"
    }

    Production would use upstox-python library:
        from upstox_api.api import Session
        s = Session(api_key)
        s.set_access_token(access_token)
    """

    async def authenticate(self) -> bool:
        """Authenticate with Upstox API."""
        try:
            api_key = self.credentials.get("api_key")
            access_token = self.credentials.get("access_token")

            if not api_key or not access_token:
                raise AuthenticationError("Missing api_key or access_token")

            await asyncio.sleep(0.1)

            self.authenticated = True
            logger.info("Upstox: Authenticated successfully")
            return True

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Upstox: Authentication failed - {e}")
            raise AuthenticationError(f"Authentication failed: {e}")

    async def place_order(
        self,
        symbol: str,
        action: str,
        quantity: int
    ) -> OrderResult:
        """
        Place order with Upstox.

        Production:
            u.place_order(
                transaction_type="BUY" or "SELL",
                instrument=u.get_instrument_by_symbol('NSE_EQ', symbol),
                quantity=quantity,
                order_type="MARKET",
                product_type="I"  # Intraday
            )
        """
        if not self.authenticated:
            raise BrokerAPIError("Not authenticated")

        try:
            await asyncio.sleep(0.2)

            if symbol.startswith("INVALID"):
                raise InvalidSymbolError(f"Symbol {symbol} not found")

            broker_order_id = f"UPS{symbol[:4]}{quantity:06d}"

            logger.info(
                f"Upstox: {action} {quantity} {symbol} - Order ID: {broker_order_id}"
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
            logger.error(f"Upstox: Order failed for {symbol} - {e}")
            return OrderResult(
                success=False,
                symbol=symbol,
                action=action,
                quantity=quantity,
                error_message=str(e)
            )

    async def get_positions(self) -> list[Position]:
        """Get current positions from Upstox."""
        if not self.authenticated:
            raise BrokerAPIError("Not authenticated")

        await asyncio.sleep(0.1)

        return [
            Position(symbol="WIPRO", quantity=20, average_price=450.0),
        ]
