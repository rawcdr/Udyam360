# Udyam360: AI-Powered Digital Onboarding Platform for Indian MSMEs

Udyam360 is an enterprise-grade digital onboarding platform tailored for Indian Micro, Small, and Medium Enterprises (MSMEs), built for the **Airtel SYNC Hackathon 2026 — Enterprise Track A (Project Udyam Digital)**.

---

## 1. Project Introduction

Indian MSMEs form the backbone of the economy but struggle with complex digital adoption, fragmented telecom and SaaS procurements, lengthy paperwork, and opaque onboarding pipelines. In the baseline dataset, only **7.36% of leads successfully activate**, taking an average of **17.6 days** and multiple follow-up calls with high customer drop-offs at needs assessment and KYC stages.

**Udyam360** re-architects this journey by introducing a frictionless, AI-assisted onboarding funnel:
- Conversational MSME Business Advisory powered by Google Gemini.
- Intelligent product bundle recommendation engine enforcing eligibility and dependency rules.
- Real-time GSTIN and Udyam registry verification.
- Smart KYC pipeline with automated document fraud detection and OCR verification.
- Transparent end-to-end order tracking.
- Executive analytics dashboard with ML-powered lead propensity scoring.

---

## 2. Hackathon Problem Statement Summary

- **Track:** Enterprise Track A — Project Udyam Digital (Airtel SYNC Hackathon 2026).
- **Core Challenge:** Simplify and compress the multi-week enterprise customer acquisition and onboarding journey for Indian small businesses into a self-service, intelligent, and compliant digital experience.
- **Key Milestones:**
  - Slash customer activation cycle time from ~17.6 days to near instant self-onboarding.
  - Automate compliance verification against synthetic GSTIN and Udyam registries.
  - Provide personalized product bundle quotes based on business size, segment, and location constraints.
  - Maintain data privacy and prevent fraud during document onboarding.

---

## 3. Target Customer Segments

Udyam360 targets two core MSME sectors representing **79.12%** of the SMB market base:

1. **Micro Retail & Services** (54.18% of leads in dataset)
   - *Archetypes:* Kirana stores, neighborhood pharmacies, salons, hardware stores, boutique retail.
   - *Key Needs:* Affordable high-speed broadband, UPI/digital payment terminals, cloud billing, basic security surveillance.
2. **Professional Offices** (24.94% of leads in dataset)
   - *Archetypes:* Medical clinics, chartered accountants (CA) firms, coaching centres, legal consultancies, architectural studios.
   - *Key Needs:* Dedicated leased-line / office internet, collaboration suites (Google Workspace / M365), cybersecurity, IP telephony.

---

## 4. Technology Stack

- **Backend:** Python 3.13.7, FastAPI, Uvicorn, Pydantic v2
- **GenAI / LLM:** Google Gemini Developer API (`google-genai` SDK v2.34.0), utilizing `gemini-3.1-flash-lite` (free-tier preference)
- **Data & ML:** Pandas, NumPy, Scikit-Learn, OpenPyXL
- **Testing & Tooling:** PyTest, HTTPX, Pillow, Python-Dotenv, Vitest, React Testing Library
- **Hardware Acceleration:** Windows 11, Intel Core i5-12450H, 16GB RAM, NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM)
- **Frontend (Phase 4):** React 18, TypeScript, Tailwind CSS, Vite 5, React Router v6, Axios, Lucide React

---

## 5. Project Directory Structure

