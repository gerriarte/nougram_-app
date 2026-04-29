import { apiRequest } from '@/lib/api-client';
import { getAuthToken } from '@/lib/auth';

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
  /** Visual identity for this proposal */
  branding?: ProposalBranding;
  [key: string]: unknown;
};

export type ProposalBranding = {
  brandColor?: string;
  logoUrl?: string;
  coverImageUrl?: string;
};

export type ProposalSectionPlanItem = {
  id: string;
  label?: string;
  enabled: boolean;
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

export type ProposalSharePayload = {
  to_email?: string;
  quote_id?: number;
  access_expires_at?: string;
  access_code?: string;
  message?: string;
  send_email?: boolean;
};

export type ProposalShareResponse = {
  success: boolean;
  message: string;
  public_url: string;
  access_expires_at: string;
  last_sent_at?: string;
  access_code?: string;
  sent_email?: boolean;
};

export type ProposalShareStats = {
  proposal_id: number;
  link_id?: number | null;
  status?: string | null;
  view_count: number;
  viewed_at?: string | null;
  last_sent_at?: string | null;
  decided_at?: string | null;
  decision_comment?: string | null;
  access_expires_at?: string | null;
};

export type ProposalAssetUploadResponse = {
  success: boolean;
  asset_type: 'logo' | 'cover';
  asset_url: string;
  asset_key: string;
  body_json: ProposalBody;
};

export type ProposalAIGeneratePayload = {
  title?: string;
  language?: 'es' | 'en';
  extra_instructions?: string;
  services_context?: string;
  proposal_objective?: string;
  estimated_timeline?: string;
  payment_conditions?: string;
  execution_conditions?: string;
  tone?: string;
  audience?: string;
  differentiators?: string;
  section_plan?: ProposalSectionPlanItem[];
  persist_context?: boolean;
  user_api_key?: string;
  ai_provider?: 'openai' | 'anthropic';
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

  async generateAI(projectId: string, payload?: ProposalAIGeneratePayload): Promise<ProposalDocument | null> {
    const response = await apiRequest<ProposalDocument>(`/projects/${projectId}/proposals/ai-generate`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    });
    if (response.error || !response.data) return null;
    return response.data;
  },

  async shareWithClient(
    projectId: string,
    proposalId: number,
    payload: ProposalSharePayload,
  ): Promise<ProposalShareResponse | null> {
    const response = await apiRequest<ProposalShareResponse>(
      `/projects/${projectId}/proposals/${proposalId}/share`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
    );
    if (response.error || !response.data) return null;
    return response.data;
  },

  async getShareStats(projectId: string, proposalId: number): Promise<ProposalShareStats | null> {
    const response = await apiRequest<ProposalShareStats>(
      `/projects/${projectId}/proposals/${proposalId}/share-stats`,
    );
    if (response.error || !response.data) return null;
    return response.data;
  },

  async uploadAsset(
    projectId: string,
    proposalId: number,
    assetType: 'logo' | 'cover',
    file: File,
  ): Promise<ProposalAssetUploadResponse | null> {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, '');
    if (!baseUrl) return null;
    const token = getAuthToken();
    const formData = new FormData();
    formData.append('asset_type', assetType);
    formData.append('file', file);

    const response = await fetch(`${baseUrl}/projects/${projectId}/proposals/${proposalId}/assets`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!response.ok) return null;
    return await response.json() as ProposalAssetUploadResponse;
  },
};
