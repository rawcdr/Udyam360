# Udyam360: Phase 3 Pre-Implementation Audit Report

## Project Context
- **Hackathon:** Airtel SYNC Hackathon 2026 — Enterprise Track A (Project Udyam Digital)
- **Phase:** Phase 3 — Smart KYC, Document OCR & Mock Registry Verification
- **Date:** November 2026
- **Status:** COMPLETED & VERIFIED

---

## 1. Phase 1 and Phase 2 Integration Audit

### 1.1. Data Flow from Onboarding / Advisor to KYC
In Phase 2, a conversational onboarding session produces:
- `session_id`: Unique session UUID.
- `ConversationState.profile`: Structured Pydantic model (`ExtractedProfileData`).
- Selected bundle: Recommended bundle (Essential, Growth, Premium) containing product SKUs.
- Optional Quote: Server-generated quote reference (`quote_id`) from `/api/v1/quotes/preview`.

### 1.2. Schema Field Mapping
There is an intentional distinction between conversational extraction (`ExtractedProfileData`) and deterministic recommendation (`BusinessProfile`):

| Conceptual Entity | Phase 2 Extraction (`ExtractedProfileData`) | Phase 1 Profile (`BusinessProfile`) | KYC Application Snapshot Field |
| :--- | :--- | :--- | :--- |
| **Business Name** | `business_name: Optional[str]` | N/A (Lead metadata) | `legal_business_name: str` |
| **Segment** | `segment: Optional[Literal['micro', 'office']]` | `business_segment: CustomerSegment` | `business_segment: str` |
| **Location** | `city: Optional[str]` | `city: str` | `city: str` |
| **City Tier** | `city_tier: Optional[int]` (1 or 2) | `city_tier: CityTier` (`TIER_1`/`TIER_2`)| `city_tier: int` |
| **Premises Count** | `sites_count: Optional[int]` | `num_sites: int` | `num_sites: int` |
| **Staff Count** | `employee_count: Optional[int]` | `employee_count: int` | `employee_count: int` |
| **GSTIN Claim** | `has_gstin: Optional[bool]` | `has_gstin: bool` | `claimed_has_gstin: bool` |
| **Required Products** | `requested_services: List[str]` | `required_services: List[str]` | `selected_product_ids: List[str]` |

**Resolution in Phase 3:**
When a KYC case is created via `POST /api/v1/kyc/cases`, the backend looks up `ConversationService.get_conversation(session_id)`, validates that the profile is complete, and captures a frozen snapshot of the `BusinessProfile` and `selected_product_ids`.

---

## 2. Dataset Conventions & Synthetic Validation Rules

Audit of `YTL_TrackA_Udyam_Digital_Data/README.md` confirmed the following synthetic rules:

1. **Synthetic Reference Date:**
   - **`2026-07-15`** MUST be used as "today" for all deterministic date and freshness checks.
   - The computer's system wall-clock date MUST NEVER be used for document freshness evaluations.
2. **GSTIN Synthetic Convention:**
   - Standard 15-character structure: 2-digit state code + 10-character PAN + 1-digit entity code + `Z` + 1 checksum character.
   - The 4th character of the embedded PAN is always `'X'` (e.g. `37IHKXV5167L1ZS`), intentionally indicating a synthetic non-real taxpayer entity. The validator must explicitly accept `'X'`.
3. **Udyam Synthetic Convention:**
   - Format: `UDYAM-{STATE_CODE}-00-{7_DIGIT_SERIAL}` (e.g. `UDYAM-WB-00-5053330`).
   - The district code is always `'00'`, which does not exist in real Udyam registrations. The validator must accept `'00'`.
4. **Address Proof Freshness Limit:**
   - Address proof documents (electricity bills) must be dated within **90 days** of `2026-07-15` (i.e. on or after `2026-04-16`).
   - Any document dated earlier than `2026-04-16` must be flagged as `STALE_ADDRESS_PROOF`.
5. **Mock GSTIN Statuses:**
   - `Active` (3,266 records in `mock_gstin_registry.csv`): Allowed for KYC activation.
   - `Cancelled` (167 records): Must be flagged as `GSTIN_STATUS_CANCELLED` and prevent automatic verification.
   - `Suspended` (101 records): Must be flagged as `GSTIN_STATUS_SUSPENDED` and sent for manual review.
6. **Product Catalogue GSTIN Requirement:**
   - 10 products (`P03`, `P05`, `P06`, `P10`, `P12`, `P13`, `P14`, `P15`, `P21`, `P24`) require an active GSTIN (`requires_gstin == 'Y'`).
   - 15 products (`P01`, `P02`, `P04`, `P07`, `P08`, `P09`, `P11`, `P16`, `P17`, `P18`, `P19`, `P20`, `P22`, `P23`, `P25`) do NOT require GSTIN.
   - If selected products do not include any GST-mandated product and the customer does not claim GSTIN, a GST certificate is NOT required.

---

## 3. Specimen Document Audit (Applicants K01–K12)

