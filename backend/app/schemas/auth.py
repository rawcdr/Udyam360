"""Pydantic schemas for Customer OTP and Admin authentication."""

from typing import Optional
from pydantic import BaseModel, Field


class OTPRequestPayload(BaseModel):
    """Payload to initiate a customer phone OTP request."""
    phone_number: str = Field(..., description="10-digit Indian mobile number (e.g., 9876543210 or +919876543210)")
    correlation_id: Optional[str] = Field(None, description="Optional request tracking correlation ID")


class OTPRequestResponse(BaseModel):
    """Response returned upon successful OTP dispatch."""
    status: str = Field("OTP_SENT", description="Status code indicating OTP was generated and dispatched")
    phone_number: str = Field(..., description="Masked telephone number (+91******3210)")
    cooldown_seconds: int = Field(60, description="Minimum seconds before another OTP may be requested")
    expires_in_seconds: int = Field(300, description="OTP validity window in seconds")
    demo_otp_hint: Optional[str] = Field(None, description="Demo OTP hint provided in non-production mode for testing")


class OTPVerifyPayload(BaseModel):
    """Payload to verify an OTP and authenticate customer."""
    phone_number: str = Field(..., description="10-digit Indian mobile number")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")
    advisor_session_id: Optional[str] = Field(None, description="Optional advisor conversation session to bind")
    correlation_id: Optional[str] = Field(None, description="Optional request correlation ID")


class CustomerProfileResponse(BaseModel):
    """Public customer profile model."""
    customer_id: str
    phone_number: str
    business_name: Optional[str] = None
    is_active: bool
    created_at: str


class CustomerAuthResponse(BaseModel):
    """Response returned upon successful OTP verification."""
    status: str = "AUTHENTICATED"
    customer: CustomerProfileResponse
    session_id: str
    session_token: str
    csrf_token: str
    message: str = "Customer authenticated successfully."


class AdminLoginPayload(BaseModel):
    """Payload for administrator credentials login."""
    username: str = Field(..., description="Administrator username")
    password: str = Field(..., min_length=8, description="Administrator password")
    correlation_id: Optional[str] = Field(None, description="Optional tracking correlation ID")


class AdminProfileResponse(BaseModel):
    """Public administrator profile model."""
    admin_id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    is_active: bool


class AdminAuthResponse(BaseModel):
    """Response returned upon successful administrator authentication."""
    status: str = "AUTHENTICATED"
    admin: AdminProfileResponse
    session_id: str
    session_token: str
    csrf_token: str
    message: str = "Administrator authenticated successfully."


class CSRFTokenResponse(BaseModel):
    """Response providing a CSRF token for web clients."""
    csrf_token: str

