/** Type definitions corresponding to backend/app/schemas/advisor.py and business_profile.py */

export interface BusinessProfile {
  business_name?: string | null;
  business_type?: string | null;
  business_segment?: string | null;
  segment?: string | null;
  num_sites?: number;
  sites_count?: number;
  employee_count?: number | null;
  num_employees?: number | null;
  city?: string | null;
  city_tier?: number | null;
  has_gstin?: boolean | null;
  gstin_available?: boolean | null;
  has_udyam?: boolean | null;
  udyam_available?: boolean | null;
  monthly_budget_inr?: number | null;
  budget_monthly?: number | null;
  requested_services?: string[];
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface AdvisorStartResponse {
  conversation_id: string;
  welcome_message: string;
  suggested_prompts: string[];
}

export interface AdvisorMessageRequest {
  conversation_id: string;
  message: string;
}

export interface AdvisorMessageResponse {
  conversation_id: string;
  assistant_message: string;
  extracted_profile?: BusinessProfile | null;
  missing_fields: string[];
  clarification_required: boolean;
  recommendations_available: boolean;
  recommendations?: any | null;
  processing_status: 'SUCCESS' | 'FALLBACK' | 'ERROR';
  error_detail?: string | null;
}

export interface ConversationState {
  conversation_id: string;
  profile: BusinessProfile;
  history: ChatMessage[];
  missing_fields: string[];
  turn_count: number;
  recommendations_available: boolean;
  last_recommendations?: any | null;
  status: string;
}
