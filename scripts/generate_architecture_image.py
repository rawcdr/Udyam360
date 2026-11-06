import os
import subprocess
import time
from PIL import Image

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HTML_PATH = os.path.abspath("render_arch.html")
OUTPUT_PNG = os.path.abspath("submission/final_architecture.png")

mermaid_code = """
flowchart TD
    subgraph Client_Layer ["Client Layer (React 18 + Vite SPA)"]
        LP["Landing Page (Archetypes)"]
        ADV["AI Business Advisor (Chat UI)"]
        REC["Recommendations & Bundles"]
        QT["Quote Review (MRC vs OTC)"]
        KYC_UI["Smart KYC (Consent Gate & Upload)"]
        OT["Order Tracker (Simulated Activation)"]
        subgraph Admin_Portal ["Code-Split Admin Portal (/admin)"]
            AO["Executive Overview (Funnel Telemetry)"]
            AL["Lead Prioritization (4,632 Actionable)"]
            AM["ML Model Hub & Sandbox"]
        end
    end

    subgraph Gateway ["API Gateway & Security Boundary"]
        FastAPI_App["FastAPI REST Application (ASGI)"]
        AG["Role Guard: X-Admin-Role (Prototype)"]
        CORS["CORS & Request Validation (Pydantic v2)"]
    end

    subgraph Core_Backend ["Core Backend Services (Local Execution)"]
        AS["Advisor Orchestrator (Session Manager)"]
        CS["Catalogue & Eligibility Service"]
        RE["Deterministic Recommendation Engine"]
        QE["Pricing & Quote Preview Service"]
        KO["KYC Orchestrator & Validator"]
        OS["Order Service (State Machine)"]
        AN["Executive Analytics Service"]
        LSS["Lead Scoring & Prioritization Service"]
    end

    subgraph AI_ML_Engines ["AI & Machine Learning Layer"]
        subgraph Cloud_AI ["External Cloud AI (Strict Boundary)"]
            GEM["Google Gemini API (gemini-2.5-flash)"]
        end
        subgraph Local_ML ["Local On-Premises ML / OCR (Zero Cloud Egress)"]
            OCR["Local RapidOCR / WinOCR Engine"]
            LR["Logistic Regression Pipeline (v1.1.0)"]
            CAL["5-Fold Platt Sigmoid Calibration"]
            EXP["Log-Odds ModelExplainer"]
        end
    end

    subgraph Data_Storage ["Data & Persistence Layer"]
        PC["product_catalogue.csv (25 Products)"]
        SL["smb_leads.csv (5,000 Leads, Read-Only)"]
        REG_G["mock_gstin_registry.csv (Synthetic Registry)"]
        REG_U["mock_udyam_registry.csv (Synthetic Registry)"]
        MA["backend/models/ (Serialized Pipelines & JSON)"]
        KYC_DIR["local_uploads/ (Temporary Doc Cache)"]
        MEM["In-Memory Stores (Sessions, Orders, Notes)"]
    end

    %% Client to Gateway
    LP --> FastAPI_App
    ADV --> FastAPI_App
    REC --> FastAPI_App
    QT --> FastAPI_App
    KYC_UI --> FastAPI_App
    OT --> FastAPI_App
    Admin_Portal --> AG --> FastAPI_App

    %% Gateway to Services
    FastAPI_App --> AS
    FastAPI_App --> CS
    FastAPI_App --> RE
    FastAPI_App --> QE
    FastAPI_App --> KO
    FastAPI_App --> OS
    FastAPI_App --> AN
    FastAPI_App --> LSS

    %% Service to AI/ML & Data
    AS -.->|"1. Dialogue & Profile Extraction ONLY (No PII/Docs)"| GEM
    AS -->|"2. Deterministic Fallback Guard"| CS
    CS --> PC
    RE --> PC
    QE --> PC
    KO -->|"Local OCR Extraction"| OCR
    KO -->|"Synthetic Verification"| REG_G
    KO -->|"Synthetic Verification"| REG_U
    KO --> KYC_DIR
    LSS --> LR
    LR --> CAL
    CAL --> EXP
    LSS --> MA
    AN --> SL
    OS --> MEM

    classDef cloud fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1;
    classDef local fill:#f0fdf4,stroke:#16a34a,stroke-width:2px,color:#15803d;
    classDef boundary fill:#fef2f2,stroke:#dc2626,stroke-width:2px,color:#991b1b;
    classDef data fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#334155;

    class GEM cloud;
    class OCR,LR,CAL,EXP local;
    class AG,CORS boundary;
    class PC,SL,REG_G,REG_U,MA,KYC_DIR,MEM data;
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Udyam360 System Architecture</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 30px;
      background-color: #ffffff;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .header {{
      text-align: center;
      margin-bottom: 25px;
    }}
    .header h1 {{
      margin: 0 0 8px 0;
      font-size: 26px;
      color: #0f172a;
      font-weight: 800;
    }}
    .header p {{
      margin: 0;
      font-size: 14px;
      color: #64748b;
    }}
    .mermaid {{
      background: #ffffff;
      padding: 20px;
      border-radius: 12px;
      border: 1px solid #e2e8f0;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'default',
      flowchart: {{
        useMaxWidth: false,
        htmlLabels: true,
        curve: 'basis'
      }}
    }});
  </script>
</head>
<body>
  <div class="header">
    <h1>Udyam360 — End-to-End System Architecture</h1>
    <p>Airtel SYNC Hackathon 2026 • Enterprise Track A • Final Component & Execution Boundary Blueprint</p>
  </div>
  <div class="mermaid">
{mermaid_code}
  </div>
</body>
</html>
"""

def main():
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated {HTML_PATH}")

    file_url = "file:///" + HTML_PATH.replace("\\", "/")
    print(f"Rendering architecture diagram via Chrome to {OUTPUT_PNG}...")

    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--screenshot={OUTPUT_PNG}",
        "--window-size=1600,1400",
        "--virtual-time-budget=5000",
        "--hide-scrollbars",
        "--disable-gpu",
        file_url
    ]
    subprocess.run(cmd, check=True)

    if os.path.exists(OUTPUT_PNG):
        size = os.path.getsize(OUTPUT_PNG)
        img = Image.open(OUTPUT_PNG)
        extrema = img.convert("RGB").getextrema()
        print(f"Architecture diagram rendered: {size} bytes, dimensions {img.size}")
        print(f"Extrema: {extrema}")
        if not all(e[0] == e[1] for e in extrema):
            print("Successfully rendered high-resolution architecture diagram!")
        else:
            print("Warning: rendered image appears blank.")
    
    if os.path.exists(HTML_PATH):
        os.remove(HTML_PATH)

if __name__ == "__main__":
    main()

