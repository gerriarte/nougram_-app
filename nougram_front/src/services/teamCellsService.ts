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

export type TeamSummary = {
    id: number;
    group_id: number;
    name: string;
    description?: string;
    is_active: boolean;
};

type TeamCellListResponse = {
    items: TeamSummary[];
    total: number;
};

export type TeamVersionMember = {
    id: number;
    team_member_id: number;
    weight: string | number;
    role_override?: string | null;
    is_active: boolean;
};

export type TeamVersion = {
    id: number;
    cell_id: number;
    version_number: number;
    status: string;
    members: TeamVersionMember[];
};

type TeamCellVersionListResponse = {
    items: TeamVersion[];
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

export type TeamPublishMemberInput = {
    team_member_id: number;
    weight: string;
    role_override?: string | null;
    is_active?: boolean;
};

type TeamCellPublishVersionPayload = {
    members: TeamPublishMemberInput[];
    notes?: string;
};

type TeamCellVersionResponse = TeamVersion;

let cachedGroups: TeamGroup[] | null = null;
let cachedCells: TeamSummary[] | null = null;
const cachedVersionsByCell = new Map<number, TeamVersion[]>();

export const workTeamsService = {
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

    async listTeams(forceRefresh = false): Promise<TeamSummary[]> {
        if (!forceRefresh && cachedCells) return cachedCells;
        const response = await apiRequest<TeamCellListResponse>('/settings/team-cells?include_inactive=false');
        if (response.error || !response.data?.items) return [];
        cachedCells = response.data.items;
        return cachedCells;
    },

    async createTeam(payload: TeamCellCreatePayload): Promise<TeamSummary | null> {
        const response = await apiRequest<TeamSummary>('/settings/team-cells', {
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

    async listTeamVersions(teamId: number, forceRefresh = false): Promise<TeamVersion[]> {
        if (!forceRefresh && cachedVersionsByCell.has(teamId)) {
            return cachedVersionsByCell.get(teamId) || [];
        }
        const response = await apiRequest<TeamCellVersionListResponse>(`/settings/team-cells/${teamId}/versions`);
        if (response.error || !response.data?.items) return [];
        cachedVersionsByCell.set(teamId, response.data.items);
        return response.data.items;
    },

    async publishVersion(teamId: number, payload: TeamCellPublishVersionPayload): Promise<TeamCellVersionResponse | null> {
        const response = await apiRequest<TeamCellVersionResponse>(`/settings/team-cells/${teamId}/publish-version`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        if (response.error || !response.data) return null;
        cachedVersionsByCell.delete(teamId);
        return response.data;
    },
};

// Backward compatibility aliases while transitioning from "cell" to "team".
export type TeamCellSummary = TeamSummary;
export type TeamCellVersionMember = TeamVersionMember;
export type TeamCellVersion = TeamVersion;
export type TeamCellPublishMemberInput = TeamPublishMemberInput;
export const teamCellsService = {
    ...workTeamsService,
    listCells: workTeamsService.listTeams,
    createCell: workTeamsService.createTeam,
    listCellVersions: workTeamsService.listTeamVersions,
};
