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
      name: c.display_name,
      company: c.display_name,
      requester: c.requester_name ?? undefined,
      email: c.email ?? undefined,
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
      name: response.data.display_name,
      company: response.data.display_name,
      requester: response.data.requester_name ?? undefined,
      email: response.data.email ?? undefined,
    };
  },
};
