"""Pydantic schemas for Order Lifecycle, State Transitions, and Tracking."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class OrderState(str, Enum):
    """Permitted states in the Udyam360 order lifecycle state machine."""

    QUOTE_CONFIRMED = "QUOTE_CONFIRMED"
    KYC_PENDING = "KYC_PENDING"
    KYC_VERIFICATION = "KYC_VERIFICATION"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    KYC_VERIFIED = "KYC_VERIFIED"
    ORDER_PROCESSING = "ORDER_PROCESSING"
    ACTIVATION_IN_PROGRESS = "ACTIVATION_IN_PROGRESS"
    ACTIVATED = "ACTIVATED"
    CANCELLED = "CANCELLED"


class OrderTimelineEvent(BaseModel):
    """Milestone event recording a status progression in the order journey."""

    event_id: str
    from_state: Optional[OrderState] = None
    to_state: OrderState
    title: str
    description: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_simulated: bool = False


class CustomerInfo(BaseModel):
    """Customer identity and service location details captured during order confirmation."""

    business_name: str
    contact_name: Optional[str] = "Owner / Authorized Signatory"
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    installation_address: Optional[str] = "Registered Business Premises"
    city: Optional[str] = None
    segment: Optional[str] = None


class PricingSnapshot(BaseModel):
    """Immutable pricing snapshot taken at quote confirmation."""

    currency: str = "INR"
    monthly_recurring_charges: float = Field(..., ge=0)
    one_time_charges: float = Field(default=0.0, ge=0)
    estimated_first_month: float = Field(..., ge=0)


class OrderCreateRequest(BaseModel):
    """Payload to initiate a new customer order from confirmed quote and KYC case."""

    advisor_session_id: Optional[str] = None
    quote_reference: str = Field(..., min_length=3)
    kyc_case_id: Optional[str] = None
    selected_product_ids: List[str] = Field(..., min_length=1)
    bundle_tier: Optional[str] = "Custom"
    customer_info: CustomerInfo
    pricing: PricingSnapshot


class OrderAdvanceRequest(BaseModel):
    """Payload for advancing the order through lifecycle states (including simulation)."""

    target_state: Optional[OrderState] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Complete order record returned to client applications."""

    order_id: str
    order_reference: str
    quote_reference: str
    kyc_case_id: Optional[str] = None
    advisor_session_id: Optional[str] = None
    current_state: OrderState
    selected_product_ids: List[str]
    bundle_tier: Optional[str] = None
    customer_info: CustomerInfo
    pricing: PricingSnapshot
    created_at: str
    updated_at: str
    timeline: List[OrderTimelineEvent] = Field(default_factory=list)
    is_simulated_stage: bool = False
    next_action_prompt: Optional[str] = None
    session_token: Optional[str] = Field(default=None, description="Signed customer session token")


class OrderTimelineResponse(BaseModel):
    """Timeline milestones for order tracking view."""

    order_id: str
    order_reference: str
    current_state: OrderState
    timeline: List[OrderTimelineEvent]
    is_simulated_stage: bool

