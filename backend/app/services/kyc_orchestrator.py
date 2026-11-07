"""Central KYC Orchestrator executing the complete document verification pipeline."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.schemas.kyc import (
    CheckStatus,
    ConsentRecord,
    DocumentType,
    ExtractedDocumentFields,
    FreshnessCheckResult,
    KYCCaseResponse,
    KYCDocumentMetadata,
    KYCStatus,
    KYCValidationResult,
    MatchStatus,
    RegistryVerificationResult,
    ValidationCheckItem,
)
from app.services.conversation_service import conversation_service
from app.services.kyc_consent_service import kyc_consent_service
from app.services.kyc_document_service import kyc_document_service
from app.services.kyc_extraction_service import kyc_extraction_service
from app.services.kyc_storage_service import kyc_storage_service
from app.services.kyc_validation_service import kyc_validation_service
from app.services.registry_verification_service import registry_verification_service


class KYCOrchestrator:
    """Coordinates storage, OCR, registry lookups, and deterministic validation rules."""

    def __init__(self):
        # case_id -> KYCCaseResponse
        self._cases: Dict[str, KYCCaseResponse] = {}
        # case_id -> KYCValidationResult
        self._validation_results: Dict[str, KYCValidationResult] = {}

    def create_case(
        self,
        advisor_session_id: str,
        selected_product_ids: Optional[List[str]] = None,
        quote_reference: Optional[str] = None
    ) -> KYCCaseResponse:
        """Initialize a new KYC onboarding case linked to an existing advisor session."""
        conv_state = conversation_service.get_conversation(advisor_session_id)
        if not conv_state:
            conv_state = conversation_service.create_conversation(advisor_session_id)

        # Capture frozen snapshot of the customer profile
        profile_dict = conv_state.profile.model_dump()
        product_ids = selected_product_ids or []

        # Determine required documents
        required_docs = kyc_validation_service.determine_required_documents(
            business_profile_snapshot=profile_dict,
            selected_product_ids=product_ids
        )

        case_id = f"KYC-{uuid.uuid4().hex[:10].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        case_response = KYCCaseResponse(
            kyc_case_id=case_id,
            advisor_session_id=advisor_session_id,
            business_profile_snapshot=profile_dict,
            selected_product_ids=product_ids,
            quote_reference=quote_reference,
            application_status=KYCStatus.PROCESSING,
            required_document_types=required_docs,
            uploaded_documents=[],
            consent_recorded=False,
            created_at=now_iso,
            updated_at=now_iso
        )

        self._cases[case_id] = case_response

        # Persist case in SQLite database
        try:
            from app.db.database import SessionLocal
            from app.db.models import KYCCaseRecord
            from app.services.audit_service import audit_service
            db = SessionLocal()
            try:
                record = KYCCaseRecord(
                    case_id=case_id,
                    advisor_session_id=advisor_session_id,
                    application_status=case_response.application_status.value,
                    created_at=now_iso,
                    updated_at=now_iso,
                )
                db.add(record)
                db.commit()

                audit_service.log_event(
                    event_type="KYC_CASE_CREATED",
                    actor_type="CUSTOMER",
                    outcome="SUCCESS",
                    resource_type="KYC_CASE",
                    resource_id=case_id,
                    details={"advisor_session_id": advisor_session_id},
                )
            finally:
                db.close()
        except Exception:
            pass

        return case_response

    def get_case(self, case_id: str) -> Optional[KYCCaseResponse]:
        """Retrieve a KYC case by ID, syncing latest uploaded documents and consent."""
        case = self._cases.get(case_id)
        if case:
            case.uploaded_documents = kyc_document_service.list_documents(case_id)
            case.consent_recorded = kyc_consent_service.is_consent_active(case_id)
        return case

    def delete_case(self, case_id: str) -> bool:
        """Safely delete a KYC case, attached files, consent, and validation records."""
        if case_id not in self._cases:
            return False
        kyc_document_service.delete_case_documents(case_id)
        kyc_consent_service.delete_consent(case_id)
        self._validation_results.pop(case_id, None)
        self._cases.pop(case_id, None)
        return True

    async def process_kyc(self, case_id: str) -> KYCValidationResult:
        """Execute end-to-end deterministic verification pipeline for a KYC application."""
        case = self.get_case(case_id)
        if not case:
            raise ValueError(f"KYC case '{case_id}' not found.")

        # 1. Enforce Customer Consent Precondition
        if not kyc_consent_service.is_consent_active(case_id):
            consent_rec = kyc_consent_service.get_consent(case_id)
            if consent_rec and consent_rec.withdrawn:
                reason = "Customer consent was withdrawn. Document processing halted."
            else:
                reason = "Explicit customer consent has not been granted. Document processing is blocked."

            result = KYCValidationResult(
                kyc_case_id=case_id,
                overall_status=KYCStatus.PENDING_REVIEW,
                checks_passed=[],
                checks_failed=[
                    ValidationCheckItem(
                        check_code="CONSENT_MISSING",
                        check_name="Customer Consent Verification",
                        status=CheckStatus.FAIL,
                        message=reason
                    )
                ],
                warnings=[],
                missing_documents=case.required_document_types,
                manual_review_required=True,
                review_reasons=[reason],
                explanation=reason
            )
            self._validation_results[case_id] = result
            case.application_status = KYCStatus.PENDING_REVIEW
            return result

        # 2. Check Document Completeness
        uploaded_docs = kyc_document_service.list_documents(case_id)
        uploaded_types = {d.document_type for d in uploaded_docs}
        missing_docs = [t for t in case.required_document_types if t not in uploaded_types]

        checks_passed: List[ValidationCheckItem] = []
        checks_failed: List[ValidationCheckItem] = []
        warnings: List[ValidationCheckItem] = []
        registry_results: List[RegistryVerificationResult] = []
        freshness_results: List[FreshnessCheckResult] = []
        review_reasons: List[str] = []

        if missing_docs:
            checks_failed.append(
                ValidationCheckItem(
                    check_code="DOCUMENTS_INCOMPLETE",
                    check_name="Mandatory Document Completeness",
                    status=CheckStatus.FAIL,
                    message=f"Missing required documents: {[d.value for d in missing_docs]}"
                )
            )
            review_reasons.append(f"Application is missing {len(missing_docs)} required document(s).")
        else:
            checks_passed.append(
                ValidationCheckItem(
                    check_code="DOCUMENTS_COMPLETE",
                    check_name="Mandatory Document Completeness",
                    status=CheckStatus.PASS,
                    message="All mandatory documents for this bundle and segment are present."
                )
            )

        # 3. Execute Local OCR and Field Extraction on all uploaded documents
        extracted_fields_list: List[ExtractedDocumentFields] = []

        for doc in uploaded_docs:
            doc_bytes = kyc_storage_service.read_document_bytes(doc.document_id)
            if not doc_bytes:
                warnings.append(
                    ValidationCheckItem(
                        check_code="FILE_UNREADABLE",
                        check_name=f"Document Readability ({doc.document_type.value})",
                        status=CheckStatus.WARN,
                        message=f"Could not read bytes for document ID {doc.document_id}."
                    )
                )
                continue

            extracted, ocr_res = await kyc_extraction_service.extract_document_fields(
                image_input=doc_bytes,
                document_type=doc.document_type
            )
            kyc_document_service.update_extracted_fields(doc.document_id, extracted)
            extracted_fields_list.append(extracted)

            if ocr_res.average_confidence < settings.OCR_MIN_CONFIDENCE_THRESHOLD:
                warnings.append(
                    ValidationCheckItem(
                        check_code="LOW_OCR_CONFIDENCE",
                        check_name=f"OCR Confidence ({doc.document_type.value})",
                        status=CheckStatus.WARN,
                        message=f"Confidence is low ({ocr_res.average_confidence:.2f}). File requires human visual verification.",
                        details={"confidence": ocr_res.average_confidence, "document_type": doc.document_type.value}
                    )
                )
                review_reasons.append(f"Low OCR quality on {doc.document_type.value}.")
            else:
                checks_passed.append(
                    ValidationCheckItem(
                        check_code="OCR_CONFIDENCE_OK",
                        check_name=f"OCR Confidence ({doc.document_type.value})",
                        status=CheckStatus.PASS,
                        message=f"OCR extracted successfully with confidence {ocr_res.average_confidence:.2f}."
                    )
                )

        # 4. Mock GSTIN Registry Verification
        gst_doc = next((f for f in extracted_fields_list if f.document_type == DocumentType.GST_CERTIFICATE), None)
        if gst_doc:
            if gst_doc.gstin:
                gst_res = registry_verification_service.verify_gstin(gst_doc.gstin)
                registry_results.append(gst_res)

                if gst_res.found and gst_res.status == "Active":
                    checks_passed.append(
                        ValidationCheckItem(
                            check_code="GSTIN_REGISTRY_ACTIVE",
                            check_name="Mock GSTIN Registry Verification",
                            status=CheckStatus.PASS,
                            message=f"GSTIN {gst_res.searched_identifier} verified as ACTIVE in mock GST database."
                        )
                    )
                elif gst_res.found and gst_res.status == "Cancelled":
                    checks_failed.append(
                        ValidationCheckItem(
                            check_code="GSTIN_STATUS_CANCELLED",
                            check_name="Mock GSTIN Registry Verification",
                            status=CheckStatus.FAIL,
                            message=f"CRITICAL: GSTIN {gst_res.searched_identifier} is CANCELLED in mock GST database."
                        )
                    )
                    review_reasons.append("Applicant's GST registration is Cancelled.")
                elif gst_res.found and gst_res.status == "Suspended":
                    warnings.append(
                        ValidationCheckItem(
                            check_code="GSTIN_STATUS_SUSPENDED",
                            check_name="Mock GSTIN Registry Verification",
                            status=CheckStatus.WARN,
                            message=f"WARNING: GSTIN {gst_res.searched_identifier} is SUSPENDED. Human review required."
                        )
                    )
                    review_reasons.append("Applicant's GST registration is Suspended.")
                else:
                    checks_failed.append(
                        ValidationCheckItem(
                            check_code="GSTIN_NOT_FOUND",
                            check_name="Mock GSTIN Registry Verification",
                            status=CheckStatus.FAIL,
                            message=f"GSTIN {gst_res.searched_identifier} was not found in mock GST registry."
                        )
                    )
                    review_reasons.append("GSTIN record not located in mock registry.")
            else:
                checks_failed.append(
                    ValidationCheckItem(
                        check_code="GSTIN_EXTRACTION_FAILED",
                        check_name="GSTIN Identifier Identification",
                        status=CheckStatus.FAIL,
                        message="GST registration certificate was submitted but GSTIN identifier could not be extracted."
                    )
                )
                review_reasons.append("GST certificate missing legible registration number.")

        # 5. Mock Udyam Registry Verification
        udyam_doc = next((f for f in extracted_fields_list if f.document_type == DocumentType.UDYAM_CERTIFICATE), None)
        if udyam_doc:
            if udyam_doc.udyam_registration_number:
                u_res = registry_verification_service.verify_udyam(udyam_doc.udyam_registration_number)
                registry_results.append(u_res)

                if u_res.found and u_res.checks_passed:
                    checks_passed.append(
                        ValidationCheckItem(
                            check_code="UDYAM_REGISTRY_VERIFIED",
                            check_name="Mock Udyam Registry Verification",
                            status=CheckStatus.PASS,
                            message=f"Udyam registration {u_res.searched_identifier} verified ({u_res.status}) in mock database."
                        )
                    )
                else:
                    checks_failed.append(
                        ValidationCheckItem(
                            check_code="UDYAM_NOT_FOUND",
                            check_name="Mock Udyam Registry Verification",
                            status=CheckStatus.FAIL,
                            message=f"Udyam number {u_res.searched_identifier} not found in mock Udyam registry."
                        )
                    )
                    review_reasons.append("Udyam registration not found in registry database.")
            else:
                checks_failed.append(
                    ValidationCheckItem(
                        check_code="UDYAM_EXTRACTION_FAILED",
                        check_name="Udyam Identifier Identification",
                        status=CheckStatus.FAIL,
                        message="Udyam certificate submitted but registration number could not be extracted."
                    )
                )
                review_reasons.append("Udyam certificate missing registration number.")

        # 6. Document Freshness Verification (Address Proof 90-day limit)
        addr_doc = next((f for f in extracted_fields_list if f.document_type == DocumentType.ADDRESS_PROOF), None)
        if addr_doc:
            fresh_res = kyc_validation_service.validate_document_freshness(
                doc_type=DocumentType.ADDRESS_PROOF,
                doc_date_str=addr_doc.address_proof_date or addr_doc.document_date
            )
            freshness_results.append(fresh_res)

            if fresh_res.is_fresh:
                checks_passed.append(
                    ValidationCheckItem(
                        check_code="ADDRESS_PROOF_FRESH",
                        check_name="Document Freshness Verification",
                        status=CheckStatus.PASS,
                        message=fresh_res.reason
                    )
                )
            else:
                checks_failed.append(
                    ValidationCheckItem(
                        check_code="ADDRESS_PROOF_STALE",
                        check_name="Document Freshness Verification",
                        status=CheckStatus.FAIL,
                        message=fresh_res.reason
                    )
                )
                review_reasons.append(fresh_res.reason)

        # 7. Cross-Document Consistency (Names and Addresses)
        profile_name = case.business_profile_snapshot.get("business_name")
        consistency_res = kyc_validation_service.compare_entities(
            extracted_fields_list=extracted_fields_list,
            profile_name=profile_name
        )

        if consistency_res.name_match_status == MatchStatus.MATCH:
            checks_passed.append(
                ValidationCheckItem(
                    check_code="NAME_CONSISTENCY_PASS",
                    check_name="Cross-Document Business Name Matching",
                    status=CheckStatus.PASS,
                    message=f"Business name matches consistently across documents ({consistency_res.name_similarity_score:.2f})."
                )
            )
        elif consistency_res.name_match_status == MatchStatus.POSSIBLE_MISMATCH:
            warnings.append(
                ValidationCheckItem(
                    check_code="NAME_POSSIBLE_MISMATCH",
                    check_name="Cross-Document Business Name Matching",
                    status=CheckStatus.WARN,
                    message=f"Possible name variation detected ({consistency_res.name_similarity_score:.2f}). Manual review suggested."
                )
            )
            review_reasons.append("Minor name variation across documents.")
        elif consistency_res.name_match_status == MatchStatus.CONFIRMED_MISMATCH:
            checks_failed.append(
                ValidationCheckItem(
                    check_code="NAME_MISMATCH_CONFIRMED",
                    check_name="Cross-Document Business Name Matching",
                    status=CheckStatus.FAIL,
                    message=f"Confirmed name mismatch detected between submitted documents ({consistency_res.name_similarity_score:.2f})."
                )
            )
            review_reasons.append("Confirmed business name discrepancy.")

        # 8. Determine Overall Status
        manual_review = len(review_reasons) > 0 or len(warnings) > 0

        # Fatal rejection triggers: Cancelled GSTIN
        is_cancelled_gst = any(c.check_code == "GSTIN_STATUS_CANCELLED" for c in checks_failed)

        if is_cancelled_gst:
            overall_status = KYCStatus.REJECTED
            explanation = "KYC Rejected: Registration authority records show that the submitted GSTIN is CANCELLED."
        elif missing_docs:
            overall_status = KYCStatus.MISSING_DOCUMENTS
            explanation = f"KYC Incomplete: Missing mandatory documents: {', '.join([d.value for d in missing_docs])}."
        elif len(checks_failed) > 0 or len(warnings) > 0:
            overall_status = KYCStatus.PENDING_REVIEW
            failed_msgs = [c.message for c in checks_failed]
            warn_msgs = [w.message for w in warnings]
            explanation = f"KYC Pending Manual Review. Issues flagged: {'; '.join(failed_msgs + warn_msgs)}"
        else:
            overall_status = KYCStatus.VERIFIED
            explanation = "KYC Verified: All mandatory documents, mock registry lookups, and freshness checks passed successfully."

        validation_result = KYCValidationResult(
            kyc_case_id=case_id,
            overall_status=overall_status,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            warnings=warnings,
            missing_documents=missing_docs,
            registry_results=registry_results,
            cross_document_consistency=consistency_res,
            freshness_results=freshness_results,
            manual_review_required=manual_review,
            review_reasons=review_reasons,
            explanation=explanation
        )

        self._validation_results[case_id] = validation_result
        case.application_status = overall_status
        case.updated_at = datetime.now(timezone.utc).isoformat()
        return validation_result

    def get_validation_result(self, case_id: str) -> Optional[KYCValidationResult]:
        """Retrieve stored validation outcome for a KYC case."""
        return self._validation_results.get(case_id)


kyc_orchestrator = KYCOrchestrator()

