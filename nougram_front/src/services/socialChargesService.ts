import { apiRequest } from '@/lib/api-client';
import { Currency, SocialChargesConfig } from '@/types/admin';
import {
    buildSocialChargesConfigFromCurrency,
    getSocialChargesPresetMetaByCountry,
} from '@/lib/social-charges-presets';

type CurrentUserResponse = {
    organization_id?: number | null;
};

type OrganizationResponse = {
    id: number;
    settings?: {
        social_charges_config?: Partial<SocialChargesConfig>;
        primary_currency?: Currency;
        currency?: Currency;
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

function normalizeSocialConfig(
    input: Partial<SocialChargesConfig>,
    baseCurrency: Currency
): SocialChargesConfig {
    const presetFromCurrency = buildSocialChargesConfigFromCurrency(baseCurrency, false);
    const presetFromCountry = getSocialChargesPresetMetaByCountry(input.country_code);
    const preset = {
        ...presetFromCurrency,
        ...presetFromCountry.percentages,
        country_code: presetFromCountry.countryCode,
        preset_key: presetFromCountry.presetKey,
    };
    const config: SocialChargesConfig = {
        enable_social_charges: Boolean(input.enable_social_charges ?? preset.enable_social_charges),
        health_percentage: Number(input.health_percentage ?? preset.health_percentage),
        pension_percentage: Number(input.pension_percentage ?? preset.pension_percentage),
        arl_percentage: Number(input.arl_percentage ?? preset.arl_percentage),
        parafiscales_percentage: Number(input.parafiscales_percentage ?? preset.parafiscales_percentage),
        prima_services_percentage: Number(input.prima_services_percentage ?? preset.prima_services_percentage),
        cesantias_percentage: Number(input.cesantias_percentage ?? preset.cesantias_percentage),
        int_cesantias_percentage: Number(input.int_cesantias_percentage ?? preset.int_cesantias_percentage),
        vacations_percentage: Number(input.vacations_percentage ?? preset.vacations_percentage),
        total_percentage: 0,
        country_code: input.country_code || preset.country_code,
        preset_key: input.preset_key || preset.preset_key,
        version: Number(input.version || 1),
        updated_at: input.updated_at || new Date().toISOString(),
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
        const orgCurrency =
            orgResponse.data?.settings?.primary_currency ||
            orgResponse.data?.settings?.currency ||
            'COP';
        const baseCurrency = orgCurrency as Currency;
        if (orgResponse.error || !config) return null;
        return normalizeSocialConfig(config, baseCurrency);
    },

    async save(config: SocialChargesConfig): Promise<boolean> {
        const organizationId = await getCurrentOrganizationId();
        if (!organizationId) return false;

        const normalized = normalizeSocialConfig(config, 'COP');
        const payload = {
            social_charges_config: {
                ...normalized
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

