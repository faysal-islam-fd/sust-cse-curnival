from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional

class Transaction(BaseModel):
    transaction_id: str = Field(..., min_length=1)
    timestamp: str = Field(..., min_length=1)  # ISO 8601
    type: str = Field(..., min_length=1)       # transfer, payment, cash_in, cash_out, settlement, refund
    amount: float
    counterparty: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)     # completed, failed, pending, reversed

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = ["transfer", "payment", "cash_in", "cash_out", "settlement", "refund"]
        if v not in allowed:
            raise ValueError(f"Invalid transaction type. Allowed: {allowed}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = ["completed", "failed", "pending", "reversed"]
        if v not in allowed:
            raise ValueError(f"Invalid transaction status. Allowed: {allowed}")
        return v

class TicketRequest(BaseModel):
    ticket_id: str = Field(..., min_length=1)
    complaint: str = Field(..., min_length=1)
    language: Optional[str] = None
    channel: Optional[str] = None
    user_type: Optional[str] = None
    campaign_context: Optional[str] = None
    transaction_history: Optional[List[Transaction]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        allowed = ["en", "bn", "mixed"]
        if v not in allowed:
            raise ValueError(f"Invalid language '{v}'. Allowed: {allowed}")
        return v

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        allowed = ["in_app_chat", "call_center", "email", "merchant_portal", "field_agent"]
        if v not in allowed:
            raise ValueError(f"Invalid channel '{v}'. Allowed: {allowed}")
        return v

    @field_validator("user_type")
    @classmethod
    def validate_user_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        allowed = ["customer", "merchant", "agent", "unknown"]
        if v not in allowed:
            raise ValueError(f"Invalid user_type '{v}'. Allowed: {allowed}")
        return v
