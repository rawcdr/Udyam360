"""OCR provider factory and selector."""

import os
import platform
from typing import Optional
from app.core.config import settings
from .base import BaseOCRProvider
from .local_ocr import MockOCRProvider, RapidOCRProvider, WinOCRProvider


_cached_provider: Optional[BaseOCRProvider] = None


def get_ocr_provider(provider_type: Optional[str] = None) -> BaseOCRProvider:
    """Retrieve or instantiate the configured OCR provider.

    Args:
        provider_type: Optional explicit provider override ('winocr', 'rapidocr', 'mock', 'auto').

    Returns:
        Instance of BaseOCRProvider.
    """
    global _cached_provider

    target = provider_type or settings.OCR_PROVIDER or "auto"
    target = target.lower().strip()

    if target == "mock":
        return MockOCRProvider()

    if target == "winocr":
        return WinOCRProvider()

    if target == "rapidocr":
        return RapidOCRProvider()

    # 'auto' strategy: prefer native WinOCR on Windows, else RapidOCR
    if platform.system() == "Windows":
        try:
            import winocr  # Verify availability
            return WinOCRProvider()
        except ImportError:
            pass

    try:
        import rapidocr_onnxruntime
        return RapidOCRProvider()
    except ImportError:
        pass

    # Fallback to mock if no OCR engine is available
    return MockOCRProvider()

