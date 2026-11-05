import { apiClient } from './client';
import {
  OrderCreateRequest,
  OrderResponse,
  OrderTimelineResponse,
  OrderState,
} from '../types/order';

export const orderApi = {
  create: async (request: OrderCreateRequest): Promise<OrderResponse> => {
    const res = await apiClient.post<OrderResponse>('/orders', request);
    return res.data;
  },

  getById: async (orderId: string): Promise<OrderResponse> => {
    const res = await apiClient.get<OrderResponse>(`/orders/${orderId}`);
    return res.data;
  },

  getTimeline: async (orderId: string): Promise<OrderTimelineResponse> => {
    const res = await apiClient.get<OrderTimelineResponse>(`/orders/${orderId}/timeline`);
    return res.data;
  },

  trackByReference: async (orderReference: string): Promise<OrderResponse> => {
    const res = await apiClient.get<OrderResponse>(`/orders/track/${encodeURIComponent(orderReference)}`);
    return res.data;
  },

  advance: async (
    orderId: string,
    targetState?: OrderState,
    notes?: string
  ): Promise<OrderResponse> => {
    const res = await apiClient.post<OrderResponse>(`/orders/${orderId}/advance`, {
      target_state: targetState || null,
      notes: notes || null,
    });
    return res.data;
  },
};

