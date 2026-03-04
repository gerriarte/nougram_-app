import { apiRequest } from '@/lib/api-client';
import { Equipment } from '@/types/equipment';

type EquipmentApi = {
  id: number;
  name: string;
  description?: string | null;
  category: string;
  purchase_price: string | number;
  purchase_date: string;
  currency: Equipment['currency'];
  exchange_rate_at_purchase?: string | number | null;
  useful_life_months: number;
  salvage_value: string | number;
  depreciation_method: Equipment['depreciationMethod'];
  is_active: boolean;
  created_at?: string;
};

type EquipmentListResponse = {
  items: EquipmentApi[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

function toNumber(value: string | number | null | undefined, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function mapApiToUi(item: EquipmentApi): Equipment {
  return {
    id: String(item.id),
    name: item.name,
    description: item.description ?? undefined,
    category: item.category as Equipment['category'],
    purchasePrice: toNumber(item.purchase_price),
    purchaseDate: item.purchase_date,
    currency: item.currency || 'COP',
    exchangeRateAtPurchase: item.exchange_rate_at_purchase == null ? undefined : toNumber(item.exchange_rate_at_purchase),
    usefulLifeMonths: item.useful_life_months,
    salvageValue: toNumber(item.salvage_value),
    depreciationMethod: item.depreciation_method,
    isActive: item.is_active,
    createdAt: item.created_at || new Date().toISOString(),
  };
}

function mapUiToApi(item: Omit<Equipment, 'id' | 'createdAt'>) {
  return {
    name: item.name,
    description: item.description,
    category: item.category,
    purchase_price: item.purchasePrice,
    purchase_date: item.purchaseDate,
    currency: item.currency,
    exchange_rate_at_purchase: item.exchangeRateAtPurchase,
    useful_life_months: item.usefulLifeMonths,
    salvage_value: item.salvageValue,
    depreciation_method: item.depreciationMethod,
    is_active: item.isActive,
  };
}

export const equipmentService = {
  async getAll(): Promise<Equipment[]> {
    const response = await apiRequest<EquipmentListResponse>('/settings/equipment?page=1&page_size=100');
    if (response.error || !response.data?.items) {
      console.warn('Failed to load equipment from backend:', response.error);
      return [];
    }
    return response.data.items.map(mapApiToUi);
  },

  async create(item: Omit<Equipment, 'id' | 'createdAt'>): Promise<Equipment | null> {
    const response = await apiRequest<EquipmentApi>('/settings/equipment', {
      method: 'POST',
      body: JSON.stringify(mapUiToApi(item)),
    });
    if (response.error || !response.data) return null;
    return mapApiToUi(response.data);
  },

  async update(id: string, updates: Partial<Equipment>): Promise<Equipment | null> {
    const numericId = Number(id);
    if (!Number.isFinite(numericId)) return null;
    const payload: Record<string, unknown> = {};

    if (updates.name !== undefined) payload.name = updates.name;
    if (updates.description !== undefined) payload.description = updates.description;
    if (updates.category !== undefined) payload.category = updates.category;
    if (updates.purchasePrice !== undefined) payload.purchase_price = updates.purchasePrice;
    if (updates.purchaseDate !== undefined) payload.purchase_date = updates.purchaseDate;
    if (updates.currency !== undefined) payload.currency = updates.currency;
    if (updates.exchangeRateAtPurchase !== undefined) payload.exchange_rate_at_purchase = updates.exchangeRateAtPurchase;
    if (updates.usefulLifeMonths !== undefined) payload.useful_life_months = updates.usefulLifeMonths;
    if (updates.salvageValue !== undefined) payload.salvage_value = updates.salvageValue;
    if (updates.depreciationMethod !== undefined) payload.depreciation_method = updates.depreciationMethod;
    if (updates.isActive !== undefined) payload.is_active = updates.isActive;

    const response = await apiRequest<EquipmentApi>(`/settings/equipment/${numericId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    if (response.error || !response.data) return null;
    return mapApiToUi(response.data);
  },

  async remove(id: string): Promise<boolean> {
    const numericId = Number(id);
    if (!Number.isFinite(numericId)) return false;
    const response = await apiRequest<void>(`/settings/equipment/${numericId}`, { method: 'DELETE' });
    return !response.error;
  },
};
