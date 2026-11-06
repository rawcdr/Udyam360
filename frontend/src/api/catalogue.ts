import { apiClient } from './client';
import { Product, CatalogueSummary } from '../types/catalogue';

export const catalogueApi = {
  getAll: async (category?: string): Promise<Product[]> => {
    const params = category ? { category } : {};
    const res = await apiClient.get<any[]>('/catalogue', { params });
    return (res.data || []).map((p) => ({
      ...p,
      monthly_price_min: p.monthly_price_min ?? p.price_min_inr_per_month ?? 0,
      monthly_price_max: p.monthly_price_max ?? p.price_max_inr_per_month ?? 0,
      pricing_unit: p.pricing_unit ?? p.unit ?? 'per site',
      one_time_setup_fee: p.one_time_setup_fee ?? p.one_time_setup_inr ?? 0,
    }));
  },

  getSummary: async (): Promise<CatalogueSummary> => {
    const res = await apiClient.get<CatalogueSummary>('/catalogue/summary');
    return res.data;
  },

  getById: async (productId: string): Promise<Product> => {
    const res = await apiClient.get<any>(`/catalogue/${productId}`);
    const p = res.data;
    return {
      ...p,
      monthly_price_min: p.monthly_price_min ?? p.price_min_inr_per_month ?? 0,
      monthly_price_max: p.monthly_price_max ?? p.price_max_inr_per_month ?? 0,
      pricing_unit: p.pricing_unit ?? p.unit ?? 'per site',
      one_time_setup_fee: p.one_time_setup_fee ?? p.one_time_setup_inr ?? 0,
    };
  },

  getSegments: async (): Promise<any[]> => {
    const res = await apiClient.get('/segments');
    return res.data;
  },
};

