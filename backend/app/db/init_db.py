"""Database initialization and schema bootstrapping for Udyam360."""

import json
import os
import uuid
from datetime import datetime, timezone
import bcrypt

from .database import Base, SessionLocal, engine
from .models import AdminUser, OrderRecordModel


def init_database() -> None:
    """Creates tables and provisions initial administrative credentials if not present."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if default admin exists
        admin_username = os.getenv("ADMIN_INITIAL_USERNAME", "admin").strip().lower()
        existing_admin = db.query(AdminUser).filter(AdminUser.username == admin_username).first()

        if not existing_admin:
            raw_password = os.getenv("ADMIN_INITIAL_PASSWORD", "ExecutiveAdmin2026!")
            salt = bcrypt.gensalt(rounds=12)
            password_hash = bcrypt.hashpw(raw_password.encode(), salt).decode("utf-8")
            now_iso = datetime.now(timezone.utc).isoformat()

            admin = AdminUser(
                admin_id=f"adm_{uuid.uuid4().hex[:12]}",
                username=admin_username,
                password_hash=password_hash,
                role="ExecutiveAdmin",
                is_active=True,
                failed_login_attempts=0,
                locked_until=None,
                created_at=now_iso,
                last_login_at=None,
            )
            db.add(admin)
            db.commit()

        # Seed approved demo order if not in db
        demo_ref = "UDYAM-ORD-2026-C954DD97"
        existing_order = db.query(OrderRecordModel).filter(OrderRecordModel.order_reference == demo_ref).first()
        if not existing_order:
            now_iso = datetime.now(timezone.utc).isoformat()
            demo_record = OrderRecordModel(
                order_id="ord_demo_2026_c954dd97",
                order_reference=demo_ref,
                customer_id="CUST-DEMO-001",
                quote_reference="Q-DEMO-2026-GROWTH",
                kyc_case_id="KYC-DEMO-C954DD97",
                advisor_session_id="conv_demo_neelgiri",
                bundle_tier="Growth",
                current_state="KYC_VERIFIED",
                customer_info_json=json.dumps({
                    "business_name": "Apex Business Solutions",
                    "contact_name": "Dr. Shalini Gupta",
                    "contact_phone": "9811223344",
                    "contact_email": "contact@apexsolutions.example.com",
                    "city": "Delhi",
                    "installation_address": "B-42 Okhla Industrial Area Phase II, New Delhi 110020",
                    "segment": "prof",
                }),
                pricing_json=json.dumps({
                    "currency": "INR",
                    "monthly_recurring_charges": 3817.0,
                    "one_time_charges": 1500.0,
                    "estimated_first_month": 5317.0,
                    "gst_rate": 0.18,
                    "estimated_monthly_tax": 687.06,
                    "estimated_first_month_tax": 957.06,
                }),
                selected_product_ids_json=json.dumps([
                    "BIZ_FIBRE_300", "BACKUP_4G", "STATIC_IP",
                    "CLOUD_OFFICE", "CLOUD_BACKUP_1TB", "SEC_ENDPOINT"
                ]),
                timeline_json=json.dumps([
                    {"event_id": "evt_01", "from_state": None, "to_state": "QUOTE_CONFIRMED", "title": "Quote Confirmed", "description": "Selected Growth bundle registered in catalogue.", "timestamp": now_iso, "is_simulated": False},
                    {"event_id": "evt_02", "from_state": "QUOTE_CONFIRMED", "to_state": "KYC_PENDING", "title": "KYC Consent Captured", "description": "Digital DPDP consent recorded with timestamp audit.", "timestamp": now_iso, "is_simulated": False},
                    {"event_id": "evt_03", "from_state": "KYC_PENDING", "to_state": "KYC_VERIFICATION", "title": "OCR Verification Passed", "description": "Local CPU OCR extracted GSTIN and Udyam credentials.", "timestamp": now_iso, "is_simulated": False},
                    {"event_id": "evt_04", "from_state": "KYC_VERIFICATION", "to_state": "KYC_VERIFIED", "title": "Business Identity Approved", "description": "Entity active status and registrations verified against mock registries.", "timestamp": now_iso, "is_simulated": False},
                ]),
                created_at=now_iso,
                updated_at=now_iso,
            )
            db.add(demo_record)
            db.commit()

    finally:
        db.close()

