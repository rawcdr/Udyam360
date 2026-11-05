"""Pydantic schemas for Bundle Recommendations."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.schemas.catalogue import Product
from app.schemas.pricing import PricingCalculation


class ScoreBreakdown(BaseModel):
    """Transparent scoring components for a recommendation bundle."""

    requirement_match_score: float = Field(..., ge=0, le=100)
    budget_fit_score: float = Field(..., ge=0, le=100)
    catalogue_eligibility_score: float = Field(..., ge=0, le=100)
    segment_suitability_score: float = Field(..., ge=0, le=100)
    total_score: float = Field(..., ge=0, le=100)
    formula_explanation: str


class RecommendedBundle(BaseModel):
    """A fully verified, priced, and scored recommendation bundle."""

    bundle_tier: str = Field(..., description="Essential | Growth | Premium")
    bundle_name: str
    product_ids: List[str]
    products: List[Product]
    pricing: PricingCalculation
    score: ScoreBreakdown
    explanation: Dict[str, Any]
    budget_status: str = Field(
        ...,
        description="WITHIN_BUDGET (entire range fits) | PARTIALLY_WITHIN_BUDGET (min fits, max exceeds) | EXCEEDS_BUDGET (min exceeds) | NO_BUDGET_SPECIFIED",
    )
    budget_gap_inr: float = Field(
        default=0.0,
        description="Amount by which minimum monthly price exceeds budget (0 if minimum fits within budget)",
    )
    max_budget_gap_inr: float = Field(
        default=0.0,
        description="Amount by which maximum monthly price exceeds budget (0 if entire price range fits within budget)",
    )


class RecommendationResponse(BaseModel):
    """Complete multi-tier recommendation response for a customer profile."""

    business_segment: str
    is_primary_target_segment: bool
    status: str = Field(..., description="SUCCESS | PARTIAL | NO_ELIGIBLE_BUNDLE")
    essential_bundle: Optional[RecommendedBundle] = None
    growth_bundle: Optional[RecommendedBundle] = None
    premium_bundle: Optional[RecommendedBundle] = None
    missing_information: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

