import { apiRequest } from '@/lib/api-client';

export type CapacityState = 'tentative' | 'committed' | 'actual';

type CapacityOverviewApiMember = {
    team_member_id: number;
    name: string;
    role: string;
    capacity_hours: string | number;
    tentative_hours: string | number;
    committed_hours: string | number;
    actual_hours: string | number;
    total_hours: string | number;
    utilization_ratio: string | number;
};

type CapacityOverviewApiCell = {
    cell_id: number;
    cell_name: string;
    tentative_hours: string | number;
    committed_hours: string | number;
    actual_hours: string | number;
    total_hours: string | number;
};

type CapacityOverviewApiTotals = {
    tentative_hours: string | number;
    committed_hours: string | number;
    actual_hours: string | number;
    total_hours: string | number;
};

type CapacityOverviewApiResponse = {
    period_start: string;
    period_end: string;
    months_count: number;
    states: CapacityState[];
    members: CapacityOverviewApiMember[];
    cells: CapacityOverviewApiCell[];
    totals: CapacityOverviewApiTotals;
};

export type CapacityOverviewMember = {
    teamMemberId: number;
    name: string;
    role: string;
    capacityHours: number;
    tentativeHours: number;
    committedHours: number;
    actualHours: number;
    totalHours: number;
    utilizationRatio: number;
};

export type CapacityOverviewCell = {
    cellId: number;
    cellName: string;
    tentativeHours: number;
    committedHours: number;
    actualHours: number;
    totalHours: number;
};

export type CapacityOverview = {
    periodStart: string;
    periodEnd: string;
    monthsCount: number;
    states: CapacityState[];
    members: CapacityOverviewMember[];
    cells: CapacityOverviewCell[];
    totals: {
        tentativeHours: number;
        committedHours: number;
        actualHours: number;
        totalHours: number;
    };
};

function toNumber(value: string | number | undefined): number {
    const parsed = Number(value ?? 0);
    return Number.isFinite(parsed) ? parsed : 0;
}

function mapCapacityOverview(apiData: CapacityOverviewApiResponse): CapacityOverview {
    return {
        periodStart: apiData.period_start,
        periodEnd: apiData.period_end,
        monthsCount: Number(apiData.months_count || 1),
        states: apiData.states || [],
        members: (apiData.members || []).map((member) => ({
            teamMemberId: member.team_member_id,
            name: member.name,
            role: member.role,
            capacityHours: toNumber(member.capacity_hours),
            tentativeHours: toNumber(member.tentative_hours),
            committedHours: toNumber(member.committed_hours),
            actualHours: toNumber(member.actual_hours),
            totalHours: toNumber(member.total_hours),
            utilizationRatio: toNumber(member.utilization_ratio),
        })),
        cells: (apiData.cells || []).map((cell) => ({
            cellId: cell.cell_id,
            cellName: cell.cell_name,
            tentativeHours: toNumber(cell.tentative_hours),
            committedHours: toNumber(cell.committed_hours),
            actualHours: toNumber(cell.actual_hours),
            totalHours: toNumber(cell.total_hours),
        })),
        totals: {
            tentativeHours: toNumber(apiData.totals?.tentative_hours),
            committedHours: toNumber(apiData.totals?.committed_hours),
            actualHours: toNumber(apiData.totals?.actual_hours),
            totalHours: toNumber(apiData.totals?.total_hours),
        },
    };
}

export const capacityService = {
    async getOverview(periodStart: string, periodEnd: string, states: CapacityState[]): Promise<CapacityOverview> {
        const stateQuery = (states || []).map((state) => `states=${encodeURIComponent(state)}`).join('&');
        const query = `/settings/capacity/overview?period_start=${encodeURIComponent(periodStart)}&period_end=${encodeURIComponent(periodEnd)}${stateQuery ? `&${stateQuery}` : ''}`;
        const response = await apiRequest<CapacityOverviewApiResponse>(query);
        if (response.error || !response.data) {
            throw new Error(response.error || 'No se pudo cargar la capacidad del equipo.');
        }
        return mapCapacityOverview(response.data);
    },
};
