"""Advisor Dialogue Service for Udyam360.

Evaluates missing profile fields, prioritizes follow-up questions deterministically,
and governs when a customer profile is sufficiently complete for recommendations.
"""

from typing import List, Optional, Tuple
from app.schemas.business_profile import BusinessProfile


class AdvisorDialogueService:
    """Calculates missing fields and formulates targeted follow-up questions."""

    def identify_missing_fields(self, profile: BusinessProfile) -> List[str]:
        """Return list of uncollected business profile fields in priority order."""
        missing = []

        if not profile.business_type and not profile.business_segment:
            missing.append("business_type")

        if not profile.city:
            missing.append("city")

        if profile.employee_count is None:
            missing.append("employee_count")

        if profile.num_sites is None:
            missing.append("num_sites")

        if not profile.required_services and not profile.required_categories:
            missing.append("required_services")

        if profile.has_gstin is None:
            missing.append("has_gstin")

        if profile.monthly_budget_inr is None:
            missing.append("monthly_budget_inr")

        return missing

    def is_profile_ready_for_recommendations(self, profile: BusinessProfile) -> bool:
        """Determine whether profile has sufficient information to generate recommendations.
        
        Requires:
        1. Business type / segment identified.
        2. Location (city) or scale (employee_count/num_sites) or specific needs provided.
        """
        has_business = bool(profile.business_type or profile.business_segment)
        has_context = bool(
            profile.city or
            profile.employee_count is not None or
            profile.required_services or
            profile.monthly_budget_inr is not None
        )
        return has_business and has_context

    def get_focused_follow_up(
        self, profile: BusinessProfile, missing_fields: List[str]
    ) -> Optional[Tuple[str, str]]:
        """Select the single highest-priority missing field and return (field_name, natural_question)."""
        if not missing_fields:
            return None

        # Prioritize follow-up fields
        field = missing_fields[0]
        biz_name = profile.business_type or "your business"

        questions = {
            "business_type": (
                "business_type",
                "Could you tell me what kind of business you operate (e.g. pharmacy, kirana store, clinic, CA firm, or salon)?",
            ),
            "city": (
                "city",
                f"Which city or town is {biz_name} located in? This helps verify local broadband network availability.",
            ),
            "employee_count": (
                "employee_count",
                f"How many employees or staff members work at {biz_name}?",
            ),
            "num_sites": (
                "num_sites",
                f"Do you operate from a single shop/office, or do you have multiple branches?",
            ),
            "required_services": (
                "required_services",
                "What digital services do you primarily need (e.g. high-speed broadband, billing POS, CCTV security, or business email)?",
            ),
            "has_gstin": (
                "has_gstin",
                "Do you currently possess an active GST registration (GSTIN)? Certain business telecom plans require active GSTIN.",
            ),
            "monthly_budget_inr": (
                "monthly_budget_inr",
                "Do you have an approximate monthly budget in mind for telecom, internet, and software?",
            ),
        }

        return questions.get(field, (field, f"Could you provide more details regarding {field}?"))


advisor_dialogue_service = AdvisorDialogueService()

