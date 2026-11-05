import { apiClient } from './client';
import {
  KYCCaseResponse,
  ConsentRecord,
  KYCDocumentMetadata,
  KYCValidationResult,
  DocumentType,
} from '../types/kyc';

export const kycApi = {
  createCase: async (payload: {
    advisor_session_id?: string | null;
    selected_product_ids: string[];
    quote_reference?: string | null;
  }): Promise<KYCCaseResponse> => {
    const res = await apiClient.post<KYCCaseResponse>('/kyc/cases', payload);
    return res.data;
  },

  getCase: async (caseId: string): Promise<KYCCaseResponse> => {
    const res = await apiClient.get<KYCCaseResponse>(`/kyc/cases/${caseId}`);
    return res.data;
  },

  recordConsent: async (caseId: string, consentGranted: boolean): Promise<ConsentRecord> => {
    const res = await apiClient.post<ConsentRecord>(`/kyc/cases/${caseId}/consent`, {
      consent_granted: consentGranted,
      consent_version: 'v1.0-Airtel-Udyam360-Prototype',
    });
    return res.data;
  },

  uploadDocument: async (
    caseId: string,
    documentType: DocumentType,
    file: File
  ): Promise<KYCDocumentMetadata> => {
    const formData = new FormData();
    formData.append('document_type', documentType);
    formData.append('file', file);

    const res = await apiClient.post<KYCDocumentMetadata>(
      `/kyc/cases/${caseId}/documents`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return res.data;
  },

  listDocuments: async (caseId: string): Promise<KYCDocumentMetadata[]> => {
    const res = await apiClient.get<KYCDocumentMetadata[]>(`/kyc/cases/${caseId}/documents`);
    return res.data;
  },

  processKYC: async (caseId: string): Promise<KYCValidationResult> => {
    const res = await apiClient.post<KYCValidationResult>(`/kyc/cases/${caseId}/process`);
    return res.data;
  },

  getStatus: async (caseId: string): Promise<any> => {
    const res = await apiClient.get(`/kyc/cases/${caseId}/status`);
    return res.data;
  },

  getValidationDetails: async (caseId: string): Promise<KYCValidationResult> => {
    const res = await apiClient.get<KYCValidationResult>(`/kyc/cases/${caseId}/validation`);
    return res.data;
  },
};

