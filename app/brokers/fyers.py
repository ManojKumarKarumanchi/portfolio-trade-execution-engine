"""Fyers broker adapter."""
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


class FyersAdapter(BaseBroker):
    """
    Fyers broker adapter.

    Credentials format:
    {
        "app_id": "your_app_id",
        "access_token": "your_access_token"
    }

    Production would use fyers-apiv3 library:
        from fyers_apiv3 import fyersModel
        fyers = fyersModel.FyersModel(client_id=app_id, token=access_token)
    """

    async def authenticate(self) -> bool:
        """Authenticate with Fyers API."""
        try:
            app_id = self.credentials.get("app_id")
            access_token = self.credentials.get("access_token")

            if not app_id or not access_token:
                raise AuthenticationError("Missing app_id or access_token")

            await asyncio.sleep(0.1)

            self.authenticated = True
            logger.info("Fyers: Authenticated successfully")
            return True

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Fyers: Authentication failed - {e}")
            raise AuthenticationError(f"Authentication failed: {e}")

    async def place_order(
        self,
        symbol: str,
        action: str,
        quantity: int
    ) -> OrderResult:
        """
        Place order with Fyers.

        Production:
            data = {
                "symbol": f"NSE:{symbol}-EQ",
                "qty": quantity,
                "type": 2,  # Market order
                "side": 1 if action == "BUY" else -1,
                "productType": "INTRADAY",
                "limitPrice": 0,
                "stopPrice": 0,
                "validity": "DAY",
                "disclosedQty": 0,
                "offlineOrder": False
            }
            result = fyers.place_order(data=data)
        """
        if not self.authenticated:
            raise BrokerAPIError("Not authenticated")

        try:
            await asyncio.sleep(0.2)

            if symbol.startswith("INVALID"):
                raise InvalidSymbolError(f"Symbol {symbol} not found")

            broker_order_id = f"FYE{symbol[:4]}{quantity:06d}"

            logger.info(
                f"Fyers: {action} {quantity} {symbol} - Order ID: {broker_order_id}"
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
            logger.error(f"Fyers: Order failed for {symbol} - {e}")
            return OrderResult(
                success=False,
                symbol=symbol,
                action=action,
                quantity=quantity,
                error_message=str(e)
            )

    async def get_positions(self) -> list[Position]:
        """Get current positions from Fyers."""
        if not self.authenticated:
            raise BrokerAPIError("Not authenticated")

        await asyncio.sleep(0.1)

        return [
            Position(symbol="RELIANCE", quantity=8, average_price=2400.0),
        ]
