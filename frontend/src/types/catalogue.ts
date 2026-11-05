/** Type definitions corresponding to backend/app/schemas/catalogue.py */

export interface Product {
  product_id: string;
  product_name: string;
  category: string;
  monthly_price_min: number;
  monthly_price_max: number;
  pricing_unit: string;
  one_time_setup_fee: number;
  min_contract_months: number;
  typical_install_days: number;
  requires_gstin: boolean;
  min_employees: number;
  max_employees: number;
  supported_segments: string[];
  supported_city_tiers: number[];
  prerequisite_product_ids: string[];
  description: string;
  sla_target: string;
  cloud_features: string[];
}

export interface CatalogueSummary {
  total_products: number;
  categories: Record<string, number>;
  pricing_units: Record<string, number>;
  monthly_price_overall_min: number;
  monthly_price_overall_max: number;
  gstin_required_count: number;
}

