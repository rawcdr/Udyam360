import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AdminKYCExceptionsPage } from '../pages/admin/AdminKYCExceptionsPage';
import { adminApi } from '../api/admin';

vi.mock('../api/admin', () => ({
  adminApi: {
    getKYCExceptions: vi.fn(),
    getKYCExceptionDetail: vi.fn(),
    resolveKYCException: vi.fn(),
  },
}));

const mockExceptions = [
  {
    case_id: 'KYC-EXP-9042',
    customer_name: 'Rajesh Kumar Sharma',
    business_name: 'Shree Ganesh Textiles & Garments',
    trade_name: 'Shree Ganesh Textiles',
    legal_name: 'Rajesh Kumar Sharma (Sole Proprietorship)',
    city: 'Surat, Gujarat',
    segment: 'Micro Manufacturing',
    risk_level: 'LOW',
    confidence_score: 91.4,
    flag_reason: 'Trade Name vs. Legal Entity Discrepancy',
    status: 'PENDING_REVIEW',
    created_at: '2026-11-07T12:00:00Z',
    entity_structure: 'Sole Proprietorship under GSTIN 24AAAAA0000A1Z5',
    order_reference: 'UDYAM-ORD-2026-C954DD97',
    cross_checks: [
      {
        check_name: 'PAN vs. Signatory Name',
        status: 'MATCH',
        detail: 'Signatory PAN matches applicant name with 100% confidence.',
      },
    ],
    copilot_analysis: 'Sole Proprietorship archetype detected. Trade name matches GSTIN principal place.',
    copilot_recommendation: 'RECOMMENDED ACTION: APPROVE.',
  },
];

describe('AdminKYCExceptionsPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (adminApi.getKYCExceptions as any).mockResolvedValue(mockExceptions);
  });

  it('renders the exceptions queue and copilot dossier for flagged MSME case', async () => {
    render(
      <BrowserRouter>
        <AdminKYCExceptionsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Exceptions Review Queue')).toBeInTheDocument();
      expect(screen.getAllByText('Shree Ganesh Textiles & Garments').length).toBeGreaterThan(0);
      expect(screen.getByText('Airtel AI KYC Copilot Risk Intelligence')).toBeInTheDocument();
      expect(screen.getByText(/Sole Proprietorship archetype detected/i)).toBeInTheDocument();
    });
  });

  it('allows KYC officer to approve exception and advance order state', async () => {
    (adminApi.resolveKYCException as any).mockResolvedValue({
      case_id: 'KYC-EXP-9042',
      status: 'APPROVED',
      action_taken: 'APPROVE',
      reviewed_by: 'Senior KYC Compliance Officer',
      reviewed_at: '2026-11-07T12:05:00Z',
      notes: 'Approved following cross-check',
      order_reference: 'UDYAM-ORD-2026-C954DD97',
      order_status: 'ORDER_PROCESSING',
    });

    render(
      <BrowserRouter>
        <AdminKYCExceptionsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Approve & Release Order')).toBeInTheDocument();
    });

    const approveButton = screen.getByText('Approve & Release Order');
    fireEvent.click(approveButton);

    await waitFor(() => {
      expect(adminApi.resolveKYCException).toHaveBeenCalledWith(
        'KYC-EXP-9042',
        'APPROVE',
        expect.any(String)
      );
      expect(screen.getByText(/Successfully APPROVE/i)).toBeInTheDocument();
    });
  });
});
