# Udyam360 — Phase 6.1 Discrepancy Audit & Evidence Reconciliation

**Project:** Udyam360 — Airtel SYNC Hackathon 2026 (Enterprise Track A, Project Udyam Digital)  
**Document:** `docs/phase-reports/phase_6_1_discrepancy_audit.md`  
**Date:** November 6, 2026  
**Status:** **AUTHORITATIVE EVIDENCE AUDIT**

---

## 1. Executive Summary

This discrepancy audit reviews and reconciles all project artifacts, evaluation outputs, model metrics, bundle sizes, screenshots, and presentation text against actual implementation evidence in the Udyam360 repository.

Every discrepancy identified below is traceable to source code, serialized model artifacts (`backend/models/`), test logs, or build outputs.

---

## 2. Audit Findings & Discrepancy Register

### 2.1 Machine Learning Metrics Discrepancy

| Metric Dimension | Presentation (.pptx) | Demo Script (.md) | Previous Checklist (.md) | Authoritative Evidence (`backend/models/`) | Resolution & Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Calibrated Test Brier Score** | 0.0666 | 0.0666 | 0.0898 *(Error)* | **0.0666** (`model_metadata.json` line 49) | Correct checklist and reports to **0.0666**. The 0.0898 was an errant copy-paste typo. |
| **Raw Model Test Brier Score** | 0.2136 | 0.2136 | 0.2136 | **0.2136** (`model_metadata.json` line 40) | Retain 0.2136 as raw uncalibrated score explaining balanced weighting. |
| **Naive Prevalence Baseline** | 0.0680 | 0.0680 | 0.0680 | **0.0680** ($p(1-p) = 0.0733 \times 0.9267$) | Retain 0.0680. Calibrated model (0.0666) beats naive baseline. |
| **Held-out Test ROC-AUC** | 0.6692 | 0.6692 | 0.6692 | **0.6692** (Raw) / **0.6662** (Calibrated) | Explicitly document raw ranking AUC vs calibrated AUC. |
| **Held-out Test PR-AUC** | 0.1327 | 0.1327 | 0.1327 | **0.1327** (Raw) / **0.1292** (Calibrated) | Authoritative test PR-AUC confirmed. |
| **Eligible Lead Count** | 4,632 | 4,632 | 4,632 | **4,632** unconverted leads | 368 already-activated accounts strictly quarantined. |
| **High Propensity Band ($\ge 70\%$)** | 569 (12.3%) | 569 | 569 | **569 leads** (12.28%) | Authoritative band count confirmed. |
| **Medium Propensity Band ($40–70\%$)**| 1,564 (33.8%)| 1,564 | 1,564 | **1,564 leads** (33.77%) | Authoritative band count confirmed. |
| **Low Propensity Band ($< 40\%$)** | 2,499 (54.0%)| 2,499 | 2,499 | **2,499 leads** (53.95%) | Authoritative band count confirmed. |

---

### 2.2 Frontend Production Build & Bundle Metrics

| Bundle Dimension | Previous Claim | Actual Build Output (`npm run build`) | Discrepancy & Correction |
| :--- | :--- | :--- | :--- |
| **Main Customer JS Bundle** | 327.99 kB raw | **329.89 kB** raw ( **99.31 kB** gzip ) | Update to exact Vite build: 329.89 kB raw, 99.31 kB gzip. |
| **Main Customer CSS Bundle** | Unspecified | **39.71 kB** raw ( **7.01 kB** gzip ) | Document explicit CSS size. |
| **Total Initial Payload** | Unspecified | **369.60 kB** raw ( **106.32 kB** gzip ) | State both raw and gzip figures clearly. |
| **Admin Analytics Chunk** | ~372 kB | **372.13 kB** raw ( **108.83 kB** gzip ) | Isolated via Rollup code-splitting to `/admin` routes only. |
| **Pre-Split Customer Bundle** | 764.2 kB raw | **764.20 kB** raw ( ~225 kB gzip ) | Confirmed **56.8% raw reduction** in customer-facing bundle. |

---

### 2.3 Historical Funnel & Business Metrics

| Metric | Hackathon Baseline (`smb_leads.csv`) | Discrepancy in Prior Drafts | Authoritative Grounding |
| :--- | :--- | :--- | :--- |
| **Total Leads** | 5,000 | None | 5,000 historical MSME records. |
| **Contacted** | 3,406 (68.12%) | None | 3,406 reached by sales. |
| **Needs Assessed** | 1,974 (39.48%) | None | 1,974 completed discovery. |
| **Quotes Accepted** | 861 (17.22%) | Described loosely as "56% drop at quote" | **56.4% drop from Needs Assessed to Quote Accepted** ($(1974 - 861)/1974 = 56.38\%$). |
| **KYC Complete** | 588 (11.76%) | None | 588 submitted complete documents. |
| **Activated Accounts** | 368 (7.36%) | None | 368 active paying customers. |
| **Cycle Time** | **17.6 days average** | Drafts intermittently mentioned "14 days" | Strictly preserve **17.6 days**; do not substitute 14 days. |
| **Customer Acquisition Cost**| **~₹15,000 CAC** | None | Preserve historical baseline; frame 40% reduction as proposed pilot target. |

