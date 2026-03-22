import { apiRequest } from '@/lib/api-client';

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

let cachedCells: TeamCellSummary[] | null = null;
const cachedVersionsByCell = new Map<number, TeamCellVersion[]>();

export const teamCellsService = {
    async listCells(forceRefresh = false): Promise<TeamCellSummary[]> {
        if (!forceRefresh && cachedCells) return cachedCells;
        const response = await apiRequest<TeamCellListResponse>('/settings/team-cells?include_inactive=false');
        if (response.error || !response.data?.items) return [];
        cachedCells = response.data.items;
        return cachedCells;
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
};
