import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { RecommendationsPage } from '../pages/RecommendationsPage';
import { QuotePage } from '../pages/QuotePage';
import { OnboardingProvider } from '../context/OnboardingContext';
import { recommendationApi } from '../api/recommendations';
import { catalogueApi } from '../api/catalogue';
import { quoteApi } from '../api/quotes';

vi.mock('../api/recommendations', () => ({
  recommendationApi: {
    getRecommendations: vi.fn(),
  },
}));

vi.mock('../api/catalogue', () => ({
  catalogueApi: {
    getAll: vi.fn(),
  },
}));

vi.mock('../api/quotes', () => ({
  quoteApi: {
    previewQuote: vi.fn(),
  },
}));

const mockRecommendationsResponse = {
  profile_summary: {
    segment: 'micro',
    sites_count: 1,
    num_employees: 4,
    city: 'Chennai',
    monthly_budget: 4000,
    gstin_declared: false,
  },
  essential_bundle: {
    tier: 'Essential',
    bundle_name: 'Micro Starter Connectivity',
    target_profile_summary: 'Cost-optimized connectivity',
    monthly_price_min: 999,
    monthly_price_max: 999,
    one_time_setup_total: 500,
    within_budget: true,
    budget_status: 'WITHIN_BUDGET',
    budget_fit_score: 1.0,
    suitability_score: 0.8,
    composite_score: 0.9,
    product_ids: ['P01'],
    included_products: [
      {
        product_id: 'P01',
        product_name: 'Airtel Business Broadband 100M',
        category: 'Connectivity',
        monthly_price_min: 999,
        monthly_price_max: 999,
        one_time_setup_fee: 500,
        pricing_unit: 'connection',
        relevance_reason: 'Core business broadband',
      },
    ],
    explanation: {
      bundle_name: 'Micro Starter Connectivity',
      tier: 'Essential',
      monthly_price_min: 999,
      monthly_price_max: 999,
      budget_status: 'WITHIN_BUDGET',
      budget_fit_text: 'Well within ₹4,000 monthly budget.',
      operational_rationale: 'Provides core baseline connectivity.',
      key_advantages: ['Low cost', 'No GSTIN mandatory'],
      missing_prerequisites: [],
      risk_warnings: [],
    },
    recommended_addons: ['P03'],
  },
  growth_bundle: {
    tier: 'Growth',
    bundle_name: 'Micro Retail Complete Growth',
    target_profile_summary: 'Broadband with POS failover',
    monthly_price_min: 1999,
    monthly_price_max: 1999,
    one_time_setup_total: 1000,
    within_budget: true,
    budget_status: 'WITHIN_BUDGET',
    budget_fit_score: 0.95,
    suitability_score: 0.95,
    composite_score: 0.95,
    product_ids: ['P01', 'P03'],
    included_products: [
      {
        product_id: 'P01',
        product_name: 'Airtel Business Broadband 100M',
        category: 'Connectivity',
        monthly_price_min: 999,
        monthly_price_max: 999,
        one_time_setup_fee: 500,
        pricing_unit: 'connection',
        relevance_reason: 'High-speed broadband',
      },
      {
        product_id: 'P03',
        product_name: '4G POS Backup Wireless',
        category: 'Connectivity',
        monthly_price_min: 1000,
        monthly_price_max: 1000,
        one_time_setup_fee: 500,
        pricing_unit: 'connection',
        relevance_reason: 'Uninterrupted digital payments',
      },
    ],
    explanation: {
      bundle_name: 'Micro Retail Complete Growth',
      tier: 'Growth',
      monthly_price_min: 1999,
      monthly_price_max: 1999,
      budget_status: 'WITHIN_BUDGET',
      budget_fit_text: 'Leaves ₹2,001 monthly cushion.',
      operational_rationale: 'Balanced solution with POS payment protection.',
      key_advantages: ['POS uptime guarantee', 'Dual path failover'],
      missing_prerequisites: [],
      risk_warnings: [],
    },
    recommended_addons: [],
  },
  premium_bundle: {
    tier: 'Premium',
    bundle_name: 'Enterprise Grade MSME Suite',
    target_profile_summary: 'Full connectivity, calling & cloud CCTV',
    monthly_price_min: 3499,
    monthly_price_max: 3499,
    one_time_setup_total: 2500,
    within_budget: true,
    budget_status: 'WITHIN_BUDGET',
    budget_fit_score: 0.85,
    suitability_score: 1.0,
    composite_score: 0.92,
    product_ids: ['P01', 'P03', 'P14'],
    included_products: [],
    explanation: {
      bundle_name: 'Enterprise Grade MSME Suite',
      tier: 'Premium',
      monthly_price_min: 3499,
      monthly_price_max: 3499,
      budget_status: 'WITHIN_BUDGET',
      budget_fit_text: 'Comprehensive business package.',
      operational_rationale: 'Maximum reliability and security.',
      key_advantages: ['Cloud CCTV', 'Business Voice'],
      missing_prerequisites: [],
      risk_warnings: [],
    },
    recommended_addons: [],
  },
  catalog_version: '2026.1',
  generated_at: '2026-11-05T12:00:00Z',
};

