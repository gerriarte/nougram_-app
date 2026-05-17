import { apiRequest } from '@/lib/api-client';
import { Vendor } from '@/types/quote-builder';

type VendorApiItem = {
    id: number;
    name: string;
    description?: string | null;
    category?: string | null;
    default_cost?: string | number | null;
    default_markup_percentage?: string | number | null;
    is_active: boolean;
};

type VendorListResponse = {
    items: VendorApiItem[];
    total: number;
};

type VendorCreatePayload = {
    name: string;
    description?: string;
    category?: string;
    default_cost?: number;
    default_markup_percentage?: number;
    is_active?: boolean;
};

function mapVendor(item: VendorApiItem): Vendor {
    return {
        id: item.id,
        name: item.name,
        description: item.description ?? undefined,
        category: item.category ?? undefined,
        defaultCost: item.default_cost != null ? Number(item.default_cost) : undefined,
        defaultMarkupPercentage: item.default_markup_percentage != null
            ? Number(item.default_markup_percentage)
            : undefined,
        isActive: item.is_active,
    };
}

export const vendorService = {
    async getAll(activeOnly = false): Promise<Vendor[]> {
        const params = new URLSearchParams({ page_size: '200' });
        if (activeOnly) params.set('active_only', 'true');
        const response = await apiRequest<VendorListResponse>(`/vendors/?${params}`);
        if (response.error) throw new Error(response.error);
        return (response.data?.items || []).map(mapVendor);
    },

    async create(payload: VendorCreatePayload): Promise<Vendor> {
        const response = await apiRequest<VendorApiItem>('/vendors/', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        if (response.error || !response.data) {
            throw new Error(response.error || 'No se pudo crear el proveedor');
        }
        return mapVendor(response.data);
    },

    async update(id: number, payload: Partial<VendorCreatePayload>): Promise<Vendor> {
        const response = await apiRequest<VendorApiItem>(`/vendors/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(payload),
        });
        if (response.error || !response.data) {
            throw new Error(response.error || 'No se pudo actualizar el proveedor');
        }
        return mapVendor(response.data);
    },

    async remove(id: number): Promise<void> {
        const response = await apiRequest<void>(`/vendors/${id}`, { method: 'DELETE' });
        if (response.error) throw new Error(response.error);
    },
};
