"""Schemas for product eligibility checks."""

from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class EligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"
    DEPENDENCY_REQUIRED = "DEPENDENCY_REQUIRED"


class ProductEligibility(BaseModel):
    """Detailed eligibility evaluation for a single product."""

    product_id: str
    product_name: str
    category: str
    is_eligible: bool = Field(..., description="True if unconditionally ELIGIBLE")
    eligibility_status: EligibilityStatus
    reasons: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    required_dependencies: List[str] = Field(default_factory=list)
    eligible_prerequisites: List[str] = Field(default_factory=list)


class EligibilityCheckResponse(BaseModel):
    """Full catalogue eligibility check result for a given customer profile."""

    business_segment: Optional[str]
    total_evaluated: int
    eligible_count: int
    ineligible_count: int
    needs_info_count: int
    dependency_required_count: int
    results: List[ProductEligibility]

