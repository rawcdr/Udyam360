# Phase 0 Report — Environment Setup, Dataset Discovery & Gemini API Validation

**Project:** Udyam360 (Airtel SYNC Hackathon 2026 — Enterprise Track A)  
**Phase:** 0 (Setup, Discovery, Connectivity)  
**Execution Date:** 2026-11-05  
**Status:** **PASSED / COMPLETE**  

---

## 1. Environment Setup Results

The development environment has been initialized and verified on the local host machine.

### 1.1. Hardware & Operating System Profile
- **Operating System:** Microsoft Windows 11 Home Single Language (Version 10.0.26200, 64-bit)
- **CPU:** 12th Gen Intel(R) Core(TM) i5-12450H (8 physical cores, 12 logical processors)
- **Host RAM:** 16,474,168 KB (~16 GB system memory)
- **Discrete GPU:** NVIDIA GeForce RTX 3050 Laptop GPU
  - Dedicated VRAM: 4,096 MiB (4 GB)
  - Driver Version: 610.62
  - CUDA Driver Capability: 13.3 (PyTorch / CUDA installation deferred per Phase 0 guidelines)

### 1.2. Python Virtual Environment
- **Python Binary:** Python 3.13.7 (64-bit) located at `backend\venv\Scripts\python.exe`
- **Pip Version:** Pip 26.3
- **Virtual Environment Location:** `backend/venv`

### 1.3. Installed Package Versions
Locked in `backend/requirements.txt`:

| Package Name | Installed Version | Primary Role |
| :--- | :--- | :--- |
| `google-genai` | 2.34.0 | Official Google Gemini Developer API SDK |
| `fastapi` | 0.162.0 | High-performance asynchronous backend API framework |
| `uvicorn[standard]` | 0.54.0 | ASGI web server (includes uvloop/httptools/watchfiles) |
| `pydantic` | 2.14.3 | Data schema validation and serialization |
| `pandas` | 3.1.1 | Dataframe analysis, registry lookup, and dataset handling |
| `numpy` | 2.5.4 | Numerical computing and array transformations |
| `scikit-learn` | 1.9.1 | Future ML lead propensity modeling |
| `python-dotenv` | 1.2.4 | Secure environment variable handling |
| `pillow` | 13.0.0 | Image loading and inspection for KYC documents |
| `pytest` | 9.2.0 | Unit and integration testing |
| `httpx` | 0.28.1 | Asynchronous HTTP client for API verification |
| `openpyxl` | 3.1.5 | Excel spreadsheet ingestion support |
| `python-multipart` | 0.0.33 | Multi-part form-data parser for file uploads |

All packages imported cleanly without deprecation warnings or version collisions in Python 3.13.7.

---

## 2. Gemini API Validation & Connectivity

### 2.1. Model Discovery Results
The model discovery service (`backend/app/services/model_discovery.py`) queried the Google GenAI Developer API endpoint and retrieved 60 registered models.
- **Preferred Model Target:** `gemini-3.1-flash-lite`
- **Discovery Status:** Model `models/gemini-3.1-flash-lite` was successfully located and verified to support content generation.
- **Configured Model in `.env`:** `gemini-3.1-flash-lite`

### 2.2. Free-Tier Eligibility Status
- **SDK Limitation:** The official Google GenAI Developer API SDK (`google-genai`) exposes model attributes, rate limits, and modality support, but does not expose account billing tiers or live free-tier quota balances.
- **Developer Confirmation:** Free-tier eligibility is configured and confirmed via the developer's Google AI Studio project settings with zero paid billing activated.

### 2.3. Live Connection Test Results (`backend/test_gemini.py`)
- **Target Model:** `gemini-3.1-flash-lite`
- **Test Prompt:** `"You are testing the Udyam360 AI development environment. Reply with exactly: Udyam360 Gemini API connection successful."`
- **Response Received:** `"Udyam360 Gemini API connection successful."` (Exact match)
- **Response Latency:** `1469.87 ms` (~1.47 seconds)
- **Token Usage Metadata:**
  - Prompt tokens: 30
  - Candidate tokens: 11
  - Total tokens: 41
- **Security Check:** Zero credentials, tokens, or keys were printed or leaked in console stdout or logs.

### 2.4. LLM Service Health Checks (`backend/tests/test_llm_service.py`)
- Service wrapper `GeminiLLMService` initialized.
- Lazy client initialization implemented to prevent unwanted API requests during test discovery or app startup.
- 4 unit tests covering configuration, key absence handling, and validation passed in `0.90s`.

---

## 3. Dataset Discovery and Inventory Summary

The hackathon dataset folder was discovered at `YTL_TrackA_Udyam_Digital_Data`. All original files have been left intact and unmodified.

- **`product_catalogue.csv`:** 25 products across 5 categories (Connectivity, Communication, Cloud & Productivity, Security, IoT & Physical). 10 products require GSTIN. 7 products have cross-product dependencies (`requires_one_of`).
- **`smb_leads.csv`:** 5,000 leads over Q2 2026. Target segments: Micro retail & services (2,709 leads, 54.18%), Professional offices (1,247 leads, 24.94%). Overall activation conversion rate is 7.36% (368 activated leads).
- **`mock_gstin_registry.csv`:** 3,534 records matching leads with `has_gstin = 'Y'`. 3,266 Active, 167 Cancelled, 101 Suspended.
- **`mock_udyam_registry.csv`:** 2,723 records matching leads with `has_udyam = 'Y'`. 1,833 Micro, 737 Small, 153 Medium enterprises.
- **`kyc_documents/`:** 47 PNG specimen images for 12 applicants (`K01` through `K12`). Applicant `K05` intentionally lacks an Udyam certificate specimen.
- **Dataset Rules Preserved:**
  - GSTIN 4th PAN character convention (`'X'`).
  - Udyam registration district code `00`.
  - Baseline comparison date: `2026-07-15`.

Full details documented in `docs/phase-reports/dataset_inventory.md`.

---

## 4. Problems Encountered and Resolutions

1. **Python 3.13 Module Resolution in Pytest:**
   - *Problem:* When running `pytest` from the root, Python 3.13 did not include the root directory in `sys.path` by default for the `backend.app` namespace.
   - *Resolution:* Added `pytest.ini` with `pythonpath = . backend` and implemented fallback import handling in test modules. Tests now run seamlessly from both root and `backend/`.
2. **Environment Key Fallback in Test Harness:**
   - *Problem:* Passing `api_key=""` in unit tests fell back to the loaded environment variable due to an `or` operator in `__init__`.
   - *Resolution:* Explicitly checked `if api_key is not None` to allow isolated unit testing of degraded/missing key states without unsetting environment variables.

---

## 5. Unresolved Issues

- **None.** All criteria for Phase 0 have been satisfied. No billing issues, quota issues, or missing files were encountered.

---

## 6. Commands to Reproduce Phase 0 Verification

```powershell
# 1. Activate Virtual Environment
.\backend\venv\Scripts\Activate.ps1

# 2. Verify Python environment & hardware
python scripts/verify_environment.py

# 3. Inspect Hackathon Dataset
python scripts/inspect_dataset.py

# 4. Discover Gemini models
python backend/app/services/model_discovery.py

# 5. Execute Gemini connection test
python backend/test_gemini.py

# 6. Run unit tests
pytest -v
```

