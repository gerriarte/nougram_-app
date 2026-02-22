
import { TeamMemberMock, ResourceAllocation } from '@/types/quote-builder';
import { apiRequest } from '@/lib/api-client';

type TeamApiMember = {
    id: number;
    name: string;
    role: string;
    billable_hours_per_week: number;
    non_billable_hours_percentage?: string | number;
    is_active?: boolean;
};

type TeamListResponse = {
    items: TeamApiMember[];
    total: number;
};

const WEEKS_PER_MONTH = 4.33;

function toNumber(value: string | number | undefined, fallback = 0): number {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}

function mapTeamApiMemberToResourceMember(member: TeamApiMember): TeamMemberMock {
    const nonBillable = toNumber(member.non_billable_hours_percentage, 0);
    const availableHours = member.billable_hours_per_week * WEEKS_PER_MONTH * (1 - nonBillable);
    return {
        id: member.id,
        name: member.name,
        role: member.role,
        availableHours: Number.isFinite(availableHours) && availableHours > 0 ? Number(availableHours.toFixed(2)) : 0
    };
}

export const resourceService = {
    getAllMembers: async (): Promise<TeamMemberMock[]> => {
        const response = await apiRequest<TeamListResponse>('/settings/team/allocation-members');
        if (response.error || !response.data?.items) return [];
        return response.data.items
            .filter((member) => member.is_active !== false)
            .map(mapTeamApiMemberToResourceMember);
    },

    getMemberById: async (id: number): Promise<TeamMemberMock | undefined> => {
        const members = await resourceService.getAllMembers();
        return members.find((member) => member.id === id);
    },

    /**
     * Calculates utilization for a member based on a list of allocations.
     * @param memberId The ID of the member to check.
     * @param allAllocations The full list of allocations context (could be global or just local to quote).
     */
    calculateUtilization: (member: TeamMemberMock, allAllocations: ResourceAllocation[]) => {
        const used = allAllocations
            .filter(a => a.teamMemberId === member.id)
            .reduce((sum, a) => sum + a.hours, 0);

        const percentage = member.availableHours > 0 ? (used / member.availableHours) * 100 : 0;

        return {
            capacity: member.availableHours,
            used,
            percentage,
            remaining: member.availableHours - used
        };
    }
};
