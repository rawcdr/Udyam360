# Udyam360: Smart KYC & Document Verification Architecture

## 1. System Overview

The **Udyam360 Smart KYC subsystem** bridges conversational business onboarding (Phase 2) with deterministic regulatory verification. It processes applicant document images (GST certificates, Udyam certificates, utility bills, and signatory IDs) using local, privacy-preserving Optical Character Recognition (OCR), cross-document semantic matching, and synthetic mock registry lookups.

### Architectural Principle: Zero External Cloud OCR / Zero Gemini Leakage

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ADVISOR ONBOARDING (PHASE 2)                    │
│  - Conversation State & BusinessProfile Snapshot                      │
│  - Selected Product IDs (e.g., P01, P03, P16)                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ Creates KYC Case
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   SMART KYC PIPELINE (PHASE 3)                         │
│                                                                        │
│   [Consent Gate] ──► [Secure Storage] ──► [Local OCR Engine]           │
│   (KYCConsent)       (Path Isolation)     (WinMediaOCR / RapidOCR)     │
│                             │                       │                  │
│                             ▼                       ▼                  │
│                     [Pillow Sniffer]      [Field Normalizer]           │
│                     (PNG/JPEG verify)     (GSTIN/Udyam Regex)          │
│                                                     │                  │
│                                                     ▼                  │
│                    ┌──────────────────────────────────────────────┐    │
│                    │     DETERMINISTIC VERIFICATION ENGINES       │    │
│                    │  - Mock GST Registry (Active/Cancelled)      │    │
│                    │  - Mock Udyam Registry (Micro/Small)         │    │
│                    │  - Freshness Checker (90d vs 2026-07-15)     │    │
│                    │  - Cross-Document Entity Similarity (>=0.75) │    │
│                    └──────────────────────┬───────────────────────┘    │
└───────────────────────────────────────────┼────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        EXPLAINABLE OUTCOME                             │
│   - VERIFIED: All mandatory checks pass cleanly                        │
│   - PENDING_REVIEW: Low OCR conf, minor name variants, suspended GSTIN │
│   - MISSING_DOCUMENTS: Mandatory documents unsubmitted                 │
│   - REJECTED: Confirmed cancelled GSTIN status in registry             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. End-to-End Orchestration Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as Applicant / Agent
    participant API as KYC API (/api/v1/kyc)
    participant Orch as KYCOrchestrator
    participant State as ConversationService
    participant Consent as KYCConsentService
    participant Store as KYCStorageService
    participant OCR as KYCExtractionService (Local OCR)
    participant Reg as RegistryVerificationService
    participant Val as KYCValidationService

    User->>API: POST /cases {advisor_session_id, selected_product_ids}
    API->>Orch: create_case(session_id, products)
    Orch->>State: get_conversation(session_id)
    State-->>Orch: conv_state.profile
    Orch->>Val: determine_required_documents(profile, products)
    Val-->>Orch: required_document_types
    Orch-->>API: KYCCaseResponse (case_id, required_docs)
    API-->>User: 201 Created

    User->>API: POST /cases/{id}/consent {consent_granted: true}
    API->>Consent: record_consent(case_id, true)
    Consent-->>API: ConsentRecord
    API-->>User: 200 OK

    loop For each document
        User->>API: POST /cases/{id}/documents (file, document_type)
        API->>Store: validate_file & save_document(case_id, file)
        Store-->>API: document_id, internal_path
        API-->>User: 201 Created (KYCDocumentMetadata)
    end

    User->>API: POST /cases/{id}/process
    API->>Orch: process_kyc(case_id)
    Orch->>Consent: is_consent_active(case_id)
    alt Consent Not Active
        Consent-->>Orch: False
        Orch-->>API: PENDING_REVIEW (Consent Missing)
    else Consent Active
        loop For each uploaded document
            Orch->>Store: read_document_bytes(doc_id)
            Orch->>OCR: extract_document_fields(bytes, doc_type)
            OCR-->>Orch: ExtractedDocumentFields, OCRResult
        end
        Orch->>Reg: verify_gstin(extracted_gstin)
        Reg-->>Orch: RegistryVerificationResult (Active / Cancelled / Suspended)
        Orch->>Reg: verify_udyam(extracted_udyam)
        Reg-->>Orch: RegistryVerificationResult (Micro / Small)
        Orch->>Val: validate_document_freshness(bill_date, "2026-07-15")
        Val-->>Orch: FreshnessCheckResult (age <= 90d)
        Orch->>Val: compare_entities(extracted_fields, profile_name)
        Val-->>Orch: CrossDocumentConsistencyResult
        Orch-->>API: KYCValidationResult (VERIFIED / REVIEW / REJECTED)
        API-->>User: Structured explainable verification report
    end
