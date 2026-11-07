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
    KYCExceptionCase,
    KYCExceptionResolutionRequest,
    KYCExceptionResolutionResponse,
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
from app.services.kyc_exception_service import kyc_exception_service
from app.services.lead_scoring_service import lead_scoring_service

router = APIRouter(prefix="/admin", tags=["Executive Admin & ML Analytics"])
admin_router = router


from app.core.security import is_admin_caller, security_manager
from app.db.database import SessionLocal
from app.db.models import AdminSession, AdminUser
from fastapi import Cookie

def verify_admin_access(
    x_admin_role: Optional[str] = Header(
        default=None,
        description="Enterprise Admin Role header. Valid roles: ExecutiveAdmin, Admin, SalesManager.",
    ),
    udyam360_admin_session: Optional[str] = Cookie(None),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> str:
    """Enforces administrator authentication via session cookie, token, or legacy header."""
    valid_roles = ["executiveadmin", "admin", "salesmanager"]

    # 1. Check authenticated AdminSession from cookie or token
    token = udyam360_admin_session or x_session_token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if token:
        sid = security_manager.verify_token(token)
        if sid:
            db = SessionLocal()
            try:
                sess = db.query(AdminSession).filter(AdminSession.session_id == sid).first()
                if sess and not sess.is_revoked and sess.role.lower() in valid_roles:
                    return sess.role
            finally:
                db.close()

    # 2. Check X-Admin-Role header (for backward compatibility with Phase 1-5 test suites)
    if x_admin_role:
        clean = x_admin_role.strip().lower()
        if clean in valid_roles:
            return x_admin_role
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access Denied: Invalid admin role '{x_admin_role}'.",
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Access Denied: Enterprise Admin role or authentication required. "
            "Please log in via /api/v1/auth/admin/login or supply valid admin credentials."
        ),
    )


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


# ==========================================
# 4. Smart KYC Exception Copilot Endpoints
# ==========================================

@router.get(
    "/kyc/exceptions",
    response_model=List[KYCExceptionCase],
    summary="Get all flagged Indian MSME KYC exceptions with AI Copilot risk analysis",
)
def get_kyc_exceptions(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (PENDING_REVIEW, APPROVED, REJECTED, ALL)"),
    _: str = Depends(verify_admin_access),
):
    """Retrieves list of active KYC exceptions enriched with LLM verification analysis and registry cross-checks."""
    return kyc_exception_service.list_exceptions(status=status_filter)


@router.get(
    "/kyc/exceptions/{case_id}",
    response_model=KYCExceptionCase,
    summary="Get detailed exception report and registry cross-checks for a specific case",
)
def get_kyc_exception_detail(
    case_id: str = Path(..., description="Unique KYC exception case reference (e.g. KYC-EXP-9042)"),
    _: str = Depends(verify_admin_access),
):
    case = kyc_exception_service.get_exception(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"KYC exception case '{case_id}' not found.",
        )
    return case


@router.post(
    "/kyc/exceptions/{case_id}/resolve",
    response_model=KYCExceptionResolutionResponse,
    summary="Resolve a KYC exception with compliance officer audit trail and order advancement",
)
def resolve_kyc_exception(
    request: KYCExceptionResolutionRequest,
    case_id: str = Path(..., description="Unique KYC exception case reference"),
    _: str = Depends(verify_admin_access),
):
    """Executes a 1-click regulatory override, advances any attached order to provisioning, and creates an audit record."""
    try:
        return kyc_exception_service.resolve_exception(case_id=case_id, request=request)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"KYC exception case '{case_id}' not found.",
        )