```
Udyam360/
│
├── YTL_TrackA_Udyam_Digital_Data/   # Verified Hackathon Dataset (Preserved & Unmodified)
│   ├── kyc_documents/               # 47 KYC specimen images across 12 applicants
│   ├── mock_gstin_registry.csv      # 3,534 mock GST records
│   ├── mock_udyam_registry.csv      # 2,723 mock Udyam records
│   ├── product_catalogue.csv        # 25 products with eligibility & dependency rules
│   ├── smb_leads.csv                # 5,000 SMB lead funnel records
│   └── README.md                    # Dataset conventions and synthetic rules
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI application entrypoint & middleware
│   │   ├── api/                     # REST API routers
│   │   │   ├── __init__.py
│   │   │   ├── advisor.py           # GenAI Conversational Advisor endpoints
│   │   │   ├── admin.py             # Executive Admin & ML Analytics endpoints
│   │   │   ├── catalogue.py         # Product catalogue endpoints
│   │   │   ├── eligibility.py       # Eligibility evaluation endpoint
│   │   │   ├── kyc.py               # Smart KYC & Document Verification endpoints
│   │   │   ├── orders.py            # Order management and lifecycle endpoints
│   │   │   ├── quotes.py            # Server-side quote preview endpoint
│   │   │   ├── recommendations.py   # Multi-tier bundle recommendation endpoint
│   │   │   └── segments.py          # Customer segments endpoints
│   │   ├── ml/                      # Zero-leakage ML lead propensity package
│   │   │   ├── explainability.py    # Log-odds attribution & business explainer
│   │   │   ├── feature_engineering.py # Allowlist feature selection & leakage quarantine
│   │   │   ├── inference.py         # Calibrated propensity inference & stage plays
│   │   │   ├── model_registry.py    # Model metadata & evaluation report loader
│   │   │   ├── preprocessing.py     # Scikit-learn ColumnTransformer pipeline
│   │   │   └── train.py             # Stratified benchmark trainer (LR, RF, HGB)
│   │   ├── core/                    # App configuration and core settings
│   │   │   ├── __init__.py
│   │   │   └── config.py            # Centralized project settings & paths
│   │   ├── schemas/                 # Pydantic data schemas
│   │   │   ├── __init__.py
│   │   │   ├── advisor.py           # Conversational profile extraction & message models
│   │   │   ├── business_profile.py  # Customer business profile models
│   │   │   ├── catalogue.py         # Product & catalogue summary models
│   │   │   ├── eligibility.py       # Eligibility evaluation models
│   │   │   ├── kyc.py               # KYC application, document, and validation models
│   │   │   ├── pricing.py           # Breakdown & contract pricing models
│   │   │   ├── quote.py             # Quote preview request/response models
│   │   │   └── recommendation.py    # Bundle recommendation & scoring models
│   │   ├── services/                # Business services & recommendation logic
│   │   │   ├── __init__.py
│   │   │   ├── advisor_dialogue_service.py # Missing field analysis & clarification
│   │   │   ├── advisor_orchestrator.py     # End-to-end advisor coordinator
│   │   │   ├── advisor_response_service.py # Gemini grounded explanation & template fallback
│   │   │   ├── analytics_service.py        # Executive KPI & 6-stage funnel analytics
│   │   │   ├── bundle_explanation.py       # Deterministic bundle rationale service
│   │   │   ├── catalogue_service.py        # Catalogue loading & integrity validator
│   │   │   ├── conversation_service.py     # In-memory session & state merge manager
│   │   │   ├── eligibility_engine.py       # Hard rules & dependency resolution engine
│   │   │   ├── kyc_consent_service.py      # Customer consent capture & withdrawal
│   │   │   ├── kyc_document_service.py     # Document metadata & lifecycle manager
│   │   │   ├── kyc_extraction_service.py   # Document-specific field extractors
│   │   │   ├── kyc_orchestrator.py         # End-to-end KYC coordinator
│   │   │   ├── kyc_storage_service.py      # Secure local file storage & binary sniffing
│   │   │   ├── kyc_validation_service.py   # Freshness, required docs, cross-doc consistency
│   │   │   ├── lead_scoring_service.py     # Propensity scoring, caching & sales audit log
│   │   │   ├── llm_service.py              # Safe Gemini API integration wrapper
│   │   │   ├── model_discovery.py          # Gemini model capability discovery script
│   │   │   ├── ocr/                        # Local OCR provider abstraction package
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py                 # Abstract BaseOCRProvider interface
│   │   │   │   ├── local_ocr.py            # WinOCR, RapidOCR, and MockOCR implementations
│   │   │   │   ├── preprocessing.py        # Grayscale, contrast enhancement, sharpening
│   │   │   │   └── provider.py             # Provider selector factory
│   │   │   ├── pricing_engine.py           # High-precision decimal pricing calculator
│   │   │   ├── profile_extraction_service.py # Gemini structured JSON + regex extractor
│   │   │   ├── registry_verification_service.py # Mock GSTIN and Udyam CSV lookup service
│   │   │   └── segment_service.py          # Segment intelligence & suitability scoring
│   │   └── utils/                   # Shared utility functions
│   │       └── __init__.py
│   │
│   ├── tests/                       # Comprehensive PyTest test suite (109 tests)
│   │   ├── __init__.py
│   │   ├── conftest.py              # Pytest fixtures & quota isolation
│   │   ├── test_advisor_api.py      # Advisor REST API endpoint tests
│   │   ├── test_advisor_guardrails.py # Guardrails, fallbacks & prompt injection tests
│   │   ├── test_advisor_orchestrator.py # Multi-turn orchestration tests (Scenarios A-D)
│   │   ├── test_api.py              # REST API endpoint integration tests
│   │   ├── test_catalogue.py        # Catalogue service unit tests
│   │   ├── test_conversation.py    # Session isolation & state merge tests
│   │   ├── test_eligibility.py      # Hard constraints & dependency tests
│   │   ├── test_kyc_api.py          # KYC REST API endpoint integration tests
│   │   ├── test_kyc_consent.py      # Consent grant, decline, withdrawal tests
│   │   ├── test_kyc_extraction.py   # Document field parsing & normalization tests
│   │   ├── test_kyc_orchestrator.py # KYC pipeline end-to-end workflow tests
│   │   ├── test_kyc_security.py     # File validation, path traversal, isolation tests
│   │   ├── test_kyc_validation.py   # Freshness, requirements, consistency tests
│   │   ├── test_llm_service.py      # LLM service health check unit tests
│   │   ├── test_ocr_service.py      # OCR provider abstraction & preprocessing tests
│   │   ├── test_pricing.py          # Pricing engine unit tests
│   │   ├── test_profile_extraction.py # Dual-mode extraction unit tests
│   │   ├── test_recommendation.py   # Archetype recommendation tests
│   │   └── test_registry_verification.py # Mock GSTIN and Udyam lookup tests
│   ├── test_gemini.py               # Gemini Developer API connectivity test
│   ├── .env                         # Environment secrets (Git-ignored)
│   ├── .env.example                 # Example configuration template
│   └── requirements.txt             # Locked Python dependencies
│
├── frontend/
│   └── README.md                    # Frontend placeholder
│
├── docs/
│   ├── architecture/                # System architecture documentation
│   │   ├── README.md
│   │   ├── advisor_architecture.md  # GenAI Advisor architecture & Mermaid flows
│   │   ├── kyc_architecture.md      # Smart KYC architecture & Mermaid flows
│   │   └── recommendation_engine.md # Architecture & Mermaid pipeline diagram
│   ├── kyc_privacy_security.md      # DPDP Act compliance, data retention & file isolation
│   └── phase-reports/               # Execution reports & inventories
│       ├── catalogue_schema_analysis.md # Column-by-column catalogue analysis
│       ├── dataset_inventory.md     # Full dataset validation report
│       ├── phase_0_report.md        # Phase 0 setup & validation report
│       ├── phase_1_audit_before_phase_2.md # Audit findings & fixes applied
│       ├── phase_1_report.md        # Phase 1 execution & test report
│       ├── phase_2_evaluation.md    # Comprehensive evaluation of Scenarios A-J
│       ├── phase_2_report.md        # Phase 2 execution & delivery report
│       ├── phase_3_ocr_evaluation.md # Benchmark report on 47 specimen documents
│       ├── phase_3_preimplementation_audit.md # Pre-implementation audit & conventions
│       └── phase_3_report.md        # Phase 3 execution & delivery report
│
├── scripts/
│   ├── analyze_catalogue.py         # Catalogue distribution analyzer
│   ├── evaluate_kyc_ocr.py          # Standalone benchmark across 47 specimen documents
│   ├── inspect_dataset.py           # Dataset audit and verification script
│   ├── test_advisor_live.py         # Standalone live Gemini integration test
│   └── verify_environment.py        # System hardware & dependency audit
│
├── pytest.ini                       # Pytest configuration
├── .gitignore                       # Git ignore rules
└── README.md                        # Root project documentation
```

