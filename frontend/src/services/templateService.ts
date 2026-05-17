
import { apiRequest } from '@/lib/api-client';

export interface Template {
    id: string;
    name: string;
    amount: number;
    currency: string;
}

type OnboardingTemplatesResponse = {
    items: Array<{
        id: string;
        name: string;
        amount: string | number;
        currency: string;
    }>;
};

const mapTemplate = (item: OnboardingTemplatesResponse['items'][number]): Template => ({
    id: item.id,
    name: item.name,
    amount: Number(item.amount),
    currency: item.currency,
});

export const templateService = {
    getAll: async (): Promise<Template[]> => {
        const response = await apiRequest<OnboardingTemplatesResponse>('/onboarding/templates');
        if (response.error || !response.data?.items) return [];
        return response.data.items.map(mapTemplate);
    },

    search: async (query: string): Promise<Template[]> => {
        const all = await templateService.getAll();
        const lowerQuery = query.toLowerCase();
        return all.filter((template) => template.name.toLowerCase().includes(lowerQuery));
    }
};
