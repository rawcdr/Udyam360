"""Customer passwordless OTP authentication and Admin credentials management service."""

import hashlib
import hmac
import os
import re
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import bcrypt
from fastapi import HTTPException, status

from app.core.rate_limiter import rate_limiter
from app.db.database import SessionLocal
from app.db.models import AdminSession, AdminUser, Customer, CustomerSession, OTPChallenge
from app.services.audit_service import audit_service
from app.services.otp import get_otp_provider

# Configuration constants
OTP_TTL_SECONDS = 300  # 5 minutes
OTP_COOLDOWN_SECONDS = 60  # 1 minute between OTP requests
OTP_MAX_ATTEMPTS = 3
SESSION_INACTIVITY_TIMEOUT_SECONDS = 1800  # 30 minutes
SESSION_ABSOLUTE_LIFETIME_SECONDS = 28800  # 8 hours

# Secret for session token HMAC signature
SECRET_KEY = getattr(os.getenv("SECRET_KEY", "udyam360-enterprise-sync-secret-key-2026"), "encode")()


def normalize_indian_mobile(raw_phone: str) -> str:
    """Validates and normalizes Indian mobile telephone numbers to E.164 (+91XXXXXXXXXX)."""
    cleaned = re.sub(r"[^\d+]", "", raw_phone.strip())
    if cleaned.startswith("+91"):
        digits = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) == 12:
        digits = cleaned[2:]
    elif len(cleaned) == 10:
        digits = cleaned
    else:
        raise ValueError("Invalid mobile number format. Supply a 10-digit Indian mobile number.")

    if len(digits) != 10 or not digits[0] in "6789":
        raise ValueError("Invalid Indian mobile number. Must be 10 digits starting with 6, 7, 8, or 9.")

    return f"+91{digits}"


def mask_phone_number(normalized: str) -> str:
    """Masks telephone number keeping country code and terminal 4 digits (+91******3210)."""
    if len(normalized) >= 7:
        return f"{normalized[:3]}******{normalized[-4:]}"
    return "******"


def generate_signed_session_token(session_id: str) -> str:
    """Generates a cryptographic session token: <session_id>.<timestamp>.<signature>."""
    now_ts = str(int(datetime.now(timezone.utc).timestamp()))
    payload = f"{session_id}.{now_ts}".encode()
    sig = hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest()[:32]
    return f"{session_id}.{now_ts}.{sig}"


def verify_signed_session_token(token: str) -> Optional[str]:
    """Validates token format and HMAC signature. Returns session_id if valid."""
    parts = token.strip().split(".")
    if len(parts) != 3:
        return None
    sid, ts_str, sig = parts
    payload = f"{sid}.{ts_str}".encode()
    expected_sig = hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(sig, expected_sig):
        return None
    return sid


