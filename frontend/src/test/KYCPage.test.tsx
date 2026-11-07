import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { KYCPage } from '../pages/KYCPage';
import { OnboardingProvider } from '../context/OnboardingContext';
import { AuthProvider } from '../context/AuthContext';
import { kycApi } from '../api/kyc';

vi.mock('../api/auth', () => ({
  authApi: {
    getCurrentCustomer: vi.fn().mockResolvedValue({
      customer_id: 'CUST-TEST-01',
      phone_number: '+91******3210',
      is_active: true,
      created_at: '2026-11-05T12:00:00Z',
    }),
    getCurrentAdmin: vi.fn().mockResolvedValue(null),
    requestOtp: vi.fn(),
    verifyOtp: vi.fn(),
    logoutCustomer: vi.fn(),
    logoutAdmin: vi.fn(),
  },
}));

vi.mock('../api/kyc', () => ({
  kycApi: {
    createCase: vi.fn(),
    listDocuments: vi.fn(),
    recordConsent: vi.fn(),
    uploadDocument: vi.fn(),
    processKYC: vi.fn(),
    getStatus: vi.fn(),
  },
}));

vi.mock('../api/orders', () => ({
  orderApi: {
    create: vi.fn(),
    advance: vi.fn(),
  },
}));

const mockKYCCase = {
  kyc_case_id: 'KYC-2026-TEST01',
  advisor_session_id: 'conv-test-01',
  quote_reference: 'Q-TEST1234',
  application_status: 'INITIATED',
  required_documents: ['GST_CERTIFICATE', 'ADDRESS_PROOF', 'SIGNATORY_ID'],
  created_at: '2026-11-05T12:00:00Z',
  business_profile: { segment: 'prof' },
};

describe('KYCPage Component & Consent Gate', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (kycApi.createCase as any).mockResolvedValue(mockKYCCase);
    (kycApi.listDocuments as any).mockResolvedValue([]);
  });

  const renderWithProviders = (ui: React.ReactElement) => {
    return render(
      <AuthProvider>
        <OnboardingProvider>
          <BrowserRouter>
            {ui}
          </BrowserRouter>
        </OnboardingProvider>
      </AuthProvider>
    );
  };

  it('enforces explicit consent gate before unlocking document uploads', async () => {
    renderWithProviders(<KYCPage />);

    await waitFor(() => {
      expect(screen.getByText(/Step 1: Data Privacy & Customer Processing Consent/i)).toBeInTheDocument();
    });

    // Checkbox must NOT be pre-checked
    const consentCheckbox = screen.getByRole('checkbox');
    expect(consentCheckbox).not.toBeChecked();

    const grantBtn = screen.getByRole('button', { name: /Grant & Record Consent/i });
    expect(grantBtn).toBeDisabled();

    // Check it
    fireEvent.click(consentCheckbox);
    expect(consentCheckbox).toBeChecked();
    expect(grantBtn).not.toBeDisabled();

    // Grant consent
    (kycApi.recordConsent as any).mockResolvedValue({
      case_id: 'KYC-2026-TEST01',
      consent_granted: true,
      status: 'CONSENT_RECORDED',
    });
    fireEvent.click(grantBtn);

    await waitFor(() => {
      expect(screen.getByText(/Consent Confirmed & Audited/i)).toBeInTheDocument();
    });
  });

  it('renders dynamic required document types returned by backend', async () => {
    renderWithProviders(<KYCPage />);

    await waitFor(() => {
      expect(screen.getByText(/GST_CERTIFICATE/i)).toBeInTheDocument();
      expect(screen.getByText(/ADDRESS_PROOF/i)).toBeInTheDocument();
      expect(screen.getByText(/SIGNATORY_ID/i)).toBeInTheDocument();
    });
  });

  it('accurately displays verification results and pending manual review without marking as rejected', async () => {
    (kycApi.processKYC as any).mockResolvedValue({
      kyc_case_id: 'KYC-2026-TEST01',
      overall_status: 'PENDING_REVIEW',
      checks_passed: [
        { check_name: 'Registry Lookup', passed: true, score: 1.0, details: 'Active in GST registry' },
      ],
      checks_failed: [],
      warnings: ['Name discrepancy score 78% (below 85% auto-approval threshold)'],
      registry_match: true,
      freshness_valid: true,
      manual_review_required: true,
      review_reasons: ['Minor name discrepancy requiring human compliance review'],
      explanation: 'Application queued for administrative compliance review.',
      processed_at: '2026-11-05T12:00:00Z',
    });

    // Grant consent and process
    (kycApi.listDocuments as any).mockResolvedValue([
      {
        document_id: 'doc_1',
        case_id: 'KYC-2026-TEST01',
        document_type: 'GST_CERTIFICATE',
        original_filename: 'gst_cert.png',
        detected_mime: 'image/png',
        sha256_hash: 'abc',
        file_size_bytes: 10240,
        uploaded_at: '2026-11-05T12:00:00Z',
      },
    ]);

    renderWithProviders(<KYCPage />);

    await waitFor(() => {
      expect(screen.getByText(/Step 1: Data Privacy & Customer Processing Consent/i)).toBeInTheDocument();
    });

    const consentCheckbox = screen.getByRole('checkbox');
    fireEvent.click(consentCheckbox);
    (kycApi.recordConsent as any).mockResolvedValue({ case_id: 'KYC-2026-TEST01', consent_granted: true });
    fireEvent.click(screen.getByRole('button', { name: /Grant & Record Consent/i }));

    await waitFor(() => {
      expect(screen.getByText(/Verify Documents & Cross-Check Registries/i)).toBeInTheDocument();
    });

    const verifyBtn = screen.getByRole('button', { name: /Verify Documents & Cross-Check Registries/i });
    fireEvent.click(verifyBtn);

    await waitFor(() => {
      expect(screen.getByText('Verification Outcome Report')).toBeInTheDocument();
      expect(screen.getByText('PENDING_REVIEW')).toBeInTheDocument();
      expect(screen.queryByText('REJECTED')).not.toBeInTheDocument();
    });
  });
});
