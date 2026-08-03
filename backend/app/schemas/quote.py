"""
Pydantic schemas for Quotes
ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
"""

from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer

from app.core.pydantic_config import DECIMAL_CONFIG


class MarginSummary(BaseModel):
    """Canonical margin contract using ratio scale (0-1)."""

    gross_margin_ratio: Decimal | None = Field(None, description="Gross margin before taxes (0-1)")
    net_margin_ratio: Decimal | None = Field(None, description="Net margin after taxes (0-1)")
    target_margin_ratio: Decimal | None = Field(None, description="Target margin (0-1)")
    tax_burden_ratio: Decimal | None = Field(
        None, description="Tax burden as share of client price (0-1)"
    )
    scale: str = Field(default="ratio_0_1", description="Scale used for ratio fields")

    @field_serializer(
        "gross_margin_ratio", "net_margin_ratio", "target_margin_ratio", "tax_burden_ratio"
    )
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class QuoteItemBase(BaseModel):
    """Base schema for quote items (Sprint 14: supports multiple pricing types)
    ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
    """

    service_id: int = Field(..., description="Service ID", gt=0)
    custom_service_name: str | None = Field(
        None, description="User-defined service label for this quote item"
    )
    description: str | None = Field(
        None, description="Scope detail for this item, shown in the client proposal"
    )
    estimated_hours: float | None = Field(
        None, description="Estimated hours (required for hourly pricing)", ge=0
    )
    pricing_type: str | None = Field(
        None,
        description="Pricing type: 'hourly', 'fixed', 'recurring', 'project_value' (overrides service default)",
    )
    fixed_price: Decimal | None = Field(
        None, description="Fixed price (required for fixed pricing)", ge=0
    )
    quantity: Decimal | None = Field(
        Decimal("1.0"), description="Quantity for fixed/recurring pricing", ge=0
    )
    recurring_price: Decimal | None = Field(
        None, description="Recurring price (required for recurring pricing)", ge=0
    )
    billing_frequency: str | None = Field(
        None, description="Billing frequency: 'monthly', 'annual' (for recurring pricing)"
    )
    project_value: Decimal | None = Field(
        None, description="Project value (for project_value pricing)", ge=0
    )
    client_price_override: Decimal | None = Field(
        None,
        description="Manual client price set by the user; overrides the derived price",
        ge=0,
    )

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer(
        "fixed_price", "quantity", "recurring_price", "project_value", "client_price_override"
    )
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class QuoteItemCreate(QuoteItemBase):
    """Schema for creating a quote item"""

    pass


class QuoteItemResponse(QuoteItemBase):
    """Schema for quote item response"""

    id: int
    service_name: str | None = None
    internal_cost: float | None = None
    client_price: float | None = None
    margin_percentage: float | None = None

    class Config:
        from_attributes = True


class QuoteExpenseBase(BaseModel):
    """Base schema for quote expenses (Sprint 15: third-party costs with markup)
    ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
    """

    name: str = Field(..., description="Expense name", min_length=1)
    description: str | None = Field(None, description="Expense description")
    cost: Decimal = Field(..., description="Real cost", ge=0)
    markup_percentage: Decimal = Field(
        Decimal("0.0"), description="Mark-up percentage (0.10 = 10%)", ge=0, le=10
    )
    category: str | None = Field(
        None, description="Category: 'Third Party', 'Materials', 'Licenses'"
    )
    quantity: Decimal = Field(Decimal("1.0"), description="Quantity", ge=0)

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer("cost", "markup_percentage", "quantity")
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class QuoteExpenseCreate(QuoteExpenseBase):
    """Schema for creating a quote expense"""

    pass


