"""Tests for Executive Admin Dashboard, Analytics, and ML Lead Propensity APIs."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ADMIN_HEADERS = {"X-Admin-Role": "ExecutiveAdmin"}
INVALID_HEADERS = {"X-Admin-Role": "PublicGuest"}


def test_admin_access_guard_rejection():
    """Verify endpoint rejects requests with invalid admin role header."""
    response = client.get("/api/v1/admin/analytics/overview", headers=INVALID_HEADERS)
    assert response.status_code == 403
    assert "Access Denied" in response.json()["detail"]


def test_admin_access_guard_success():
    """Verify endpoint accepts requests with valid admin roles."""
    for role in ["ExecutiveAdmin", "Admin", "SalesManager", "executiveadmin"]:
        response = client.get("/api/v1/admin/analytics/overview", headers={"X-Admin-Role": role})
        assert response.status_code == 200


def test_analytics_overview():
    """Verify headline KPI counts match smb_leads.csv actual data."""
    response = client.get("/api/v1/admin/analytics/overview", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["total_leads"] == 5000
    assert data["activated_leads"] == 368
    assert round(data["overall_conversion_rate_pct"], 2) == 7.36
    assert data["unconverted_leads"] == 5000 - 368
    assert data["needs_assessed_leads"] == 1974
    assert data["quote_accepted_leads"] == 861
    assert data["benchmark_match"]["total_leads_match"] is True
    assert data["benchmark_match"]["activated_match"] is True


def test_analytics_funnel():
    """Verify 6-stage funnel progression and bottleneck diagnosis."""
    response = client.get("/api/v1/admin/analytics/funnel", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    stages = {s["stage_name"]: s for s in data["stages"]}
    
    assert "Lead Intake" in stages
    assert stages["Lead Intake"]["count"] == 5000
    assert stages["Contacted"]["count"] == 3406
    assert stages["Needs Assessed"]["count"] == 1974
    assert stages["Quote Accepted"]["count"] == 861
    assert stages["KYC Complete"]["count"] == 588
    assert stages["Activated"]["count"] == 368

    # Verify largest absolute drop is Lead Intake to Contacted (1,594 drop)
    assert data["primary_bottleneck"]["volume_lost"] == 1594
    assert "Contacted" in data["primary_bottleneck"]["largest_volume_bottleneck"]


def test_analytics_segments():
    """Verify segment breakdown returns all 4 customer segments."""
    response = client.get("/api/v1/admin/analytics/segments", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    segments = response.json()
    assert len(segments) == 4
    segment_names = [s["segment"] for s in segments]
    assert "Micro retail & services" in segment_names
    assert "Professional offices" in segment_names
    assert "Small manufacturers" in segment_names
    assert "Small multi-site businesses" in segment_names


def test_analytics_sources():
    """Verify acquisition sources and identify top and bottom converting channels."""
    response = client.get("/api/v1/admin/analytics/sources", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    sources = {s["lead_source"]: s for s in response.json()}
    assert "Referral" in sources
    assert "WhatsApp campaign" in sources
    # Referral converts highest (~14.77%), WhatsApp lowest (~2.79%)
    assert sources["Referral"]["conversion_rate_pct"] > sources["WhatsApp campaign"]["conversion_rate_pct"]


def test_analytics_geography():
    """Verify city-tier and geographic hub analysis."""
    response = client.get("/api/v1/admin/analytics/geography", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "by_tier" in data
    tiers = {t["city_tier"]: t for t in data["by_tier"]}
    assert "Tier 1" in tiers or 1 in tiers or "1" in tiers or any("1" in str(k) for k in tiers.keys())
    assert len(data["top_cities"]) > 0


def test_ml_model_info():
    """Verify ML model registry provides architecture, version, and training specs."""
    response = client.get("/api/v1/admin/ml/model-info", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "LogisticRegression"
    assert data["splits"]["train_size"] == 3500
    assert len(data["feature_schema"]["categorical_features"]) == 12
    assert len(data["feature_schema"]["numeric_features"]) == 12


def test_ml_evaluation():
    """Verify held-out evaluation report metrics."""
    response = client.get("/api/v1/admin/ml/evaluation", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "held_out_test_metrics" in data
    assert data["held_out_test_metrics"]["roc_auc"] > 0.60
    assert "comparison" in data
    assert len(data["comparison"]) >= 3


def test_ml_feature_importance():
    """Verify model explainer feature importance list."""
    response = client.get("/api/v1/admin/ml/feature-importance", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    features = response.json()
    assert len(features) > 0
    assert "feature" in features[0]
    assert "coefficient" in features[0]


def test_ml_propensity_overview():
    """Verify eligible unconverted lead propensity bands and calibration metrics."""
    response = client.get("/api/v1/admin/ml/propensity-overview", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["total_historical_leads"] == 5000
    assert data["activated_leads"] == 368
    assert data["unconverted_leads"] == 4632
    assert data["eligible_leads_for_prioritization"] == 4632
    assert data["successfully_scored_leads"] == 4632
    assert data["excluded_leads_count"] == 368
    assert data["excluded_leads_by_reason"]["ALREADY_ACTIVATED"] == 368

    # Recalculated distribution strictly on 4,632 eligible leads
    assert data["high_propensity_count"] == 569
    assert data["medium_propensity_count"] == 1564
    assert data["low_propensity_count"] == 2499
    assert (
        data["high_propensity_count"]
        + data["medium_propensity_count"]
        + data["low_propensity_count"]
        == 4632
    )

    # Calibration audit checks
    assert data["baseline_brier_score"] == 0.068
    assert data["raw_brier_score"] == 0.2136
    assert data["calibrated_brier_score"] == 0.0666
    assert data["calibrated_brier_score"] < data["baseline_brier_score"]
    assert "CALIBRATED" in data["calibration_status"]


def test_activated_leads_excluded_from_actionable_list():
    """Verify that already-activated leads CANNOT appear in the actionable prospect table."""
    response = client.get("/api/v1/admin/ml/leads?page=1&page_size=100", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    leads = response.json()["leads"]
    assert len(leads) > 0
    for lead in leads:
        assert lead["stage_reached"] != "Activated"
        assert lead["outcome"] != "Activated"
        assert lead["is_eligible_for_sales_action"] is True
        assert lead["exclusion_reason"] is None


def test_eligible_stages_selection():
    """Verify querying eligible stages and confirming Activated returns zero actionable leads."""
    eligible_stages = ["Lead", "Contacted", "Needs assessed", "Quote accepted", "KYC complete"]
    for stg in eligible_stages:
        resp = client.get(f"/api/v1/admin/ml/leads?stage={stg}&page_size=5", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        for item in resp.json()["leads"]:
            assert item["stage_reached"].lower() == stg.lower()

    # Querying Activated in the actionable lead table must return zero
    resp_act = client.get("/api/v1/admin/ml/leads?stage=Activated", headers=ADMIN_HEADERS)
    assert resp_act.status_code == 200
    assert resp_act.json()["total_count"] == 0
    assert len(resp_act.json()["leads"]) == 0


def test_missing_feature_handling():
    """Verify inference pipeline handles missing prediction features without throwing or dropping."""
    # Completely sparse/minimal dictionary missing almost all optional allowlist features
    sparse_lead = {
        "lead_id": "SPARSE_TEST_LEAD",
        "segment": "Micro retail & services",
    }
    response = client.post(
        "/api/v1/admin/ml/score",
        json={"lead_dict": sparse_lead},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    res = response.json()
    assert 0.0 <= res["propensity_score"] <= 100.0
    assert res["propensity_band"] in ["HIGH", "MEDIUM", "LOW"]
    assert len(res["positive_factors"]) >= 0


def test_baseline_brier_and_calibration_evaluation():
    """Verify prevalence calculations, baseline Brier, and candidate Briers."""
    response = client.get("/api/v1/admin/ml/evaluation", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()

    # Prevalences
    assert data["prevalence"]["train"] == pytest.approx(0.0737, abs=1e-3)
    assert data["prevalence"]["test"] == pytest.approx(0.0733, abs=1e-3)

    # Baseline test Brier score = p*(1-p)
    assert data["baseline_brier_score"] == pytest.approx(0.0680, abs=1e-3)

    # Calibration assessment
    cal_info = data["calibration_assessment"]
    assert cal_info["raw_model"]["test_brier"] == pytest.approx(0.2136, abs=1e-3)
    assert cal_info["calibrated_model"]["test_brier"] == pytest.approx(0.0666, abs=1e-3)
    assert cal_info["calibrated_model"]["beats_baseline"] is True


def test_feature_odds_ratios_mathematical_validity():
    """Verify that all feature odds ratios are exp(beta), pct_change is (OR - 1)*100, and >= -100%."""
    import math

    response = client.get("/api/v1/admin/ml/feature-importance", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    features = response.json()
    assert len(features) > 0

    for item in features:
        coef = item["coefficient"]
        odds_ratio = item["odds_ratio"]
        pct_change = item["pct_change_in_odds"]

        # Check OR = exp(beta)
        expected_or = math.exp(coef)
        assert odds_ratio == pytest.approx(expected_or, rel=1e-2)

        # Check pct_change = (OR - 1) * 100
        expected_pct = (expected_or - 1.0) * 100.0
        assert pct_change == pytest.approx(expected_pct, abs=0.1)

        # Never describe a negative odds change below -100%
        assert pct_change >= -100.0

        # Check non-causal note presence
        assert item["non_causal_note"] is not None
        assert "causal" in item["non_causal_note"].lower()


def test_ml_score_single_lead():
    """Verify real-time single lead scoring endpoint with grounded drivers."""
    lead_dict = {
        "lead_id": "TEST_INBOUND_01",
        "lead_source": "Referral",
        "business_type": "Accounting / CA Firm",
        "segment": "Professional offices",
        "city": "Bengaluru",
        "city_tier": 1,
        "state": "Karnataka",
        "preferred_language": "English",
        "annual_turnover_band": "25L-1Cr",
        "has_gstin": "Y",
        "has_udyam": "Y",
        "current_internet": "Broadband",
        "current_provider": "Airtel",
        "contact_role": "Owner",
        "employee_count": 8,
        "num_sites": 1,
        "monthly_telecom_spend_inr": 6500,
        "products_of_interest": "P01;P07;P14",
    }
    response = client.post(
        "/api/v1/admin/ml/score",
        json={"lead_dict": lead_dict},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    res = response.json()
    assert 0.0 <= res["conversion_probability"] <= 1.0
    assert 0.0 <= res["propensity_score"] <= 100.0
    assert res["propensity_band"] in ["HIGH", "MEDIUM", "LOW"]
    assert len(res["positive_factors"]) > 0
    assert res["recommended_next_action"] is not None


def test_leads_table_pagination_and_filtering():
    """Verify lead table filtering by segment, stage, band, and search."""
    # Test default query
    response = client.get("/api/v1/admin/ml/leads?page=1&page_size=10", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data["leads"]) == 10
    assert data["total_count"] == 4632  # unconverted default

    # Test filtering by segment
    resp_seg = client.get(
        "/api/v1/admin/ml/leads?segment=Professional+offices&page_size=5",
        headers=ADMIN_HEADERS,
    )
    assert resp_seg.status_code == 200
    for item in resp_seg.json()["leads"]:
        assert item["segment"] == "Professional offices"

    # Test filtering by propensity band
    resp_band = client.get(
        "/api/v1/admin/ml/leads?band=HIGH&page_size=5",
        headers=ADMIN_HEADERS,
    )
    assert resp_band.status_code == 200
    for item in resp_band.json()["leads"]:
        assert item["propensity_band"] == "HIGH"


def test_lead_detail_and_sales_action():
    """Verify fetching single lead detail and recording sales audit action note."""
    # Fetch lead L00001
    response = client.get("/api/v1/admin/leads/L00001", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    lead = response.json()
    assert lead["lead_id"] == "L00001"
    assert "positive_factors" in lead

    # Log an action note
    action_payload = {
        "action_type": "Phone Call",
        "notes": "Discussed professional bundle pricing. Lead requested follow-up tomorrow.",
        "rep_name": "Airtel Account Manager Vikram",
    }
    action_resp = client.post(
        "/api/v1/admin/leads/L00001/action",
        json=action_payload,
        headers=ADMIN_HEADERS,
    )
    assert action_resp.status_code == 200
    action_data = action_resp.json()
    assert action_data["lead_id"] == "L00001"
    assert action_data["action_type"] == "Phone Call"

    # Verify action appears in updated lead details
    response_updated = client.get("/api/v1/admin/leads/L00001", headers=ADMIN_HEADERS)
    assert response_updated.status_code == 200
    assert len(response_updated.json()["sales_action_history"]) >= 1


def test_nonexistent_lead_404():
    """Verify appropriate 404 for missing lead ID."""
    response = client.get("/api/v1/admin/leads/INVALID_99999", headers=ADMIN_HEADERS)
    assert response.status_code == 404
