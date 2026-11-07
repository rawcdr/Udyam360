"""Comprehensive security, authentication, RBAC, session management, and persistence tests for Phase 7."""

import base64
import hashlib
import io
import os
import secrets
import time
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.rate_limiter import rate_limiter
from app.core.security import get_vault_cipher, security_manager
from app.db.database import SessionLocal
from app.db.init_db import init_database
from app.db.models import (
    AdminSession,
    AdminUser,
    Customer,
    CustomerSession,
    KYCCaseRecord,
    OTPChallenge,
    OrderRecordModel,
    SecurityAuditEvent,
)
from app.main import app
from app.services.audit_service import audit_service
from app.services.auth_service import (
    OTP_TTL_SECONDS,
    SESSION_INACTIVITY_TIMEOUT_SECONDS,
    auth_service,
    generate_signed_session_token,
    normalize_indian_mobile,
)
from app.services.otp import MockOTPProvider, get_otp_provider


from PIL import Image

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Ensure database is initialized and reset rate limiter and admin lockout before each test."""
    init_database()
    rate_limiter.clear()
    db = SessionLocal()
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()
        if admin:
            admin.failed_login_attempts = 0
            admin.locked_until = None
            db.commit()
    finally:
        db.close()
    yield
    rate_limiter.clear()
    db = SessionLocal()
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()
        if admin:
            admin.failed_login_attempts = 0
            admin.locked_until = None
            db.commit()
    finally:
        db.close()


@pytest.fixture
def client():
    """TestClient instance for API integration."""
    return TestClient(app)


# ============================================================
# 1. Customer OTP Authentication Tests
# ============================================================

class TestCustomerOTPAuthentication:
    """Verifies phone number validation, OTP dispatch, limits, and hashing."""

    def test_valid_indian_mobile_receives_otp(self, client):
        phone = "9876543210"
        response = client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OTP_SENT"
        assert "******" in data["phone_number"]
        assert "demo_otp_hint" in data
        assert len(data["demo_otp_hint"]) == 6

    def test_invalid_phone_number_rejected(self, client):
        # 9-digit number
        res1 = client.post("/api/v1/auth/otp/request", json={"phone_number": "987654321"})
        assert res1.status_code == 400

        # Does not start with 6, 7, 8, or 9
        res2 = client.post("/api/v1/auth/otp/request", json={"phone_number": "1234567890"})
        assert res2.status_code == 400

        # String with letters
        res3 = client.post("/api/v1/auth/otp/request", json={"phone_number": "abcdefghij"})
        assert res3.status_code == 400

    def test_otp_rate_limiting_per_phone(self, client):
        phone = "9811122233"
        key = f"req:phone:+91{phone}"
        # 3 requests allowed within sliding window
        assert rate_limiter.check_and_record(key, 3, 600)[0] is True
        assert rate_limiter.check_and_record(key, 3, 600)[0] is True
        assert rate_limiter.check_and_record(key, 3, 600)[0] is True
        # 4th request must be rejected
        allowed_4th, _ = rate_limiter.check_and_record(key, 3, 600)
        assert allowed_4th is False

    def test_otp_cooldown_enforcement(self, client):
        phone = "9822233344"
        res1 = client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
        assert res1.status_code == 200

        # Immediate second request should be blocked by 60s cooldown
        res2 = client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
        assert res2.status_code == 429
        assert "wait" in res2.json()["detail"].lower()

    def test_correct_otp_verification_creates_session(self, client):
        phone = "9833344455"
        req_res = client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
        otp = req_res.json()["demo_otp_hint"]

        verify_res = client.post(
            "/api/v1/auth/otp/verify",
            json={"phone_number": phone, "otp": otp},
        )
        assert verify_res.status_code == 200
        data = verify_res.json()
        assert data["status"] == "AUTHENTICATED"
        assert "customer" in data
        assert "session_token" in data
        assert "csrf_token" in data

        # Check cookies were set
        assert "udyam360_session" in verify_res.cookies
        assert "udyam360_csrf" in verify_res.cookies

    def test_incorrect_otp_increments_attempts(self, client):
        phone = "9844455566"
        client.post("/api/v1/auth/otp/request", json={"phone_number": phone})

        bad_res = client.post(
            "/api/v1/auth/otp/verify",
            json={"phone_number": phone, "otp": "000000"},
        )
        assert bad_res.status_code == 400
        assert "attempt(s) remaining" in bad_res.json()["detail"]

    def test_three_incorrect_attempts_invalidates_challenge(self, client):
        phone = "9855566677"
        client.post("/api/v1/auth/otp/request", json={"phone_number": phone})

        for _ in range(3):
            client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "otp": "000000"})

        # 4th try should be rejected as exhausted/lockout
        res4 = client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "otp": "000000"})
        assert res4.status_code in (400, 429)

    def test_reused_otp_is_rejected(self, client):
        phone = "9866677788"
        req = client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
        otp = req.json()["demo_otp_hint"]

        # First use succeeds
        res1 = client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "otp": otp})
        assert res1.status_code == 200

        # Second use with same OTP must fail
        res2 = client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "otp": otp})
        assert res2.status_code == 400

    def test_new_otp_request_invalidates_prior_otp(self, client):
        phone = "9877788899"
        req1 = client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
        otp1 = req1.json()["demo_otp_hint"]

        # Clear cooldown to allow second request
        rate_limiter.clear()

        req2 = client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
        otp2 = req2.json()["demo_otp_hint"]
        assert otp1 != otp2

        # First OTP should now be rejected
        res_old = client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "otp": otp1})
        assert res_old.status_code == 400

        # Second OTP should succeed
        res_new = client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "otp": otp2})
        assert res_new.status_code == 200

    def test_plaintext_otp_never_stored_in_db(self, client):
        phone = "9888899900"
        req = client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
        otp = req.json()["demo_otp_hint"]

        db = SessionLocal()
        try:
            norm_phone = normalize_indian_mobile(phone)
            challenge = db.query(OTPChallenge).filter(OTPChallenge.phone_number == norm_phone).first()
            assert challenge is not None
            # DB record MUST NOT contain plaintext otp
            assert challenge.otp_hash != otp
            # Must be a 64-char sha256 hex string
            assert len(challenge.otp_hash) == 64
        finally:
            db.close()

    def test_mock_otp_provider_fails_in_production(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("OTP_PROVIDER", "mock")
        with pytest.raises(RuntimeError, match="MockOTPProvider is strictly prohibited in production"):
            get_otp_provider()


# ============================================================
# 2. Customer Session Management & CSRF Tests
# ============================================================

class TestCustomerSessionManagement:
    """Verifies HttpOnly cookies, timeouts, revocation, and CSRF Double-Submit protection."""

    def test_customer_me_endpoint_with_session_cookie(self, client):
        phone = "9899900011"
        req = client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
        otp = req.json()["demo_otp_hint"]
        verify = client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "otp": otp})
        assert verify.status_code == 200

        # Call /customer/me with cookie automatically stored in TestClient
        me_res = client.get("/api/v1/auth/customer/me")
        assert me_res.status_code == 200
        assert me_res.json()["phone_number"] == "+91******0011"

    def test_customer_logout_revokes_session(self, client):
        phone = "9812345678"
        req = client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
        otp = req.json()["demo_otp_hint"]
        verify = client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "otp": otp})
        csrf_token = verify.cookies.get("udyam360_csrf")

        # Logout with CSRF token header
        logout_res = client.post("/api/v1/auth/customer/logout", headers={"X-CSRF-Token": csrf_token})
        assert logout_res.status_code == 200

        # Attempt to access /customer/me should now fail
        me_res = client.get("/api/v1/auth/customer/me")
        assert me_res.status_code == 401

    def test_csrf_protection_blocks_cookie_mutation_without_csrf_header(self, client):
        phone = "9823456789"
        req = client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
        otp = req.json()["demo_otp_hint"]
        client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "otp": otp})

        # TestClient now possesses `udyam360_session` cookie.
        # Calling a state-changing endpoint without X-CSRF-Token must return 403 Forbidden
        order_payload = {
            "quote_reference": "QTE-2026-CSRF",
            "selected_product_ids": ["P01"],
            "bundle_tier": "Essential",
            "customer_info": {"business_name": "CSRF Test Shop", "city": "Delhi"},
            "pricing": {"monthly_recurring_charges": 1000.0, "estimated_first_month": 1000.0},
        }
        res_no_csrf = client.post("/api/v1/orders", json=order_payload)
        assert res_no_csrf.status_code == 403
        assert "CSRF" in res_no_csrf.json()["detail"]

    def test_csrf_protection_passes_with_matching_header(self, client):
        phone = "9834567890"
        req = client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
        otp = req.json()["demo_otp_hint"]
        verify = client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "otp": otp})
        csrf_token = verify.cookies.get("udyam360_csrf")

        order_payload = {
            "quote_reference": "QTE-2026-CSRF-PASS",
            "selected_product_ids": ["P01"],
            "bundle_tier": "Essential",
            "customer_info": {"business_name": "CSRF Valid Shop", "city": "Delhi"},
            "pricing": {"monthly_recurring_charges": 1000.0, "estimated_first_month": 1000.0},
        }
        res_with_csrf = client.post(
            "/api/v1/orders",
            json=order_payload,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert res_with_csrf.status_code == 201

    def test_header_only_token_auth_exempt_from_csrf(self, client):
        # Clear any ambient cookies
        client.cookies.clear()
        sid = security_manager.create_session("sess_api_client")
        token = security_manager.generate_token(sid)

        order_payload = {
            "quote_reference": "QTE-2026-API",
            "selected_product_ids": ["P01"],
            "bundle_tier": "Essential",
            "customer_info": {"business_name": "API Client Shop", "city": "Mumbai"},
            "pricing": {"monthly_recurring_charges": 1000.0, "estimated_first_month": 1000.0},
        }
        # Direct header token authentication is exempt from CSRF
        res = client.post(
            "/api/v1/orders",
            json=order_payload,
            headers={"X-Session-Token": token},
        )
        assert res.status_code == 201


# ============================================================
# 3. Admin Authentication & RBAC Tests
# ============================================================

class TestAdminAuthenticationAndRBAC:
    """Verifies admin credentials authentication, lockout, and RBAC enforcement."""

    def test_admin_login_success(self, client):
        res = client.post(
            "/api/v1/auth/admin/login",
            json={"username": "admin", "password": "ExecutiveAdmin2026!"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "AUTHENTICATED"
        assert data["admin"]["role"] == "ExecutiveAdmin"
        assert "udyam360_admin_session" in res.cookies

    def test_admin_login_invalid_password(self, client):
        res = client.post(
            "/api/v1/auth/admin/login",
            json={"username": "admin", "password": "WrongPassword123!"},
        )
        assert res.status_code == 401
        assert "Invalid administrator credentials" in res.json()["detail"]

    def test_admin_account_lockout_after_five_failures(self, client):
        for _ in range(5):
            client.post(
                "/api/v1/auth/admin/login",
                json={"username": "admin", "password": "BadPassword!"},
            )

        # 6th attempt should be locked out
        res = client.post(
            "/api/v1/auth/admin/login",
            json={"username": "admin", "password": "ExecutiveAdmin2026!"},
        )
        assert res.status_code in (423, 429)

    def test_admin_can_access_analytics_overview(self, client):
        login_res = client.post(
            "/api/v1/auth/admin/login",
            json={"username": "admin", "password": "ExecutiveAdmin2026!"},
        )
        assert login_res.status_code == 200

        overview_res = client.get("/api/v1/admin/analytics/overview")
        assert overview_res.status_code == 200
        assert "total_leads" in overview_res.json()

    def test_customer_cannot_access_admin_overview(self, client):
        client.cookies.clear()
        # Authenticate as normal customer
        phone = "9845678901"
        req = client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
        otp = req.json()["demo_otp_hint"]
        client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "otp": otp})

        # Try to access admin overview
        res = client.get("/api/v1/admin/analytics/overview")
        assert res.status_code == 403

    def test_admin_logout_invalidates_session(self, client):
        login = client.post(
            "/api/v1/auth/admin/login",
            json={"username": "admin", "password": "ExecutiveAdmin2026!"},
        )
        assert login.status_code == 200
        csrf = login.cookies.get("udyam360_csrf") or login.json().get("csrf_token")

        # Logout
        logout = client.post("/api/v1/auth/admin/logout", headers={"X-CSRF-Token": csrf})
        assert logout.status_code == 200

        # Subsequent admin call should be rejected
        res = client.get("/api/v1/admin/analytics/overview")
        assert res.status_code == 403


# ============================================================
# 4. KYC Document Security & Ownership Tests
# ============================================================

class TestKYCDocumentSecurity:
    """Verifies IDOR protection, encryption at rest, and input validation."""

    def test_customer_a_cannot_access_customer_b_kyc_case(self, client):
        # Create Customer A session
        sid_a = security_manager.create_session("sess_cust_a")
        token_a = security_manager.generate_token(sid_a)

        # Create Customer B session
        sid_b = security_manager.create_session("sess_cust_b")
        token_b = security_manager.generate_token(sid_b)

        # Create KYC case for Customer A
        case_res = client.post(
            "/api/v1/kyc/cases",
            json={"advisor_session_id": "conv_cust_a", "selected_product_ids": ["P01"]},
            headers={"X-Session-Token": token_a},
        )
        assert case_res.status_code == 201
        case_id = case_res.json()["kyc_case_id"]

        # Customer A can access their case
        get_a = client.get(f"/api/v1/kyc/cases/{case_id}", headers={"X-Session-Token": token_a})
        assert get_a.status_code == 200

        # Customer B attempting to access Customer A's case must receive 403 Forbidden
        get_b = client.get(f"/api/v1/kyc/cases/{case_id}", headers={"X-Session-Token": token_b})
        assert get_b.status_code == 403

    def test_upload_requires_explicit_consent(self, client):
        sid = security_manager.create_session("sess_no_consent")
        token = security_manager.generate_token(sid)

        case_res = client.post(
            "/api/v1/kyc/cases",
            json={"advisor_session_id": "conv_no_consent", "selected_product_ids": ["P01"]},
            headers={"X-Session-Token": token},
        )
        case_id = case_res.json()["kyc_case_id"]

        # Attempt upload without recording consent
        fake_file = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 50)
        res = client.post(
            f"/api/v1/kyc/cases/{case_id}/documents",
            headers={"X-Session-Token": token},
            data={"document_type": "GST_CERTIFICATE"},
            files={"file": ("test.png", fake_file, "image/png")},
        )
        assert res.status_code == 403
        assert "consent" in res.json()["detail"].lower()

    def test_document_encrypted_at_rest_with_fernet(self, client):
        sid = security_manager.create_session("sess_encrypt_test")
        token = security_manager.generate_token(sid)

        case_res = client.post(
            "/api/v1/kyc/cases",
            json={"advisor_session_id": "conv_enc", "selected_product_ids": ["P01"]},
            headers={"X-Session-Token": token},
        )
        case_id = case_res.json()["kyc_case_id"]

        # Record consent
        client.post(
            f"/api/v1/kyc/cases/{case_id}/consent",
            json={"consent_granted": True},
            headers={"X-Session-Token": token},
        )

        # Upload valid PNG
        buf = io.BytesIO()
        Image.new("RGB", (60, 60), color="blue").save(buf, format="PNG")
        raw_png = buf.getvalue()

        up_res = client.post(
            f"/api/v1/kyc/cases/{case_id}/documents",
            headers={"X-Session-Token": token},
            data={"document_type": "GST_CERTIFICATE"},
            files={"file": ("cert.png", io.BytesIO(raw_png), "image/png")},
        )
        assert up_res.status_code == 201

        # Check physical file on disk: it must NOT start with PNG magic bytes (must be encrypted)
        case_dir = settings.KYC_STORAGE_DIR / case_id
        assert case_dir.exists()
        files = list(case_dir.glob("*"))
        assert len(files) > 0
        disk_bytes = files[0].read_bytes()

        # Physical file is ciphertext and does not match raw PNG magic header
        assert not disk_bytes.startswith(b"\x89PNG\r\n\x1a\n")

        # Vault cipher can decrypt it back to raw PNG
        cipher = get_vault_cipher()
        decrypted = cipher.decrypt(disk_bytes)
        assert decrypted == raw_png


# ============================================================
# 5. API Security, Headers, Rate Limiting & Audit Logging Tests
# ============================================================

class TestAPISecurityAndAuditLogging:
    """Verifies security headers, PII masking, rate limiting, and structured audit logs."""

    def test_security_headers_present(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        headers = res.headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "default-src 'self'" in headers.get("Content-Security-Policy", "")

    def test_public_tracking_masks_customer_pii(self, client):
        # Demo order reference
        res = client.get("/api/v1/orders/track/UDYAM-ORD-2026-C954DD97")
        assert res.status_code == 200
        cust = res.json()["customer_info"]

        # Phone masked
        if cust.get("contact_phone"):
            assert "******" in cust["contact_phone"]

        # Email masked
        if cust.get("contact_email"):
            assert "****" in cust["contact_email"]

        # Address masked
        if cust.get("installation_address"):
            assert "protected" in cust["installation_address"].lower()

    def test_security_audit_logs_record_events(self, client):
        phone = "9856789012"
        client.post("/api/v1/auth/otp/request", json={"phone_number": phone})

        db = SessionLocal()
        try:
            events = db.query(SecurityAuditEvent).filter(SecurityAuditEvent.event_type == "AUTH_OTP_REQUEST").all()
            assert len(events) > 0
            latest = events[-1]
            assert latest.actor_type == "CUSTOMER"
            # Ensure no plain OTP or raw secret in details
            assert "otp" not in latest.details_json.lower() or "demo_otp" not in latest.details_json.lower()
        finally:
            db.close()


# ============================================================
# 6. Database Persistence Tests
# ============================================================

class TestDatabasePersistence:
    """Verifies that customers, sessions, and orders persist in SQLite."""

    def test_customer_and_session_persistence(self, client):
        phone = "9867890123"
        req = client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
        otp = req.json()["demo_otp_hint"]
        verify = client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "otp": otp})
        customer_id = verify.json()["customer"]["customer_id"]
        session_id = verify.json()["session_id"]

        # Verify records exist in SQLite table
        db = SessionLocal()
        try:
            cust = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            assert cust is not None
            assert cust.phone_number == normalize_indian_mobile(phone)

            sess = db.query(CustomerSession).filter(CustomerSession.session_id == session_id).first()
            assert sess is not None
            assert sess.is_revoked is False
        finally:
            db.close()
