"""Pydantic schemas for Executive Admin Dashboard, Analytics, and ML Propensity."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ==========================================
# Analytics Schemas
# ==========================================

class OverviewKPIResponse(BaseModel):
    total_leads: int
    contacted_leads: int
    needs_assessed_leads: int
    quote_accepted_leads: int
    kyc_completed_leads: int
    activated_leads: int
    unconverted_leads: int
    overall_conversion_rate_pct: float
    benchmark_match: Dict[str, bool]


class FunnelStageItem(BaseModel):
    stage_name: str
    count: int
    entered: int
    dropped: int
    stage_conversion_rate_pct: float
    stage_drop_rate_pct: float
    overall_conversion_pct: float


class FunnelBottleneckDetail(BaseModel):
    largest_volume_bottleneck: str
    volume_lost: int
    volume_drop_pct: float
    highest_rate_bottleneck: str
    highest_rate_lost: int
    highest_rate_pct: float
    explanation: str


class FunnelAnalysisResponse(BaseModel):
    total_leads: int
    stages: List[FunnelStageItem]
    primary_bottleneck: FunnelBottleneckDetail


class SegmentAnalysisItem(BaseModel):
    segment: str
    total_leads: int
    activated_leads: int
    conversion_rate_pct: float
    contacted_count: int
    needs_assessed_count: int
    quote_accepted_count: int
    kyc_complete_count: int
    share_of_total_leads_pct: float
    share_of_activations_pct: float


class LeadSourceAnalysisItem(BaseModel):
    lead_source: str
    total_leads: int
    activated_leads: int
    conversion_rate_pct: float
    share_of_total_pct: float
    share_of_activations_pct: float


class CityTierAnalysisItem(BaseModel):
    city_tier: str
    total_leads: int
    activated_leads: int
    conversion_rate_pct: float


class CityAnalysisItem(BaseModel):
    city: str
    total_leads: int
    activated_leads: int
    conversion_rate_pct: float


class GeographicAnalysisResponse(BaseModel):
    by_tier: List[CityTierAnalysisItem]
    top_cities: List[CityAnalysisItem]


# ==========================================
# ML Propensity Schemas
# ==========================================

class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float
    coefficient: Optional[float] = None
    odds_ratio: Optional[float] = None
    pct_change_in_odds: Optional[float] = None
    direction: Optional[str] = None
    impact: Optional[str] = None
    non_causal_note: Optional[str] = None


class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    phase: Optional[str] = None
    trained_at: str
    framework: str
    dataset_shape: List[int]
    target: str
    class_distribution: Dict[str, Any]
    splits: Dict[str, Any]
    prevalence: Optional[Dict[str, float]] = None
    baseline_brier_score: Optional[float] = None
    calibration_assessment: Optional[Dict[str, Any]] = None
    feature_schema: Dict[str, Any]
    evaluation: Dict[str, Any]
    top_features: List[FeatureImportanceItem]


class EvaluationReportResponse(BaseModel):
    comparison: Dict[str, Any]
    selected_model: str
    selection_rationale: str
    prevalence: Optional[Dict[str, float]] = None
    baseline_brier_score: Optional[float] = None
    calibration_assessment: Optional[Dict[str, Any]] = None
    held_out_test_metrics: Dict[str, Any]
    feature_importance: List[FeatureImportanceItem]


class PropensityOverviewResponse(BaseModel):
    total_historical_leads: int = 5000
    activated_leads: int = 368
    unconverted_leads: int = 4632
    total_unconverted_leads: int = 4632
    eligible_leads_for_prioritization: int = 4632
    successfully_scored_leads: int = 4632
    excluded_leads_count: int = 368
    excluded_leads_by_reason: Dict[str, int] = Field(default_factory=dict)
    high_propensity_count: int
    high_propensity_pct: float
    medium_propensity_count: int
    medium_propensity_pct: float
    low_propensity_count: int
    low_propensity_pct: float
    thresholds: Dict[str, float]
    model_version: str
    baseline_brier_score: float = 0.068
    raw_brier_score: float = 0.2136
    calibrated_brier_score: float = 0.0666
    calibration_status: str = "CALIBRATED_PLATT_SCALING"
    calibration_notes: str = ""


class ScoredLeadSummary(BaseModel):
    lead_id: str
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    segment: str
    city: str
    city_tier: int
    lead_source: str
    employee_count: int
    num_sites: int
    monthly_telecom_spend_inr: int
    stage_reached: str
    outcome: str
    conversion_probability: float
    propensity_score: float
    propensity_band: str
    recommended_next_action: str
    positive_factors: List[str] = Field(default_factory=list)
    negative_factors: List[str] = Field(default_factory=list)
    business_summary: Optional[str] = None
    actions_count: int = 0
    is_eligible_for_sales_action: bool = True
    exclusion_reason: Optional[str] = None


class LeadPaginationResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    leads: List[ScoredLeadSummary]


class SingleLeadScoreRequest(BaseModel):
    lead_dict: Dict[str, Any]


class SingleLeadScoreResponse(BaseModel):
    lead_id: str
    conversion_probability: float
    propensity_score: float
    propensity_band: str
    current_stage: str
    recommended_next_action: str
    positive_factors: List[str]
    negative_factors: List[str]
    business_summary: str
    model_version: str


# ==========================================
# Sales Action Schemas
# ==========================================

class SalesActionRequest(BaseModel):
    action_type: str = Field(..., description="e.g. Call, Meeting, Email, Offer Sent")
    notes: str = Field(..., min_length=3, description="Sales follow-up notes")
    rep_name: Optional[str] = "Executive Sales Rep"


class SalesActionResponse(BaseModel):
    lead_id: str
    action_type: str
    notes: str
    rep_name: str
    timestamp: str


# ==========================================
# Smart KYC Exception Copilot Schemas
# ==========================================

class KYCExceptionCrossCheck(BaseModel):
    check_name: str
    status: str
    detail: str


class KYCExceptionCase(BaseModel):
    case_id: str
    customer_name: str
    business_name: str
    trade_name: str
    legal_name: str
    city: str
    segment: str
    risk_level: str
    confidence_score: float
    flag_reason: str
    status: str
    created_at: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    entity_structure: str
    cross_checks: List[KYCExceptionCrossCheck]
    copilot_analysis: str
    copilot_recommendation: str
    order_reference: Optional[str] = None


class KYCExceptionResolutionRequest(BaseModel):
    action: str = Field(..., description="APPROVE, REJECT, REQUEST_REUPLOAD")
    notes: str = Field(..., min_length=2, description="KYC compliance officer notes")
    officer_name: Optional[str] = "KYC Operations Officer"


class KYCExceptionResolutionResponse(BaseModel):
    case_id: str
    status: str
    action_taken: str
    reviewed_by: str
    reviewed_at: str
    notes: str
    order_reference: Optional[str] = None
    order_status: Optional[str] = None

