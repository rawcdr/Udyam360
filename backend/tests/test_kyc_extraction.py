"""Unit tests for document field parsing and OCR text normalization."""

import pytest
from app.schemas.kyc import DocumentType
from app.services.kyc_extraction_service import (
    KYCExtractionService,
    normalize_gstin_candidate,
    normalize_udyam_candidate,
)
from app.services.ocr.local_ocr import MockOCRProvider


def test_normalize_gstin_candidate_clean():
    clean = "37IHKXV5167L1ZS"
    assert normalize_gstin_candidate(clean) == "37IHKXV5167L1ZS"


def test_normalize_gstin_candidate_with_ocr_confusions():
    # 1 confused with I, and I confused with 1
    ocr_raw = "371HKXV5167LIZS"
    assert normalize_gstin_candidate(ocr_raw) == "37IHKXV5167L1ZS"


def test_normalize_gstin_invalid_length():
    assert normalize_gstin_candidate("INVALID_TOO_SHORT") is None
    assert normalize_gstin_candidate("37IHKXV5167L1ZSTOO_LONG") is None


def test_normalize_udyam_candidate_valid():
    raw = "UDYAM-WB-OO- 5053330"
    assert normalize_udyam_candidate(raw) == "UDYAM-WB-00-5053330"


def test_normalize_udyam_candidate_en_dash():
    raw = "UDYAM–MH–00–9516696"
    assert normalize_udyam_candidate(raw) == "UDYAM-MH-00-9516696"


@pytest.mark.anyio
async def test_parse_gst_certificate_with_mock():
    mock_text = (
        "Specimen: GST Registration Certificate\n"
        "GSTIN\n"
        "Legal name\n"
        "Trade name\n"
        "Address of principal place of business\n"
        "Date of liability\n"
        "37IHKXV5167L1ZS\n"
        "Neha Kaur (Prop. Vindhya Tours & Travels)\n"
        "Vindhya Tours & Travels\n"
        "Proprietorship\n"
        "Shop/Unit 1, Tech Park Road, Visakhapatnam, Andhra Pradesh - 118383\n"
        "2025-06-07\n"
        "Regular"
    )
    provider = MockOCRProvider(predefined_results={"gst_doc": mock_text})
    service = KYCExtractionService(ocr_provider=provider)

    fields, ocr_res = await service.extract_document_fields("gst_doc.png", DocumentType.GST_CERTIFICATE)

    assert fields.document_type == DocumentType.GST_CERTIFICATE
    assert fields.gstin == "37IHKXV5167L1ZS"
    assert "Vindhya Tours" in str(fields.trade_name)
    assert fields.document_date == "2025-06-07"
    assert len(fields.warnings) == 0


@pytest.mark.anyio
async def test_parse_missing_registration_number_scenario_4():
    mock_text = (
        "Specimen: GST Registration Certificate\n"
        "Legal name: Acme Retailers\n"
        "Address: Civil Lines, Pune\n"
    )
    provider = MockOCRProvider(predefined_results={"missing_gstin": mock_text})
    service = KYCExtractionService(ocr_provider=provider)

    fields, _ = await service.extract_document_fields("missing_gstin.png", DocumentType.GST_CERTIFICATE)

    assert fields.gstin is None
    assert any("GSTIN registration number could not be reliably extracted" in w for w in fields.warnings)

