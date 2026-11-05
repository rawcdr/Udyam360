export type DocumentType =
  | 'GST_CERTIFICATE'
  | 'UDYAM_CERTIFICATE'
  | 'ADDRESS_PROOF'
  | 'SIGNATORY_ID'
  | 'OTHER';

export type KYCStatus =
  | 'VERIFIED'
  | 'PENDING_REVIEW'
  | 'MISSING_DOCUMENTS'
  | 'REJECTED'
  | 'PROCESSING';

export interface KYCDocumentMetadata {
  document_id: string;
  kyc_case_id: string;
  document_type: DocumentType;
  original_filename: string;
  file_size_bytes: number;
  mime_type: string;
  uploaded_at: string;
  is_processed: boolean;
}

export interface KYCCaseResponse {
  kyc_case_id: string;
  advisor_session_id: string;
  business_profile_snapshot: Record<string, any>;
  selected_product_ids: string[];
  quote_reference?: string | null;
  application_status: KYCStatus;
  required_document_types: DocumentType[];
  uploaded_documents: KYCDocumentMetadata[];
  consent_recorded: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConsentRecord {
  consent_id: string;
  kyc_case_id: string;
  consent_granted: boolean;
  consent_version: string;
  purpose: string;
  timestamp: string;
  withdrawn: boolean;
  withdrawn_timestamp?: string | null;
}

export interface ValidationCheckItem {
  check_code: string;
  check_name: string;
  status: string;
  message: string;
  details?: Record<string, any> | null;
}

export interface KYCValidationResult {
  kyc_case_id: string;
  overall_status: KYCStatus;
  checks_passed: ValidationCheckItem[];
  checks_failed: ValidationCheckItem[];
  warnings: ValidationCheckItem[];
  missing_documents: DocumentType[];
  manual_review_required: boolean;
  review_reasons: string[];
  explanation: string;
}
