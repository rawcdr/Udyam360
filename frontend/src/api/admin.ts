import { apiClient } from './client';

export interface OverviewKPIs {
  total_leads: number;
  contacted_leads: number;
  needs_assessed_leads: number;
  quote_accepted_leads: number;
  kyc_completed_leads: number;
  activated_leads: number;
  unconverted_leads: number;
  overall_conversion_rate_pct: number;
  benchmark_match: Record<string, boolean>;
}

export interface FunnelStage {
  stage_name: string;
  count: number;
  entered: number;
  dropped: number;
  stage_conversion_rate_pct: number;
  stage_drop_rate_pct: number;
  overall_conversion_pct: number;
}

export interface FunnelBottleneck {
  largest_volume_bottleneck: string;
  volume_lost: number;
  volume_drop_pct: number;
  highest_rate_bottleneck: string;
  highest_rate_lost: number;
  highest_rate_pct: number;
  explanation: string;
}

export interface FunnelAnalysis {
  total_leads: number;
  stages: FunnelStage[];
  primary_bottleneck: FunnelBottleneck;
}

export interface SegmentAnalysis {
  segment: string;
  total_leads: number;
  activated_leads: number;
  conversion_rate_pct: number;
  contacted_count: number;
  needs_assessed_count: number;
  quote_accepted_count: number;
  kyc_complete_count: number;
  share_of_total_leads_pct: number;
  share_of_activations_pct: number;
}

export interface LeadSourceAnalysis {
  lead_source: string;
  total_leads: number;
  activated_leads: number;
  conversion_rate_pct: number;
  share_of_total_pct: number;
  share_of_activations_pct: number;
}

export interface CityTierAnalysis {
  city_tier: string | number;
  total_leads: number;
  activated_leads: number;
  conversion_rate_pct: number;
}

export interface CityAnalysis {
  city: string;
  total_leads: number;
  activated_leads: number;
  conversion_rate_pct: number;
}

export interface GeographicAnalysis {
  by_tier: CityTierAnalysis[];
  top_cities: CityAnalysis[];
}

export interface FeatureImportance {
  feature: string;
  importance: number;
  coefficient?: number;
  odds_ratio?: number;
  pct_change_in_odds?: number;
  direction?: string;
  impact?: string;
  non_causal_note?: string;
}

export interface ModelInfo {
  model_name: string;
  model_version: string;
  phase?: string;
  trained_at: string;
  framework: string;
  dataset_shape: number[];
  target: string;
  class_distribution: {
    total: number;
    activated: number;
    dropped: number;
    activation_rate: number;
  };
  splits: {
    train_size: number;
    val_size: number;
    test_size: number;
    random_state: number;
    stratified: boolean;
  };
  prevalence?: {
    train: number;
    validation: number;
    test: number;
  };
  baseline_brier_score?: number;
  calibration_assessment?: Record<string, any>;
  feature_schema: {
    categorical_features: string[];
    numeric_features: string[];
    total_transformed_features: number;
  };
  evaluation: any;
  top_features: FeatureImportance[];
}

export interface EvaluationReport {
  comparison: Record<string, any>;
  selected_model: string;
  selection_rationale: string;
  prevalence?: {
    train: number;
    validation: number;
    test: number;
  };
  baseline_brier_score?: number;
  calibration_assessment?: Record<string, any>;
  held_out_test_metrics: Record<string, any>;
  feature_importance: FeatureImportance[];
}

export interface PropensityOverview {
  total_historical_leads?: number;
  activated_leads?: number;
  unconverted_leads?: number;
  total_unconverted_leads: number;
  eligible_leads_for_prioritization?: number;
  successfully_scored_leads?: number;
  excluded_leads_count?: number;
  excluded_leads_by_reason?: Record<string, number>;
  high_propensity_count: number;
  high_propensity_pct: number;
  medium_propensity_count: number;
  medium_propensity_pct: number;
  low_propensity_count: number;
  low_propensity_pct: number;
  thresholds: Record<string, number>;
  model_version: string;
  baseline_brier_score?: number;
  raw_brier_score?: number;
  calibrated_brier_score?: number;
  calibration_status?: string;
  calibration_notes?: string;
}

export interface ScoredLead {
  lead_id: string;
  business_name?: string;
  business_type?: string;
  segment: string;
  city: string;
  city_tier: number | string;
  lead_source: string;
  employee_count: number;
  num_sites: number;
  monthly_telecom_spend_inr: number;
  stage_reached: string;
  outcome: string;
  conversion_probability: number;
  propensity_score: number;
  propensity_band: 'HIGH' | 'MEDIUM' | 'LOW';
  recommended_next_action: string;
  positive_factors: string[];
  negative_factors: string[];
  business_summary?: string;
  actions_count?: number;
  is_eligible_for_sales_action?: boolean;
  exclusion_reason?: string | null;
}

export interface LeadPagination {
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  leads: ScoredLead[];
}

export interface SingleLeadScoreResult {
  lead_id: string;
  conversion_probability: number;
  propensity_score: number;
  propensity_band: string;
  current_stage: string;
  recommended_next_action: string;
  positive_factors: string[];
  negative_factors: string[];
  business_summary: string;
  model_version: string;
}

export interface SalesAction {
  lead_id: string;
  action_type: string;
  notes: string;
  rep_name: string;
  timestamp: string;
}

