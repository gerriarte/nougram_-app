import { apiRequest } from '@/lib/api-client';

export type TeamGroup = {
    id: number;
    name: string;
    description?: string;
    is_active: boolean;
};

type TeamGroupListResponse = {
    items: TeamGroup[];
    total: number;
};

export type TeamCellSummary = {
    id: number;
    group_id: number;
    name: string;
    description?: string;
    is_active: boolean;
};

type TeamCellListResponse = {
    items: TeamCellSummary[];
    total: number;
};

export type TeamCellVersionMember = {
    id: number;
    team_member_id: number;
    weight: string | number;
    role_override?: string | null;
    is_active: boolean;
};

export type TeamCellVersion = {
    id: number;
    cell_id: number;
    version_number: number;
    status: string;
    members: TeamCellVersionMember[];
};

type TeamCellVersionListResponse = {
    items: TeamCellVersion[];
    total: number;
};

type TeamGroupCreatePayload = {
    name: string;
    description?: string;
    is_active?: boolean;
};

type TeamCellCreatePayload = {
    group_id: number;
    name: string;
    description?: string;
    is_active?: boolean;
};

export type TeamCellPublishMemberInput = {
    team_member_id: number;
    weight: string;
    role_override?: string | null;
    is_active?: boolean;
};

type TeamCellPublishVersionPayload = {
    members: TeamCellPublishMemberInput[];
    notes?: string;
};

type TeamCellVersionResponse = TeamCellVersion;

let cachedGroups: TeamGroup[] | null = null;
let cachedCells: TeamCellSummary[] | null = null;
const cachedVersionsByCell = new Map<number, TeamCellVersion[]>();

export const teamCellsService = {
    async listGroups(forceRefresh = false): Promise<TeamGroup[]> {
        if (!forceRefresh && cachedGroups) return cachedGroups;
        const response = await apiRequest<TeamGroupListResponse>('/settings/team-groups?include_inactive=false');
        if (response.error || !response.data?.items) return [];
        cachedGroups = response.data.items;
        return cachedGroups;
    },

    async createGroup(payload: TeamGroupCreatePayload): Promise<TeamGroup | null> {
        const response = await apiRequest<TeamGroup>('/settings/team-groups', {
            method: 'POST',
            body: JSON.stringify({
                ...payload,
                is_active: payload.is_active ?? true,
            }),
        });
        if (response.error || !response.data) return null;
        cachedGroups = null;
        return response.data;
    },

    async listCells(forceRefresh = false): Promise<TeamCellSummary[]> {
        if (!forceRefresh && cachedCells) return cachedCells;
        const response = await apiRequest<TeamCellListResponse>('/settings/team-cells?include_inactive=false');
        if (response.error || !response.data?.items) return [];
        cachedCells = response.data.items;
        return cachedCells;
    },

    async createCell(payload: TeamCellCreatePayload): Promise<TeamCellSummary | null> {
        const response = await apiRequest<TeamCellSummary>('/settings/team-cells', {
            method: 'POST',
            body: JSON.stringify({
                ...payload,
                is_active: payload.is_active ?? true,
            }),
        });
        if (response.error || !response.data) return null;
        cachedCells = null;
        return response.data;
    },

    async listCellVersions(cellId: number, forceRefresh = false): Promise<TeamCellVersion[]> {
        if (!forceRefresh && cachedVersionsByCell.has(cellId)) {
            return cachedVersionsByCell.get(cellId) || [];
        }
        const response = await apiRequest<TeamCellVersionListResponse>(`/settings/team-cells/${cellId}/versions`);
        if (response.error || !response.data?.items) return [];
        cachedVersionsByCell.set(cellId, response.data.items);
        return response.data.items;
    },

    async publishVersion(cellId: number, payload: TeamCellPublishVersionPayload): Promise<TeamCellVersionResponse | null> {
        const response = await apiRequest<TeamCellVersionResponse>(`/settings/team-cells/${cellId}/publish-version`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        if (response.error || !response.data) return null;
        cachedVersionsByCell.delete(cellId);
        return response.data;
    },
};
