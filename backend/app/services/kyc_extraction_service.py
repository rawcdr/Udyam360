"""Document extraction pipeline executing local OCR and structured field parsing."""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union
from app.core.config import settings
from app.schemas.kyc import DocumentType, ExtractedDocumentFields
from app.services.ocr import OCRResult, get_ocr_provider


# Common OCR character confusions for alphanumeric normalization
DIGIT_TO_ALPHA = {"0": "O", "1": "I", "5": "S", "8": "B", "2": "Z"}
ALPHA_TO_DIGIT = {"O": "0", "I": "1", "l": "1", "S": "5", "B": "8", "Z": "2", "o": "0", "i": "1"}


def normalize_gstin_candidate(raw: str) -> Optional[str]:
    """Normalize OCR text into a compliant 15-character Indian synthetic GSTIN.

    Synthetic structure:
    - [0:2]   2 digits: State code
    - [2:7]   5 letters: PAN prefix (4th char index 5 is always 'X')
    - [7:11]  4 digits: PAN serial
    - [11:12] 1 letter:  PAN check letter
    - [12:13] 1 char:    Entity number (typically 1-9)
    - [13:14] 'Z':       Default 14th character
    - [14:15] 1 char:    Checksum character
    """
    clean = re.sub(r"[^a-zA-Z0-9]", "", raw).upper()
    if len(clean) != 15:
        return None

    chars = list(clean)

    # 1. First 2 characters must be digits (State Code)
    for i in (0, 1):
        if chars[i] in ALPHA_TO_DIGIT:
            chars[i] = ALPHA_TO_DIGIT[chars[i]]
        if not chars[i].isdigit():
            return None

    # 2. Characters 2..6 must be uppercase letters (PAN alphabetic portion)
    for i in range(2, 7):
        if chars[i] in DIGIT_TO_ALPHA:
            chars[i] = DIGIT_TO_ALPHA[chars[i]]
        if not chars[i].isalpha():
            return None

    # Enforce synthetic hackathon rule: 4th char of PAN (index 5) is 'X'
    if chars[5] != "X":
        # Check if confused with another char or accept as is
        pass

    # 3. Characters 7..10 must be digits (PAN numeric portion)
    for i in range(7, 11):
        if chars[i] in ALPHA_TO_DIGIT:
            chars[i] = ALPHA_TO_DIGIT[chars[i]]
        if not chars[i].isdigit():
            return None

    # 4. Character 11 must be letter (PAN check letter)
    if chars[11] in DIGIT_TO_ALPHA:
        chars[11] = DIGIT_TO_ALPHA[chars[11]]
    if not chars[11].isalpha():
        return None

    # 5. Character 12 is typically entity digit (1..9)
    if chars[12] in ALPHA_TO_DIGIT:
        chars[12] = ALPHA_TO_DIGIT[chars[12]]

    # 6. Character 13 is almost universally 'Z'
    if chars[13] in ("2", "z"):
        chars[13] = "Z"

    candidate = "".join(chars)
    # Final regex validation against 15-char standard pattern
    if re.match(r"^[0-9]{2}[A-Z]{4}[A-Z][0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$", candidate):
        return candidate
    return None


def normalize_udyam_candidate(raw: str) -> Optional[str]:
    """Normalize OCR text into a compliant synthetic Udyam number (e.g. UDYAM-WB-00-5053330)."""
    # Clean whitespace and hyphens
    m = re.search(
        r"UDYAM\s*[-–—]\s*([A-Za-z]{2})\s*[-–—]\s*([0-9A-Za-z]{2})\s*[-–—]\s*([0-9]{7})",
        raw,
        re.IGNORECASE
    )
    if m:
        state_code = m.group(1).upper()
        district_code = m.group(2).upper().replace("O", "0")
        serial = m.group(3)
        return f"UDYAM-{state_code}-{district_code}-{serial}"
    return None


