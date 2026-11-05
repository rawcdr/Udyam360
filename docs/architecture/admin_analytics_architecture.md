# Udyam360 Admin Analytics & ML Inference Architecture

**Document:** `docs/architecture/admin_analytics_architecture.md`  
**System Version:** `v1.0.0` (Phase 5)  
**Track:** Airtel SYNC Hackathon 2026 — Enterprise Track A  

---

## 1. System Architecture Diagram

```mermaid
flowchart TD
    subgraph DataLayer["Data Layer & Dataset Isolation"]
        CSV[("smb_leads.csv (5,000 Rows, 40 Cols)<br/>Strictly Read-Only")]
        AuditDoc["phase_5_data_audit.md<br/>Zero Contamination Guarantee"]
    end

    subgraph MLLayer["Zero-Leakage ML & Feature Engineering Layer"]
        Isolation["Feature Isolation & Blacklist<br/>17 Downstream Columns Excluded"]
        Allowlist["Safe Intake Allowlist<br/>12 Categorical + 12 Numeric Features"]
        Preprocessor["ColumnTransformer<br/>StandardScaler + OneHotEncoder"]
        LR["Logistic Regression Classifier<br/>Class Weight: Balanced"]
        Artifacts[("backend/models/<br/>lead_propensity_pipeline.joblib<br/>model_metadata.json<br/>evaluation_report.json")]
    end

    subgraph ServiceLayer["Enterprise Core Services"]
        AnalyticsSvc["AnalyticsService<br/>- 6-Stage Funnel Telemetry<br/>- Bottleneck Diagnostics<br/>- Segment & Channel Analysis<br/>- Geographic Distribution"]
        ScoringSvc["LeadScoringService<br/>- In-Memory Precomputed Cache<br/>- Multi-Column Filter & Sort<br/>- Lead Pagination<br/>- Sales Action Audit Logging"]
        Explainer["ModelExplainer & Inference<br/>- Exact Linear Log-Odds Weights<br/>- Grounded Business Drivers<br/>- Stage-Aware Recommended Plays"]
    end

    subgraph SecurityLayer["Enterprise Access & Governance"]
        Guard["verify_admin_access Dependency<br/>Header: X-Admin-Role: ExecutiveAdmin<br/>Rejects unauthorized public requests (403)"]
    end

    subgraph APILayer["FastAPI Admin Endpoints (/api/v1/admin)"]
        AnalyticsAPI["/analytics/*<br/>/overview<br/>/funnel<br/>/segments<br/>/sources<br/>/geography"]
        MLAPI["/ml/*<br/>/model-info<br/>/evaluation<br/>/feature-importance<br/>/propensity-overview<br/>/score (POST)<br/>/leads (GET)"]
        LeadsAPI["/leads/*<br/>/{lead_id}<br/>/{lead_id}/propensity<br/>/{lead_id}/action (POST)"]
    end

    subgraph FrontendLayer["React Admin Dashboard (/admin)"]
        Nav["AdminLayout & Executive Top Bar"]
        View1["AdminOverviewPage<br/>- Headline KPI Cards<br/>- 6-Stage Recharts Funnel<br/>- Bottleneck Alerts<br/>- Channel & Segment Bars"]
        View2["AdminLeadsPage<br/>- Unconverted Prioritization Table<br/>- Segment/Stage/Band Filters<br/>- Lead Detail Modal<br/>- Sales Action Logging Form"]
        View3["AdminModelPage<br/>- Candidate Benchmark Table<br/>- Feature Log-Odds Chart<br/>- Real-time Scoring Sandbox"]
    end

    %% Data Flow Connections
    CSV --> Isolation
    Isolation --> Allowlist
    Allowlist --> Preprocessor
    Preprocessor --> LR
    LR --> Artifacts

    CSV --> AnalyticsSvc
    Artifacts --> Explainer
    Artifacts --> ScoringSvc
    CSV --> ScoringSvc

    AnalyticsSvc --> AnalyticsAPI
    ScoringSvc --> MLAPI
    ScoringSvc --> LeadsAPI
    Explainer --> MLAPI
    Explainer --> LeadsAPI

    Guard -.->|Protects| AnalyticsAPI
    Guard -.->|Protects| MLAPI
    Guard -.->|Protects| LeadsAPI

    AnalyticsAPI --> View1
    MLAPI --> View2
    MLAPI --> View3
    LeadsAPI --> View2
    Nav --> View1
    Nav --> View2
    Nav --> View3
```

---

## 2. Core Architectural Principles

### 2.1 Zero-Leakage Pipeline Architecture
- Downstream milestone timestamps (`contacted_date`, `needs_assessed_date`, `quote_accepted_date`, `kyc_complete_date`, `activated_date`) and post-outcome commercial attributes (`monthly_bundle_value_inr`, `one_time_setup_inr`, `nps_score`, `churned_within_6_months`) are isolated via strict feature masking before feature transformations.
- Preprocessing parameters (means, scales, category encoders) are fit strictly on the 70% training split (3,500 samples) and applied transitively to validation, test, and live inference.

### 2.2 Sub-Millisecond In-Memory Caching
- To guarantee responsive sub-millisecond interaction across 5,000 records, `LeadScoringService` evaluates and caches model predictions in-memory upon startup.
- Dynamic filtering (by MSME vertical, funnel stage, and propensity tier), fuzzy multi-term search, and multi-key sorting execute entirely in memory.

### 2.3 Transparent Explainability Guarantee
- Rather than presenting black-box probability figures, every propensity score is accompanied by local linear attributions ($x_i \cdot w_i$).
- Feature attributions are translated into grounded business strings (e.g., *Referred by existing partner (+98% conversion odds)*, *Micro retail archetype (historically higher price sensitivity)*) to provide actionable guidance to sales teams.

### 2.4 Secure Prototype Role Guard
- Endpoints are gated by FastAPI's dependency injection (`verify_admin_access`), verifying role credentials via `X-Admin-Role: ExecutiveAdmin`.
- Public unauthorized callers without appropriate role headers receive a `403 Forbidden` response.

