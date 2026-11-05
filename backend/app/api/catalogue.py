"""FastAPI router for Product Catalogue endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.schemas.catalogue import Product, CatalogueSummary
from app.services.catalogue_service import catalogue_service

router = APIRouter(prefix="/catalogue", tags=["Product Catalogue"])


@router.get("", response_model=List[Product], summary="Get all catalogue products")
def get_catalogue(category: Optional[str] = Query(None, description="Filter products by category")):
    """Retrieve all 25 commercial products, optionally filtered by category."""
    if category:
        prods = catalogue_service.get_products_by_category(category)
        if not prods:
            raise HTTPException(status_code=404, detail=f"No products found for category '{category}'")
        return prods
    return catalogue_service.get_all_products()


@router.get("/summary", response_model=CatalogueSummary, summary="Get catalogue statistical summary")
def get_catalogue_summary():
    """Retrieve category counts, unit distributions, and price ranges across the catalogue."""
    return catalogue_service.get_catalogue_summary()


@router.get("/{product_id}", response_model=Product, summary="Get individual product by ID")
def get_product(product_id: str):
    """Retrieve single product by its unique product ID (e.g. P01)."""
    prod = catalogue_service.get_product_by_id(product_id)
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product with ID '{product_id}' not found in catalogue.")
    return prod

