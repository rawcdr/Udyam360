"""Unit tests for local OCR provider abstractions, image preprocessing, and mock providers."""

import pytest
from PIL import Image
import io
from app.services.ocr import (
    BaseOCRProvider,
    OCRResult,
    get_ocr_provider,
    preprocess_document_image,
)
from app.services.ocr.local_ocr import MockOCRProvider


def test_mock_ocr_provider_basic():
    provider = MockOCRProvider()
    assert provider.name == "MockOCR"


@pytest.mark.anyio
async def test_mock_ocr_provider_predefined_mapping():
    predefined = {
        "test_doc": "Sample Company Private Limited\nGSTIN: 27AABCT1234F1Z5\nDate: 2026-05-10"
    }
    provider = MockOCRProvider(predefined_results=predefined)
    res = await provider.extract_text("path/to/test_doc.png")

    assert res.provider_name == "MockOCR"
    assert "Sample Company" in res.raw_text
    assert len(res.lines) == 3
    assert res.average_confidence >= 0.95


def test_image_preprocessing():
    # Create simple synthetic test image in memory
    img = Image.new("RGB", (600, 400), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    processed_img, orig_w, orig_h = preprocess_document_image(raw_bytes)
    assert orig_w == 600
    assert orig_h == 400
    assert processed_img.mode == "L"  # Grayscale
    assert processed_img.size[0] >= 1000  # Rescaled for OCR readability


def test_ocr_provider_factory_mock():
    provider = get_ocr_provider("mock")
    assert isinstance(provider, MockOCRProvider)
    assert provider.name == "MockOCR"

