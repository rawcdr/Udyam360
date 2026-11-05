import { apiClient } from './client';
import { Product, CatalogueSummary } from '../types/catalogue';

export const catalogueApi = {
  getAll: async (category?: string): Promise<Product[]> => {
    const params = category ? { category } : {};
    const res = await apiClient.get<Product[]>('/catalogue', { params });
    return res.data;
  },

  getSummary: async (): Promise<CatalogueSummary> => {
    const res = await apiClient.get<CatalogueSummary>('/catalogue/summary');
    return res.data;
  },

  getById: async (productId: string): Promise<Product> => {
    const res = await apiClient.get<Product>(`/catalogue/${productId}`);
    return res.data;
  },

  getSegments: async (): Promise<any[]> => {
    const res = await apiClient.get('/segments');
    return res.data;
  },
};

