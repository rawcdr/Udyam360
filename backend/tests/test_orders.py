"""Unit and Integration Tests for Order Lifecycle, State Machine, and Tracking APIs."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.order import CustomerInfo, OrderCreateRequest, OrderState, PricingSnapshot
from app.services.order_service import OrderService

client = TestClient(app)


@pytest.fixture
def clean_order_service():
    """Provides a fresh isolated OrderService instance for unit testing."""
    return OrderService()


@pytest.fixture
def sample_order_request():
    return OrderCreateRequest(
        quote_reference="Q-TEST1234",
        selected_product_ids=["P01", "P03", "P14"],
        bundle_tier="Growth",
        customer_info=CustomerInfo(
            business_name="Apex Diagnostic Clinic",
            contact_name="Dr. Shalini Gupta",
            city="Pune",
            segment="prof",
        ),
        pricing=PricingSnapshot(
            monthly_recurring_charges=2499.0,
            one_time_charges=1000.0,
            estimated_first_month=3499.0,
        ),
    )


class TestOrderServiceUnit:
    """Unit tests for OrderService state machine logic."""

    def test_order_creation_generates_valid_references(self, clean_order_service, sample_order_request):
        order = clean_order_service.create_order(sample_order_request)
        assert order.order_id.startswith("ord_")
        assert order.order_reference.startswith("UDYAM-ORD-2026-")
        assert order.current_state == OrderState.QUOTE_CONFIRMED
        assert len(order.timeline) == 1
        assert order.timeline[0].to_state == OrderState.QUOTE_CONFIRMED
        assert not order.is_simulated_stage

    def test_order_lookup_by_id_and_reference(self, clean_order_service, sample_order_request):
        order = clean_order_service.create_order(sample_order_request)

        # Lookup by ID
        found_by_id = clean_order_service.get_order(order.order_id)
        assert found_by_id is not None
        assert found_by_id.order_reference == order.order_reference

        # Lookup by reference (case insensitive)
        found_by_ref = clean_order_service.get_order_by_reference(order.order_reference.lower())
        assert found_by_ref is not None
        assert found_by_ref.order_id == order.order_id

    def test_valid_sequential_lifecycle_progression(self, clean_order_service, sample_order_request):
        order = clean_order_service.create_order(sample_order_request)

        # QUOTE_CONFIRMED -> KYC_PENDING
        s1 = clean_order_service.advance_order_state(order.order_id)
        assert s1.current_state == OrderState.KYC_PENDING
        assert not s1.is_simulated_stage

        # KYC_PENDING -> KYC_VERIFICATION
        s2 = clean_order_service.advance_order_state(order.order_id)
        assert s2.current_state == OrderState.KYC_VERIFICATION
        assert not s2.is_simulated_stage

        # KYC_VERIFICATION -> KYC_VERIFIED
        s3 = clean_order_service.advance_order_state(order.order_id)
        assert s3.current_state == OrderState.KYC_VERIFIED
        assert not s3.is_simulated_stage

        # KYC_VERIFIED -> ORDER_PROCESSING (Simulated)
        s4 = clean_order_service.advance_order_state(order.order_id)
        assert s4.current_state == OrderState.ORDER_PROCESSING
        assert s4.is_simulated_stage

        # ORDER_PROCESSING -> ACTIVATION_IN_PROGRESS (Simulated)
        s5 = clean_order_service.advance_order_state(order.order_id)
        assert s5.current_state == OrderState.ACTIVATION_IN_PROGRESS
        assert s5.is_simulated_stage

        # ACTIVATION_IN_PROGRESS -> ACTIVATED (Simulated)
        s6 = clean_order_service.advance_order_state(order.order_id)
        assert s6.current_state == OrderState.ACTIVATED
        assert s6.is_simulated_stage
        assert len(s6.timeline) == 7

    def test_manual_review_branching(self, clean_order_service, sample_order_request):
        order = clean_order_service.create_order(sample_order_request)
        clean_order_service.advance_order_state(order.order_id, OrderState.KYC_PENDING)
        clean_order_service.advance_order_state(order.order_id, OrderState.KYC_VERIFICATION)

        # Transition to MANUAL_REVIEW
        rev = clean_order_service.advance_order_state(
            order.order_id,
            OrderState.MANUAL_REVIEW,
            notes="Document name discrepancy flagged",
        )
        assert rev.current_state == OrderState.MANUAL_REVIEW

        # Approved from MANUAL_REVIEW to KYC_VERIFIED
        appr = clean_order_service.advance_order_state(order.order_id, OrderState.KYC_VERIFIED)
        assert appr.current_state == OrderState.KYC_VERIFIED

    def test_invalid_transition_rejected(self, clean_order_service, sample_order_request):
        order = clean_order_service.create_order(sample_order_request)

        # QUOTE_CONFIRMED directly to ACTIVATED is forbidden
        with pytest.raises(ValueError, match="Invalid order state transition"):
            clean_order_service.advance_order_state(order.order_id, OrderState.ACTIVATED)

    def test_terminal_state_cannot_advance(self, clean_order_service, sample_order_request):
        order = clean_order_service.create_order(sample_order_request)
        clean_order_service.advance_order_state(order.order_id, OrderState.CANCELLED)

        with pytest.raises(ValueError, match="cannot be advanced further"):
            clean_order_service.advance_order_state(order.order_id)


class TestOrderAPIIntegration:
    """End-to-end HTTP integration tests for /api/v1/orders endpoints."""

    def test_create_order_api(self):
        payload = {
            "quote_reference": "Q-API-001",
            "selected_product_ids": ["P01", "P03"],
            "bundle_tier": "Essential",
            "customer_info": {
                "business_name": "Sharma General Store",
                "city": "Bengaluru",
                "segment": "micro",
            },
            "pricing": {
                "monthly_recurring_charges": 1499.0,
                "one_time_charges": 500.0,
                "estimated_first_month": 1999.0,
            },
        }
        res = client.post("/api/v1/orders", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert "order_id" in data
        assert data["order_reference"].startswith("UDYAM-ORD-2026-")
        assert data["current_state"] == "QUOTE_CONFIRMED"

        order_id = data["order_id"]
        order_ref = data["order_reference"]

        # Track by reference
        track_res = client.get(f"/api/v1/orders/track/{order_ref}")
        assert track_res.status_code == 200
        assert track_res.json()["order_id"] == order_id

        # Retrieve by id
        get_res = client.get(f"/api/v1/orders/{order_id}")
        assert get_res.status_code == 200

        # Retrieve timeline
        tl_res = client.get(f"/api/v1/orders/{order_id}/timeline")
        assert tl_res.status_code == 200
        assert len(tl_res.json()["timeline"]) >= 1

        # Advance order to next state
        adv_res = client.post(f"/api/v1/orders/{order_id}/advance")
        assert adv_res.status_code == 200
        assert adv_res.json()["current_state"] == "KYC_PENDING"

    def test_track_nonexistent_reference_returns_404(self):
        res = client.get("/api/v1/orders/track/UDYAM-ORD-NONEXISTENT")
        assert res.status_code == 404
        assert "No order found" in res.json()["detail"]

    def test_advance_invalid_transition_returns_400(self):
        # Create an order
        payload = {
            "quote_reference": "Q-API-002",
            "selected_product_ids": ["P01"],
            "bundle_tier": "Essential",
            "customer_info": {"business_name": "Test Micro"},
            "pricing": {
                "monthly_recurring_charges": 999.0,
                "one_time_charges": 0.0,
                "estimated_first_month": 999.0,
            },
        }
        res = client.post("/api/v1/orders", json=payload)
        order_id = res.json()["order_id"]

        # Attempt illegal jump to ACTIVATED
        adv_res = client.post(
            f"/api/v1/orders/{order_id}/advance",
            json={"target_state": "ACTIVATED"},
        )
        assert adv_res.status_code == 400
        assert "Invalid order state transition" in adv_res.json()["detail"]

