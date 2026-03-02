import {
    BreakEvenAnalysisResponse,
    ScenarioConfig,
    ScenarioResult,
    BreakEvenProjectionResponse,
    MonthProjection,
    BreakEvenStatus
} from '@/types/break-even';
import { financialSummaryService } from '@/services/financialSummaryService';

export const breakEvenService = {
    /**
     * Fetches the current break even analysis data.
     */
    getAnalysis: async (): Promise<BreakEvenAnalysisResponse> => {
        const summary = await financialSummaryService.get();
        if (!summary) {
            throw new Error('No se pudo obtener el resumen financiero desde backend');
        }

        const totalFixedCosts = Number(summary.monthlyFixedCosts || 0);
        const totalCosts = Number((summary.monthlyFixedCosts || 0) + (summary.monthlyPayroll || 0));
        const totalBillableHours = Number(summary.totalBillableHours || 0);
        const blendedCostRate = Number(summary.blendedCostRate || 0);
        const breakEvenHours = blendedCostRate > 0 ? totalCosts / blendedCostRate : 0;
        const currentAllocatedHours = totalBillableHours;
        const hoursToBreakEven = Math.max(0, breakEvenHours - currentAllocatedHours);
        const safetyMarginHours = Math.max(0, currentAllocatedHours - breakEvenHours);
        const safetyMarginPercentage = breakEvenHours > 0 ? (safetyMarginHours / breakEvenHours) * 100 : 0;
        const breakEvenRevenue = breakEvenHours * blendedCostRate;
        const currentProjectedRevenue = currentAllocatedHours * blendedCostRate;
        const revenueToBreakEven = Math.max(0, breakEvenRevenue - currentProjectedRevenue);
        const currentUtilizationRate = totalBillableHours > 0 ? (currentAllocatedHours / totalBillableHours) * 100 : 0;
        const breakEvenUtilizationRate = totalBillableHours > 0 ? (breakEvenHours / totalBillableHours) * 100 : 0;
        const averageMargin = blendedCostRate > 0 ? ((blendedCostRate * 1.5 - blendedCostRate) / (blendedCostRate * 1.5)) * 100 : 0;

        const status: BreakEvenStatus =
            currentAllocatedHours > breakEvenHours
                ? 'above_break_even'
                : Math.abs(currentAllocatedHours - breakEvenHours) < 1
                    ? 'at_break_even'
                    : 'below_break_even';

        return {
            period: 'monthly',
            currency: summary.currency || 'USD',
            total_fixed_costs: totalFixedCosts,
            total_costs: totalCosts,
            total_billable_hours_available: totalBillableHours,
            break_even_hours: breakEvenHours,
            current_allocated_hours: currentAllocatedHours,
            hours_to_break_even: hoursToBreakEven,
            safety_margin_hours: safetyMarginHours,
            safety_margin_percentage: safetyMarginPercentage,
            break_even_revenue: breakEvenRevenue,
            current_projected_revenue: currentProjectedRevenue,
            revenue_to_break_even: revenueToBreakEven,
            average_margin: averageMargin,
            operating_leverage: totalFixedCosts > 0 ? totalCosts / totalFixedCosts : 0,
            current_utilization_rate: currentUtilizationRate,
            break_even_utilization_rate: breakEvenUtilizationRate,
            status,
            status_message:
                status === 'above_break_even'
                    ? 'Estás por encima del punto de equilibrio'
                    : status === 'at_break_even'
                        ? 'Estás en punto de equilibrio'
                        : 'Aún estás por debajo del punto de equilibrio',
            cost_breakdown: [
                {
                    category: 'Costos Fijos',
                    amount: totalFixedCosts,
                    percentage: totalCosts > 0 ? (totalFixedCosts / totalCosts) * 100 : 0,
                    color: '#6366F1',
                },
                {
                    category: 'Nómina',
                    amount: Number(summary.monthlyPayroll || 0),
                    percentage: totalCosts > 0 ? (Number(summary.monthlyPayroll || 0) / totalCosts) * 100 : 0,
                    color: '#14B8A6',
                },
            ],
        };
    },

    /**
     * Calculates a new scenario based on the base data and configuration.
     */
    calculateScenario: async (baseData: BreakEvenAnalysisResponse, config: ScenarioConfig): Promise<ScenarioResult> => {
        return calculateScenarioLogic(baseData, config);
    },

    /**
     * Generates a projection based on base data, growth rate, and months.
     */
    generateProjection: async (
        baseData: BreakEvenAnalysisResponse,
        months: number = 12,
        growthRate: number = 0
    ): Promise<BreakEvenProjectionResponse> => {
        return generateProjectionLogic(baseData, months, growthRate);
    }
};

// --- Logic helpers ---

const calculateScenarioLogic = (baseData: BreakEvenAnalysisResponse, config: ScenarioConfig): ScenarioResult => {
    const currentFixedCosts = baseData.total_fixed_costs;
    const currentAvgMargin = baseData.average_margin;

    // Apply Multipliers
    const newFixedCosts = currentFixedCosts + config.fixed_costs_adjustment;

    let newMargin = currentAvgMargin;

    // Apply BCR Multiplier (assuming it improves margin/rate)
    newMargin = newMargin * config.bcr_multiplier;

    // Apply explicit Margin adjustment
    newMargin = newMargin * (1 + config.average_margin_adjustment);

    // Calculate New Break Even
    // Prevent division by zero
    const effectiveMargin = newMargin <= 0 ? 1 : newMargin;

    const newBreakEvenHours = newFixedCosts / effectiveMargin;
    const newBreakEvenRevenue = newBreakEvenHours * (effectiveMargin * 2); // Assuming Price is ~2x Margin

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

const generateProjectionLogic = (
    baseData: BreakEvenAnalysisResponse,
    months: number,
    growthRate: number
): BreakEvenProjectionResponse => {
    const projection: MonthProjection[] = [];
    const currentDate = new Date();

    let currentAllocated = baseData.current_allocated_hours;
    const breakEvenTarget = baseData.break_even_hours;

    let breakEvenDateFound: string | undefined = undefined;
    let monthsToBE: number | undefined = undefined;

    for (let i = 1; i <= months; i++) {
        // Increment month safely
        const d = new Date(currentDate);
        d.setDate(1); // Avoids Jan 31 -> Mar 3 issues
        d.setMonth(d.getMonth() + i);

        // Format: "feb. 2026"
        const monthStr = d.toLocaleDateString('es-ES', { month: 'short', year: 'numeric' });

        // Apply growth (monthly compound)
        if (i >= 1) {
            currentAllocated = currentAllocated * (1 + (growthRate / 100));
        }

        const hoursToBE = breakEvenTarget - currentAllocated;
        let status: BreakEvenStatus = 'below_break_even';
        let profitHours = 0;

        if (currentAllocated > breakEvenTarget) {
            status = 'above_break_even';
            profitHours = currentAllocated - breakEvenTarget;

            if (!breakEvenDateFound) {
                breakEvenDateFound = monthStr;
                monthsToBE = i; // Rough estimate
            }
        } else if (Math.abs(hoursToBE) < 1) {
            status = 'at_break_even';
            if (!breakEvenDateFound) {
                breakEvenDateFound = monthStr;
                monthsToBE = i;
            }
        }

        projection.push({
            month: monthStr,
            allocated_hours: Math.round(currentAllocated * 10) / 10,
            break_even_hours: breakEvenTarget,
            hours_to_break_even: Math.max(0, Math.round(hoursToBE * 10) / 10),
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
        break_even_date: breakEvenDateFound,
        months_to_break_even: monthsToBE
    };
};
