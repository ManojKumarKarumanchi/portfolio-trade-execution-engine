"""Pydantic schemas for broker credentials."""
from pydantic import BaseModel, Field


class BrokerCredentials(BaseModel):
    """Base schema for broker credentials."""
    pass


class ZerodhaCredentials(BrokerCredentials):
    """Zerodha broker credentials."""
    api_key: str = Field(..., description="Kite Connect API key")
    access_token: str = Field(..., description="User access token")

    class Config:
        json_schema_extra = {
            "example": {
                "api_key": "your_api_key",
                "access_token": "your_access_token"
            }
        }


class FyersCredentials(BrokerCredentials):
    """Fyers broker credentials."""
    app_id: str = Field(..., description="Fyers APP ID")
    access_token: str = Field(..., description="Fyers access token")

    class Config:
        json_schema_extra = {
            "example": {
                "app_id": "your_app_id",
                "access_token": "your_access_token"
            }
        }


class AngelOneCredentials(BrokerCredentials):
    """AngelOne (SmartAPI) broker credentials."""
    api_key: str = Field(..., description="SmartAPI key")
    client_id: str = Field(..., description="Client ID")
    password: str = Field(..., description="Client password")
    totp: str | None = Field(None, description="TOTP token")

    class Config:
        json_schema_extra = {
            "example": {
                "api_key": "your_api_key",
                "client_id": "your_client_id",
                "password": "your_password"
            }
        }


class GrowwCredentials(BrokerCredentials):
    """Groww broker credentials (mock - no public API)."""
    user_id: str = Field(..., description="Groww user ID")
    token: str = Field(..., description="Mock token")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "your_user_id",
                "token": "mock_token"
            }
        }


class UpstoxCredentials(BrokerCredentials):
    """Upstox broker credentials."""
    api_key: str = Field(..., description="Upstox API key")
    access_token: str = Field(..., description="Access token")

    class Config:
        json_schema_extra = {
            "example": {
                "api_key": "your_api_key",
                "access_token": "your_access_token"
            }
        }
