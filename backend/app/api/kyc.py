"""FastAPI router implementing REST endpoints for Udyam360 Smart KYC."""

from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.schemas.kyc import (
    ConsentRecord,
    ConsentRequest,
    DocumentType,
    KYCCaseCreateRequest,
    KYCCaseResponse,
    KYCDocumentMetadata,
    KYCStatus,
    KYCValidationResult,
)
from app.services.kyc_consent_service import kyc_consent_service
from app.services.kyc_document_service import kyc_document_service
from app.services.kyc_orchestrator import kyc_orchestrator

kyc_router = APIRouter(prefix="/kyc", tags=["Smart KYC & Document Verification"])


@kyc_router.post(
    "/cases",
    response_model=KYCCaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize KYC onboarding application case",
    description="Creates a new KYC application snapshotting validated profile data from an existing advisor session."
)
async def create_kyc_case(request: KYCCaseCreateRequest):
    try:
        case = kyc_orchestrator.create_case(
            advisor_session_id=request.advisor_session_id,
            selected_product_ids=request.selected_product_ids,
            quote_reference=request.quote_reference
        )
        return case
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Case creation error: {str(e)}")


@kyc_router.get(
    "/cases/{case_id}",
    response_model=KYCCaseResponse,
    summary="Retrieve KYC application details"
)
async def get_kyc_case(case_id: str):
    case = kyc_orchestrator.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"KYC case '{case_id}' not found.")
    return case


@kyc_router.post(
    "/cases/{case_id}/consent",
    response_model=ConsentRecord,
    summary="Record customer processing consent",
    description="Captures explicit customer consent prior to local OCR processing and mock registry verification."
)
async def record_customer_consent(case_id: str, request: ConsentRequest):
    case = kyc_orchestrator.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"KYC case '{case_id}' not found.")

    record = kyc_consent_service.record_consent(
        case_id=case_id,
        consent_granted=request.consent_granted,
        consent_version=request.consent_version
    )
    return record


@kyc_router.post(
    "/cases/{case_id}/documents",
    response_model=KYCDocumentMetadata,
    status_code=status.HTTP_201_CREATED,
    summary="Upload KYC document",
    description="Uploads a document (PNG, JPEG, PDF) for local secure storage and subsequent OCR extraction."
)
async def upload_kyc_document(
    case_id: str,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...)
):
    case = kyc_orchestrator.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"KYC case '{case_id}' not found.")

    file_bytes = await file.read()
    try:
        metadata = kyc_document_service.upload_document(
            case_id=case_id,
            document_type=document_type,
            original_filename=file.filename or "uploaded_file",
            file_bytes=file_bytes,
            declared_mime=file.content_type
        )
        return metadata
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload error: {str(e)}")


@kyc_router.get(
    "/cases/{case_id}/documents",
    response_model=List[KYCDocumentMetadata],
    summary="List uploaded documents for a case"
)
async def list_kyc_documents(case_id: str):
    case = kyc_orchestrator.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"KYC case '{case_id}' not found.")
    return kyc_document_service.list_documents(case_id)


@kyc_router.post(
    "/cases/{case_id}/process",
    response_model=KYCValidationResult,
    summary="Execute KYC verification pipeline",
    description="Executes local OCR, field extraction, mock registry lookup, and cross-document verification."
)
async def process_kyc_case(case_id: str):
    case = kyc_orchestrator.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"KYC case '{case_id}' not found.")

    try:
        result = await kyc_orchestrator.process_kyc(case_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Processing error: {str(e)}")


@kyc_router.get(
    "/cases/{case_id}/status",
    summary="Get high-level KYC status"
)
async def get_kyc_status(case_id: str):
    case = kyc_orchestrator.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"KYC case '{case_id}' not found.")

    result = kyc_orchestrator.get_validation_result(case_id)
    return {
        "kyc_case_id": case_id,
        "application_status": case.application_status,
        "consent_recorded": kyc_consent_service.is_consent_active(case_id),
        "documents_count": len(kyc_document_service.list_documents(case_id)),
        "manual_review_required": result.manual_review_required if result else False,
        "review_reasons": result.review_reasons if result else [],
        "explanation": result.explanation if result else "Application pending processing."
    }


@kyc_router.get(
    "/cases/{case_id}/validation",
    response_model=KYCValidationResult,
    summary="Get detailed validation report"
)
async def get_validation_details(case_id: str):
    case = kyc_orchestrator.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"KYC case '{case_id}' not found.")

    result = kyc_orchestrator.get_validation_result(case_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation report not yet generated for case '{case_id}'. Run /process first."
        )
    return result


@kyc_router.delete(
    "/cases/{case_id}",
    summary="Delete development KYC case"
)
async def delete_kyc_case(case_id: str):
    success = kyc_orchestrator.delete_case(case_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"KYC case '{case_id}' not found.")
    return {"status": "deleted", "kyc_case_id": case_id}

