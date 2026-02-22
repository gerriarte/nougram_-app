import { apiRequest } from '@/lib/api-client';
import { SocialChargesConfig } from '@/types/admin';

type CurrentUserResponse = {
    organization_id?: number | null;
};

type OrganizationResponse = {
    id: number;
    settings?: {
        social_charges_config?: Partial<SocialChargesConfig>;
        [key: string]: unknown;
    };
};

type SaveOnboardingConfigResponse = {
    success: boolean;
    settings?: {
        social_charges_config?: Partial<SocialChargesConfig>;
        [key: string]: unknown;
    };
};

function normalizeSocialConfig(input: Partial<SocialChargesConfig>): SocialChargesConfig {
    const config: SocialChargesConfig = {
        enable_social_charges: Boolean(input.enable_social_charges),
        health_percentage: Number(input.health_percentage ?? 8.5),
        pension_percentage: Number(input.pension_percentage ?? 12),
        arl_percentage: Number(input.arl_percentage ?? 0.522),
        parafiscales_percentage: Number(input.parafiscales_percentage ?? 4),
        prima_services_percentage: Number(input.prima_services_percentage ?? 8.33),
        cesantias_percentage: Number(input.cesantias_percentage ?? 8.33),
        int_cesantias_percentage: Number(input.int_cesantias_percentage ?? 1),
        vacations_percentage: Number(input.vacations_percentage ?? 4.17),
        total_percentage: 0
    };

    config.total_percentage =
        config.health_percentage +
        config.pension_percentage +
        config.arl_percentage +
        config.parafiscales_percentage +
        config.prima_services_percentage +
        config.cesantias_percentage +
        config.int_cesantias_percentage +
        config.vacations_percentage;

    return config;
}

async function getCurrentOrganizationId(): Promise<number | null> {
    const userResponse = await apiRequest<CurrentUserResponse>('/auth/me');
    if (userResponse.error || !userResponse.data?.organization_id) return null;
    return userResponse.data.organization_id;
}

export const socialChargesService = {
    async get(): Promise<SocialChargesConfig | null> {
        const organizationId = await getCurrentOrganizationId();
        if (!organizationId) return null;

        const orgResponse = await apiRequest<OrganizationResponse>(`/organizations/${organizationId}`);
        const config = orgResponse.data?.settings?.social_charges_config;
        if (orgResponse.error || !config) return null;
        return normalizeSocialConfig(config);
    },

    async save(config: SocialChargesConfig): Promise<boolean> {
        const organizationId = await getCurrentOrganizationId();
        if (!organizationId) return false;

        const payload = {
            social_charges_config: {
                ...config
            }
        };

        const response = await apiRequest<SaveOnboardingConfigResponse>(
            `/organizations/${organizationId}/onboarding-config`,
            {
                method: 'POST',
                body: JSON.stringify(payload)
            }
        );

        return !response.error;
    }
};

