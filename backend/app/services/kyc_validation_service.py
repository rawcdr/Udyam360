"""Deterministic validation engine for KYC documents, cross-document matching, and freshness checks."""

import difflib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.config import settings
from app.schemas.kyc import (
    CheckStatus,
    CrossDocumentConsistencyResult,
    DocumentType,
    ExtractedDocumentFields,
    FreshnessCheckResult,
    KYCDocumentMetadata,
    KYCStatus,
    MatchStatus,
    RegistryVerificationResult,
    ValidationCheckItem,
)
from app.services.catalogue_service import catalogue_service


# Common legal prefixes and suffixes to strip during entity name normalization
LEGAL_AFFIXES = [
    r"\bprop\.?\b",
    r"\bproprietorship\b",
    r"\bllp\b",
    r"\blimited liability partnership\b",
    r"\bpvt\.?\s*ltd\.?\b",
    r"\bprivate limited\b",
    r"\bltd\.?\b",
    r"\blimited\b",
    r"\binc\.?\b",
    r"\bcorp\.?\b",
    r"\bco\.?\b",
    r"\band\b",
    r"\b&\b",
]

# Common address token normalizations
ADDRESS_ABBREVIATIONS = {
    "rd": "road",
    "stn": "station",
    "sec": "sector",
    "opp": "opposite",
    "nr": "near",
    "apt": "apartment",
    "bldg": "building",
    "flr": "floor",
    "ap": "andhra pradesh",
    "mh": "maharashtra",
    "wb": "west bengal",
    "dl": "delhi",
    "gj": "gujarat",
    "rj": "rajasthan",
    "pb": "punjab",
    "kl": "kerala",
    "tn": "tamil nadu",
}


def normalize_business_name(name: Optional[str]) -> str:
    """Normalize company name for fuzzy matching by removing noise and legal suffixes."""
    if not name:
        return ""
    clean = name.lower().strip()
    # If "(Prop. XYZ)" is in name, extract the trade name portion
    if "(prop." in clean:
        parts = clean.split("(prop.")
        if len(parts) > 1:
            clean = parts[1].replace(")", "").strip()

    # Remove legal affixes
    for affix in LEGAL_AFFIXES:
        clean = re.sub(affix, " ", clean, flags=re.IGNORECASE)

    # Remove non-alphanumeric
    clean = re.sub(r"[^a-z0-9\s]", " ", clean)
    # Collapse whitespace
    return " ".join(clean.split())


def normalize_address(address: Optional[str]) -> str:
    """Normalize address string for robust token comparison."""
    if not address:
        return ""
    clean = address.lower()
    # Replace punctuation with spaces
    clean = re.sub(r"[^a-z0-9\s]", " ", clean)
    tokens = clean.split()
    expanded = [ADDRESS_ABBREVIATIONS.get(t, t) for t in tokens]
    return " ".join(expanded)


