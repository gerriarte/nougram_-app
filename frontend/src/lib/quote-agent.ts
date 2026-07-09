import { apiRequest, type ApiResponse } from '@/lib/api-client';

export type QuoteAgentEstimateItem = {
  service_id: number;
  service_name?: string | null;
  pricing_type?: string | null;
  estimated_hours?: number | null;
  quantity?: number | null;
  internal_cost: number;
  client_price: number;
  margin_percentage: number;
};

export type QuoteAgentEstimate = {
  items: QuoteAgentEstimateItem[];
  total_internal_cost: number;
  total_client_price: number;
  margin_percentage: number;
  target_margin_percentage?: number | null;
  minimum_margin_threshold?: number | null;
  below_minimum_margin: boolean;
};

export type QuoteAgentMessage = {
  id: number;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content?: string | null;
  meta?: Record<string, unknown> | null;
  created_at?: string | null;
};

export type QuoteAgentConversation = {
  id: number;
  status: string;
  project_id?: number | null;
  quote_id?: number | null;
  created_at?: string | null;
  messages: QuoteAgentMessage[];
};

export type SendMessageResult = {
  assistant_message: QuoteAgentMessage;
  estimate?: QuoteAgentEstimate | null;
};

export type ConfirmResult = {
  project_id: number;
  quote_id: number;
};

export type ConfirmPayload = {
  client_name: string;
  client_email?: string | null;
  project_name?: string | null;
  tax_ids?: number[];
  target_margin_percentage?: number | null;
  allow_low_margin?: boolean;
};

export async function createConversation(): Promise<ApiResponse<{ id: number; status: string }>> {
  return apiRequest('/quote-agent/conversations', { method: 'POST' });
}

export async function getConversation(
  conversationId: number
): Promise<ApiResponse<QuoteAgentConversation>> {
  return apiRequest(`/quote-agent/conversations/${conversationId}`);
}

export async function listConversations(): Promise<
  ApiResponse<Array<Omit<QuoteAgentConversation, 'messages'>>>
> {
  return apiRequest('/quote-agent/conversations');
}

export async function sendMessage(
  conversationId: number,
  content: string
): Promise<ApiResponse<SendMessageResult>> {
  return apiRequest(`/quote-agent/conversations/${conversationId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });
}

export async function confirmDraft(
  conversationId: number,
  payload: ConfirmPayload
): Promise<ApiResponse<ConfirmResult>> {
  return apiRequest(`/quote-agent/conversations/${conversationId}/confirm`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
