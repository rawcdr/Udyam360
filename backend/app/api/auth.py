"""Authentication API endpoints for customer passwordless OTP and administrator login."""

import os
import secrets
from typing import Optional
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import AdminSession, AdminUser, Customer, CustomerSession
from app.schemas.auth import (
    AdminAuthResponse,
    AdminLoginPayload,
    AdminProfileResponse,
    CSRFTokenResponse,
    CustomerAuthResponse,
    CustomerProfileResponse,
    OTPRequestPayload,
    OTPRequestResponse,
    OTPVerifyPayload,
)
from app.services.auth_service import (
    SESSION_ABSOLUTE_LIFETIME_SECONDS,
    auth_service,
    mask_phone_number,
    verify_signed_session_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").strip().lower() == "production"
COOKIE_MAX_AGE = SESSION_ABSOLUTE_LIFETIME_SECONDS


def get_client_ip(request: Request) -> str:
    """Extracts client IP considering forwarding headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


# ============================================================
# Customer OTP Endpoints
# ============================================================

@router.post(
    "/otp/request",
    response_model=OTPRequestResponse,
    summary="Request a 6-digit verification code sent via SMS",
)
def request_customer_otp(payload: OTPRequestPayload, request: Request):
    """Generates and dispatches a time-limited 6-digit OTP to an Indian mobile number."""
    ip = get_client_ip(request)
    try:
        result = auth_service.request_otp(
            phone_number=payload.phone_number,
            ip_address=ip,
            correlation_id=payload.correlation_id,
        )
        return OTPRequestResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/otp/verify",
    response_model=CustomerAuthResponse,
    summary="Verify OTP and establish authenticated customer session",
)
def verify_customer_otp(payload: OTPVerifyPayload, request: Request, response: Response):
    """Verifies OTP, persists session, and sets secure HttpOnly session cookies."""
    ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    try:
        customer, session, session_token, csrf_token = auth_service.verify_otp(
            phone_number=payload.phone_number,
            otp=payload.otp,
            advisor_session_id=payload.advisor_session_id,
            ip_address=ip,
            user_agent=user_agent,
            correlation_id=payload.correlation_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Set secure HttpOnly session cookie
    response.set_cookie(
        key="udyam360_session",
        value=session_token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )

    # Set readable CSRF token cookie for Double-Submit protection
    response.set_cookie(
        key="udyam360_csrf",
        value=csrf_token,
        httponly=False,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )

    return CustomerAuthResponse(
        status="AUTHENTICATED",
        customer=CustomerProfileResponse(
            customer_id=customer.customer_id,
            phone_number=mask_phone_number(customer.phone_number),
            business_name=customer.business_name,
            is_active=customer.is_active,
            created_at=customer.created_at,
        ),
        session_id=session.session_id,
        session_token=session_token,
        csrf_token=csrf_token,
    )


@router.get(
    "/customer/me",
    response_model=CustomerProfileResponse,
    summary="Get authenticated customer profile",
)
def get_current_customer_profile(
    udyam360_session: Optional[str] = Cookie(None),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    """Returns the profile of the currently authenticated customer."""
    token = udyam360_session or x_session_token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in with your phone number.",
        )

    session_id = verify_signed_session_token(token)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token.",
        )

    sess = db.query(CustomerSession).filter(CustomerSession.session_id == session_id).first()
    if not sess or sess.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked or expired.",
        )

    customer = db.query(Customer).filter(Customer.customer_id == sess.customer_id).first()
    if not customer or not customer.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer account inactive or not found.",
        )

    return CustomerProfileResponse(
        customer_id=customer.customer_id,
        phone_number=mask_phone_number(customer.phone_number),
        business_name=customer.business_name,
        is_active=customer.is_active,
        created_at=customer.created_at,
    )


@router.post(
    "/customer/logout",
    summary="Log out authenticated customer and invalidate session",
)
def logout_customer(
    response: Response,
    request: Request,
    udyam360_session: Optional[str] = Cookie(None),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Revokes active customer session and clears cookies."""
    token = udyam360_session or x_session_token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if token:
        session_id = verify_signed_session_token(token)
        if session_id:
            auth_service.logout_customer(session_id, ip_address=get_client_ip(request))

    response.delete_cookie(key="udyam360_session", path="/")
    response.delete_cookie(key="udyam360_csrf", path="/")
    return {"status": "LOGGED_OUT", "message": "Successfully logged out."}


# ============================================================
# Administrator Authentication Endpoints
# ============================================================

@router.post(
    "/admin/login",
    response_model=AdminAuthResponse,
    summary="Administrator login with username and password",
)
def login_admin(payload: AdminLoginPayload, request: Request, response: Response):
    """Authenticates administrator with bcrypt, sets HttpOnly cookie, and returns session tokens."""
    ip = get_client_ip(request)

    admin, session, session_token, csrf_token = auth_service.authenticate_admin(
        username=payload.username,
        password=payload.password,
        ip_address=ip,
        correlation_id=payload.correlation_id,
    )

    # Set secure HttpOnly admin session cookie
    response.set_cookie(
        key="udyam360_admin_session",
        value=session_token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )

    # Set readable CSRF cookie
    response.set_cookie(
        key="udyam360_csrf",
        value=csrf_token,
        httponly=False,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )

    return AdminAuthResponse(
        status="AUTHENTICATED",
        admin=AdminProfileResponse(
            admin_id=admin.admin_id,
            username=admin.username,
            email=getattr(admin, "email", None),
            full_name=getattr(admin, "full_name", None),
            role=admin.role,
            is_active=admin.is_active,
        ),
        session_id=session.session_id,
        session_token=session_token,
        csrf_token=csrf_token,
    )


@router.get(
    "/admin/me",
    response_model=AdminProfileResponse,
    summary="Get authenticated administrator profile",
)
def get_current_admin_profile(
    udyam360_admin_session: Optional[str] = Cookie(None),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    """Returns profile and role of currently authenticated administrator."""
    token = udyam360_admin_session or x_session_token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator authentication required.",
        )

    session_id = verify_signed_session_token(token)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired administrator session.",
        )

    sess = db.query(AdminSession).filter(AdminSession.session_id == session_id).first()
    if not sess or sess.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator session has expired or been revoked.",
        )

    admin = db.query(AdminUser).filter(AdminUser.admin_id == sess.admin_id).first()
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator account disabled or not found.",
        )

    return AdminProfileResponse(
        admin_id=admin.admin_id,
        username=admin.username,
        email=getattr(admin, "email", None),
        full_name=getattr(admin, "full_name", None),
        role=sess.role,
        is_active=admin.is_active,
    )


@router.post(
    "/admin/logout",
    summary="Log out administrator and invalidate session",
)
def logout_admin(
    response: Response,
    request: Request,
    udyam360_admin_session: Optional[str] = Cookie(None),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Revokes active administrator session and clears cookies."""
    token = udyam360_admin_session or x_session_token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if token:
        session_id = verify_signed_session_token(token)
        if session_id:
            auth_service.logout_admin(session_id, ip_address=get_client_ip(request))

    response.delete_cookie(key="udyam360_admin_session", path="/")
    response.delete_cookie(key="udyam360_csrf", path="/")
    return {"status": "LOGGED_OUT", "message": "Administrator logged out successfully."}


# ============================================================
# CSRF Token Generation
# ============================================================

@router.get(
    "/csrf",
    response_model=CSRFTokenResponse,
    summary="Obtain a valid CSRF token and set cookie",
)
def get_csrf_token(response: Response):
    """Generates a cryptographically strong CSRF token and sets the cookie."""
    token = secrets.token_hex(32)
    response.set_cookie(
        key="udyam360_csrf",
        value=token,
        httponly=False,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )
    return CSRFTokenResponse(csrf_token=token)
