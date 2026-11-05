"""Pydantic schemas for Quote Previews."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from app.schemas.business_profile import BusinessProfile
from app.schemas.pricing import PricingCalculation


class QuotePreviewRequest(BaseModel):
    """Client request to preview and price a selected bundle with optional add-ons."""

    profile: BusinessProfile
    bundle_tier: Optional[str] = Field(default="Custom", description="Essential | Growth | Premium | Custom")
    selected_product_ids: List[str] = Field(..., min_length=1, description="List of product IDs to quote")
    quantity_overrides: Optional[Dict[str, int]] = Field(
        default=None, description="Optional custom product quantity overrides (e.g. {'P16': 5})"
    )


class QuotePreviewResponse(BaseModel):
    """Server-validated, server-calculated quote preview with unique reference ID."""

    quote_id: str = Field(..., description="Unique server-generated quote reference identifier (e.g. Q-A1B2C3D4)")
    business_segment: str
    bundle_tier: str
    is_eligible: bool
    eligibility_issues: List[str]
    pricing: PricingCalculation
    typical_install_days: int
    min_contract_months: int
    terms_and_conditions: List[str]

