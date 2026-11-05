# Phase 4 — API Integration Audit & Frontend Contract Mapping

**Project:** Udyam360 — Airtel SYNC Hackathon 2026 (Enterprise Track A)  
**Date:** 2026-11-05  
**Status:** Completed  
**Objective:** Audit all backend endpoints from Phases 1, 2, and 3, document exact request/response schemas, identify required frontend integration patterns, and identify missing endpoints required for the customer onboarding journey.

---

## 1. Executive Summary

A comprehensive pre-implementation audit was conducted against the running FastAPI codebase (`backend/app/api/`, `backend/app/schemas/`, and `backend/app/services/`). All documented endpoints from Phases 1, 2, and 3 were verified directly in the source code.

### Key Audit Findings:
1. **Advisor Service (Phase 2):** Fully operational. Provides session initialization (`/start`), conversational dialogue processing (`/message`), state retrieval (`/conversation/{id}`), session reset (`/reset/{id}`), and LLM provider health check (`/health`).
2. **Catalogue & Recommendation Engines (Phase 1):** Fully operational. Exposes all 25 products with category filtering, customer segment definitions, hard eligibility checks, deterministic bundle recommendations (Essential, Growth, Premium), and server-authoritative quote previews with decimal arithmetic.
3. **Smart KYC Pipeline (Phase 3):** Fully operational. Exposes case creation linked to advisor sessions, explicit consent recording, secure document upload with magic-byte verification, local OCR extraction, mock GSTIN/Udyam registry cross-verification, and explainable decision status.
4. **Missing Capability (Identified Blocker):** As anticipated in Part 7 of the Phase 4 specification, an **Order Management & Tracking API** (`/api/v1/orders`) is not yet present in the backend. An order lifecycle state machine, order creation endpoint, and order tracking endpoint must be implemented in the backend prior to frontend integration.

---

## 2. Comprehensive Endpoint Audit Matrix

