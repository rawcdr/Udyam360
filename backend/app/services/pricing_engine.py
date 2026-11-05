"""Pricing Engine for Udyam360.

Calculates accurate monthly recurring totals, one-time setup charges,
and first-month payments from actual catalogue values and customer attributes.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional, Set
from app.schemas.catalogue import Product
from app.schemas.business_profile import BusinessProfile
from app.schemas.pricing import (
    ProductPriceBreakdown,
    ContractDetail,
    PricingCalculation,
)
from app.services.catalogue_service import catalogue_service


class PricingEngine:
    """Calculates granular pricing based on actual catalogue unit pricing and profile multipliers."""

    def __init__(self, catalogue_svc=None):
        self.catalogue_service = catalogue_svc or catalogue_service

    def determine_quantity(
        self, product: Product, profile: Optional[BusinessProfile] = None, explicit_qty: Optional[int] = None
    ) -> int:
        """Derive appropriate billing quantity based on product unit and customer profile."""
        if explicit_qty is not None and explicit_qty > 0:
            return explicit_qty

        if not profile:
            return 1

        unit = product.unit.strip().lower()

        if unit == "per site":
            return max(1, profile.num_sites or 1)
        elif unit == "per user":
            if profile.num_users:
                return profile.num_users
            return max(1, profile.employee_count or 1)
        elif unit == "per line":
            if profile.num_lines:
                return profile.num_lines
            return 1
        elif unit == "per counter":
            if profile.num_counters:
                return profile.num_counters
            return max(1, profile.num_sites or 1)
        elif unit == "per device":
            if profile.num_devices:
                return profile.num_devices
            return max(1, profile.employee_count or 1)
        elif unit == "per camera":
            if profile.num_cameras:
                return profile.num_cameras
            return 1
        else:
            # per account, per pack, per number, per IP, per channel, per vehicle, etc.
            return 1

    def calculate_price(
        self,
        product_ids: List[str],
        profile: Optional[BusinessProfile] = None,
        quantity_overrides: Optional[Dict[str, int]] = None,
    ) -> PricingCalculation:
        """Compute monthly, setup, and first-month payment breakdowns for a set of products."""
        qty_overrides = quantity_overrides or {}
        breakdowns: List[ProductPriceBreakdown] = []
        contracts: List[ContractDetail] = []

        monthly_min_sum = Decimal("0.00")
        monthly_max_sum = Decimal("0.00")
        setup_min_sum = Decimal("0.00")
        setup_max_sum = Decimal("0.00")

        # De-duplicate product_ids while preserving order
        unique_ids = list(dict.fromkeys(product_ids))

        for p_id in unique_ids:
            product = self.catalogue_service.get_product_by_id(p_id)
            if not product:
                raise ValueError(f"Product ID '{p_id}' not found in catalogue.")

            qty = self.determine_quantity(product, profile, qty_overrides.get(p_id))

            unit_min = Decimal(str(product.price_min_inr_per_month))
            unit_max = Decimal(str(product.price_max_inr_per_month))
            unit_setup = Decimal(str(product.one_time_setup_inr))

            sub_monthly_min = unit_min * qty
            sub_monthly_max = unit_max * qty
            sub_setup = unit_setup * qty

            monthly_min_sum += sub_monthly_min
            monthly_max_sum += sub_monthly_max
            setup_min_sum += sub_setup
            setup_max_sum += sub_setup

            breakdowns.append(
                ProductPriceBreakdown(
                    product_id=product.product_id,
                    product_name=product.product_name,
                    category=product.category,
                    unit=product.unit,
                    quantity=qty,
                    unit_price_min_inr=float(unit_min),
                    unit_price_max_inr=float(unit_max),
                    unit_setup_inr=float(unit_setup),
                    monthly_subtotal_min=float(sub_monthly_min),
                    monthly_subtotal_max=float(sub_monthly_max),
                    setup_subtotal=float(sub_setup),
                    min_contract_months=product.min_contract_months,
                )
            )

            contracts.append(
                ContractDetail(
                    product_id=product.product_id,
                    product_name=product.product_name,
                    min_contract_months=product.min_contract_months,
                    typical_install_days=product.typical_install_days,
                )
            )

        first_month_min = monthly_min_sum + setup_min_sum
        first_month_max = monthly_max_sum + setup_max_sum

        return PricingCalculation(
            monthly_total_min=float(monthly_min_sum),
            monthly_total_max=float(monthly_max_sum),
            setup_total_min=float(setup_min_sum),
            setup_total_max=float(setup_max_sum),
            estimated_first_month_min=float(first_month_min),
            estimated_first_month_max=float(first_month_max),
            contract_details=contracts,
            product_breakdown=breakdowns,
        )


pricing_engine = PricingEngine()

