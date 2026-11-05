"""FastAPI router for Executive Admin Dashboard, Funnel Analytics, and ML Lead Propensity.

Includes prototype-level role verification guard to prevent unrestricted public exposure.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, status

from app.ml.inference import lead_propensity_inference
from app.ml.model_registry import model_registry
from app.schemas.admin import (
    EvaluationReportResponse,
    FeatureImportanceItem,
    FunnelAnalysisResponse,
    GeographicAnalysisResponse,
    LeadPaginationResponse,
    LeadSourceAnalysisItem,
    ModelInfoResponse,
    OverviewKPIResponse,
    PropensityOverviewResponse,
    SalesActionRequest,
    SalesActionResponse,
    SegmentAnalysisItem,
    SingleLeadScoreRequest,
    SingleLeadScoreResponse,
)
from app.services.analytics_service import analytics_service
from app.services.lead_scoring_service import lead_scoring_service

router = APIRouter(prefix="/admin", tags=["Executive Admin & ML Analytics"])
admin_router = router


def verify_admin_access(
    x_admin_role: Optional[str] = Header(
        default="ExecutiveAdmin",
        description="Prototype Admin Role header. Valid roles: ExecutiveAdmin, Admin, SalesManager.",
    ),
) -> str:
    """Prototype access guard. Enforces admin role header while avoiding hardcoded secrets."""
    valid_roles = ["executiveadmin", "admin", "salesmanager"]
    if not x_admin_role or x_admin_role.strip().lower() not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Access Denied: Enterprise Admin role header required. "
                "Supply 'X-Admin-Role: ExecutiveAdmin' to access internal sales intelligence."
            ),
        )
    return x_admin_role


# ==========================================
# 1. Analytics Endpoints
# ==========================================

@router.get(
    "/analytics/overview",
    response_model=OverviewKPIResponse,
    summary="Get executive headline KPI cards",
)
def get_analytics_overview(_: str = Depends(verify_admin_access)):
    """Computes total leads, funnel volumes, activations, and benchmark comparisons from data."""
    try:
        return analytics_service.get_overview_kpis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics calculation error: {str(e)}")


@router.get(
    "/analytics/funnel",
    response_model=FunnelAnalysisResponse,
    summary="Get complete stage progression & drop-off analysis",
)
def get_funnel_analysis(_: str = Depends(verify_admin_access)):
    """Computes 6-stage funnel conversion percentages and diagnoses the primary bottleneck."""
    try:
        return analytics_service.get_funnel_analysis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Funnel analysis error: {str(e)}")


@router.get(
    "/analytics/segments",
    response_model=List[SegmentAnalysisItem],
    summary="Get segment-level volume & activation rates",
)
def get_segment_analysis(_: str = Depends(verify_admin_access)):
    """Returns actual lead and activation distributions across MSME segments."""
    try:
        return analytics_service.get_segment_analysis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Segment analysis error: {str(e)}")


@router.get(
    "/analytics/sources",
    response_model=List[LeadSourceAnalysisItem],
    summary="Get lead acquisition channel performance",
)
def get_lead_sources(_: str = Depends(verify_admin_access)):
    """Returns conversion rates and activation shares across all 6 marketing/sales channels."""
    try:
        return analytics_service.get_lead_sources_analysis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Source analysis error: {str(e)}")


@router.get(
    "/analytics/geography",
    response_model=GeographicAnalysisResponse,
    summary="Get geographic and city-tier distribution",
)
def get_geography(_: str = Depends(verify_admin_access)):
    """Returns lead volume and conversion metrics by city tier and top MSME hubs."""
    try:
        return analytics_service.get_geographic_analysis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geographic analysis error: {str(e)}")


# ==========================================
# 2. ML Propensity Endpoints
# ==========================================

@router.get(
    "/ml/model-info",
    response_model=ModelInfoResponse,
    summary="Get ML model metadata and training parameters",
)
def get_model_info(_: str = Depends(verify_admin_access)):
    """Retrieves selected model architecture, version, class balance, and feature schema."""
    metadata = model_registry.get_metadata()
    if not metadata or metadata.get("status") == "NOT_TRAINED":
        raise HTTPException(status_code=404, detail="Model metadata not yet generated.")
    return metadata


@router.get(
    "/ml/evaluation",
    response_model=EvaluationReportResponse,
    summary="Get candidate model benchmarks and held-out test evaluation",
)
def get_model_evaluation(_: str = Depends(verify_admin_access)):
    """Returns ROC-AUC, PR-AUC, Brier score, and calibration metrics across all candidate models."""
    eval_report = model_registry.get_evaluation_report()
    if not eval_report or not eval_report.get("comparison"):
        raise HTTPException(status_code=404, detail="Evaluation report not available.")
    return eval_report


@router.get(
    "/ml/feature-importance",
    response_model=List[FeatureImportanceItem],
    summary="Get global feature importance ranking",
)
def get_feature_importances(_: str = Depends(verify_admin_access)):
    """Returns ranked feature weights and odds impacts."""
    return model_registry.get_feature_importances()


@router.get(
    "/ml/propensity-overview",
    response_model=PropensityOverviewResponse,
    summary="Get aggregate distribution of lead propensity bands",
)
def get_propensity_overview(_: str = Depends(verify_admin_access)):
    """Returns breakdown of High, Medium, and Low propensity leads for unconverted accounts."""
    return lead_scoring_service.get_propensity_overview()


@router.post(
    "/ml/score",
    response_model=SingleLeadScoreResponse,
    summary="Score a single lead dictionary in real time",
)
def score_lead(
    request: SingleLeadScoreRequest,
    _: str = Depends(verify_admin_access),
):
    """Calculates propensity score and positive/negative drivers for an arbitrary lead profile."""
    try:
        return lead_propensity_inference.score_single_lead(request.lead_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Scoring error: {str(e)}")


@router.get(
    "/ml/leads",
    response_model=LeadPaginationResponse,
    summary="Get searchable, filterable, and ranked lead management table",
)
def get_leads_table(
    segment: Optional[str] = Query(None, description="Filter by business segment"),
    stage: Optional[str] = Query(None, description="Filter by stage reached"),
    band: Optional[str] = Query(None, description="Filter by propensity band (HIGH, MEDIUM, LOW)"),
    search: Optional[str] = Query(None, description="Search lead ID, business name, or city"),
    unconverted_only: bool = Query(True, description="Filter to unconverted leads only"),
    sort_by: str = Query("propensity_score", description="Sort column"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    _: str = Depends(verify_admin_access),
):
    """Returns paginated, prioritized leads enriched with ML propensity scores and next actions."""
    try:
        return lead_scoring_service.get_leads_paginated(
            segment=segment,
            stage=stage,
            band=band,
            search=search,
            unconverted_only=unconverted_only,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lead query error: {str(e)}")


# ==========================================
# 3. Individual Lead Details & Sales Actions
# ==========================================

@router.get(
    "/leads/{lead_id}",
    summary="Get full profile and propensity details for a lead",
)
def get_lead_details(
    lead_id: str = Path(..., description="Unique lead identifier (e.g. L00001)"),
    _: str = Depends(verify_admin_access),
):
    """Retrieves full lead details, positive/negative drivers, and audit interaction history."""
    detail = lead_scoring_service.get_lead_detail(lead_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID '{lead_id}' not found in dataset.",
        )
    return detail


@router.get(
    "/leads/{lead_id}/propensity",
    response_model=SingleLeadScoreResponse,
    summary="Get dedicated propensity score card for a lead",
)
def get_lead_propensity_card(
    lead_id: str = Path(..., description="Unique lead identifier"),
    _: str = Depends(verify_admin_access),
):
    """Returns propensity score, band, drivers, and operational next action."""
    detail = lead_scoring_service.get_lead_detail(lead_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID '{lead_id}' not found.",
        )
    return {
        "lead_id": detail["lead_id"],
        "conversion_probability": detail["conversion_probability"],
        "propensity_score": detail["propensity_score"],
        "propensity_band": detail["propensity_band"],
        "current_stage": detail["stage_reached"],
        "recommended_next_action": detail["recommended_next_action"],
        "positive_factors": detail["positive_factors"],
        "negative_factors": detail["negative_factors"],
        "business_summary": detail["business_summary"],
        "model_version": detail["model_version"],
    }


@router.post(
    "/leads/{lead_id}/action",
    response_model=SalesActionResponse,
    summary="Log sales follow-up interaction note (Part 6)",
)
def log_sales_action(
    request: SalesActionRequest,
    lead_id: str = Path(..., description="Unique lead identifier"),
    _: str = Depends(verify_admin_access),
):
    """Records a sales interaction note in memory without modifying the original dataset."""
    try:
        return lead_scoring_service.record_sales_action(
            lead_id=lead_id,
            action_type=request.action_type,
            notes=request.notes,
            rep_name=request.rep_name or "Executive Sales Rep",
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead '{lead_id}' not found.",
        )
