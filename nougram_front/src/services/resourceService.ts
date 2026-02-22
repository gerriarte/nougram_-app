
import { TeamMemberMock, ResourceAllocation } from '@/types/quote-builder';

// Mock Data moved from Context
const MOCK_TEAM_MEMBERS: TeamMemberMock[] = [
    { id: 1, name: 'Juan Pérez', role: 'Lead Developer', availableHours: 138.56 },
    { id: 2, name: 'María López', role: 'UI/UX Designer', availableHours: 120.0 },
    { id: 3, name: 'Carlos Ruiz', role: 'Project Manager', availableHours: 100.0 },
];

export const resourceService = {
    getAllMembers: async (): Promise<TeamMemberMock[]> => {
        // Simulate API call
        return new Promise((resolve) => {
            setTimeout(() => resolve([...MOCK_TEAM_MEMBERS]), 300);
        });
    },

    getMemberById: async (id: number): Promise<TeamMemberMock | undefined> => {
        return new Promise((resolve) => {
            setTimeout(() => resolve(MOCK_TEAM_MEMBERS.find(m => m.id === id)), 200);
        });
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
