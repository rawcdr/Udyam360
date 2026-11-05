"""FastAPI router for Product Eligibility endpoints."""

from fastapi import APIRouter
from app.schemas.business_profile import BusinessProfile
from app.schemas.eligibility import EligibilityCheckResponse
from app.services.eligibility_engine import eligibility_engine

router = APIRouter(prefix="/eligibility", tags=["Product Eligibility"])


@router.post("/check", response_model=EligibilityCheckResponse, summary="Check catalogue eligibility for profile")
def check_eligibility(profile: BusinessProfile):
    """Evaluate all 25 catalogue products against the given business profile."""
    return eligibility_engine.check_all_products(profile)