---

## 6. Python Environment Setup

The backend runs inside an isolated virtual environment (`backend/venv`) using Python 3.13.7.

### Step 1: Activate Virtual Environment
On Windows PowerShell:
```powershell
backend\venv\Scripts\Activate.ps1
```

### Step 2: Install Locked Dependencies
```powershell
pip install -r backend/requirements.txt
```

### Step 3: Verify Environment Health
```powershell
python scripts/verify_environment.py
```

---

## 7. Gemini API Setup

Udyam360 connects to the Google Gemini Developer API via Google AI Studio using the official `google-genai` SDK.

1. Create a `backend/.env` file (copied from `backend/.env.example`):
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-3.1-flash-lite
   LLM_PROVIDER=gemini
   ```
2. **Billing Note:** Ensure the API key uses the **Free Tier** in Google AI Studio. Do NOT enable paid automatic billing.
3. **Security:** `.env` is strictly excluded from Git tracking via `.gitignore`. Never hardcode or commit API keys.

---

## 8. Instructions to Run the Connection Test

### Run Model Discovery
To discover available Gemini models and check content generation capabilities:
```powershell
python backend/app/services/model_discovery.py
```

### Run Live Gemini Connection Test
To execute a minimal latency and token-audited ping against `gemini-3.1-flash-lite`:
```powershell
python backend/test_gemini.py
```
*Expected Output:*
```
=== UDYAM360 GEMINI API CONNECTION TEST ===
Selected Model: gemini-3.1-flash-lite
Initialising Google GenAI client...
Sending test prompt to gemini-3.1-flash-lite...

