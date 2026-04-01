"""Base broker interface using Adapter Pattern."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class OrderResult:
    """Result of a single order execution."""
    success: bool
    symbol: str
    action: str  # BUY or SELL
    quantity: int
    broker_order_id: str | None = None
    error_message: str | None = None
    executed_at: datetime | None = None

    def __post_init__(self):
        if self.executed_at is None and self.success:
            self.executed_at = datetime.now()


@dataclass
class Position:
    """Broker position/holding."""
    symbol: str
    quantity: int
    average_price: float


class BaseBroker(ABC):
    """
    Abstract base class for broker adapters.

    All broker implementations must inherit from this class and
    implement the three core methods:
    - authenticate()
    - place_order()
    - get_positions()

    This enforces the Adapter Pattern, making it trivial to add new brokers.
    """

    def __init__(self, credentials: dict):
        """
        Initialize broker with credentials.

        Args:
            credentials: Broker-specific authentication credentials
        """
        self.credentials = credentials
        self.authenticated = False
        self.broker_name = self.__class__.__name__.replace("Adapter", "").lower()

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the broker API.

        Returns:
            True if authentication successful, False otherwise

        Raises:
            AuthenticationError: If credentials are invalid
            BrokerAPIError: If broker API is unavailable
        """
        pass

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        action: str,
        quantity: int
    ) -> OrderResult:
        """
        Place a single order with the broker.

        Args:
            symbol: Stock symbol (e.g., "INFY", "TCS")
            action: Order action ("BUY" or "SELL")
            quantity: Number of shares

        Returns:
            OrderResult with execution details

        Raises:
            BrokerAPIError: If order placement fails
            InvalidSymbolError: If symbol is not valid
            InsufficientFundsError: If account lacks funds
        """
        pass

    @abstractmethod
    async def get_positions(self) -> list[Position]:
        """
        Get current holdings/positions from broker.

        Returns:
            List of Position objects

        Raises:
            BrokerAPIError: If unable to fetch positions
        """
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}(authenticated={self.authenticated})>"


class BrokerError(Exception):
    """Base exception for broker-related errors."""
    pass


class AuthenticationError(BrokerError):
    """Raised when broker authentication fails."""
    pass


class BrokerAPIError(BrokerError):
    """Raised when broker API returns an error."""
    pass


class InvalidSymbolError(BrokerError):
    """Raised when symbol is not valid."""
    pass


class InsufficientFundsError(BrokerError):
    """Raised when account has insufficient funds."""
    pass


class RateLimitError(BrokerError):
    """Raised when broker API rate limit is hit."""
    pass
