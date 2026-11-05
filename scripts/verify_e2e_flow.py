"""End-to-End Complete Flow Verification for Udyam360 Phase 4.

Traces the entire customer journey:
Landing/Health -> Advisor Start & Dialogue -> Bundle Recommendations ->
Quote Preview -> Smart KYC Case & Consent -> Document Upload & Local OCR ->
Order Creation -> Order State Progression & Tracking.
"""

import os
import sys
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.schemas.order import OrderState

client = TestClient(app)


def test_full_customer_journey():
    print("==================================================")
    print("UDYAM360 PHASE 4: FULL END-TO-END FLOW VERIFICATION")
    print("==================================================")

    # 1. Health & Catalogue Check
    print("\n[Step 1] Checking System Health & Catalogue...")
    h_res = client.get("/health")
    assert h_res.status_code == 200, f"Health check failed: {h_res.text}"
    print("  -> System Status:", h_res.json())

    cat_res = client.get("/api/v1/catalogue/summary")
    assert cat_res.status_code == 200
    summary = cat_res.json()
    print(f"  -> Catalogue loaded: {summary['total_products']} products across {len(summary['categories'])} categories.")

    # 2. Advisor Start & Dialogue
    print("\n[Step 2] Starting Advisor Onboarding Session...")
    start_res = client.post("/api/v1/advisor/start")
    assert start_res.status_code == 200
    conv_id = start_res.json()["conversation_id"]
    print(f"  -> Session ID: {conv_id}")
    print(f"  -> Greeting: {start_res.json()['welcome_message'][:60]}...")

    print("\n[Step 3] Customer Sends Message to Advisor...")
    user_prompt = "I run a retail pharmacy in Chennai with 4 employees and a monthly budget of Rs 4000. I need broadband and POS backup."
    msg_res = client.post("/api/v1/advisor/message", json={"conversation_id": conv_id, "message": user_prompt})
    assert msg_res.status_code == 200
    msg_data = msg_res.json()
    print("  -> Assistant Reply:", msg_data["assistant_message"][:100] + "...")
    print("  -> Processing Status:", msg_data["processing_status"])
    extracted = msg_data.get("extracted_profile") or {}
    print(f"  -> Extracted Profile: type={extracted.get('business_type')}, city={extracted.get('city')}, budget={extracted.get('budget_monthly')}")

    # 3. Product Recommendations
    print("\n[Step 4] Generating Recommendations...")
    # Fetch current session state to get full business profile
    session_res = client.get(f"/api/v1/advisor/conversation/{conv_id}")
    assert session_res.status_code == 200
    profile_data = session_res.json()["profile"]

    rec_res = client.post("/api/v1/recommendations", json=profile_data)
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    print("  -> Essential Bundle:", rec_data["essential_bundle"]["bundle_name"], f"₹{rec_data['essential_bundle']['pricing']['monthly_total_min']}/mo")
    print("  -> Growth Bundle:", rec_data["growth_bundle"]["bundle_name"], f"₹{rec_data['growth_bundle']['pricing']['monthly_total_min']}/mo")
    print("  -> Premium Bundle:", rec_data["premium_bundle"]["bundle_name"], f"₹{rec_data['premium_bundle']['pricing']['monthly_total_min']}/mo")

    # 4. Quote Preview
    selected_prods = rec_data["growth_bundle"]["product_ids"]
    print(f"\n[Step 5] Requesting Quote Preview for Growth Bundle {selected_prods}...")
    quote_res = client.post(
        "/api/v1/quotes/preview",
        json={
            "profile": profile_data,
            "selected_product_ids": selected_prods,
            "bundle_tier": "Growth",
        },
    )
    assert quote_res.status_code == 200
    quote_data = quote_res.json()
    quote_id = quote_data["quote_id"]
    pricing = quote_data["pricing"]
    print(f"  -> Quote Reference: {quote_id}")
    print(f"  -> MRC: ₹{pricing['monthly_total_min']}, OTC: ₹{pricing['setup_total_min']}, First Month: ₹{pricing['estimated_first_month_min']}")

    # 5. Smart KYC Initialization & Consent
    print("\n[Step 6] Initializing KYC Case...")
    kyc_init_res = client.post(
        "/api/v1/kyc/cases",
        json={
            "advisor_session_id": conv_id,
            "selected_product_ids": selected_prods,
            "quote_reference": quote_id,
        },
    )
    assert kyc_init_res.status_code == 201
    case_data = kyc_init_res.json()
    case_id = case_data["kyc_case_id"]
    print(f"  -> KYC Case ID: {case_id}")
    req_docs = case_data.get("required_document_types") or case_data.get("required_documents") or []
    print(f"  -> Dynamic Required Documents: {req_docs}")

    print("\n[Step 7] Recording Customer Consent...")
    consent_res = client.post(
        f"/api/v1/kyc/cases/{case_id}/consent",
        json={"consent_granted": True, "consent_version": "v1.0-Airtel-Udyam360-Prototype"},
    )
    assert consent_res.status_code == 200
    print("  -> Consent Audit Record:", consent_res.json().get("consent_id"), "granted=", consent_res.json().get("consent_granted"))

    # 6. Upload Specimen Document
    print("\n[Step 8] Uploading Specimen KYC Document...")
    specimen_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "YTL_TrackA_Udyam_Digital_Data", "kyc_documents"))
    specimen_file = None
    if os.path.exists(specimen_dir):
        files = os.listdir(specimen_dir)
        if files:
            specimen_file = os.path.join(specimen_dir, files[0])

    if specimen_file and os.path.exists(specimen_file):
        with open(specimen_file, "rb") as f:
            file_bytes = f.read()
        filename = os.path.basename(specimen_file)
        doc_type = req_docs[0] if req_docs else "GST_CERTIFICATE"
        upload_res = client.post(
            f"/api/v1/kyc/cases/{case_id}/documents",
            data={"document_type": doc_type},
            files={"file": (filename, file_bytes, "image/png")},
        )
        assert upload_res.status_code == 201
        print(f"  -> Uploaded specimen '{filename}' ({len(file_bytes)} bytes) as {doc_type}.")
    else:
        print("  -> Specimen file not found, skipping file upload.")

    # 7. Process KYC
    print("\n[Step 9] Executing Local OCR and Registry Verification...")
    proc_res = client.post(f"/api/v1/kyc/cases/{case_id}/process")
    assert proc_res.status_code == 200
    val_data = proc_res.json()
    print(f"  -> Overall KYC Status: {val_data['overall_status']}")
    print(f"  -> Passed Checks Count: {len(val_data['checks_passed'])}")
    print(f"  -> Explanation: {val_data['explanation']}")

    # 8. Order Creation
    print("\n[Step 10] Placing Customer Order...")
    order_payload = {
        "advisor_session_id": conv_id,
        "quote_reference": quote_id,
        "kyc_case_id": case_id,
        "selected_product_ids": selected_prods,
        "bundle_tier": "Growth",
        "customer_info": {
            "business_name": "Apollo Care Pharmacy",
            "city": "Chennai",
            "segment": "micro",
        },
        "pricing": {
            "currency": "INR",
            "monthly_recurring_charges": pricing["monthly_total_min"],
            "one_time_charges": pricing["setup_total_min"],
            "estimated_first_month": pricing["estimated_first_month_min"],
        },
    }
    ord_res = client.post("/api/v1/orders", json=order_payload)
    assert ord_res.status_code == 201
    ord_data = ord_res.json()
    order_id = ord_data["order_id"]
    order_ref = ord_data["order_reference"]
    print(f"  -> Order Created! ID: {order_id}, Reference: {order_ref}")
    print(f"  -> Initial State: {ord_data['current_state']}")

    # 9. Order Tracking by Reference
    print("\n[Step 11] Tracking Order by Customer Reference...")
    track_res = client.get(f"/api/v1/orders/track/{order_ref}")
    assert track_res.status_code == 200
    assert track_res.json()["order_reference"] == order_ref
    print("  -> Order tracking successfully retrieved record.")

    # 10. Lifecycle State Machine Progression (Simulation)
    print("\n[Step 12] Progressing Lifecycle State Machine...")
    steps_to_activate = [
        OrderState.KYC_PENDING,
        OrderState.KYC_VERIFICATION,
        OrderState.KYC_VERIFIED,
        OrderState.ORDER_PROCESSING,
        OrderState.ACTIVATION_IN_PROGRESS,
        OrderState.ACTIVATED,
    ]
    for target in steps_to_activate:
        adv_res = client.post(f"/api/v1/orders/{order_id}/advance", json={"target_state": target.value})
        assert adv_res.status_code == 200
        adv_data = adv_res.json()
        sim_flag = " [SIMULATED]" if adv_data["is_simulated_stage"] else ""
        print(f"  -> Transitioned to: {adv_data['current_state']}{sim_flag}")

    # Final timeline audit
    tl_res = client.get(f"/api/v1/orders/{order_id}/timeline")
    assert tl_res.status_code == 200
    timeline = tl_res.json()["timeline"]
    print(f"\n[Step 13] Order Timeline Milestones ({len(timeline)} events recorded):")
    for evt in timeline:
        sim_tag = " (Simulated)" if evt["is_simulated"] else ""
        print(f"   • [{evt['to_state']}] {evt['title']}{sim_tag}")

    print("\n==================================================")
    print("UDYAM360 PHASE 4 COMPLETE END-TO-END VERIFICATION: 100% SUCCESS")
    print("==================================================")


if __name__ == "__main__":
    test_full_customer_journey()
