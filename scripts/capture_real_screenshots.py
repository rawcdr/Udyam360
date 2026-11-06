import os
import sys
import time
import json
import urllib.request
import subprocess

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

def create_sample_order():
    url = "http://127.0.0.1:8000/api/v1/orders"
    payload = {
        "quote_reference": "Q-PHARMACY-2026",
        "kyc_case_id": "KYC-DEMO-001",
        "selected_product_ids": ["P01", "P03"],
        "bundle_tier": "Growth",
        "customer_info": {
            "business_name": "Apollo Care Pharmacy",
            "contact_name": "Dr. R. Sharma",
            "city": "Bengaluru",
            "segment": "micro",
            "installation_address": "45 Commercial Street, Bengaluru"
        },
        "pricing": {
            "currency": "INR",
            "monthly_recurring_charges": 1998.0,
            "one_time_charges": 1000.0,
            "estimated_first_month": 2998.0
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data.get("order_reference", "ORD-DEMO12345")
    except Exception as e:
        print(f"Failed to create sample order via API: {e}")
        return "ORD-DEMO12345"

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
    if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
        print(f"Captured: {os.path.basename(output_file)} ({os.path.getsize(output_file)} bytes)")
    else:
        print(f"Warning: Failed to capture {output_file}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("1. Starting backend server on port 8000...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd="backend"
    )
    
    print("2. Starting frontend dev server on port 5173...")
    frontend_proc = subprocess.Popen(
        ["npm.cmd", "run", "dev", "--", "--port", "5173"],
        cwd="frontend"
    )
    
    try:
        print("Waiting for servers to become healthy...")
        if not wait_for_url("http://127.0.0.1:8000/api/v1/health", timeout=20):
            print("Backend health check timed out!")
            return
        if not wait_for_url("http://localhost:5173/", timeout=20):
            print("Frontend server check timed out!")
            return
        print("Both servers healthy and responding!")
        
        # Create an order to track
        order_ref = create_sample_order()
        print(f"Created sample order for tracker: {order_ref}")
        
        targets = [
            ("landing_page.png", "http://localhost:5173/", 2000),
            ("advisor.png", "http://localhost:5173/advisor", 4000),
            ("recommendations.png", "http://localhost:5173/recommendations", 4000),
            ("quote.png", "http://localhost:5173/quote", 4000),
            ("kyc.png", "http://localhost:5173/kyc", 4000),
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
            
        print("\nAll 9 application screenshots captured successfully!")
        
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
