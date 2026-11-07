"""SQLAlchemy ORM models for Udyam360 persistent security & domain entities."""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Customer(Base):
    """Persistent customer identity grounded in verified mobile number."""
    __tablename__ = "customers"

    customer_id = Column(String(32), primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    business_name = Column(String(255), nullable=True)
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    sessions = relationship("CustomerSession", back_populates="customer", cascade="all, delete-orphan")


class CustomerSession(Base):
    """Server-side authenticated customer session record."""
    __tablename__ = "customer_sessions"

    session_id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(32), ForeignKey("customers.customer_id"), nullable=False, index=True)
    session_token_hash = Column(String(64), unique=True, index=True, nullable=False)
    csrf_token = Column(String(64), nullable=False)
    created_at = Column(String(50), nullable=False)
    last_activity_at = Column(String(50), nullable=False)
    expires_at = Column(String(50), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)

    customer = relationship("Customer", back_populates="sessions")


class OTPChallenge(Base):
    """Hashed OTP verification challenge with single-use and rate-limit tracking."""
    __tablename__ = "otp_challenges"

    challenge_id = Column(String(32), primary_key=True, index=True)
    phone_number = Column(String(20), index=True, nullable=False)
    otp_hash = Column(String(128), nullable=False)
    salt = Column(String(64), nullable=False)
    attempts_count = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    created_at = Column(String(50), nullable=False)
    expires_at = Column(String(50), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    ip_address = Column(String(45), nullable=True)


class AdminUser(Base):
    """Administrator credentials with bcrypt hashing and RBAC."""
    __tablename__ = "admin_users"

    admin_id = Column(String(32), primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), default="ExecutiveAdmin", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(String(50), nullable=True)
    created_at = Column(String(50), nullable=False)
    last_login_at = Column(String(50), nullable=True)

    sessions = relationship("AdminSession", back_populates="admin", cascade="all, delete-orphan")


class AdminSession(Base):
    """Server-side authenticated admin session record."""
    __tablename__ = "admin_sessions"

    session_id = Column(String(64), primary_key=True, index=True)
    admin_id = Column(String(32), ForeignKey("admin_users.admin_id"), nullable=False, index=True)
    session_token_hash = Column(String(64), unique=True, index=True, nullable=False)
    csrf_token = Column(String(64), nullable=False)
    role = Column(String(30), nullable=False)
    created_at = Column(String(50), nullable=False)
    last_activity_at = Column(String(50), nullable=False)
    expires_at = Column(String(50), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    ip_address = Column(String(45), nullable=True)

    admin = relationship("AdminUser", back_populates="sessions")


class ConsentAudit(Base):
    """Immutable audit trail of customer DPDP consent records and withdrawals."""
    __tablename__ = "consent_audits"

    consent_id = Column(String(32), primary_key=True, index=True)
    case_id = Column(String(32), index=True, nullable=False)
    customer_id = Column(String(32), index=True, nullable=True)
    consent_granted = Column(Boolean, nullable=False)
    consent_version = Column(String(20), default="v1.0-2026", nullable=False)
    purpose = Column(String(255), nullable=False)
    timestamp = Column(String(50), nullable=False)
    withdrawn = Column(Boolean, default=False, nullable=False)
    withdrawn_timestamp = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)


class SecurityAuditEvent(Base):
    """Structured security audit event logs for monitoring and compliance."""
    __tablename__ = "security_audit_logs"

    event_id = Column(String(32), primary_key=True, index=True)
    timestamp = Column(String(50), index=True, nullable=False)
    actor_id = Column(String(64), nullable=True)
    actor_type = Column(String(30), nullable=False)  # CUSTOMER, ADMIN, SYSTEM, ANONYMOUS
    event_type = Column(String(50), index=True, nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(64), nullable=True)
    outcome = Column(String(20), nullable=False)  # SUCCESS, FAILURE, DENIED
    details_json = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    correlation_id = Column(String(64), nullable=True)


class KYCCaseRecord(Base):
    """Persistent KYC case record with customer ownership."""
    __tablename__ = "kyc_cases"

    kyc_case_id = Column(String(32), primary_key=True, index=True)
    customer_id = Column(String(32), index=True, nullable=True)
    advisor_session_id = Column(String(64), index=True, nullable=False)
    quote_reference = Column(String(64), nullable=True)
    application_status = Column(String(30), nullable=False)
    business_profile_json = Column(Text, nullable=False)
    required_docs_json = Column(Text, nullable=False)
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)

    documents = relationship("KYCDocumentRecord", back_populates="case", cascade="all, delete-orphan")


class KYCDocumentRecord(Base):
    """Metadata record for an uploaded KYC document."""
    __tablename__ = "kyc_documents"

    document_id = Column(String(32), primary_key=True, index=True)
    kyc_case_id = Column(String(32), ForeignKey("kyc_cases.kyc_case_id"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(50), nullable=False)
    uploaded_at = Column(String(50), nullable=False)
    is_processed = Column(Boolean, default=False, nullable=False)
    extracted_fields_json = Column(Text, nullable=True)

    case = relationship("KYCCaseRecord", back_populates="documents")


class OrderRecordModel(Base):
    """Persistent customer order with state progression and customer ownership."""
    __tablename__ = "customer_orders"

    order_id = Column(String(32), primary_key=True, index=True)
    order_reference = Column(String(64), unique=True, index=True, nullable=False)
    customer_id = Column(String(32), index=True, nullable=True)
    quote_reference = Column(String(64), nullable=False)
    kyc_case_id = Column(String(32), nullable=True)
    advisor_session_id = Column(String(64), nullable=True)
    bundle_tier = Column(String(50), nullable=True)
    current_state = Column(String(50), nullable=False)
    customer_info_json = Column(Text, nullable=False)
    pricing_json = Column(Text, nullable=False)
    selected_product_ids_json = Column(Text, nullable=False)
    timeline_json = Column(Text, nullable=False)
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)

