# Phase 1 Report — Dataset Engineering, Catalogue Intelligence & Recommendation Engine

**Project:** Udyam360 (Airtel SYNC Hackathon 2026 — Enterprise Track A)  
**Phase:** 1 (Core Business Intelligence & Recommendation Engine)  
**Execution Date:** 2026-11-05  
**Status:** **PASSED / COMPLETE**  

---

## 1. Executive Summary

Phase 1 implemented the deterministic, explainable business intelligence and product recommendation core for Udyam360. All 25 commercial products from the hackathon catalogue (`product_catalogue.csv`) are ingested, validated, and normalized into Pydantic models. A multi-stage recommendation pipeline evaluates hard eligibility constraints, resolves cross-product dependency graphs, scores bundles against customer budgets and segment priorities, and outputs three calibrated bundles: **Essential**, **Growth**, and **Premium**.

All 46 unit and integration tests passed cleanly in `5.13s` with zero LLM hallucinations or external API costs.

---

## 2. Catalogue Schema Analysis & Loading Implementation

### 2.1. Dataset Schema Analysis
The catalogue was analyzed across 16 dimensions without modifying the source CSV:
- **25 Products across 5 Categories:** Connectivity (11), Communication (4), Cloud & Productivity (4), Security (3), IoT & Physical (3).
- **Billing Units:** 12 distinct unit bases (`per site`, `per user`, `per line`, `per counter`, `per device`, `per camera`, `per account`, `per pack`, `per number`, `per IP`, `per channel`, `per vehicle`).
- **Eligibility Rules:**
  - 10 products mandate active GSTIN (`requires_gstin = 'Y'`).
  - 1 product (`P03` Biz Fibre 1G) is restricted to Tier 1 cities only; 24 products are available in both Tier 1 and Tier 2.
  - Headcount thresholds: 1 employee (18 products), 3 employees (`P12`), 5 employees (`P03`), 10 employees (`P05`, `P10`, `P21`, `P24`), 25 employees (`P06`).
  - Multi-site requirement: `P10` (Managed SD-WAN) mandates ≥ 3 business premises.

### 2.2. Service Implementation (`backend/app/services/catalogue_service.py`)
- Ingests data through dynamic path resolution (no hardcoded Windows paths).
- Verifies schema completeness, catches duplicate product IDs, checks price bounds (`price_max >= price_min >= 0`), and validates all referential dependencies.
- Exposes query methods: `get_all_products()`, `get_product_by_id()`, `get_products_by_category()`, and `get_catalogue_summary()`.

---

## 3. Eligibility Logic & Dependency Resolution

### 3.1. Hard Eligibility Engine (`backend/app/services/eligibility_engine.py`)
Deterministic checks evaluate each product against customer attributes:
- **`ELIGIBLE`:** Product satisfies all headcount, premise, city-tier, and GSTIN criteria.
- **`INELIGIBLE`:** Profile violates a hard condition (e.g. Tier 2 location applying for `P03`, or non-GST business selecting `P14`).
- **`NEEDS_INFORMATION`:** Customer left optional information blank (e.g. unconfirmed GSTIN status or unstated headcount); avoids premature disqualification while logging required fields.
- **`DEPENDENCY_REQUIRED`:** Product is eligible but requires at least one prerequisite product from `requires_one_of`.

### 3.2. Dependency Graph Closure
Seven products possess cross-product dependencies on base connectivity:
- `P09` (Backup Failover), `P10` (SD-WAN), `P11` (Static IP), `P12` (SIP Telephony), `P21` (Firewall), `P22` (Guest Wi-Fi), and `P23` (Cloud CCTV).
- When a dependent product is requested without a base connection, `resolve_dependencies()` automatically selects and injects the lowest-cost eligible prerequisite (e.g. `P04` AirFiber 100 @ ₹899 or `P01` Biz Fibre 100 @ ₹999).
- Recursion depth limits and self-dependency checks guard against circular references.

---

## 4. Customer Segment Intelligence (`backend/app/services/segment_service.py`)

Target segment priorities are configured using category weight matrices and feature keywords:
- **Micro Retail (`micro`):** Kirana stores, pharmacies, salons, retail outlets.
  - *Priorities:* Low-cost broadband, POS digital billing (`P19`), WhatsApp marketing (`P15`), Cloud CCTV surveillance (`P23`), and business mobile lines (`P07`).
- **Professional Offices (`prof`):** Clinics, CA firms, coaching institutes, consultancies.
  - *Priorities:* High-uptime fibre (`P01`/`P02`), business email suites (`P16`), encrypted cloud backup (`P17`), endpoint security (`P20`), and IP telephony (`P12`).

---

## 5. Bundle Recommendation & Scoring Engine

### 5.1. Bundle Tiers
1. **Essential Bundle:** Lowest recurring cost meeting baseline connectivity and core operations.
2. **Growth Bundle:** Optimal balance of customer requirements, segment suitability, and affordability.
3. **Premium Bundle:** Comprehensive setup featuring enterprise security, backup, and advanced communication.

