"""Unit tests for Product Catalogue Service."""

import pytest
from pathlib import Path
from app.services.catalogue_service import CatalogueService, catalogue_service


def test_catalogue_loads_all_25_products():
    """Verify all 25 products are loaded from catalogue."""
    products = catalogue_service.get_all_products()
    assert len(products) == 25


def test_product_ids_are_unique():
    """Verify all 25 product IDs are distinct."""
    products = catalogue_service.get_all_products()
    ids = [p.product_id for p in products]
    assert len(ids) == len(set(ids))


def test_required_columns_and_fields():
    """Verify essential attributes on loaded products."""
    for p in catalogue_service.get_all_products():
        assert p.product_id.startswith("P")
        assert len(p.product_name) > 0
        assert p.category in [
            "Connectivity",
            "Communication",
            "Cloud & Productivity",
            "Security",
            "IoT & Physical",
        ]
        assert p.price_min_inr_per_month <= p.price_max_inr_per_month
        assert p.one_time_setup_inr >= 0
        assert p.min_contract_months >= 1
        assert len(p.available_city_tiers) > 0
        assert p.min_employees >= 1
        assert p.min_sites >= 1
        assert isinstance(p.requires_gstin, bool)


def test_get_product_by_id_found_and_not_found():
    """Verify product retrieval by ID."""
    p01 = catalogue_service.get_product_by_id("P01")
    assert p01 is not None
    assert p01.product_name == "Biz Fibre 100"

    non_existent = catalogue_service.get_product_by_id("P99")
    assert non_existent is None


def test_get_products_by_category():
    """Verify filtering by category."""
    conn_prods = catalogue_service.get_products_by_category("Connectivity")
    assert len(conn_prods) == 11

    cloud_prods = catalogue_service.get_products_by_category("Cloud & Productivity")
    assert len(cloud_prods) == 4

    unknown_cat = catalogue_service.get_products_by_category("NonExistentCategory")
    assert len(unknown_cat) == 0


def test_catalogue_summary():
    """Verify catalogue summary statistics."""
    summary = catalogue_service.get_catalogue_summary()
    assert summary.total_products == 25
    assert summary.categories["Connectivity"] == 11
    assert summary.gstin_required_count == 10
    assert summary.price_range_overall["min"] == 99
    assert summary.price_range_overall["max"] == 35000


def test_missing_catalogue_file_handling():
    """Verify graceful FileNotFoundError when CSV does not exist."""
    fake_path = Path("non_existent_dir/catalogue.csv")
    with pytest.raises(FileNotFoundError, match="Product catalogue file not found"):
        CatalogueService(csv_path=fake_path)


def test_invalid_pricing_detected(tmp_path):
    """Verify ValueError when max price is less than min price."""
    bad_csv = tmp_path / "bad_catalogue.csv"
    bad_csv.write_text(
        "product_id,category,product_name,description,unit,price_min_inr_per_month,price_max_inr_per_month,one_time_setup_inr,min_contract_months,available_city_tiers,min_employees,min_sites,requires_gstin,requires_one_of,typical_install_days,target_segments\n"
        "P01,Connectivity,Biz Fibre 100,Desc,per site,1200,900,0,12,1;2,1,1,N,,5,micro\n"
    )
    with pytest.raises(ValueError, match="price_max .* < price_min"):
        CatalogueService(csv_path=bad_csv)

