"""Pydantic schemas for execution requests and responses."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum


class ActionType(str, Enum):
    """Order action types."""
    BUY = "BUY"
    SELL = "SELL"
    REBALANCE = "REBALANCE"


class OrderActionSchema(BaseModel):
    """Schema for a single order action."""
    type: ActionType = Field(..., description="Action type: BUY, SELL, or REBALANCE")
    symbol: str = Field(..., min_length=1, max_length=20, description="Stock symbol (e.g., INFY, TCS)")
    qty: int = Field(..., gt=0, description="Quantity of shares")

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate symbol is alphanumeric."""
        if not v.replace('&', '').replace('-', '').isalnum():
            raise ValueError("Symbol must be alphanumeric")
        return v.upper()

    @field_validator('qty')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate quantity is reasonable."""
        if v > 100000:
            raise ValueError("Quantity too large (max 100,000)")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "type": "BUY",
                "symbol": "INFY",
                "qty": 10
            }
        }


class ExecutionRequest(BaseModel):
    """Schema for execution request."""
    execution_id: str | None = Field(
        None,
        description="Optional execution ID for idempotency. Server generates if not provided."
    )
    broker: str = Field(..., description="Broker name (zerodha, fyers, angelone, groww, upstox)")
    credentials: dict = Field(..., description="Broker-specific credentials")
    actions: list[OrderActionSchema] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of order actions to execute"
    )

    @field_validator('broker')
    @classmethod
    def validate_broker(cls, v: str) -> str:
        """Validate broker is supported."""
        supported = ["zerodha", "fyers", "angelone", "groww", "upstox"]
        if v.lower() not in supported:
            raise ValueError(f"Unsupported broker. Must be one of: {', '.join(supported)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "broker": "zerodha",
                "credentials": {
                    "api_key": "your_api_key",
                    "access_token": "your_access_token"
                },
                "actions": [
                    {"type": "BUY", "symbol": "INFY", "qty": 10},
                    {"type": "SELL", "symbol": "TCS", "qty": 5},
                    {"type": "REBALANCE", "symbol": "HDFC", "qty": -3}
                ]
            }
        }


class OrderResponse(BaseModel):
    """Schema for individual order result."""
    symbol: str
    action: str
    quantity: int
    status: str
    broker_order_id: str | None = None
    error_message: str | None = None
    retry_count: int = 0
    executed_at: datetime | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "INFY",
                "action": "BUY",
                "quantity": 10,
                "status": "success",
                "broker_order_id": "230410000123456",
                "error_message": None,
                "retry_count": 0
            }
        }


class ExecutionResponse(BaseModel):
    """Schema for execution response."""
    execution_id: str
    status: str
    message: str
    broker: str | None = None
    total_orders: int | None = None
    successful_orders: int | None = None
    failed_orders: int | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None
    orders: list[OrderResponse] | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "execution_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "message": "Execution completed successfully",
                "broker": "zerodha",
                "total_orders": 3,
                "successful_orders": 3,
                "failed_orders": 0,
                "orders": [
                    {
                        "symbol": "INFY",
                        "action": "BUY",
                        "quantity": 10,
                        "status": "success"
                    }
                ]
            }
        }


class StatusResponse(BaseModel):
    """Schema for execution status query response."""
    execution_id: str
    status: str
    broker: str
    total_orders: int
    successful_orders: int
    failed_orders: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    orders: list[OrderResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "execution_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "partial_success",
                "broker": "zerodha",
                "total_orders": 3,
                "successful_orders": 2,
                "failed_orders": 1,
                "created_at": "2026-04-01T12:30:45Z",
                "updated_at": "2026-04-01T12:31:15Z",
                "completed_at": "2026-04-01T12:31:15Z",
                "orders": [...]
            }
        }
