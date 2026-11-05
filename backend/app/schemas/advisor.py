"""Pydantic schemas for GenAI Advisor, profile extraction, and conversation flow."""

from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.schemas.business_profile import BusinessProfile
from app.schemas.recommendation import RecommendationResponse


class ExtractedProfileData(BaseModel):
    """Normalized structured profile extracted from user dialogue."""

    business_type: Optional[str] = Field(default=None, description="e.g. Pharmacy, Kirana, Clinic, CA Firm")
    business_segment: Optional[str] = Field(default=None, description="micro | prof | multi | mfg")
    employee_count: Optional[int] = Field(default=None, ge=1, description="Total headcount")
    num_sites: Optional[int] = Field(default=None, ge=1, description="Number of locations")
    city: Optional[str] = Field(default=None, description="City or town")
    city_tier: Optional[int] = Field(default=None, ge=1, le=2, description="1 or 2")
    has_gstin: Optional[bool] = Field(default=None, description="GSTIN status")
    has_udyam: Optional[bool] = Field(default=None, description="Udyam status")
    monthly_budget_inr: Optional[float] = Field(default=None, ge=0, description="Monthly spend budget")
    required_services: List[str] = Field(default_factory=list, description="Requested services or keywords")
    current_connectivity: Optional[str] = Field(default=None, description="Current ISP or telecom setup")
    current_tools: Optional[str] = Field(default=None, description="Current software or payment tools")
    mobile_lines_required: Optional[int] = Field(default=None, ge=1, description="Business mobile lines")
    number_of_counters: Optional[int] = Field(default=None, ge=1, description="Store checkout counters")
    preferred_language: Optional[str] = Field(default="English", description="Communication language")


class ProfileExtractionResult(BaseModel):
    """Outcome of parsing a user message for business attributes."""

    extracted_profile: ExtractedProfileData
    fields_updated: List[str] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    confidence_by_field: Dict[str, float] = Field(default_factory=dict)
    clarification_required: bool = False
    clarification_reason: Optional[str] = None


class ChatMessage(BaseModel):
    """Single turn message in an advisor onboarding conversation."""

    role: str = Field(..., description="user | assistant | system")
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConversationState(BaseModel):
    """Complete in-memory session state for multi-turn onboarding."""

    conversation_id: str
    profile: BusinessProfile = Field(default_factory=BusinessProfile)
    history: List[ChatMessage] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    turn_count: int = 0
    recommendations_available: bool = False
    last_recommendations: Optional[RecommendationResponse] = None
    status: str = "collecting"  # collecting | ready | recommended | clarification_needed


class AdvisorStartResponse(BaseModel):
    """Response returned upon starting a new advisor conversation."""

    conversation_id: str
    welcome_message: str
    suggested_prompts: List[str]


class AdvisorMessageRequest(BaseModel):
    """Request payload for sending a customer message to the advisor."""

    conversation_id: str
    message: str = Field(..., min_length=1, max_length=2000, description="User message text")


class AdvisorMessageResponse(BaseModel):
    """Assistant turn response containing natural language reply and updated state."""

    conversation_id: str
    assistant_message: str
    extracted_profile: Optional[BusinessProfile] = None
    missing_fields: List[str] = Field(default_factory=list)
    clarification_required: bool = False
    recommendations_available: bool = False
    recommendations: Optional[RecommendationResponse] = None
    processing_status: str = Field(default="SUCCESS", description="SUCCESS | FALLBACK | ERROR")
    error_detail: Optional[str] = None
