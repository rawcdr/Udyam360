"""Integration tests for Advisor REST Endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_advisor_start_endpoint():
    """Verify POST /api/v1/advisor/start initializes session."""
    resp = client.post("/api/v1/advisor/start")
    assert resp.status_code == 200
    data = resp.json()
    assert "conversation_id" in data
    assert data["conversation_id"].startswith("conv_")
    assert "welcome_message" in data
    assert len(data["suggested_prompts"]) > 0


def test_advisor_message_endpoint_conversation_flow():
    """Verify POST /api/v1/advisor/message multi-turn flow."""
    # 1. Start conversation
    start_resp = client.post("/api/v1/advisor/start")
    start_data = start_resp.json()
    cid = start_data["conversation_id"]
    token = start_data.get("session_token") or start_resp.headers.get("x-session-token")
    headers = {"X-Session-Token": token}

    # 2. Turn 1: Incomplete info
    t1_payload = {"conversation_id": cid, "message": "I run a pharmacy in Pune."}
    r1 = client.post("/api/v1/advisor/message", json=t1_payload, headers=headers)
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["conversation_id"] == cid
    assert d1["recommendations_available"] is True  # Location & business type ready
    assert d1["extracted_profile"]["business_type"] == "Pharmacy"

    # 3. Get conversation state (authenticated with session token)
    get_resp = client.get(f"/api/v1/advisor/conversation/{cid}", headers=headers)
    assert get_resp.status_code == 200
    state = get_resp.json()
    assert state["conversation_id"] == cid
    assert len(state["history"]) >= 2

    # 4. Reset conversation (authenticated with session token)
    reset_resp = client.post(f"/api/v1/advisor/reset/{cid}", headers=headers)
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "RESET_SUCCESSFUL"


def test_advisor_health_endpoint():
    """Verify GET /api/v1/advisor/health."""
    resp = client.get("/api/v1/advisor/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "advisor_enabled" in data
    assert "configured_model" in data
    assert "api_key_configured" in data
    assert "status" in data


def test_advisor_invalid_conversation_id():
    """Verify unauthenticated request without session token returns 401."""
    resp = client.get("/api/v1/advisor/conversation/conv_nonexistent_xyz")
    assert resp.status_code == 401

