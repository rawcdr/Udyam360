"""Secure local storage service for KYC document files."""

import io
import os
import re
import uuid
from pathlib import Path
from typing import Optional, Set, Tuple
from PIL import Image

from app.core.config import settings


# Supported magic bytes for deep content sniffing
MAGIC_NUMBERS = {
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
    "application/pdf": b"%PDF",
}


class KYCStorageService:
    """Manages secure on-disk storage and isolation of uploaded KYC documents."""

    def __init__(self, base_storage_dir: Optional[Path] = None):
        self.storage_dir = (base_storage_dir or settings.KYC_STORAGE_DIR).resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        # Store index mapping document_id to internal path: {doc_id: Path}
        self._doc_index: dict = {}

    def sanitize_filename(self, filename: str) -> str:
        """Strip directory paths and unsafe characters from filenames."""
        # Strip path traversal elements
        base = os.path.basename(filename)
        # Keep only alphanumeric, dash, underscore, and dot
        clean = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", base)
        return clean.strip("._") or "unnamed_document"

    def validate_file(
        self,
        filename: str,
        data: bytes,
        declared_mime: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """Validate file size, extension, and binary magic signatures.

        Returns:
            (is_valid, detected_mime, error_message)
        """
        # 1. Size Check
        if not data:
            return False, "", "File is empty (0 bytes)."
        if len(data) > settings.KYC_MAX_FILE_SIZE_BYTES:
            max_mb = settings.KYC_MAX_FILE_SIZE_BYTES / (1024 * 1024)
            return False, "", f"File size exceeds maximum permitted limit of {max_mb:.1f} MB."

        # 2. Extension Check
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in settings.KYC_ALLOWED_EXTENSIONS:
            return False, "", f"Unsupported file extension '.{ext}'. Allowed: {settings.KYC_ALLOWED_EXTENSIONS}"

        # 3. Magic Number Validation
        detected_mime = ""
        for mime, magic in MAGIC_NUMBERS.items():
            if data.startswith(magic):
                detected_mime = mime
                break

        if not detected_mime:
            # Check secondary JPEG format
            if len(data) > 3 and data[0:2] == b"\xff\xd8":
                detected_mime = "image/jpeg"

        if not detected_mime:
            return False, "", "File binary content does not match allowed types (PNG, JPEG, PDF)."

        # 4. Integrity check for image formats via Pillow
        if detected_mime in ("image/png", "image/jpeg"):
            try:
                img = Image.open(io.BytesIO(data))
                img.verify()  # Verifies file integrity without full decoding
            except Exception as e:
                return False, "", f"Corrupted or invalid image file: {str(e)}"

        return True, detected_mime, ""

    def save_document(
        self,
        case_id: str,
        original_filename: str,
        data: bytes,
        mime_type: str
    ) -> Tuple[str, Path]:
        """Store an uploaded document securely under the case's private directory.

        Returns:
            (document_id, internal_file_path)
        """
        document_id = f"DOC-{uuid.uuid4().hex[:12].upper()}"
        ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else "bin"

        # Dedicated isolated folder per case to prevent cross-case contamination
        case_dir = (self.storage_dir / case_id).resolve()
        case_dir.mkdir(parents=True, exist_ok=True)

        # Generate internal UUID filename to discard user-controlled paths
        internal_filename = f"{document_id}.{ext}"
        internal_path = (case_dir / internal_filename).resolve()

        # Path traversal guard
        if not str(internal_path).startswith(str(self.storage_dir)):
            raise ValueError("Path traversal attempt detected.")

        with open(internal_path, "wb") as f:
            f.write(data)

        self._doc_index[document_id] = internal_path
        return document_id, internal_path

    def get_document_path(self, document_id: str) -> Optional[Path]:
        """Retrieve the internal Path for a document ID without exposing it via API."""
        return self._doc_index.get(document_id)

    def read_document_bytes(self, document_id: str) -> Optional[bytes]:
        """Read document bytes safely."""
        path = self.get_document_path(document_id)
        if path and path.exists():
            with open(path, "rb") as f:
                return f.read()
        return None

    def delete_case_storage(self, case_id: str) -> int:
        """Safely delete all stored files for a case."""
        case_dir = (self.storage_dir / case_id).resolve()
        deleted_count = 0
        if case_dir.exists() and case_dir.is_dir():
            for child in case_dir.iterdir():
                if child.is_file():
                    # Remove from index
                    doc_id = child.stem
                    self._doc_index.pop(doc_id, None)
                    child.unlink()
                    deleted_count += 1
            case_dir.rmdir()
        return deleted_count


kyc_storage_service = KYCStorageService()

