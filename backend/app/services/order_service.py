"""Order Lifecycle Management Service for Udyam360.

Implements a deterministic state machine managing the customer order lifecycle:
QUOTE_CONFIRMED -> KYC_PENDING -> KYC_VERIFICATION -> KYC_VERIFIED ->
ORDER_PROCESSING -> ACTIVATION_IN_PROGRESS -> ACTIVATED.

Later fulfillment stages (ORDER_PROCESSING, ACTIVATION_IN_PROGRESS, ACTIVATED)
are clearly marked as simulated telecom events for hackathon demonstration.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.schemas.order import (
    CustomerInfo,
    OrderCreateRequest,
    OrderResponse,
    OrderState,
    OrderTimelineEvent,
    OrderTimelineResponse,
    PricingSnapshot,
)


class OrderRecord:
    """Internal mutable record representing an order session."""

    def __init__(
        self,
        order_id: str,
        order_reference: str,
        quote_reference: str,
        selected_product_ids: List[str],
        customer_info: CustomerInfo,
        pricing: PricingSnapshot,
        advisor_session_id: Optional[str] = None,
        kyc_case_id: Optional[str] = None,
        bundle_tier: Optional[str] = "Custom",
        initial_state: OrderState = OrderState.QUOTE_CONFIRMED,
    ):
        self.order_id = order_id
        self.order_reference = order_reference
        self.quote_reference = quote_reference
        self.selected_product_ids = selected_product_ids
        self.customer_info = customer_info
        self.pricing = pricing
        self.advisor_session_id = advisor_session_id
        self.kyc_case_id = kyc_case_id
        self.bundle_tier = bundle_tier
        self.current_state = initial_state
        now = datetime.now(timezone.utc).isoformat()
        self.created_at = now
        self.updated_at = now
        self.timeline: List[OrderTimelineEvent] = []

    def to_response(self) -> OrderResponse:
        is_sim = self.current_state in (
            OrderState.ORDER_PROCESSING,
            OrderState.ACTIVATION_IN_PROGRESS,
            OrderState.ACTIVATED,
        )
        return OrderResponse(
            order_id=self.order_id,
            order_reference=self.order_reference,
            quote_reference=self.quote_reference,
            kyc_case_id=self.kyc_case_id,
            advisor_session_id=self.advisor_session_id,
            current_state=self.current_state,
            selected_product_ids=self.selected_product_ids,
            bundle_tier=self.bundle_tier,
            customer_info=self.customer_info,
            pricing=self.pricing,
            created_at=self.created_at,
            updated_at=self.updated_at,
            timeline=list(self.timeline),
            is_simulated_stage=is_sim,
            next_action_prompt=self._get_next_action_prompt(),
        )

    def _get_next_action_prompt(self) -> str:
        prompts = {
            OrderState.QUOTE_CONFIRMED: "Order created. Please proceed to KYC document upload.",
            OrderState.KYC_PENDING: "Pending document upload and customer consent.",
            OrderState.KYC_VERIFICATION: "Documents submitted. Local OCR verification in progress.",
            OrderState.MANUAL_REVIEW: "Document flag detected. Manual compliance review in progress.",
            OrderState.KYC_VERIFIED: "KYC verified. Ready for telecom provisioning dispatch.",
            OrderState.ORDER_PROCESSING: "Provisioning order generated (Simulated). Site readiness check.",
            OrderState.ACTIVATION_IN_PROGRESS: "Hardware dispatched & SIM configuration underway (Simulated).",
            OrderState.ACTIVATED: "All business services are active and ready to use! (Simulated).",
            OrderState.CANCELLED: "This order has been cancelled.",
        }
        return prompts.get(self.current_state, "")


class OrderService:
    """Manages order creation, lookup, and validated state transitions."""

    # Valid transitions map: source_state -> list of permitted target_states
    VALID_TRANSITIONS: Dict[OrderState, List[OrderState]] = {
        OrderState.QUOTE_CONFIRMED: [OrderState.KYC_PENDING, OrderState.KYC_VERIFIED, OrderState.CANCELLED],
        OrderState.KYC_PENDING: [OrderState.KYC_VERIFICATION, OrderState.KYC_VERIFIED, OrderState.CANCELLED],
        OrderState.KYC_VERIFICATION: [OrderState.KYC_VERIFIED, OrderState.MANUAL_REVIEW, OrderState.CANCELLED],
        OrderState.MANUAL_REVIEW: [OrderState.KYC_VERIFIED, OrderState.CANCELLED],
        OrderState.KYC_VERIFIED: [OrderState.ORDER_PROCESSING, OrderState.CANCELLED],
        OrderState.ORDER_PROCESSING: [OrderState.ACTIVATION_IN_PROGRESS, OrderState.CANCELLED],
        OrderState.ACTIVATION_IN_PROGRESS: [OrderState.ACTIVATED, OrderState.CANCELLED],
        OrderState.ACTIVATED: [],  # Terminal state
        OrderState.CANCELLED: [],  # Terminal state
    }

    # Sequential default next state
    DEFAULT_NEXT: Dict[OrderState, OrderState] = {
        OrderState.QUOTE_CONFIRMED: OrderState.KYC_PENDING,
        OrderState.KYC_PENDING: OrderState.KYC_VERIFICATION,
        OrderState.KYC_VERIFICATION: OrderState.KYC_VERIFIED,
        OrderState.MANUAL_REVIEW: OrderState.KYC_VERIFIED,
        OrderState.KYC_VERIFIED: OrderState.ORDER_PROCESSING,
        OrderState.ORDER_PROCESSING: OrderState.ACTIVATION_IN_PROGRESS,
        OrderState.ACTIVATION_IN_PROGRESS: OrderState.ACTIVATED,
    }

    def __init__(self):
        self._orders_by_id: Dict[str, OrderRecord] = {}
        self._orders_by_reference: Dict[str, OrderRecord] = {}

    def create_order(self, request: OrderCreateRequest) -> OrderResponse:
        """Create a new order record from quote and KYC details."""
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        hex_ref = uuid.uuid4().hex[:8].upper()
        order_reference = f"UDYAM-ORD-2026-{hex_ref}"

        # If KYC is already completed for this case, start at KYC_VERIFIED; else QUOTE_CONFIRMED
        initial_state = OrderState.QUOTE_CONFIRMED

        record = OrderRecord(
            order_id=order_id,
            order_reference=order_reference,
            quote_reference=request.quote_reference,
            selected_product_ids=request.selected_product_ids,
            customer_info=request.customer_info,
            pricing=request.pricing,
            advisor_session_id=request.advisor_session_id,
            kyc_case_id=request.kyc_case_id,
            bundle_tier=request.bundle_tier,
            initial_state=initial_state,
        )

        # Initial timeline event
        record.timeline.append(
            OrderTimelineEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                from_state=None,
                to_state=initial_state,
                title="Order Created & Quote Confirmed",
                description=f"Order {order_reference} initialized with quote reference {request.quote_reference}.",
                is_simulated=False,
            )
        )

        self._orders_by_id[order_id] = record
        self._orders_by_reference[order_reference] = record
        return record.to_response()

    def get_order(self, order_id: str) -> Optional[OrderResponse]:
        """Retrieve order by internal order_id."""
        record = self._orders_by_id.get(order_id)
        return record.to_response() if record else None

    def get_order_by_reference(self, order_reference: str) -> Optional[OrderResponse]:
        """Retrieve order by customer-facing order reference (case-insensitive)."""
        ref_clean = order_reference.strip().upper()
        record = self._orders_by_reference.get(ref_clean)
        return record.to_response() if record else None

    def get_timeline(self, order_id: str) -> Optional[OrderTimelineResponse]:
        """Retrieve milestone timeline for an order."""
        record = self._orders_by_id.get(order_id)
        if not record:
            return None
        is_sim = record.current_state in (
            OrderState.ORDER_PROCESSING,
            OrderState.ACTIVATION_IN_PROGRESS,
            OrderState.ACTIVATED,
        )
        return OrderTimelineResponse(
            order_id=record.order_id,
            order_reference=record.order_reference,
            current_state=record.current_state,
            timeline=list(record.timeline),
            is_simulated_stage=is_sim,
        )

    def advance_order_state(
        self,
        order_id: str,
        target_state: Optional[OrderState] = None,
        notes: Optional[str] = None,
    ) -> OrderResponse:
        """Advance the order to a valid subsequent state."""
        record = self._orders_by_id.get(order_id)
        if not record:
            raise KeyError(f"Order '{order_id}' not found.")

        current = record.current_state

        # Determine target state
        if target_state is None:
            if current not in self.DEFAULT_NEXT:
                raise ValueError(f"Order in state '{current.value}' cannot be advanced further.")
            target_state = self.DEFAULT_NEXT[current]

        # Validate transition
        allowed = self.VALID_TRANSITIONS.get(current, [])
        if target_state not in allowed:
            raise ValueError(
                f"Invalid order state transition from '{current.value}' to '{target_state.value}'. "
                f"Permitted next states: {[s.value for s in allowed]}"
            )

        # Build timeline title and description
        is_sim = target_state in (
            OrderState.ORDER_PROCESSING,
            OrderState.ACTIVATION_IN_PROGRESS,
            OrderState.ACTIVATED,
        )
        title, desc = self._build_event_description(current, target_state, notes, is_sim)

        record.timeline.append(
            OrderTimelineEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                from_state=current,
                to_state=target_state,
                title=title,
                description=desc,
                is_simulated=is_sim,
            )
        )

        record.current_state = target_state
        record.updated_at = datetime.now(timezone.utc).isoformat()
        return record.to_response()

    def _build_event_description(
        self,
        from_state: OrderState,
        to_state: OrderState,
        notes: Optional[str],
        is_sim: bool,
    ) -> Tuple[str, str]:
        descriptions = {
            OrderState.KYC_PENDING: (
                "KYC Pending",
                "Customer has entered the KYC verification workflow; awaiting document submission.",
            ),
            OrderState.KYC_VERIFICATION: (
                "KYC Processing Started",
                "Documents uploaded and submitted to local OCR and mock registry validation pipeline.",
            ),
            OrderState.MANUAL_REVIEW: (
                "Sent for Manual Review",
                notes or "Document verification flagged for compliance review. Under analyst inspection.",
            ),
            OrderState.KYC_VERIFIED: (
                "KYC Verification Completed",
                notes or "Business identity and documents successfully verified against registry records.",
            ),
            OrderState.ORDER_PROCESSING: (
                "Order Dispatched for Provisioning (Demo / Simulated)",
                notes or "Backend telecom provisioning order created. Allocating IP blocks and service profiles.",
            ),
            OrderState.ACTIVATION_IN_PROGRESS: (
                "Fulfillment & Activation in Progress (Demo / Simulated)",
                notes or "Field engineer dispatched. CPE equipment and SIM cards in transit to business site.",
            ),
            OrderState.ACTIVATED: (
                "Services Activated (Demo / Simulated)",
                notes or "Broadband circuit live, voice trunk operational, and cloud services provisioned.",
            ),
            OrderState.CANCELLED: (
                "Order Cancelled",
                notes or "Order has been cancelled by customer request or policy exception.",
            ),
        }
        title, default_desc = descriptions.get(to_state, ("State Update", notes or f"Moved to {to_state.value}"))
        if is_sim and "(Demo / Simulated)" not in title:
            title += " (Demo / Simulated)"
        return title, default_desc


# Global singleton instance
order_service = OrderService()

