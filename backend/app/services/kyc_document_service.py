"""Document management service tracking KYC document metadata and storage integration."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas.kyc import DocumentType, ExtractedDocumentFields, KYCDocumentMetadata
from app.services.kyc_storage_service import kyc_storage_service


class KYCDocumentService:
    """Manages document uploads, validation, and lifecycle metadata."""

    def __init__(self):
        # document_id -> KYCDocumentMetadata
        self._documents: Dict[str, KYCDocumentMetadata] = {}
        # case_id -> List[document_id]
        self._case_index: Dict[str, List[str]] = {}

    def upload_document(
        self,
        case_id: str,
        document_type: DocumentType,
        original_filename: str,
        file_bytes: bytes,
        declared_mime: Optional[str] = None
    ) -> KYCDocumentMetadata:
        """Validate and store an uploaded document, recording its metadata."""
        # 1. Security & Format Validation
        sanitized_name = kyc_storage_service.sanitize_filename(original_filename)
        is_valid, mime_type, error_msg = kyc_storage_service.validate_file(
            filename=sanitized_name,
            data=file_bytes,
            declared_mime=declared_mime
        )
        if not is_valid:
            raise ValueError(f"Document validation failed: {error_msg}")

        # 2. Store safely on disk
        doc_id, internal_path = kyc_storage_service.save_document(
            case_id=case_id,
            original_filename=sanitized_name,
            data=file_bytes,
            mime_type=mime_type
        )

        # 3. Create metadata record
        now_iso = datetime.now(timezone.utc).isoformat()
        metadata = KYCDocumentMetadata(
            document_id=doc_id,
            kyc_case_id=case_id,
            document_type=document_type,
            original_filename=sanitized_name,
            file_size_bytes=len(file_bytes),
            mime_type=mime_type,
            uploaded_at=now_iso,
            is_processed=False
        )

        self._documents[doc_id] = metadata
        if case_id not in self._case_index:
            self._case_index[case_id] = []
        self._case_index[case_id].append(doc_id)

        return metadata

    def get_document_metadata(self, document_id: str) -> Optional[KYCDocumentMetadata]:
        """Retrieve metadata for a specific document ID."""
        return self._documents.get(document_id)

    def list_documents(self, case_id: str) -> List[KYCDocumentMetadata]:
        """List all uploaded document metadata for a given KYC case."""
        doc_ids = self._case_index.get(case_id, [])
        return [self._documents[did] for did in doc_ids if did in self._documents]

    def update_extracted_fields(
        self,
        document_id: str,
        fields: ExtractedDocumentFields
    ) -> Optional[KYCDocumentMetadata]:
        """Attach OCR extraction results to document metadata."""
        doc = self._documents.get(document_id)
        if doc:
            doc.extracted_fields = fields
            doc.is_processed = True
        return doc

    def delete_case_documents(self, case_id: str) -> int:
        """Delete all document records and disk files for a KYC case."""
        doc_ids = self._case_index.pop(case_id, [])
        for did in doc_ids:
            self._documents.pop(did, None)
        return kyc_storage_service.delete_case_storage(case_id)


kyc_document_service = KYCDocumentService()

