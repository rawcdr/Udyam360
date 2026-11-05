# Udyam360: Phase 3 Specimen OCR Dataset Evaluation

- **Evaluated Documents:** 47 PNG images across applicants K01–K12
- **Active OCR Engine:** WindowsMediaOCR
- **Average Duration:** 193.80 ms per document
- **Average Confidence:** 0.9298
- **Success Rate:** 100.0%
- **Planted / Flagged Cases Requiring Review:** 12

## Document-by-Document Evaluation Results

| File Name | Applicant | Document Type | Latency (ms) | OCR Conf | Extracted Identifier | Extracted Business Name | Registry Match Status | Requires Review | Warnings |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `K01_address_proof.png` | K01 | ADDRESS_PROOF | 228.9 | 0.95 | `N/A` | Supply address | **N/A** | No | None |
| `K01_gst_certificate.png` | K01 | GST_CERTIFICATE | 146.2 | 0.95 | `N/A` | Vindhya Tours & Travels | **N/A** | YES | GSTIN registration number could not be reliably extracted from certificate. |
| `K01_signatory_id.png` | K01 | SIGNATORY_ID | 77.3 | 0.95 | `N/A` | Vindhya Tours & Travels | **N/A** | No | None |
| `K01_udyam_certificate.png` | K01 | UDYAM_CERTIFICATE | 156.8 | 0.95 | `N/A` | Majo activity | **N/A** | YES | Udyam registration number could not be found or extracted. |
| `K02_address_proof.png` | K02 | ADDRESS_PROOF | 147.2 | 0.95 | `N/A` | Supply address | **N/A** | No | None |
| `K02_gst_certificate.png` | K02 | GST_CERTIFICATE | 307.4 | 0.95 | `N/A` | Harmony Dental Care | **N/A** | YES | GSTIN registration number could not be reliably extracted from certificate. |
| `K02_signatory_id.png` | K02 | SIGNATORY_ID | 93.5 | 0.95 | `N/A` | Harmony Dental Care | **N/A** | No | None |
| `K02_udyam_certificate.png` | K02 | UDYAM_CERTIFICATE | 183.9 | 0.95 | `UDYAM-WB-00-5053330` | Majo activity | **Small** | No | None |
| `K03_address_proof.png` | K03 | ADDRESS_PROOF | 254.5 | 0.95 | `N/A` | Supply address | **N/A** | No | None |
| `K03_gst_certificate.png` | K03 | GST_CERTIFICATE | 212.0 | 0.95 | `N/A` | Ganesh Woodcraft | **N/A** | YES | GSTIN registration number could not be reliably extracted from certificate. |
| `K03_signatory_id.png` | K03 | SIGNATORY_ID | 109.7 | 0.95 | `N/A` | Ganesh Woodcraft | **N/A** | No | None |
| `K03_udyam_certificate.png` | K03 | UDYAM_CERTIFICATE | 234.4 | 0.95 | `UDYAM-MH-00-9516696` | Majo activity | **Micro** | No | None |
| `K04_address_proof.png` | K04 | ADDRESS_PROOF | 203.1 | 0.95 | `N/A` | Supply address | **N/A** | No | None |
| `K04_gst_certificate.png` | K04 | GST_CERTIFICATE | 252.7 | 0.0 | `N/A` | N/A | **N/A** | YES | Low OCR confidence (0.00 < 0.6). Manual review recommended.; GSTIN registration number could not be reliably extracted from certificate. |
| `K04_signatory_id.png` | K04 | SIGNATORY_ID | 68.1 | 0.95 | `N/A` | Saffron Dental Care LLP | **N/A** | No | None |
| `K04_udyam_certificate.png` | K04 | UDYAM_CERTIFICATE | 128.4 | 0.95 | `UDYAM-MH-00-6131836` | Majo activity | **Micro** | No | None |
| `K05_address_proof.png` | K05 | ADDRESS_PROOF | 131.6 | 0.95 | `N/A` | Supply address | **N/A** | No | None |
| `K05_gst_certificate.png` | K05 | GST_CERTIFICATE | 130.9 | 0.95 | `N/A` | onstitution | **N/A** | YES | GSTIN registration number could not be reliably extracted from certificate. |
| `K05_signatory_id.png` | K05 | SIGNATORY_ID | 77.9 | 0.95 | `N/A` | Balaji Realty LLP | **N/A** | No | None |
| `K06_address_proof.png` | K06 | ADDRESS_PROOF | 135.2 | 0.95 | `N/A` | Supply address | **N/A** | No | None |
| `K06_gst_certificate.png` | K06 | GST_CERTIFICATE | 146.1 | 0.95 | `08YKZXS8189L1ZO` | Saffron Unisex Salon | **NOT_FOUND** | YES | None |
| `K06_signatory_id.png` | K06 | SIGNATORY_ID | 69.4 | 0.95 | `N/A` | Saffron Unisex Salon | **N/A** | No | None |
| `K06_udyam_certificate.png` | K06 | UDYAM_CERTIFICATE | 129.6 | 0.95 | `UDYAM-RJ-00-6577157` | Majo activity | **Micro** | No | None |
| `K07_address_proof.png` | K07 | ADDRESS_PROOF | 125.5 | 0.95 | `N/A` | Supply address | **N/A** | No | None |
| `K07_gst_certificate.png` | K07 | GST_CERTIFICATE | 133.1 | 0.95 | `07CPCXN0398P1ZT` | Shri Physio Clinic | **Active** | No | None |
| `K07_signatory_id.png` | K07 | SIGNATORY_ID | 63.7 | 0.95 | `N/A` | Neelgiri Physio Clinic | **N/A** | No | None |
| `K07_udyam_certificate.png` | K07 | UDYAM_CERTIFICATE | 139.4 | 0.95 | `UDYAM-DL-00-9565547` | Majo activity | **Small** | No | None |
| `K08_address_proof.png` | K08 | ADDRESS_PROOF | 125.7 | 0.95 | `N/A` | Supply address | **N/A** | No | None |
| `K08_gst_certificate.png` | K08 | GST_CERTIFICATE | 189.3 | 0.95 | `N/A` | Green Leaf Legal Associates | **N/A** | YES | GSTIN registration number could not be reliably extracted from certificate. |
| `K08_signatory_id.png` | K08 | SIGNATORY_ID | 90.9 | 0.95 | `N/A` | Green Leaf Legal Associates | **N/A** | No | None |
| `K08_udyam_certificate.png` | K08 | UDYAM_CERTIFICATE | 144.1 | 0.95 | `UDYAM-GJ-00-8477445` | Majo activity | **Small** | No | None |
| `K09_address_proof.png` | K09 | ADDRESS_PROOF | 128.3 | 0.95 | `N/A` | Supply address | **N/A** | No | None |
| `K09_gst_certificate.png` | K09 | GST_CERTIFICATE | 129.7 | 0.95 | `N/A` | Kaveri Insurance Advisors | **N/A** | YES | GSTIN registration number could not be reliably extracted from certificate. |
| `K09_signatory_id.png` | K09 | SIGNATORY_ID | 66.0 | 0.95 | `N/A` | Kaveri Insurance Advisors | **N/A** | No | None |
| `K09_udyam_certificate.png` | K09 | UDYAM_CERTIFICATE | 166.7 | 0.95 | `UDYAM-AP-00-9751562` | Majo activity | **Micro** | No | None |
| `K10_address_proof.png` | K10 | ADDRESS_PROOF | 139.7 | 0.95 | `N/A` | Supply address | **N/A** | No | None |
| `K10_gst_certificate.png` | K10 | GST_CERTIFICATE | 164.6 | 0.95 | `N/A` | onstitution | **N/A** | YES | GSTIN registration number could not be reliably extracted from certificate. |
| `K10_signatory_id.png` | K10 | SIGNATORY_ID | 132.4 | 0.95 | `N/A` | Kaveri Stays LLP | **N/A** | No | None |
| `K10_udyam_certificate.png` | K10 | UDYAM_CERTIFICATE | 583.8 | 0.95 | `UDYAM-MH-00-7183141` | Majo activity | **Small** | No | None |
| `K11_address_proof.png` | K11 | ADDRESS_PROOF | 336.1 | 0.95 | `N/A` | Supply address | **N/A** | No | None |
| `K11_gst_certificate.png` | K11 | GST_CERTIFICATE | 438.1 | 0.95 | `03KGZXT1320R1ZZ` | onstitution | **Active** | No | None |
| `K11_signatory_id.png` | K11 | SIGNATORY_ID | 139.0 | 0.95 | `N/A` | Trinity Bake House Pvt Ltd | **N/A** | No | None |
| `K11_udyam_certificate.png` | K11 | UDYAM_CERTIFICATE | 244.8 | 0.95 | `N/A` | Majo activity | **N/A** | YES | Udyam registration number could not be found or extracted. |
| `K12_address_proof.png` | K12 | ADDRESS_PROOF | 347.8 | 0.95 | `N/A` | Supply address | **N/A** | No | None |
| `K12_gst_certificate.png` | K12 | GST_CERTIFICATE | 879.8 | 0.95 | `N/A` | Star Electronics | **N/A** | YES | GSTIN registration number could not be reliably extracted from certificate. |
| `K12_signatory_id.png` | K12 | SIGNATORY_ID | 233.4 | 0.95 | `N/A` | Star Electronics | **N/A** | No | None |
| `K12_udyam_certificate.png` | K12 | UDYAM_CERTIFICATE | 341.3 | 0.95 | `UDYAM-AP-00-5186772` | Majo activity | **Micro** | No | None |
