"""Unit tests for deterministic KYC validation rules (Scenarios 5, 6, 7)."""

from app.schemas.kyc import DocumentType, ExtractedDocumentFields, MatchStatus
from app.services.kyc_validation_service import (
    KYCValidationService,
    normalize_address,
    normalize_business_name,
)


def test_required_documents_with_gst_mandated_product():
    service = KYCValidationService()
    # P03 requires GSTIN == 'Y'
    reqs = service.determine_required_documents(
        business_profile_snapshot={"has_gstin": False},
        selected_product_ids=["P03"]
    )
    assert DocumentType.GST_CERTIFICATE in reqs
    assert DocumentType.ADDRESS_PROOF in reqs


def test_required_documents_without_gst_mandated_product():
    service = KYCValidationService()
    # P01 & P19 do NOT require GSTIN
    reqs = service.determine_required_documents(
        business_profile_snapshot={"has_gstin": False},
        selected_product_ids=["P01", "P19"]
    )
    assert DocumentType.GST_CERTIFICATE not in reqs
    assert DocumentType.ADDRESS_PROOF in reqs


def test_scenario_7_freshness_within_90_days():
    service = KYCValidationService()
    # 2026-06-26 is 19 days old relative to 2026-07-15
    res = service.validate_document_freshness(
        doc_type=DocumentType.ADDRESS_PROOF,
        doc_date_str="2026-06-26",
        reference_date_str="2026-07-15",
        max_age_days=90
    )
    assert res.is_fresh is True
    assert res.age_days == 19


def test_scenario_7_freshness_stale_address_proof_k11():
    service = KYCValidationService()
    # K11 bill date 2025-10-31 is 257 days old relative to 2026-07-15
    res = service.validate_document_freshness(
        doc_type=DocumentType.ADDRESS_PROOF,
        doc_date_str="2025-10-31",
        reference_date_str="2026-07-15",
        max_age_days=90
    )
    assert res.is_fresh is False
    assert res.age_days == 257
    assert "STALE" in res.reason


def test_scenario_5_business_name_mismatch():
    service = KYCValidationService()
    fields1 = ExtractedDocumentFields(
        document_type=DocumentType.GST_CERTIFICATE,
        trade_name="Vindhya Tours & Travels"
    )
    fields2 = ExtractedDocumentFields(
        document_type=DocumentType.UDYAM_CERTIFICATE,
        trade_name="Completely Different Electronics Private Limited"
    )

    res = service.compare_entities([fields1, fields2])
    assert res.name_match_status == MatchStatus.CONFIRMED_MISMATCH
    assert res.name_similarity_score < 0.50


def test_scenario_6_address_mismatch():
    service = KYCValidationService()
    fields1 = ExtractedDocumentFields(
        document_type=DocumentType.GST_CERTIFICATE,
        business_address="Shop 1, Tech Park Road, Visakhapatnam, Andhra Pradesh"
    )
    fields2 = ExtractedDocumentFields(
        document_type=DocumentType.ADDRESS_PROOF,
        business_address="Unit 99, Marine Drive, Mumbai, Maharashtra"
    )

    res = service.compare_entities([fields1, fields2])
    assert res.address_match_status == MatchStatus.CONFIRMED_MISMATCH
    assert res.address_similarity_score < 0.50


def test_entity_name_normalization_affixes():
    norm1 = normalize_business_name("Neha Kaur (Prop. Vindhya Tours & Travels)")
    norm2 = normalize_business_name("Vindhya Tours & Travels Pvt Ltd")
    assert norm1 == norm2 == "vindhya tours travels"

