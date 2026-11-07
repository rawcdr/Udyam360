"""Explicit customer consent capture and lifecycle tracking service."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from app.schemas.kyc import ConsentRecord


class KYCConsentService:
    """Manages customer consent records ensuring regulatory compliance prior to document processing."""

    def __init__(self):
        # kyc_case_id -> ConsentRecord
        self._consents: Dict[str, ConsentRecord] = {}

    def record_consent(
        self,
        case_id: str,
        consent_granted: bool,
        consent_version: str = "v1.0-2026",
        purpose: str = "Verification against mock registries and OCR onboarding processing"
    ) -> ConsentRecord:
        """Capture and record explicit customer consent."""
        consent_id = f"CNS-{uuid.uuid4().hex[:10].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        record = ConsentRecord(
            consent_id=consent_id,
            kyc_case_id=case_id,
            consent_granted=consent_granted,
            consent_version=consent_version,
            purpose=purpose,
            timestamp=now_iso,
            withdrawn=False,
            withdrawn_timestamp=None
        )

        self._consents[case_id] = record

        # Persist consent audit trail to SQLite database
        try:
            from app.db.database import SessionLocal
            from app.db.models import ConsentAudit
            from app.services.audit_service import audit_service
            db = SessionLocal()
            try:
                audit = ConsentAudit(
                    consent_id=consent_id,
                    case_id=case_id,
                    consent_type="DPDP_PROCESSING",
                    consent_granted=consent_granted,
                    consent_version=consent_version,
                    timestamp=now_iso,
                )
                db.add(audit)
                db.commit()

                audit_service.log_event(
                    event_type="KYC_CONSENT_CAPTURED",
                    actor_type="CUSTOMER",
                    outcome="SUCCESS" if consent_granted else "DENIED",
                    resource_type="CONSENT_RECORD",
                    resource_id=consent_id,
                    details={"case_id": case_id, "version": consent_version, "granted": consent_granted},
                )
            finally:
                db.close()
        except Exception:
            pass

        return record

    def get_consent(self, case_id: str) -> Optional[ConsentRecord]:
        """Retrieve active consent record for a KYC case."""
        return self._consents.get(case_id)

    def is_consent_active(self, case_id: str) -> bool:
        """Verify whether explicit, unwithdrawn consent is currently active."""
        consent = self._consents.get(case_id)
        if not consent:
            return False
        return consent.consent_granted and not consent.withdrawn

    def withdraw_consent(self, case_id: str) -> Optional[ConsentRecord]:
        """Record customer consent withdrawal, halting automated document processing."""
        consent = self._consents.get(case_id)
        if consent:
            consent.withdrawn = True
            consent.withdrawn_timestamp = datetime.now(timezone.utc).isoformat()
        return consent

    def delete_consent(self, case_id: str):
        """Remove consent record when case is cleared."""
        self._consents.pop(case_id, None)


kyc_consent_service = KYCConsentService()