--- CONNECTION STATUS: SUCCESS ---
Response Latency: ~1400 ms
Response Text:
Udyam360 Gemini API connection successful.

[MATCH] Response text matches expected output exactly.
Token Usage Metadata:
  - Prompt tokens: 30
  - Candidate tokens: 11
  - Total tokens: 41
```

### Run Unit and Integration Tests
To run the full suite of 118 deterministic backend tests (Catalogue, Eligibility, Pricing, Recommendation, API, Advisor Guardrails, Conversation isolation, OCR abstractions, KYC validation, consent, orders, and security):
```powershell
pytest -v
```
*(Note: Automated unit tests run fully offline via deterministic fallback fixtures without consuming Gemini API quota).*

### Run Frontend Automated Tests
To run the 14 Vitest & React Testing Library component and flow tests:
```powershell
cd frontend
npm test
cd ..
```

### Run Full End-to-End Customer Flow Verification
To execute the automated end-to-end verification script tracing health, advisor chat, recommendation scoring, quote preview, KYC consent/upload/OCR, and order state machine progression:
```powershell
python scripts/verify_e2e_flow.py
```

### Start the FastAPI Backend Server
```powershell
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation:
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

### Start the React Frontend Application
```powershell
cd frontend
npm run dev
```
Customer web application: `http://localhost:5173/`

### Order Lifecycle & Tracking Endpoints available at `/api/v1/orders/`:
- `POST /`: Create a new customer order from confirmed quote and KYC case.
- `GET  /{order_id}`: Retrieve complete order status and customer details.
- `GET  /{order_id}/timeline`: Retrieve order audit milestone event log.
- `GET  /track/{order_reference}`: Customer-facing order lookup by tracking reference (`UDYAM-ORD-2026-XXXXXXXX`).
- `POST /{order_id}/advance`: Progress order lifecycle state (with clear `(Demo / Simulated)` labeling).

