"""FastAPI router for Order Management, State Progression, and Status Tracking."""

from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Path, Request, Response, status

from app.core.rate_limiter import rate_limiter
from app.core.security import (
    extract_session_token,
    is_admin_caller,
    require_order_access,
    resolve_or_create_session,
    security_manager,
)
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
def create_order(
    request: OrderCreateRequest,
    response: Response,
    session_token: Optional[str] = Depends(extract_session_token),
):
    """Creates a new customer order with a unique tracking reference (UDYAM-ORD-YYYY-XXXXXXXX)."""
    try:
        order_resp = order_service.create_order(request)
        sid, token = resolve_or_create_session(token=session_token, preferred_id=request.advisor_session_id)
        security_manager.bind_order(sid, order_resp.order_id, order_resp.order_reference)
        order_resp.session_token = token
        response.headers["X-Session-Token"] = token
        return order_resp
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
    order_id: str = Path(..., description="Internal order identifier (e.g. ord_...)"),
    _: str = Depends(require_order_access),
):
    """Retrieves full order state, customer details, product list, and pricing for authenticated owner."""
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
    order_id: str = Path(..., description="Internal order identifier"),
    _: str = Depends(require_order_access),
):
    """Retrieves all milestone events and simulation flags for an order for authenticated owner."""
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
    request: Request,
    order_reference: str = Path(
        ..., description="Customer-facing tracking reference (e.g. UDYAM-ORD-2026-A1B2C3D4)"
    ),
    session_token: Optional[str] = Depends(extract_session_token),
    x_admin_role: Optional[str] = Header(None, alias="X-Admin-Role"),
):
    """Public lookup endpoint for customer order tracking. Masks PII for unauthenticated public callers."""
    # 1. Enforce rate limiting: 30 requests per minute per IP for public tracking lookups
    client_ip = request.client.host if request.client else "127.0.0.1"
    allowed, retry_after = rate_limiter.check_and_record(f"track_ip:{client_ip}", 30, 60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Tracking rate limit exceeded. Please wait {retry_after} seconds before trying again.",
        )

    # 2. Check caller authentication
    is_admin = is_admin_caller(x_admin_role)
    is_owner = False
    if session_token:
        sid = security_manager.verify_token(session_token)
        if sid and security_manager.owns_order(sid, order_reference):
            is_owner = True

    sanitize_pii = not (is_admin or is_owner)
    order = order_service.get_order_by_reference(order_reference, sanitize_pii=sanitize_pii)
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
    _: str = Depends(require_order_access),
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

