"""Broker factory for creating broker instances."""
from .base import BaseBroker
from .zerodha import ZerodhaAdapter
from .fyers import FyersAdapter
from .angelone import AngelOneAdapter
from .groww import GrowwAdapter
from .upstox import UpstoxAdapter


class BrokerFactory:
    """
    Factory class for creating broker adapter instances.

    This implements the Factory Pattern, making it trivial to add new brokers.
    To add a 6th broker:
    1. Create new adapter class inheriting BaseBroker
    2. Add entry to _brokers dict
    3. Done - zero changes to core engine!
    """

    _brokers = {
        "zerodha": ZerodhaAdapter,
        "fyers": FyersAdapter,
        "angelone": AngelOneAdapter,
        "groww": GrowwAdapter,
        "upstox": UpstoxAdapter,
    }

    @classmethod
    def get_broker(cls, broker_name: str, credentials: dict) -> BaseBroker:
        """
        Create and return a broker adapter instance.

        Args:
            broker_name: Name of the broker (e.g., "zerodha")
            credentials: Broker-specific credentials

        Returns:
            BaseBroker instance

        Raises:
            ValueError: If broker is not supported

        Example:
            broker = BrokerFactory.get_broker("zerodha", {
                "api_key": "xxx",
                "access_token": "yyy"
            })
        """
        broker_name = broker_name.lower()

        if broker_name not in cls._brokers:
            supported = ", ".join(cls._brokers.keys())
            raise ValueError(
                f"Unsupported broker: {broker_name}. "
                f"Supported brokers: {supported}"
            )

        broker_class = cls._brokers[broker_name]
        return broker_class(credentials)

    @classmethod
    def supported_brokers(cls) -> list[str]:
        """Get list of supported broker names."""
        return list(cls._brokers.keys())

    @classmethod
    def register_broker(cls, name: str, broker_class: type[BaseBroker]):
        """
        Register a new broker adapter (for extensibility).

        Args:
            name: Broker name
            broker_class: Broker adapter class

        Example:
            class ICICI DirectAdapter(BaseBroker):
                ...

            BrokerFactory.register_broker("icicidirect", ICICIDirectAdapter)
        """
        cls._brokers[name.lower()] = broker_class
