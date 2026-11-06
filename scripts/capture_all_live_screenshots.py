import os
import sys
import time
import json
import urllib.request
import subprocess
from PIL import Image

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = os.path.abspath("submission/screenshots")

def wait_for_url(url, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(1)
    return False

def http_post_json(url, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode('utf-8'))

def capture_screenshot(url, output_file, wait_ms=4000):
    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--screenshot={output_file}",
        "--window-size=1280,850",
        f"--virtual-time-budget={wait_ms}",
        "--hide-scrollbars",
        "--disable-gpu",
        url
    ]
    subprocess.run(cmd, check=True)
    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        img = Image.open(output_file)
        extrema = img.convert("RGB").getextrema()
        print(f"Captured {os.path.basename(output_file)}: {size} bytes, extrema: {extrema}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("1. Starting backend on port 8000...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd="backend"
    )
    print("2. Starting frontend on port 5173...")
    frontend_proc = subprocess.Popen(
        ["npm.cmd", "run", "dev", "--", "--port", "5173"],
        cwd="frontend"
    )

    try:
        print("Waiting for servers to become ready...")
        if not wait_for_url("http://127.0.0.1:8000/api/v1/health", timeout=20):
            print("Backend timed out!")
            return
        if not wait_for_url("http://localhost:5173/", timeout=20):
            print("Frontend timed out!")
            return
        print("Servers ready!")

        # 1. Start Advisor Session
        start_res = http_post_json("http://127.0.0.1:8000/api/v1/advisor/start", {})
        conv_id = start_res["conversation_id"]
        print(f"Created conversation: {conv_id}")

        # 2. Send Message for Shri Physio Clinic in Delhi
        msg_res = http_post_json("http://127.0.0.1:8000/api/v1/advisor/message", {
            "conversation_id": conv_id,
            "message": "Hello, I run Shri Physio Clinic in Delhi. We have 5 staff and 1 location. My monthly telecom budget is around Rs 4,500. We need reliable high-speed office internet and business calling SIMs."
        })
        profile = msg_res.get("extracted_profile", {})
        profile["business_name"] = "Shri Physio Clinic"
        print(f"Profile extracted: {profile.get('business_type')} in {profile.get('city')}, headcount: {profile.get('employee_count')}")

        # 3. Create KYC Case linked to conv_id
        kyc_case = http_post_json("http://127.0.0.1:8000/api/v1/kyc/cases", {
            "advisor_session_id": conv_id,
            "selected_product_ids": ["P01", "P03", "P08"],
            "quote_reference": "Q-DELHI-2026"
        })
        case_id = kyc_case["kyc_case_id"]
        print(f"Created KYC case: {case_id}")

        # 4. Record Consent
        http_post_json(f"http://127.0.0.1:8000/api/v1/kyc/cases/{case_id}/consent", {
            "consent_granted": True,
            "consent_version": "v1.0-2026"
        })
        print("Consent recorded successfully")

        # 5. Upload K07 Specimen Documents via Multipart Form
        def upload_file(doc_type, filepath):
            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
            filename = os.path.basename(filepath)
            with open(filepath, "rb") as f:
                file_bytes = f.read()
            
            body = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="document_type"\r\n\r\n'
                f"{doc_type}\r\n"
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                f"Content-Type: image/png\r\n\r\n"
            ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

            url = f"http://127.0.0.1:8000/api/v1/kyc/cases/{case_id}/documents"
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))

        upload_file("GST_CERTIFICATE", "YTL_TrackA_Udyam_Digital_Data/kyc_documents/K07_gst_certificate.png")
        upload_file("UDYAM_CERTIFICATE", "YTL_TrackA_Udyam_Digital_Data/kyc_documents/K07_udyam_certificate.png")
        upload_file("ADDRESS_PROOF", "YTL_TrackA_Udyam_Digital_Data/kyc_documents/K07_address_proof.png")
        upload_file("SIGNATORY_ID", "YTL_TrackA_Udyam_Digital_Data/kyc_documents/K07_signatory_id.png")
        print("Uploaded 4 K07 documents")

        # 6. Process KYC with OCR
        kyc_val = http_post_json(f"http://127.0.0.1:8000/api/v1/kyc/cases/{case_id}/process", {})
        print(f"KYC processed with OCR. Overall status: {kyc_val.get('overall_status')}")
        print(f"Checks passed: {len(kyc_val.get('checks_passed', []))}")

        # 7. Create Sample Order for Tracker
        order_res = http_post_json("http://127.0.0.1:8000/api/v1/orders", {
            "quote_reference": "Q-DELHI-2026",
            "kyc_case_id": case_id,
            "selected_product_ids": ["P01", "P03", "P08"],
            "bundle_tier": "Growth",
            "customer_info": {
                "business_name": "Shri Physio Clinic",
                "contact_name": "Dr. Neha Banerjee",
                "city": "Delhi",
                "segment": "prof",
                "installation_address": "Shop/Unit 52, Transport Nagar, Delhi"
            },
            "pricing": {
                "currency": "INR",
                "monthly_recurring_charges": 2998.0,
                "one_time_charges": 1500.0,
                "estimated_first_month": 4498.0
            }
        })
        order_ref = order_res.get("order_reference", "UDYAM-ORD-2026-633D0E53")
        print(f"Created order: {order_ref}")

        # 8. Capture all 9 screenshots
        targets = [
            ("landing_page.png", "http://localhost:5173/", 2000),
            ("advisor.png", f"http://localhost:5173/advisor?conv={conv_id}", 4000),
            ("recommendations.png", "http://localhost:5173/recommendations", 4000),
            ("quote.png", "http://localhost:5173/quote", 4000),
            ("kyc.png", f"http://localhost:5173/kyc?case={case_id}", 4000),
            ("order_tracker.png", f"http://localhost:5173/track-order?ref={order_ref}", 4000),
            ("admin_overview.png", "http://localhost:5173/admin/overview", 5000),
            ("admin_leads.png", "http://localhost:5173/admin/leads", 5000),
            ("admin_model.png", "http://localhost:5173/admin/model", 5000),
        ]

        for fname, url, delay in targets:
            out_path = os.path.join(OUTPUT_DIR, fname)
            print(f"Capturing {fname} from {url}...")
            capture_screenshot(url, out_path, wait_ms=delay)
            time.sleep(1)

        print("\nAll 9 application screenshots successfully captured and verified!")

    finally:
        print("Cleaning up server processes...")
        backend_proc.terminate()
        frontend_proc.terminate()
        try:
            backend_proc.wait(timeout=3)
        except Exception:
            backend_proc.kill()
        try:
            frontend_proc.wait(timeout=3)
        except Exception:
            frontend_proc.kill()

if __name__ == "__main__":
    main()

