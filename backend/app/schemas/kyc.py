"""Pydantic schemas and enums for Udyam360 Smart KYC."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Supported document types grounded in hackathon specimen dataset."""
    GST_CERTIFICATE = "GST_CERTIFICATE"
    UDYAM_CERTIFICATE = "UDYAM_CERTIFICATE"
    ADDRESS_PROOF = "ADDRESS_PROOF"
    SIGNATORY_ID = "SIGNATORY_ID"
    OTHER = "OTHER"


class KYCStatus(str, Enum):
    """Overall lifecycle status of a KYC application."""
    VERIFIED = "VERIFIED"
    PENDING_REVIEW = "PENDING_REVIEW"
    MISSING_DOCUMENTS = "MISSING_DOCUMENTS"
    REJECTED = "REJECTED"
    PROCESSING = "PROCESSING"


class MatchStatus(str, Enum):
    """Cross-document comparison classification."""
    MATCH = "MATCH"
    POSSIBLE_MISMATCH = "POSSIBLE_MISMATCH"
    CONFIRMED_MISMATCH = "CONFIRMED_MISMATCH"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class CheckStatus(str, Enum):
    """Individual verification check status."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"


class ConsentRecord(BaseModel):
    """Explicit customer consent record prior to document processing."""
    consent_id: str
    kyc_case_id: str
    consent_granted: bool
    consent_version: str = "v1.0-2026"
    purpose: str = "Verification against mock registries and OCR onboarding processing"
    timestamp: str
    withdrawn: bool = False
    withdrawn_timestamp: Optional[str] = None


class ExtractedDocumentFields(BaseModel):
    """Structured fields parsed from document OCR text."""
    document_type: DocumentType
    legal_business_name: Optional[str] = None
    trade_name: Optional[str] = None
    gstin: Optional[str] = None
    udyam_registration_number: Optional[str] = None
    business_address: Optional[str] = None
    issue_date: Optional[str] = None
    document_date: Optional[str] = None
    address_proof_date: Optional[str] = None
    registration_status: Optional[str] = None
    signatory_name: Optional[str] = None
    signatory_designation: Optional[str] = None
    ocr_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    raw_text_summary: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class KYCDocumentMetadata(BaseModel):
    """Safe metadata representation of an uploaded document."""
    document_id: str
    kyc_case_id: str
    document_type: DocumentType
    original_filename: str
    file_size_bytes: int
    mime_type: str
    uploaded_at: str
    is_processed: bool = False
    extracted_fields: Optional[ExtractedDocumentFields] = None


class ValidationCheckItem(BaseModel):
    """Result of an individual deterministic rule or registry check."""
    check_code: str
    check_name: str
    status: CheckStatus
    message: str
    details: Optional[Dict[str, Any]] = None


class RegistryVerificationResult(BaseModel):
    """Outcome of mock registry verification."""
    registry_name: str  # "mock_gstin_registry" or "mock_udyam_registry"
    searched_identifier: str
    found: bool
    status: Optional[str] = None  # Active, Cancelled, Suspended, Micro, Small, etc.
    registered_name: Optional[str] = None
    registered_address: Optional[str] = None
    checks_passed: bool = False
    notes: List[str] = Field(default_factory=list)


class CrossDocumentConsistencyResult(BaseModel):
    """Outcome of comparing fields across uploaded documents."""
    name_match_status: MatchStatus = MatchStatus.NOT_AVAILABLE
    name_similarity_score: float = 0.0
    address_match_status: MatchStatus = MatchStatus.NOT_AVAILABLE
    address_similarity_score: float = 0.0
    details: List[str] = Field(default_factory=list)


class FreshnessCheckResult(BaseModel):
    """Outcome of document date freshness checks against synthetic reference date."""
    document_type: DocumentType
    document_date: Optional[str] = None
    reference_date: str = "2026-07-15"
    age_days: Optional[int] = None
    max_allowed_days: int = 90
    is_fresh: bool = False
    reason: str = ""


class KYCValidationResult(BaseModel):
    """Comprehensive explainable KYC validation report."""
    kyc_case_id: str
    overall_status: KYCStatus
    checks_passed: List[ValidationCheckItem] = Field(default_factory=list)
    checks_failed: List[ValidationCheckItem] = Field(default_factory=list)
    warnings: List[ValidationCheckItem] = Field(default_factory=list)
    missing_documents: List[DocumentType] = Field(default_factory=list)
    registry_results: List[RegistryVerificationResult] = Field(default_factory=list)
    cross_document_consistency: Optional[CrossDocumentConsistencyResult] = None
    freshness_results: List[FreshnessCheckResult] = Field(default_factory=list)
    manual_review_required: bool = False
    review_reasons: List[str] = Field(default_factory=list)
    explanation: str


class KYCCaseCreateRequest(BaseModel):
    """Request payload to initialize a new KYC onboarding case."""
    advisor_session_id: str
    selected_product_ids: List[str] = Field(default_factory=list)
    quote_reference: Optional[str] = None


class ConsentRequest(BaseModel):
    """Request payload to record explicit customer consent."""
    consent_granted: bool
    consent_version: str = "v1.0-2026"


class KYCCaseResponse(BaseModel):
    """Response representation of a KYC application case."""
    kyc_case_id: str
    advisor_session_id: str
    business_profile_snapshot: Dict[str, Any]
    selected_product_ids: List[str]
    quote_reference: Optional[str] = None
    application_status: KYCStatus
    required_document_types: List[DocumentType]
    uploaded_documents: List[KYCDocumentMetadata] = Field(default_factory=list)
    consent_recorded: bool = False
    created_at: str
    updated_at: str
    session_token: Optional[str] = Field(default=None, description="Signed customer session token")

