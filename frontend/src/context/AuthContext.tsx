import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import {
  authApi,
  CustomerProfile,
  AdminProfile,
  OTPRequestResponse,
  CustomerAuthResponse,
  AdminAuthResponse,
} from '../api/auth';

interface AuthContextType {
  customer: CustomerProfile | null;
  admin: AdminProfile | null;
  isLoading: boolean;
  isCustomerAuthenticated: boolean;
  isAdminAuthenticated: boolean;
  requestOtp: (phoneNumber: string) => Promise<OTPRequestResponse>;
  verifyOtp: (phoneNumber: string, otp: string, advisorSessionId?: string) => Promise<CustomerAuthResponse>;
  adminLogin: (username: string, password: string) => Promise<AdminAuthResponse>;
  customerLogout: () => Promise<void>;
  adminLogout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [customer, setCustomer] = useState<CustomerProfile | null>(null);
  const [admin, setAdmin] = useState<AdminProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshAuth = useCallback(async () => {
    setIsLoading(true);
    try {
      const [custProfile, admProfile] = await Promise.allSettled([
        authApi.getCurrentCustomer(),
        authApi.getCurrentAdmin(),
      ]);

      if (custProfile.status === 'fulfilled' && custProfile.value) {
        setCustomer(custProfile.value);
      } else {
        setCustomer(null);
      }

      if (admProfile.status === 'fulfilled' && admProfile.value) {
        setAdmin(admProfile.value);
      } else {
        setAdmin(null);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshAuth();
  }, [refreshAuth]);

  const requestOtp = async (phoneNumber: string): Promise<OTPRequestResponse> => {
    return await authApi.requestOtp(phoneNumber);
  };

  const verifyOtp = async (
    phoneNumber: string,
    otp: string,
    advisorSessionId?: string
  ): Promise<CustomerAuthResponse> => {
    const res = await authApi.verifyOtp(phoneNumber, otp, advisorSessionId);
    setCustomer(res.customer);
    return res;
  };

  const adminLogin = async (username: string, password: string): Promise<AdminAuthResponse> => {
    const res = await authApi.adminLogin(username, password);
    setAdmin(res.admin);
    return res;
  };

  const customerLogout = async (): Promise<void> => {
    try {
      await authApi.logoutCustomer();
    } finally {
      setCustomer(null);
    }
  };

  const adminLogout = async (): Promise<void> => {
    try {
      await authApi.logoutAdmin();
    } finally {
      setAdmin(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        customer,
        admin,
        isLoading,
        isCustomerAuthenticated: !!customer,
        isAdminAuthenticated: !!admin,
        requestOtp,
        verifyOtp,
        adminLogin,
        customerLogout,
        adminLogout,
        refreshAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

