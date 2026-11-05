"""FastAPI router for Quote Preview and pricing endpoints."""

import uuid
from fastapi import APIRouter, HTTPException
from app.schemas.quote import QuotePreviewRequest, QuotePreviewResponse
from app.schemas.eligibility import EligibilityStatus
from app.services.catalogue_service import catalogue_service
from app.services.eligibility_engine import eligibility_engine
from app.services.pricing_engine import pricing_engine

router = APIRouter(prefix="/quotes", tags=["Quote Previews"])


@router.post("/preview", response_model=QuotePreviewResponse, summary="Server-side quote calculation and validation")
def preview_quote(request: QuotePreviewRequest):
    """Validate customer eligibility and calculate server-side pricing for a selected product combination."""
    profile = request.profile
    product_ids = request.selected_product_ids

    # 1. Verify existence of all requested product IDs
    for p_id in product_ids:
        if not catalogue_service.get_product_by_id(p_id):
            raise HTTPException(status_code=400, detail=f"Product '{p_id}' does not exist in catalogue.")

    # 2. Resolve dependencies
    try:
        resolved_ids, resolution_notes = eligibility_engine.resolve_dependencies(set(product_ids), profile)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Dependency resolution failure: {str(e)}")

    # 3. Server-side eligibility re-validation
    eligibility_issues = []
    is_fully_eligible = True

    for p_id in resolved_ids:
        prod = catalogue_service.get_product_by_id(p_id)
        if prod:
            eval_res = eligibility_engine.evaluate_product(prod, profile, resolved_ids)
            if eval_res.eligibility_status == EligibilityStatus.INELIGIBLE:
                is_fully_eligible = False
                eligibility_issues.extend(eval_res.reasons)
            elif eval_res.eligibility_status == EligibilityStatus.NEEDS_INFORMATION:
                eligibility_issues.extend(
                    [f"Verification required for '{prod.product_name}': {r}" for r in eval_res.reasons]
                )

    # 4. Calculate exact server-side pricing (ignoring any client-submitted prices)
    pricing = pricing_engine.calculate_price(
        list(resolved_ids), profile, request.quantity_overrides
    )

    max_install_days = max(
        [c.typical_install_days for c in pricing.contract_details], default=1
    )
    max_contract_months = max(
        [c.min_contract_months for c in pricing.contract_details], default=1
    )

    quote_id = f"Q-{uuid.uuid4().hex[:8].upper()}"

    terms = [
        "All pricing is computed server-side from verified Airtel / Accel Business catalogue rates.",
        f"Unique server-generated quote reference: {quote_id} (valid for 30 days).",
        f"Installation and fulfillment turnaround: estimated {max_install_days} business days.",
        f"Contract commitment: {max_contract_months} months minimum term.",
        "Monthly recurring charges (MRC) commence upon successful site activation.",
        "One-time setup charges (OTC) apply to the first billing invoice.",
        "Taxes (GST 18%) are not included in base catalogue figures and apply at checkout.",
    ]
    if resolution_notes:
        terms.extend(resolution_notes)

    return QuotePreviewResponse(
        quote_id=quote_id,
        business_segment=profile.get_normalized_segment(),
        bundle_tier=request.bundle_tier or "Custom",
        is_eligible=is_fully_eligible,
        eligibility_issues=eligibility_issues,
        pricing=pricing,
        typical_install_days=max_install_days,
        min_contract_months=max_contract_months,
        terms_and_conditions=terms,
    )

