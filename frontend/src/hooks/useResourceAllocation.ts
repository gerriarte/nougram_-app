
import { useState, useEffect } from 'react';
import { resourceService } from '@/services/resourceService';
import { TeamMemberMock, ResourceAllocation } from '@/types/quote-builder';

export function useResourceAllocation(initialAllocations: ResourceAllocation[] = []) {
    const [teamMembers, setTeamMembers] = useState<TeamMemberMock[]>([]);
    const [loading, setLoading] = useState(true);
    const [allocations, setAllocations] = useState<ResourceAllocation[]>(initialAllocations);

    useEffect(() => {
        const loadMembers = async () => {
            try {
                const members = await resourceService.getAllMembers();
                setTeamMembers(members);
            } catch (error) {
                console.error("Failed to load team members", error);
            } finally {
                setLoading(false);
            }
        };
        loadMembers();
    }, []);

    // Allows updating the local allocations for "Preview" calculations
    const updateAllocations = (newAllocations: ResourceAllocation[]) => {
        setAllocations(newAllocations);
    };

    const getUtilization = (memberId: number) => {
        const member = teamMembers.find(m => m.id === memberId);
        if (!member) return { capacity: 0, used: 0, percentage: 0, remaining: 0 };

        return resourceService.calculateUtilization(member, allocations);
    };

    return {
        teamMembers,
        loading,
        getUtilization,
        updateAllocations
    };
}