const mockQuoteResponse = {
  quote_id: 'Q-TEST9988',
  business_segment: 'micro',
  bundle_tier: 'Growth',
  is_eligible: true,
  eligibility_issues: [],
  pricing: {
    monthly_recurring_charges: 1999.0,
    one_time_charges: 1000.0,
    estimated_first_month_payable: 2999.0,
    currency: 'INR',
    itemized_breakdown: [
      {
        product_id: 'P01',
        product_name: 'Airtel Business Broadband 100M',
        category: 'Connectivity',
        unit_price: 999.0,
        quantity: 1,
        pricing_unit: 'connection',
        monthly_subtotal: 999.0,
        one_time_setup_fee: 500.0,
      },
      {
        product_id: 'P03',
        product_name: '4G POS Backup Wireless',
        category: 'Connectivity',
        unit_price: 1000.0,
        quantity: 1,
        pricing_unit: 'connection',
        monthly_subtotal: 1000.0,
        one_time_setup_fee: 500.0,
      },
    ],
  },
  typical_install_days: 3,
  min_contract_months: 12,
  terms_and_conditions: [
    'All pricing is computed server-side.',
    'Quote reference: Q-TEST9988.',
    'Taxes (GST 18%) apply at checkout.',
  ],
};

describe('Recommendations & Quote Review Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (recommendationApi.getRecommendations as any).mockResolvedValue(mockRecommendationsResponse);
    (catalogueApi.getAll as any).mockResolvedValue([
      {
        product_id: 'P01',
        product_name: 'Airtel Business Broadband 100M',
        category: 'Connectivity',
        monthly_price_min: 999,
        monthly_price_max: 999,
        pricing_unit: 'connection',
        one_time_setup_fee: 500,
        min_contract_months: 12,
        typical_install_days: 3,
        requires_gstin: false,
        description: 'Standard 100Mbps optical fiber connection.',
      },
      {
        product_id: 'P03',
        product_name: '4G POS Backup Wireless',
        category: 'Connectivity',
        monthly_price_min: 1000,
        monthly_price_max: 1000,
        pricing_unit: 'connection',
        one_time_setup_fee: 500,
        min_contract_months: 12,
        typical_install_days: 2,
        requires_gstin: false,
        description: 'Wireless automatic cellular backup for payment terminals.',
      },
    ]);
    (quoteApi.previewQuote as any).mockResolvedValue(mockQuoteResponse);
  });

  it('renders Essential, Growth, and Premium bundle cards with backend prices', async () => {
    render(
      <OnboardingProvider>
        <BrowserRouter>
          <RecommendationsPage />
        </BrowserRouter>
      </OnboardingProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Essential Bundle')).toBeInTheDocument();
      expect(screen.getByText('Growth Bundle')).toBeInTheDocument();
      expect(screen.getByText('Premium Bundle')).toBeInTheDocument();
    });

    expect(screen.getByText('Micro Starter Connectivity')).toBeInTheDocument();
    expect(screen.getByText('Micro Retail Complete Growth')).toBeInTheDocument();
  });

  it('clearly separates Monthly Recurring Charges (MRC) from One-Time Charges and First-Month Total on Quote Page', async () => {
    render(
      <OnboardingProvider>
        <BrowserRouter>
          <QuotePage />
        </BrowserRouter>
      </OnboardingProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Commercial Quote Preview')).toBeInTheDocument();
      expect(screen.getByText('Q-TEST9988')).toBeInTheDocument();
    });

    // Check distinct MRC vs OTC vs First Month Payable
    expect(screen.getByText('Monthly Recurring Charges (MRC)')).toBeInTheDocument();
    expect(screen.getByText('One-Time Setup & Hardware (OTC)')).toBeInTheDocument();
    expect(screen.getByText('Estimated First-Month Payable')).toBeInTheDocument();

    expect(screen.getByText('₹1,999')).toBeInTheDocument();
    expect(screen.getAllByText('₹1,000').length).toBeGreaterThan(0);
    expect(screen.getByText('₹2,999')).toBeInTheDocument();

    // Check turnaround and contract
    expect(screen.getByText('3 Business Days')).toBeInTheDocument();
    expect(screen.getByText('12 Months Term')).toBeInTheDocument();
  });
});
