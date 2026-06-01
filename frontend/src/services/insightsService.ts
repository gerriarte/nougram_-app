import { apiRequest } from '@/lib/api-client';

export type BreakEven = {
    currency: string;
    break_even_cost: number;
    total_fixed: number;
    total_equipment: number;
    total_payroll: number;
    committed_revenue: number;
    mrr: number;
    one_time_monthly: number;
    coverage_percentage: number;
    surplus_or_deficit: number;
    break_even_rate_per_hour: number;
    capacity_hours: number;
    active_team_members: number;
    status: 'profit' | 'break_even' | 'deficit';
};

export type ResourceUtilizationMember = {
    team_member_id: number;
    name: string;
    role?: string;
    capacity_hours: number;
    allocated_hours: number;
    remaining_hours: number;
    utilization_percentage: number;
    over_allocated: boolean;
};

export type ResourceUtilization = {
    members: ResourceUtilizationMember[];
    total_capacity_hours: number;
    total_allocated_hours: number;
    overall_utilization_percentage: number;
};

export const insightsService = {
    getBreakEven: async (): Promise<BreakEven | null> => {
        const res = await apiRequest<BreakEven>('/insights/break-even');
        if (res.error || !res.data) return null;
        return res.data;
    },
    getResourceUtilization: async (start?: string, end?: string): Promise<ResourceUtilization | null> => {
        const params = new URLSearchParams();
        if (start) params.set('start_date', start);
        if (end) params.set('end_date', end);
        const qs = params.toString();
        const res = await apiRequest<ResourceUtilization>(`/insights/resource-utilization${qs ? `?${qs}` : ''}`);
        if (res.error || !res.data) return null;
        return res.data;
    },
};
