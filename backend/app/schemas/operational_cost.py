"""
Canonical DTOs for operational cost dashboard.
ESTÁNDAR NOUGRAM: Decimal end-to-end; amounts serialized as string in API.
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_serializer


class CalculationMetadataSchema(BaseModel):
    """Metadata for audit and traceability of the operational cost calculation."""

    currency: str = Field(..., description="Primary currency for all amounts")
    period_start: date = Field(..., description="Start of the calculation period (inclusive)")
    period_end: date = Field(..., description="End of the calculation period (inclusive)")
    formula_version: str = Field(default="1.0", description="Version of the calculation formula")
    calculation_id: Optional[str] = Field(None, description="Unique id for log traceability")


class OperationalCostPayloadSchema(BaseModel):
    """
    Canonical payload for GET /dashboard/operational-costs.
    Single source of truth: all amounts in primary currency, Decimal as string in API.
    """

    resource_costs: Decimal = Field(
        default=Decimal("0"),
        description="Total monthly cost of resources (payroll + social charges)",
    )
    fixed_costs: Decimal = Field(
        default=Decimal("0"),
        description="Total monthly fixed/overhead costs (excl. amortization)",
    )
    amortization: Decimal = Field(
        default=Decimal("0"),
        description="Total monthly depreciation/amortization of assets",
    )
    tax_costs: Decimal = Field(
        default=Decimal("0"),
        description="Tax-related operational cost (e.g. withholdings) if applicable",
    )
    total_operational_cost: Decimal = Field(
        default=Decimal("0"),
        description="resource_costs + fixed_costs + amortization + tax_costs",
    )
    target_margin_configured: Optional[Decimal] = Field(
        None,
        description="Target margin used when quoting (0-1, e.g. 0.40 = 40%)",
    )
    effective_margin_observed: Optional[Decimal] = Field(
        None,
        description="Effective margin from Won quotes in period; (revenue - cost) / revenue",
    )
    calculation_metadata: CalculationMetadataSchema = Field(
        ...,
        description="Currency, period, formula version, calculation_id",
    )
    data_integrity_ok: bool = Field(
        default=True,
        description="True if required data for the period is complete (no missing amortization etc.)",
    )

    model_config = {"from_attributes": True}

    @field_serializer(
        "resource_costs",
        "fixed_costs",
        "amortization",
        "tax_costs",
        "total_operational_cost",
        "target_margin_configured",
        "effective_margin_observed",
    )
    def serialize_decimal_as_str(self, value: Optional[Decimal]) -> Optional[str]:
        if value is None:
            return None
        return str(value)
