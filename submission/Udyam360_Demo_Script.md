# Udyam360 — Official 3-Minute Hackathon Demonstration Script

**Project:** Udyam360 — Making Small Businesses Digital in One Sitting  
**Track:** Airtel SYNC Hackathon 2026 — Enterprise Track A (Project Udyam Digital)  
**Total Target Duration:** 3 minutes 00 seconds (180 seconds)  
**Presenter:** Single Presenter or Co-Founding Duo  

---

## 1. Pre-Demo Environment & Browser Setup

### A. Terminal Commands to Start Services
Open two terminal windows:
```bash
# Terminal 1: Backend API (FastAPI)
cd backend
venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend Web App (Vite)
cd frontend
npm run dev
# Running on http://localhost:5173
```

### B. Pre-Loaded Browser Tabs
Prepare a single browser window (1080p / 1920x1080 resolution, 100% zoom) with 2 tabs:
1. **Tab 1 (Customer Journey):** `http://localhost:5173/` (Landing Page)
2. **Tab 2 (Admin Portal):** `http://localhost:5173/admin/overview` (Executive Dashboard)

### C. Recommended Demo Data (Pharmacy Customer Archetype)
* **Business Description:** *"I run Apollo Care Pharmacy in Bengaluru. We have 4 employees, 1 store, and our monthly telecom budget is around ₹4,000. We need fast broadband for billing and card payments, plus a calling SIM for home deliveries."*
* **Specimen KYC Document:** `data/specimens/sample_gstin_active.png` (or GSTIN: `29ABCDE1234F1Z5`, Apollo Care Pharmacy, Karnataka).
* **Gemini Fallback Step:** If internet connectivity drops or Gemini API rate limit occurs, type the same message; the backend's deterministic fallback extractor triggers automatically with zero latency or error prompt.

---

## 2. Timed Demonstration Walkthrough (180 Seconds)

### [0:00 – 0:20] The Problem: Fragmented Indian MSME Onboarding
* **Screen Displayed:** Tab 1 — `http://localhost:5173/` (Landing Page)
* **Visual Action:** Scroll smoothly past the hero section highlighting the two target archetypes: **Micro Retail** and **Professional Offices**. Hover over the 4-step journey badge.
* **Spoken Script:**
  > *"Every month, tens of thousands of Indian small businesses—from local kiranas to CA clinics—try to digitize. Today, that journey is broken. An MSME owner talks to multiple disconnected vendors, waits 3 to 5 days just to receive a manual quote, submits physical paper KYC, and waits an average of 17.6 days for activation. 
  > 
  > Welcome to **Udyam360**—Airtel’s AI-powered digital onboarding platform that takes an MSME from zero to digitally activated in one single sitting."*
* **Transition:** Click the primary red CTA: **"Start Digital Onboarding"** $\rightarrow$ Navigates to `/advisor`.

---

### [0:20 – 0:55] GenAI Business Advisor & Profile Extraction
* **Screen Displayed:** Tab 1 — `/advisor` (Conversational AI Advisor)
* **Visual Action:** 
  1. The welcome message loads from the advisor.
  2. Paste or type the demo prompt: *"I run Apollo Care Pharmacy in Bengaluru with 4 staff and ₹4,000 monthly spend. Need broadband and a calling SIM."*
  3. Send message. The live extraction badge updates on the right-hand panel, showing extracted archetype: *Micro Retail (Pharmacy)*, *Bengaluru (Tier 1)*, *Headcount: 4*, *Budget: ₹4,000/mo*.
* **Spoken Script:**
  > *"Instead of forcing a small business owner to navigate confusing telco product SKUs, our GenAI Advisor speaks their language. Powered by Gemini (gemini-3.1-flash-lite), it extracts the customer's business archetype, location, and telecom budget in real-time. 
  > 
  > Crucially, we enforce strict architectural boundaries: Gemini understands the conversation, but all product eligibility, catalog pricing, and commercial bundles are computed 100% deterministically on our backend."*
* **Transition:** Click **"View Recommended Bundles"** $\rightarrow$ Navigates to `/recommendations`.

---

### [0:55 – 1:20] Intelligent Bundles & Transparent Quote Preview
* **Screen Displayed:** Tab 1 — `/recommendations` & `/quote`
* **Visual Action:**
  1. Show the 3 dynamically scored bundles: **Essential** (lowest cost), **Growth** (recommended fit), and **Premium**.
  2. Point out the Growth bundle: *Airtel Office Internet (100 Mbps) + Airtel Business Calling SIM*.
  3. Select **Growth Bundle** and toggle the optional *Airtel Cloud Voice* add-on.
  4. Click **"Review Formal Quote"** $\rightarrow$ On `/quote`, point to the clear itemized separation of Monthly Recurring Charges (₹2,198/mo) vs. One-Time Setup Charges (₹1,000).
