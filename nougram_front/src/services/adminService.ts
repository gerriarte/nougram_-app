import {
    TeamMemberInput,
    SocialChargesConfig,
    FixedCostInput,
    GlobalConfig
} from "@/types/admin";

// --- INITIAL DATA CONSTANTS ---
// Moved from page.tsx to here
const INITIAL_SOCIAL_CHARGES: SocialChargesConfig = {
    enable_social_charges: true,
    health_percentage: 8.5,
    pension_percentage: 12.0,
    arl_percentage: 0.522,
    parafiscales_percentage: 4.0,
    prima_services_percentage: 8.33,
    cesantias_percentage: 8.33,
    int_cesantias_percentage: 1.0,
    vacations_percentage: 4.17
};

const INITIAL_GLOBAL_CONFIG: GlobalConfig = {
    default_billable_hours_per_week: 32,
    default_non_billable_percentage: "0.20",
    default_margin_target: "0.30",
    primary_currency: "COP"
};

const INITIAL_MEMBERS: TeamMemberInput[] = [
    { id: 1, name: "Ana Silva", role: "Senior Designer", is_active: true, salary_monthly_brute: "4500000", currency: "COP", billable_hours_per_week: 32, non_billable_hours_percentage: "0.20" },
    { id: 2, name: "Carlos Ruiz", role: "Frontend Dev", is_active: true, salary_monthly_brute: "5000000", currency: "COP", billable_hours_per_week: 35, non_billable_hours_percentage: "0.10" }
];

const INITIAL_COSTS: FixedCostInput[] = [
    { id: 1, name: "Alquiler WeWork", category: "Overhead", amount_monthly: "1200000", currency: "COP", description: "Oficina principal" },
    { id: 2, name: "Suscripción Figma", category: "Software", amount_monthly: "200000", currency: "COP", description: "Licencia Team" }
];

export const adminService = {
    // --- LOADERS ---
    getMembers: (): TeamMemberInput[] => {
        return INITIAL_MEMBERS;
    },

    getCosts: (): FixedCostInput[] => {
        return INITIAL_COSTS;
    },

    getSocialConfig: (): SocialChargesConfig => {
        return INITIAL_SOCIAL_CHARGES;
    },

    getGlobalConfig: (): GlobalConfig => {
        return INITIAL_GLOBAL_CONFIG;
    },

    // --- SAVERS ---
    saveMembers: (_data: TeamMemberInput[]) => undefined,

    saveCosts: (_data: FixedCostInput[]) => undefined,

    saveSocialConfig: (_data: SocialChargesConfig) => undefined,

    saveGlobalConfig: (_data: GlobalConfig) => undefined,

    // --- RESET ---
    resetDefaults: () => {
        return {
            members: INITIAL_MEMBERS,
            costs: INITIAL_COSTS,
            social: INITIAL_SOCIAL_CHARGES,
            global: INITIAL_GLOBAL_CONFIG
        };
    }
};