class QuoteExpenseResponse(QuoteExpenseBase):
    """Schema for quote expense response
    ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
    """

    id: int
    quote_id: int
    client_price: Decimal = Field(..., description="Client price (cost * quantity * (1 + markup))")
    created_at: str | None = None

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer("client_price", "cost")
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class QuoteCalculateRequest(BaseModel):
    """Schema for quote calculation request (Sprint 16: includes expenses and revisions)
    ESTÁNDAR NOUGRAM: Campos monetarios y porcentajes usan Decimal serializado como string
    """

    items: list[QuoteItemBase] = Field(..., description="List of quote items")
    expenses: list[QuoteExpenseBase] | None = Field(
        default_factory=list, description="List of quote expenses (third-party costs)"
    )
    tax_ids: list[int] | None = Field(default_factory=list, description="List of tax IDs to apply")
    target_margin_percentage: Decimal | None = Field(
        None,
        ge=0,
        le=1,
        description="Target margin for the quote (0-1, e.g., 0.40 = 40%). If not provided, uses service default margins.",
    )
    revisions_included: int | None = Field(
        default=2, description="Number of included revisions", ge=0
    )
    revision_cost_per_additional: Decimal | None = Field(
        None, description="Cost per additional revision", ge=0
    )
    revisions_count: int | None = Field(
        None, description="Actual number of revisions requested (for calculation)", ge=0
    )
    contingency_type: str | None = Field(
        None, description="Contingency type: 'fixed' | 'percentage'"
    )
    contingency_value: Decimal | None = Field(
        None, ge=0, description="Contingency amount (fixed) or percentage (e.g. 10 = 10%)"
    )

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer(
        "target_margin_percentage", "revision_cost_per_additional", "contingency_value"
    )
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class QuoteCalculateResponse(BaseModel):
    """Schema for quote calculation response (Sprint 16: includes expenses and revisions breakdown)
    ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
    """

    total_internal_cost: Decimal = Field(
        ..., description="Total internal cost (services + expenses cost)"
    )
    total_client_price: Decimal = Field(..., description="Total client price (before taxes)")
    total_expenses_cost: Decimal = Field(
        default=Decimal("0"), description="Total expenses cost (before markup)"
    )
    total_expenses_client_price: Decimal = Field(
        default=Decimal("0"), description="Total expenses client price (with markup)"
    )
    total_taxes: Decimal = Field(default=Decimal("0"), description="Total taxes amount")
    total_with_taxes: Decimal = Field(
        default=Decimal("0"), description="Total client price with taxes"
    )
    margin_percentage: Decimal = Field(..., description="Legacy gross margin ratio (0-1)")
    target_margin_percentage: Decimal | None = Field(
        None, description="Legacy target margin ratio (0-1)"
    )
    margin: MarginSummary | None = Field(
        default=None, description="Canonical margin contract (0-1 ratios)"
    )
    items: list[dict] = Field(default_factory=list, description="Calculated items")
    expenses: list[dict] = Field(default_factory=list, description="Calculated expenses breakdown")
    taxes: list[dict] = Field(default_factory=list, description="Applied taxes breakdown")
    revisions_cost: Decimal = Field(
        default=Decimal("0"), description="Additional cost for revisions beyond included count"
    )
    revisions_included: int = Field(default=2, description="Number of included revisions")
    revisions_count: int | None = Field(None, description="Actual number of revisions requested")
    contingency_amount: Decimal = Field(
        default=Decimal("0"), description="Resolved contingency amount added to client price"
    )

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer(
        "total_internal_cost",
        "total_client_price",
        "total_expenses_cost",
        "total_expenses_client_price",
        "total_taxes",
        "total_with_taxes",
        "margin_percentage",
        "target_margin_percentage",
        "revisions_cost",
        "contingency_amount",
    )
    def serialize_decimal(self, value: Decimal) -> str:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class CurrencyInfo(BaseModel):
    """Schema for currency information
    ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
    """

    code: str = Field(..., description="Currency code")
    count: int = Field(..., description="Number of costs/team members using this currency")
    exchange_rate_to_primary: Decimal = Field(..., description="Exchange rate to primary currency")
    total_amount: Decimal = Field(..., description="Total amount in this currency")

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer("exchange_rate_to_primary", "total_amount")
    def serialize_decimal(self, value: Decimal) -> str:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class BlendedCostRateResponse(BaseModel):
    """Schema for blended cost rate response
    ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
    """

    blended_cost_rate: Decimal = Field(..., description="Blended cost rate per hour")
    total_monthly_costs: Decimal = Field(
        ..., description="Total monthly costs (normalized to primary currency)"
    )
    total_fixed_overhead: Decimal = Field(
        Decimal("0"), description="Total fixed overhead (Rent, Utilities, etc.)"
    )
    total_tools_costs: Decimal = Field(Decimal("0"), description="Total software and tools costs")
    total_salaries: Decimal = Field(
        Decimal("0"), description="Total salaries (Resources) with social charges"
    )
    total_monthly_hours: float = Field(..., description="Total monthly billable hours")
    active_team_members: int = Field(..., description="Number of active team members")
    primary_currency: str = Field(..., description="Primary currency code")
    currencies_used: list[CurrencyInfo] = Field(
        default_factory=list, description="List of currencies used in costs"
    )
    exchange_rates_date: str | None = Field(None, description="Date of exchange rates (ISO format)")

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer(
        "blended_cost_rate",
        "total_monthly_costs",
        "total_fixed_overhead",
        "total_tools_costs",
        "total_salaries",
    )
    def serialize_decimal(self, value: Decimal) -> str:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class QuoteEmailRequest(BaseModel):
    """Schema for sending quote by email"""

    to_email: str = Field(..., description="Recipient email address")
    subject: str | None = Field(
        None, description="Email subject (optional, will be auto-generated if not provided)"
    )
    message: str | None = Field(None, description="Additional message to include in email body")
    proposal_id: int | None = Field(
        None, description="Optional proposal document ID to use as proposal body"
    )
    proposal_message: str | None = Field(
        None, description="Optional proposal plain text/body override"
    )
    cc: list[str] | None = Field(default_factory=list, description="CC email addresses")
    bcc: list[str] | None = Field(default_factory=list, description="BCC email addresses")
    include_pdf: bool = Field(True, description="Include PDF attachment")
    include_docx: bool = Field(False, description="Include DOCX attachment")


