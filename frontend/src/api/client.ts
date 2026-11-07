import axios, { AxiosError } from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
  withCredentials: true, // Send and receive HttpOnly cookies
});

// Helper to extract cookie value
export function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^|;\\s*)(' + name + ')=([^;]*)'));
  return match ? decodeURIComponent(match[3]) : null;
}

// Attach authenticated session token and CSRF token if available
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = sessionStorage.getItem('udyam360_session_token');
    if (token && config.headers) {
      config.headers['X-Session-Token'] = token;
    }

    // Attach X-CSRF-Token for state-changing requests when csrf cookie is present
    const method = config.method?.toLowerCase();
    if (['post', 'put', 'delete', 'patch'].includes(method || '')) {
      const csrfToken = getCookie('udyam360_csrf');
      if (csrfToken && config.headers) {
        config.headers['X-CSRF-Token'] = csrfToken;
      }
    }
  }
  return config;
});

// Capture issued session tokens and handle errors
apiClient.interceptors.response.use(
  (response) => {
    if (typeof window !== 'undefined') {
      const tokenHeader = response.headers?.['x-session-token'];
      if (tokenHeader && typeof tokenHeader === 'string') {
        sessionStorage.setItem('udyam360_session_token', tokenHeader);
      } else if (response.data && response.data.session_token) {
        sessionStorage.setItem('udyam360_session_token', response.data.session_token);
      }
    }
    return response;
  },
  (error: AxiosError<{ detail?: string | any }>) => {
    let message = 'An unexpected server error occurred.';
    if (error.response?.data?.detail) {
      if (typeof error.response.data.detail === 'string') {
        message = error.response.data.detail;
      } else if (Array.isArray(error.response.data.detail)) {
        message = error.response.data.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
      } else {
        message = JSON.stringify(error.response.data.detail);
      }
    } else if (error.message) {
      message = error.message;
    }
    return Promise.reject(new Error(message));
  }
);
