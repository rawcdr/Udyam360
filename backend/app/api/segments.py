"""FastAPI router for Customer Segments endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter
from app.services.segment_service import segment_service

router = APIRouter(prefix="/segments", tags=["Customer Segments"])


@router.get("", summary="Get supported customer segments")
def get_segments() -> List[Dict[str, Any]]:
    """Retrieve supported MSME customer segments, preference mappings, and priority features."""
    return segment_service.get_supported_segments()

