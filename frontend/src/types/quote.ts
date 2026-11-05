import { BusinessProfile } from './advisor';
import { PricingCalculation } from './recommendations';

export interface QuotePreviewRequest {
  profile: BusinessProfile;
  selected_product_ids: string[];
  bundle_tier?: string | null;
  quantity_overrides?: Record<string, number>;
}

export interface QuotePreviewResponse {
  quote_id: string;
  business_segment: string;
  bundle_tier: string;
  is_eligible: boolean;
  eligibility_issues: string[];
  pricing: PricingCalculation;
  typical_install_days: number;
  min_contract_months: number;
  terms_and_conditions: string[];
}
