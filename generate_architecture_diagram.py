import os
from PIL import Image, ImageDraw, ImageFont

def create_architecture_diagram(output_path):
    width = 1920
    height = 1080
    
    # Create high-res canvas
    img = Image.new("RGBA", (width, height), (248, 250, 252, 255)) # #F8FAFC
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    font_dir = "C:/Windows/Fonts/"
    try:
        title_font = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 34)
        subtitle_font = ImageFont.truetype(os.path.join(font_dir, "segoeui.ttf"), 18)
        header_tag_font = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 14)
        section_title_font = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 17)
        card_title_font = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 16)
        body_font = ImageFont.truetype(os.path.join(font_dir, "segoeui.ttf"), 13)
        badge_font = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 12)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        header_tag_font = ImageFont.load_default()
        section_title_font = ImageFont.load_default()
        card_title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()

    # Draw header bar
    # Red accent badge
    draw.rounded_rectangle([60, 35, 360, 62], radius=6, fill=(238, 0, 0, 25), outline=(238, 0, 0, 180), width=1)
    draw.text((75, 40), "AIRTEL SYNC 2026 • ENTERPRISE TRACK A", fill=(218, 0, 0, 255), font=header_tag_font)
    
    # Title & Subtitle
    draw.text((60, 72), "Udyam360: Production Solution Architecture & Zero-PII Boundary", fill=(15, 23, 42, 255), font=title_font)
    draw.text((60, 118), "Live Split Cloud Topology: Vercel Global Edge (React SPA) + Render ASGI Container (FastAPI + Air-Gapped Tesseract OCR)", fill=(100, 116, 139, 255), font=subtitle_font)

    # Status pill on right
    draw.rounded_rectangle([1570, 45, 1860, 85], radius=20, fill=(240, 253, 244, 255), outline=(34, 197, 94, 255), width=2)
    draw.ellipse([1590, 60, 1600, 70], fill=(34, 197, 94, 255))
    draw.text((1612, 54), "DPDP ACT 2023 VERIFIED", fill=(22, 101, 52, 255), font=badge_font)

    # Divider line
    draw.line([60, 155, 1860, 155], fill=(226, 232, 240, 255), width=2)

    # Function to draw styled card
    def draw_card(box, title, subtitle, items, bg_color, border_color, title_color, badge=None):
        x1, y1, x2, y2 = box
        draw.rounded_rectangle([x1, y1, x2, y2], radius=10, fill=bg_color, outline=border_color, width=2)
        
        # Header text
        curr_y = y1 + 14
        draw.text((x1 + 16, curr_y), title, fill=title_color, font=card_title_font)
        
        if badge:
            bx1 = x2 - 130
            draw.rounded_rectangle([bx1, curr_y - 2, x2 - 14, curr_y + 18], radius=4, fill=(255, 255, 255, 200), outline=border_color, width=1)
            draw.text((bx1 + 8, curr_y), badge, fill=title_color, font=badge_font)

        curr_y += 24
        if subtitle:
            draw.text((x1 + 16, curr_y), subtitle, fill=(100, 116, 139, 255), font=body_font)
            curr_y += 20
        
        for item in items:
            draw.ellipse([x1 + 18, curr_y + 6, x1 + 22, curr_y + 10], fill=title_color)
            draw.text((x1 + 28, curr_y), item, fill=(51, 65, 85, 255), font=body_font)
            curr_y += 20

    # -------------------------------------------------------------
    # 1. CLIENT & PRESENTATION TIER (TOP ROW)
    # -------------------------------------------------------------
    # Container box for Presentation Layer
    draw.rounded_rectangle([60, 175, 1860, 310], radius=12, fill=(241, 245, 249, 120), outline=(203, 213, 225, 255), width=1)
    draw.text((80, 186), "1. CLIENT INGESTION & PRESENTATION TIER (Vercel Global Edge Network - TLS 1.3)", fill=(30, 41, 59, 255), font=section_title_font)

    # Client cards
    draw_card([80, 215, 620, 295], "MSME Business Applicant", "Mobile Web / Desktop (Cross-Platform)", 
              ["Natural language requirement discovery", "Instant 2s transparent decimal quotes"], 
              (255, 255, 255, 255), (148, 163, 184, 255), (15, 23, 42, 255), "Self-Serve")

    draw_card([650, 215, 1250, 295], "React 18 SPA (Vite + Tailwind CSS)", "Edge CDN Cached Assets (<1.2s Load)", 
              ["Zustand client state with encrypted sessionStorage", "Unbundled DPDP Section 6 opt-in consent gate"], 
              (239, 246, 255, 255), (59, 130, 246, 255), (29, 78, 216, 255), "Vercel Edge")

    draw_card([1280, 215, 1840, 295], "Airtel KYC & Sales Operations", "KYC Officer Desk & Executive Analytics", 
              ["Smart Exception Copilot (45-sec trade name override)", "5,000-Lead Propensity & Funnel telemetry"], 
              (255, 255, 255, 255), (148, 163, 184, 255), (15, 23, 42, 255), "Enterprise Desk")

    # Downward connectors from Presentation to Gateway
    for cx in [350, 950, 1560]:
        draw.line([cx, 310, cx, 335], fill=(59, 130, 246, 255), width=2)
        draw.polygon([(cx-5, 332), (cx+5, 332), (cx, 340)], fill=(59, 130, 246, 255))

    # -------------------------------------------------------------
    # 2. API GATEWAY & SECURITY LAYER
    # -------------------------------------------------------------
    draw.rounded_rectangle([60, 340, 1860, 465], radius=12, fill=(253, 242, 248, 80), outline=(244, 114, 182, 255), width=1)
    draw.text((80, 350), "2. API GATEWAY & SECURITY ENFORCEMENT (Render ASGI Container - Linux Isolated)", fill=(157, 23, 77, 255), font=section_title_font)

    draw_card([80, 375, 480, 450], "FastAPI ASGI Engine", "Uvicorn Async Runtime", 
              ["High-concurrency async handlers", "Pydantic v2 strict schema validation"], 
              (255, 255, 255, 255), (236, 72, 153, 255), (157, 23, 77, 255))

    draw_card([500, 375, 920, 450], "Sliding-Window Rate Limiter", "Anti-Brute Force Middleware", 
              ["60s OTP resend cooldown & 5-min TTL", "15-min IP sliding lockout upon 5 failures"], 
              (255, 255, 255, 255), (236, 72, 153, 255), (157, 23, 77, 255))

    draw_card([940, 375, 1380, 450], "Salted SHA-256 OTP & Bcrypt", "Passwordless + RBAC Auth", 
              ["Customer: SHA-256(OTP + Salt)", "Admin: Bcrypt (cost 12) + HttpOnly sessions"], 
              (255, 255, 255, 255), (236, 72, 153, 255), (157, 23, 77, 255))

    draw_card([1400, 375, 1840, 450], "DPDP Consent Interceptor", "Section 6 Statutory Gate", 
              ["Hard 403 Forbidden if consent inactive", "Cryptographic audit logging (IP/Time/UA)"], 
              (255, 255, 255, 255), (236, 72, 153, 255), (157, 23, 77, 255), "Mandatory")

    # Downward connectors to Core Services
    for cx in [280, 710, 1160, 1620]:
        draw.line([cx, 465, cx, 490], fill=(236, 72, 153, 255), width=2)
        draw.polygon([(cx-5, 487), (cx+5, 487), (cx, 495)], fill=(236, 72, 153, 255))

    # -------------------------------------------------------------
    # 3. CORE ENGINES & AIR-GAPPED PRIVACY BOUNDARY (MIDDLE ROW)
    # -------------------------------------------------------------
    # Left: GenAI Discovery Box (Cloud)
    draw.rounded_rectangle([60, 495, 520, 785], radius=12, fill=(245, 243, 255, 120), outline=(139, 92, 246, 255), width=2)
    draw.text((80, 508), "3A. PUBLIC CLOUD GENAI (INTAKE)", fill=(109, 40, 217, 255), font=section_title_font)
    draw.rounded_rectangle([390, 504, 505, 526], radius=4, fill=(139, 92, 246, 30), outline=(139, 92, 246, 180), width=1)
    draw.text((400, 508), "ZERO PII", fill=(109, 40, 217, 255), font=badge_font)

    draw_card([80, 538, 500, 765], "Google Gemini 3.1 Flash-Lite", "Conversational Intake Specialist", [
        "Analyzes raw business descriptions",
        "Extracts staffing & bandwidth targets",
        "Recommends tier (Essential, Growth, Pro)",
        "Zero token retention / Stateless API",
        "NEVER sees PAN, GSTIN or Documents",
        "Air-gapped from KYC verification engine"
    ], (255, 255, 255, 255), (167, 139, 250, 255), (91, 33, 182, 255))

    # Center: Deterministic Engines
    draw.rounded_rectangle([540, 495, 1140, 785], radius=12, fill=(255, 241, 242, 100), outline=(244, 63, 94, 255), width=2)
    draw.text((560, 508), "3B. DETERMINISTIC DOMAIN ENGINES", fill=(190, 18, 60, 255), font=section_title_font)

    draw_card([560, 538, 1120, 645], "Deterministic Pricing & Bundle Solver", "Python decimal.Decimal Precision", [
        "Calculates setup fee waiver & 18% GST deterministically",
        "Zero generative hallucination in commercial quotes",
        "Guarantees 30-day price lock with contract binding"
    ], (255, 255, 255, 255), (251, 113, 133, 255), (159, 18, 57, 255))

    draw_card([560, 658, 1120, 765], "Order Lifecycle & State Machine (FSM)", "Transactional Integrity Manager", [
        "Enforces Draft -> Consent -> DocPending -> Verified -> Active",
        "Powers real-time SMS / WhatsApp order tracker",
        "Telemetry ingestion for Airtel SYNC conversion model"
    ], (255, 255, 255, 255), (251, 113, 133, 255), (159, 18, 57, 255))

    # Right: Air-Gapped Local KYC Subsystem (Green shield)
    draw.rounded_rectangle([1160, 495, 1860, 785], radius=12, fill=(236, 253, 245, 120), outline=(16, 185, 129, 255), width=2)
    draw.text((1180, 508), "3C. LOCAL AIR-GAPPED KYC SUBSYSTEM", fill=(4, 120, 87, 255), font=section_title_font)
    draw.rounded_rectangle([1700, 504, 1845, 526], radius=4, fill=(16, 185, 129, 40), outline=(16, 185, 129, 255), width=1)
    draw.text((1712, 508), "CONTAINER ISOLATED", fill=(6, 95, 70, 255), font=badge_font)

    draw_card([1180, 538, 1500, 765], "Local C++ Tesseract OCR", "Zero External Cloud Transmission", [
        "Native Tesseract 5.x + Pillow filters",
        "Processes PAN / Udyam / Bills in <800ms",
        "₹0.00 recurring external API cost",
        "Zero cross-border PII exposure",
        "In-memory ephemeral buffer purge",
        "Magic byte & malware validation"
    ], (255, 255, 255, 255), (52, 211, 153, 255), (6, 95, 70, 255))

    draw_card([1520, 538, 1840, 765], "Smart Exception Copilot", "Multi-Registry Matcher & Resolver", [
        "Solves trade name vs proprietor PAN",
        "Local cross-checks: PAN + GSTIN + Udyam",
        "UIDAI Aadhaar 8-digit auto-masking",
        "Officer 1-click regulatory override desk",
        "Reduces KYC verification from 7d to 45s",
        "Audit trail logged for DoT / TRAI"
    ], (255, 255, 255, 255), (52, 211, 153, 255), (6, 95, 70, 255))

    # Downward connectors to Storage
    for cx in [840, 1500]:
        draw.line([cx, 785, cx, 815], fill=(16, 185, 129, 255), width=2)
        draw.polygon([(cx-5, 812), (cx+5, 812), (cx, 820)], fill=(16, 185, 129, 255))

    # -------------------------------------------------------------
    # 4. CRYPTOGRAPHIC DATA & AUDIT VAULT (BOTTOM ROW)
    # -------------------------------------------------------------
    draw.rounded_rectangle([60, 820, 1860, 960], radius=12, fill=(254, 252, 232, 120), outline=(234, 179, 8, 255), width=1)
    draw.text((80, 832), "4. CRYPTOGRAPHIC DATA PERSISTENCE & COMPLIANCE VAULT (DPDP ACT SECTION 8)", fill=(161, 98, 7, 255), font=section_title_font)

    draw_card([80, 858, 650, 942], "Fernet AES-128-CBC Specimen Storage", "/app/storage/kyc_documents (Private Volume)", [
        "Authenticated symmetric encryption at rest (AES-128-CBC + HMAC-SHA256)",
        "Keys injected via container environment; files outside public web root"
    ], (255, 255, 255, 255), (250, 204, 21, 255), (113, 63, 18, 255))

    draw_card([680, 858, 1260, 942], "SQLite Relational Store (WAL Mode)", "udyam360.db (ACID Compliance)", [
        "Configured with PRAGMA journal_mode=WAL & synchronous=NORMAL",
        "Multi-reader high-throughput concurrency with zero corruption on restart"
    ], (255, 255, 255, 255), (250, 204, 21, 255), (113, 63, 18, 255))

    draw_card([1290, 858, 1840, 942], "Immutable Compliance Audit Vault", "security_audit_logs & kyc_consent_audits", [
        "Append-only audit trail capturing consent, OTP, upload, and override events",
        "Cryptographic shredding on demand (DPDP Section 8(7) Right to Erasure)"
    ], (255, 255, 255, 255), (250, 204, 21, 255), (113, 63, 18, 255), "Audit Ready")

    # Footer note
    draw.text((60, 990), "Security Directives: DPDP Act 2023 Sections 6, 7 & 8 | TRAI Telecom Commercial KYC Regulations | UIDAI Aadhaar Masking Circular | CERT-In", fill=(100, 116, 139, 255), font=body_font)
    draw.text((1500, 990), "Project Udyam Digital • Airtel SYNC Hackathon 2026", fill=(148, 163, 184, 255), font=body_font)

    # Save image
    img.save(output_path, "PNG", quality=95)
    print(f"Architecture diagram successfully saved to {output_path}")

if __name__ == "__main__":
    out_dir = "c:/Users/adifr/OneDrive/Desktop/Udyam360/docs/architecture"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "udyam360_architecture_diagram.png")
    create_architecture_diagram(out_file)