class KYCValidationService:
    """Deterministic validation rules enforcing document completeness, freshness, and consistency."""

    def determine_required_documents(
        self,
        business_profile_snapshot: Dict[str, Any],
        selected_product_ids: List[str]
    ) -> List[DocumentType]:
        """Determine mandatory document types based on profile and selected product catalogue rules."""
        required: List[DocumentType] = [
            DocumentType.ADDRESS_PROOF,
            DocumentType.SIGNATORY_ID,
        ]

        # 1. Check if any selected product mandates active GSTIN
        requires_gst_by_product = False
        for pid in selected_product_ids:
            prod = catalogue_service.get_product_by_id(pid)
            if prod:
                req_val = getattr(prod, "requires_gstin", False)
                if req_val is True or req_val == "Y" or str(req_val).lower() == "true":
                    requires_gst_by_product = True
                    break

        # Check if customer explicitly claimed to possess GSTIN
        claimed_has_gst = bool(business_profile_snapshot.get("has_gstin") or business_profile_snapshot.get("claimed_has_gstin"))

        if requires_gst_by_product or claimed_has_gst:
            required.append(DocumentType.GST_CERTIFICATE)

        # Udyam certificate is standard for Indian MSME verification
        required.append(DocumentType.UDYAM_CERTIFICATE)

        return required

    def validate_document_freshness(
        self,
        doc_type: DocumentType,
        doc_date_str: Optional[str],
        reference_date_str: Optional[str] = None,
        max_age_days: Optional[int] = None
    ) -> FreshnessCheckResult:
        """Evaluate document date freshness using synthetic reference date (2026-07-15)."""
        ref_str = reference_date_str or settings.KYC_SYNTHETIC_REFERENCE_DATE
        max_days = max_age_days or settings.KYC_ADDRESS_PROOF_MAX_AGE_DAYS

        ref_date = datetime.strptime(ref_str, "%Y-%m-%d")

        if not doc_date_str:
            return FreshnessCheckResult(
                document_type=doc_type,
                document_date=None,
                reference_date=ref_str,
                age_days=None,
                max_allowed_days=max_days,
                is_fresh=False,
                reason="Document date is missing or could not be extracted from OCR."
            )

        try:
            doc_date = datetime.strptime(doc_date_str, "%Y-%m-%d")
        except ValueError:
            return FreshnessCheckResult(
                document_type=doc_type,
                document_date=doc_date_str,
                reference_date=ref_str,
                age_days=None,
                max_allowed_days=max_days,
                is_fresh=False,
                reason=f"Invalid date format '{doc_date_str}'. Expected YYYY-MM-DD."
            )

        age_days = (ref_date - doc_date).days

        if age_days < 0:
            return FreshnessCheckResult(
                document_type=doc_type,
                document_date=doc_date_str,
                reference_date=ref_str,
                age_days=age_days,
                max_allowed_days=max_days,
                is_fresh=False,
                reason=f"Document date is in the future relative to reference date {ref_str}."
            )

        is_fresh = age_days <= max_days
        reason = (
            f"Document is fresh ({age_days} days old <= limit of {max_days} days)."
            if is_fresh else
            f"Document is STALE ({age_days} days old exceeds maximum allowed limit of {max_days} days)."
        )

        return FreshnessCheckResult(
            document_type=doc_type,
            document_date=doc_date_str,
            reference_date=ref_str,
            age_days=age_days,
            max_allowed_days=max_days,
            is_fresh=is_fresh,
            reason=reason
        )

    def compare_entities(
        self,
        extracted_fields_list: List[ExtractedDocumentFields],
        profile_name: Optional[str] = None
    ) -> CrossDocumentConsistencyResult:
        """Perform cross-document name and address similarity checks."""
        names: List[str] = []
        addresses: List[str] = []

        if profile_name:
            names.append(profile_name)

        for fields in extracted_fields_list:
            n = fields.trade_name or fields.legal_business_name
            if n:
                names.append(n)
            if fields.business_address:
                addresses.append(fields.business_address)

        # 1. Compare Names
        name_scores = []
        norm_names = [normalize_business_name(n) for n in names if normalize_business_name(n)]
        if len(norm_names) >= 2:
            base = norm_names[0]
            for other in norm_names[1:]:
                score = difflib.SequenceMatcher(None, base, other).ratio()
                name_scores.append(score)

        avg_name_score = sum(name_scores) / len(name_scores) if name_scores else 1.0

        if not norm_names or len(norm_names) < 2:
            name_status = MatchStatus.NOT_AVAILABLE
        elif avg_name_score >= settings.NAME_SIMILARITY_THRESHOLD:
            name_status = MatchStatus.MATCH
        elif avg_name_score >= (settings.NAME_SIMILARITY_THRESHOLD - 0.20):
            name_status = MatchStatus.POSSIBLE_MISMATCH
        else:
            name_status = MatchStatus.CONFIRMED_MISMATCH

        # 2. Compare Addresses
        addr_scores = []
        norm_addrs = [normalize_address(a) for a in addresses if normalize_address(a)]
        if len(norm_addrs) >= 2:
            base_addr = norm_addrs[0]
            for other_addr in norm_addrs[1:]:
                score = difflib.SequenceMatcher(None, base_addr, other_addr).ratio()
                addr_scores.append(score)

        avg_addr_score = sum(addr_scores) / len(addr_scores) if addr_scores else 1.0

        if not norm_addrs or len(norm_addrs) < 2:
            addr_status = MatchStatus.NOT_AVAILABLE
        elif avg_addr_score >= settings.ADDRESS_SIMILARITY_THRESHOLD:
            addr_status = MatchStatus.MATCH
        elif avg_addr_score >= (settings.ADDRESS_SIMILARITY_THRESHOLD - 0.20):
            addr_status = MatchStatus.POSSIBLE_MISMATCH
        else:
            addr_status = MatchStatus.CONFIRMED_MISMATCH

        details = [
            f"Business name consistency status: {name_status.value} (similarity: {avg_name_score:.2f})",
            f"Business address consistency status: {addr_status.value} (similarity: {avg_addr_score:.2f})",
        ]

        return CrossDocumentConsistencyResult(
            name_match_status=name_status,
            name_similarity_score=round(avg_name_score, 2),
            address_match_status=addr_status,
            address_similarity_score=round(avg_addr_score, 2),
            details=details
        )


kyc_validation_service = KYCValidationService()
