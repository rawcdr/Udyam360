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
- **Testing & Tooling:** PyTest, HTTPX, Pillow, Python-Dotenv
- **Hardware Acceleration:** Windows 11, Intel Core i5-12450H, 16GB RAM, NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM)
- **Frontend (Planned for Phase 1+):** React, TypeScript, Tailwind CSS, Vite

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
│   │   │   ├── catalogue.py         # Product catalogue endpoints
│   │   │   ├── segments.py          # Customer segments endpoints
│   │   │   ├── eligibility.py       # Eligibility evaluation endpoint
│   │   │   ├── recommendations.py   # Multi-tier bundle recommendation endpoint
│   │   │   └── quotes.py            # Server-side quote preview endpoint
│   │   ├── core/                    # App configuration and core settings
│   │   │   ├── __init__.py
│   │   │   └── config.py            # Centralized project settings & paths
│   │   ├── schemas/                 # Pydantic data schemas
│   │   │   ├── __init__.py
│   │   │   ├── advisor.py           # Conversational profile extraction & message models
│   │   │   ├── business_profile.py  # Customer business profile models
│   │   │   ├── catalogue.py         # Product & catalogue summary models
│   │   │   ├── eligibility.py       # Eligibility evaluation models
│   │   │   ├── pricing.py           # Breakdown & contract pricing models
│   │   │   ├── quote.py             # Quote preview request/response models
│   │   │   └── recommendation.py    # Bundle recommendation & scoring models
│   │   ├── services/                # Business services & recommendation logic
│   │   │   ├── __init__.py
│   │   │   ├── advisor_dialogue_service.py # Missing field analysis & clarification
│   │   │   ├── advisor_orchestrator.py     # End-to-end advisor coordinator
│   │   │   ├── advisor_response_service.py # Gemini grounded explanation & template fallback
│   │   │   ├── bundle_explanation.py       # Deterministic bundle rationale service
│   │   │   ├── catalogue_service.py        # Catalogue loading & integrity validator
│   │   │   ├── conversation_service.py     # In-memory session & state merge manager
│   │   │   ├── eligibility_engine.py       # Hard rules & dependency resolution engine
│   │   │   ├── llm_service.py              # Safe Gemini API integration wrapper
│   │   │   ├── model_discovery.py          # Gemini model capability discovery script
│   │   │   ├── pricing_engine.py           # High-precision decimal pricing calculator
│   │   │   ├── profile_extraction_service.py # Gemini structured JSON + regex extractor
│   │   │   └── segment_service.py          # Segment intelligence & suitability scoring
│   │   └── utils/                   # Shared utility functions
│   │       └── __init__.py
│   │
│   ├── tests/                       # Comprehensive PyTest test suite (69 tests)
│   │   ├── __init__.py
│   │   ├── conftest.py              # Pytest fixtures & quota isolation
│   │   ├── test_advisor_api.py      # Advisor REST API endpoint tests
│   │   ├── test_advisor_guardrails.py # Guardrails, fallbacks & prompt injection tests
│   │   ├── test_advisor_orchestrator.py # Multi-turn orchestration tests (Scenarios A-D)
│   │   ├── test_api.py              # REST API endpoint integration tests
│   │   ├── test_catalogue.py        # Catalogue service unit tests
│   │   ├── test_conversation.py    # Session isolation & state merge tests
│   │   ├── test_eligibility.py      # Hard constraints & dependency tests
│   │   ├── test_llm_service.py      # LLM service health check unit tests
│   │   ├── test_pricing.py          # Pricing engine unit tests
│   │   ├── test_profile_extraction.py # Dual-mode extraction unit tests
│   │   └── test_recommendation.py   # Archetype recommendation tests
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
│   │   └── recommendation_engine.md # Architecture & Mermaid pipeline diagram
│   └── phase-reports/               # Execution reports & inventories
│       ├── catalogue_schema_analysis.md # Column-by-column catalogue analysis
│       ├── dataset_inventory.md     # Full dataset validation report
│       ├── phase_0_report.md        # Phase 0 setup & validation report
│       ├── phase_1_audit_before_phase_2.md # Audit findings & fixes applied
│       ├── phase_1_report.md        # Phase 1 execution & test report
│       ├── phase_2_evaluation.md    # Comprehensive evaluation of Scenarios A-J
│       └── phase_2_report.md        # Phase 2 execution & delivery report
│
├── scripts/
│   ├── analyze_catalogue.py         # Catalogue distribution analyzer
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
To run the full suite of 69 deterministic tests (Catalogue, Eligibility, Pricing, Recommendation, API, Advisor Guardrails, and Conversation isolation):
```powershell
pytest -v
```
*(Note: Automated unit tests run fully offline via deterministic fallback fixtures without consuming Gemini API quota).*

### Run Live Gemini Advisor Test
To execute the live end-to-end integration test against `gemini-3.1-flash-lite` (profile extraction, deterministic recommendation, and grounded natural language synthesis):
```powershell
python scripts/test_advisor_live.py
```

### Start the FastAPI Backend Server
```powershell
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
Once started, explore the interactive Swagger API documentation at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

Advisor endpoints available at `/api/v1/advisor/`:
- `POST /start`: Initialize new conversational session.
- `POST /message`: Send user message and receive grounded recommendations.
- `GET  /conversation/{id}`: Inspect active conversation state and profile.
- `POST /reset/{id}`: Reset and discard active session history.
- `GET  /health`: Health check for Gemini model connectivity.

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
| **Phase 3+: Smart KYC & OCR** | *Pending* | Document OCR, synthetic registry verification & fraud detection |
| **Phase 4+: Order Tracker & Admin**| *Pending* | Real-time order tracker and executive ML analytics dashboard |

