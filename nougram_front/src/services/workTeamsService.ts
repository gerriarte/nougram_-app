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

type TeamListResponse = {
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

type TeamVersionListResponse = {
    items: TeamVersion[];
    total: number;
};

type TeamGroupCreatePayload = {
    name: string;
    description?: string;
    is_active?: boolean;
};

type TeamCreatePayload = {
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

type TeamPublishVersionPayload = {
    members: TeamPublishMemberInput[];
    notes?: string;
};

let cachedGroups: TeamGroup[] | null = null;
let cachedTeams: TeamSummary[] | null = null;
const cachedVersionsByTeam = new Map<number, TeamVersion[]>();

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
        if (!forceRefresh && cachedTeams) return cachedTeams;
        const response = await apiRequest<TeamListResponse>('/settings/team-cells?include_inactive=false');
        if (response.error || !response.data?.items) return [];
        cachedTeams = response.data.items;
        return cachedTeams;
    },

    async createTeam(payload: TeamCreatePayload): Promise<TeamSummary | null> {
        const response = await apiRequest<TeamSummary>('/settings/team-cells', {
            method: 'POST',
            body: JSON.stringify({
                ...payload,
                is_active: payload.is_active ?? true,
            }),
        });
        if (response.error || !response.data) return null;
        cachedTeams = null;
        return response.data;
    },

    async listTeamVersions(teamId: number, forceRefresh = false): Promise<TeamVersion[]> {
        if (!forceRefresh && cachedVersionsByTeam.has(teamId)) {
            return cachedVersionsByTeam.get(teamId) || [];
        }
        const response = await apiRequest<TeamVersionListResponse>(`/settings/team-cells/${teamId}/versions`);
        if (response.error || !response.data?.items) return [];
        cachedVersionsByTeam.set(teamId, response.data.items);
        return response.data.items;
    },

    async publishVersion(teamId: number, payload: TeamPublishVersionPayload): Promise<TeamVersion | null> {
        const response = await apiRequest<TeamVersion>(`/settings/team-cells/${teamId}/publish-version`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        if (response.error || !response.data) return null;
        cachedVersionsByTeam.delete(teamId);
        return response.data;
    },
};

