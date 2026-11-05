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
│   │   ├── api/                     # API routers and endpoints
│   │   │   └── __init__.py
│   │   ├── core/                    # App configuration and core settings
│   │   │   └── __init__.py
│   │   ├── schemas/                 # Pydantic data schemas
│   │   │   └── __init__.py
│   │   ├── services/                # Business services & LLM service
│   │   │   ├── __init__.py
│   │   │   ├── llm_service.py       # Safe Gemini API integration wrapper
│   │   │   └── model_discovery.py   # Gemini model capability discovery script
│   │   └── utils/                   # Shared utility functions
│   │       └── __init__.py
│   │
│   ├── tests/                       # Pytest test suite
│   │   ├── __init__.py
│   │   └── test_llm_service.py      # LLM service health check unit tests
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
│   │   └── README.md
│   └── phase-reports/               # Execution reports & inventories
│       ├── dataset_inventory.md     # Full dataset validation report
│       └── phase_0_report.md        # Phase 0 setup & validation report
│
├── scripts/
│   ├── inspect_dataset.py           # Dataset audit and verification script
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

### Run Unit Tests
To verify LLM service health checks without making network calls:
```powershell
pytest -v
```

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
| **Phase 1+: Business Features** | *Pending* | Business Advisor, Bundle Recommender, Smart KYC, Order Tracker |

