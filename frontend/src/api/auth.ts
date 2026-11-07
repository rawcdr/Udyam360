import { apiClient } from './client';

export interface OTPRequestPayload {
  phone_number: string;
  correlation_id?: string;
}

export interface OTPRequestResponse {
  status: string;
  phone_number: string;
  cooldown_seconds: number;
  expires_in_seconds: number;
  demo_otp_hint?: string;
}

export interface OTPVerifyPayload {
  phone_number: string;
  otp: string;
  advisor_session_id?: string;
}

export interface CustomerProfile {
  customer_id: string;
  phone_number: string;
  business_name?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface CustomerAuthResponse {
  status: string;
  customer: CustomerProfile;
  session_id: string;
  session_token: string;
  csrf_token: string;
  message: string;
}

export interface AdminProfile {
  admin_id: string;
  username: string;
  email?: string | null;
  full_name?: string | null;
  role: string;
  is_active: boolean;
}

export interface AdminAuthResponse {
  status: string;
  admin: AdminProfile;
  session_id: string;
  session_token: string;
  csrf_token: string;
  message: string;
}

export const authApi = {
  // Request OTP
  requestOtp: async (phoneNumber: string): Promise<OTPRequestResponse> => {
    const response = await apiClient.post<OTPRequestResponse>('/auth/otp/request', {
      phone_number: phoneNumber,
    });
    return response.data;
  },

  // Verify OTP
  verifyOtp: async (phoneNumber: string, otp: string, advisorSessionId?: string): Promise<CustomerAuthResponse> => {
    const response = await apiClient.post<CustomerAuthResponse>('/auth/otp/verify', {
      phone_number: phoneNumber,
      otp,
      advisor_session_id: advisorSessionId,
    });
    return response.data;
  },

  // Get current customer profile
  getCurrentCustomer: async (): Promise<CustomerProfile | null> => {
    try {
      const response = await apiClient.get<CustomerProfile>('/auth/customer/me');
      return response.data;
    } catch {
      return null;
    }
  },

  // Customer logout
  logoutCustomer: async (): Promise<void> => {
    await apiClient.post('/auth/customer/logout');
    sessionStorage.removeItem('udyam360_session_token');
  },

  // Admin Login
  adminLogin: async (username: string, password: string): Promise<AdminAuthResponse> => {
    const response = await apiClient.post<AdminAuthResponse>('/auth/admin/login', {
      username,
      password,
    });
    return response.data;
  },

  // Get current admin profile
  getCurrentAdmin: async (): Promise<AdminProfile | null> => {
    try {
      const response = await apiClient.get<AdminProfile>('/auth/admin/me');
      return response.data;
    } catch {
      return null;
    }
  },

  // Admin Logout
  logoutAdmin: async (): Promise<void> => {
    await apiClient.post('/auth/admin/logout');
    sessionStorage.removeItem('udyam360_session_token');
  },

  // Refresh CSRF Token
  getCsrfToken: async (): Promise<string> => {
    const response = await apiClient.get<{ csrf_token: string }>('/auth/csrf');
    return response.data.csrf_token;
  },
};
