import { apiClient } from './client';
import {
  AdvisorStartResponse,
  AdvisorMessageRequest,
  AdvisorMessageResponse,
  ConversationState,
} from '../types/advisor';

export const advisorApi = {
  start: async (): Promise<AdvisorStartResponse> => {
    const res = await apiClient.post<AdvisorStartResponse>('/advisor/start');
    return res.data;
  },

  sendMessage: async (conversationId: string, message: string): Promise<AdvisorMessageResponse> => {
    const payload: AdvisorMessageRequest = { conversation_id: conversationId, message };
    const res = await apiClient.post<AdvisorMessageResponse>('/advisor/message', payload);
    return res.data;
  },

  getConversation: async (conversationId: string): Promise<ConversationState> => {
    const res = await apiClient.get<ConversationState>(`/advisor/conversation/${conversationId}`);
    return res.data;
  },

  reset: async (conversationId: string): Promise<{ status: string; message: string }> => {
    const res = await apiClient.post(`/advisor/reset/${conversationId}`);
    return res.data;
  },

  getHealth: async (): Promise<{ status: string; llm_provider: string; configured_model: string }> => {
    const res = await apiClient.get('/advisor/health');
    return res.data;
  },
};

