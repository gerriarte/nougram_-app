
export type EquipmentCategory = 'Hardware' | 'Software' | 'Vehicles' | 'Office Equipment';
export type DepreciationMethod = 'straight_line' | 'declining_balance';
export type Currency = 'COP' | 'USD' | 'EUR';

export interface Equipment {
    id: string;
    name: string;
    description?: string;
    category: EquipmentCategory;

    // Purchase Info
    purchasePrice: number;
    purchaseDate: string; // ISO Date YYYY-MM-DD
    currency: Currency;
    exchangeRateAtPurchase?: number; // Required if currency != primary

    // Depreciation Params
    usefulLifeMonths: number;
    salvageValue: number;
    depreciationMethod: DepreciationMethod;

    // Computed / State
    isActive: boolean;
    createdAt: string;
}

export interface DepreciationResult {
    monthlyDepreciation: number;    // The cost to add to overhead/BCR
    currentBookValue: number;       // Value today
    totalDepreciated: number;       // How much lost so far
    percentageDepreciated: number;  // 0-100%
    monthsRemaining: number;
    isFullyDepreciated: boolean;
}
