import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AdminOverviewPage } from '../pages/admin/AdminOverviewPage';
import { AdminLeadsPage } from '../pages/admin/AdminLeadsPage';
import { AdminModelPage } from '../pages/admin/AdminModelPage';
import { adminApi } from '../api/admin';

// Mock Recharts ResponsiveContainer to avoid jsdom zero width/height issues
vi.mock('recharts', async () => {
  const original = await vi.importActual<any>('recharts');
  return {
    ...original,
    ResponsiveContainer: ({ children }: any) => (
      <div style={{ width: 800, height: 400 }}>{children}</div>
    ),
  };
});

describe('Executive Admin Dashboard & ML Propensity Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders executive overview headline KPIs and bottleneck diagnostics', async () => {
    vi.spyOn(adminApi, 'getOverviewKPIs').mockResolvedValue({
      total_leads: 5000,
      contacted_leads: 3406,
      needs_assessed_leads: 1974,
      quote_accepted_leads: 861,
      kyc_completed_leads: 588,
      activated_leads: 368,
      unconverted_leads: 4632,
      overall_conversion_rate_pct: 7.36,
      benchmark_match: { total_leads_match: true, activated_match: true },
    });

    vi.spyOn(adminApi, 'getFunnelAnalysis').mockResolvedValue({
      total_leads: 5000,
      stages: [
        {
          stage_name: 'Lead Intake',
          count: 5000,
          entered: 5000,
          dropped: 0,
          stage_conversion_rate_pct: 100,
          stage_drop_rate_pct: 0,
          overall_conversion_pct: 100,
        },
        {
          stage_name: 'Contacted',
          count: 3406,
          entered: 5000,
          dropped: 1594,
          stage_conversion_rate_pct: 68.12,
          stage_drop_rate_pct: 31.88,
          overall_conversion_pct: 68.12,
        },
      ],
      primary_bottleneck: {
        largest_volume_bottleneck: 'Lead Intake -> Contacted',
        volume_lost: 1594,
        volume_drop_pct: 31.88,
        highest_rate_bottleneck: 'Needs Assessed -> Quote Accepted',
        highest_rate_lost: 1113,
        highest_rate_pct: 56.38,
        explanation: 'Highest drop occurs at needs assessment and quote acceptance.',
      },
    });

    vi.spyOn(adminApi, 'getSegmentAnalysis').mockResolvedValue([
      {
        segment: 'Small manufacturers',
        total_leads: 1000,
        activated_leads: 128,
        conversion_rate_pct: 12.8,
        contacted_count: 800,
        needs_assessed_count: 500,
        quote_accepted_count: 300,
        kyc_complete_count: 200,
        share_of_total_leads_pct: 20,
        share_of_activations_pct: 34.78,
      },
    ]);

    vi.spyOn(adminApi, 'getLeadSources').mockResolvedValue([
      {
        lead_source: 'Referral',
        total_leads: 500,
        activated_leads: 74,
        conversion_rate_pct: 14.77,
        share_of_total_pct: 10,
        share_of_activations_pct: 20.1,
      },
    ]);

    vi.spyOn(adminApi, 'getGeographicAnalysis').mockResolvedValue({
      by_tier: [
        { city_tier: 1, total_leads: 2000, activated_leads: 180, conversion_rate_pct: 9.0 },
      ],
      top_cities: [
        { city: 'Bengaluru', total_leads: 800, activated_leads: 80, conversion_rate_pct: 10.0 },
      ],
    });

    render(
      <BrowserRouter>
        <AdminOverviewPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('5,000').length).toBeGreaterThan(0);
      expect(screen.getAllByText('368').length).toBeGreaterThan(0);
      expect(screen.getByText(/7.36% Overall Conv/i)).toBeInTheDocument();
      expect(screen.getByText(/Primary Bottleneck Alert:/i)).toBeInTheDocument();
    });
  });

  it('renders lead management table with propensity badges and eligible lead filters', async () => {
    vi.spyOn(adminApi, 'getPropensityOverview').mockResolvedValue({
      total_historical_leads: 5000,
      activated_leads: 368,
      unconverted_leads: 4632,
      total_unconverted_leads: 4632,
      eligible_leads_for_prioritization: 4632,
      successfully_scored_leads: 4632,
      excluded_leads_count: 368,
      excluded_leads_by_reason: { ALREADY_ACTIVATED: 368 },
      high_propensity_count: 569,
      high_propensity_pct: 12.28,
      medium_propensity_count: 1564,
      medium_propensity_pct: 33.77,
      low_propensity_count: 2499,
      low_propensity_pct: 53.95,
      thresholds: { high: 0.7, medium: 0.4 },
      model_version: '1.1.0',
      baseline_brier_score: 0.068,
      raw_brier_score: 0.2136,
      calibrated_brier_score: 0.0666,
      calibration_status: 'CALIBRATED_PLATT_SCALING',
    });

    vi.spyOn(adminApi, 'getLeads').mockResolvedValue({
      total_count: 1,
      page: 1,
      page_size: 15,
      total_pages: 1,
      leads: [
        {
          lead_id: 'L00001',
          business_name: 'Apex CA Consultancy',
          business_type: 'CA Practice',
          segment: 'Professional offices',
          city: 'Bengaluru',
          city_tier: 1,
          lead_source: 'Referral',
          employee_count: 8,
          num_sites: 1,
          monthly_telecom_spend_inr: 6500,
          stage_reached: 'Needs assessed',
          outcome: 'Needs assessed',
          conversion_probability: 0.784,
          propensity_score: 78.4,
          propensity_band: 'HIGH',
          recommended_next_action: 'Present tailored product quote.',
          positive_factors: ['Referred by existing partner (+166% conversion odds, OR 2.66)'],
          negative_factors: [],
          is_eligible_for_sales_action: true,
          exclusion_reason: null,
        },
      ],
    });

    render(
      <BrowserRouter>
        <AdminLeadsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Apex CA Consultancy')).toBeInTheDocument();
      expect(screen.getByText('78.4%')).toBeInTheDocument();
      expect(screen.getByText('HIGH')).toBeInTheDocument();
      expect(screen.getAllByText(/569/).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/Deterministic Lead Filter Active:/i)).toBeInTheDocument();
    });
  });

  it('renders ML model architecture, calibration audit, and candidate benchmark comparison', async () => {
    vi.spyOn(adminApi, 'getModelInfo').mockResolvedValue({
      model_name: 'LogisticRegression',
      model_version: '1.1.0',
      trained_at: '2026-11-05T18:42:25Z',
      framework: 'scikit-learn',
      dataset_shape: [5000, 40],
      target: "outcome == 'Activated'",
      class_distribution: { total: 5000, activated: 368, dropped: 4632, activation_rate: 0.0736 },
      splits: { train_size: 3500, val_size: 750, test_size: 750, random_state: 42, stratified: true },
      prevalence: { train: 0.0737, validation: 0.0733, test: 0.0733 },
      baseline_brier_score: 0.068,
      calibration_assessment: {
        baseline_brier_score: 0.068,
        raw_model: { test_brier: 0.2136 },
        calibrated_model: { test_brier: 0.0666 },
      },
      feature_schema: { categorical_features: [], numeric_features: [], total_transformed_features: 128 },
      evaluation: {},
      top_features: [],
    });

    vi.spyOn(adminApi, 'getModelEvaluation').mockResolvedValue({
      selected_model: 'LogisticRegression',
      selection_rationale: 'Highest test ROC-AUC (0.6692) & PR-AUC with 100% linear odds interpretability.',
      prevalence: { train: 0.0737, validation: 0.0733, test: 0.0733 },
      baseline_brier_score: 0.068,
      calibration_assessment: {
        baseline_brier_score: 0.068,
        raw_model: { test_brier: 0.2136 },
        calibrated_model: { test_brier: 0.0666 },
      },
      comparison: {
        LogisticRegression: {
          validation: { roc_auc: 0.6974 },
          test: { roc_auc: 0.6692, pr_auc: 0.1327, brier_score: 0.2136 },
        },
        RandomForest: {
          validation: { roc_auc: 0.6819 },
          test: { roc_auc: 0.6526, pr_auc: 0.1133, brier_score: 0.1758 },
        },
        HistGradientBoosting: {
          validation: { roc_auc: 0.6371 },
          test: { roc_auc: 0.6023, pr_auc: 0.1100, brier_score: 0.1143 },
        },
      },
      held_out_test_metrics: { roc_auc: 0.6692 },
      feature_importance: [
        {
          feature: 'lead_source_Referral',
          importance: 0.9774,
          coefficient: 0.9774,
          odds_ratio: 2.6575,
          pct_change_in_odds: 165.75,
          direction: 'POSITIVE',
          impact: 'POSITIVE',
          non_causal_note: 'Statistical association; does not demonstrate causal effect.',
        },
      ],
    });

    vi.spyOn(adminApi, 'getFeatureImportances').mockResolvedValue([
      {
        feature: 'lead_source_Referral',
        importance: 0.9774,
        coefficient: 0.9774,
        odds_ratio: 2.6575,
        pct_change_in_odds: 165.75,
        direction: 'POSITIVE',
        impact: 'POSITIVE',
        non_causal_note: 'Statistical association; does not demonstrate causal effect.',
      },
    ]);

    render(
      <BrowserRouter>
        <AdminModelPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText(/LogisticRegression/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('Winner: Logistic Regression')).toBeInTheDocument();
      expect(screen.getByText(/Probability Calibration & Brier Baseline Audit/i)).toBeInTheDocument();
      expect(screen.getByText(/Platt Calibrated Brier/i)).toBeInTheDocument();
      expect(screen.getByText(/Non-Causal Interpretability Notice:/i)).toBeInTheDocument();
      expect(screen.getByText('Live Propensity Scoring Sandbox')).toBeInTheDocument();
    });
  });
});
