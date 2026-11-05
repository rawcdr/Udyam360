"""Deterministic Bundle Explanation Service for Udyam360.

Generates structured, explainable rationales for bundle recommendations, product inclusions,
contract obligations, and unmet requirements without LLM calls.
"""

from typing import List, Dict, Optional, Any
from app.schemas.catalogue import Product
from app.schemas.business_profile import BusinessProfile
from app.schemas.pricing import PricingCalculation
from app.services.segment_service import segment_service


class BundleExplanation:
    """Container for human-readable and structured bundle recommendation explanations."""

    def __init__(
        self,
        bundle_tier: str,
        summary: str,
        segment_fit: str,
        satisfied_requirements: List[str],
        unmet_requirements: List[str],
        product_justifications: Dict[str, str],
        pricing_and_contract_notes: List[str],
        eligibility_assumptions: List[str],
        missing_information_warnings: List[str],
    ):
        self.bundle_tier = bundle_tier
        self.summary = summary
        self.segment_fit = segment_fit
        self.satisfied_requirements = satisfied_requirements
        self.unmet_requirements = unmet_requirements
        self.product_justifications = product_justifications
        self.pricing_and_contract_notes = pricing_and_contract_notes
        self.eligibility_assumptions = eligibility_assumptions
        self.missing_information_warnings = missing_information_warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bundle_tier": self.bundle_tier,
            "summary": self.summary,
            "segment_fit": self.segment_fit,
            "satisfied_requirements": self.satisfied_requirements,
            "unmet_requirements": self.unmet_requirements,
            "product_justifications": self.product_justifications,
            "pricing_and_contract_notes": self.pricing_and_contract_notes,
            "eligibility_assumptions": self.eligibility_assumptions,
            "missing_information_warnings": self.missing_information_warnings,
        }


class BundleExplanationService:
    """Generates deterministic explanations for recommendation bundles."""

    def explain_bundle(
        self,
        bundle_tier: str,
        products: List[Product],
        pricing: PricingCalculation,
        profile: BusinessProfile,
        missing_info: List[str],
    ) -> BundleExplanation:
        """Produce structured justification for the chosen bundle."""
        seg_code = profile.get_normalized_segment()
        biz_name = profile.business_type or "MSME business"

        tier_summaries = {
            "Essential": (
                f"Essential entry bundle providing foundational connectivity and core business operations "
                f"at the lowest recurring monthly outlay for {biz_name}."
            ),
            "Growth": (
                f"Growth-optimized bundle delivering the best balance of operational efficiency, customer communication, "
                f"and digital presence tailored for {biz_name}."
            ),
            "Premium": (
                f"Comprehensive premium bundle providing enterprise-grade security, redundancy, and enhanced productivity "
                f"for modern {biz_name} operations."
            ),
        }
        summary = tier_summaries.get(bundle_tier, f"{bundle_tier} bundle for {biz_name}.")

        # Segment fit
        segment_fit = (
            f"Tailored for {biz_name} ({seg_code} segment). Products align with segment priorities "
            f"such as reliable broadband, point-of-sale, customer communication, and data protection."
        )

        # Product justifications
        justifications: Dict[str, str] = {}
        for p in products:
            justifications[p.product_id] = segment_service.explain_suitability(p, seg_code)

        # Satisfied vs Unmet requirements
        satisfied: List[str] = []
        unmet: List[str] = []

        all_bundle_text = " ".join([f"{p.product_id} {p.product_name} {p.category}" for p in products]).lower()

        # Check required categories
        for cat in profile.required_categories:
            if any(p.category.lower() == cat.lower() for p in products):
                satisfied.append(f"Includes requested category: {cat}")
            else:
                unmet.append(f"Could not include requested category: {cat}")

        # Check required services
        for req in profile.required_services:
            if req.lower() in all_bundle_text:
                satisfied.append(f"Satisfies requested service/keyword: '{req}'")
            else:
                unmet.append(f"Requested service '{req}' was not included in this bundle tier")

        # Pricing & contract notes
        pricing_notes: List[str] = [
            f"Monthly recurring cost ranges from ₹{pricing.monthly_total_min:,.2f} to ₹{pricing.monthly_total_max:,.2f}.",
        ]
        if profile.monthly_budget_inr is not None:
            budget = float(profile.monthly_budget_inr)
            if pricing.monthly_total_max <= budget:
                pricing_notes.append(f"Entire monthly recurring cost range is fully within your budget of ₹{budget:,.2f}.")
            elif pricing.monthly_total_min <= budget < pricing.monthly_total_max:
                gap = pricing.monthly_total_max - budget
                pricing_notes.append(
                    f"Minimum monthly cost (₹{pricing.monthly_total_min:,.2f}) fits within your ₹{budget:,.2f} budget; "
                    f"upper-tier usage (₹{pricing.monthly_total_max:,.2f}) exceeds budget by ₹{gap:,.2f}."
                )
            else:
                gap = pricing.monthly_total_min - budget
                pricing_notes.append(
                    f"Monthly recurring cost exceeds your budget of ₹{budget:,.2f} by at least ₹{gap:,.2f}."
                )

        if pricing.setup_total_min > 0:
            pricing_notes.append(
                f"One-time installation and onboarding charges: ₹{pricing.setup_total_min:,.2f} (payable on first billing invoice, separate from monthly budget)."
            )
        else:
            pricing_notes.append("Zero one-time installation charges (free setup).")

        pricing_notes.append(
            f"Estimated first-month payment (Month 1 MRC + Setup): ₹{pricing.estimated_first_month_min:,.2f} to ₹{pricing.estimated_first_month_max:,.2f} (excludes applicable 18% GST)."
        )

        max_contract = max([c.min_contract_months for c in pricing.contract_details], default=1)
        max_install = max([c.typical_install_days for c in pricing.contract_details], default=1)
        pricing_notes.append(
            f"Minimum contract commitment: {max_contract} months. Estimated activation turnaround: {max_install} business days."
        )

        # Assumptions
        assumptions: List[str] = []
        if profile.employee_count is None:
            assumptions.append("Headcount unprovided: assumed standard single-seat operational tier.")
        if profile.num_sites is None:
            assumptions.append("Business locations unprovided: assumed single business premise.")
        if profile.city_tier is None:
            assumptions.append("Location tier unprovided: assumed standard Tier 1/2 availability.")

        # Missing information warnings
        warnings: List[str] = []
        for info in missing_info:
            if info == "has_gstin":
                warnings.append("GSTIN confirmation pending: products requiring active GSTIN may be restricted.")
            elif info == "employee_count":
                warnings.append("Employee count unprovided: may restrict multi-user volume pricing.")
            elif info == "city_tier":
                warnings.append("City tier verification needed prior to order submission.")

        return BundleExplanation(
            bundle_tier=bundle_tier,
            summary=summary,
            segment_fit=segment_fit,
            satisfied_requirements=satisfied,
            unmet_requirements=unmet,
            product_justifications=justifications,
            pricing_and_contract_notes=pricing_notes,
            eligibility_assumptions=assumptions,
            missing_information_warnings=warnings,
        )


bundle_explanation_service = BundleExplanationService()

