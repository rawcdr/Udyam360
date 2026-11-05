# Product Catalogue Schema Analysis & Engine Mapping

**Project:** Udyam360 (Airtel SYNC Hackathon 2026 — Enterprise Track A)  
**Dataset Source:** `YTL_TrackA_Udyam_Digital_Data/product_catalogue.csv`  
**Records Analyzed:** 25 products  
**Document Purpose:** Detailed column-by-column analysis defining types, domain constraints, synthetic conventions, and mapping to the eligibility, recommendation, and pricing engines.

---

## 1. Catalogue Overview

The product catalogue contains 25 telecom, cloud, and digital security solutions offered by Accel Business for Indian SMBs. The portfolio covers 5 categories:

| Category | Product Count | Product Range | Primary Use Case |
| :--- | :---: | :--- | :--- |
| **Connectivity** | 11 | P01–P11 | Fibre, 5G FWA, Leased Lines, Mobile, Failover, SD-WAN, Static IP |
| **Communication** | 4 | P12–P15 | Cloud Telephony / SIP, Toll-Free 1800, Business SMS, WhatsApp API |
| **Cloud & Productivity**| 4 | P16–P19 | Business Email (M365/Google), Cloud Backup, Website, Cloud POS |
| **Security** | 3 | P20–P22 | Endpoint Antivirus/EDR, Managed Firewall, Secure Guest Wi-Fi |
| **IoT & Physical** | 3 | P23–P25 | Cloud CCTV, Industrial Machine IoT, Fleet GPS Tracker |

---

## 2. Column-by-Column Schema Specification

### 2.1. `product_id`
- **Data Type:** String (Format: `P[0-9]{2}`, e.g., `P01` to `P25`)
- **Nullability:** Non-nullable, unique primary key across all 25 rows.
- **Engine Usage:** Universal primary key referenced by customer profiles, bundle definitions, dependency graph, quote generation, and order tracking.

### 2.2. `category`
- **Data Type:** String Enum (`Connectivity`, `Communication`, `Cloud & Productivity`, `Security`, `IoT & Physical`)
- **Nullability:** Non-nullable.
- **Engine Usage:**
  - Filtering by customer-requested categories (`required_categories`).
  - Diversification in bundle generation (ensuring growth and premium bundles span connectivity + cloud + security).
  - Category-level preference scoring for customer segments.

### 2.3. `product_name`
- **Data Type:** String (e.g. `Biz Fibre 100`, `Cloud POS & Billing`)
- **Nullability:** Non-nullable.
- **Engine Usage:** Customer-facing display, quote line items, explanation text generation.

### 2.4. `description`
- **Data Type:** String
- **Nullability:** Non-nullable.
- **Engine Usage:** Explains bundle suitability and technical specifications (e.g., speed, SLA, user tier) to the business owner.

### 2.5. `unit` (Pricing Unit & Billing Basis)
- **Data Type:** String Enum
- **Actual Values:**
  - `per site` (10 products: P01, P02, P03, P04, P05, P06, P09, P10, P21, P22)
  - `per line` (2 products: P07, P08)
  - `per IP` (1 product: P11)
  - `per channel` (1 product: P12)
  - `per number` (1 product: P13)
  - `per pack` (1 product: P14)
  - `per account` (3 products: P15, P17, P18)
  - `per user` (1 product: P16)
  - `per counter` (1 product: P19)
  - `per device` (2 products: P20, P24)
  - `per camera` (1 product: P23)
  - `per vehicle` (1 product: P25)
- **Engine Usage:**
  - Governs quantity multipliers in the Pricing Engine.
  - Multipliers adapt to business profile attributes:
    - `per site`: multiplied by `profile.num_sites` (default 1).
    - `per user`: multiplied by `profile.employee_count` (or requested user count).
    - `per line`: multiplied by requested business mobile lines (or employee count).
    - `per counter`: multiplied by retail billing counters (default 1 per store site).
    - `per device`: multiplied by protected PC/phone device count.
    - `per camera`: multiplied by CCTV camera count requested.

### 2.6. `price_min_inr_per_month` & `price_max_inr_per_month`
- **Data Type:** Integer (INR)
- **Range:** ₹99 to ₹25,000 (min), ₹149 to ₹35,000 (max).
- **Engine Usage:**
  - Evaluates monthly recurring charge (MRC) range for each product line item.
  - Used in budget constraint scoring: compares sum of `price_min_inr_per_month` against `profile.monthly_budget_inr`.
  - Enables transparent minimum-to-maximum cost projection.

### 2.7. `one_time_setup_inr`
- **Data Type:** Integer (INR)
- **Range:** ₹0 to ₹15,000 (e.g., Leased lines have ₹10k–₹15k installation; Cloud POS has ₹2,500; broadband has ₹0).
- **Engine Usage:**
  - Calculates non-recurring setup charges (OTC).
  - Distinguishes upfront Day-1 onboarding costs from ongoing monthly operational costs.

### 2.8. `min_contract_months`
- **Data Type:** Integer (Months: 1, 3, 6, 12, 24)
- **Distribution:**
  - 1 month: P07, P08, P14
  - 3 months: P15
  - 6 months: P04 (Biz 5G AirFiber)
  - 12 months: 16 products (Standard broadband, SaaS, Wi-Fi, CCTV)
  - 24 months: P06 (ILL 100), P10 (SD-WAN), P21 (Firewall), P24 (Machine IoT)
- **Engine Usage:**
  - Contractual commitment disclosure in quote preview.
  - Contract term matching if the customer specifies maximum commitment tolerance.

### 2.9. `available_city_tiers`
- **Data Type:** String (`"1;2"` or `"1"`)
- **Values:**
  - `P03` (Biz Fibre 1G): Available **only** in Tier 1 (`"1"`).
  - All other 24 products: Available in both Tier 1 and Tier 2 (`"1;2"`).
- **Engine Usage:** Hard eligibility check against `profile.city_tier`. A Tier 2 business profile is strictly ineligible for `P03`.

### 2.10. `min_employees`
- **Data Type:** Integer
- **Thresholds:**
  - `1`: 18 products (accessible to solo entrepreneurs / micro businesses)
  - `3`: P12 (Cloud Telephony / SIP)
  - `5`: P03 (Biz Fibre 1G)
  - `10`: P05 (ILL 20), P10 (SD-WAN), P21 (Managed Firewall), P24 (Machine IoT)
  - `25`: P06 (ILL 100)
- **Engine Usage:** Hard eligibility check. A customer with `employee_count < min_employees` is marked `INELIGIBLE` for that product.

### 2.11. `min_sites`
- **Data Type:** Integer
- **Thresholds:**
  - `3`: P10 (Managed SD-WAN requires at least 3 distributed branches/sites)
  - `1`: All other 24 products
- **Engine Usage:** Hard eligibility check. Single-site businesses cannot buy P10.

### 2.12. `requires_gstin`
- **Data Type:** String (`'Y'` or `'N'`)
- **Breakdown:** 10 products require GSTIN (`'Y'`), 15 do not (`'N'`).
- **Engine Usage:** Hard eligibility check against `profile.has_gstin`. If `has_gstin == False`, products with `requires_gstin == 'Y'` are marked `INELIGIBLE`. If `has_gstin` is unknown/unprovided, the product is marked `NEEDS_INFORMATION`.

### 2.13. `requires_one_of` (Dependency Rule)
- **Data Type:** String or NaN (Pipe-delimited product IDs, e.g., `P01|P02|P03|P05|P06`)
- **Rules Defined:**
  - `P09` (Backup Failover): requires one of `P01|P02|P03|P05|P06`
  - `P10` (Managed SD-WAN): requires one of `P01|P02|P03|P05|P06`
  - `P11` (Static IP): requires one of `P01|P02|P03`
  - `P12` (Cloud Telephony / SIP): requires one of `P01|P02|P03|P04|P05|P06`
  - `P21` (Managed Firewall): requires one of `P01|P02|P03|P05|P06`
  - `P22` (Secure Wi-Fi): requires one of `P01|P02|P03|P04`
  - `P23` (Cloud CCTV): requires one of `P01|P02|P03|P04|P05|P06`
- **Engine Usage:** Dependency resolution engine. If an add-on or required product is selected, the engine verifies that at least one prerequisite is present in the bundle; if not, it automatically injects the most suitable eligible prerequisite or flags `DEPENDENCY_REQUIRED`.

### 2.14. `typical_install_days`
- **Data Type:** Integer (1 to 30 days)
- **Engine Usage:**
  - Bundle estimated delivery time: calculated as `max(typical_install_days)` of all included products.
  - Used in quote preview and Phase 3 order tracking.

### 2.15. `target_segments`
- **Data Type:** Semicolon-delimited String codes (`micro`, `prof`, `multi`, `mfg`)
- **Mapping:**
  - `micro`: Micro Retail & Services (9 products)
  - `prof`: Professional Offices (18 products)
  - `multi`: Small Multi-site Businesses (18 products)
  - `mfg`: Small Manufacturers (13 products)
- **Engine Usage:**
  - Segment suitability scoring (boosting products natively mapped to the customer's segment).
  - Default candidate pool filtering when generating segment-specific bundles.

---

## 3. Product-to-Segment Matrix

| Product ID | Product Name | Target Segments | Requires GSTIN | Prerequisite Dependencies |
| :--- | :--- | :--- | :---: | :--- |
| **P01** | Biz Fibre 100 | `micro;prof` | N | None |
| **P02** | Biz Fibre 300 | `prof;multi` | N | None |
| **P03** | Biz Fibre 1G | `prof;multi;mfg` | Y | None (Tier 1 only, min 5 emp) |
| **P04** | Biz 5G AirFiber 100 | `micro;prof` | N | None |
| **P05** | Internet Leased Line 20 | `mfg;multi` | Y | None (min 10 emp) |
| **P06** | Internet Leased Line 100 | `mfg` | Y | None (min 25 emp) |
| **P07** | Business Postpaid 299 | `micro;prof;multi;mfg` | N | None |
| **P08** | Business Postpaid 599 | `prof;multi;mfg` | N | None |
| **P09** | Backup 4G/5G Failover | `multi;prof` | N | P01 \| P02 \| P03 \| P05 \| P06 |
| **P10** | Managed SD-WAN | `multi` | Y | P01 \| P02 \| P03 \| P05 \| P06 (min 3 sites, min 10 emp) |
| **P11** | Static IP | `prof;mfg` | N | P01 \| P02 \| P03 |
| **P12** | Cloud Telephony / SIP | `prof;multi` | Y | P01 \| P02 \| P03 \| P04 \| P05 \| P06 (min 3 emp) |
| **P13** | Toll-free Number | `multi;prof` | Y | None |
| **P14** | Business SMS 10k | `prof;multi;micro` | Y | None |
| **P15** | WhatsApp Business API | `micro;prof;multi` | Y | None |
| **P16** | Cloud Email & Office Suite | `prof;multi;mfg` | N | None |
| **P17** | Cloud Backup 1 TB | `prof;mfg` | N | None |
| **P18** | Website + Domain Starter | `micro;prof` | N | None |
| **P19** | Cloud POS & Billing | `micro;multi` | N | None |
| **P20** | Endpoint Security | `prof;mfg;multi` | N | None |
| **P21** | Managed Firewall | `mfg;multi;prof` | Y | P01 \| P02 \| P03 \| P05 \| P06 (min 10 emp) |
| **P22** | Secure Wi-Fi with Guest Net | `micro;multi;prof` | N | P01 \| P02 \| P03 \| P04 |
| **P23** | Cloud CCTV | `micro;multi;mfg` | N | P01 \| P02 \| P03 \| P04 \| P05 \| P06 |
| **P24** | Machine Monitoring IoT | `mfg` | Y | None (min 10 emp) |
| **P25** | Fleet Tracker | `multi;mfg` | N | None |

---

## 4. Architectural Rules for Phase 1 Engine

1. **Deterministic Execution:** No LLM or non-deterministic heuristic is used for scoring or bundle assembly.
2. **Hard Ineligibility Pruning:** Hard constraints (`city_tier`, `min_employees`, `min_sites`, `requires_gstin`) are evaluated strictly prior to bundle generation.
3. **Graph Dependency Closure:** Any candidate bundle missing a prerequisite is either repaired by adding the lowest-cost eligible prerequisite or discarded.
4. **Transparent Scoring:** Score is normalized to 0–100 with clear weights:
   - 50% Requirement Match
   - 25% Budget Fit
   - 15% Catalogue Eligibility & Completeness
   - 10% Segment Suitability
5. **Exact Arithmetic:** All pricing reflects actual catalogue unit rates multiplied by verified profile quantities.