### Executive Admin & ML Propensity Endpoints available at `/api/v1/admin/` (Header: `X-Admin-Role: ExecutiveAdmin`):
- `GET  /analytics/overview`: Headline KPIs matching dataset benchmarks (5,000 leads, 368 activations / 7.36%).
- `GET  /analytics/funnel`: 6-stage drop progression & bottleneck diagnosis.
- `GET  /analytics/segments`: Segment volumes and conversion rates.
- `GET  /analytics/sources`: Acquisition channel performance (Referral 14.77% vs WhatsApp 2.79%).
- `GET  /analytics/geography`: Tier 1/2/3 and top MSME hub distribution.
- `GET  /ml/model-info`: Selected model architecture (`LogisticRegression`), version, and training splits.
- `GET  /ml/evaluation`: Held-out test metrics and candidate model benchmark comparison.
- `GET  /ml/feature-importance`: Top positive and negative log-odds feature drivers.
- `GET  /ml/propensity-overview`: Pipeline breakdown across High ($\ge 70\%$), Medium, and Low bands.
- `POST /ml/score`: Real-time single lead scoring with grounded driver explanations.
- `GET  /ml/leads`: Searchable, filterable, and paginated unconverted lead table.
- `GET  /leads/{lead_id}`: Full lead profile, conversion probability, and sales interaction history.
- `POST /leads/{lead_id}/action`: Record follow-up interaction note (in-memory audit log).

Executive Admin Portal: Navigate to `/admin` in the web application.

---

## 9. Dataset Location and Description

The dataset resides in `YTL_TrackA_Udyam_Digital_Data/`:
- **`product_catalogue.csv`** (25 products): Product catalog with pricing, setup fees, minimum terms, and dependency rules.
- **`smb_leads.csv`** (5,000 leads): 1-quarter historical lead funnel with drop reasons, churn data, NPS, and bundle purchases.
- **`mock_gstin_registry.csv`** (3,534 records): Mock GSTIN database supporting format verification and lookup.
- **`mock_udyam_registry.csv`** (2,723 records): Mock Udyam database supporting enterprise type classification.
- **`kyc_documents/`** (47 PNG images): Specimen registration and KYC files across 12 businesses (`K01`–`K12`).

To re-run dataset validation at any time:
```powershell
python scripts/inspect_dataset.py
```

---

## 10. Current Implementation Status

| Stage / Component | Status | Description |
| :--- | :--- | :--- |
| **Phase 0: Environment Setup** | **COMPLETED** | Python 3.13 venv, dependencies, hardware audits, and `.gitignore` |
| **Phase 0: Dataset Discovery** | **COMPLETED** | 100% record verification across all CSVs & KYC files |
| **Phase 0: Gemini API Validation** | **COMPLETED** | Verified with `gemini-3.1-flash-lite` (latency ~1.47s, exact string match) |
| **Phase 0: Architecture & Reports** | **COMPLETED** | Detailed dataset inventory and Phase 0 report created |
| **Phase 1: Catalogue Intelligence** | **COMPLETED** | Full 25-product validation, referential integrity & schema mapping |
| **Phase 1: Eligibility Engine** | **COMPLETED** | Hard constraint checks & dependency graph closure resolver |
| **Phase 1: Recommendation Engine** | **COMPLETED** | Deterministic Essential, Growth, and Premium bundle generation |
| **Phase 1: Pricing & Explanations** | **COMPLETED** | Decimal arithmetic, OTC/MRC separation & structured rationales |
| **Phase 1: FastAPI REST APIs** | **COMPLETED** | Endpoints for catalogue, segments, eligibility, recommendations, quotes |
| **Phase 2: AI Business Advisor** | **COMPLETED** | Conversational onboarding, Gemini profile extraction, Phase 1 grounded advice, dual fallback engine |
| **Phase 3: Smart KYC & OCR** | **COMPLETED** | Local CPU OCR (Windows Media OCR/RapidOCR), mock GST/Udyam registries, 47 specimen evaluations, DPDP compliance |
| **Phase 4: Customer Web App** | **COMPLETED** | React 18 + TS + Tailwind frontend, Advisor UI, Recommendations & Quote review, Smart KYC consent/upload, Order State Machine & Live Tracker |
| **Phase 5: Admin & ML Analytics** | **COMPLETED** | Executive Admin Dashboard, 6-stage funnel telemetry, zero-leakage ML pipeline, Logistic Regression lead scoring (ROC-AUC 0.6692, 100% odds explainability), sales action logging |
| **Phase 6: Final Review & Polish** | *Pending* | Final end-to-end integration review, evaluation documentation, and presentation materials |

