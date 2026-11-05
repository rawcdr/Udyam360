import { Product } from './catalogue';

export interface ScoreBreakdown {
  requirement_match_score: number;
  budget_fit_score: number;
  catalogue_eligibility_score: number;
  segment_suitability_score: number;
  total_score: number;
  formula_explanation: string;
}

export interface ContractDetail {
  product_id: string;
  product_name: string;
  min_contract_months: number;
  typical_install_days: number;
}

export interface ProductPriceBreakdown {
  product_id: string;
  product_name: string;
  category: string;
  unit: string;
  quantity: number;
  unit_price_min_inr: number;
  unit_price_max_inr: number;
  unit_setup_inr: number;
  monthly_subtotal_min: number;
  monthly_subtotal_max: number;
  setup_subtotal: number;
  min_contract_months: number;
}

export interface PricingCalculation {
  monthly_total_min: number;
  monthly_total_max: number;
  setup_total_min: number;
  setup_total_max: number;
  estimated_first_month_min: number;
  estimated_first_month_max: number;
  contract_details: ContractDetail[];
  product_breakdown: ProductPriceBreakdown[];
}

export interface RecommendedBundle {
  bundle_tier: 'Essential' | 'Growth' | 'Premium' | string;
  bundle_name: string;
  product_ids: string[];
  products: Product[];
  pricing: PricingCalculation;
  score: ScoreBreakdown;
  explanation: Record<string, any>;
  budget_status: string;
  budget_gap_inr: number;
  max_budget_gap_inr: number;
}

export interface RecommendationResponse {
  business_segment: string;
  is_primary_target_segment: boolean;
  status: string;
  essential_bundle?: RecommendedBundle | null;
  growth_bundle?: RecommendedBundle | null;
  premium_bundle?: RecommendedBundle | null;
  missing_information: string[];
  notes: string[];
}
