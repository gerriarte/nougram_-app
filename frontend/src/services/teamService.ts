import { apiRequest } from '@/lib/api-client';
import { TeamMember } from '@/types/admin';

type TeamApiMember = {
    id: number;
    name: string;
    role: string;
    salary_monthly_brute: string | number;
    currency: TeamMember['currency'];
    billable_hours_per_week: number;
    non_billable_hours_percentage?: string | number;
    apply_social_charges?: boolean;
    is_active?: boolean;
};

type TeamListResponse = {
    items: TeamApiMember[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
};

type TeamCreatePayload = {
    name: string;
    role: string;
    salary_monthly_brute: number;
    currency: TeamMember['currency'];
    billable_hours_per_week: number;
    non_billable_hours_percentage: number;
    apply_social_charges: boolean;
    is_active: boolean;
};

export type TeamMemberSaveResult =
    | { ok: true; member: TeamMember }
    | { ok: false; error: string };

function toNumber(value: string | number | undefined, fallback = 0): number {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}

function mapApiToUi(member: TeamApiMember): TeamMember {
    return {
        id: String(member.id),
        name: member.name,
        role: member.role,
        salaryMonthlyBrute: toNumber(member.salary_monthly_brute),
        currency: member.currency || 'COP',
        applySocialCharges: member.apply_social_charges ?? true,
        salaryWithCharges: 0,
        billableHoursPerWeek: member.billable_hours_per_week || 0,
        nonBillablePercentage: toNumber(member.non_billable_hours_percentage, 0),
        vacationDaysPerYear: 15,
        isActive: member.is_active ?? true
    };
}

function mapUiToApi(member: TeamMember): TeamCreatePayload {
    return {
        name: member.name,
        role: member.role,
        salary_monthly_brute: member.salaryMonthlyBrute,
        currency: member.currency,
        billable_hours_per_week: member.billableHoursPerWeek,
        non_billable_hours_percentage: member.nonBillablePercentage,
        apply_social_charges: member.applySocialCharges,
        is_active: member.isActive
    };
}

export const teamService = {
    async getAll(): Promise<TeamMember[]> {
        const response = await apiRequest<TeamListResponse>('/settings/team?page=1&page_size=100');
        if (response.error || !response.data?.items) return [];
        return response.data.items.map(mapApiToUi);
    },

    async create(member: TeamMember): Promise<TeamMemberSaveResult> {
        const response = await apiRequest<TeamApiMember>('/settings/team', {
            method: 'POST',
            body: JSON.stringify(mapUiToApi(member))
        });
        if (response.error || !response.data) {
            return { ok: false, error: response.error ?? 'No se pudo crear el miembro.' };
        }
        return { ok: true, member: mapApiToUi(response.data) };
    },

    async update(member: TeamMember): Promise<TeamMemberSaveResult> {
        const memberId = Number(member.id);
        if (!Number.isFinite(memberId)) {
            return { ok: false, error: 'Identificador de miembro inválido.' };
        }
        const response = await apiRequest<TeamApiMember>(`/settings/team/${memberId}`, {
            method: 'PUT',
            body: JSON.stringify(mapUiToApi(member))
        });
        if (response.error || !response.data) {
            return { ok: false, error: response.error ?? 'No se pudo actualizar el miembro.' };
        }
        return { ok: true, member: mapApiToUi(response.data) };
    },

    async remove(memberId: string): Promise<boolean> {
        const numericId = Number(memberId);
        if (!Number.isFinite(numericId)) return false;
        const response = await apiRequest<void>(`/settings/team/${numericId}`, { method: 'DELETE' });
        return !response.error;
    }
};
