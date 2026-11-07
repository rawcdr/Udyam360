"""Service powering the Smart KYC Exception Copilot & Live Registry Resolver.

Enables KYC Operations Officers to review AI-flagged Indian MSME documentation
discrepancies (e.g. Sole Proprietor Trade Name vs Legal Name, Address format variations),
evaluate LLM-derived risk assessments, and execute 1-click regulatory overrides.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas.admin import (
    KYCExceptionCase,
    KYCExceptionCrossCheck,
    KYCExceptionResolutionRequest,
    KYCExceptionResolutionResponse,
)
from app.services.audit_service import audit_service


class KYCExceptionService:
    def __init__(self):
        # In-memory store initialized with realistic Indian MSME telecom exception archetypes
        now_iso = datetime.now(timezone.utc).isoformat()
        self._exceptions: Dict[str, KYCExceptionCase] = {
            "KYC-EXP-9042": KYCExceptionCase(
                case_id="KYC-EXP-9042",
                customer_name="Rajesh Kumar Sharma",
                business_name="Shree Ganesh Textiles & Garments",
                trade_name="Shree Ganesh Textiles",
                legal_name="Rajesh Kumar Sharma (Sole Proprietorship)",
                city="Surat, Gujarat",
                segment="Micro Manufacturing / Retail",
                risk_level="LOW",
                confidence_score=91.4,
                flag_reason="Trade Name vs. Legal Entity Discrepancy & Address Format Variation",
                status="PENDING_REVIEW",
                created_at=now_iso,
                entity_structure="Sole Proprietorship registered under GSTIN 24AAAAA0000A1Z5",
                order_reference="UDYAM-ORD-2026-C954DD97",
                cross_checks=[
                    KYCExceptionCrossCheck(
                        check_name="PAN vs. Signatory Name",
                        status="MATCH",
                        detail="Signatory PAN (AAAAA0000A) matches applicant name 'Rajesh Kumar Sharma' with 100% confidence.",
                    ),
                    KYCExceptionCrossCheck(
                        check_name="GSTIN REG-06 Trade Name",
                        status="MINOR_VARIATION",
                        detail="Trade Name 'Shree Ganesh Textiles' matches GSTIN principal business name (Omits '& Garments').",
                    ),
                    KYCExceptionCrossCheck(
                        check_name="Commercial Address Verification",
                        status="MATCH",
                        detail="Electricity bill address (Shop 14, Ring Road Market, Surat) matches GSTIN principal place of business.",
                    ),
                    KYCExceptionCrossCheck(
                        check_name="Udyam MSME Registration",
                        status="MATCH",
                        detail="Udyam Certificate UDYAM-GJ-01-0012345 active; enterprise category: Micro Manufacturing.",
                    ),
                ],
                copilot_analysis=(
                    "Sole Proprietorship archetype detected. In Indian MSME law, sole proprietorships "
                    "operate under a commercial trade name while banking and PAN remain in the individual proprietor's name. "
                    "All primary identifiers (PAN, Udyam, Commercial Address) show high integrity with 0% fraud signals."
                ),
                copilot_recommendation="RECOMMENDED ACTION: APPROVE. Discrepancy is standard Indian MSME trade formatting. SLA risk if stalled: High.",
            ),
            "KYC-EXP-8109": KYCExceptionCase(
                case_id="KYC-EXP-8109",
                customer_name="Dr. Anita Deshmukh",
                business_name="Apex Healthcare Diagnostic Lab",
                trade_name="Apex Diagnostic Clinic",
                legal_name="Apex Healthcare Services LLP",
                city="Pune, Maharashtra",
                segment="Healthcare & Professional Services",
                risk_level="LOW",
                confidence_score=89.2,
                flag_reason="LLP Designated Partner Signatory vs Certificate of Incorporation",
                status="PENDING_REVIEW",
                created_at=now_iso,
                entity_structure="Limited Liability Partnership (LLP) registered under MCA",
                order_reference="UDYAM-ORD-2026-78E31A02",
                cross_checks=[
                    KYCExceptionCrossCheck(
                        check_name="MCA Company Master Data",
                        status="MATCH",
                        detail="LLP Identification Number (LLPIN: AAA-1234) active and verified on Ministry of Corporate Affairs registry.",
                    ),
                    KYCExceptionCrossCheck(
                        check_name="Designated Partner DPIN Match",
                        status="MATCH",
                        detail="Signatory Dr. Anita Deshmukh verified as Active Designated Partner (DPIN 08765432).",
                    ),
                    KYCExceptionCrossCheck(
                        check_name="Utility Bill Freshness",
                        status="MINOR_VARIATION",
                        detail="Commercial MSEDCL electricity bill dated 94 days ago (Threshold: 90 days; 4 days grace).",
                    ),
                ],
                copilot_analysis=(
                    "Professional medical clinic operating as an LLP. Signatory authority confirmed through official MCA "
                    "registry. Minor 4-day freshness variance on electricity bill is offset by active municipal biomedical license."
                ),
                copilot_recommendation="RECOMMENDED ACTION: APPROVE with grace waiver for utility bill freshness.",
            ),
            "KYC-EXP-7721": KYCExceptionCase(
                case_id="KYC-EXP-7721",
                customer_name="Mohammed Farooq Khan",
                business_name="Al-Buraq Freight Logistics",
                trade_name="Al Buraq Express Delivery",
                legal_name="Al-Buraq Freight & Transport Pvt Ltd",
                city="Bengaluru, Karnataka",
                segment="Logistics & Warehousing",
                risk_level="MEDIUM",
                confidence_score=78.6,
                flag_reason="Registered Office Pincode Discrepancy (560002 vs 560027)",
                status="PENDING_REVIEW",
                created_at=now_iso,
                entity_structure="Private Limited Company",
                order_reference="UDYAM-ORD-2026-F149B890",
                cross_checks=[
                    KYCExceptionCrossCheck(
                        check_name="CIN Verification (MCA)",
                        status="MATCH",
                        detail="Corporate Identification Number U63090KA2021PTC145678 active and in good standing.",
                    ),
                    KYCExceptionCrossCheck(
                        check_name="Pincode Cross-Check",
                        status="MISMATCH",
                        detail="GSTIN shows Pincode 560027 (Shantinagar); Lease agreement submitted lists 560002 (City Market warehouse).",
                    ),
                    KYCExceptionCrossCheck(
                        check_name="Director DIN Verification",
                        status="MATCH",
                        detail="Managing Director DIN matches signatory Aadhaar / PAN exactly.",
                    ),
                ],
                copilot_analysis=(
                    "Warehouse location differs by 2 km from registered corporate office address. "
                    "Common pattern where operating logistics hub is different from registered office."
                ),
                copilot_recommendation="RECOMMENDED ACTION: Request Additional Branch Office Annexure or approve as operating branch address.",
            ),
        }

    def list_exceptions(self, status: Optional[str] = None) -> List[KYCExceptionCase]:
        """Returns list of KYC exceptions, optionally filtered by status."""
        items = list(self._exceptions.values())
        if status and status.upper() != "ALL":
            items = [e for e in items if e.status == status.upper()]
        return sorted(items, key=lambda x: x.created_at, reverse=True)

    def get_exception(self, case_id: str) -> Optional[KYCExceptionCase]:
        return self._exceptions.get(case_id)

    def resolve_exception(
        self,
        case_id: str,
        request: KYCExceptionResolutionRequest,
    ) -> KYCExceptionResolutionResponse:
        case = self._exceptions.get(case_id)
        if not case:
            raise KeyError(f"KYC Exception case '{case_id}' not found.")

        now_iso = datetime.now(timezone.utc).isoformat()
        action = request.action.upper()

        if action == "APPROVE":
            new_status = "APPROVED"
            order_status = "ORDER_PROCESSING"
        elif action == "REJECT":
            new_status = "REJECTED"
            order_status = "REJECTED"
        else:
            new_status = "INFO_REQUESTED"
            order_status = "KYC_PENDING"

        case.status = new_status
        case.reviewed_at = now_iso
        case.reviewed_by = request.officer_name or "KYC Compliance Officer"
        case.review_notes = request.notes

        # Advance order if linked
        if case.order_reference:
            try:
                from app.services.order_service import order_service
                from app.schemas.orders import OrderState
                # If approved, update order state in order service
                if action == "APPROVE":
                    order_obj = order_service.get_order_by_reference(case.order_reference)
                    if order_obj:
                        order_service.update_order_state(
                            order_obj.order_id,
                            OrderState.KYC_VERIFIED,
                            note=f"KYC Exception {case_id} approved by officer: {request.notes}",
                        )
                        order_service.update_order_state(
                            order_obj.order_id,
                            OrderState.ORDER_PROCESSING,
                            note="Provisioning commenced automatically following KYC exception approval.",
                        )
            except Exception:
                pass

        # Log security and compliance audit event
        audit_service.log_event(
            event_type="KYC_EXCEPTION_RESOLVED",
            actor_type="ADMIN",
            outcome="SUCCESS",
            resource_type="KYC_CASE",
            resource_id=case_id,
            details={
                "action": action,
                "reviewed_by": case.reviewed_by,
                "notes": request.notes,
                "confidence_score": case.confidence_score,
                "order_reference": case.order_reference,
            },
        )

        return KYCExceptionResolutionResponse(
            case_id=case_id,
            status=new_status,
            action_taken=action,
            reviewed_by=case.reviewed_by,
            reviewed_at=now_iso,
            notes=request.notes,
            order_reference=case.order_reference,
            order_status=order_status,
        )


kyc_exception_service = KYCExceptionService()

