import { BreakEvenAnalysisResponse, ScenarioResult, ScenarioConfig, BreakEvenProjectionResponse, MonthProjection, BreakEvenStatus } from '@/types/break-even';

export const MOCK_BREAK_EVEN_DATA: BreakEvenAnalysisResponse = {
    period: 'monthly',
    currency: 'USD',

    // Costos (Mocked: $15,000 fixed costs)
    total_fixed_costs: 15000,
    total_costs: 15000, // Simplified

    // Horas
    total_billable_hours_available: 500, // 5 employees * 100h
    break_even_hours: 300,               // Need 300h to cover 15k at $50/h margin
    current_allocated_hours: 250,        // Currently have 250h sold
    hours_to_break_even: 50,             // 300 - 250
    safety_margin_hours: -50,
    safety_margin_percentage: -16.6,

    // Ingresos (Avg Margin $50/h -> needs $15k margin, probably revenue is higher but let's simplify)
    // Let's assume Price = $100/h, Cost = $50/h => Margin = $50/h
    break_even_revenue: 30000,
    current_projected_revenue: 25000,
    revenue_to_break_even: 5000,
    average_margin: 50,

    // Métricas
    operating_leverage: 2.5,
    current_utilization_rate: 50, // 250/500
    break_even_utilization_rate: 60, // 300/500

    // Estado
    status: 'below_break_even',
    status_message: 'Necesitas 50 horas adicionales para alcanzar el punto de equilibrio',

    // Proyección
    months_to_break_even: 1.5,
    projected_break_even_date: '2026-03-15',

    // Breakdown
    cost_breakdown: [
        { category: 'Salarios (Nómina)', amount: 12000, percentage: 80, color: 'bg-blue-500' },
        { category: 'Overhead', amount: 2000, percentage: 13, color: 'bg-indigo-500' },
        { category: 'Software', amount: 1000, percentage: 7, color: 'bg-cyan-500' }
    ]
};

// --- SIMULATION HELPERS ---

export const calculateScenario = (baseData: BreakEvenAnalysisResponse, config: ScenarioConfig): ScenarioResult => {
    // 1. Calculate new values based on adjustments
    // Base assumptions
    const currentFixedCosts = baseData.total_fixed_costs;
    const currentAvgMargin = baseData.average_margin; // e.g. 50
    // We infer BCR (Blended Cost Rate) roughly relates to costs/hours, but let's stick to Margin/FixedCosts model
    // BreakEvenHours = FixedCosts / AvgMargin

    // Apply Multipliers
    const newFixedCosts = currentFixedCosts + config.fixed_costs_adjustment;

    // BCR Multiplier logic: If BCR increases (costs increase), Margin usually decreases unless Price increases.
    // Requirement says: "BCR Multiplier... 1.1 (+10%)... A higher BCR reduces break even hours?" 
    // Wait, usually Higher Costs = Higher Break Even. 
    // Let's interpret "BCR Multiplier" context from requirements: 
    // "Un BCR más alto reduce las horas necesarias para equilibrio" -> This implies BCR is maybe "Billable Content Rate"? 
    // No, usually BCR is Blended Cost Rate. 
    // Let's look at the requirement text again: "ℹ️ Un BCR más alto reduce las horas necesarias para equilibrio".
    // If BCR = Rate charged to client? No that's Bill Rate. 
    // If BCR = Internal Cost? Higher internal cost = Lower Margin = HIGHER break even hours.

    // Let's assume the user meant "Average Rate Multiplier" OR maybe "Efficiency".
    // OR, if BCR multiplier is applied to the MARGIN directly?
    // Let's assume "Multiplicador de BCR" effectively improves the margin for this simulation (User might mean Rate).
    // Let's apply it to the MARGIN for positive effect as per requirement text.

    let newMargin = currentAvgMargin;

    // If logic is: Multiplier 1.1 IMPROVES position (reduces hours), then it must increase the numerator (Revenue/Margin).
    // Let's assume it multiplies the Margin.
    newMargin = newMargin * config.bcr_multiplier;

    // Apply explicit Margin adjustment
    // (0.15 = +15%)
    newMargin = newMargin * (1 + config.average_margin_adjustment);

    // Calculate New Break Even
    const newBreakEvenHours = newFixedCosts / newMargin;
    const newBreakEvenRevenue = newBreakEvenHours * (newMargin * 2); // Assuming Price is 2x Margin rough approx

    const hoursChange = newBreakEvenHours - baseData.break_even_hours;
    const revenueChange = newBreakEvenRevenue - baseData.break_even_revenue;

    // Improvement = Less hours needed
    const isImprovement = newBreakEvenHours < baseData.break_even_hours;

    return {
        id: config.id,
        name: config.name,
        break_even_hours: Math.round(newBreakEvenHours * 10) / 10,
        break_even_revenue: Math.round(newBreakEvenRevenue),
        hours_to_break_even: Math.max(0, Math.round((newBreakEvenHours - baseData.current_allocated_hours) * 10) / 10),
        impact: {
            hours_change: Math.round(hoursChange * 10) / 10,
            revenue_change: Math.round(revenueChange),
            impact_percentage: Math.round((hoursChange / baseData.break_even_hours) * 100 * 10) / 10,
            is_improvement: isImprovement
        },
        config
    };
};

export const generateProjection = (
    baseData: BreakEvenAnalysisResponse,
    months: number = 12,
    growthRate: number = 0
): BreakEvenProjectionResponse => {

    const projection: MonthProjection[] = [];
    const currentDate = new Date(); // Start next month

    let currentAllocated = baseData.current_allocated_hours;
    const breakEvenTarget = baseData.break_even_hours;

    let breakEvenDateFound: string | undefined = undefined;

    for (let i = 1; i <= months; i++) {
        // Increment month
        const d = new Date(currentDate);
        d.setMonth(d.getMonth() + i);
        const monthStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;

        // Apply growth
        // Growth is monthly compound
        if (i > 1) { // Apply growth starting from second month of projection relative to first? Or immediate?
            currentAllocated = currentAllocated * (1 + (growthRate / 100));
        } else {
            // First month already has growth applied? Or starts from current?
            currentAllocated = currentAllocated * (1 + (growthRate / 100));
        }

        const hoursToBE = breakEvenTarget - currentAllocated;
        let status: BreakEvenStatus = 'below_break_even';
        let profitHours = 0;

        if (currentAllocated > breakEvenTarget) {
            status = 'above_break_even';
            profitHours = currentAllocated - breakEvenTarget;
            if (!breakEvenDateFound) breakEvenDateFound = monthStr; // Roughly this month
        } else if (Math.abs(hoursToBE) < 1) {
            status = 'at_break_even';
            if (!breakEvenDateFound) breakEvenDateFound = monthStr;
        }

        projection.push({
            month: monthStr,
            allocated_hours: Math.round(currentAllocated * 10) / 10,
            break_even_hours: breakEvenTarget,
            hours_to_break_even: Math.round(hoursToBE * 10) / 10,
            status,
            break_even_date: (status !== 'below_break_even' && !breakEvenDateFound) ? monthStr : undefined,
            profit_hours: profitHours > 0 ? Math.round(profitHours) : undefined
        });
    }

    return {
        current_status: {
            allocated_hours: baseData.current_allocated_hours,
            break_even_hours: baseData.break_even_hours,
            hours_to_break_even: baseData.hours_to_break_even
        },
        projection,
        break_even_date: breakEvenDateFound
    };
};
