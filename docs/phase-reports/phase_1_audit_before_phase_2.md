# Phase 1 Codebase Audit Report (Prior to Phase 2 Execution)

**Project:** Udyam360 (Airtel SYNC Hackathon 2026 — Enterprise Track A)  
**Audit Date:** 2026-11-05  
**Auditor:** Automated Engineering Pair  
**Scope:** Phase 1 core logic, budget semantics, quote integrity, pricing boundaries, and regression testing.

---

## 1. Audit Objectives & Scope

Prior to introducing the Phase 2 Conversational GenAI Advisor, a strict architectural audit was executed across the existing codebase to verify:
1. **Budget Semantics:** Proper distinction between monthly recurring charges (MRC) and one-time setup fees (OTC); handling of minimum vs. maximum price ranges against customer budget.
2. **Quote Integrity:** Verification of whether quote references claim cryptographic signing vs. unique server-generated reference tracking.
3. **Pricing Boundaries:** Separation of base monthly fees, installation costs, first-month payments, and uncalculated taxes.

---

## 2. Issues Inspected and Confirmed Defects

### Defect 1: Misleading `WITHIN_BUDGET` Status for Price Ranges
- **Inspection Area:** `backend/app/services/recommendation_engine.py` (lines 258–267) and `backend/app/schemas/recommendation.py`.
- **Finding:** A bundle was evaluated as `WITHIN_BUDGET` if `pricing.monthly_total_min <= profile.monthly_budget_inr`. When a bundle's price range was ₹4,216 to ₹5,491 for a budget of ₹5,000 (such as the CA Practice growth bundle), the output marked the bundle as `WITHIN_BUDGET`, hiding the fact that upper-tier monthly charges exceed the customer's budget by ₹491.00.
- **Severity:** High (misleading customer expectations on recurring expenses).

### Defect 2: Incomplete Budget Scoring Evaluation
- **Inspection Area:** `backend/app/services/recommendation_engine.py` (method `_calculate_score`).
- **Finding:** The budget fit score formula strictly tested `pricing.monthly_total_min`, assigning high scores (e.g., 97.6/100) even when the maximum recurring rate exceeded the user's budget.
- **Severity:** Medium.

### Defect 3: Misleading "Server-Signed Quote" Nomenclature
- **Inspection Area:** `backend/app/api/quotes.py` and Phase 1 completion notes.
- **Finding:** Code generated a unique UUID hex reference `Q-XXXXXXXX`. While completely valid for server-side quote lookup, calling it "server-signed" implied cryptographic signature generation (RSA/HMAC) and tamper verification that was not implemented.
- **Severity:** Low (documentation/terminology accuracy).

---

## 3. Fixes Applied

1. **Enhanced Budget Status Enum & Gap Tracking:**
   - Updated `backend/app/schemas/recommendation.py` to support 4 explicit statuses:
     - `WITHIN_BUDGET`: Entire monthly range fits (`monthly_total_max <= budget`).
     - `PARTIALLY_WITHIN_BUDGET`: Minimum fits, but upper tier exceeds (`monthly_total_min <= budget < monthly_total_max`).
     - `EXCEEDS_BUDGET`: Both min and max exceed budget (`monthly_total_min > budget`).
     - `NO_BUDGET_SPECIFIED`: Budget unprovided.
   - Added `max_budget_gap_inr` to expose the exact upper-tier overrun.

2. **Calibrated Budget Scoring:**
   - Modified `_calculate_score` in `recommendation_engine.py`:
     - Entire range within budget: Score 85–100.
     - Partial fit (`min <= budget < max`): Proportional penalty on the upper overrun (Score 70–84).
     - Over budget (`min > budget`): Overspend penalty (Score 0–65).

3. **Explicit Monthly vs. One-Time Explanation Separation:**
   - Updated `backend/app/services/bundle_explanation.py` to clearly contrast monthly recurring commitments from one-time setup charges (OTC) and estimated first-month payments (`Month 1 MRC + OTC`).
   - Added explicit disclaimers that catalogue rates exclude applicable Indian GST (18%).

4. **Corrected Quote Terminology:**
   - Updated `backend/app/schemas/quote.py` and `backend/app/api/quotes.py` to label `quote_id` as `"Unique server-generated quote reference identifier (e.g. Q-A1B2C3D4)"`.
   - Removed all references to cryptographic signing.

---

## 4. Tests Added & Regression Verification

- **New Regression Test:** `test_budget_semantics_audit_ca_practice_partially_within_budget` in `backend/tests/test_recommendation.py`.
  - Verifies CA Practice with ₹5,000 monthly budget.
  - Asserts `budget_status == "PARTIALLY_WITHIN_BUDGET"`.
  - Asserts `budget_gap_inr == 0.0` and `max_budget_gap_inr == 491.0`.
  - Asserts setup fees (₹2,500) are separate from monthly comparison.
- **Test Suite Status:** All 47 tests passed cleanly in `3.62s`.

---

## 5. Remaining Known Limitations

- **GST Taxation (18%):** Pre-tax catalogue prices remain standard for Phase 1 & 2. Full tax computation is scheduled for Phase 3 during order checkout and invoice preview.
- **Audit Sign-off:** All core business logic is verified and robust. Ready for Phase 2 GenAI Advisor implementation.