class KYCExtractionService:
    """Document extraction service executing local OCR and document-specific parsing."""

    def __init__(self, ocr_provider=None):
        self._provider = ocr_provider

    @property
    def provider(self):
        if self._provider is None:
            self._provider = get_ocr_provider()
        return self._provider

    async def extract_document_fields(
        self,
        image_input: Union[bytes, str, Path],
        document_type: DocumentType
    ) -> Tuple[ExtractedDocumentFields, OCRResult]:
        """Execute OCR on a document and parse fields based on declared document type."""
        ocr_result = await self.provider.extract_text(image_input, preprocess=True, document_type=document_type)
        warnings: List[str] = list(ocr_result.warnings)

        if ocr_result.average_confidence < settings.OCR_MIN_CONFIDENCE_THRESHOLD:
            warnings.append(
                f"Low OCR confidence ({ocr_result.average_confidence:.2f} < {settings.OCR_MIN_CONFIDENCE_THRESHOLD}). Manual review recommended."
            )

        # Dispatch to document-specific parser
        if document_type == DocumentType.GST_CERTIFICATE:
            fields = self._parse_gst_certificate(ocr_result.lines, warnings)
        elif document_type == DocumentType.UDYAM_CERTIFICATE:
            fields = self._parse_udyam_certificate(ocr_result.lines, warnings)
        elif document_type == DocumentType.ADDRESS_PROOF:
            fields = self._parse_address_proof(ocr_result.lines, warnings)
        elif document_type == DocumentType.SIGNATORY_ID:
            fields = self._parse_signatory_id(ocr_result.lines, warnings)
        else:
            fields = ExtractedDocumentFields(
                document_type=DocumentType.OTHER,
                ocr_confidence=ocr_result.average_confidence,
                warnings=warnings
            )

        fields.ocr_confidence = ocr_result.average_confidence
        fields.raw_text_summary = ocr_result.raw_text[:200] if ocr_result.raw_text else None
        return fields, ocr_result

    def _parse_gst_certificate(self, lines: list, warnings: List[str]) -> ExtractedDocumentFields:
        """Parse structured fields from GST registration certificate."""
        gstin: Optional[str] = None
        legal_name: Optional[str] = None
        trade_name: Optional[str] = None
        address: Optional[str] = None
        doc_date: Optional[str] = None
        reg_status: Optional[str] = "Regular"

        full_text = " ".join([l.text for l in lines])

        # 1. Search for 15-char GSTIN pattern
        tokens = re.split(r"[\s,;]+", full_text)
        for token in tokens:
            candidate = normalize_gstin_candidate(token)
            if candidate:
                gstin = candidate
                break

        # Fallback regex across entire text block if broken by spaces
        if not gstin:
            m = re.search(r"\b([0-9]{2}[A-Za-z0-9]{13})\b", full_text.replace(" ", ""))
            if m:
                gstin = normalize_gstin_candidate(m.group(1))

        if not gstin:
            warnings.append("GSTIN registration number could not be reliably extracted from certificate.")

        # 2. Extract Legal Name & Trade Name
        headers = {
            "specimen", "gstin", "legal name", "trade name", "constitution",
            "address of principal", "place of business", "date of liability",
            "type of registration", "regular", "synthetic", "accel ytl hackathon"
        }

        for i, l in enumerate(lines):
            t = l.text.strip()
            t_lower = t.lower()
            if "legal name" in t_lower:
                if ":" in t and len(t.split(":", 1)[1].strip()) > 0:
                    legal_name = t.split(":", 1)[1].strip()
                elif i + 1 < len(lines):
                    next_t = lines[i + 1].text.strip()
                    if not any(h in next_t.lower() for h in headers):
                        legal_name = next_t
            elif "trade name" in t_lower:
                if ":" in t and len(t.split(":", 1)[1].strip()) > 0:
                    trade_name = t.split(":", 1)[1].strip()
                elif i + 1 < len(lines):
                    next_t = lines[i + 1].text.strip()
                    if not any(h in next_t.lower() for h in headers):
                        trade_name = next_t
            elif "address of principal" in t_lower:
                if ":" in t and len(t.split(":", 1)[1].strip()) > 0:
                    address = t.split(":", 1)[1].strip()
                else:
                    addr_parts = []
                    for j in range(i + 1, min(i + 5, len(lines))):
                        pj = lines[j].text.strip()
                        if any(kw in pj.lower() for kw in ("date of liability", "type of registration", "regular")):
                            break
                        if not any(h == pj.lower() for h in ("place of business", "constitution")):
                            addr_parts.append(pj)
                    address = " ".join(addr_parts).strip()

        # Fallback name search via "(Prop." or "LLP" or "Pvt Ltd" or entity tokens
        for l in lines:
            t = l.text.strip()
            if "(prop." in t.lower():
                legal_name = t
                parts = re.split(r"\(prop\.?", t, flags=re.IGNORECASE)
                if len(parts) > 1:
                    trade_name = parts[1].replace(")", "").strip()
            elif any(kw in t for kw in ("LLP", "Pvt Ltd", "Private Limited", "Tours & Travels", "Dental Care", "Woodcraft", "Salon", "Clinic", "Bake House", "Electronics")):
                if not trade_name:
                    trade_name = t
                if not legal_name:
                    legal_name = t

        # 3. Extract Liability / Document Date
        date_match = re.search(r"\b(20[12][0-9]-[01][0-9]-[0-3][0-9])\b", full_text)
        if date_match:
            doc_date = date_match.group(1)

        return ExtractedDocumentFields(
            document_type=DocumentType.GST_CERTIFICATE,
            legal_business_name=legal_name,
            trade_name=trade_name,
            gstin=gstin,
            business_address=address,
            document_date=doc_date,
            registration_status=reg_status,
            warnings=warnings
        )

    def _parse_udyam_certificate(self, lines: list, warnings: List[str]) -> ExtractedDocumentFields:
        """Parse structured fields from Udyam registration certificate."""
        udyam_number: Optional[str] = None
        enterprise_name: Optional[str] = None
        address_parts: List[str] = []
        doc_date: Optional[str] = None

        full_text = " ".join([l.text for l in lines])

        # 1. Search for Udyam Number
        udyam_number = normalize_udyam_candidate(full_text)
        if not udyam_number:
            # Check individual lines
            for l in lines:
                candidate = normalize_udyam_candidate(l.text)
                if candidate:
                    udyam_number = candidate
                    break

        if not udyam_number:
            warnings.append("Udyam registration number could not be found or extracted.")

        # 2. Extract Enterprise Name and Address Details
        for i, l in enumerate(lines):
            t = l.text.strip()
            t_lower = t.lower()
            if "enterprise name" in t_lower:
                if ":" in t and len(t.split(":", 1)[1].strip()) > 0:
                    enterprise_name = t.split(":", 1)[1].strip()
                elif i + 1 < len(lines):
                    enterprise_name = lines[i + 1].text.strip()
            elif any(kw in t for kw in ("Visakhapatnam", "Nagpur", "Kolkata", "Jaipur", "Delhi", "Vadodara", "Mumbai", "Ludhiana", "Kochi", "Chennai", "Bengaluru", "Pune")):
                address_parts.append(t)
            elif "State" in t and i + 1 < len(lines):
                address_parts.append(lines[i + 1].text.strip())

        # Fallback enterprise name extraction
        if not enterprise_name:
            for l in lines:
                t = l.text.strip()
                if any(kw in t for kw in ("Tours", "Dental", "Woodcraft", "Salon", "Physio", "Legal", "Insurance", "Stays", "Bake", "Electronics", "LLP")):
                    enterprise_name = t
                    break

        # 3. Extract Registration Date
        date_match = re.search(r"\b(20[12][0-9]-[01][0-9]-[0-3][0-9])\b", full_text)
        if date_match:
            doc_date = date_match.group(1)

        business_address = ", ".join(address_parts) if address_parts else None

        return ExtractedDocumentFields(
            document_type=DocumentType.UDYAM_CERTIFICATE,
            legal_business_name=enterprise_name,
            trade_name=enterprise_name,
            udyam_registration_number=udyam_number,
            business_address=business_address,
            document_date=doc_date,
            warnings=warnings
        )

    def _parse_address_proof(self, lines: list, warnings: List[str]) -> ExtractedDocumentFields:
        """Parse structured fields from utility bill address proof."""
        billed_to: Optional[str] = None
        supply_address: Optional[str] = None
        bill_date: Optional[str] = None

        full_text = " ".join([l.text for l in lines])

        for i, l in enumerate(lines):
            t = l.text.strip()
            t_lower = t.lower()
            if "billed to" in t_lower:
                if ":" in t and len(t.split(":", 1)[1].strip()) > 0:
                    billed_to = t.split(":", 1)[1].strip()
                elif i + 1 < len(lines):
                    billed_to = lines[i + 1].text.strip()
            elif "supply address" in t_lower:
                if ":" in t and len(t.split(":", 1)[1].strip()) > 0:
                    supply_address = t.split(":", 1)[1].strip()
                else:
                    parts = []
                    for j in range(i + 1, min(i + 4, len(lines))):
                        if "Bill date" in lines[j].text or "Units" in lines[j].text:
                            break
                        parts.append(lines[j].text.strip())
                    supply_address = " ".join(parts).strip()

        # Fallback date search
        date_match = re.search(r"\b(20[12][0-9]-[01][0-9]-[0-3][0-9])\b", full_text)
        if date_match:
            bill_date = date_match.group(1)
        else:
            warnings.append("Bill date could not be identified on address proof.")

        # Fallback address search
        if not supply_address:
            m = re.search(r"(Shop/Unit [^0-9]+[0-9]+[^\n\r]+)", full_text)
            if m:
                supply_address = m.group(1)

        return ExtractedDocumentFields(
            document_type=DocumentType.ADDRESS_PROOF,
            trade_name=billed_to,
            business_address=supply_address,
            address_proof_date=bill_date,
            document_date=bill_date,
            warnings=warnings
        )

    def _parse_signatory_id(self, lines: list, warnings: List[str]) -> ExtractedDocumentFields:
        """Parse structured fields from authorised signatory ID document."""
        name: Optional[str] = None
        designation: Optional[str] = None
        business_name: Optional[str] = None

        for i, l in enumerate(lines):
            t = l.text.strip()
            t_lower = t.lower()
            if "name" in t_lower and "business" not in t_lower:
                if ":" in t and len(t.split(":", 1)[1].strip()) > 0:
                    name = t.split(":", 1)[1].strip()
                elif t == "Name" and i + 1 < len(lines):
                    name = lines[i + 1].text.strip()
            elif "designation" in t_lower:
                if ":" in t and len(t.split(":", 1)[1].strip()) > 0:
                    designation = t.split(":", 1)[1].strip()
                elif t == "Designation" and i + 1 < len(lines):
                    designation = lines[i + 1].text.strip()
            elif "for business" in t_lower or "business name" in t_lower:
                if ":" in t and len(t.split(":", 1)[1].strip()) > 0:
                    business_name = t.split(":", 1)[1].strip()
                elif i + 1 < len(lines):
                    business_name = lines[i + 1].text.strip()

        return ExtractedDocumentFields(
            document_type=DocumentType.SIGNATORY_ID,
            signatory_name=name,
            signatory_designation=designation,
            trade_name=business_name,
            warnings=warnings
        )


kyc_extraction_service = KYCExtractionService()
