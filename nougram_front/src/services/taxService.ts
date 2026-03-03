import { apiRequest } from '@/lib/api-client';
import { TaxConfig } from '@/types/quote-builder';

type TaxApiItem = {
    id: number;
    name: string;
    code: string;
    percentage: string | number;
    country?: string | null;
    description?: string | null;
    is_active?: boolean;
};

type TaxListResponse = {
    items: TaxApiItem[];
    total: number;
};

type TaxCreatePayload = {
    name: string;
    code: string;
    percentage: number;
    country?: string;
    description?: string;
    is_active?: boolean;
};

type TaxUpdatePayload = Partial<TaxCreatePayload>;

function mapTax(item: TaxApiItem): TaxConfig {
    return {
        id: item.id,
        name: item.name,
        code: item.code,
        percentage: Number(item.percentage || 0),
        country: item.country || undefined,
        description: item.description || undefined,
        isActive: Boolean(item.is_active ?? true),
    };
}

export const taxService = {
    async getAll(
        options: boolean | { activeOnly?: boolean; country?: string } = true
    ): Promise<TaxConfig[]> {
        const resolved = typeof options === 'boolean'
            ? { activeOnly: options, country: undefined as string | undefined }
            : { activeOnly: options.activeOnly ?? true, country: options.country };

        const params = new URLSearchParams({
            page: '1',
            page_size: '200',
        });
        if (resolved.activeOnly) {
            params.set('active_only', 'true');
        }
        if (resolved.country && resolved.country.trim().length > 0) {
            params.set('country', resolved.country.trim().toUpperCase());
        }
        const query = `/taxes/?${params.toString()}`;

        const response = await apiRequest<TaxListResponse>(query);
        if (response.error) {
            throw new Error(response.error);
        }

        const items = response.data?.items || [];
        return items.map(mapTax);
    },

    async create(payload: TaxCreatePayload): Promise<TaxConfig> {
        const response = await apiRequest<TaxApiItem>('/taxes/', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        if (response.error || !response.data) {
            throw new Error(response.error || 'No se pudo crear el impuesto');
        }
        return mapTax(response.data);
    },

    async update(id: number, payload: TaxUpdatePayload): Promise<TaxConfig> {
        const response = await apiRequest<TaxApiItem>(`/taxes/${id}`, {
            method: 'PUT',
            body: JSON.stringify(payload),
        });
        if (response.error || !response.data) {
            throw new Error(response.error || 'No se pudo actualizar el impuesto');
        }
        return mapTax(response.data);
    },

    async remove(id: number): Promise<void> {
        const response = await apiRequest(`/taxes/${id}`, {
            method: 'DELETE',
        });
        if (response.error) {
            throw new Error(response.error);
        }
    },
};

