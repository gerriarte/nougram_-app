
import { QuoteItem, TaxConfig, CalculationSummary, ResourceAllocation } from '@/types/quote-builder';

// Interface for calculation results per item
export interface ItemCalculationResult {
    internalCost: number;
    clientPrice: number;
    marginPercentage: number;
    marginAmount: number;
}

// Interface for total calculation results (maps to CalculationSummary)
export interface QuoteCalculationResult extends CalculationSummary { }

export const pricingService = {

    /**
     * Calculates the financial details for a single item based on its inputs and context.
     * This simulates a backend endpoint: POST /api/quotes/calculate-item
     */
    calculateItem: (
        item: QuoteItem,
        bcr: number,
        globalTargetMargin: number
    ): ItemCalculationResult => {
        let internalCost = 0;
        let clientPrice = 0;

        // 1. Calculate Internal Cost (Based on Resources if available, or base params)
        // Unified Logic: If allocations exist, they ALWAYS drive the cost (except for project_value maybe?)
        // Actually, for 'project_value' cost is traditionally % of value, but if resources are added, we should probably track that too.
        // For now, let's stick to the specific types logic but prioritize resources.

        const resourceCost = (item.allocations || []).reduce((sum, alloc) => sum + (alloc.hours * bcr), 0);

        // Multiplier for recurring (Duration)
        const duration = item.durationMonths || 1;
        const totalResourceCost = resourceCost * duration;

        switch (item.pricingType) {
            case 'hourly':
                // Cost is derived purely from resources
                internalCost = totalResourceCost;
                // If no resources, cost is 0 (we removed manual estimated hours input)
                break;

            case 'fixed':
                // Cost is derived purely from resources (tracking profitability)
                internalCost = totalResourceCost;
                break;

            case 'recurring':
                // Cost is derived purely from resources
                internalCost = totalResourceCost;
                break;

            case 'project_value':
                // Cost is 60% of value (legacy rule) OR resource cost if higher?
                // Let's keep legacy rule for base calculation but maybe resources are just for info?
                // Request said: "Unified... resource allocation... for all 3 types (Hourly, Fixed, Recurring)".
                // Project Value wasn't explicitly mentioned to change, so we keep it as is, 
                // but maybe we allow adding resources just for tracking?
                // Let's assume resources track cost here too if present, otherwise fallback to percentage?
                // For safety, let's keep existing logic for Project Value: Cost = 60% of Price.
                internalCost = (item.projectValue || 0) * 0.60;
                break;
        }

        // 2. Calculate Client Price
        if (item.pricingType === 'recurring' && item.manualPrice) {
            clientPrice = item.manualPrice;
        } else {
            switch (item.pricingType) {
                case 'hourly':
                    // Price = Cost * (1 + Margin)
                    clientPrice = internalCost * (1 + globalTargetMargin);
                    break;

                case 'fixed':
                    // Price is independent of cost (it's fixed)
                    clientPrice = (item.fixedPrice || 0) * item.quantity;
                    break;

                case 'recurring':
                    // Price = (Monthly Cost * (1 + Margin)) * Duration
                    // If internalCost is Total Cost (Monthly * Duration), then:
                    // Price = (Total Cost * (1 + Margin))
                    clientPrice = internalCost * (1 + globalTargetMargin);
                    break;

                case 'project_value':
                    clientPrice = item.projectValue || 0;
                    break;
            }
        }

        // 3. Calculate Margin
        const marginAmount = clientPrice - internalCost;
        const marginPercentage = clientPrice > 0 ? (marginAmount / clientPrice) * 100 : 0;

        return {
            internalCost: Math.round(internalCost),
            clientPrice: Math.round(clientPrice),
            marginAmount: Math.round(marginAmount),
            marginPercentage
        };
    },

    /**
     * Calculates totals for the entire quote.
     * This simulates a backend endpoint: POST /api/quotes/calculate-totals
     */
    calculateQuoteTotals: (
        items: QuoteItem[],
        taxes: TaxConfig[],
        selectedTaxIds: number[],
        contingency?: { type: 'fixed' | 'percentage'; value: number }
    ): QuoteCalculationResult => {
        let totalInternalCost = 0;
        let totalClientPrice = 0;

        // Sum up items
        items.forEach(item => {
            totalInternalCost += item.internalCost;
            totalClientPrice += item.clientPrice;
        });

        // Calculate Contingency
        let contingencyAmount = 0;
        if (contingency && contingency.value > 0) {
            if (contingency.type === 'fixed') {
                contingencyAmount = contingency.value;
            } else {
                // Percentage of Total Client Price (Before Tax)
                contingencyAmount = totalClientPrice * (contingency.value / 100);
            }
        }

        const totalClientPriceWithContingency = totalClientPrice + contingencyAmount;

        // Calculate Taxes (Base = Price + Contingency)
        let totalTaxes = 0;
        selectedTaxIds.forEach(taxId => {
            const tax = taxes.find(t => t.id === taxId);
            if (tax) {
                totalTaxes += totalClientPriceWithContingency * (tax.percentage / 100);
            }
        });

        const totalWithTaxes = Math.round(totalClientPriceWithContingency + totalTaxes);
        // Real Income = (Price + Contingency) - Taxes
        const realIncome = Math.round(totalClientPriceWithContingency - totalTaxes);

        const netMarginAmount = realIncome - totalInternalCost;
        const netMarginPercent = realIncome > 0 ? (netMarginAmount / realIncome) * 100 : 0;

        return {
            totalInternalCost: Math.round(totalInternalCost),
            totalClientPrice: Math.round(totalClientPrice),

            contingencyAmount: Math.round(contingencyAmount),
            contingencyTotal: Math.round(totalClientPriceWithContingency),

            totalTaxes: Math.round(totalTaxes),
            totalWithTaxes,
            netMarginAmount: Math.round(netMarginAmount),
            netMarginPercent,
            realIncome
        };
    }
};
