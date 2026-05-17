import { apiRequest } from '@/lib/api-client';
import { FixedCost } from '@/types/admin';

type FixedCostApi = {
  id: number;
  name: string;
  description?: string | null;
  category: string;
  amount_monthly: string | number;
  currency: FixedCost['currency'];
  is_active?: boolean;
};

type FixedCostListResponse = {
  items: FixedCostApi[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

function toNumber(value: string | number | null | undefined, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function mapApiToUi(item: FixedCostApi): FixedCost {
  return {
    id: String(item.id),
    name: item.name,
    description: item.description ?? undefined,
    category: item.category as FixedCost['category'],
    amountMonthly: toNumber(item.amount_monthly),
    currency: item.currency || 'COP',
    // Backend costs_fixed model does not include is_active flag.
    isActive: item.is_active ?? true,
  };
}

function mapUiToApi(item: Omit<FixedCost, 'id' | 'isActive'>) {
  return {
    name: item.name,
    description: item.description,
    category: item.category,
    amount_monthly: item.amountMonthly,
    currency: item.currency,
  };
}

export const fixedCostService = {
  async getAll(): Promise<FixedCost[]> {
    const response = await apiRequest<FixedCostListResponse>('/settings/costs/fixed?page=1&page_size=100');
    if (response.error || !response.data?.items) {
      console.warn('Failed to load fixed costs from backend:', response.error);
      return [];
    }
    return response.data.items.map(mapApiToUi);
  },

  async create(cost: Omit<FixedCost, 'id' | 'isActive'>): Promise<FixedCost | null> {
    const response = await apiRequest<FixedCostApi>('/settings/costs/fixed', {
      method: 'POST',
      body: JSON.stringify(mapUiToApi(cost)),
    });
    if (response.error || !response.data) return null;
    return mapApiToUi(response.data);
  },

  async update(id: string, updates: Partial<FixedCost>): Promise<FixedCost | null> {
    const numericId = Number(id);
    if (!Number.isFinite(numericId)) return null;

    const payload: Record<string, unknown> = {};
    if (updates.name !== undefined) payload.name = updates.name;
    if (updates.description !== undefined) payload.description = updates.description;
    if (updates.category !== undefined) payload.category = updates.category;
    if (updates.amountMonthly !== undefined) payload.amount_monthly = updates.amountMonthly;
    if (updates.currency !== undefined) payload.currency = updates.currency;

    const response = await apiRequest<FixedCostApi>(`/settings/costs/fixed/${numericId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    if (response.error || !response.data) return null;
    return mapApiToUi(response.data);
  },

  async remove(id: string): Promise<boolean> {
    const numericId = Number(id);
    if (!Number.isFinite(numericId)) return false;
    const response = await apiRequest<void>(`/settings/costs/fixed/${numericId}`, { method: 'DELETE' });
    return !response.error;
  },
};
