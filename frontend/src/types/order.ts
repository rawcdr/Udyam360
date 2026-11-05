export type OrderState =
  | 'QUOTE_CONFIRMED'
  | 'KYC_PENDING'
  | 'KYC_VERIFICATION'
  | 'MANUAL_REVIEW'
  | 'KYC_VERIFIED'
  | 'ORDER_PROCESSING'
  | 'ACTIVATION_IN_PROGRESS'
  | 'ACTIVATED'
  | 'CANCELLED';

export interface OrderTimelineEvent {
  event_id: string;
  from_state?: OrderState | null;
  to_state: OrderState;
  title: string;
  description: string;
  timestamp: string;
  is_simulated: boolean;
}

export interface CustomerInfo {
  business_name: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  installation_address?: string;
  city?: string;
  segment?: string;
}

export interface PricingSnapshot {
  currency: string;
  monthly_recurring_charges: number;
  one_time_charges: number;
  estimated_first_month: number;
}

export interface OrderCreateRequest {
  advisor_session_id?: string | null;
  quote_reference: string;
  kyc_case_id?: string | null;
  selected_product_ids: string[];
  bundle_tier?: string | null;
  customer_info: CustomerInfo;
  pricing: PricingSnapshot;
}

export interface OrderResponse {
  order_id: string;
  order_reference: string;
  quote_reference: string;
  kyc_case_id?: string | null;
  advisor_session_id?: string | null;
  current_state: OrderState;
  selected_product_ids: string[];
  bundle_tier?: string | null;
  customer_info: CustomerInfo;
  pricing: PricingSnapshot;
  created_at: string;
  updated_at: string;
  timeline: OrderTimelineEvent[];
  is_simulated_stage: boolean;
  next_action_prompt?: string | null;
}

export interface OrderTimelineResponse {
  order_id: string;
  order_reference: string;
  current_state: OrderState;
  timeline: OrderTimelineEvent[];
  is_simulated_stage: boolean;
}

