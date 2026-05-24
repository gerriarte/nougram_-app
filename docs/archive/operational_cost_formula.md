# Operational Cost Dashboard Formula (Current Month)

This document defines the canonical backend formula used by `GET /api/v1/dashboard/operational-costs`.

## Scope

- Period: current month (`period=current_month`)
- Source of truth: backend only
- Currency: normalized to tenant primary currency (`organization.settings.primary_currency`, fallback `USD`)
- Precision: `Decimal` end-to-end, serialized as strings in API

## Canonical Metrics

- `resource_costs`: Sum of active team salaries plus social charges multiplier.
- `fixed_costs`: Sum of active fixed costs (`costs_fixed`), excluding amortization.
- `amortization`: Sum of monthly depreciation for active assets:
  - `monthly = (purchase_price - salvage_value) / useful_life_months`
- `tax_costs`: Sum of applicable tax amounts for Won projects in period:
  - `tax_amount = quote.total_client_price * (tax.percentage / 100)`
- `total_operational_cost`:
  - `resource_costs + fixed_costs + amortization + tax_costs`
- `target_margin_configured`:
  - `organization.settings.quote_default_margin`
  - fallback: average `service.default_margin_target` (active services)
- `effective_margin_observed`:
  - For Won projects in period: `(sum(revenue) - sum(cost)) / sum(revenue)`
  - Revenue/cost normalized to primary currency before aggregation.

## Data Integrity Rules

- Negative salary, fixed cost, or amortization inputs are rejected as domain errors.
- Amortization records with invalid life (`<= 0`) or non-positive monthly result are skipped and mark `data_integrity_ok = false`.
- Tax percentages must be non-negative.

## Response Metadata

- `calculation_metadata.currency`
- `calculation_metadata.period_start`
- `calculation_metadata.period_end`
- `calculation_metadata.formula_version`
- `calculation_metadata.calculation_id` (trace id for logs)

## Observability

Structured logs include:

- `level`
- `module`
- `function`
- `calculation_id`

This allows correlating endpoint responses with calculation events in logs.