* **Spoken Script:**
  > *"The engine evaluates 25 products from the supplied product catalogue and generates three tailored packages: Essential, Growth, and Premium. For Apollo Pharmacy, it recommends our Growth bundle with broadband and business calling. 
  > 
  > Moving into quote preview, pricing is completely transparent and itemized. We strictly distinguish Monthly Recurring Charges from One-Time Setup fees, preventing the quote shock that causes 56.4% of leads to drop between needs assessment and quote acceptance."*
* **Transition:** Click **"Accept Quote & Proceed to KYC"** $\rightarrow$ Navigates to `/kyc`.

---

### [1:20 – 1:55] Smart KYC: DPDP Consent, Local OCR & Mock Verification
* **Screen Displayed:** Tab 1 — `/kyc`
* **Visual Action:**
  1. Point out the explicit **Digital Personal Data Protection (DPDP) Consent Gate**. Check the mandatory consent box.
  2. Upload the specimen GSTIN certificate (`sample_gstin_active.png`).
  3. Click **"Verify Documents"**. The spinner runs local OCR extraction.
  4. Show the verified results card: *GSTIN verified against local mock registry, Trade Name matches Apollo Care Pharmacy, Document Freshness confirmed*.
* **Spoken Script:**
  > *"Now to Smart KYC. We implement an explicit DPDP consent gate before any document is uploaded. 
  > 
  > For document extraction, we run a local on-premises OCR engine. No customer document bytes or identity details are ever sent to Gemini or external cloud LLMs. The extracted registration is verified in milliseconds against our mock GSTIN registry, performing automated cross-document identity and address matching."*
* **Transition:** Click **"Submit Order"** $\rightarrow$ Navigates to `/track-order`.

---

### [1:55 – 2:20] Instant Order Confirmation & Simulated Activation
* **Screen Displayed:** Tab 1 — `/track-order`
* **Visual Action:**
  1. Point out the prototype generated **Order Reference** (`ORD-XXXXX`).
  2. Show the visual progression state machine: *Order Created $\rightarrow$ KYC Verified $\rightarrow$ Provisioning $\rightarrow$ Simulated Activation*.
  3. Point to the explicit notice badge: *"Notice: Simulated telecom provisioning in hackathon environment."*
* **Spoken Script:**
  > *"The customer immediately receives their prototype Order Reference. With automated verification complete, the order moves directly through provisioning into simulated activation. 
  > 
  > What historically took an average of 17.6 days of back-and-forth manual paperwork is now concluded in this 3-minute prototype onboarding demonstration, with zero physical touchpoints."*
* **Transition:** Switch to Browser Tab 2 — `http://localhost:5173/admin/overview`.

---

### [2:20 – 2:50] Executive Admin Intelligence & Calibrated Propensity Scoring
* **Screen Displayed:** Tab 2 — `/admin/overview`, `/admin/leads`, and `/admin/model`
* **Visual Action:**
  1. **Overview:** Show the 6-stage funnel telemetry and drop-off rates on 5,000 leads.
  2. **Leads View (`/admin/leads`):** Show the 4,632 actionable unconverted leads categorized into **569 High**, **1,564 Medium**, and **2,499 Low** propensity tiers, with 368 already-activated accounts cleanly excluded.
  3. **Model Hub (`/admin/model`):** Highlight the **Platt Calibrated Brier score of 0.0666** beating the naive baseline of **0.0680**, with exact linear log-odds transparency (+166% odds for referrals, -72% for WhatsApp broadcast).
* **Spoken Script:**
  > *"On the enterprise sales side, our Executive Admin Portal turns raw data into action. Across 5,000 hackathon leads, we diagnose exact funnel drop-offs. 
  > 
  > For unconverted accounts, our ML Propensity Engine ranks 4,632 actionable leads. Crucially, we exclude already-activated customers, and we calibrated our model with Platt scaling, achieving a test Brier score of 0.0666 that beats the naive baseline. Sales reps get interpretable logistic-regression odds ratios with zero data leakage."*

---

### [2:50 – 3:00] Closing & Value Proposition
* **Screen Displayed:** Tab 2 — Returning to top of `/admin/overview` or Tab 1 Hero
* **Spoken Script:**
  > *"Udyam360 delivers the future of Indian MSME telecommunications: natural AI conversation, deterministic commercial trust, privacy-first local KYC, and calibrated sales intelligence. 
  > 
  > Fast, compliant, and ready to scale. Thank you!"*

---

## 3. Demo Contingency & Fallback Checklist

| Scenario | Risk | Automatic Safeguard / Presenter Action |
| :--- | :--- | :--- |
| **No Internet / Gemini Outage** | Cloud LLM fails or times out | Backend automatically triggers rule-based regex and keyword extractor. The advisor continues seamlessly. |
| **Port 8000 Conflict** | Another process on 8000 | Kill blocking process: `netstat -ano \| findstr :8000` $\rightarrow$ `taskkill /PID <PID> /F`. |
| **Document Upload Lag** | Large specimen file slow to OCR | Pre-load `sample_gstin_active.png` (lightweight 150 KB test specimen) in the file picker. |
| **Admin Route Permissions** | Missing header error in dev | In demo UI, the frontend Axios client automatically injects `X-Admin-Role: ExecutiveAdmin`. |

