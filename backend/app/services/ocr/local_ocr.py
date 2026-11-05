"""Concrete implementations of local OCR providers."""

import asyncio
import io
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from PIL import Image

from .base import BaseOCRProvider, OCRResult, OCRTextLine
from .preprocessing import load_image, preprocess_document_image


class WinOCRProvider(BaseOCRProvider):
    """Windows native Media OCR provider using Windows 10/11 system OCR engine."""

    def __init__(self, language: str = "en"):
        self.language = language

    @property
    def name(self) -> str:
        return "WindowsMediaOCR"

    async def extract_text(
        self,
        image_input: Union[bytes, str, Path],
        preprocess: bool = True,
        document_type: Optional[Any] = None
    ) -> OCRResult:
        import winocr  # Imported dynamically

        t0 = time.perf_counter()
        warnings: List[str] = []

        try:
            if preprocess:
                pil_img, orig_w, orig_h = preprocess_document_image(image_input)
            else:
                pil_img = load_image(image_input)
                orig_w, orig_h = pil_img.size

            # Run winocr asynchronously
            ocr_res = await winocr.recognize_pil(pil_img, lang=self.language)
            duration_ms = (time.perf_counter() - t0) * 1000.0

            lines: List[OCRTextLine] = []
            for line in ocr_res.lines:
                text_clean = line.text.strip()
                if text_clean:
                    lines.append(OCRTextLine(
                        text=text_clean,
                        confidence=0.95  # Windows Media OCR produces high-confidence text
                    ))

            full_text = "\n".join([line.text for line in lines])
            avg_conf = 0.95 if lines else 0.0

            return OCRResult(
                raw_text=full_text,
                lines=lines,
                average_confidence=avg_conf,
                processing_duration_ms=round(duration_ms, 2),
                provider_name=self.name,
                image_width=orig_w,
                image_height=orig_h,
                warnings=warnings
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - t0) * 1000.0
            return OCRResult(
                raw_text="",
                lines=[],
                average_confidence=0.0,
                processing_duration_ms=round(duration_ms, 2),
                provider_name=self.name,
                warnings=[f"WinOCR extraction failed: {str(e)}"]
            )


class RapidOCRProvider(BaseOCRProvider):
    """Cross-platform CPU OCR provider using ONNX Runtime (PaddleOCR PP-OCRv4)."""

    def __init__(self):
        from rapidocr_onnxruntime import RapidOCR
        self._engine = RapidOCR()

    @property
    def name(self) -> str:
        return "RapidOCR_ONNX"

    async def extract_text(
        self,
        image_input: Union[bytes, str, Path],
        preprocess: bool = True,
        document_type: Optional[Any] = None
    ) -> OCRResult:
        t0 = time.perf_counter()
        warnings: List[str] = []

        try:
            if preprocess:
                pil_img, orig_w, orig_h = preprocess_document_image(image_input)
            else:
                pil_img = load_image(image_input)
                orig_w, orig_h = pil_img.size

            # RapidOCR accepts file path, PIL Image, or numpy array
            # Run in thread pool to avoid blocking async event loop
            loop = asyncio.get_running_loop()
            result, _ = await loop.run_in_executor(None, self._engine, pil_img)

            duration_ms = (time.perf_counter() - t0) * 1000.0

            lines: List[OCRTextLine] = []
            confidences: List[float] = []

            if result:
                for box, text, score in result:
                    clean_txt = str(text).strip()
                    conf = float(score) if score is not None else 0.80
                    if clean_txt:
                        lines.append(OCRTextLine(
                            text=clean_txt,
                            confidence=round(conf, 4),
                            bounding_box=box
                        ))
                        confidences.append(conf)

            full_text = "\n".join([line.text for line in lines])
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

            return OCRResult(
                raw_text=full_text,
                lines=lines,
                average_confidence=round(avg_conf, 4),
                processing_duration_ms=round(duration_ms, 2),
                provider_name=self.name,
                image_width=orig_w,
                image_height=orig_h,
                warnings=warnings
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - t0) * 1000.0
            return OCRResult(
                raw_text="",
                lines=[],
                average_confidence=0.0,
                processing_duration_ms=round(duration_ms, 2),
                provider_name=self.name,
                warnings=[f"RapidOCR extraction failed: {str(e)}"]
            )


class MockOCRProvider(BaseOCRProvider):
    """Deterministic Mock OCR provider for unit tests and offline testing."""

    def __init__(self, predefined_results: Optional[Dict[str, str]] = None):
        self.predefined_results: Dict[str, str] = predefined_results or {}

    @property
    def name(self) -> str:
        return "MockOCR"

    async def extract_text(
        self,
        image_input: Union[bytes, str, Path],
        preprocess: bool = True,
        document_type: Optional[Any] = None
    ) -> OCRResult:
        # 1. Match by document_type (direct, substring, or common aliases)
        if document_type:
            dt_str = getattr(document_type, "value", str(document_type)).lower()
            aliases = {
                "address_proof": ("address", "bill", "utility", "electric"),
                "gst_certificate": ("gst", "gstin"),
                "udyam_certificate": ("udyam", "msme"),
                "signatory_id": ("sign", "signatory", "id"),
            }.get(dt_str, ())

            for pattern, text in self.predefined_results.items():
                p_lower = str(pattern).lower()
                if p_lower in dt_str or dt_str in p_lower or any(a in p_lower for a in aliases):
                    lines = [OCRTextLine(text=l.strip(), confidence=0.98) for l in text.split("\n") if l.strip()]
                    return OCRResult(
                        raw_text=text,
                        lines=lines,
                        average_confidence=0.98,
                        processing_duration_ms=1.5,
                        provider_name=self.name,
                        image_width=1200,
                        image_height=1600
                    )

        # 2. Check if matching key in image_input path/representation
        key = str(image_input)
        for pattern, text in self.predefined_results.items():
            if str(pattern).lower() in key.lower():
                lines = [OCRTextLine(text=l.strip(), confidence=0.98) for l in text.split("\n") if l.strip()]
                return OCRResult(
                    raw_text=text,
                    lines=lines,
                    average_confidence=0.98,
                    processing_duration_ms=1.5,
                    provider_name=self.name,
                    image_width=1200,
                    image_height=1600
                )

        # Default fallback text
        default_text = "Specimen Document\nMock OCR Output"
        lines = [OCRTextLine(text=l, confidence=0.95) for l in default_text.split("\n")]
        return OCRResult(
            raw_text=default_text,
            lines=lines,
            average_confidence=0.95,
            processing_duration_ms=1.0,
            provider_name=self.name,
            image_width=1000,
            image_height=1000
        )