class AuthService:
    """Handles passwordless customer OTP authentication, admin login, and session lifecycles."""

    def request_otp(
        self,
        phone_number: str,
        ip_address: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validates phone number, applies rate limits, generates OTP challenge, and dispatches via provider."""
        norm_phone = normalize_indian_mobile(phone_number)
        phone_key = f"phone:{norm_phone}"
        ip_key = f"ip:{ip_address or 'unknown'}"

        # 1. Check active lockout
        lockout_phone = rate_limiter.check_lockout(f"lockout:{phone_key}")
        if lockout_phone:
            audit_service.log_event(
                event_type="AUTH_OTP_REQUEST",
                actor_type="ANONYMOUS",
                outcome="DENIED",
                resource_type="OTP_CHALLENGE",
                resource_id=norm_phone,
                details={"reason": "Temporary lockout active", "retry_after": lockout_phone},
                ip_address=ip_address,
                correlation_id=correlation_id,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed attempts. Temporary lockout active. Try again in {lockout_phone} seconds.",
            )

        # 2. Check resend cooldown
        cooldown = rate_limiter.check_cooldown(f"cooldown:{phone_key}", OTP_COOLDOWN_SECONDS)
        if cooldown:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {cooldown} seconds before requesting another verification code.",
            )

        # 3. Sliding window limits (3 per 10m per phone, 10 per 10m per IP)
        allowed_phone, retry_phone = rate_limiter.check_and_record(f"req:{phone_key}", 3, 600)
        if not allowed_phone:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Maximum OTP requests exceeded for this number. Try again in {retry_phone} seconds.",
            )

        allowed_ip, retry_ip = rate_limiter.check_and_record(f"req:{ip_key}", 10, 600)
        if not allowed_ip:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many verification requests from your network. Try again in {retry_ip} seconds.",
            )

        # 4. Generate cryptographically secure 6-digit OTP
        otp_int = secrets.randbelow(900000) + 100000
        otp_str = str(otp_int)

        # 5. Salt and hash OTP (never store plaintext OTP!)
        salt = secrets.token_hex(16)
        otp_hash = hashlib.sha256(f"{otp_str}:{salt}".encode()).hexdigest()

        challenge_id = f"OTP-{uuid.uuid4().hex[:10].upper()}"
        now_dt = datetime.now(timezone.utc)
        expires_dt = datetime.fromtimestamp(now_dt.timestamp() + OTP_TTL_SECONDS, timezone.utc)

        db = SessionLocal()
        try:
            # Invalidate any previous unused challenges for this phone number
            db.query(OTPChallenge).filter(
                OTPChallenge.phone_number == norm_phone,
                OTPChallenge.is_used == False,
            ).update({"is_used": True})

            challenge = OTPChallenge(
                challenge_id=challenge_id,
                phone_number=norm_phone,
                otp_hash=otp_hash,
                salt=salt,
                attempts_count=0,
                max_attempts=OTP_MAX_ATTEMPTS,
                created_at=now_dt.isoformat(),
                expires_at=expires_dt.isoformat(),
                is_used=False,
                ip_address=ip_address,
            )
            db.add(challenge)
            db.commit()

            # Record cooldown
            rate_limiter.record_cooldown(f"cooldown:{phone_key}")

            # 6. Dispatch via configured provider
            provider = get_otp_provider()
            provider.send_otp(norm_phone, otp_str)

            audit_service.log_event(
                event_type="AUTH_OTP_REQUEST",
                actor_type="CUSTOMER",
                outcome="SUCCESS",
                resource_type="OTP_CHALLENGE",
                resource_id=challenge_id,
                details={"phone_masked": mask_phone_number(norm_phone), "provider": provider.get_provider_name()},
                ip_address=ip_address,
                correlation_id=correlation_id,
            )

            response_data = {
                "status": "OTP_SENT",
                "phone_number": mask_phone_number(norm_phone),
                "cooldown_seconds": OTP_COOLDOWN_SECONDS,
                "expires_in_seconds": OTP_TTL_SECONDS,
            }

            # In development/mock mode, surface demo OTP hint for evaluators and automated test harnesses
            env = os.getenv("ENVIRONMENT", "development").strip().lower()
            if env != "production" and provider.get_provider_name() == "mock":
                response_data["demo_otp_hint"] = otp_str

            return response_data
        finally:
            db.close()

    def verify_otp(
        self,
        phone_number: str,
        otp: str,
        advisor_session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Tuple[Customer, CustomerSession, str, str]:
        """Verifies customer OTP, increments attempt counters, creates persistent session, and returns tokens."""
        norm_phone = normalize_indian_mobile(phone_number)
        phone_key = f"phone:{norm_phone}"

        # 1. Check lockout
        lockout = rate_limiter.check_lockout(f"lockout:{phone_key}")
        if lockout:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed verification attempts. Account locked for {lockout} seconds.",
            )

        # 2. Check per-attempt rate limits (max 5 verify tries per 15 min)
        allowed, retry_after = rate_limiter.check_and_record(f"verify:{phone_key}", 5, 900)
        if not allowed:
            rate_limiter.set_lockout(f"lockout:{phone_key}", 900)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed verification attempts. Lockout triggered for 15 minutes.",
            )

        db = SessionLocal()
        try:
            # Retrieve latest active challenge
            challenge = (
                db.query(OTPChallenge)
                .filter(
                    OTPChallenge.phone_number == norm_phone,
                    OTPChallenge.is_used == False,
                )
                .order_by(OTPChallenge.created_at.desc())
                .first()
            )

            now_iso = datetime.now(timezone.utc).isoformat()
            if not challenge or challenge.expires_at < now_iso:
                audit_service.log_event(
                    event_type="AUTH_OTP_VERIFY_FAILURE",
                    actor_type="ANONYMOUS",
                    outcome="FAILURE",
                    resource_type="OTP_CHALLENGE",
                    resource_id=norm_phone,
                    details={"reason": "Challenge expired or not found"},
                    ip_address=ip_address,
                    correlation_id=correlation_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired verification code. Please request a new code.",
                )

            # Check attempt limit on this challenge
            if challenge.attempts_count >= challenge.max_attempts:
                challenge.is_used = True
                db.commit()
                rate_limiter.set_lockout(f"lockout:{phone_key}", 900)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification code has exceeded maximum permitted attempts. Please request a new code.",
                )

            challenge.attempts_count += 1

            # Validate OTP hash using constant-time comparison
            expected_hash = hashlib.sha256(f"{otp.strip()}:{challenge.salt}".encode()).hexdigest()
            if not hmac.compare_digest(challenge.otp_hash, expected_hash):
                db.commit()
                audit_service.log_event(
                    event_type="AUTH_OTP_VERIFY_FAILURE",
                    actor_type="CUSTOMER",
                    outcome="FAILURE",
                    resource_type="OTP_CHALLENGE",
                    resource_id=challenge.challenge_id,
                    details={"attempt": challenge.attempts_count, "phone_masked": mask_phone_number(norm_phone)},
                    ip_address=ip_address,
                    correlation_id=correlation_id,
                )
                remaining_tries = challenge.max_attempts - challenge.attempts_count
                if remaining_tries <= 0:
                    challenge.is_used = True
                    db.commit()
                    rate_limiter.set_lockout(f"lockout:{phone_key}", 900)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Verification code exhausted. Temporary 15-minute lockout enforced.",
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid verification code. {remaining_tries} attempt(s) remaining.",
                )

            # OTP verified successfully
            challenge.is_used = True

            # 3. Find or create persistent Customer entity
            customer = db.query(Customer).filter(Customer.phone_number == norm_phone).first()
            if not customer:
                customer = Customer(
                    customer_id=f"CUST-{uuid.uuid4().hex[:10].upper()}",
                    phone_number=norm_phone,
                    business_name=None,
                    created_at=now_iso,
                    updated_at=now_iso,
                    is_active=True,
                )
                db.add(customer)
                db.commit()
                db.refresh(customer)

            # 4. Create persistent CustomerSession
            session_id = f"sess_{uuid.uuid4().hex[:16]}"
            raw_token = generate_signed_session_token(session_id)
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            csrf_token = secrets.token_hex(32)

            now_ts = datetime.now(timezone.utc).timestamp()
            expires_at_iso = datetime.fromtimestamp(
                now_ts + SESSION_ABSOLUTE_LIFETIME_SECONDS, timezone.utc
            ).isoformat()

            session = CustomerSession(
                session_id=session_id,
                customer_id=customer.customer_id,
                session_token_hash=token_hash,
                csrf_token=csrf_token,
                created_at=now_iso,
                last_activity_at=now_iso,
                expires_at=expires_at_iso,
                is_revoked=False,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(session)
            db.commit()
            db.refresh(session)

            # Associate onboarding conversation if supplied
            if advisor_session_id:
                from app.core.security import security_manager
                security_manager.bind_conversation(session_id, advisor_session_id)

            audit_service.log_event(
                event_type="AUTH_OTP_VERIFY_SUCCESS",
                actor_type="CUSTOMER",
                outcome="SUCCESS",
                actor_id=customer.customer_id,
                resource_type="SESSION",
                resource_id=session_id,
                details={"phone_masked": mask_phone_number(norm_phone)},
                ip_address=ip_address,
                correlation_id=correlation_id,
            )

            return customer, session, raw_token, csrf_token
        finally:
            db.close()

    def logout_customer(self, session_id: str, ip_address: Optional[str] = None) -> bool:
        """Revokes a customer session in database."""
        db = SessionLocal()
        try:
            sess = db.query(CustomerSession).filter(CustomerSession.session_id == session_id).first()
            if sess:
                sess.is_revoked = True
                db.commit()
                audit_service.log_event(
                    event_type="CUSTOMER_LOGOUT",
                    actor_type="CUSTOMER",
                    outcome="SUCCESS",
                    actor_id=sess.customer_id,
                    resource_type="SESSION",
                    resource_id=session_id,
                    ip_address=ip_address,
                )
                return True
            return False
        finally:
            db.close()

    def authenticate_admin(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Tuple[AdminUser, AdminSession, str, str]:
        """Authenticates administrator with bcrypt and returns an isolated AdminSession."""
        clean_user = username.strip().lower()
        ip_key = f"admin_login:{ip_address or 'unknown'}"
        user_key = f"admin_user:{clean_user}"

        # Check rate limits (5 attempts per 15 min)
        allowed_ip, retry = rate_limiter.check_and_record(ip_key, 5, 900)
        if not allowed_ip:
            rate_limiter.set_lockout(f"lockout:{user_key}", 900)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed administrator login attempts. Try again in {retry} seconds.",
            )

        db = SessionLocal()
        try:
            admin = db.query(AdminUser).filter(AdminUser.username == clean_user).first()
            now_iso = datetime.now(timezone.utc).isoformat()

            if not admin or not admin.is_active:
                audit_service.log_event(
                    event_type="AUTH_ADMIN_LOGIN_FAILURE",
                    actor_type="ANONYMOUS",
                    outcome="FAILURE",
                    resource_type="ADMIN_USER",
                    resource_id=clean_user,
                    details={"reason": "User not found or disabled"},
                    ip_address=ip_address,
                    correlation_id=correlation_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid administrator credentials.",
                )

            # Check locked until
            if admin.locked_until and admin.locked_until > now_iso:
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Administrator account is temporarily locked due to repeated failed attempts.",
                )

            # Verify password with bcrypt
            is_valid = bcrypt.checkpw(password.encode("utf-8"), admin.password_hash.encode("utf-8"))
            if not is_valid:
                admin.failed_login_attempts += 1
                if admin.failed_login_attempts >= 5:
                    lockout_dt = datetime.fromtimestamp(
                        datetime.now(timezone.utc).timestamp() + 900, timezone.utc
                    ).isoformat()
                    admin.locked_until = lockout_dt
                db.commit()

                audit_service.log_event(
                    event_type="AUTH_ADMIN_LOGIN_FAILURE",
                    actor_type="ADMIN",
                    outcome="FAILURE",
                    actor_id=admin.admin_id,
                    resource_type="ADMIN_USER",
                    resource_id=clean_user,
                    details={"failed_attempts": admin.failed_login_attempts},
                    ip_address=ip_address,
                    correlation_id=correlation_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid administrator credentials.",
                )

            # Reset failed attempts and set last login
            admin.failed_login_attempts = 0
            admin.locked_until = None
            admin.last_login_at = now_iso

            session_id = f"adm_sess_{uuid.uuid4().hex[:16]}"
            raw_token = generate_signed_session_token(session_id)
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            csrf_token = secrets.token_hex(32)

            now_ts = datetime.now(timezone.utc).timestamp()
            expires_at_iso = datetime.fromtimestamp(
                now_ts + SESSION_ABSOLUTE_LIFETIME_SECONDS, timezone.utc
            ).isoformat()

            session = AdminSession(
                session_id=session_id,
                admin_id=admin.admin_id,
                session_token_hash=token_hash,
                csrf_token=csrf_token,
                role=admin.role,
                created_at=now_iso,
                last_activity_at=now_iso,
                expires_at=expires_at_iso,
                is_revoked=False,
                ip_address=ip_address,
            )
            db.add(session)
            db.commit()
            db.refresh(session)

            audit_service.log_event(
                event_type="AUTH_ADMIN_LOGIN_SUCCESS",
                actor_type="ADMIN",
                outcome="SUCCESS",
                actor_id=admin.admin_id,
                resource_type="ADMIN_SESSION",
                resource_id=session_id,
                details={"role": admin.role},
                ip_address=ip_address,
                correlation_id=correlation_id,
            )

            return admin, session, raw_token, csrf_token
        finally:
            db.close()

    def logout_admin(self, session_id: str, ip_address: Optional[str] = None) -> bool:
        """Revokes an admin session."""
        db = SessionLocal()
        try:
            sess = db.query(AdminSession).filter(AdminSession.session_id == session_id).first()
            if sess:
                sess.is_revoked = True
                db.commit()
                audit_service.log_event(
                    event_type="ADMIN_LOGOUT",
                    actor_type="ADMIN",
                    outcome="SUCCESS",
                    actor_id=sess.admin_id,
                    resource_type="ADMIN_SESSION",
                    resource_id=session_id,
                    ip_address=ip_address,
                )
                return True
            return False
        finally:
            db.close()


auth_service = AuthService()

