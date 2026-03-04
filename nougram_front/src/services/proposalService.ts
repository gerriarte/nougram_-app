import { apiRequest } from '@/lib/api-client';

/** Hybrid commercial proposal: guided sections + free text */
export type ProposalBody = {
  description?: string;
  objectives?: string[];
  deliverables?: Array<{ name: string; status?: string }>;
  executive_summary?: string;
  /** Alcance del proyecto */
  scope?: string;
  /** Cronograma o hitos */
  timeline?: string;
  /** Condiciones comerciales o legales */
  conditions?: string;
  /** Ajustes narrativos finales */
  free_text?: string;
  [key: string]: unknown;
};

export type ProposalDocument = {
  id: number;
  project_id: number;
  organization_id: number;
  version: number;
  title: string;
  body_json: ProposalBody;
  status: string;
  is_locked: boolean;
  created_at?: string;
  updated_at?: string;
};

type ProposalListResponse = {
  items: ProposalDocument[];
  total: number;
};

export const proposalService = {
  async list(projectId: string): Promise<ProposalDocument[]> {
    const response = await apiRequest<ProposalListResponse>(`/projects/${projectId}/proposals`);
    if (response.error || !response.data?.items) return [];
    return response.data.items;
  },

  async getLatest(projectId: string): Promise<ProposalDocument | null> {
    const items = await proposalService.list(projectId);
    if (items.length === 0) return null;
    return items[0];
  },

  async create(projectId: string, payload: { title: string; body_json: ProposalBody; status?: string }): Promise<ProposalDocument | null> {
    const response = await apiRequest<ProposalDocument>(`/projects/${projectId}/proposals`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (response.error || !response.data) return null;
    return response.data;
  },

  async update(projectId: string, proposalId: number, payload: { title?: string; body_json?: ProposalBody; status?: string; is_locked?: boolean }): Promise<ProposalDocument | null> {
    const response = await apiRequest<ProposalDocument>(`/projects/${projectId}/proposals/${proposalId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    if (response.error || !response.data) return null;
    return response.data;
  },

  async generateAI(projectId: string, payload?: { title?: string; language?: 'es' | 'en'; extra_instructions?: string }): Promise<ProposalDocument | null> {
    const response = await apiRequest<ProposalDocument>(`/projects/${projectId}/proposals/ai-generate`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    });
    if (response.error || !response.data) return null;
    return response.data;
  },
};
