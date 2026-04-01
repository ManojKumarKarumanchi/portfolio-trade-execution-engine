"""Execution model for tracking portfolio execution requests."""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database.base import Base


class ExecutionStatus(str, enum.Enum):
    """Execution status states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


class Execution(Base):
    """
    Tracks the overall execution of a portfolio trade request.

    Each execution represents one API request to execute trades.
    Provides idempotency via unique execution_id.
    """
    __tablename__ = "executions"

    # Primary key: client-provided or server-generated UUID
    id = Column(String, primary_key=True, index=True)

    # Execution metadata
    broker = Column(String, nullable=False, index=True)
    status = Column(
        SQLEnum(ExecutionStatus),
        nullable=False,
        default=ExecutionStatus.PENDING,
        index=True
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Statistics (denormalized for quick queries)
    total_orders = Column(String, default=0)
    successful_orders = Column(String, default=0)
    failed_orders = Column(String, default=0)

    # Error tracking
    error_message = Column(String, nullable=True)

    # Relationships
    orders = relationship(
        "Order",
        back_populates="execution",
        cascade="all, delete-orphan",
        lazy="selectin"  # Eager load orders with execution
    )

    def __repr__(self):
        return (
            f"<Execution(id={self.id}, broker={self.broker}, "
            f"status={self.status}, orders={len(self.orders)})>"
        )

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "execution_id": self.id,
            "broker": self.broker,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_orders": self.total_orders,
            "successful_orders": self.successful_orders,
            "failed_orders": self.failed_orders,
            "error_message": self.error_message,
            "orders": [order.to_dict() for order in self.orders] if self.orders else []
        }