export interface LeadDetail extends ScoredLead {
  state?: string;
  annual_turnover_band?: string;
  has_gstin?: string;
  has_udyam?: string;
  current_internet?: string;
  current_provider?: string;
  products_of_interest?: string;
  contact_role?: string;
  model_version?: string;
  sales_action_history?: SalesAction[];
}

const ADMIN_CONFIG = {
  headers: {
    'X-Admin-Role': 'ExecutiveAdmin',
  },
};

export const adminApi = {
  async getOverviewKPIs(): Promise<OverviewKPIs> {
    const res = await apiClient.get('/admin/analytics/overview', ADMIN_CONFIG);
    return res.data;
  },

  async getFunnelAnalysis(): Promise<FunnelAnalysis> {
    const res = await apiClient.get('/admin/analytics/funnel', ADMIN_CONFIG);
    return res.data;
  },

  async getSegmentAnalysis(): Promise<SegmentAnalysis[]> {
    const res = await apiClient.get('/admin/analytics/segments', ADMIN_CONFIG);
    return res.data;
  },

  async getLeadSources(): Promise<LeadSourceAnalysis[]> {
    const res = await apiClient.get('/admin/analytics/sources', ADMIN_CONFIG);
    return res.data;
  },

  async getGeographicAnalysis(): Promise<GeographicAnalysis> {
    const res = await apiClient.get('/admin/analytics/geography', ADMIN_CONFIG);
    return res.data;
  },

  async getModelInfo(): Promise<ModelInfo> {
    const res = await apiClient.get('/admin/ml/model-info', ADMIN_CONFIG);
    return res.data;
  },

  async getModelEvaluation(): Promise<EvaluationReport> {
    const res = await apiClient.get('/admin/ml/evaluation', ADMIN_CONFIG);
    return res.data;
  },

  async getFeatureImportances(): Promise<FeatureImportance[]> {
    const res = await apiClient.get('/admin/ml/feature-importance', ADMIN_CONFIG);
    return res.data;
  },

  async getPropensityOverview(): Promise<PropensityOverview> {
    const res = await apiClient.get('/admin/ml/propensity-overview', ADMIN_CONFIG);
    return res.data;
  },

  async scoreSingleLead(leadDict: Record<string, any>): Promise<SingleLeadScoreResult> {
    const res = await apiClient.post('/admin/ml/score', { lead_dict: leadDict }, ADMIN_CONFIG);
    return res.data;
  },

  async getLeads(params?: {
    segment?: string;
    stage?: string;
    band?: string;
    search?: string;
    unconverted_only?: boolean;
    sort_by?: string;
    sort_order?: string;
    page?: number;
    page_size?: number;
  }): Promise<LeadPagination> {
    const res = await apiClient.get('/admin/ml/leads', {
      params,
      ...ADMIN_CONFIG,
    });
    return res.data;
  },

  async getLeadDetail(leadId: string): Promise<LeadDetail> {
    const res = await apiClient.get(`/admin/leads/${leadId}`, ADMIN_CONFIG);
    return res.data;
  },

  async recordSalesAction(leadId: string, actionType: string, notes: string, repName?: string): Promise<SalesAction> {
    const res = await apiClient.post(
      `/admin/leads/${leadId}/action`,
      {
        action_type: actionType,
        notes,
        rep_name: repName || 'Executive Sales Rep',
      },
      ADMIN_CONFIG
    );
    return res.data;
  },

  async getKYCExceptions(status?: string): Promise<KYCExceptionCase[]> {
    const res = await apiClient.get('/admin/kyc/exceptions', {
      params: status ? { status } : undefined,
      ...ADMIN_CONFIG,
    });
    return res.data;
  },

  async getKYCExceptionDetail(caseId: string): Promise<KYCExceptionCase> {
    const res = await apiClient.get(`/admin/kyc/exceptions/${caseId}`, ADMIN_CONFIG);
    return res.data;
  },

  async resolveKYCException(
    caseId: string,
    action: string,
    notes: string,
    officerName?: string
  ): Promise<KYCExceptionResolution> {
    const res = await apiClient.post(
      `/admin/kyc/exceptions/${caseId}/resolve`,
      {
        action,
        notes,
        officer_name: officerName || 'Senior KYC Compliance Officer',
      },
      ADMIN_CONFIG
    );
    return res.data;
  },
};

export interface KYCExceptionCrossCheck {
  check_name: string;
  status: 'MATCH' | 'MINOR_VARIATION' | 'MISMATCH' | string;
  detail: string;
}

export interface KYCExceptionCase {
  case_id: string;
  customer_name: string;
  business_name: string;
  trade_name: string;
  legal_name: string;
  city: string;
  segment: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  confidence_score: number;
  flag_reason: string;
  status: 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED' | 'INFO_REQUESTED';
  created_at: string;
  reviewed_at?: string;
  reviewed_by?: string;
  review_notes?: string;
  entity_structure: string;
  cross_checks: KYCExceptionCrossCheck[];
  copilot_analysis: string;
  copilot_recommendation: string;
  order_reference?: string;
}

export interface KYCExceptionResolution {
  case_id: string;
  status: string;
  action_taken: string;
  reviewed_by: string;
  reviewed_at: string;
  notes: string;
  order_reference?: string;
  order_status?: string;
}


