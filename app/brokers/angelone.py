"""AngelOne (SmartAPI) broker adapter."""
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


class AngelOneAdapter(BaseBroker):
    """
    AngelOne broker adapter using SmartAPI.

    Credentials format:
    {
        "api_key": "your_api_key",
        "client_id": "your_client_id",
        "password": "your_password",
        "totp": "optional_totp"
    }

    Production would use smartapi-python library:
        from smartapi import SmartConnect
        obj = SmartConnect(api_key=api_key)
        data = obj.generateSession(client_id, password, totp)
    """

    async def authenticate(self) -> bool:
        """Authenticate with AngelOne SmartAPI."""
        try:
            api_key = self.credentials.get("api_key")
            client_id = self.credentials.get("client_id")
            password = self.credentials.get("password")

            if not all([api_key, client_id, password]):
                raise AuthenticationError("Missing required credentials")

            await asyncio.sleep(0.1)

            self.authenticated = True
            logger.info("AngelOne: Authenticated successfully")
            return True

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"AngelOne: Authentication failed - {e}")
            raise AuthenticationError(f"Authentication failed: {e}")

    async def place_order(
        self,
        symbol: str,
        action: str,
        quantity: int
    ) -> OrderResult:
        """
        Place order with AngelOne.

        Production:
            orderparams = {
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": token,
                "transactiontype": "BUY" or "SELL",
                "exchange": "NSE",
                "ordertype": "MARKET",
                "producttype": "INTRADAY",
                "duration": "DAY",
                "quantity": quantity
            }
            order_id = obj.placeOrder(orderparams)
        """
        if not self.authenticated:
            raise BrokerAPIError("Not authenticated")

        try:
            await asyncio.sleep(0.2)

            if symbol.startswith("INVALID"):
                raise InvalidSymbolError(f"Symbol {symbol} not found")

            broker_order_id = f"ANG{symbol[:4]}{quantity:06d}"

            logger.info(
                f"AngelOne: {action} {quantity} {symbol} - Order ID: {broker_order_id}"
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
            logger.error(f"AngelOne: Order failed for {symbol} - {e}")
            return OrderResult(
                success=False,
                symbol=symbol,
                action=action,
                quantity=quantity,
                error_message=str(e)
            )

    async def get_positions(self) -> list[Position]:
        """Get current positions from AngelOne."""
        if not self.authenticated:
            raise BrokerAPIError("Not authenticated")

        await asyncio.sleep(0.1)

        return [
            Position(symbol="SBIN", quantity=15, average_price=550.0),
        ]
