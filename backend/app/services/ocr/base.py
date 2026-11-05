"""Abstract base class and data structures for OCR providers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class OCRTextLine(BaseModel):
    """Single line of text extracted by OCR with coordinates and confidence."""
    text: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    bounding_box: Optional[List[List[float]]] = None


class OCRResult(BaseModel):
    """Normalized OCR extraction result."""
    raw_text: str
    lines: List[OCRTextLine] = Field(default_factory=list)
    average_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    processing_duration_ms: float = 0.0
    provider_name: str = "Unknown"
    image_width: int = 0
    image_height: int = 0
    warnings: List[str] = Field(default_factory=list)


class BaseOCRProvider(ABC):
    """Abstract interface for local OCR engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the OCR provider."""
        pass

    @abstractmethod
    async def extract_text(
        self,
        image_input: Union[bytes, str, Path],
        preprocess: bool = True,
        document_type: Optional[Any] = None
    ) -> OCRResult:
        """Extract text from an image (bytes, file path or Path object).

        Args:
            image_input: Image file path or raw bytes.
            preprocess: Whether to apply image preprocessing prior to OCR.
            document_type: Optional document type hint (e.g. DocumentType.GST_CERTIFICATE).

        Returns:
            Structured OCRResult containing extracted text and metadata.
        """
        pass
