export interface ProjectInputs {
    // Información básica
    name: string;
    client_name: string;
    client_email?: string;
    currency: "COP" | "USD";

    // Items de cotización
    items: QuoteItemInput[];

    // Impuestos (selección múltiple - IDs)
    tax_ids: number[];

    // Configuración de margen
    target_margin_percentage?: string; // Decimal string (0-1)

    // Revisiones
    revisions_included?: number;
    revision_cost_per_additional?: string; // Decimal string
    revisions_count?: number;

    // Gastos de terceros
    expenses?: ExpenseInput[];
}

export interface QuoteItemInput {
    service_id: number;

    // Pricing Types
    pricing_type?: "hourly" | "fixed" | "recurring" | "project_value";

    // Hourly
    estimated_hours?: number;

    // Fixed
    fixed_price?: string;
    quantity?: string; // default "1.0"

    // Recurring
    recurring_price?: string;
    billing_frequency?: "monthly" | "annual";

    // Project Value
    project_value?: string;
}

export interface ExpenseInput {
    name: string;
    description?: string;
    cost: string; // Decimal string
    markup_percentage: string; // Decimal string
    quantity?: string; // default "1.0"
    category: string;
}

export interface SocialChargesConfig {
    enable_social_charges: boolean;
    health_percentage: number;
    pension_percentage: number;
    arl_percentage: number;
    parafiscales_percentage: number;
    prima_services_percentage: number;
    cesantias_percentage: number;
    int_cesantias_percentage: number;
    vacations_percentage: number;
    total_percentage: number;
}

export interface Tax {
    id: number;
    name: string;
    code: string;
    percentage: string; // Decimal string
    country: string;
    is_active: boolean;
}

export interface QuoteCalculationResponse {
    total_internal_cost: string;
    total_client_price: string;
    total_expenses_cost: string;
    total_expenses_client_price: string;
    total_taxes: string;
    total_with_taxes: string;

    margin_percentage: string;
    target_margin_percentage: string | null;

    items: Array<{
        service_id: number;
        service_name: string;
        internal_cost: string;
        client_price: string;
        margin_percentage: string;
        estimated_hours?: number;
        pricing_type: string;
    }>;

    expenses: Array<{
        id?: number;
        name: string;
        cost: string;
        markup_percentage: string;
        client_price: string;
        quantity: string;
        category: string;
    }>;

    taxes: Array<{
        id: number;
        name: string;
        code: string;
        percentage: string;
        amount: string;
    }>;

    revisions_cost: string;
    revisions_included: number;
    revisions_count?: number;
}

export interface BlendedCostRateResponse {
    blended_cost_rate: string;
    total_monthly_costs: string;
    total_fixed_overhead: string;
    total_tools_costs: string;
    total_salaries: string;
    total_monthly_hours: number;
    active_team_members: number;
    primary_currency: string;
    currencies_used: Array<{
        currency: string;
        amount: string;
        exchange_rate: string;
    }>;
    exchange_rates_date: string | null;
}

// Alert Interface for UI State
export interface CalculationAlert {
    type: "PRICE_BELOW_COST" | "LOW_MARGIN" | "OPTIMAL_MARGIN" | "HIGH_MARGIN" | "MISSING_COLOMBIA_TAXES" | "MISSING_HOURS" | "MISSING_FIXED_PRICE";
    message: string;
    severity: "critical" | "warning" | "info" | "success";
    action?: string;
    action_link?: string;
}
