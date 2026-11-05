"""Product Catalogue Service for Udyam360.

Loads, validates, normalizes, and provides query interfaces for the 25
commercial products in the Accel Business catalogue without modifying source files.
"""

from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd

from app.core.config import settings
from app.schemas.catalogue import Product, CatalogueSummary


EXPECTED_COLUMNS = [
    "product_id",
    "category",
    "product_name",
    "description",
    "unit",
    "price_min_inr_per_month",
    "price_max_inr_per_month",
    "one_time_setup_inr",
    "min_contract_months",
    "available_city_tiers",
    "min_employees",
    "min_sites",
    "requires_gstin",
    "requires_one_of",
    "typical_install_days",
    "target_segments",
]


class CatalogueService:
    """Manages ingestion, integrity validation, and retrieval of product catalogue data."""

    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = csv_path or settings.PRODUCT_CATALOGUE_PATH
        self._products: Dict[str, Product] = {}
        self._load_and_validate()

    def _load_and_validate(self) -> None:
        """Load CSV, validate schema integrity, check dependencies, and construct Product models."""
        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"Product catalogue file not found at: {self.csv_path}. "
                "Ensure YTL_TrackA_Udyam_Digital_Data is in the project root."
            )

        df = pd.read_csv(self.csv_path)

        # 1. Validate required columns exist
        missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Catalogue CSV missing required columns: {missing_cols}")

        # 2. Check for duplicate product_ids
        duplicate_ids = df[df["product_id"].duplicated()]["product_id"].tolist()
        if duplicate_ids:
            raise ValueError(f"Duplicate product_ids detected in catalogue: {duplicate_ids}")

        products_temp: Dict[str, Product] = {}

        for _, row in df.iterrows():
            p_id = str(row["product_id"]).strip()

            # Parse city tiers (e.g. "1;2" or "1")
            raw_tiers = str(row["available_city_tiers"]).split(";")
            tiers = [int(t.strip()) for t in raw_tiers if t.strip().isdigit()]

            # Parse requires_gstin ('Y' -> True, 'N' -> False)
            raw_gst = str(row["requires_gstin"]).strip().upper()
            requires_gst = (raw_gst == "Y")

            # Parse requires_one_of ('P01|P02' or NaN -> list)
            req_one_of: List[str] = []
            if pd.notna(row["requires_one_of"]) and str(row["requires_one_of"]).strip():
                req_one_of = [
                    dep.strip() for dep in str(row["requires_one_of"]).split("|") if dep.strip()
                ]

            # Parse target segments ('micro;prof' -> list)
            raw_segs = str(row["target_segments"]).split(";")
            target_segs = [s.strip().lower() for s in raw_segs if s.strip()]

            # Price validation
            min_price = int(row["price_min_inr_per_month"])
            max_price = int(row["price_max_inr_per_month"])
            if min_price < 0 or max_price < 0:
                raise ValueError(f"Invalid negative price for product {p_id}")
            if max_price < min_price:
                raise ValueError(
                    f"Product {p_id} has price_max ({max_price}) < price_min ({min_price})"
                )

            product = Product(
                product_id=p_id,
                category=str(row["category"]).strip(),
                product_name=str(row["product_name"]).strip(),
                description=str(row["description"]).strip(),
                unit=str(row["unit"]).strip(),
                price_min_inr_per_month=min_price,
                price_max_inr_per_month=max_price,
                one_time_setup_inr=int(row["one_time_setup_inr"]),
                min_contract_months=int(row["min_contract_months"]),
                available_city_tiers=tiers,
                min_employees=int(row["min_employees"]),
                min_sites=int(row["min_sites"]),
                requires_gstin=requires_gst,
                requires_one_of=req_one_of,
                typical_install_days=int(row["typical_install_days"]),
                target_segments=target_segs,
            )
            products_temp[p_id] = product

        # 3. Validate dependency references (referential integrity & self-reference checks)
        all_ids = set(products_temp.keys())
        for p_id, prod in products_temp.items():
            for dep_id in prod.requires_one_of:
                if dep_id not in all_ids:
                    raise ValueError(
                        f"Product {p_id} requires non-existent product ID '{dep_id}'"
                    )
                if dep_id == p_id:
                    raise ValueError(f"Product {p_id} cannot depend on itself")

        self._products = products_temp

    def get_all_products(self) -> List[Product]:
        """Return list of all 25 catalogue products."""
        return list(self._products.values())

    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """Retrieve a single product by its unique product_id."""
        return self._products.get(product_id.strip())

    def get_products_by_category(self, category: str) -> List[Product]:
        """Filter products by category name (case-insensitive)."""
        target = category.strip().lower()
        return [p for p in self._products.values() if p.category.lower() == target]

    def get_catalogue_summary(self) -> CatalogueSummary:
        """Generate statistical summary of catalogue products."""
        total = len(self._products)
        cats: Dict[str, int] = {}
        units: Dict[str, int] = {}
        target_segs: Dict[str, int] = {}
        gst_count = 0
        min_overall = float("inf")
        max_overall = 0

        for p in self._products.values():
            cats[p.category] = cats.get(p.category, 0) + 1
            units[p.unit] = units.get(p.unit, 0) + 1
            if p.requires_gstin:
                gst_count += 1
            if p.price_min_inr_per_month < min_overall:
                min_overall = p.price_min_inr_per_month
            if p.price_max_inr_per_month > max_overall:
                max_overall = p.price_max_inr_per_month
            for s in p.target_segments:
                target_segs[s] = target_segs.get(s, 0) + 1

        return CatalogueSummary(
            total_products=total,
            categories=cats,
            units=units,
            gstin_required_count=gst_count,
            price_range_overall={"min": int(min_overall), "max": int(max_overall)},
            target_segment_counts=target_segs,
        )


# Singleton instance initialized with default dataset path
catalogue_service = CatalogueService()