class QuoteEmailResponse(BaseModel):
    """Schema for quote email response"""

    success: bool = Field(..., description="Whether the email was sent successfully")
    message: str = Field(..., description="Response message")


class RentabilityCategory(BaseModel):
    """Schema for a rentability category breakdown
    ESTÁNDAR NOUGRAM: Campos monetarios y porcentajes usan Decimal serializado como string
    """

    category: str = Field(..., description="Category name (e.g., 'Operating Costs', 'Net Profit')")
    concept: str = Field(..., description="Concept/Sub-category (e.g., 'Talent', 'Taxes')")
    amount: Decimal = Field(..., description="Amount in primary currency")
    percentage: Decimal = Field(..., description="Percentage relative to total client price")
    description: str | None = Field(None, description="Optional description or detail")

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer("amount", "percentage")
    def serialize_decimal(self, value: Decimal) -> str:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class RentabilitySummaryResponse(BaseModel):
    """Schema for the full profitability summary response
    ESTÁNDAR NOUGRAM: Campos monetarios y porcentajes usan Decimal serializado como string
    """

    quote_id: int
    total_client_price: Decimal = Field(..., description="Total client price")
    total_internal_cost: Decimal = Field(..., description="Total internal cost")
    total_taxes: Decimal = Field(..., description="Total taxes")
    net_profit_amount: Decimal = Field(..., description="Net profit amount")
    net_profit_margin: Decimal = Field(..., description="Legacy net margin percentage (0-100)")
    margin: MarginSummary | None = Field(
        default=None, description="Canonical margin contract (0-1 ratios)"
    )
    categories: list[RentabilityCategory] = Field(
        default_factory=list, description="Detailed breakdown categories"
    )
    status: str = Field(
        ..., description="Profitability status: healthy (>30%), warning (15-30%), critical (<15%)"
    )

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer(
        "total_client_price",
        "total_internal_cost",
        "total_taxes",
        "net_profit_amount",
        "net_profit_margin",
    )
    def serialize_decimal(self, value: Decimal) -> str:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG
