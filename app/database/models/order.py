"""Order model for tracking individual trade executions."""
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database.base import Base


class OrderStatus(str, enum.Enum):
    """Order execution status."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class OrderAction(str, enum.Enum):
    """Order action types."""
    BUY = "BUY"
    SELL = "SELL"


class Order(Base):
    """
    Tracks individual order execution within a portfolio request.

    Each order represents one BUY or SELL action for a specific symbol.
    Multiple orders belong to one execution.
    """
    __tablename__ = "orders"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to execution
    execution_id = Column(
        String,
        ForeignKey("executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Order details
    symbol = Column(String, nullable=False, index=True)
    action = Column(SQLEnum(OrderAction), nullable=False)
    quantity = Column(Integer, nullable=False)

    # Execution tracking
    status = Column(
        SQLEnum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True
    )
    retry_count = Column(Integer, default=0)

    # Broker response
    broker_order_id = Column(String, nullable=True)  # Broker's order ID
    error_message = Column(String, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    executed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    execution = relationship("Execution", back_populates="orders")

    def __repr__(self):
        return (
            f"<Order(id={self.id}, symbol={self.symbol}, "
            f"action={self.action}, qty={self.quantity}, "
            f"status={self.status})>"
        )

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "symbol": self.symbol,
            "action": self.action.value,
            "quantity": self.quantity,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "broker_order_id": self.broker_order_id,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }
