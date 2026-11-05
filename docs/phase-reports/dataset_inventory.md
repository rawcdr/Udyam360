# Dataset Inventory & Validation Report

**Project:** Udyam360 (Airtel SYNC Hackathon 2026 — Enterprise Track A, Project Udyam Digital)  
**Date:** 2026-11-05  
**Discovered Dataset Directory:** `YTL_TrackA_Udyam_Digital_Data`  
**Location:** `c:\Users\adifr\OneDrive\Desktop\Udyam360\YTL_TrackA_Udyam_Digital_Data`  

---

## 1. Executive Summary

A comprehensive automated inspection of the hackathon dataset was performed on the existing extracted directory. All 4 primary CSV datasets, the KYC document folder, and the dataset documentation were discovered, structurally intact, and uncorrupted.

| Dataset Item | Expected Benchmark | Actual Verified | Verification Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `product_catalogue.csv` | 25 records | 25 records, 16 cols | **PASS** | 0 duplicates; catalog of telecom & SaaS products |
| `smb_leads.csv` | 5,000 records | 5,000 records, 40 cols | **PASS** | 0 duplicates; complete quarterly funnel data |
| `mock_gstin_registry.csv` | 3,534 records | 3,534 records, 8 cols | **PASS** | 0 duplicates; matches leads with `has_gstin = 'Y'` |
| `mock_udyam_registry.csv` | 2,723 records | 2,723 records, 8 cols | **PASS** | 0 duplicates; matches leads with `has_udyam = 'Y'` |
| `kyc_documents/` | 47 images (12 applicants) | 47 PNG images (12 applicants) | **PASS** | Applicants K01–K12; all PNG format |
| `README.md` | Present | Present (69 lines) | **PASS** | Contains core synthetic validation rules |

---

## 2. Detailed File Inventories

### 2.1. Product Catalogue (`product_catalogue.csv`)
- **Row count:** 25
- **Column count:** 16
- **Duplicate rows:** 0
- **Columns:**
  1. `product_id` (object - e.g. P01..P25)
  2. `category` (object - 5 categories: Connectivity, Communication, Cloud & Productivity, Security, IoT & Physical)
  3. `product_name` (object)
  4. `description` (object)
  5. `unit` (object)
  6. `price_min_inr_per_month` (int64)
  7. `price_max_inr_per_month` (int64)
  8. `one_time_setup_inr` (int64)
  9. `min_contract_months` (int64)
  10. `available_city_tiers` (object - e.g. "1,2")
  11. `min_employees` (int64)
  12. `min_sites` (int64)
  13. `requires_gstin` (object - 'Y' for 10 products, 'N' for 15 products)
  14. `requires_one_of` (object - 18 missing values where no prerequisite product is needed; 7 products have dependencies delimited by `|`)
  15. `typical_install_days` (int64)
  16. `target_segments` (object)

### 2.2. SMB Leads (`smb_leads.csv`)
- **Row count:** 5,000
- **Column count:** 40
- **Duplicate rows:** 0
- **Segment distribution:**
  - `Micro retail & services`: 2,709 (54.18%) — **Primary Target Segment 1**
  - `Professional offices`: 1,247 (24.94%) — **Primary Target Segment 2**
  - `Small multi-site businesses`: 755 (15.10%)
  - `Small manufacturers`: 289 (5.78%)
- **Funnel Drop-off & Stage Analysis:**
  - `Lead`: 1,594
  - `Contacted`: 1,432
  - `Needs assessed`: 1,113
  - `Quote accepted`: 273
  - `KYC complete`: 220
  - `Activated`: 368 (Overall conversion: 7.36%)
- **Outcome:** Dropped: 4,632 | Activated: 368
- **Geographic distribution:** Tier 1: 2,578 leads | Tier 2: 2,422 leads
- **Registration penetration:**
  - `has_gstin = 'Y'`: 3,534 leads (exactly corresponds to mock GSTIN records)
  - `has_udyam = 'Y'`: 2,723 leads (exactly corresponds to mock Udyam records)

