import { apiClient } from './client';
import { QuotePreviewRequest, QuotePreviewResponse } from '../types/quote';

export const quoteApi = {
  previewQuote: async (request: QuotePreviewRequest): Promise<QuotePreviewResponse> => {
    const res = await apiClient.post<QuotePreviewResponse>('/quotes/preview', request);
    return res.data;
  },
};