| HTTP Method | Route | Schema / Request Body | Response Model / Payload | Auth / Session | Consuming Frontend View | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | None | `{ "status": "HEALTHY", "service": "...", "version": "...", "catalogue_loaded": true }` | Public | System Health Badge | **Verified** |
| `POST` | `/api/v1/advisor/start` | None | `AdvisorStartResponse` (`conversation_id`, `welcome_message`, `suggested_prompts`) | Public (creates session) | `/advisor` | **Verified** |
| `POST` | `/api/v1/advisor/message` | `AdvisorMessageRequest` (`conversation_id`, `message`) | `AdvisorMessageResponse` (`assistant_message`, `extracted_profile`, `missing_fields`, `clarification_required`, `recommendations_available`, `recommendations`, `processing_status`) | Session ID | `/advisor` | **Verified** |
| `GET` | `/api/v1/advisor/conversation/{id}` | Path: `conversation_id` | `ConversationState` (`conversation_id`, `profile`, `history`, `missing_fields`, `turn_count`, `recommendations_available`, `last_recommendations`, `status`) | Session ID | `/advisor` (state recovery) | **Verified** |
| `POST` | `/api/v1/advisor/reset/{id}` | Path: `conversation_id` | `{ "status": "RESET_SUCCESSFUL", "conversation_id": "...", "message": "..." }` | Session ID | `/advisor` (Restart button) | **Verified** |
| `GET` | `/api/v1/advisor/health` | None | `{ "advisor_enabled": true, "llm_provider": "gemini", "configured_model": "...", "api_key_configured": true, "max_history_turns": 10, "status": "HEALTHY" }` | Public | System Health Badge | **Verified** |
| `GET` | `/api/v1/catalogue` | Query: `category` (optional) | `List[Product]` (all 25 products or filtered) | Public | `/recommendations`, Catalogue Drawer | **Verified** |
| `GET` | `/api/v1/catalogue/summary` | None | `CatalogueSummary` (counts, unit distributions, price ranges) | Public | Landing Page / Catalogue Stats | **Verified** |
| `GET` | `/api/v1/catalogue/{id}` | Path: `product_id` | `Product` (complete product specifications) | Public | Product Detail Modal | **Verified** |
| `GET` | `/api/v1/segments` | None | `List[Dict]` (supported segments: micro, prof, multi, mfg) | Public | Landing Page, Segment Guides | **Verified** |
| `POST` | `/api/v1/eligibility/check` | `BusinessProfile` | `EligibilityCheckResponse` (`eligible_products`, `ineligible_products`, `needs_information`) | Public | Dynamic add-on validator | **Verified** |
| `POST` | `/api/v1/recommendations` | `BusinessProfile` | `RecommendationResponse` (`bundles`: Essential, Growth, Premium; `profile_summary`, `catalog_version`) | Public | `/recommendations` | **Verified** |
| `POST` | `/api/v1/quotes/preview` | `QuotePreviewRequest` (`profile`, `selected_product_ids`, `bundle_tier`, `quantity_overrides`) | `QuotePreviewResponse` (`quote_id`, `business_segment`, `bundle_tier`, `is_eligible`, `eligibility_issues`, `pricing` with MRC, OTC, estimated first month, itemized lines, `typical_install_days`, `min_contract_months`, `terms_and_conditions`) | Public | `/recommendations` (interactive add-on preview), `/quote` | **Verified** |
| `POST` | `/api/v1/kyc/cases` | `KYCCaseCreateRequest` (`advisor_session_id`, `selected_product_ids`, `quote_reference`) | `KYCCaseResponse` (`kyc_case_id`, `advisor_session_id`, `quote_reference`, `application_status`, `required_documents`, `created_at`, `business_profile`) | Session ID | `/kyc` (Case Init) | **Verified** |
| `GET` | `/api/v1/kyc/cases/{id}` | Path: `case_id` | `KYCCaseResponse` | Case ID | `/kyc` (State Recovery) | **Verified** |
| `POST` | `/api/v1/kyc/cases/{id}/consent` | `ConsentRequest` (`consent_granted: bool`, `consent_version: str`) | `ConsentRecord` (`case_id`, `consent_granted`, `consent_version`, `timestamp`, `ip_address`, `status`) | Case ID | `/kyc` (Step 1 Consent Gate) | **Verified** |
| `POST` | `/api/v1/kyc/cases/{id}/documents` | Form-data: `document_type`, File: `file` (PNG, JPG, PDF up to 10MB) | `KYCDocumentMetadata` (`document_id`, `case_id`, `document_type`, `original_filename`, `detected_mime`, `sha256_hash`, `file_size_bytes`, `uploaded_at`) | Case ID | `/kyc` (Step 2 Uploads) | **Verified** |
| `GET` | `/api/v1/kyc/cases/{id}/documents` | Path: `case_id` | `List[KYCDocumentMetadata]` | Case ID | `/kyc` (Document list) | **Verified** |
| `POST` | `/api/v1/kyc/cases/{id}/process` | Path: `case_id` | `KYCValidationResult` (`kyc_case_id`, `overall_status`, `checks_passed`, `checks_failed`, `warnings`, `registry_match`, `freshness_valid`, `manual_review_required`, `review_reasons`, `explanation`, `processed_at`) | Case ID | `/kyc` (Verification Action) | **Verified** |
| `GET` | `/api/v1/kyc/cases/{id}/status` | Path: `case_id` | `{ "kyc_case_id": "...", "application_status": "...", "consent_recorded": true, "documents_count": N, "manual_review_required": bool, "review_reasons": [...], "explanation": "..." }` | Case ID | `/kyc/status`, Order tracking | **Verified** |
| `GET` | `/api/v1/kyc/cases/{id}/validation` | Path: `case_id` | `KYCValidationResult` | Case ID | `/kyc/status` | **Verified** |
| `POST` | `/api/v1/orders` | `OrderCreateRequest` | `OrderResponse` | Required for Part 7 | `/order/confirmation` | **Missing — To Implement** |
| `GET` | `/api/v1/orders/{order_id}` | Path: `order_id` | `OrderResponse` | Order ID | `/track-order` | **Missing — To Implement** |
| `GET` | `/api/v1/orders/{order_id}/timeline` | Path: `order_id` | `OrderTimelineResponse` | Order ID | `/track-order` | **Missing — To Implement** |
| `GET` | `/api/v1/orders/track/{reference}` | Path: `order_reference` | `OrderResponse` | Order Reference | `/track-order` (Public lookup) | **Missing — To Implement** |
| `POST` | `/api/v1/orders/{order_id}/advance` | Path: `order_id` | `OrderResponse` | Order ID | `/track-order` (Simulation Demo) | **Missing — To Implement** |

---

## 3. Detailed Schema Mapping & Translation Rules

### 3.1 Advisor to Recommendations & Quote Transition
- **Advisor Session State:** Returns `profile: BusinessProfile` with fields:
  - `business_name: Optional[str]`
  - `business_type: Optional[str]` (e.g., `"Pharmacy"`, `"CA Firm"`)
  - `segment: Optional[str]` (`"micro"`, `"prof"`, `"multi"`, `"mfg"`)
  - `sites_count: int` (default 1)
  - `num_employees: Optional[int]`
  - `city: Optional[str]`, `city_tier: Optional[int]`
  - `gstin_available: Optional[bool]`, `udyam_available: Optional[bool]`
  - `budget_monthly: Optional[float]`
  - `requested_services: List[str]`
- **Recommendation Invocation:** The frontend passes this exact `profile` object to `POST /api/v1/recommendations`.
- **Add-on Modification:** When users select additional catalogue products on the `/recommendations` page, the frontend calls `POST /api/v1/quotes/preview` passing `{ profile, selected_product_ids, bundle_tier }`. The backend recalculates exact decimal pricing, installation turnaround, and terms.
- **Rule:** The frontend **never** calculates or estimates pricing client-side. The backend is the single authoritative source of truth.