### 2.3. Mock GSTIN Registry (`mock_gstin_registry.csv`)
- **Row count:** 3,534
- **Column count:** 8
- **Duplicate rows:** 0
- **Missing values:** 0
- **Columns:** `gstin`, `legal_name`, `trade_name`, `constitution`, `principal_place_of_business`, `state`, `registration_date`, `status`
- **Status breakdown:**
  - `Active`: 3,266 (92.42%)
  - `Cancelled`: 167 (4.73%)
  - `Suspended`: 101 (2.86%)
- **Constitution breakdown:**
  - `Proprietorship`: 2,443 (69.13%)
  - `Private Limited Company`: 631 (17.86%)
  - `Limited Liability Partnership`: 460 (13.02%)

### 2.4. Mock Udyam Registry (`mock_udyam_registry.csv`)
- **Row count:** 2,723
- **Column count:** 8
- **Duplicate rows:** 0
- **Missing values:** 0
- **Columns:** `udyam_number`, `enterprise_name`, `enterprise_type`, `major_activity`, `nic_description`, `state`, `city`, `date_of_registration`
- **Enterprise Type breakdown:**
  - `Micro`: 1,833 (67.32%)
  - `Small`: 737 (27.07%)
  - `Medium`: 153 (5.62%)
- **Major Activity breakdown:**
  - `Trading`: 1,678 (61.62%)
  - `Services`: 787 (28.90%)
  - `Manufacturing`: 258 (9.48%)

### 2.5. KYC Document Specimen Pool (`kyc_documents/`)
- **Total files:** 47
- **Format:** 100% PNG (`.png`)
- **Applicants:** 12 distinct applicants (`K01` through `K12`)
- **Document breakdown per applicant:**
  - Applicants `K01`, `K02`, `K03`, `K04`, `K06`, `K07`, `K08`, `K09`, `K10`, `K11`, `K12` each possess 4 specimen documents:
    1. `address_proof.png`
    2. `gst_certificate.png`
    3. `signatory_id.png`
    4. `udyam_certificate.png`
  - Applicant `K05` possesses 3 specimen documents:
    1. `address_proof.png`
    2. `gst_certificate.png`
    3. `signatory_id.png`
    *(Missing `udyam_certificate.png` — an intentional KYC anomaly for edge-case verification)*

---

## 3. Preserved Synthetic Validation Rules & Conventions

From `YTL_TrackA_Udyam_Digital_Data/README.md`, the following domain rules must be enforced in subsequent application phases:

1. **Synthetic GSTIN Format Convention:**
   - Follows the real 15-character Indian GSTIN structure with valid checksum.
   - The 4th character of the embedded PAN is always `'X'` (which is not a real income tax entity code, preventing collision with actual taxpayers).
   - *Rule:* The GSTIN format validator must accept `'X'` as the 4th character.

2. **Synthetic Udyam Registration Convention:**
   - Format: `UDYAM-XX-00-XXXXXXX`
   - Uses district code `00` (which does not exist in real Udyam records).
   - *Rule:* The Udyam validator must accept district code `00`.

3. **Temporal Baseline Date:**
   - The reference baseline "today" for all date-dependent checks (e.g., document freshness, KYC address proof validity within 90 days, install timelines) is strictly **`2026-07-15`**.

4. **Product Eligibility Constraints:**
   - `available_city_tiers`: Restricts product to Tier 1 or Tier 2.
   - `min_employees` and `min_sites`: Hard minimum thresholds.
   - `requires_gstin = 'Y'`: Cannot be quoted without an Active GSTIN.
   - `requires_one_of`: Cross-product dependency requirement (delimited by `|`).

5. **Privacy and Masking Requirements:**
   - PII (names, contact details, identifiers) must be masked in terminal logs, UI displays, and reports.
   - Retention policy and customer consent notice required before KYC processing.

---

## 4. Discrepancies and Observations

- **No missing files:** All files mentioned in the hackathon brief exist in the dataset directory.
- **Exact record match:** Every row count matches the exact expected figure.
- **Data integrity:** No corrupt rows, no unexpected duplicate records found.
- **Target customer alignment:** Micro retail (2,709 leads) and Professional offices (1,247 leads) represent 79.12% of the dataset, perfectly aligning with Udyam360's core target focus.

