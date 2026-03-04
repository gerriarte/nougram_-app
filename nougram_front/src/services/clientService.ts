import { apiRequest } from '@/lib/api-client';

export interface ClientSearchItem {
  id: number;
  display_name: string;
  requester_name?: string | null;
  email?: string | null;
}

export interface Client {
  id: number;
  name: string;
  company?: string;
  requester?: string;
  email?: string;
}

function normalizeOptionalText(value: unknown): string {
  if (typeof value !== 'string') return '';
  const trimmed = value.trim();
  if (!trimmed) return '';
  if (trimmed.toLowerCase() === 'undefined' || trimmed.toLowerCase() === 'null') return '';
  return trimmed;
}

type ClientSearchResponse = {
  items: ClientSearchItem[];
  total: number;
};

type ClientCreatePayload = {
  display_name: string;
  requester_name?: string;
  email?: string;
  status?: string;
  notes?: string;
};

export const clientService = {
  searchClients: async (query: string): Promise<Client[]> => {
    if (!query || query.trim().length < 2) return [];
    const response = await apiRequest<ClientSearchResponse>(
      `/clients/search?q=${encodeURIComponent(query.trim())}&limit=20`
    );
    if (response.error || !response.data?.items) return [];
    return response.data.items.map((c) => ({
      id: c.id,
      name: normalizeOptionalText(c.display_name),
      company: normalizeOptionalText(c.display_name),
      requester: normalizeOptionalText(c.requester_name) || undefined,
      email: normalizeOptionalText(c.email) || undefined,
    }));
  },

  createClient: async (payload: ClientCreatePayload): Promise<Client | null> => {
    const response = await apiRequest<{
      id: number;
      display_name: string;
      requester_name?: string | null;
      email?: string | null;
    }>('/clients/', {
      method: 'POST',
      body: JSON.stringify({
        display_name: payload.display_name,
        requester_name: payload.requester_name || undefined,
        email: payload.email || undefined,
        status: 'active',
      }),
    });
    if (response.error || !response.data) return null;
    return {
      id: response.data.id,
      name: normalizeOptionalText(response.data.display_name),
      company: normalizeOptionalText(response.data.display_name),
      requester: normalizeOptionalText(response.data.requester_name) || undefined,
      email: normalizeOptionalText(response.data.email) || undefined,
    };
  },
};