```

---

## 3. Subsystem Component Breakdown

### 3.1. Provider-Abstracted Local OCR Engine (`app/services/ocr/`)
- **`BaseOCRProvider` (`ocr/base.py`):** Abstract interface standardizing `extract_text(image_input, preprocess=True) -> OCRResult`.
- **`WinOCRProvider` (`ocr/local_ocr.py`):** Primary Windows 10/11 engine leveraging `winrt.windows.media.ocr`. Delivers sub-200ms processing with zero model downloads.
- **`RapidOCRProvider` (`ocr/local_ocr.py`):** Cross-platform fallback utilizing PaddleOCR PP-OCRv4 ONNX model on CPU.
- **`MockOCRProvider` (`ocr/local_ocr.py`):** Fast, deterministic provider for automated CI/CD testing.
- **`preprocessing.py`:** Applies Pillow-based grayscale conversion, adaptive contrast enhancement (factor 1.5), size scaling (> 1000px), and sharpening filters.

### 3.2. Secure Local Document Storage (`app/services/kyc_storage_service.py`)
- **Directory Isolation:** Files stored under `backend/storage/kyc_documents/{case_id}/`.
- **Sanitization:** User filenames stripped of directory traversal tokens (`..`, `/`, `\`); stored under unique UUIDs (`DOC-XXXXXXXXXXXX.png`).
- **Binary Validation:** Checks MIME magic bytes (`PNG`, `JPEG`, `PDF`) and structural Pillow integrity.

### 3.3. Document Extraction & Field Parsing (`app/services/kyc_extraction_service.py`)
- **GST Certificate Parser:** Normalizes 15-character Indian synthetic GSTINs (allowing embedded PAN 4th character `'X'`); extracts Legal Name, Trade Name, Address, and Liability Date.
- **Udyam Certificate Parser:** Normalizes `UDYAM-XX-00-XXXXXXX` (allowing synthetic district code `'00'`); extracts Enterprise Name, Address, and Registration Date.
- **Address Proof Parser:** Extracts Consumer No, Billed To Name, Supply Address, and Bill Date.
- **Signatory ID Parser:** Extracts Authorized Representative Name, Designation, and Business Name.

### 3.4. Mock Registry Verification (`app/services/registry_verification_service.py`)
- **GSTIN Registry (`mock_gstin_registry.csv`):** Lookups across 3,534 records. Enforces status rules:
  - `Active`: Pass.
  - `Cancelled`: Hard Rejection (`GSTIN_STATUS_CANCELLED`).
  - `Suspended`: Human review required (`GSTIN_STATUS_SUSPENDED`).
- **Udyam Registry (`mock_udyam_registry.csv`):** Lookups across 2,723 records verifying enterprise classification (`Micro`, `Small`, `Medium`).

### 3.5. Deterministic Validation & Consistency Engine (`app/services/kyc_validation_service.py`)
- **Catalogue-Aware Requirement Engine:** Dynamically requires `GST_CERTIFICATE` only if selected products mandate it (`requires_gstin == True` in `product_catalogue.csv`) or customer claims GSTIN.
- **Document Freshness:** Enforces the 90-day validity window relative to the synthetic baseline date **`2026-07-15`**.
- **Cross-Document Entity Matching:** Applies token and sequence-similarity algorithms across documents (`settings.NAME_SIMILARITY_THRESHOLD = 0.75`, `settings.ADDRESS_SIMILARITY_THRESHOLD = 0.70`).

