"""FastAPI router for Order Management, State Progression, and Status Tracking."""

from fastapi import APIRouter, HTTPException, Path, status

from app.schemas.order import (
    OrderAdvanceRequest,
    OrderCreateRequest,
    OrderResponse,
    OrderTimelineResponse,
)
from app.services.order_service import order_service

router = APIRouter(prefix="/orders", tags=["Order Lifecycle & Tracking"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new MSME digital onboarding order",
    description="Initiates an order record from confirmed quote pricing, selected products, and customer profile.",
)
def create_order(request: OrderCreateRequest):
    """Creates a new customer order with a unique tracking reference (UDYAM-ORD-YYYY-XXXXXXXX)."""
    try:
        return order_service.create_order(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Order creation failed: {str(e)}",
        )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Retrieve order by internal order ID",
)
def get_order_by_id(
    order_id: str = Path(..., description="Internal order identifier (e.g. ord_...)")
):
    """Retrieves full order state, customer details, product list, and pricing."""
    order = order_service.get_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found.",
        )
    return order


@router.get(
    "/{order_id}/timeline",
    response_model=OrderTimelineResponse,
    summary="Retrieve milestone timeline for an order",
)
def get_order_timeline(
    order_id: str = Path(..., description="Internal order identifier")
):
    """Retrieves all milestone events and simulation flags for an order."""
    timeline = order_service.get_timeline(order_id)
    if not timeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found.",
        )
    return timeline


@router.get(
    "/track/{order_reference}",
    response_model=OrderResponse,
    summary="Public order tracking by customer reference",
    description="Allows MSME customers to check real-time order and activation progress using their tracking reference.",
)
def track_order_by_reference(
    order_reference: str = Path(
        ..., description="Customer-facing tracking reference (e.g. UDYAM-ORD-2026-A1B2C3D4)"
    )
):
    """Public lookup endpoint for customer order tracking."""
    order = order_service.get_order_by_reference(order_reference)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No order found matching reference '{order_reference}'. Please verify your reference number.",
        )
    return order


@router.post(
    "/{order_id}/advance",
    response_model=OrderResponse,
    summary="Advance order lifecycle state (simulation & workflow transition)",
    description="Advances order through verified state machine. Simulated telecom stages are clearly flagged.",
)
def advance_order_state(
    order_id: str = Path(..., description="Internal order identifier"),
    request: OrderAdvanceRequest = OrderAdvanceRequest(),
):
    """Transitions the order to its next state or target state, subject to state machine validity."""
    try:
        return order_service.advance_order_state(
            order_id=order_id,
            target_state=request.target_state,
            notes=request.notes,
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found.",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

