import { ProjectInputs, QuoteCalculationResponse, QuoteItemInput, Tax } from "@/types/quote";

// Mock Constants
const MOCK_BCR = 50000; // 50,000 COP per hour internal cost
const DEFAULT_MARGIN_TARGET = 0.30; // 30%

const TAX_DEFINITIONS: Record<number, Tax> = {
    1: { id: 1, name: "IVA", code: "IVA_CO", percentage: "0.19", country: "CO", is_active: true },
    2: { id: 2, name: "ICA", code: "ICA_CO", percentage: "0.00966", country: "CO", is_active: true },
    3: { id: 3, name: "ReteFuente", code: "RETE_FUENTE_CO", percentage: "0.11", country: "CO", is_active: true },
};

export function calculateQuote(inputs: ProjectInputs): QuoteCalculationResponse {
    let totalInternalCost = 0;
    let totalClientPrice = 0;

    // 1. Calculate Items
    const calculatedItems = inputs.items.map(item => {
        let internalCost = 0;
        let clientPrice = 0;

        // Logic based on pricing type
        if (item.pricing_type === "hourly") {
            const hours = item.estimated_hours || 0;
            internalCost = hours * MOCK_BCR;
            // For hourly, usually price is `hours * rate`. Rate could be derived from target margin.
            // Price = Cost / (1 - Target Margin)
            const targetMargin = inputs.target_margin_percentage ? parseFloat(inputs.target_margin_percentage) : DEFAULT_MARGIN_TARGET;
            clientPrice = internalCost / (1 - targetMargin);

        } else if (item.pricing_type === "fixed") {
            clientPrice = parseFloat(item.fixed_price || "0") * parseFloat(item.quantity || "1");
            // Estimate cost as 70% of price if unknown (or 0 if pure profit? Let's assume 70% cost implies 30% margin)
            // Or better, assume cost is 0 for purely fixed (like licensing) unless specified. 
            // But usually "fixed" services still have hours. 
            // For this mock, I'll assume internal cost is 60% of price (40% margin).
            internalCost = clientPrice * 0.6;
        } else if (item.pricing_type === "recurring") {
            clientPrice = parseFloat(item.recurring_price || "0");
            internalCost = clientPrice * 0.5; // 50% margin estimate
        }

        totalInternalCost += internalCost;
        totalClientPrice += clientPrice;

        return {
            service_id: item.service_id,
            service_name: `Servicio ${item.service_id}`, // Mock name
            internal_cost: internalCost.toFixed(2),
            client_price: clientPrice.toFixed(2),
            margin_percentage: clientPrice > 0 ? ((clientPrice - internalCost) / clientPrice).toFixed(4) : "0",
            estimated_hours: item.estimated_hours,
            pricing_type: item.pricing_type || "hourly",
        };
    });

    // 2. Calculate Taxes
    let totalTaxes = 0;
    const calculatedTaxes = inputs.tax_ids.map(taxId => {
        const taxDef = TAX_DEFINITIONS[taxId];
        if (!taxDef) return null;

        const percentage = parseFloat(taxDef.percentage);
        const amount = totalClientPrice * percentage;
        totalTaxes += amount;

        return {
            id: taxDef.id,
            name: taxDef.name,
            code: taxDef.code,
            percentage: percentage.toString(),
            amount: amount.toFixed(2)
        };
    }).filter(t => t !== null) as any[];

    // 3. Totals
    const totalWithTaxes = totalClientPrice + totalTaxes;
    // Margin Logic: (Revenue - Cost) / Revenue. Revenue here is Client Price (without taxes usually, or with? Standard is margin on Net Revenue).
    // Margin = (Price - Cost) / Price
    const totalMargin = totalClientPrice > 0 ? (totalClientPrice - totalInternalCost) / totalClientPrice : 0;

    return {
        total_internal_cost: totalInternalCost.toFixed(2),
        total_client_price: totalClientPrice.toFixed(2),
        total_expenses_cost: "0", // Not implemented expenses input yet fully
        total_expenses_client_price: "0",
        total_taxes: totalTaxes.toFixed(2),
        total_with_taxes: totalWithTaxes.toFixed(2),
        margin_percentage: totalMargin.toFixed(4),
        target_margin_percentage: inputs.target_margin_percentage || DEFAULT_MARGIN_TARGET.toString(),
        items: calculatedItems,
        expenses: [],
        taxes: calculatedTaxes,
        revisions_cost: "0",
        revisions_included: 2
    };
}
