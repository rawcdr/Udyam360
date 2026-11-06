# Udyam360 — Final End-to-End System Architecture

**Project:** Udyam360 — Airtel SYNC Hackathon 2026 (Enterprise Track A, Project Udyam Digital)  
**Document:** `docs/architecture/final_system_architecture.md`  
**Date:** November 6, 2026  
**Status:** **FINAL SUBMISSION ARCHITECTURE**

---

## 1. High-Level Architectural Blueprint

```mermaid
flowchart TD
    subgraph Client_Layer ["Client Layer (React 18 + Vite SPA)"]
        LP["Landing Page (Archetypes)"]
        ADV["AI Business Advisor (Chat UI)"]
        REC["Recommendations & Bundles"]
        QT["Quote Review (MRC vs OTC)"]
        KYC_UI["Smart KYC (Consent Gate & Upload)"]
        OT["Order Tracker (Simulated Activation)"]
        subgraph Admin_Portal ["Code-Split Admin Portal (/admin)"]
            AO["Executive Overview (Funnel Telemetry)"]
            AL["Lead Prioritization (4,632 Actionable)"]
            AM["ML Model Hub & Sandbox"]
        end
    end

    subgraph Gateway ["API Gateway & Security Boundary"]
        F划["FastAPI REST Application (ASGI)"]
        AG["Role Guard: X-Admin-Role (Prototype)"]
        CORS["CORS & Request Validation (Pydantic v2)"]
    end

    subgraph Core_Backend ["Core Backend Services (Local Execution)"]
        AS["Advisor Orchestrator (Session Manager)"]
        CS["Catalogue & Eligibility Service"]
        RE["Deterministic Recommendation Engine"]
        QE["Pricing & Quote Preview Service"]
        KO["KYC Orchestrator & Validator"]
        OS["Order Service (State Machine)"]
        AN["Executive Analytics Service"]
        LSS["Lead Scoring & Prioritization Service"]
    end

    subgraph AI_ML_Engines ["AI & Machine Learning Layer"]
        subgraph Cloud_AI ["External Cloud AI (Strict Boundary)"]
            GEM["Google Gemini API (gemini-2.5-flash)"]
        end
        subgraph Local_ML ["Local On-Premises ML / OCR (Zero Cloud Egress)"]
            OCR["Local RapidOCR / WinOCR Engine"]
            LR["Logistic Regression Pipeline (v1.1.0)"]
            CAL["5-Fold Platt Sigmoid Calibration"]
            EXP["Log-Odds ModelExplainer"]
        end
    end

    subgraph Data_Storage ["Data & Persistence Layer"]
        PC["product_catalogue.csv (25 Products)"]
        SL["smb_leads.csv (5,000 Leads, Read-Only)"]
        REG_G["mock_gstin_registry.csv (Synthetic Registry)"]
        REG_U["mock_udyam_registry.csv (Synthetic Registry)"]
        MA["backend/models/ (Serialized Pipelines & JSON)"]
        KYC_DIR["local_uploads/ (Temporary Doc Cache)"]
        MEM["In-Memory Stores (Sessions, Orders, Notes)"]
    end

    %% Client to Gateway
    LP --> F划
    ADV --> F划
    REC --> F划
    QT --> F划
    KYC_UI --> F划
    OT --> F划
    Admin_Portal --> AG --> F划

    %% Gateway to Services
    F划 --> AS
    F划 --> CS
    F划 --> RE
    F划 --> QE
    F划 --> KO
    F划 --> OS
    F划 --> AN
    F划 --> LSS

    %% Service to AI/ML & Data
    AS -.->|"1. Dialogue & Profile Extraction ONLY (No PII/Docs)"| GEM
    AS -->|"2. Deterministic Fallback Guard"| CS
    CS --> PC
    RE --> PC
    QE --> PC
    KO -->|"Local OCR Extraction"| OCR
    KO -->|"Synthetic Verification"| REG_G
    KO -->|"Synthetic Verification"| REG_U
    KO --> KYC_DIR
    LSS --> LR
    LR --> CAL
    CAL --> EXP
    LSS --> MA
    AN --> SL
    OS --> MEM

    classDef cloud fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1;
    classDef local fill:#f0fdf4,stroke:#16a34a,stroke-width:2px,color:#15803d;
    classDef boundary fill:#fef2f2,stroke:#dc2626,stroke-width:2px,color:#991b1b;
    classDef data fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#334155;

    class GEM cloud;
    class OCR,LR,CAL,EXP local;
    class AG,CORS boundary;
    class PC,SL,REG_G,REG_U,MA,KYC_DIR,MEM data;
```

---

## 2. Component Boundaries & Execution Architecture

### 2.1 The Gemini API Boundary (Cloud vs. Local Isolation)
To guarantee strict compliance with enterprise privacy standards and India's DPDP Act:
* **What Communicates with Gemini:**
  * Only natural-language business descriptions provided in the conversational advisor chat (e.g., *"I run a pharmacy in Bengaluru with 4 staff and ₹4,000 monthly telecom spend"*).
  * Gemini extracts structured MSME profile attributes (segment, headcount, location, budget).
