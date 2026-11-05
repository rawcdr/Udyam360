"""Standalone benchmark script evaluating local OCR and field extraction on the 47 specimen documents."""

import asyncio
import glob
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.schemas.kyc import DocumentType
from app.services.kyc_extraction_service import kyc_extraction_service
from app.services.ocr import get_ocr_provider
from app.services.registry_verification_service import registry_verification_service


async def evaluate():
    doc_dir = BASE_DIR / "YTL_TrackA_Udyam_Digital_Data" / "kyc_documents"
    files = sorted(glob.glob(str(doc_dir / "*.png")))
    total_files = len(files)

    print("=" * 80)
    print(f"UDYAM360 SMART KYC: OCR SPECIMEN DATASET BENCHMARK")
    print(f"Dataset Location: {doc_dir}")
    print(f"Total Specimen Documents: {total_files}")
    print("=" * 80)

    provider = get_ocr_provider()
    print(f"Active OCR Engine: {provider.name}\n")

    results: List[Dict[str, Any]] = []
    durations: List[float] = []
    confidences: List[float] = []
    success_count = 0
    failure_count = 0
    manual_review_count = 0

    # Type detection helper from filename
    def infer_doc_type(filename: str) -> DocumentType:
        if "gst_certificate" in filename:
            return DocumentType.GST_CERTIFICATE
        if "udyam_certificate" in filename:
            return DocumentType.UDYAM_CERTIFICATE
        if "address_proof" in filename:
            return DocumentType.ADDRESS_PROOF
        if "signatory_id" in filename:
            return DocumentType.SIGNATORY_ID
        return DocumentType.OTHER

    for idx, f in enumerate(files, 1):
        filename = os.path.basename(f)
        applicant_id = filename.split("_")[0]
        doc_type = infer_doc_type(filename)

        t0 = time.perf_counter()
        try:
            fields, ocr_res = await kyc_extraction_service.extract_document_fields(f, doc_type)
            dt_ms = (time.perf_counter() - t0) * 1000.0
            durations.append(dt_ms)
            confidences.append(ocr_res.average_confidence)
            success_count += 1

            # Registry cross-verification
            reg_status = "N/A"
            reg_found = False
            if doc_type == DocumentType.GST_CERTIFICATE and fields.gstin:
                gst_chk = registry_verification_service.verify_gstin(fields.gstin)
                reg_found = gst_chk.found
                reg_status = gst_chk.status or "NOT_FOUND"
            elif doc_type == DocumentType.UDYAM_CERTIFICATE and fields.udyam_registration_number:
                udyam_chk = registry_verification_service.verify_udyam(fields.udyam_registration_number)
                reg_found = udyam_chk.found
                reg_status = udyam_chk.status or "NOT_FOUND"

            needs_review = ocr_res.average_confidence < 0.60 or len(fields.warnings) > 0 or reg_status in ("Cancelled", "Suspended", "NOT_FOUND")
            if needs_review:
                manual_review_count += 1

            record = {
                "file": filename,
                "applicant": applicant_id,
                "doc_type": doc_type.value,
                "latency_ms": round(dt_ms, 1),
                "confidence": round(ocr_res.average_confidence, 2),
                "extracted_id": fields.gstin or fields.udyam_registration_number or "N/A",
                "extracted_name": fields.trade_name or fields.legal_business_name or fields.signatory_name or "N/A",
                "registry_status": reg_status,
                "needs_review": needs_review,
                "warnings": "; ".join(fields.warnings) if fields.warnings else "None"
            }
            results.append(record)

            print(f"[{idx:02d}/{total_files:02d}] {filename:<28} | {dt_ms:>6.1f}ms | Conf: {ocr_res.average_confidence:.2f} | Status: {reg_status:<9} | ID: {record['extracted_id']}")

        except Exception as e:
            failure_count += 1
            print(f"[{idx:02d}/{total_files:02d}] {filename:<28} | FAILED: {str(e)}")

    avg_time = sum(durations) / len(durations) if durations else 0.0
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY & BENCHMARK METRICS")
    print("=" * 80)
    print(f"Total Specimen Documents Evaluated: {total_files}")
    print(f"Successful OCR Executions:         {success_count} ({success_count/total_files*100:.1f}%)")
    print(f"Failed OCR Executions:             {failure_count} ({failure_count/total_files*100:.1f}%)")
    print(f"Average Processing Latency:        {avg_time:.2f} ms per document")
    print(f"Average Character Confidence:      {avg_conf:.4f}")
    print(f"Documents Flagged for Review:      {manual_review_count} (due to planted noise, missing IDs, or registry status)")
    print("=" * 80)

    # Save detailed evaluation markdown table
    report_path = BASE_DIR / "docs" / "phase-reports" / "phase_3_ocr_evaluation.md"
    df_eval = pd.DataFrame(results)
    
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("# Udyam360: Phase 3 Specimen OCR Dataset Evaluation\n\n")
        rf.write(f"- **Evaluated Documents:** {total_files} PNG images across applicants K01–K12\n")
        rf.write(f"- **Active OCR Engine:** {provider.name}\n")
        rf.write(f"- **Average Duration:** {avg_time:.2f} ms per document\n")
        rf.write(f"- **Average Confidence:** {avg_conf:.4f}\n")
        rf.write(f"- **Success Rate:** {success_count/total_files*100:.1f}%\n")
        rf.write(f"- **Planted / Flagged Cases Requiring Review:** {manual_review_count}\n\n")
        rf.write("## Document-by-Document Evaluation Results\n\n")
        rf.write("| File Name | Applicant | Document Type | Latency (ms) | OCR Conf | Extracted Identifier | Extracted Business Name | Registry Match Status | Requires Review | Warnings |\n")
        rf.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for r in results:
            rf.write(f"| `{r['file']}` | {r['applicant']} | {r['doc_type']} | {r['latency_ms']} | {r['confidence']} | `{r['extracted_id']}` | {r['extracted_name']} | **{r['registry_status']}** | {'YES' if r['needs_review'] else 'No'} | {r['warnings']} |\n")

    print(f"\n[REPORT GENERATED] Saved full evaluation report to: {report_path}")


if __name__ == "__main__":
    asyncio.run(evaluate())

