export type BreakEvenPeriod = 'monthly' | 'quarterly' | 'annual';
export type BreakEvenStatus = 'above_break_even' | 'at_break_even' | 'below_break_even';

export interface BreakEvenAnalysisResponse {
    period: BreakEvenPeriod;
    currency: string;

    // Costos
    total_fixed_costs: number;      // Changed to number for easier calculation in frontend mock
    total_costs: number;

    // Horas
    total_billable_hours_available: number;
    break_even_hours: number;
    current_allocated_hours: number;
    hours_to_break_even: number;
    safety_margin_hours: number;
    safety_margin_percentage: number;

    // Ingresos
    break_even_revenue: number;    // Changed to number
    current_projected_revenue: number; // Changed to number
    revenue_to_break_even: number;     // Changed to number
    average_margin: number;

    // Métricas
    operating_leverage: number;
    current_utilization_rate: number;
    break_even_utilization_rate: number;

    // Estado
    status: BreakEvenStatus;
    status_message: string;

    // Proyección
    months_to_break_even?: number;
    projected_break_even_date?: string;

    // Breakdown
    cost_breakdown: {
        category: string;
        amount: number;
        percentage: number;
        color?: string;
    }[];
}

export interface ScenarioConfig {
    id: string;
    name: string;
    bcr_multiplier: number;        // 1.0 = sin cambio, 1.1 = +10%
    fixed_costs_adjustment: number; // 0 = sin cambio, positivo = aumentar
    average_margin_adjustment: number; // 0 = sin cambio, 0.15 = +15%
}

export interface ScenarioResult {
    id: string;
    name: string;
    isBase?: boolean;
    break_even_hours: number;
    break_even_revenue: number;
    hours_to_break_even: number;
    impact: {
        hours_change: number;
        revenue_change: number;
        impact_percentage: number;
        is_improvement: boolean;
    };
    config: ScenarioConfig;
}

export type MonthProjectionStatus = BreakEvenStatus;

export interface MonthProjection {
    month: string;              // "2026-02"
    allocated_hours: number;
    break_even_hours: number;
    hours_to_break_even: number;
    status: MonthProjectionStatus;
    break_even_date?: string;
    profit_hours?: number;
}

export interface BreakEvenProjectionResponse {
    current_status: {
        allocated_hours: number;
        break_even_hours: number;
        hours_to_break_even: number;
    };
    projection: MonthProjection[];
    break_even_date?: string;
    months_to_break_even?: number;
}
