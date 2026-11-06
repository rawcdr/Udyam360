import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    # 16:9 widescreen
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    
    # Color palette
    AIRTEL_RED = RGBColor(225, 29, 72)     # #E11D48
    SLATE_DARK = RGBColor(15, 23, 42)      # #0F172A
    SLATE_GRAY = RGBColor(71, 85, 105)     # #475569
    SLATE_LIGHT = RGBColor(241, 245, 249)  # #F1F5F9
    WHITE = RGBColor(255, 255, 255)
    EMERALD = RGBColor(16, 185, 129)       # #10B981
    BORDER_COLOR = RGBColor(203, 213, 225) # #CBD5E1

    def add_header(slide, title_text, category_text="AIRTEL SYNC HACKATHON 2026 • ENTERPRISE TRACK A"):
        # Header category
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = AIRTEL_RED

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.6))
        tf_t = title_box.text_frame
        tf_t.word_wrap = True
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.font.size = Pt(22)
        p_t.font.bold = True
        p_t.font.color.rgb = SLATE_DARK

    def add_card(slide, left, top, width, height, title, body_paragraphs, bg_color=WHITE, border_color=BORDER_COLOR):
        # Card background
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.2)
        
        # Text
        tb = slide.shapes.add_textbox(Inches(left + 0.25), Inches(top + 0.2), Inches(width - 0.5), Inches(height - 0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        
        if title:
            p0 = tf.paragraphs[0]
            p0.text = title
            p0.font.size = Pt(14)
            p0.font.bold = True
            p0.font.color.rgb = SLATE_DARK
            p0.space_after = Pt(6)
            first_body = True
        else:
            first_body = False
            
        for text in body_paragraphs:
            p = tf.add_paragraph() if (title or not first_body) else tf.paragraphs[0]
            first_body = False
            p.text = text
            p.font.size = Pt(10.5)
            p.font.color.rgb = SLATE_GRAY
            p.space_after = Pt(4)

    # -------------------------------------------------------------
    # SLIDE 1: Title & Vision
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = SLATE_DARK
    bg1.line.fill.background()

    # Red accent pill
    pill = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.4), Inches(4.2), Inches(0.45))
    pill.fill.solid()
    pill.fill.fore_color.rgb = AIRTEL_RED
    pill.line.fill.background()
    p_pill = pill.text_frame.paragraphs[0]
    p_pill.text = "AIRTEL SYNC HACKATHON 2026 • TRACK A"
    p_pill.font.size = Pt(11)
    p_pill.font.bold = True
    p_pill.font.color.rgb = WHITE
    p_pill.alignment = PP_ALIGN.CENTER

    tb1 = s1.shapes.add_textbox(Inches(1.2), Inches(2.1), Inches(10.9), Inches(3.2))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    
    p_title = tf1.paragraphs[0]
    p_title.text = "Udyam360"
    p_title.font.size = Pt(54)
    p_title.font.bold = True
    p_title.font.color.rgb = WHITE
    p_title.space_after = Pt(10)
    
    p_sub = tf1.add_paragraph()
    p_sub.text = "Making Small Businesses Digital in One Sitting"
    p_sub.font.size = Pt(26)
    p_sub.font.bold = True
    p_sub.font.color.rgb = AIRTEL_RED
    p_sub.space_after = Pt(16)
    
    p_vp = tf1.add_paragraph()
    p_vp.text = "An AI-powered digital onboarding and sales intelligence platform for Indian MSMEs — collapsing a 17.6-day average fragmented onboarding ordeal into a 3-minute prototype onboarding demonstration, catalogue-grounded, privacy-first digital experience (simulated provisioning)."
    p_vp.font.size = Pt(14)
    p_vp.font.color.rgb = RGBColor(203, 213, 225)
    
    # Footer metadata
    tb1_foot = s1.shapes.add_textbox(Inches(1.2), Inches(5.8), Inches(10.9), Inches(0.8))
    p_f = tb1_foot.text_frame.paragraphs[0]
    p_f.text = "Enterprise Track A: Project Udyam Digital  |  Target Archetypes: Micro Retail & Professional Offices"
    p_f.font.size = Pt(12)
    p_f.font.color.rgb = RGBColor(148, 163, 184)

    # -------------------------------------------------------------
    # SLIDE 2: Problem & Opportunity
    # -------------------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "The MSME Onboarding Crisis in Indian Telecom", "THE PROBLEM & MARKET FRICTION")
    
    add_card(s2, 0.8, 1.6, 3.6, 4.8, "1. Fragmented Buying Journey", [
        "• Multiple Uncoordinated Vendors: A merchant buys broadband from one vendor, POS terminal from another, calling SIMs elsewhere.",
        "• 56.4% Drop from Needs Assessed to Quote Accepted: MSMEs experience acute quote shock when hidden fees and disconnected charges are delivered.",
        "• Confusing Telecom SKUs: Small business owners do not know whether they need DIA, MPLS, or FWA."
    ])
    add_card(s2, 4.8, 1.6, 3.6, 4.8, "2. High Friction KYC & Compliance", [
        "• Physical Paperwork & Manual Email: Physical document pickup and xerox copies cause 3-5 days in administrative latency.",
        "• Cross-Document Identity Mismatches: Spelling inconsistencies between GSTIN, PAN, and trade licenses trigger frequent rejections.",
        "• Privacy Insecurities: Sensitive business identity documents circulated across informal WhatsApp channels."
    ])
    add_card(s2, 8.8, 1.6, 3.6, 4.8, "3. Painful Delays & High Telco CAC", [
        "• 17.6 Days Lead-to-Activation: Historical telecom benchmark across 5,000 leads in dataset.",
        "• ₹15,000 Approximate CAC: Heavy field sales overhead, physical site visits, and repetitive follow-ups.",
        "• 3+ Status Follow-up Calls: Customers repeatedly call customer care asking for provisioning updates."
    ])

    # -------------------------------------------------------------
    # SLIDE 3: Our Solution
    # -------------------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Udyam360: A Unified Five-Stage Onboarding Flow", "END-TO-END CUSTOMER JOURNEY")

    steps = [
        ("1. Discover", "Conversational AI Advisor conducts natural dialogue in plain English/Hinglish. Extracts archetype, headcount, budget."),
        ("2. Recommend", "Deterministic engine maps needs to 25 products from the supplied product catalogue, generating 3 tailored bundles: Essential, Growth, Premium."),
        ("3. Quote", "Transparent itemized pricing preview strictly distinguishing Monthly Recurring Charges (MRC) from One-Time Setup fees (OTC)."),
        ("4. Verify", "Smart KYC with mandatory DPDP consent, local on-premises OCR, and automated mock GSTIN/Udyam registry lookup."),
        ("5. Track", "Immediate prototype order reference generation with step-by-step lifecycle tracking through to simulated service activation.")
    ]
    for i, (stitle, sdesc) in enumerate(steps):
        add_card(s3, 0.8 + (i * 2.4), 1.6, 2.2, 4.8, stitle, [sdesc], bg_color=SLATE_LIGHT if i%2==1 else WHITE)

    # -------------------------------------------------------------
    # SLIDE 4: AI-Powered Business Advisor
    # -------------------------------------------------------------
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "Conversational AI with Deterministic Commercial Trust", "GENAI ADVISOR & EXTRACTION")

    add_card(s4, 0.8, 1.6, 5.6, 4.8, "Generative Dialogue vs. Deterministic Pricing", [
        "• Natural Language Discovery: Powered by Google Gemini (gemini-3.1-flash-lite), the advisor conducts fluid dialogue without forcing users through rigid form drop-downs.",
        "• Real-Time Profile Extraction: Dynamically captures business archetype (e.g. Pharmacy, CA Office), location, employee headcount, and monthly telecom budget.",
        "• CRITICAL ARCHITECTURAL BOUNDARY: Gemini NEVER controls product eligibility, catalogue pricing, or bundle scoring.",
        "• Guaranteed Price Integrity: All pricing calculations, bundle compatibility rules, and discounts are 100% deterministic code executed locally on the backend.",
        "• Graceful Fallback Guard: If Gemini API is unreachable, a local regex-based profile extractor continues onboarding with zero downtime."
    ])

    add_card(s4, 6.8, 1.6, 5.6, 4.8, "Target Customer Archetype Tailoring", [
        "• Archetype 1: Micro Retail & Services (Kiranas, Pharmacies, Salons)",
        "  - Low monthly telecom spend (₹1,500 - ₹3,500/mo).",
        "  - Needs: Fast retail broadband for POS/UPI billing + commercial calling SIM for local delivery dispatch.",
        "  - Solves: Replaces fragmented personal SIMs with dedicated business connectivity.",
        "",
        "• Archetype 2: Professional Offices (Clinics, CA Firms, Coaching Hubs)",
        "  - Mid-range telecom budget (₹3,000 - ₹8,000/mo).",
        "  - Needs: Secure high-bandwidth broadband + multi-line Cloud Voice + static IP security for client compliance.",
        "  - Solves: Prevents client call drops and ensures high-speed multi-user cloud accounting."
    ])

    # -------------------------------------------------------------
    # SLIDE 5: Smart KYC & Digital Verification
    # -------------------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Privacy-First Smart KYC & Local Document OCR", "REGULATORY ONBOARDING AUTOMATION")

    add_card(s5, 0.8, 1.6, 5.6, 4.8, "Local OCR & Identity Protection", [
        "• 100% Local OCR Execution: Uses an on-premises RapidOCR (ONNX) and WinOCR pipeline. Document parsing executes entirely on local CPU.",
        "• Zero Cloud Document Egress: Document bytes, certificate scans, and extracted personal data are NEVER transmitted to Gemini or external LLMs.",
        "• Mandatory DPDP Consent Gate: Explicit digital consent must be accepted before any file can be uploaded, with timestamped audit trails.",
        "• Sensitive Identifier Masking: Extracted GSTIN and Udyam IDs are masked in the client UI (e.g. 29*****1234*1Z5).",
        "• Path-Traversal Security: Uploads are renamed using cryptographically secure UUIDs, completely preventing directory traversal attacks."
    ])

    add_card(s5, 6.8, 1.6, 5.6, 4.8, "Automated Verification Rules (Mock Registries)", [
        "• Synthetic Mock Registries: Extracted identifiers are verified in milliseconds against mock GSTIN and Udyam registries (offline CSV fixtures).",
        "• Multi-Factor Rule Verification:",
        "  1. Entity Status: Confirms status is Active (flags Suspended/Cancelled).",
        "  2. Trade Name Matching: Fuzzy token ratio matches certificate name with customer business name (>=80% confidence).",
        "  3. Document Freshness: Validates certificate issuance within acceptable operational recency.",
        "  4. Cross-Document Consistency: Validates state and entity alignment across uploaded proofs.",
        "• Human-in-the-Loop Branching: Ambiguous or borderline documents route to manual review without outright rejection."
    ])

    # -------------------------------------------------------------
    # SLIDE 6: Technical Architecture
    # -------------------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "High-Performance Full-Stack Enterprise Architecture", "SYSTEM ARCHITECTURE")

    add_card(s6, 0.8, 1.6, 3.6, 4.8, "1. Modern Frontend (React 18)", [
        "• Vite 5 Single Page Application: Sub-second HMR and instant page rendering.",
        "• Code-Split Production Bundle: Admin portal and charting libraries lazy-loaded via React.lazy & Suspense.",
        "• Lightweight Initial Customer Payload: ~106 kB gzip (370 kB raw) initial load; admin chunk 109 kB gzip (372 kB raw) code-split.",
        "• Responsive Tailwind CSS: Optimized for desktop sales reps and mobile smartphone merchants.",
        "• 17 Vitest Test Suites: 100% pass rate."
    ])

    add_card(s6, 4.8, 1.6, 3.6, 4.8, "2. High-Speed Backend (FastAPI)", [
        "• Asynchronous ASGI Engine: FastAPI 0.162 on Python 3.13.",
        "• Strict Contract Validation: 100% Pydantic v2 schemas across all API endpoints.",
        "• Modular FastAPI Backend Services: Advisor, Catalogue, Quote, KYC, Orders, and Analytics.",
        "• Prototype Security Guards: Admin endpoints protected via X-Admin-Role authentication.",
        "• 138 PyTest Test Suites: 100% pass rate."
    ])

    add_card(s6, 8.8, 1.6, 3.6, 4.8, "3. Data & ML Boundaries", [
        "• Zero-Leakage Pipeline: Scikit-learn Logistic Regression pipeline with 5-fold Platt calibration.",
        "• Strict Dataset Isolation: Original smb_leads.csv (5,000 records) strictly read-only.",
        "• Offline Document Cache: Temporary local storage with zero cloud S3 leakage.",
        "• Deterministic Rules: Authoritative catalogue containing 25 verified products.",
        "• In-Memory Case Stores: Rapid prototype order and session management."
    ])

    # -------------------------------------------------------------
    # SLIDE 7: Executive Analytics & ML Intelligence
    # -------------------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Executive Analytics & Calibrated Propensity Scoring", "SALES INTELLIGENCE ENGINE")

    add_card(s7, 0.8, 1.6, 5.6, 4.8, "Funnel Telemetry (5,000 Historical Leads)", [
        "• Ground Truth Funnel Benchmarks:",
        "  - Lead Intake: 5,000 | Contacted: 3,406 (31.9% drop)",
        "  - Needs Assessed: 1,974 (42.0% drop)",
        "  - Quote Accepted: 861 (56.4% drop — Biggest Bottleneck!)",
        "  - KYC Complete: 588 (31.7% drop)",
        "  - Activated: 368 (Overall Conversion: 7.36%)",
        "",
        "• Acquisition Channel Insights:",
        "  - Referral: 14.77% conversion (Top performing channel)",
        "  - WhatsApp Broadcast: 2.79% conversion (Highest drop-off)"
    ])

    add_card(s7, 6.8, 1.6, 5.6, 4.8, "Calibrated ML Lead Prioritization", [
        "• Actionable Lead Population: Quarantined 368 already-activated accounts; strictly prioritizes 4,632 unconverted leads.",
        "• Platt Calibrated Brier Score: 0.0666 on held-out test data (beats naive baseline of 0.0680; 68.8% error reduction vs. raw balanced model).",
        "• Held-Out Test ROC-AUC: 0.6692 | PR-AUC: 0.1327",
        "• Interpretable Logistic-Regression Odds Ratios (Mathematically Bounded >= -100%):",
        "  - Referral Source: +165.75% conversion odds (OR: 2.66)",
        "  - GSTIN Compliant: +97.13% conversion odds (OR: 1.97)",
        "  - WhatsApp Campaign: -71.57% conversion odds (OR: 0.28)",
        "• Non-Causal Disclosure: Statistical associations, not causal effects."
    ])

    # -------------------------------------------------------------
    # SLIDE 8: Business Impact & Pilot Plan
    # -------------------------------------------------------------
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Historical Baseline vs. Proposed Pilot Targets", "BUSINESS CASE & IMPACT MODEL")

    add_card(s8, 0.8, 1.6, 5.6, 4.8, "Historical Operational Baseline (Q2 2026 Data)", [
        "• Overall Conversion Rate: 7.36% (368 activations out of 5,000 leads).",
        "• Average Lead-to-Activation Duration: 17.6 calendar days.",
        "• Customer Status Follow-Up Calls: Average 3 calls per lead.",
        "• Customer Acquisition Cost (CAC): ~₹15,000 per activated account.",
        "• Quote Abandonment Rate: 56.4% drop-off between needs assessment and quote acceptance.",
        "• 6-Month Customer Churn Rate: ~18.5% post-activation churn."
    ])

    add_card(s8, 6.8, 1.6, 5.6, 4.8, "Proposed Pilot Targets (Evaluation Hypotheses)", [
        "• Proposed Conversion Rate Target: 15.0% (collapsing drop-off through instant quoting and verified KYC).",
        "• Proposed Activation Duration: <= 5 calendar days (automated digital KYC vs. physical paper pickup).",
        "• Customer Follow-Up Calls: < 1 call (self-serve digital order tracking).",
        "• Proposed CAC Target: <= ₹8,000 (automated self-service onboarding).",
        "• Proposed 6-Month Churn Target: < 12.0% (tailored bundles reduce mismatches).",
        "",
        "NOTE: Explicitly identified as proposed pilot hypotheses to be validated in field trial, not achieved historical results."
    ])

    # -------------------------------------------------------------
    # SLIDE 9: Security, Privacy & Limitations
    # -------------------------------------------------------------
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Technical Governance, Privacy & Prototype Boundaries", "SECURITY & COMPLIANCE DISCLOSURE")

    add_card(s9, 0.8, 1.6, 5.6, 4.8, "Technical Safeguards Implemented", [
        "• Local Privacy Sandboxing: Document OCR executes locally on CPU; zero document bytes or identity records sent to Gemini.",
        "• Mandatory Consent Checkpoint: Strict gate enforces user consent before document upload unlock.",
        "• Path Traversal Neutralization: Cryptographic UUID filename sanitization prevents directory escaping.",
        "• Masked Identifiers: Client displays mask GSTIN and Udyam numbers to protect business confidentiality.",
        "• Model Leakage Blacklist: 17 downstream CRM columns strictly blacklisted from machine learning features."
    ])

    add_card(s9, 6.8, 1.6, 5.6, 4.8, "Prototype Boundaries & Production Roadmap", [
        "• Offline Synthetic Registries: Uses mock CSV datasets; not connected to live government GSTN/Udyam servers.",
        "• Simulated Telecom Provisioning: Circuit and SIM activations are simulated in a state machine, not connected to live telco OSS/BSS.",
        "• Prototype Role Authentication: Uses prototype header authentication (X-Admin-Role); requires Airtel Enterprise SSO for production.",
        "• Local Temporary Storage: Uploaded files stored in local folders; requires encrypted S3/Azure Blob vault for production.",
        "• Statutory Notice: Foundational safeguards implemented, but prototype is not yet certified DPDP Act compliant."
    ])

    # -------------------------------------------------------------
    # SLIDE 10: Demo & Closing
    # -------------------------------------------------------------
    s10 = prs.slides.add_slide(blank_layout)
    bg10 = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg10.fill.solid()
    bg10.fill.fore_color.rgb = SLATE_DARK
    bg10.line.fill.background()

    tb10 = s10.shapes.add_textbox(Inches(1.2), Inches(1.2), Inches(10.9), Inches(1.2))
    p10_sub = tb10.text_frame.paragraphs[0]
    p10_sub.text = "AIRTEL SYNC HACKATHON 2026 • PROJECT UDYAM DIGITAL"
    p10_sub.font.size = Pt(13)
    p10_sub.font.bold = True
    p10_sub.font.color.rgb = AIRTEL_RED
    
    p10_t = tb10.text_frame.add_paragraph()
    p10_t.text = "Udyam360: The Future of MSME Telco Onboarding"
    p10_t.font.size = Pt(36)
    p10_t.font.bold = True
    p10_t.font.color.rgb = WHITE

    # 3 Summary Cards
    add_card(s10, 1.2, 2.7, 3.4, 3.8, "Unified Customer Journey", [
        "• 3-Min Prototype Journey (Simulated)",
        "• Conversational AI Advisor",
        "• Itemized Pricing (MRC vs OTC)",
        "• Smart KYC with Local OCR",
        "• Real-Time Order Tracking"
    ], bg_color=WHITE)

    add_card(s10, 4.95, 2.7, 3.4, 3.8, "Calibrated Sales Intelligence", [
        "• 6-Stage Funnel Telemetry",
        "• 4,632 Actionable Leads Scored",
        "• Calibrated Brier Score 0.0666",
        "• Interpretable Odds Attribution",
        "• Quarantined Activated Leads"
    ], bg_color=WHITE)

    add_card(s10, 8.7, 2.7, 3.4, 3.8, "Enterprise-Grade Architecture", [
        "• 138 Backend Tests Passing",
        "• 17 Frontend Tests Passing",
        "• Zero Leakage ML Pipeline",
        "• Strict Privacy Sandboxing",
        "• Code-Split Production Bundle"
    ], bg_color=WHITE)

    prs.save("submission/Udyam360_Business_Case.pptx")
    print("Successfully generated 10-slide PowerPoint: submission/Udyam360_Business_Case.pptx")

if __name__ == "__main__":
    create_presentation()