---

### 2.4 KYC Screenshot Error Investigation (`kyc.png`)

- **Observed Defect:** Existing `kyc.png` displays an error banner: `Failed to initialize KYC case: Input should be a valid string`.
- **Root Cause Analysis:**
  - `KYCCaseCreateRequest` in `backend/app/schemas/kyc.py` defines `advisor_session_id: str` as a mandatory string.
  - When the automated headless screenshot capture opened `http://localhost:5173/kyc` directly in a fresh browser context, `sessionStorage` was empty and `conversationId` was `null`.
  - The client sent `{"advisor_session_id": null}`, triggering a FastAPI Pydantic validation error (`422 Unprocessable Entity`).
  - **OCR provider initialization did not fail:** `WindowsMediaOCR` and `RapidOCR` were both fully functional, but execution never reached the OCR step because the case failed initialization.
- **Remediation Plan:**
  - Pre-initialize a valid advisor session with a realistic MSME profile (`K07` — Shri Physio Clinic in Delhi) prior to opening the KYC page.
  - Test and upload real demo specimen files (`K07_gst_certificate.png`, `K07_udyam_certificate.png`, `K07_address_proof.png`).
  - Verify that explicit consent is recorded before document processing.
  - Execute end-to-end local OCR and mock registry matching.
  - Capture the actual resulting verified state screenshot from the live application.

---

### 2.5 Advisor Screenshot Investigation (`advisor.png`)

- **Observed Defect:** Existing `advisor.png` displays an initial conversation state with only a welcome prompt and empty profile cards.
- **Remediation Plan:**
  - Execute an actual live conversational turn where the MSME owner introduces their business: *"I run Shri Physio Clinic in Delhi with 5 staff and ₹4,500 monthly budget. Need office broadband and business calling."*
  - Receive the backend advisor response with extracted profile attributes (business name, clinic type, Delhi location, headcount 5, budget ₹4,500).
  - Capture the completed advisor dialogue showing the extracted profile and transition button.

---

### 2.6 Architecture Diagram Defects (`submission/final_architecture.png`)

- **Observed Defect:** Horizontal clipping at both edges (left labels truncated, right data store boxes clipped).
- **Remediation Plan:**
  - Update `docs/architecture/final_system_architecture.md` with explicit width margins, node padding, and balanced horizontal layout.
  - Re-render using headless Chrome with a widescreen viewport (1800x1100) ensuring 100% visibility of all components, boundary lines, and arrow endpoints.

---

### 2.7 Presentation & Demo Terminology Corrections

| Location | Existing Phrasing | Required Corrected Phrasing | Rationale |
| :--- | :--- | :--- | :--- |
| Slide 2, Demo Script | "56% drop-off at quote" | **"56.4% drop from Needs Assessed to Quote Accepted"** | Mathematical precision ($(1974 - 861)/1974 = 56.38\%$). |
| Slide 3, Slide 6 | "official products" | **"products from the supplied product catalogue"** | Truthful grounding in hackathon dataset. |
| Slide 3, Slide 4 | "100% transparent pricing" | **"Itemized server-side pricing separating MRC and OTC"** | Precise, non-hyperbolic pricing description. |
| Slide 6 | "micro-services" | **"Modular FastAPI backend services"** | Truthful architectural representation of monolithic ASGI codebase. |
| Slide 7 | "100% Linear Odds Attribution" | **"Interpretable logistic-regression odds ratios"** | Mathematically rigorous description of log-odds ($\beta_i \cdot x_i$). |
| Slide 8, Slide 10 | "Three-minute digital activation" | **"Three-minute prototype onboarding demonstration"** | Real telecom provisioning takes days; activation in demo is simulated. |
| Slide 5, Demo Script | "Immutable order reference" | **"Prototype order reference"** | In-memory UUID string; no distributed blockchain/ledger immutability. |
| Demo Script | Unqualified activation claim | **"Simulated OSS/BSS circuit provisioning"** | Explicit disclosure of simulated hackathon boundary. |

---

### 2.8 Privacy & Statutory Disclosures

- **Statutory Notice:** Maintain the explicit disclosure in `submission/Udyam360_Privacy_Security_Note.pdf` that Udyam360 is a hackathon prototype and is **not certified as fully DPDP Act 2023 compliant**.
- **No Machine-Specific Paths:** Remove all `file:///C:/...` absolute links from `submission/submission_checklist.md`, replacing them with clean repository-relative paths (`submission/`, `docs/`, `scripts/`).

---

## 3. Discrepancy Sign-Off & Next Steps

All 10 audit dimensions have been thoroughly analyzed and documented against actual code and test artifacts. Corrections will now be executed systematically across Parts 2 through 10.

