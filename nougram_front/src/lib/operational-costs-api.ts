/**
 * API for operational cost dashboard.
 * Single source of truth: all metrics come from backend; no client-side financial logic.
 */

import { apiRequest } from "@/lib/api-client";

export interface CalculationMetadata {
  currency: string;
  period_start: string;
  period_end: string;
  formula_version: string;
  calculation_id: string | null;
}

export interface OperationalCostPayload {
  resource_costs: string;
  fixed_costs: string;
  amortization: string;
  tax_costs: string;
  total_operational_cost: string;
  target_margin_configured: string | null;
  effective_margin_observed: string | null;
  calculation_metadata: CalculationMetadata;
  data_integrity_ok: boolean;
}

export async function fetchOperationalCosts(
  period: "current_month" = "current_month"
): Promise<{ data?: OperationalCostPayload; error?: string; statusCode?: number }> {
  return apiRequest<OperationalCostPayload>(
    `dashboard/operational-costs?period=${period}`
  );
}
