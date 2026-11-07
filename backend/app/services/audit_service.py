"""Structured security audit logging service storing immutable audit trails in SQLite."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import Request

from app.db.database import SessionLocal
from app.db.models import SecurityAuditEvent

logger = logging.getLogger("udyam360.security.audit")


class AuditService:
    """Records security-critical events while strictly excluding credentials, OTPs, and PII."""

    # Sensitive keys that must be scrubbed from audit details
    SCRUB_KEYS = {
        "password", "otp", "raw_otp", "token", "session_token",
        "secret", "api_key", "file_bytes", "encryption_key"
    }

    def _sanitize_details(self, details: Optional[Dict[str, Any]]) -> Optional[str]:
        """Deep-cleans details dictionary removing credentials and secret material."""
        if not details:
            return None

        clean: Dict[str, Any] = {}
        for k, v in details.items():
            if any(sensitive in k.lower() for sensitive in self.SCRUB_KEYS):
                clean[k] = "[REDACTED]"
            elif isinstance(v, dict):
                clean[k] = json.loads(self._sanitize_details(v) or "{}")
            else:
                clean[k] = v

        return json.dumps(clean)

    def log_event(
        self,
        event_type: str,
        actor_type: str,
        outcome: str,
        actor_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        correlation_id: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> SecurityAuditEvent:
        """Persists a structured audit event to the database and logs a summary."""
        event_id = f"EVT-{uuid.uuid4().hex[:12].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # Derive IP from request if not explicitly provided
        client_ip = ip_address
        if not client_ip and request and request.client:
            client_ip = request.client.host

        clean_details_json = self._sanitize_details(details)

        db = SessionLocal()
        try:
            audit_entry = SecurityAuditEvent(
                event_id=event_id,
                timestamp=now_iso,
                actor_id=actor_id,
                actor_type=actor_type,
                event_type=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                outcome=outcome,
                details_json=clean_details_json,
                ip_address=client_ip,
                correlation_id=correlation_id or (request.headers.get("X-Correlation-ID") if request else None),
            )
            db.add(audit_entry)
            db.commit()
            db.refresh(audit_entry)

            logger.info(
                "[AUDIT] %s | %s | actor=%s(%s) | res=%s(%s) | outcome=%s",
                event_type,
                event_id,
                actor_type,
                actor_id or "anon",
                resource_type or "none",
                resource_id or "none",
                outcome,
            )
            return audit_entry
        except Exception as e:
            logger.error("[AUDIT FAILURE] Could not record audit event: %s", str(e))
            db.rollback()
            raise
        finally:
            db.close()


audit_service = AuditService()

