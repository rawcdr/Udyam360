"""Integration tests for FastAPI REST Endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_docs_and_openapi_endpoints():
    """Verify OpenAPI JSON and Swagger docs are accessible."""
    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    schema = openapi_resp.json()
    assert "paths" in schema
    assert "/api/v1/catalogue" in schema["paths"]
    assert "/api/v1/recommendations" in schema["paths"]


def test_health_check_endpoint():
    """Verify /health and /api/v1/health endpoints."""
    resp1 = client.get("/health")
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "HEALTHY"

    resp2 = client.get("/api/v1/health")
    assert resp2.status_code == 200


def test_catalogue_endpoints():
    """Verify GET /api/v1/catalogue and GET /api/v1/catalogue/{id}."""
    resp = client.get("/api/v1/catalogue")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 25

    # Specific product
    p01_resp = client.get("/api/v1/catalogue/P01")
    assert p01_resp.status_code == 200
    assert p01_resp.json()["product_name"] == "Biz Fibre 100"

    # Non-existent product
    bad_resp = client.get("/api/v1/catalogue/P99")
    assert bad_resp.status_code == 404


def test_segments_endpoint():
    """Verify GET /api/v1/segments returns supported segments."""
    resp = client.get("/api/v1/segments")
    assert resp.status_code == 200
    segs = resp.json()
    codes = [s["code"] for s in segs]
    assert "micro" in codes
    assert "prof" in codes


def test_eligibility_check_endpoint():
    """Verify POST /api/v1/eligibility/check."""
    payload = {
        "business_type": "Kirana Store",
        "business_segment": "micro",
        "employee_count": 2,
        "num_sites": 1,
        "city": "Jaipur",
        "city_tier": 2,
        "has_gstin": False,
    }
    resp = client.post("/api/v1/eligibility/check", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_evaluated"] == 25
    assert data["eligible_count"] > 0
    assert len(data["results"]) == 25


def test_recommendation_endpoint():
    """Verify POST /api/v1/recommendations."""
    payload = {
        "business_type": "CA Firm",
        "business_segment": "prof",
        "employee_count": 5,
        "num_sites": 1,
        "city": "Delhi",
        "city_tier": 1,
        "has_gstin": True,
        "monthly_budget_inr": 4500.0,
    }
    resp = client.post("/api/v1/recommendations", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["business_segment"] == "prof"
    assert data["essential_bundle"] is not None
    assert data["growth_bundle"] is not None
    assert data["premium_bundle"] is not None
    assert data["essential_bundle"]["score"]["total_score"] > 0


def test_quote_preview_endpoint():
    """Verify POST /api/v1/quotes/preview computes server-side quote and resolves dependencies."""
    payload = {
        "profile": {
            "business_type": "Retail Store",
            "business_segment": "micro",
            "employee_count": 2,
            "num_sites": 1,
            "city_tier": 2,
            "has_gstin": False,
        },
        "bundle_tier": "Growth",
        "selected_product_ids": ["P19", "P23"],  # POS & CCTV (both require internet)
    }
    resp = client.post("/api/v1/quotes/preview", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "quote_id" in data
    assert data["is_eligible"] is True
    # Broadband dependency must have been resolved
    product_ids = [p["product_id"] for p in data["pricing"]["product_breakdown"]]
    assert any(b in product_ids for b in ["P01", "P02", "P03", "P04", "P05", "P06"])
    assert data["pricing"]["monthly_total_min"] > 0


def test_quote_preview_invalid_product():
    """Verify 400 Bad Request when quoting unknown product ID."""
    payload = {
        "profile": {"business_type": "Store"},
        "selected_product_ids": ["P99_INVALID"],
    }
    resp = client.post("/api/v1/quotes/preview", json=payload)
    assert resp.status_code == 400
    assert "does not exist in catalogue" in resp.json()["detail"]