### 5.2. Transparent Scoring Formula
Scoring is normalized to a 0–100 scale using configurable weights:
$$\text{Total Score} = (\text{ReqMatch} \times 0.50) + (\text{BudgetFit} \times 0.25) + (\text{Eligibility} \times 0.15) + (\text{SegmentSuitability} \times 0.10)$$

- **Requirement Match (50%):** Percentage of requested categories/services fulfilled.
- **Budget Fit (25%):** Full score when within budget; proportional linear penalty when exceeding budget.
- **Eligibility & Completeness (15%):** 100% for verified profiles; minor deduction when fields require verification.
- **Segment Suitability (10%):** Weighted alignment with segment-specific feature preferences.

### 5.3. Budget Enforcement
Bundles are flagged as `WITHIN_BUDGET` or `EXCEEDS_BUDGET`. If a customer’s budget is too low for baseline connectivity, the engine returns the closest valid bundle and reports the exact budget shortfall (`budget_gap_inr`) without silently removing essential services.

---

## 6. Pricing Engine (`backend/app/services/pricing_engine.py`)

Calculates exact monetary values using decimal arithmetic:
- **Monthly Recurring Charges (MRC):** Range `[monthly_total_min, monthly_total_max]`.
- **One-Time Setup Charges (OTC):** Sum of installation charges across products.
- **Estimated First Month Outlay:** `Month 1 MRC + OTC`.
- **Quantity Multipliers:** Dynamically applies user count, site count, counter count, device count, and line count based on catalogue unit definitions.

---

## 7. Deterministic Bundle Explanations (`backend/app/services/bundle_explanation.py`)

Every generated bundle includes human-readable and structured rationales:
- Summary of bundle intent.
- Specific justification for each included product based on segment priorities.
- Inventory of satisfied vs. unmet customer requests.
- Contract commitments and fulfillment installation timelines.
- Missing information warnings and operational assumptions.

---

## 8. FastAPI Endpoints & Swagger Documentation

Routers integrated under `/api/v1` in `backend/app/main.py`:

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/v1/catalogue` | `GET` | List all 25 products (optional `?category=` filter) |
| `/api/v1/catalogue/{product_id}` | `GET` | Retrieve single product details |
| `/api/v1/catalogue/summary` | `GET` | Catalogue statistical overview |
| `/api/v1/segments` | `GET` | Retrieve supported MSME segments & priority profiles |
| `/api/v1/eligibility/check` | `POST` | Check catalogue eligibility for a given customer profile |
| `/api/v1/recommendations` | `POST` | Generate Essential, Growth, and Premium bundles |
| `/api/v1/quotes/preview` | `POST` | Server-side quote calculation & eligibility re-validation |
| `/health` & `/api/v1/health` | `GET` | System health check |
| `/docs` & `/openapi.json` | `GET` | Interactive Swagger UI and OpenAPI 3.0 specification |

---

## 9. Comprehensive Testing Results

The test suite executed with Pytest across 46 unit and integration test cases:

```
collected 46 items

backend/tests/test_api.py::test_docs_and_openapi_endpoints PASSED        [  2%]
backend/tests/test_api.py::test_health_check_endpoint PASSED             [  4%]
backend/tests/test_api.py::test_catalogue_endpoints PASSED               [  6%]
backend/tests/test_api.py::test_segments_endpoint PASSED                 [  8%]
backend/tests/test_api.py::test_eligibility_check_endpoint PASSED        [ 10%]
backend/tests/test_api.py::test_recommendation_endpoint PASSED           [ 13%]
backend/tests/test_api.py::test_quote_preview_endpoint PASSED            [ 15%]
backend/tests/test_api.py::test_quote_preview_invalid_product PASSED     [ 17%]
backend/tests/test_catalogue.py (8 tests) PASSED                          [ 34%]
backend/tests/test_eligibility.py (9 tests) PASSED                        [ 54%]
backend/tests/test_llm_service.py (4 tests) PASSED                        [ 63%]
backend/tests/test_pricing.py (7 tests) PASSED                            [ 78%]
backend/tests/test_recommendation.py (10 tests) PASSED                    [100%]

======================== 46 passed in 5.13s ========================
```

---

## 10. Limitations and Unresolved Issues

1. **Tax Calculations (GST):** The dataset defines pre-tax base prices in INR. GST taxation (18% for telecom/SaaS) is not included in the raw catalogue and will be modeled in Phase 3 quote checkout.
2. **City Tier Granularity:** The dataset identifies Tier 1 vs. Tier 2. Specific pin-code-level fibre feasibility checks will be added in future integration with telecom GIS databases.

---

## 11. Commands to Run & Verify

```powershell
# 1. Activate Virtual Environment
.\backend\venv\Scripts\Activate.ps1

# 2. Run Test Suite
pytest -v

# 3. Start Backend API Server
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

# 4. Access Interactive API Documentation
# Open in browser: http://127.0.0.1:8000/docs
```