* **What NEVER Communicates with Gemini:**
  * **Zero KYC Document Egress:** Document bytes, images, and text extracted by OCR **never** leave the local server and are **never** passed to Gemini.
  * **Zero Registry Data Egress:** Tax IDs, GSTINs, and Udyam numbers are validated strictly against local mock CSVs.
  * **Zero Product Pricing Control:** Product eligibility, pricing rules, bundle scoring, and discount allocations are 100% deterministic code executing locally on the backend. Gemini has zero authority over prices.

### 2.2 Local OCR Processing Pipeline
* **Engine:** RapidOCR (ONNX runtime) with Windows Media OCR (`winocr`) fallback.
* **Execution:** 100% on-premises / local CPU inference.
* **Function:** Extracts document type, registration ID, enterprise name, address, and date of issue from uploaded PDF/PNG/JPEG files.
* **Cross-Validation:** Directly matches extracted names and identifiers against the customer's onboarding profile and the local synthetic registries.

### 2.3 Synthetic / Mock Registry Boundary
* **Registries:** `mock_gstin_registry.csv` and `mock_udyam_registry.csv`.
* **Nature:** Strictly simulated hackathon fixtures containing synthetic enterprise records.
* **Disclosure:** No real-time government GSTN or Ministry of MSME Udyam portals are queried. Active/Suspended/Cancelled states reflect the mock dataset.

### 2.4 Lead Propensity Machine Learning Pipeline
* **Algorithm:** Standardized Logistic Regression pipeline (`ColumnTransformer` with `StandardScaler` for numeric values and `OneHotEncoder(handle_unknown='ignore')` for categoricals).
* **Probability Calibration:** 5-fold cross-validated Platt Sigmoid Calibration (`CalibratedClassifierCV(method='sigmoid', cv=5)`) fit strictly on the Train + Validation splits (4,250 samples). The held-out test fold (750 samples) remained untouched.
* **Brier Score:** Calibrated Brier score of **0.0666** on held-out test data, outperforming the naive prior baseline ($0.0733 \times (1 - 0.0733) = \mathbf{0.0680}$).
* **Explainability:** Log-odds attribution ($\beta_i \cdot x_i$) with mathematically bounded percentage changes ($(\exp(\beta_i) - 1) \times 100\% \ge -100\%$) and explicit non-causal disclosures.
* **Lead Population:** Scores all 4,632 actionable unconverted leads; strictly quarantines 368 already-activated accounts with `ALREADY_ACTIVATED` flags.

### 2.5 Simulated Order Fulfillment
* **State Machine:** `Order Created` $\rightarrow$ `Document Verification` $\rightarrow$ `Commercial Approval` $\rightarrow$ `Provisioning` $\rightarrow$ `Simulated Activation`.
* **Disclosure:** In a hackathon environment without live telco network OSS/BSS connectors, service provisioning and circuit activation are explicitly simulated.

---

## 3. Technology Stack Inventory

| Tier | Component | Technology & Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend** | Framework | React 18.3.1 + TypeScript 5.6.3 | Modern, type-safe web application |
| | Build Tool | Vite 5.4.11 (with Rollup Code Splitting) | Sub-second HMR, optimized multi-chunk bundle |
| | Styling | Tailwind CSS 3.4.15 | Responsive, utility-first enterprise design |
| | Visualizations | Recharts 3.10.1 (Code-split to `/admin`) | Funnel drop-offs, segment bars, channel metrics |
| | Icons | Lucide React 0.468.0 | Consistent iconography |
| | Client Routing | React Router v6.28.0 | Declarative client-side routing & Suspense gates |
| **Backend** | Framework | FastAPI 0.162.0 (ASGI) + Uvicorn 0.54.0 | High-performance asynchronous REST API |
| | Validation | Pydantic v2.14.3 | Strict request/response typing and validation |
| | Environment | Python 3.13.7 (64-bit) | Modern Python runtime |
| **AI / ML** | Conversational AI | Google Gemini API (`google-genai` SDK) | Natural language dialogue & profile extraction |
| | Local OCR | RapidOCR ONNX / WinOCR | Local document text extraction |
| | Propensity ML | Scikit-learn 1.9.1 | Logistic Regression & Platt Calibrated Classifier |
| | Data Science | Pandas 3.1.1 & NumPy 2.5.4 | Feature engineering and analytics aggregation |
| **Testing** | Backend Tests | PyTest 9.2.0 + AnyIO | 138 passing unit, integration & scenario tests |
| | Frontend Tests | Vitest 2.1.8 + JSDOM | 17 passing React Testing Library tests |
| **Deliverables**| Presentations | `python-pptx` 1.0.2 | 10-slide enterprise presentation generator |
| | Documents | `reportlab` 5.1.0 | 1-page privacy & security note PDF generator |

