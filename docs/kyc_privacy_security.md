# Udyam360: KYC Privacy, Security & Data Governance Architecture

## 1. Privacy Overview & Regulatory Intent

The Udyam360 Smart KYC subsystem handles sensitive business identity documents (GST Registration Certificates, Udyam MSME Certificates, Utility Address Proofs, and Authorised Signatory Identification). 

In compliance with Indian data privacy expectations and the **Digital Personal Data Protection Act (DPDP Act 2023)**, the architecture operates under four strict security axioms:
1. **Zero External LLM Leakage:** KYC documents and extracted identity records are **NEVER** sent to Google Gemini or any external cloud LLM API.
2. **Local, Air-Gapped OCR Processing:** Optical character recognition executes purely locally on CPU via Windows Media OCR or ONNX Runtime. No document images leave the host environment.
3. **Explicit Consent Gatekeeping:** No OCR extraction or registry verification can occur without prior explicit, time-stamped customer consent.
4. **Synthetic Mock Isolation:** All registry validations run against synthetic offline CSV databases with zero external government network calls.

---

## 2. End-to-End KYC Data Flow & Isolation

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CUSTOMER APPLICATION CLIENT                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ 1. POST /cases {advisor_session_id}
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          KYC ORCHESTRATOR                              │
│  - Snapshots business profile from conversation service               │
│  - Determines required documents based on product catalogue rules      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ 2. POST /cases/{id}/consent (Explicit Consent)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      CONSENT SERVICE (KYCConsentService)               │
│  - Validates consent = True, records version, purpose & timestamp      │
│  - Blockade: If consent withdrawn/declined, ALL processing stops       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ 3. POST /cases/{id}/documents (Multipart Upload)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      STORAGE SERVICE (KYCStorageService)               │
│  - Magic number binary verification (PNG, JPEG, PDF)                   │
│  - Pillow image structure integrity check                              │
│  - Path traversal stripping (UUID filename generation)                 │
│  - Isolated folder storage: backend/storage/kyc_documents/{case_id}/   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ 4. POST /cases/{id}/process (Local Execution)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   LOCAL OCR & EXTRACTION SERVICE                       │
│  - Preprocessing: Grayscale, contrast enhancement, sharpening          │
│  - Local CPU OCR (WindowsMediaOCR / RapidOCR ONNX)                     │
│  - Structured field normalization (15-char GSTIN, UDYAM-XX-00-XXXXXXX) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ 5. Deterministic Verification
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    REGISTRY & VALIDATION SERVICES                      │
│  - Mock GSTIN Lookup (Active, Cancelled, Suspended)                    │
│  - Mock Udyam Lookup (Micro, Small, Medium)                            │
│  - Document Freshness Check (90-day limit vs 2026-07-15)               │
│  - Cross-Document Entity Similarity (Normalized Levenshtein / Token)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ 6. Explainable Decision (VERIFIED / PENDING_REVIEW / REJECTED)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI RESPONSE LAYER                         │
│  - Masked identifiers (e.g. 37IH***1ZS, UDYAM-WB***3330)               │
│  - Internal file paths strictly hidden                                 │
│  - Zero raw OCR dumps in standard API responses                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Storage Security & File Integrity Controls

### 3.1. Directory Partitioning & Access Control
- All uploaded documents are stored in `backend/storage/kyc_documents/{kyc_case_id}/`.
- Stored files are **strictly outside** any publicly served web server or static frontend folder.
- There is no unauthenticated public file download endpoint. Internal file paths are never exposed in JSON responses.

### 3.2. Filename Sanitization & Path Traversal Prevention
- Uploaded filenames are scrubbed using `sanitize_filename()` to remove directory separators (`..`, `/`, `\`) and non-alphanumeric characters.
- Files are saved under server-generated UUID identifiers (`DOC-XXXXXXXXXXXX.png`), discarding user-supplied filesystem names.
- File paths are validated with `resolve()` to ensure they remain inside the root storage directory.

### 3.3. Deep Content Sniffing & Anti-Malware Validation
Before writing to disk:
1. **Size Limitation:** Rejects payloads exceeding `settings.KYC_MAX_FILE_SIZE_BYTES` (10 MB).
2. **Magic Byte Inspection:** Inspects binary headers against known MIME signatures:
   - PNG: `\x89PNG\r\n\x1a\n`
   - JPEG: `\xff\xd8\xff`
   - PDF: `%PDF`
3. **Pillow Structural Verification:** Executes `Image.open().verify()` to detect corrupted, truncated, or polyglot files before processing.

---

## 4. Privacy & Masking Standards

### 4.1. Sensitive Identifier Masking
Identifiers displayed in API responses and application logs are masked to protect applicant confidentiality:
- **GSTIN Masking:** First 4 characters and last 3 characters preserved; middle 8 characters masked (e.g. `37IH***1ZS`).
- **Udyam Masking:** State code prefix and last 4 serial digits preserved; middle characters masked (e.g. `UDYAM-WB***3330`).
- **Consumer Number Masking:** Preserves only terminal digits (e.g. `******7625`).

### 4.2. Logging Sanitization
- Full GSTIN, PAN, and Udyam values are **never logged** in plaintext logs.
- Document binary contents and full OCR text dumps are excluded from standard server logging.

---

## 5. Consent Management & Withdrawal

### 5.1. Explicit Precondition
- The KYC Orchestrator explicitly validates `kyc_consent_service.is_consent_active(case_id)` prior to invoking OCR extraction or mock registry lookups.
- If consent has not been recorded, the pipeline halts immediately with status `PENDING_REVIEW` and failure code `CONSENT_MISSING`.

### 5.2. Consent Withdrawal
- Customers may withdraw consent at any time via `kyc_consent_service.withdraw_consent(case_id)`.
- Withdrawing consent immediately halts all automated processing and flags the case as requiring manual closure.

### 5.3. Development vs. Production Retraction
- For local development and hackathon evaluation, calling `DELETE /api/v1/kyc/cases/{case_id}` completely purges uploaded document bytes from disk and removes in-memory metadata.

---

## 6. Explainability & Human-in-the-Loop Safeguards

1. **No Automatic Rejection on Low OCR Confidence:**
   - A degraded or blurry image (e.g. `K04_gst_certificate.png`) produces low confidence (< 0.60).
   - The engine flags `LOW_OCR_CONFIDENCE` and transitions the case to `PENDING_REVIEW` for human visual inspection. It **never** rejects the customer outright.
2. **Technical Failure Resilience:**
   - Technical failures (e.g. missing registry file or engine timeout) return controlled error states, preserving the application for retry.
3. **Definitive Rejections Restricted to Confirmed Fraud/Cancellation:**
   - Automatic `REJECTED` status is restricted to confirmed statutory invalidity, specifically `GSTIN_STATUS_CANCELLED` verified against official mock registries.

---

## 7. Production Deployment Roadmap

In a production enterprise deployment, the following enhancements would supersede local development components:
1. **Encrypted Object Storage:** Migrate from local filesystem storage to AWS S3 / GCP Cloud Storage with SSE-KMS (Server-Side Encryption with Customer Managed Keys) and bucket policies blocking public access.
2. **Database Persistence:** Transition in-memory case and consent registries to PostgreSQL with column-level encryption (e.g. `pgcrypto` or AWS KMS envelope encryption) for PII.
3. **Automated Document Retention / TTL:** Configure automated S3 Lifecycle Rules or scheduled cron jobs purging document files 30 days post-activation, retaining only compliance hash digests.

