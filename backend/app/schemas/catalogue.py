"""Pydantic schemas for the Product Catalogue."""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator


class Product(BaseModel):
    """Schema representing an individual product from the Accel Business catalogue."""

    product_id: str = Field(..., description="Unique product identifier (e.g., P01)")
    category: str = Field(..., description="Product category (Connectivity, Communication, etc.)")
    product_name: str = Field(..., description="Commercial product name")
    description: str = Field(..., description="Detailed product description")
    unit: str = Field(..., description="Billing unit (per site, per line, per user, etc.)")
    price_min_inr_per_month: int = Field(..., ge=0, description="Minimum monthly recurring price in INR")
    price_max_inr_per_month: int = Field(..., ge=0, description="Maximum monthly recurring price in INR")
    one_time_setup_inr: int = Field(..., ge=0, description="One-time installation or setup fee in INR")
    min_contract_months: int = Field(..., ge=1, description="Minimum contract duration in months")
    available_city_tiers: List[int] = Field(..., description="Applicable city tiers (1, 2)")
    min_employees: int = Field(..., ge=1, description="Minimum employee count required for eligibility")
    min_sites: int = Field(..., ge=1, description="Minimum business locations required")
    requires_gstin: bool = Field(..., description="Whether active GSTIN registration is mandatory")
    requires_one_of: List[str] = Field(default_factory=list, description="List of prerequisite product IDs (at least one must be present)")
    typical_install_days: int = Field(..., ge=1, description="Standard fulfillment turnaround in days")
    target_segments: List[str] = Field(..., description="Target business segment codes (micro, prof, multi, mfg)")

    @field_validator("price_max_inr_per_month")
    @classmethod
    def validate_price_range(cls, v: int, info) -> int:
        min_price = info.data.get("price_min_inr_per_month")
        if min_price is not None and v < min_price:
            raise ValueError(f"price_max_inr_per_month ({v}) cannot be less than price_min_inr_per_month ({min_price})")
        return v


class CatalogueSummary(BaseModel):
    """Statistical summary of the loaded product catalogue."""

    total_products: int
    categories: Dict[str, int]
    units: Dict[str, int]
    gstin_required_count: int
    price_range_overall: Dict[str, int]
    target_segment_counts: Dict[str, int]

