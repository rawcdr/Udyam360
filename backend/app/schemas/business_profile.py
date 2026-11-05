"""Pydantic schemas for Customer Business Profile."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TargetSegmentEnum(str, Enum):
    """Normalized target segment identifiers."""
    MICRO_RETAIL = "micro"
    PROFESSIONAL_OFFICE = "prof"
    MULTI_SITE = "multi"
    MANUFACTURING = "mfg"
    OTHER = "other"


def normalize_segment_string(val: Optional[str]) -> Optional[str]:
    """Helper to normalize various segment representations into standard codes."""
    if not val:
        return None
    cleaned = val.strip().lower()
    if any(k in cleaned for k in ["micro", "retail", "kirana", "salon", "pharmacy", "store"]):
        return TargetSegmentEnum.MICRO_RETAIL.value
    if any(k in cleaned for k in ["prof", "clinic", "ca ", "doctor", "lawyer", "coaching", "consult", "office"]):
        return TargetSegmentEnum.PROFESSIONAL_OFFICE.value
    if any(k in cleaned for k in ["multi", "branch", "chain"]):
        return TargetSegmentEnum.MULTI_SITE.value
    if any(k in cleaned for k in ["mfg", "manufactur", "factory", "plant"]):
        return TargetSegmentEnum.MANUFACTURING.value
    return TargetSegmentEnum.OTHER.value


class BusinessProfile(BaseModel):
    """Customer profile representing an MSME onboarder."""

    business_name: Optional[str] = Field(
        default=None,
        description="Legal or trade name of the MSME enterprise",
    )
    business_type: Optional[str] = Field(
        default=None,
        description="Type of business (e.g. Kirana Store, Pharmacy, Clinic, CA Firm, Coaching Centre)",
    )
    business_segment: Optional[str] = Field(
        default=None,
        description="Customer segment ('micro' / 'Micro Retail', 'prof' / 'Professional Offices', etc.)",
    )
    employee_count: Optional[int] = Field(
        default=None,
        ge=1,
        description="Total employee headcount. None indicates unprovided.",
    )
    num_sites: Optional[int] = Field(
        default=None,
        ge=1,
        description="Number of physical business premises. None indicates unprovided.",
    )
    city: Optional[str] = Field(
        default=None,
        description="City or town location.",
    )
    city_tier: Optional[int] = Field(
        default=None,
        ge=1,
        le=2,
        description="City tier (1 or 2). None indicates unprovided.",
    )
    has_gstin: Optional[bool] = Field(
        default=None,
        description="Whether business possesses GSTIN (True = Yes, False = No, None = Unknown).",
    )
    has_udyam: Optional[bool] = Field(
        default=None,
        description="Whether business possesses Udyam registration (True = Yes, False = No, None = Unknown).",
    )
    monthly_budget_inr: Optional[float] = Field(
        default=None,
        ge=0,
        description="Monthly spend limit in INR. None indicates unprovided.",
    )
    preferred_language: Optional[str] = Field(
        default="English",
        description="Preferred language for communication.",
    )
    required_categories: List[str] = Field(
        default_factory=list,
        description="Explicitly requested product categories (e.g. ['Connectivity', 'Security']).",
    )
    required_services: List[str] = Field(
        default_factory=list,
        description="Explicitly requested product IDs or keywords (e.g. ['P01', 'cctv', 'pos']).",
    )
    optional_services: List[str] = Field(
        default_factory=list,
        description="Nice-to-have product IDs or keywords.",
    )
    current_provider: Optional[str] = Field(
        default=None,
        description="Current telecom / internet service provider, if any.",
    )
    additional_requirements: Optional[str] = Field(
        default=None,
        description="Free text notes or specific operational constraints.",
    )

    # Optional explicit quantity overrides
    num_lines: Optional[int] = Field(default=None, ge=1, description="Requested business mobile lines")
    num_devices: Optional[int] = Field(default=None, ge=1, description="Protected devices / PCs count")
    num_cameras: Optional[int] = Field(default=None, ge=1, description="CCTV cameras count")
    num_counters: Optional[int] = Field(default=None, ge=1, description="Billing counters count")
    num_users: Optional[int] = Field(default=None, ge=1, description="SaaS user licenses count")

    @field_validator("business_segment")
    @classmethod
    def normalize_segment(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return normalize_segment_string(v)

    def get_normalized_segment(self) -> str:
        """Derive standard segment code using explicit segment or infer from business_type."""
        if self.business_segment:
            return self.business_segment
        if self.business_type:
            inferred = normalize_segment_string(self.business_type)
            if inferred:
                return inferred
        return TargetSegmentEnum.OTHER.value

