import { apiClient } from './client';
import { BusinessProfile } from '../types/advisor';
import { RecommendationResponse } from '../types/recommendations';

export const recommendationApi = {
  getRecommendations: async (profile: any): Promise<RecommendationResponse> => {
    const payload = {
      business_name: profile.business_name || 'Apollo Care Pharmacy',
      business_type: profile.business_type || 'Retail Pharmacy',
      business_segment: profile.business_segment || profile.segment || 'micro',
      employee_count: profile.employee_count ?? profile.num_employees ?? 4,
      num_sites: profile.num_sites ?? profile.sites_count ?? 1,
      city: profile.city || 'Bengaluru',
      city_tier: profile.city_tier || 1,
      has_gstin: profile.has_gstin ?? profile.gstin_available ?? true,
      has_udyam: profile.has_udyam ?? profile.udyam_available ?? true,
      monthly_budget_inr: profile.monthly_budget_inr ?? profile.budget_monthly ?? 4000,
      required_services: profile.required_services || profile.requested_services || ['Office Internet', 'Commercial Calling'],
    };
    const res = await apiClient.post<RecommendationResponse>('/recommendations', payload);
    return res.data;
  },

  checkEligibility: async (profile: BusinessProfile): Promise<any> => {
    const res = await apiClient.post('/eligibility/check', profile);
    return res.data;
  },
};

