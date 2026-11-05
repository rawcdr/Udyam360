"""Security and input validation tests for KYC storage and file uploads (Scenarios 14, 15, 16, 17, 25)."""

import io
from PIL import Image
import pytest
from app.services.kyc_storage_service import KYCStorageService


@pytest.fixture
def storage():
    return KYCStorageService()


def test_scenario_14_corrupted_image_rejected(storage):
    corrupted_bytes = b"\x89PNG\r\n\x1a\n" + b"Corrupted broken image payload..."
    is_valid, mime, error = storage.validate_file("broken.png", corrupted_bytes)
    assert is_valid is False
    assert "Corrupted or invalid image" in error


def test_scenario_15_unsupported_file_format(storage):
    executable_bytes = b"MZ\x90\x00\x03\x00\x00\x00"
    is_valid, mime, error = storage.validate_file("malicious.exe", executable_bytes)
    assert is_valid is False
    assert "Unsupported file extension" in error


def test_scenario_16_oversized_file_upload(storage):
    # 11 MB payload
    huge_payload = b"0" * (11 * 1024 * 1024)
    is_valid, mime, error = storage.validate_file("huge.png", huge_payload)
    assert is_valid is False
    assert "exceeds maximum permitted limit" in error


def test_scenario_17_path_traversal_filename_sanitization(storage):
    malicious_filename = "../../../etc/passwd.png"
    sanitized = storage.sanitize_filename(malicious_filename)
    assert ".." not in sanitized
    assert "/" not in sanitized
    assert "\\" not in sanitized
    assert sanitized.endswith(".png")


def test_scenario_25_two_separate_kyc_cases_isolated(storage):
    # Create valid dummy PNG image bytes
    img = Image.new("RGB", (100, 100), color=(200, 200, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()

    case_a = "KYC-CASE-TENANT-A"
    case_b = "KYC-CASE-TENANT-B"

    doc_a_id, path_a = storage.save_document(case_a, "docA.png", data, "image/png")
    doc_b_id, path_b = storage.save_document(case_b, "docB.png", data, "image/png")

    # Files must reside in completely separate directories
    assert path_a.parent.name == case_a
    assert path_b.parent.name == case_b
    assert path_a != path_b

    # Cleaning case A must not delete case B
    storage.delete_case_storage(case_a)
    assert not path_a.exists()
    assert path_b.exists()

    # Clean case B
    storage.delete_case_storage(case_b)
    assert not path_b.exists()

