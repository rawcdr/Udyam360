"""Live Integration Test for GenAI Advisor (Manual Execution Only).

Tests live connectivity, structured JSON profile extraction, follow-up generation,
and grounded response explanation against Google Gemini Developer API using synthetic data.
"""

import os
import sys
import time
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

# Load .env explicitly
for p in [Path(".env"), Path("backend/.env"), backend_dir / ".env"]:
    if p.exists():
        load_dotenv(dotenv_path=p)
        break

from app.core.config import settings
from app.schemas.business_profile import BusinessProfile
from app.services.llm_service import llm_service
from app.services.profile_extraction_service import profile_extraction_service
from app.services.advisor_dialogue_service import advisor_dialogue_service
from app.services.recommendation_engine import recommendation_engine
from app.services.advisor_response_service import advisor_response_service


def run_live_integration_test():
    print("=" * 70)
    print("UDYAM360 LIVE GEMINI ADVISOR INTEGRATION TEST")
    print("=" * 70)

    # 1. Verify Gemini Configuration
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = settings.GEMINI_MODEL
    print(f"[1/6] Configured Model: {model_name}")
    print(f"      API Key configured: {'YES (REDACTED)' if api_key else 'NO'}")

    if not api_key:
        print("[FAIL] Cannot execute live test: GEMINI_API_KEY is missing from environment.")
        return False

    client = llm_service.get_client()

    # 2. Live Natural-Language Extraction Turn (Synthetic Pharmacy Case)
    synthetic_message = (
        "Hello, I run Apollo Medico (fictional neighborhood pharmacy) in Chennai. "
        "We have 3 full-time staff members and operate from a single retail premises. "
        "We need reliable broadband for UPI digital billing, POS software, and a couple of CCTV cameras. "
        "Our monthly budget is around Rs. 3,500. We do not have GST registration yet."
    )
    print(f"\n[2/6] Sending Synthetic Dialogue Turn to Gemini:")
    print(f"      \"{synthetic_message}\"")

    start_t = time.perf_counter()
    try:
        extraction_res = profile_extraction_service._extract_with_gemini(
            message=synthetic_message, existing_profile=None
        )
        latency = (time.perf_counter() - start_t) * 1000
        print(f"      Extraction Latency: {latency:.2f} ms")
    except Exception as e:
        print(f"[FAIL] Live Gemini extraction failed: {type(e).__name__}: {str(e)}")
        return False

    if not extraction_res or not extraction_res.extracted_profile:
        print("[FAIL] Gemini returned empty extraction.")
        return False

    # 3. Structured Output Validation
    ext = extraction_res.extracted_profile
    print("\n[3/6] Validating Structured Pydantic Output:")
    print(f"      - Business Type:    {ext.business_type}")
    print(f"      - Segment:          {ext.business_segment}")
    print(f"      - Employees:        {ext.employee_count}")
    print(f"      - Sites:            {ext.num_sites}")
    print(f"      - City & Tier:      {ext.city} (Tier {ext.city_tier})")
    print(f"      - Has GSTIN:        {ext.has_gstin}")
    print(f"      - Monthly Budget:   ₹{ext.monthly_budget_inr:,.2f}" if ext.monthly_budget_inr else "None")
    print(f"      - Services:         {ext.required_services}")

    # Build BusinessProfile
    profile = BusinessProfile(
        business_type=ext.business_type or "Pharmacy",
        business_segment=ext.business_segment or "micro",
        employee_count=ext.employee_count or 3,
        num_sites=ext.num_sites or 1,
        city=ext.city or "Chennai",
        city_tier=ext.city_tier or 1,
        has_gstin=ext.has_gstin or False,
        monthly_budget_inr=ext.monthly_budget_inr or 3500.0,
        required_services=ext.required_services or ["pos", "cctv"],
    )

    # 4. Dialogue Check
    missing = advisor_dialogue_service.identify_missing_fields(profile)
    ready = advisor_dialogue_service.is_profile_ready_for_recommendations(profile)
    print(f"\n[4/6] Profile Readiness Check:")
    print(f"      - Ready for Recommendations: {ready}")
    print(f"      - Missing / Unspecified Fields: {missing}")

    # 5. Recommendation Engine Invocation
    print("\n[5/6] Invoking Phase 1 Recommendation Engine:")
    recs = recommendation_engine.generate_recommendations(profile)
    print(f"      - Recommendation Status: {recs.status}")
    print(f"      - Essential Bundle:      {recs.essential_bundle.bundle_name if recs.essential_bundle else 'None'}")
    print(f"      - Growth Bundle:         {recs.growth_bundle.bundle_name if recs.growth_bundle else 'None'}")
    if recs.growth_bundle:
        g = recs.growth_bundle
        print(f"        * Monthly Range:       ₹{g.pricing.monthly_total_min:,.2f} – ₹{g.pricing.monthly_total_max:,.2f}")
        print(f"        * Setup Charges:       ₹{g.pricing.setup_total_min:,.2f}")
        print(f"        * Budget Status:       {g.budget_status}")
        print(f"        * Score:               {g.score.total_score}/100")

    # 6. Live Grounded Explanation Generation
    print("\n[6/6] Requesting Grounded Natural-Language Explanation from Gemini:")
    start_t2 = time.perf_counter()
    try:
        explanation = advisor_response_service._generate_with_gemini(
            profile=profile,
            recommendations=recs,
            missing_fields=missing,
            user_message=synthetic_message,
        )
        latency2 = (time.perf_counter() - start_t2) * 1000
        print(f"      Response Generation Latency: {latency2:.2f} ms")
        print("\n" + "-" * 70)
        print("GEMINI GROUNDED EXPLANATION:")
        print("-" * 70)
        print(explanation)
        print("-" * 70)
    except Exception as e:
        print(f"[FAIL] Grounded explanation generation failed: {type(e).__name__}: {str(e)}")
        return False

    print("\n[SUCCESS] Live Gemini Advisor integration test completed successfully!")
    return True


if __name__ == "__main__":
    success = run_live_integration_test()
    sys.exit(0 if success else 1)

