import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { CustomerAuthModal } from '../components/auth/CustomerAuthModal';
import { AdminLoginPage } from '../pages/admin/AdminLoginPage';
import { authApi } from '../api/auth';

// Mock auth API
vi.mock('../api/auth', () => ({
  authApi: {
    requestOtp: vi.fn(),
    verifyOtp: vi.fn(),
    adminLogin: vi.fn(),
    getCurrentCustomer: vi.fn().mockResolvedValue(null),
    getCurrentAdmin: vi.fn().mockResolvedValue(null),
    logoutCustomer: vi.fn().mockResolvedValue(undefined),
    logoutAdmin: vi.fn().mockResolvedValue(undefined),
  },
}));

describe('Phase 7 Frontend Security Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('CustomerAuthModal', () => {
    it('renders phone input and submits valid mobile number', async () => {
      (authApi.requestOtp as any).mockResolvedValueOnce({
        status: 'OTP_SENT',
        phone_number: '+91******3210',
        cooldown_seconds: 60,
        expires_in_seconds: 300,
        demo_otp_hint: '123456',
      });

      render(
        <AuthProvider>
          <CustomerAuthModal
            isOpen={true}
            onClose={() => {}}
            onSuccess={() => {}}
          />
        </AuthProvider>
      );

      expect(screen.getByText(/Verify Mobile Number/i)).toBeInTheDocument();
      const phoneInput = screen.getByPlaceholderText('9876543210');
      fireEvent.change(phoneInput, { target: { value: '9876543210' } });

      const submitBtn = screen.getByText('Send Verification Code');
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(authApi.requestOtp).toHaveBeenCalledWith('+919876543210');
      });

      // Transitions to OTP step
      await waitFor(() => {
        expect(screen.getByText(/Enter 6-Digit Code/i)).toBeInTheDocument();
        expect(screen.getByText('123456')).toBeInTheDocument();
      });
    });

    it('verifies 6-digit OTP and triggers onSuccess callback', async () => {
      (authApi.requestOtp as any).mockResolvedValueOnce({
        status: 'OTP_SENT',
        phone_number: '+91******3210',
        cooldown_seconds: 60,
        expires_in_seconds: 300,
        demo_otp_hint: '654321',
      });

      (authApi.verifyOtp as any).mockResolvedValueOnce({
        status: 'AUTHENTICATED',
        customer: {
          customer_id: 'CUST-123',
          phone_number: '+91******3210',
          is_active: true,
          created_at: '2026-07-15T10:00:00Z',
        },
        session_id: 'sess_123',
        session_token: 'token.123.sig',
        csrf_token: 'csrf_123',
        message: 'Success',
      });

      const handleSuccess = vi.fn();

      render(
        <AuthProvider>
          <CustomerAuthModal
            isOpen={true}
            onClose={() => {}}
            onSuccess={handleSuccess}
          />
        </AuthProvider>
      );

      // Step 1: Phone
      const phoneInput = screen.getByPlaceholderText('9876543210');
      fireEvent.change(phoneInput, { target: { value: '9876543210' } });
      fireEvent.click(screen.getByText('Send Verification Code'));

      // Step 2: OTP
      await waitFor(() => {
        expect(screen.getByPlaceholderText('123456')).toBeInTheDocument();
      });

      const otpInput = screen.getByPlaceholderText('123456');
      fireEvent.change(otpInput, { target: { value: '654321' } });
      fireEvent.click(screen.getByText('Verify & Proceed'));

      await waitFor(() => {
        expect(authApi.verifyOtp).toHaveBeenCalledWith('+919876543210', '654321', undefined);
        expect(handleSuccess).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('AdminLoginPage', () => {
    it('renders admin login form and autofills demo credentials', async () => {
      render(
        <AuthProvider>
          <BrowserRouter>
            <AdminLoginPage />
          </BrowserRouter>
        </AuthProvider>
      );

      expect(screen.getByText(/Airtel Executive Admin/i)).toBeInTheDocument();
      const autofillBtn = screen.getByText('Autofill');
      fireEvent.click(autofillBtn);

      const usernameInput = screen.getByPlaceholderText('admin') as HTMLInputElement;
      const passwordInput = screen.getByPlaceholderText('••••••••••••') as HTMLInputElement;

      expect(usernameInput.value).toBe('admin');
      expect(passwordInput.value).toBe('ExecutiveAdmin2026!');
    });
  });
});

