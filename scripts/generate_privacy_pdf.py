import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

def generate_pdf():
    pdf_path = os.path.abspath("submission/Udyam360_Privacy_Security_Note.pdf")
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    # 0.4 inch margins to guarantee exact 1-page fit
    margin = 28.0
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=17,
        textColor=colors.HexColor('#E11D48'), # Airtel Crimson
        alignment=TA_CENTER,
        spaceAfter=2
    )
    
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=10.5,
        textColor=colors.HexColor('#475569'),
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    sec_title_style = ParagraphStyle(
        'SecTitle',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=11.5,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=3,
        spaceAfter=2
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor('#1E293B'),
        alignment=TA_LEFT
    )
    
    body_bold_style = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=6.8,
        leading=8.5,
        textColor=colors.HexColor('#64748B'),
        alignment=TA_CENTER
    )

    elements = []
    
    # Header
    elements.append(Paragraph("UDYAM360 — PRIVACY, SECURITY & DATA PROTECTION NOTE", title_style))
    elements.append(Paragraph("Airtel SYNC Hackathon 2026 • Enterprise Track A • Technical Safeguards & Prototype Boundaries", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=5))
    
    # Section 1: Intro & Purpose of Collection
    p1 = "<b>1. Purpose of Data Collection:</b> Udyam360 collects minimal enterprise and operational data (business type, employee count, location, telecom spend, and GSTIN/Udyam certificates) strictly for determining telecom product eligibility, configuring accurate commercial quotes, and automating regulatory onboarding verification."
    elements.append(Paragraph(p1, body_style))
    elements.append(Spacer(1, 4))
    
    # Grid of Safeguards (2 Columns for compact, clean 1-page presentation)
    col1_content = [
        Paragraph("<b>2. Explicit DPDP Consent Process</b><br/>An unskippable digital consent gate precedes all KYC document operations. Users are informed of specific verification purposes and must check a mandatory acknowledgement. Digital timestamps and consent IDs are recorded in the verification audit trail.", body_style),
        Spacer(1, 3),
        Paragraph("<b>3. Local OCR Processing (Zero Cloud Egress)</b><br/>Document text extraction is executed 100% locally using an on-premises RapidOCR (ONNX runtime) and WinOCR engine. Scanned certificate files are parsed on the local compute node without external API relay.", body_style),
        Spacer(1, 3),
        Paragraph("<b>4. Strict LLM Boundary (No KYC to Gemini)</b><br/>Google Gemini is isolated solely to conversational intent parsing on the advisor screen. <b>Zero document bytes, scanned images, tax identifiers, or extracted KYC personal records are ever transmitted to Gemini or external LLMs.</b>", body_style),
        Spacer(1, 3),
        Paragraph("<b>5. File Validation & Path Traversal Guards</b><br/>Strict MIME-type validation permits only PNG, JPEG, and PDF formats with a 10MB size ceiling. Storage paths are sanitised using UUID hashes, completely neutralizing directory traversal vulnerabilities (e.g. <code>../</code> attacks).", body_style),
        Spacer(1, 3),
        Paragraph("<b>6. Sensitive Identifier Masking</b><br/>Extracted 15-character GSTINs and 19-character Udyam numbers are masked in client-facing displays (e.g., <code>29*****1234*1Z5</code>), safeguarding business identifiers against shoulder-surfing and unauthorized exposure.", body_style)
    ]
    
    col2_content = [
        Paragraph("<b>7. Synthetic Registry Boundary & Limitations</b><br/>All registry checks query local offline mock datasets (<code>mock_gstin_registry.csv</code> and <code>mock_udyam_registry.csv</code>). The prototype connects to no live government GSTN or Ministry portals; validity statuses reflect mock dataset fixtures.", body_style),
        Spacer(1, 3),
        Paragraph("<b>8. Temporary Local Storage Architecture</b><br/>Uploaded document artifacts are persisted strictly in local temporary application storage (<code>backend/storage/kyc_documents/</code>). The prototype does not maintain permanent S3 or Blob vaulting, ensuring uploaded files are easily purged.", body_style),
        Spacer(1, 3),
        Paragraph("<b>9. Prototype Authentication Limitations</b><br/>Administrative analytics endpoints are gated via prototype HTTP header guards (<code>X-Admin-Role: ExecutiveAdmin</code>). Production readiness mandates migration to enterprise OAuth2 / Airtel Active Directory SSO.", body_style),
        Spacer(1, 3),
        Paragraph("<b>10. Data Retention & Purge Boundaries</b><br/>Onboarding sessions, orders, and follow-up notes reside in in-memory state stores. Session termination or server restart initiates full memory purge. Formal enterprise retention schedules remain subject to production data governance.", body_style),
        Spacer(1, 3),
        Paragraph("<b>11. Synthetic Hackathon Dataset Disclosure</b><br/>All lead telemetry (<code>smb_leads.csv</code>), customer profiles, and test accounts are synthetic datasets provided for evaluation. Zero real-world consumer PII is stored, ingested, or processed.", body_style)
    ]
    
    table_data = [[col1_content, col2_content]]
    t = Table(table_data, colWidths=[275, 275])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 5))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#E2E8F0'), spaceAfter=4))
    
    # Technical Safeguards vs Legal Compliance Distinctions Box
    box_data = [[
        Paragraph(
            "<b>STATUTORY DISCLOSURE & LEGAL STATUS:</b><br/>"
            "This prototype implements foundational technical safeguards (local OCR, privacy sandboxing, file sanitization, identifier masking, and consent gating). "
            "However, <b>this hackathon prototype is NOT certified as fully compliant with the Digital Personal Data Protection (DPDP) Act 2023 or telecommunications KYC regulations.</b> "
            "Full commercial deployment requires independent legal privacy impact assessments, HSM-backed encrypted storage, and authorized UIDAI/GSTN API integration.",
            disclaimer_style
        )
    ]]
    box_table = Table(box_data, colWidths=[554])
    box_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(box_table)
    
    doc.build(elements)
    print(f"Successfully generated 1-page PDF: {pdf_path}")

if __name__ == "__main__":
    generate_pdf()

