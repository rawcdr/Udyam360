"""Product Eligibility Engine for Udyam360.

Applies deterministic, catalogue-driven eligibility rules covering GSTIN,
employee thresholds, multi-site constraints, city tiers, and prerequisites.
"""

from typing import List, Set, Optional, Dict, Tuple
from app.schemas.catalogue import Product
from app.schemas.business_profile import BusinessProfile
from app.schemas.eligibility import (
    EligibilityStatus,
    ProductEligibility,
    EligibilityCheckResponse,
)
from app.services.catalogue_service import catalogue_service


class EligibilityEngine:
    """Evaluates product-level eligibility and resolves cross-product dependency requirements."""

    def __init__(self, catalogue_svc=None):
        self.catalogue_service = catalogue_svc or catalogue_service

    def evaluate_product(
        self,
        product: Product,
        profile: BusinessProfile,
        active_bundle_ids: Optional[Set[str]] = None,
    ) -> ProductEligibility:
        """Evaluate a product against a customer business profile."""
        reasons: List[str] = []
        missing_info: List[str] = []
        status = EligibilityStatus.ELIGIBLE
        active_bundle = active_bundle_ids or set()

        # 1. City Tier Check
        if profile.city_tier is not None:
            if profile.city_tier not in product.available_city_tiers:
                status = EligibilityStatus.INELIGIBLE
                reasons.append(
                    f"Product only available in city tier(s) {product.available_city_tiers}; profile is Tier {profile.city_tier}."
                )
        else:
            # If product is restricted to specific tier (e.g. P03 requires Tier 1)
            if product.available_city_tiers != [1, 2]:
                status = EligibilityStatus.NEEDS_INFORMATION
                missing_info.append("city_tier")
                reasons.append(
                    f"Product requires city tier verification (restricted to tier(s) {product.available_city_tiers})."
                )

        # 2. Minimum Employee Count Check
        if product.min_employees > 1:
            if profile.employee_count is None:
                if status != EligibilityStatus.INELIGIBLE:
                    status = EligibilityStatus.NEEDS_INFORMATION
                missing_info.append("employee_count")
                reasons.append(
                    f"Requires at least {product.min_employees} employees, but headcount is unprovided."
                )
            elif profile.employee_count < product.min_employees:
                status = EligibilityStatus.INELIGIBLE
                reasons.append(
                    f"Requires minimum {product.min_employees} employees; profile has {profile.employee_count}."
                )

        # 3. Minimum Sites Check
        if product.min_sites > 1:
            if profile.num_sites is None:
                if status != EligibilityStatus.INELIGIBLE:
                    status = EligibilityStatus.NEEDS_INFORMATION
                missing_info.append("num_sites")
                reasons.append(
                    f"Requires at least {product.min_sites} business sites, but site count is unprovided."
                )
            elif profile.num_sites < product.min_sites:
                status = EligibilityStatus.INELIGIBLE
                reasons.append(
                    f"Requires minimum {product.min_sites} business sites; profile has {profile.num_sites}."
                )

        # 4. GSTIN Requirement Check
        if product.requires_gstin:
            if profile.has_gstin is False:
                status = EligibilityStatus.INELIGIBLE
                reasons.append(
                    "Product requires an active GSTIN registration; customer does not possess GSTIN."
                )
            elif profile.has_gstin is None:
                if status != EligibilityStatus.INELIGIBLE:
                    status = EligibilityStatus.NEEDS_INFORMATION
                missing_info.append("has_gstin")
                reasons.append(
                    "Product mandates active GSTIN registration, but GSTIN status is unconfirmed."
                )

        # 5. Product Dependency Check (requires_one_of)
        eligible_prerequisites: List[str] = []
        if product.requires_one_of:
            # Determine which prerequisites in requires_one_of are eligible for this customer
            for dep_id in product.requires_one_of:
                dep_product = self.catalogue_service.get_product_by_id(dep_id)
                if dep_product:
                    dep_eval = self._evaluate_base_constraints(dep_product, profile)
                    if dep_eval == EligibilityStatus.ELIGIBLE:
                        eligible_prerequisites.append(dep_id)

            # Check if any prerequisite is currently in the active bundle
            has_prereq_in_bundle = any(dep in active_bundle for dep in product.requires_one_of)

            if not has_prereq_in_bundle:
                if not eligible_prerequisites:
                    # No prerequisite is eligible for this customer
                    status = EligibilityStatus.INELIGIBLE
                    reasons.append(
                        f"Requires one of {product.requires_one_of}, but none of the required prerequisites are eligible for this profile."
                    )
                else:
                    if status == EligibilityStatus.ELIGIBLE:
                        status = EligibilityStatus.DEPENDENCY_REQUIRED
                        reasons.append(
                            f"Requires at least one prerequisite product from: {product.requires_one_of}."
                        )

        if not reasons:
            reasons.append("All catalogue eligibility rules satisfied.")

        is_eligible = (status == EligibilityStatus.ELIGIBLE)

        return ProductEligibility(
            product_id=product.product_id,
            product_name=product.product_name,
            category=product.category,
            is_eligible=is_eligible,
            eligibility_status=status,
            reasons=reasons,
            missing_information=missing_info,
            required_dependencies=product.requires_one_of,
            eligible_prerequisites=eligible_prerequisites,
        )

    def _evaluate_base_constraints(self, product: Product, profile: BusinessProfile) -> EligibilityStatus:
        """Internal helper to check base constraints without recursing dependencies."""
        if profile.city_tier is not None and profile.city_tier not in product.available_city_tiers:
            return EligibilityStatus.INELIGIBLE
        if product.min_employees > 1:
            if profile.employee_count is None:
                return EligibilityStatus.NEEDS_INFORMATION
            if profile.employee_count < product.min_employees:
                return EligibilityStatus.INELIGIBLE
        if product.min_sites > 1:
            if profile.num_sites is None:
                return EligibilityStatus.NEEDS_INFORMATION
            if profile.num_sites < product.min_sites:
                return EligibilityStatus.INELIGIBLE
        if product.requires_gstin:
            if profile.has_gstin is False:
                return EligibilityStatus.INELIGIBLE
            if profile.has_gstin is None:
                return EligibilityStatus.NEEDS_INFORMATION
        return EligibilityStatus.ELIGIBLE

    def check_all_products(
        self, profile: BusinessProfile, active_bundle_ids: Optional[Set[str]] = None
    ) -> EligibilityCheckResponse:
        """Evaluate all 25 products in the catalogue against the customer profile."""
        all_prods = self.catalogue_service.get_all_products()
        results: List[ProductEligibility] = []

        el_count = 0
        inel_count = 0
        needs_count = 0
        dep_count = 0

        for prod in all_prods:
            eval_res = self.evaluate_product(prod, profile, active_bundle_ids)
            results.append(eval_res)
            if eval_res.eligibility_status == EligibilityStatus.ELIGIBLE:
                el_count += 1
            elif eval_res.eligibility_status == EligibilityStatus.INELIGIBLE:
                inel_count += 1
            elif eval_res.eligibility_status == EligibilityStatus.NEEDS_INFORMATION:
                needs_count += 1
            elif eval_res.eligibility_status == EligibilityStatus.DEPENDENCY_REQUIRED:
                dep_count += 1

        return EligibilityCheckResponse(
            business_segment=profile.get_normalized_segment(),
            total_evaluated=len(all_prods),
            eligible_count=el_count,
            ineligible_count=inel_count,
            needs_info_count=needs_count,
            dependency_required_count=dep_count,
            results=results,
        )

    def resolve_dependencies(
        self, product_ids: Set[str], profile: BusinessProfile
    ) -> Tuple[Set[str], List[str]]:
        """Ensure all product dependencies are resolved by injecting eligible prerequisites.
        
        Returns:
            (resolved_product_ids, resolution_notes)
        """
        resolved = set(product_ids)
        notes: List[str] = []
        max_depth = 10
        depth = 0

        while depth < max_depth:
            depth += 1
            new_prereq_added = False

            for p_id in list(resolved):
                prod = self.catalogue_service.get_product_by_id(p_id)
                if not prod or not prod.requires_one_of:
                    continue

                # Check if already satisfied
                if any(dep in resolved for dep in prod.requires_one_of):
                    continue

                # Find eligible prerequisites
                eligible_deps = []
                for dep_id in prod.requires_one_of:
                    dep_prod = self.catalogue_service.get_product_by_id(dep_id)
                    if dep_prod:
                        eval_res = self.evaluate_product(dep_prod, profile, resolved)
                        if eval_res.is_eligible or eval_res.eligibility_status == EligibilityStatus.DEPENDENCY_REQUIRED:
                            eligible_deps.append(dep_prod)

                if not eligible_deps:
                    raise ValueError(
                        f"Cannot resolve dependencies for product {p_id}. "
                        f"None of {prod.requires_one_of} are eligible for this customer."
                    )

                # Pick the lowest-cost eligible prerequisite
                eligible_deps.sort(key=lambda x: (x.price_min_inr_per_month, x.one_time_setup_inr))
                selected_prereq = eligible_deps[0]
                resolved.add(selected_prereq.product_id)
                notes.append(
                    f"Automatically added prerequisite '{selected_prereq.product_name}' ({selected_prereq.product_id}) "
                    f"required by '{prod.product_name}' ({prod.product_id})."
                )
                new_prereq_added = True

            if not new_prereq_added:
                break

        if depth >= max_depth:
            raise ValueError("Circular or excessively deep dependency detected during resolution.")

        return resolved, notes


eligibility_engine = EligibilityEngine()

