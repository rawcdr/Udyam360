import { apiClient } from './client';
import { QuotePreviewRequest, QuotePreviewResponse } from '../types/quote';

export const quoteApi = {
  previewQuote: async (request: any): Promise<QuotePreviewResponse> => {
    const rawProfile = request.profile || {};
    const normalizedProfile = {
      business_name: rawProfile.business_name || 'Apollo Care Pharmacy',
      business_type: rawProfile.business_type || 'Retail Pharmacy',
      business_segment: rawProfile.business_segment || rawProfile.segment || 'micro',
      employee_count: rawProfile.employee_count ?? rawProfile.num_employees ?? 4,
      num_sites: rawProfile.num_sites ?? rawProfile.sites_count ?? 1,
      city: rawProfile.city || 'Bengaluru',
      city_tier: rawProfile.city_tier || 1,
      has_gstin: rawProfile.has_gstin ?? rawProfile.gstin_available ?? true,
      has_udyam: rawProfile.has_udyam ?? rawProfile.udyam_available ?? true,
      monthly_budget_inr: rawProfile.monthly_budget_inr ?? rawProfile.budget_monthly ?? 4000,
      required_services: rawProfile.required_services || rawProfile.requested_services || [],
    };
    const payload = {
      ...request,
      profile: normalizedProfile,
    };
    const res = await apiClient.post<QuotePreviewResponse>('/quotes/preview', payload);
    return res.data;
  },
};

