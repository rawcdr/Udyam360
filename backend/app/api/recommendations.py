"""FastAPI router for Bundle Recommendation endpoints."""

from fastapi import APIRouter
from app.schemas.business_profile import BusinessProfile
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_engine import recommendation_engine

router = APIRouter(prefix="/recommendations", tags=["Bundle Recommendations"])


@router.post("", response_model=RecommendationResponse, summary="Generate Essential, Growth, and Premium bundles")
def generate_recommendations(profile: BusinessProfile):
    """Generate explainable, catalogue-aware recommendation bundles for a customer profile."""
    return recommendation_engine.generate_recommendations(profile)