### 3.2 Quote to KYC Case Transition
- `POST /api/v1/kyc/cases` expects:
  ```json
  {
    "advisor_session_id": "conv-...",
    "selected_product_ids": ["P01", "P03", "P14"],
    "quote_reference": "Q-ABC12345"
  }
  ```
- The backend initializes the case, validates product dependencies, and dynamically returns `required_documents`.
- **Dynamic Documents Rule:**
  - Micro Retail without GSTIN requires `UDYAM_CERTIFICATE` or `TRADE_LICENSE` + `ADDRESS_PROOF` + `SIGNATORY_ID`.
  - Professional office or businesses with GSTIN requires `GST_CERTIFICATE` + `ADDRESS_PROOF` + `SIGNATORY_ID`.
  - The UI inspects `case.required_documents` and renders upload cards dynamically.

### 3.3 KYC to Order Transition
- Once KYC processing completes (`VERIFIED` or `PENDING_REVIEW` with manual review acknowledgment), the customer can finalize the order.
- The order links:
  - `quote_reference`: From `/quotes/preview`
  - `kyc_case_id`: From `/kyc/cases`
  - `advisor_session_id`: From `/advisor/start`
  - `customer_details`: Business name, contact, city, segment
  - `product_ids`: Final selected products
  - `pricing_snapshot`: Final monthly recurring charges, one-time charges, total estimated first month
- Unique customer order reference format: `UDYAM-ORD-<YEAR>-<HEX8>` (e.g., `UDYAM-ORD-2026-A1B2C3D4`).

---

## 4. Part 7 Order Lifecycle Architecture & State Machine

To fulfill the requirements of Part 7, the following backend architecture will be implemented:

### 4.1 Order Lifecycle States (`OrderState` Enum)
```text
  QUOTE_CONFIRMED
        │
        ▼
   KYC_PENDING
        │
        ▼
KYC_VERIFICATION
        │
        ├──────────────────► MANUAL_REVIEW (if flag raised, e.g. OCR mismatch)
        │                          │
        │                          ▼ (approved)
        ▼
   KYC_VERIFIED
        │
        ▼
 ORDER_PROCESSING (Simulated provisioning initiated)
        │
        ▼
ACTIVATION_IN_PROGRESS (Simulated field dispatch / SIM & router shipment)
        │
        ▼
    ACTIVATED (Simulated live telecom services active)
```

### 4.2 State Machine Transition Rules
1. `QUOTE_CONFIRMED` -> `KYC_PENDING`: Triggered on initial order placement.
2. `KYC_PENDING` -> `KYC_VERIFICATION`: Triggered when KYC documents are submitted for processing.
3. `KYC_VERIFICATION` -> `KYC_VERIFIED`: Auto-transition if KYC result is `VERIFIED`.
4. `KYC_VERIFICATION` -> `MANUAL_REVIEW`: Transition if KYC result requires manual review.
5. `MANUAL_REVIEW` -> `KYC_VERIFIED`: Manual administrative review approval.
6. `KYC_VERIFIED` -> `ORDER_PROCESSING`: Order dispatched to provisioning engine.
7. `ORDER_PROCESSING` -> `ACTIVATION_IN_PROGRESS`: Site readiness verified, hardware dispatched.
8. `ACTIVATION_IN_PROGRESS` -> `ACTIVATED`: Line activation completed.
9. Invalid transitions (e.g. `KYC_PENDING` -> `ACTIVATED`) are rejected with `400 Bad Request`.

---

## 5. Security & Privacy Guarantees

1. **Zero Cloud Leakage:** All KYC documents, uploaded bytes, and extracted PII remain exclusively on the local server in secure storage (`backend/storage/kyc_documents`). No document content, Aadhaar numbers, or GSTINs are ever transmitted to Gemini or external APIs.
2. **Masked Registry Displays:** Registry responses mask sensitive identifiers before displaying in the UI (e.g., `33*****1234*1Z*`).
3. **Frontend Token & Secrets Isolation:** No Gemini API keys or internal secrets are passed to or stored in frontend environment variables. Frontend only talks to `http://127.0.0.1:8000/api/v1`.
4. **CORS:** FastAPI CORS middleware is enabled for local origins (`localhost:5173`, `127.0.0.1:5173`).

---

## 6. Implementation Action Plan

1. **Step 1:** Implement backend `OrderService`, `Order` schemas, and `orders.py` API router. Add PyTest regression suite.
2. **Step 2:** Scaffold React + TypeScript + Vite frontend in `frontend/` directory with Tailwind CSS and Lucide icons.
3. **Step 3:** Implement centralized typed API client and domain-specific API modules (`advisor.ts`, `catalogue.ts`, `recommendations.ts`, `quotes.ts`, `kyc.ts`, `orders.ts`).
4. **Step 4:** Build frontend pages: Landing Page, AI Business Advisor, Recommendations & Catalogue, Quote Review, Smart KYC flow, Order Confirmation & Status Tracker.
5. **Step 5:** Write frontend component & flow tests (Vitest + React Testing Library).
6. **Step 6:** Capture execution evidence, screenshots, and compile `docs/phase-reports/phase_4_report.md`.

