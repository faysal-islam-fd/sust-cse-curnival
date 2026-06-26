from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class TicketResponse(BaseModel):
    ticket_id: str = Field(..., min_length=1)
    relevant_transaction_id: Optional[str] = None
    evidence_verdict: str
    case_type: str
    severity: str
    department: str
    agent_summary: str = Field(..., min_length=1)
    recommended_next_action: str = Field(..., min_length=1)
    customer_reply: str = Field(..., min_length=1)
    human_review_required: bool
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    reason_codes: Optional[List[str]] = Field(default_factory=list)

    @field_validator("evidence_verdict")
    @classmethod
    def validate_evidence_verdict(cls, v: str) -> str:
        allowed = ["consistent", "inconsistent", "insufficient_data"]
        if v not in allowed:
            raise ValueError(f"Invalid evidence_verdict. Allowed: {allowed}")
        return v

    @field_validator("case_type")
    @classmethod
    def validate_case_type(cls, v: str) -> str:
        allowed = [
            "wrong_transfer",
            "payment_failed",
            "refund_request",
            "duplicate_payment",
            "merchant_settlement_delay",
            "agent_cash_in_issue",
            "phishing_or_social_engineering",
            "other"
        ]
        if v not in allowed:
            raise ValueError(f"Invalid case_type. Allowed: {allowed}")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = ["low", "medium", "high", "critical"]
        if v not in allowed:
            raise ValueError(f"Invalid severity. Allowed: {allowed}")
        return v

    @field_validator("department")
    @classmethod
    def validate_department(cls, v: str) -> str:
        allowed = [
            "customer_support",
            "dispute_resolution",
            "payments_ops",
            "merchant_operations",
            "agent_operations",
            "fraud_risk"
        ]
        if v not in allowed:
            raise ValueError(f"Invalid department. Allowed: {allowed}")
        return v
