"""End-to-end unit tests for KYCOrchestrator workflows (Scenarios 1, 2, 3, 7, 8, 13, 20, 21, 23, 24)."""

import io
from PIL import Image
import pytest
from app.schemas.kyc import CheckStatus, DocumentType, KYCStatus
from app.services.conversation_service import conversation_service
from app.services.kyc_consent_service import kyc_consent_service
from app.services.kyc_document_service import kyc_document_service
from app.services.kyc_extraction_service import kyc_extraction_service
from app.services.kyc_orchestrator import KYCOrchestrator
from app.services.ocr.local_ocr import MockOCRProvider


def make_dummy_png():
    img = Image.new("RGB", (200, 200), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def test_session():
    # Initialize a valid conversation session
    state = conversation_service.create_conversation()
    sess_id = state.conversation_id
    conv = conversation_service.get_conversation(sess_id)
    conv.profile.business_name = "Harmony Dental Care"
    conv.profile.business_type = "Dental Clinic"
    conv.profile.business_segment = "prof"
    conv.profile.employee_count = 6
    conv.profile.num_sites = 1
    conv.profile.city = "Kolkata"
    conv.profile.city_tier = 1
    conv.profile.has_gstin = True
    conv.profile.monthly_budget_inr = 5000.0
    return sess_id


@pytest.mark.anyio
async def test_scenario_1_and_2_clean_verified_kyc(test_session):
    orchestrator = KYCOrchestrator()
    case = orchestrator.create_case(
        advisor_session_id=test_session,
        selected_product_ids=["P03", "P16"]
    )
    case_id = case.kyc_case_id

    # 1. Grant consent
    kyc_consent_service.record_consent(case_id, consent_granted=True)

    # 2. Upload mock documents
    png_bytes = make_dummy_png()
    kyc_document_service.upload_document(case_id, DocumentType.GST_CERTIFICATE, "gst.png", png_bytes)
    kyc_document_service.upload_document(case_id, DocumentType.UDYAM_CERTIFICATE, "udyam.png", png_bytes)
    kyc_document_service.upload_document(case_id, DocumentType.ADDRESS_PROOF, "bill.png", png_bytes)
    kyc_document_service.upload_document(case_id, DocumentType.SIGNATORY_ID, "sign.png", png_bytes)

    # Mock OCR output for Harmony Dental Care (K02)
    mock_results = {
        "gst": "GST Registration Certificate\nGSTIN: 19EOGXH4115Y1ZL\nTrade name: Harmony Dental Care\nAddress: Kolkata\nDate: 2022-04-17",
        "udyam": "Udyam Registration Certificate\nUDYAM-WB-00-5053330\nEnterprise name: Harmony Dental Care\nKolkata, West Bengal\nDate: 2023-01-11",
        "bill": "Electricity Bill\nBilled to: Harmony Dental Care\nSupply address: Shop 199, Station Road, Kolkata\nBill date: 2026-05-22",
        "sign": "Authorised Signatory ID\nName: Joseph Shah\nFor business: Harmony Dental Care\nID: SYN-ID-816907"
    }
    kyc_extraction_service._provider = MockOCRProvider(predefined_results=mock_results)

    # 3. Process
    result = await orchestrator.process_kyc(case_id)

    assert result.overall_status == KYCStatus.VERIFIED
    assert result.manual_review_required is False
    assert len(result.missing_documents) == 0
    assert any(c.check_code == "GSTIN_REGISTRY_ACTIVE" for c in result.checks_passed)
    assert any(c.check_code == "UDYAM_REGISTRY_VERIFIED" for c in result.checks_passed)
    assert any(c.check_code == "ADDRESS_PROOF_FRESH" for c in result.checks_passed)

    # Clean up
    orchestrator.delete_case(case_id)


@pytest.mark.anyio
async def test_scenario_3_k05_missing_udyam_certificate(test_session):
    orchestrator = KYCOrchestrator()
    case = orchestrator.create_case(advisor_session_id=test_session, selected_product_ids=["P03"])
    case_id = case.kyc_case_id

    kyc_consent_service.record_consent(case_id, consent_granted=True)

    # Upload only 3 documents (missing Udyam certificate)
    png_bytes = make_dummy_png()
    kyc_document_service.upload_document(case_id, DocumentType.GST_CERTIFICATE, "gst.png", png_bytes)
    kyc_document_service.upload_document(case_id, DocumentType.ADDRESS_PROOF, "bill.png", png_bytes)
    kyc_document_service.upload_document(case_id, DocumentType.SIGNATORY_ID, "sign.png", png_bytes)

    result = await orchestrator.process_kyc(case_id)

    assert result.overall_status == KYCStatus.MISSING_DOCUMENTS
    assert DocumentType.UDYAM_CERTIFICATE in result.missing_documents

    orchestrator.delete_case(case_id)


@pytest.mark.anyio
async def test_scenario_8_cancelled_gstin_rejection(test_session):
    orchestrator = KYCOrchestrator()
    case = orchestrator.create_case(advisor_session_id=test_session, selected_product_ids=["P03"])
    case_id = case.kyc_case_id

    kyc_consent_service.record_consent(case_id, consent_granted=True)
    png_bytes = make_dummy_png()
    kyc_document_service.upload_document(case_id, DocumentType.GST_CERTIFICATE, "gst.png", png_bytes)
    kyc_document_service.upload_document(case_id, DocumentType.UDYAM_CERTIFICATE, "udyam.png", png_bytes)
    kyc_document_service.upload_document(case_id, DocumentType.ADDRESS_PROOF, "bill.png", png_bytes)
    kyc_document_service.upload_document(case_id, DocumentType.SIGNATORY_ID, "sign.png", png_bytes)

    # Cancelled GSTIN K01
    mock_results = {
        "gst": "GSTIN: 37IHKXV5167L1ZS\nTrade name: Vindhya Tours & Travels",
        "udyam": "UDYAM-WB-00-5053330\nEnterprise name: Vindhya Tours & Travels",
        "bill": "Billed to: Vindhya Tours & Travels\nBill date: 2026-06-26",
        "sign": "For business: Vindhya Tours & Travels"
    }
    kyc_extraction_service._provider = MockOCRProvider(predefined_results=mock_results)

    result = await orchestrator.process_kyc(case_id)

    assert result.overall_status == KYCStatus.REJECTED
    assert any(c.check_code == "GSTIN_STATUS_CANCELLED" for c in result.checks_failed)

    orchestrator.delete_case(case_id)


@pytest.mark.anyio
async def test_scenario_13_low_confidence_ocr_triggers_review_not_rejection(test_session):
    orchestrator = KYCOrchestrator()
    case = orchestrator.create_case(advisor_session_id=test_session, selected_product_ids=["P01"])
    case_id = case.kyc_case_id

    kyc_consent_service.record_consent(case_id, consent_granted=True)
    png_bytes = make_dummy_png()
    kyc_document_service.upload_document(case_id, DocumentType.GST_CERTIFICATE, "gst.png", png_bytes)
    kyc_document_service.upload_document(case_id, DocumentType.ADDRESS_PROOF, "bill.png", png_bytes)
    kyc_document_service.upload_document(case_id, DocumentType.SIGNATORY_ID, "sign.png", png_bytes)
    kyc_document_service.upload_document(case_id, DocumentType.UDYAM_CERTIFICATE, "udyam.png", png_bytes)

    # Provider returning low confidence
    class LowConfProvider(MockOCRProvider):
        async def extract_text(self, image_input, preprocess=True, document_type=None):
            res = await super().extract_text(image_input, preprocess, document_type)
            res.average_confidence = 0.45  # below 0.60
            return res

    kyc_extraction_service._provider = LowConfProvider()

    result = await orchestrator.process_kyc(case_id)

    # Never automatically reject solely on low OCR confidence!
    assert result.overall_status == KYCStatus.PENDING_REVIEW
    assert result.manual_review_required is True
    assert any("LOW_OCR_CONFIDENCE" in c.check_code for c in result.warnings)

    orchestrator.delete_case(case_id)


@pytest.mark.anyio
async def test_scenario_20_processing_without_consent_blocked(test_session):
    orchestrator = KYCOrchestrator()
    case = orchestrator.create_case(advisor_session_id=test_session, selected_product_ids=["P01"])
    case_id = case.kyc_case_id

    # Consent NOT granted
    result = await orchestrator.process_kyc(case_id)

    assert result.overall_status == KYCStatus.PENDING_REVIEW
    assert any(c.check_code == "CONSENT_MISSING" for c in result.checks_failed)

    orchestrator.delete_case(case_id)
