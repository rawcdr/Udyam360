# Phase 5 — Data & Repository Audit Report: SMB Lead Propensity & Funnel Intelligence

**Project:** Udyam360 — Airtel SYNC Hackathon 2026 (Enterprise Track A, Project Udyam Digital)  
**Date:** 2026-11-06  
**Status:** Completed  
**Objective:** Comprehensive statistical and leakage audit of `smb_leads.csv` (5,000 records, 40 columns), prediction target definition, feature timing classification, and documented feature allowlist for ML lead propensity scoring.

---

## 1. Dataset Dimensions & Integrity Audit

- **Source File:** `YTL_TrackA_Udyam_Digital_Data/smb_leads.csv`
- **Total Records (Rows):** 5,000
- **Total Fields (Columns):** 40
- **Primary Key:** `lead_id` (Unique values: 5,000; Null count: 0)
- **Duplicate Rows:** 0 (Verified across all 40 columns)
- **Time Range (`created_date`):** `2026-04-01` to `2026-06-30` (91 calendar days / Q2 2026)
- **Activation Time Range (`activated_date`):** `2026-04-13` to `2026-07-26`
- **Integrity Guarantee:** The raw dataset file remains strictly read-only, uncompressed, and unmodified in place.

---

## 2. Funnel Progression & Ground Truth Metrics

The dataset contains explicit timestamps marking each customer's progression through the 6 stages of the MSME enterprise funnel. The computed numbers from `smb_leads.csv` match the problem statement case study:

| Funnel Stage | Date Field | Non-Null Count | Funnel Volume | Stage Drop-off | Stage Conversion % | Overall Conversion % |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Lead Intake** | `created_date` | 5,000 | 5,000 | 1,594 | 68.12% | 100.00% |
| **2. Contacted** | `contacted_date` | 3,406 | 3,406 | 1,432 | 57.96% | 68.12% |
| **3. Needs Assessed** | `needs_assessed_date` | 1,974 | 1,974 | 1,113 | 43.62% | 39.48% |
| **4. Quote Accepted** | `quote_accepted_date` | 861 | 861 | 273 | 68.29% | 17.22% |
| **5. KYC Complete** | `kyc_complete_date` | 588 | 588 | 220 | 62.59% | 11.76% |
| **6. Activated** | `activated_date` | 368 | 368 | 0 | 100.00% | **7.36%** |

### Key Observations:
1. **Largest Funnel Bottleneck:** Between **Contacted** (3,406) and **Needs Assessed** (1,974), where **1,432 leads drop off (42.04% drop-off rate)**, followed closely by **Needs Assessed to Quote Accepted** where **1,113 leads drop off (56.38% stage drop-off rate)**.
2. **Terminal Status Field (`stage_reached`):** Records the final stage at which the lead exited or stalled (`Lead`: 1,594; `Contacted`: 1,432; `Needs assessed`: 1,113; `Quote accepted`: 273; `KYC complete`: 220; `Activated`: 368). Sum: exactly 5,000.

---

## 3. Prediction Target Formulation

- **Target Variable:** `outcome`
- **Target Value:** `y = 1` if `outcome == 'Activated'`, else `0` (`outcome == 'Dropped'`)
- **Class Balance:**
  - **Negative (`Dropped` / `0`):** 4,632 (92.64%)
  - **Positive (`Activated` / `1`):** 368 (7.36%)
- **Imbalance Ratio:** ~12.6 : 1
- **Target Justification:** In enterprise telecom sales, the primary objective is to allocate scarce field sales and solution engineering resources to inbound and outbound leads with the highest propensity to reach full service activation, rather than optimizing for intermediate metrics like mere contact calls.

---

## 4. Comprehensive 40-Column Audit & Leakage Classification

To prevent data leakage, each column is classified by its time of creation and availability relative to the lead intake prediction point:

| Column Name | Data Type | Nulls (%) | Unique | Timing / Role | Leakage Status | Treatment |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| `lead_id` | str | 0% | 5,000 | Intake Identifier | Identifier (Safe Key) | Index key; excluded from model training |
| `created_date` | str | 0% | 91 | Intake Timestamp | Safe Feature | Engineered (Month, Day of Week) |
| `lead_source` | str | 0% | 6 | Intake Channel | Safe Feature | **Allowlist** (One-Hot Encoded) |
| `business_name` | str | 0% | 1,934 | Intake Free-Text | High-Cardinality / PII | Excluded from training; used in UI |
| `business_type` | str | 0% | 35 | Intake Category | Safe Feature | **Allowlist** (Frequency/Target/One-Hot) |
| `segment` | str | 0% | 4 | Intake Category | Safe Feature | **Allowlist** (One-Hot Encoded) |
| `city` | str | 0% | 22 | Intake Location | Safe Feature | **Allowlist** (One-Hot Encoded) |
| `city_tier` | int64 | 0% | 2 | Intake Category | Safe Feature | **Allowlist** (Binary/Numeric) |
| `state` | str | 0% | 14 | Intake Location | Safe Feature | **Allowlist** (One-Hot Encoded) |
| `preferred_language`| str | 0% | 10 | Intake Profile | Safe Feature | **Allowlist** (One-Hot Encoded) |
| `employee_count` | int64 | 0% | 142 | Intake Firmographics | Safe Feature | **Allowlist** (Standard Scaled) |
| `num_sites` | int64 | 0% | 12 | Intake Firmographics | Safe Feature | **Allowlist** (Standard Scaled) |
| `annual_turnover_band`| str | 0% | 5 | Intake Financials | Safe Feature | **Allowlist** (Ordinal Encoded) |
| `has_gstin` | str | 0% | 2 | Intake Compliance | Safe Feature | **Allowlist** (Binary 1/0) |
| `gstin` | str | 29.3% | 3,534 | Intake PII Identifier | PII / Redundant | Excluded (captured by `has_gstin`) |
| `has_udyam` | str | 0% | 2 | Intake Compliance | Safe Feature | **Allowlist** (Binary 1/0) |
| `udyam_number` | str | 45.5% | 2,723 | Intake PII Identifier | PII / Redundant | Excluded (captured by `has_udyam`) |
| `current_internet` | str | 2.5% | 5 | Intake Tech Profile | Safe Feature | **Allowlist** (Imputed + One-Hot) |
| `current_provider` | str | 2.5% | 5 | Intake Tech Profile | Safe Feature | **Allowlist** (Imputed + One-Hot) |
| `monthly_telecom_spend_inr` | int64 | 0% | 378 | Intake Budget | Safe Feature | **Allowlist** (Standard Scaled) |
| `products_of_interest` | str | 0% | 915 | Intake Intent | Safe Feature | **Allowlist** (Multi-hot/Count engineered) |
| `contact_name` | str | 0% | 1,184 | Intake PII | PII | Excluded from training |
| `contact_role` | str | 0% | 4 | Intake Authority | Safe Feature | **Allowlist** (One-Hot Encoded) |
| `stage_reached` | str | 0% | 6 | Downstream Status | **DIRECT LEAKAGE** | **EXCLUDED** |
| `outcome` | str | 0% | 2 | Ground Truth Target | **TARGET** | Target variable `y` |
| `drop_reason` | str | 7.4% | 20 | Post-Funnel Audit | **DIRECT LEAKAGE** | **EXCLUDED** |
| `contacted_date` | str | 31.9% | 95 | Downstream Funnel | **DIRECT LEAKAGE** | **EXCLUDED** |
| `needs_assessed_date` | str | 60.5% | 98 | Downstream Funnel | **DIRECT LEAKAGE** | **EXCLUDED** |
| `quote_accepted_date` | str | 82.8% | 97 | Downstream Funnel | **DIRECT LEAKAGE** | **EXCLUDED** |
| `kyc_complete_date` | str | 88.2% | 99 | Downstream Funnel | **DIRECT LEAKAGE** | **EXCLUDED** |
| `activated_date` | str | 92.6% | 102 | Downstream Funnel | **DIRECT LEAKAGE** | **EXCLUDED** |
| `days_lead_to_activation` | float64 | 92.6% | 25 | Post-Activation | **DIRECT LEAKAGE** | **EXCLUDED** |
| `customer_follow_up_calls`| int64 | 0% | 6 | Downstream Interaction| **LEAKAGE** (accumulates) | **EXCLUDED** |
| `bundle_products` | str | 92.6% | 306 | Post-Quote Fulfillment| **DIRECT LEAKAGE** | **EXCLUDED** |
| `monthly_bundle_value_inr`| float64 | 92.6% | 326 | Post-Quote Contract | **DIRECT LEAKAGE** | **EXCLUDED** |
| `one_time_setup_inr` | float64 | 92.6% | 99 | Post-Quote Contract | **DIRECT LEAKAGE** | **EXCLUDED** |
| `contract_months` | float64 | 92.6% | 3 | Post-Quote Contract | **DIRECT LEAKAGE** | **EXCLUDED** |
| `churned_within_6_months`| str | 92.6% | 2 | Post-Activation Metric| **DIRECT LEAKAGE** | **EXCLUDED** |
| `nps_score` | float64 | 92.6% | 9 | Post-Activation Survey| **DIRECT LEAKAGE** | **EXCLUDED** |
| `acquisition_cost_inr` | int64 | 0% | 101 | Downstream Accounting| **LEAKAGE** (accumulates) | **EXCLUDED** |

---

## 5. Documented Feature Allowlist for ML Lead Propensity

The propensity scoring engine is permitted to use **only** the following features available at initial lead registration:

```json
{
  "categorical_features": [
    "lead_source",
    "business_type",
    "segment",
    "city",
    "state",
    "preferred_language",
    "annual_turnover_band",
    "has_gstin",
    "has_udyam",
    "current_internet",
    "current_provider",
    "contact_role"
  ],
  "numeric_features": [
    "city_tier",
    "employee_count",
    "num_sites",
    "monthly_telecom_spend_inr"
  ],
  "engineered_features": [
    "num_products_of_interest",
    "interested_in_connectivity",
    "interested_in_cloud_or_security",
    "created_day_of_week",
    "created_month",
    "spend_per_employee",
    "spend_per_site"
  ]
}
```

---

## 6. Segment and Source Insights

### 6.1 Segments vs. Activation Rate
- **Micro retail & services:** 2,709 leads (54.18%), 110 activations (**4.06% conversion rate**)
- **Professional offices:** 1,247 leads (24.94%), 138 activations (**11.07% conversion rate**)
- **Small multi-site businesses:** 755 leads (15.10%), 83 activations (**10.99% conversion rate**)
- **Small manufacturers:** 289 leads (5.78%), 37 activations (**12.80% conversion rate**)

### 6.2 Lead Sources vs. Activation Rate
- **Referral:** 413 leads, 61 activations (**14.77% conversion rate** — Highest performing channel)
- **Inbound call:** 504 leads, 48 activations (**9.52% conversion rate**)
- **Channel partner:** 1,010 leads, 81 activations (**8.02% conversion rate**)
- **Field sales:** 1,720 leads, 125 activations (**7.27% conversion rate**)
- **Website form:** 995 leads, 43 activations (**4.32% conversion rate**)
- **WhatsApp campaign:** 358 leads, 10 activations (**2.79% conversion rate** — Lowest performing channel)