All 47 PNG specimen images in `YTL_TrackA_Udyam_Digital_Data/kyc_documents/` were audited using OCR and registry cross-matching:

| Applicant ID | Entity Name | Doc Count | Files Present | Observed Status & Planted Inconsistencies |
| :--- | :--- | :--- | :--- | :--- |
| **K01** | Vindhya Tours & Travels | 4 | `address_proof`, `gst_certificate`, `signatory_id`, `udyam_certificate` | **Planted Issues:** Udyam certificate is missing the registration number; GSTIN `37IHKXV5167L1ZS` is `Cancelled` in registry. |
| **K02** | Harmony Dental Care | 4 | `address_proof`, `gst_certificate`, `signatory_id`, `udyam_certificate` | **Clean:** GST `19EOGXH4115Y1ZL` (Active), Udyam `UDYAM-WB-00-5053330` (Micro), bill fresh (54 days old). |
| **K03** | Ganesh Woodcraft | 4 | `address_proof`, `gst_certificate`, `signatory_id`, `udyam_certificate` | **Clean:** GST `27XUIXG0767D1ZP` (Active), Udyam `UDYAM-MH-00-9516696` (Manufacturing), bill fresh (46 days old). |
| **K04** | Saffron Dental Care LLP | 4 | `address_proof`, `gst_certificate`, `signatory_id`, `udyam_certificate` | **Planted Issue:** `K04_gst_certificate.png` is heavily blurred/degraded. OCR confidence is low (< 0.60) / unreadable; requires manual review. |
| **K05** | Balaji Realty LLP | 3 | `address_proof`, `gst_certificate`, `signatory_id` | **Planted Issue:** Missing `udyam_certificate` entirely (only 3 files in dataset). |
| **K06** | Saffron Unisex Salon | 4 | `address_proof`, `gst_certificate`, `signatory_id`, `udyam_certificate` | **Clean:** GST `08YKZXS5189L1ZO` (Active), Udyam `UDYAM-RJ-00-6577157`, bill fresh (34 days old). |
| **K07** | Neelgiri Physio Clinic | 4 | `address_proof`, `gst_certificate`, `signatory_id`, `udyam_certificate` | **Clean:** GST `07CPCXN0398P1ZT` (Active), Udyam `UDYAM-DL-00-9565547`, bill fresh (10 days old). |
| **K08** | Green Leaf Legal Associates | 4 | `address_proof`, `gst_certificate`, `signatory_id`, `udyam_certificate` | **Clean:** GST `24XORXG9365M1Z3` (Active), Udyam `UDYAM-GJ-00-8477445`, bill fresh (50 days old). |
| **K09** | Kaveri Insurance Advisors | 4 | `address_proof`, `gst_certificate`, `signatory_id`, `udyam_certificate` | **Clean:** GST `37LDYXK0296F1ZB` (Active), Udyam `UDYAM-AP-00-9751562`, bill fresh (5 days old). |
| **K10** | Kaveri Stays LLP | 4 | `address_proof`, `gst_certificate`, `signatory_id`, `udyam_certificate` | **Clean:** GST `27QHJXK0658U1ZL` (Active), Udyam `UDYAM-MH-00-7183141`, bill fresh (27 days old). |
| **K11** | Trinity Bake House Pvt Ltd | 4 | `address_proof`, `gst_certificate`, `signatory_id`, `udyam_certificate` | **Planted Issue:** Stale address proof! Bill dated `2025-10-31` (257 days old relative to `2026-07-15`, exceeding 90-day limit). |
| **K12** | Star Electronics | 4 | `address_proof`, `gst_certificate`, `signatory_id`, `udyam_certificate` | **Clean:** GST `37NBLXS1145E1ZU` (Active), Udyam `UDYAM-AP-00-5186772`, bill fresh (9 days old). |

---

## 4. OCR Engine Selection & Compatibility Evaluation

### 4.1. Evaluated Engines
1. **Windows Media OCR (`winocr`):**
   - Built into Windows 10/11 OS (`winrt.windows.media.ocr`).
   - Tested on all 47 images: processed entire set in **< 5 seconds** (~0.10s per image).
   - Near 100% extraction accuracy on clean synthetic document images.
   - Zero external model downloads or heavy runtime footprints.
2. **RapidOCR (`rapidocr-onnxruntime`):**
   - PaddleOCR PP-OCRv4 model executed via ONNX Runtime on CPU.
   - Fully cross-platform, ~15MB wheel, no CUDA required.
   - Yields bounding boxes, per-word coordinates, and confidence scores (0.00 – 1.00).
   - Execution latency: ~1.5s – 3.5s per image.

### 4.2. Selected Architecture: Provider Abstraction
To ensure portability across development environments and automated test isolation:
- Implement an abstract `BaseOCRProvider` interface.
- Provide `WinOCRProvider` (default on Windows for speed and accuracy).
- Provide `RapidOCRProvider` (cross-platform ONNX engine).
- Provide `MockOCRProvider` (fixture-based deterministic responses for lightning-fast, reproducible unit tests without any binary dependencies).

