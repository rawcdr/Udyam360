"""Deterministic Bundle Recommendation Engine for Udyam360.

Produces Essential, Growth, and Premium recommendation bundles based on customer profiles,
catalogue eligibility, dependency graph closure, segment suitability, and budget constraints.
"""

from typing import List, Dict, Set, Optional, Tuple, Any
import re
from app.core.config import settings
from app.schemas.catalogue import Product
from app.schemas.business_profile import BusinessProfile, TargetSegmentEnum
from app.schemas.eligibility import EligibilityStatus, ProductEligibility
from app.schemas.pricing import PricingCalculation
from app.schemas.recommendation import (
    ScoreBreakdown,
    RecommendedBundle,
    RecommendationResponse,
)
from app.services.catalogue_service import catalogue_service
from app.services.eligibility_engine import eligibility_engine
from app.services.segment_service import segment_service
from app.services.pricing_engine import pricing_engine
from app.services.bundle_explanation import bundle_explanation_service


class RecommendationEngine:
    """Orchestrates catalogue-aware, explainable recommendation generation."""

    def __init__(
        self,
        catalogue_svc=None,
        eligibility_eng=None,
        segment_svc=None,
        pricing_eng=None,
        explanation_svc=None,
    ):
        self.catalogue_service = catalogue_svc or catalogue_service
        self.eligibility_engine = eligibility_eng or eligibility_engine
        self.segment_service = segment_svc or segment_service
        self.pricing_engine = pricing_eng or pricing_engine
        self.explanation_service = explanation_svc or bundle_explanation_service

    def generate_recommendations(self, profile: BusinessProfile) -> RecommendationResponse:
        """Main recommendation entry point: generates Essential, Growth, and Premium bundles."""
        seg_info = self.segment_service.identify_segment(profile)
        seg_code = seg_info["segment_code"]
        is_primary = seg_info["is_primary_target"]

        # 1. Evaluate full catalogue eligibility
        eligibility_report = self.eligibility_engine.check_all_products(profile)
        eligible_ids: Set[str] = {
            item.product_id
            for item in eligibility_report.results
            if item.is_eligible or item.eligibility_status == EligibilityStatus.DEPENDENCY_REQUIRED
        }

        # Collect missing information across the evaluation
        all_missing_info: Set[str] = set()
        for item in eligibility_report.results:
            all_missing_info.update(item.missing_information)

        notes: List[str] = []
        if not is_primary:
            notes.append(
                f"Note: Profile segment '{seg_code}' is outside the primary hackathon target segments "
                "(Micro Retail and Professional Offices). Recommendations generated using general SMB catalogue heuristics."
            )

        # 2. Identify candidate products explicitly matching customer requests
        requested_product_ids = self._match_customer_requests(profile, eligible_ids)

        # 3. Generate candidate product sets for Essential, Growth, and Premium tiers
        essential_ids = self._assemble_bundle_tier("Essential", seg_code, profile, eligible_ids, requested_product_ids)
        growth_ids = self._assemble_bundle_tier("Growth", seg_code, profile, eligible_ids, requested_product_ids)
        premium_ids = self._assemble_bundle_tier("Premium", seg_code, profile, eligible_ids, requested_product_ids)

        # 4. Resolve dependencies and validate each bundle
        essential_bundle = self._build_and_validate_bundle("Essential", essential_ids, profile, list(all_missing_info))
        growth_bundle = self._build_and_validate_bundle("Growth", growth_ids, profile, list(all_missing_info))
        premium_bundle = self._build_and_validate_bundle("Premium", premium_ids, profile, list(all_missing_info))

        # Determine overall status
        status = "SUCCESS"
        if not essential_bundle and not growth_bundle and not premium_bundle:
            status = "NO_ELIGIBLE_BUNDLE"
            notes.append("No complete bundle could be formed that satisfies all hard eligibility conditions.")
        elif not essential_bundle or not growth_bundle or not premium_bundle:
            status = "PARTIAL"
            notes.append("One or more bundle tiers could not be completed due to eligibility or budget constraints.")

        return RecommendationResponse(
            business_segment=seg_code,
            is_primary_target_segment=is_primary,
            status=status,
            essential_bundle=essential_bundle,
            growth_bundle=growth_bundle,
            premium_bundle=premium_bundle,
            missing_information=sorted(list(all_missing_info)),
            notes=notes,
        )

    def _match_customer_requests(self, profile: BusinessProfile, eligible_ids: Set[str]) -> Set[str]:
        """Match explicitly requested categories, product IDs, and keywords against eligible products."""
        matched: Set[str] = set()

        for p_id in eligible_ids:
            prod = self.catalogue_service.get_product_by_id(p_id)
            if not prod:
                continue

            # Check explicit product ID match
            if p_id in profile.required_services:
                matched.add(p_id)
                continue

            # Check category match
            if any(req_cat.lower() == prod.category.lower() for req_cat in profile.required_categories):
                matched.add(p_id)
                continue

            # Check keyword match in product name / description using word boundary
            combined_desc = f"{prod.product_name} {prod.description} {prod.category}".lower()
            for req_kw in profile.required_services:
                kw = req_kw.strip().lower()
                # Use regex word boundary to prevent 'pos' matching 'postpaid'
                pattern = rf"\b{re.escape(kw)}\b"
                if re.search(pattern, combined_desc) or kw in [prod.product_id.lower()]:
                    matched.add(p_id)
                    break

        return matched

    def _assemble_bundle_tier(
        self,
        tier: str,
        seg_code: str,
        profile: BusinessProfile,
        eligible_ids: Set[str],
        requested_ids: Set[str],
    ) -> Set[str]:
        """Assemble product set for a specific tier based on segment preferences and requested items."""
        tier_products: Set[str] = set(requested_ids)

        # Base connectivity product selection
        connectivity_options = [p for p in ["P04", "P01", "P02", "P03"] if p in eligible_ids]

        if seg_code == TargetSegmentEnum.MICRO_RETAIL.value:
            # Micro Retail Assembly
            if tier == "Essential":
                # Prefer lowest cost broadband (P04 AirFiber 100 @ 899 or P01 Biz Fibre @ 999)
                if not any(p in tier_products for p in ["P01", "P02", "P03", "P04", "P05", "P06"]):
                    if connectivity_options:
                        tier_products.add(connectivity_options[0])
                # If budget allows, include POS or Mobile
                if "P19" in eligible_ids and ("pos" in str(profile.required_services).lower() or profile.monthly_budget_inr is None or profile.monthly_budget_inr >= 1500):
                    tier_products.add("P19")
                elif "P07" in eligible_ids:
                    tier_products.add("P07")

            elif tier == "Growth":
                # High-reliability fibre or airfiber
                base = "P01" if "P01" in eligible_ids else (connectivity_options[0] if connectivity_options else None)
                if base:
                    tier_products.add(base)
                # POS & Billing
                if "P19" in eligible_ids:
                    tier_products.add("P19")
                # WhatsApp Business or SMS
                if "P15" in eligible_ids:
                    tier_products.add("P15")
                elif "P14" in eligible_ids:
                    tier_products.add("P14")
                # Business Mobile
                if "P07" in eligible_ids:
                    tier_products.add("P07")

            elif tier == "Premium":
                # Comprehensive store suite
                base = "P01" if "P01" in eligible_ids else (connectivity_options[0] if connectivity_options else None)
                if base:
                    tier_products.add(base)
                for add_on in ["P19", "P23", "P22", "P15", "P18", "P07"]:
                    if add_on in eligible_ids:
                        tier_products.add(add_on)

        elif seg_code == TargetSegmentEnum.PROFESSIONAL_OFFICE.value:
            # Professional Office Assembly
            if tier == "Essential":
                # Biz Fibre 100 (P01) or Biz Fibre 300 (P02) + Cloud Email (P16)
                if not any(p in tier_products for p in ["P01", "P02", "P03", "P04", "P05", "P06"]):
                    base = "P01" if "P01" in eligible_ids else (connectivity_options[0] if connectivity_options else None)
                    if base:
                        tier_products.add(base)
                if "P16" in eligible_ids:
                    tier_products.add("P16")

            elif tier == "Growth":
                # Biz Fibre 300 (P02) or Biz Fibre 100 (P01)
                base = "P02" if "P02" in eligible_ids else ("P01" if "P01" in eligible_ids else (connectivity_options[0] if connectivity_options else None))
                if base:
                    tier_products.add(base)
                # Office suite + Cloud Backup + Endpoint Security
                for add_on in ["P16", "P17", "P20", "P11", "P09"]:
                    if add_on in eligible_ids:
                        tier_products.add(add_on)

            elif tier == "Premium":
                # Top-tier broadband (P02, P03 if eligible, or P01)
                base = "P03" if "P03" in eligible_ids else ("P02" if "P02" in eligible_ids else "P01")
                if base in eligible_ids:
                    tier_products.add(base)
                for add_on in ["P16", "P17", "P20", "P09", "P11", "P12", "P18", "P08"]:
                    if add_on in eligible_ids:
                        tier_products.add(add_on)

        else:
            # General SMB fallback
            if connectivity_options:
                tier_products.add(connectivity_options[0])
            if tier in ["Growth", "Premium"] and "P16" in eligible_ids:
                tier_products.add("P16")
            if tier == "Premium" and "P20" in eligible_ids:
                tier_products.add("P20")

        return tier_products

    def _build_and_validate_bundle(
        self,
        tier: str,
        product_ids: Set[str],
        profile: BusinessProfile,
        missing_info: List[str],
    ) -> Optional[RecommendedBundle]:
        """Resolve dependencies, price, validate budget, score, and build a RecommendedBundle."""
        if not product_ids:
            return None

        # 1. Resolve product dependencies (closure)
        try:
            resolved_ids, _ = self.eligibility_engine.resolve_dependencies(product_ids, profile)
        except Exception:
            return None

        # 2. Strict re-validation of all products in bundle
        bundle_products: List[Product] = []
        for p_id in sorted(list(resolved_ids)):
            prod = self.catalogue_service.get_product_by_id(p_id)
            if not prod:
                return None
            eval_res = self.eligibility_engine.evaluate_product(prod, profile, resolved_ids)
            if eval_res.eligibility_status == EligibilityStatus.INELIGIBLE:
                return None  # Failed hard eligibility condition
            bundle_products.append(prod)

        # 3. Pricing Calculation
        pricing = self.pricing_engine.calculate_price(list(resolved_ids), profile)

        # 4. Budget Compatibility Evaluation
        budget_status = "NO_BUDGET_SPECIFIED"
        budget_gap = 0.0
        max_budget_gap = 0.0
        if profile.monthly_budget_inr is not None:
            budget = float(profile.monthly_budget_inr)
            m_min = float(pricing.monthly_total_min)
            m_max = float(pricing.monthly_total_max)
            if m_max <= budget:
                budget_status = "WITHIN_BUDGET"
            elif m_min <= budget < m_max:
                budget_status = "PARTIALLY_WITHIN_BUDGET"
                max_budget_gap = float(round(m_max - budget, 2))
            else:
                budget_status = "EXCEEDS_BUDGET"
                budget_gap = float(round(m_min - budget, 2))
                max_budget_gap = float(round(m_max - budget, 2))

        # 5. Calculate Transparent Scoring
        score_breakdown = self._calculate_score(bundle_products, pricing, profile)

        # 6. Generate Deterministic Explanations
        explanation = self.explanation_service.explain_bundle(
            bundle_tier=tier,
            products=bundle_products,
            pricing=pricing,
            profile=profile,
            missing_info=missing_info,
        )

        tier_names = {
            "Essential": f"{profile.business_type or 'MSME'} Essential Starter Pack",
            "Growth": f"{profile.business_type or 'MSME'} Digital Growth Bundle",
            "Premium": f"{profile.business_type or 'MSME'} Complete Enterprise Suite",
        }

        return RecommendedBundle(
            bundle_tier=tier,
            bundle_name=tier_names.get(tier, f"{tier} Bundle"),
            product_ids=[p.product_id for p in bundle_products],
            products=bundle_products,
            pricing=pricing,
            score=score_breakdown,
            explanation=explanation.to_dict(),
            budget_status=budget_status,
            budget_gap_inr=budget_gap,
            max_budget_gap_inr=max_budget_gap,
        )

    def _calculate_score(
        self,
        products: List[Product],
        pricing: PricingCalculation,
        profile: BusinessProfile,
    ) -> ScoreBreakdown:
        """Transparent scoring using configurable weights:
        - Requirement match: 50%
        - Budget fit: 25%
        - Catalogue eligibility & completeness: 15%
        - Segment suitability: 10%
        """
        w_req = settings.WEIGHT_REQUIREMENT_MATCH
        w_bud = settings.WEIGHT_BUDGET_FIT
        w_cat = settings.WEIGHT_CATALOGUE_ELIGIBILITY
        w_seg = settings.WEIGHT_SEGMENT_SUITABILITY

        # 1. Requirement Match (0 - 100)
        req_score = 100.0
        total_explicit_reqs = len(profile.required_categories) + len(profile.required_services)
        if total_explicit_reqs > 0:
            satisfied_cnt = 0
            bundle_cats = {p.category.lower() for p in products}
            bundle_text = " ".join([f"{p.product_id} {p.product_name} {p.description}" for p in products]).lower()

            for cat in profile.required_categories:
                if cat.lower() in bundle_cats:
                    satisfied_cnt += 1

            for req in profile.required_services:
                if req.lower() in bundle_text:
                    satisfied_cnt += 1

            req_score = min(100.0, (satisfied_cnt / total_explicit_reqs) * 100.0)

        # 2. Budget Fit (0 - 100)
        bud_score = 100.0
        if profile.monthly_budget_inr is not None and profile.monthly_budget_inr > 0:
            budget = float(profile.monthly_budget_inr)
            m_min = float(pricing.monthly_total_min)
            m_max = float(pricing.monthly_total_max)
            if m_max <= budget:
                # Entire monthly range is within budget
                bud_score = max(85.0, min(100.0, 100.0 - (budget - m_min) / budget * 10.0))
            elif m_min <= budget < m_max:
                # Minimum price fits, but upper tier usage exceeds budget
                overrun_ratio = (m_max - budget) / budget
                bud_score = max(70.0, min(84.0, 84.0 - overrun_ratio * 40.0))
            else:
                # Minimum price exceeds budget
                overspend_ratio = (m_min - budget) / budget
                bud_score = max(0.0, min(65.0, 65.0 - (overspend_ratio * 100.0)))

        # 3. Catalogue Eligibility & Completeness (0 - 100)
        # 100 because bundle validation strictly prunes invalid products
        cat_score = 100.0
        if profile.has_gstin is None or profile.employee_count is None:
            # Minor deduction if unverified assumptions exist
            cat_score = 90.0

        # 4. Segment Suitability (0 - 100)
        seg_code = profile.get_normalized_segment()
        if products:
            suitability_vals = [
                self.segment_service.score_product_suitability(p, seg_code) for p in products
            ]
            seg_score = (sum(suitability_vals) / len(suitability_vals)) * 100.0
        else:
            seg_score = 50.0

        total = (req_score * w_req) + (bud_score * w_bud) + (cat_score * w_cat) + (seg_score * w_seg)
        total_score = round(min(100.0, max(0.0, total)), 1)

        formula = (
            f"Total ({total_score}) = Requirement Match ({req_score:.1f} × {w_req}) + "
            f"Budget Fit ({bud_score:.1f} × {w_bud}) + "
            f"Eligibility ({cat_score:.1f} × {w_cat}) + "
            f"Segment Suitability ({seg_score:.1f} × {w_seg})"
        )

        return ScoreBreakdown(
            requirement_match_score=round(req_score, 1),
            budget_fit_score=round(bud_score, 1),
            catalogue_eligibility_score=round(cat_score, 1),
            segment_suitability_score=round(seg_score, 1),
            total_score=total_score,
            formula_explanation=formula,
        )


recommendation_engine = RecommendationEngine()
