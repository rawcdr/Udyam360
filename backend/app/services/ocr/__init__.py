"""OCR abstraction package for Udyam360 Smart KYC."""

from .base import BaseOCRProvider, OCRResult, OCRTextLine
from .preprocessing import preprocess_document_image
from .provider import get_ocr_provider

__all__ = [
    "BaseOCRProvider",
    "OCRResult",
    "OCRTextLine",
    "preprocess_document_image",
    "get_ocr_provider",
]

