"""Pydantic schemas for Pricing calculations."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class ProductPriceBreakdown(BaseModel):
    """Detailed price calculation for an individual product in a bundle."""

    product_id: str
    product_name: str
    category: str
    unit: str
    quantity: int
    unit_price_min_inr: float
    unit_price_max_inr: float
    unit_setup_inr: float
    monthly_subtotal_min: float
    monthly_subtotal_max: float
    setup_subtotal: float
    min_contract_months: int


class ContractDetail(BaseModel):
    """Contractual commitment per product line item."""

    product_id: str
    product_name: str
    min_contract_months: int
    typical_install_days: int


class PricingCalculation(BaseModel):
    """Standardized price calculation output."""

    monthly_total_min: float = Field(..., description="Minimum monthly recurring charges")
    monthly_total_max: float = Field(..., description="Maximum monthly recurring charges")
    setup_total_min: float = Field(..., description="Minimum one-time setup charges")
    setup_total_max: float = Field(..., description="Maximum one-time setup charges")
    estimated_first_month_min: float = Field(..., description="Estimated minimum Day-1 payment (Month 1 MRC + Setup)")
    estimated_first_month_max: float = Field(..., description="Estimated maximum Day-1 payment (Month 1 MRC + Setup)")
    contract_details: List[ContractDetail]
    product_breakdown: List[ProductPriceBreakdown]

