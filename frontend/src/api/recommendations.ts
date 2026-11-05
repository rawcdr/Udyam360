import { apiClient } from './client';
import { BusinessProfile } from '../types/advisor';
import { RecommendationResponse } from '../types/recommendations';

export const recommendationApi = {
  getRecommendations: async (profile: BusinessProfile): Promise<RecommendationResponse> => {
    const res = await apiClient.post<RecommendationResponse>('/recommendations', profile);
    return res.data;
  },

  checkEligibility: async (profile: BusinessProfile): Promise<any> => {
    const res = await apiClient.post('/eligibility/check', profile);
    return res.data;
  },
};

