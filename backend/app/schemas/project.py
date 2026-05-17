"""
Pydantic schemas for Projects
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from app.core.pydantic_config import DECIMAL_CONFIG
from app.schemas.quote import MarginSummary, QuoteExpenseCreate, QuoteExpenseResponse


class ProjectBase(BaseModel):
    """Base schema for projects"""

    name: str = Field(..., description="Project name", min_length=1)
    client_id: int | None = Field(None, description="Client master catalog ID (preferred)")
    client_name: str = Field(
        ..., description="Client name (snapshot or when no client_id)", min_length=1
    )
    client_email: str | None = Field(None, description="Client email")
    currency: str = Field("USD", description="Currency code (USD, COP, ARS, EUR, PEN, MXN)")
    tax_ids: list[int] | None = Field(default_factory=list, description="List of tax IDs to apply")


class ProjectCreate(ProjectBase):
    """Schema for creating a project"""

    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""

    name: str | None = Field(None, min_length=1)
    client_id: int | None = Field(None, description="Client master catalog ID")
    client_name: str | None = Field(None, min_length=1)
    client_email: str | None = None
    status: str | None = None
    currency: str | None = None
    tax_ids: list[int] | None = Field(None, description="List of tax IDs to apply")


class ProjectResponse(ProjectBase):
    """Schema for project response"""

    id: int
    status: str
    client_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    deleted_by_id: int | None = None
    deleted_by_name: str | None = None
    deleted_by_email: str | None = None
    taxes: list[dict] | None = Field(default_factory=list, description="Applied taxes")

    class Config:
        from_attributes = True


class QuoteResponse(BaseModel):
    """Schema for quote response (without items) - Sprint 16: includes revision fields
    ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
    """

    id: int
    project_id: int
    version: int
    total_internal_cost: Decimal | None = None
    total_client_price: Decimal | None = None
    total_taxes: Decimal | None = None
    total_with_taxes: Decimal | None = None
    margin_percentage: Decimal | None = None  # Calculated margin (result)
    target_margin_percentage: Decimal | None = None  # Target margin for the quote (0-1)
    margin: MarginSummary | None = Field(
        default=None, description="Canonical margin contract (0-1 ratios)"
    )
    contingency_description: str | None = Field(None, description="Contingency description")
    contingency_type: str | None = Field(None, description="Contingency type: fixed|percentage")
    contingency_value: Decimal | None = Field(None, description="Contingency value")
    notes: str | None = None
    is_active: bool = True
    deletion_requested_at: datetime | None = None
    deletion_requested_by_id: int | None = None
    deletion_request_reason: str | None = None
    revisions_included: int = Field(default=2, description="Number of included revisions")
    revision_cost_per_additional: Decimal | None = Field(
        None, description="Cost per additional revision", ge=0
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer(
        "total_internal_cost",
        "total_client_price",
        "total_taxes",
        "total_with_taxes",
        "margin_percentage",
        "target_margin_percentage",
        "revision_cost_per_additional",
        "contingency_value",
    )
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class ProjectListResponse(BaseModel):
    """Schema for list of projects"""

    items: list[ProjectResponse]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1


class QuoteItemCreate(BaseModel):
    """Schema for creating a quote item (Sprint 14: supports multiple pricing types)
    ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
    """

    service_id: int = Field(..., description="Service ID", gt=0)
    custom_service_name: str | None = Field(
        None, description="User-defined service label for this quote item"
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
    allocations: list["QuoteItemAllocationCreate"] = Field(
        default_factory=list, description="Resource allocations for this quote item"
    )
    cell_assignment: Optional["QuoteItemCellAssignmentCreate"] = Field(
        None,
        description="Optional cell-based assignment; expanded to member allocations server-side",
    )

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer("fixed_price", "quantity", "recurring_price", "project_value")
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class QuoteItemResponse(BaseModel):
    """Schema for quote item response
    ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
    """

    id: int
    service_id: int
    service_name: str | None = None
    custom_service_name: str | None = None
    estimated_hours: float | None = None
    internal_cost: Decimal | None = None
    client_price: Decimal | None = None
    margin_percentage: Decimal | None = None
    pricing_type: str | None = None
    fixed_price: Decimal | None = None
    quantity: Decimal | None = None
    recurring_price: Decimal | None = None
    billing_frequency: str | None = None
    project_value: Decimal | None = None
    allocations: list["QuoteItemAllocationResponse"] = Field(default_factory=list)
    cell_assignment: Optional["QuoteItemCellAssignmentResponse"] = None

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer(
        "internal_cost",
        "client_price",
        "margin_percentage",
        "fixed_price",
        "quantity",
        "recurring_price",
        "project_value",
    )
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class QuoteItemAllocationCreate(BaseModel):
    """Schema for creating quote item allocation"""

    team_member_id: int = Field(..., gt=0)
    hours: Decimal = Field(..., gt=0)
    role: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None

    @field_serializer("hours")
    def serialize_hours(self, value: Decimal | None) -> str | None:
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class QuoteItemAllocationResponse(BaseModel):
    """Schema for quote item allocation response"""

    id: int
    team_member_id: int
    hours: Decimal
    role: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None

    @field_serializer("hours")
    def serialize_hours(self, value: Decimal | None) -> str | None:
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class QuoteItemCellAssignmentCreate(BaseModel):
    """Schema for assigning a staffing cell to a quote item"""

    cell_id: int = Field(..., gt=0)
    cell_version_id: int | None = Field(
        None, gt=0, description="Optional explicit version; defaults to latest"
    )
    occupancy_percentage: Decimal = Field(
        ..., gt=0, le=100, description="Cell occupancy percentage (0-100)"
    )
    duration_months: int | None = Field(1, ge=1, le=60)

    @field_serializer("occupancy_percentage")
    def serialize_occupancy(self, value: Decimal | None) -> str | None:
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class QuoteItemCellAssignmentResponse(BaseModel):
    """Schema for quote item cell assignment response"""

    id: int
    cell_id: int
    cell_version_id: int
    occupancy_percentage: Decimal
    duration_months: int

    @field_serializer("occupancy_percentage")
    def serialize_occupancy(self, value: Decimal | None) -> str | None:
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class ProjectCreateWithQuote(ProjectCreate):
    """Schema for creating a project with initial quote - Sprint 16: includes revision fields"""

    quote_items: list[QuoteItemCreate] = Field(..., description="List of quote items", min_items=1)
    target_margin_percentage: Decimal | None = Field(
        None, ge=0, le=1, description="Target margin for the quote (0-1, e.g., 0.40 = 40%)"
    )
    contingency_description: str | None = Field(None, description="Contingency description")
    contingency_type: str | None = Field(None, description="Contingency type: fixed|percentage")
    contingency_value: Decimal | None = Field(None, ge=0, description="Contingency value")
    revisions_included: int | None = Field(
        default=2, description="Number of included revisions", ge=0
    )
    revision_cost_per_additional: float | None = Field(
        None, description="Cost per additional revision", ge=0
    )
    allow_low_margin: bool | None = Field(
        False, description="Allow creating quote even if margin is below threshold"
    )


class QuoteResponseWithItems(QuoteResponse):
    """Schema for quote response with items"""

    items: list[QuoteItemResponse] = Field(default_factory=list)
    expenses: list[QuoteExpenseResponse] = Field(default_factory=list)


class QuoteUpdate(BaseModel):
    """Schema for updating a quote - Sprint 16: includes revision fields
    ESTÁNDAR NOUGRAM: Campos monetarios y porcentajes usan Decimal serializado como string
    """

    items: list[QuoteItemCreate] = Field(..., description="List of quote items", min_items=1)
    notes: str | None = Field(None, description="Notes for the quote")
    target_margin_percentage: Decimal | None = Field(
        None, ge=0, le=1, description="Target margin for the quote (0-1, e.g., 0.40 = 40%)"
    )
    contingency_description: str | None = Field(None, description="Contingency description")
    contingency_type: str | None = Field(None, description="Contingency type: fixed|percentage")
    contingency_value: Decimal | None = Field(None, ge=0, description="Contingency value")
    revisions_included: int | None = Field(None, description="Number of included revisions", ge=0)
    revision_cost_per_additional: Decimal | None = Field(
        None, description="Cost per additional revision", ge=0
    )
    allow_low_margin: bool | None = Field(
        False, description="Allow creating quote even if margin is below threshold"
    )
    expenses: list[QuoteExpenseCreate] | None = Field(
        default=None, description="Vendor/third-party expenses (replaces all existing when provided)"
    )

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer(
        "target_margin_percentage", "revision_cost_per_additional", "contingency_value"
    )
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class QuoteCreateNewVersion(BaseModel):
    """Schema for creating a new version of a quote - Sprint 16: includes revision fields
    ESTÁNDAR NOUGRAM: Campos monetarios y porcentajes usan Decimal serializado como string
    """

    items: list[QuoteItemCreate] = Field(..., description="List of quote items", min_items=1)
    notes: str | None = Field(None, description="Notes for the new version")
    target_margin_percentage: Decimal | None = Field(
        None, ge=0, le=1, description="Target margin for the quote (0-1, e.g., 0.40 = 40%)"
    )
    contingency_description: str | None = Field(None, description="Contingency description")
    contingency_type: str | None = Field(None, description="Contingency type: fixed|percentage")
    contingency_value: Decimal | None = Field(None, ge=0, description="Contingency value")
    revisions_included: int | None = Field(None, description="Number of included revisions", ge=0)
    revision_cost_per_additional: Decimal | None = Field(
        None, description="Cost per additional revision", ge=0
    )
    allow_low_margin: bool | None = Field(
        False, description="Allow creating quote even if margin is below threshold"
    )

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer(
        "target_margin_percentage", "revision_cost_per_additional", "contingency_value"
    )
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class ClientSearchResult(BaseModel):
    """Resultado de búsqueda de cliente"""

    name: str = Field(..., description="Nombre del cliente")
    email: str | None = Field(None, description="Email del cliente")
    project_count: int = Field(..., description="Número de proyectos con este cliente", ge=0)
    last_project_date: datetime | None = Field(None, description="Fecha del último proyecto")

    model_config = {"from_attributes": False}  # No es un modelo ORM


class ClientSearchResponse(BaseModel):
    """Respuesta de búsqueda de clientes"""

    clients: list[ClientSearchResult] = Field(..., description="Lista de clientes encontrados")
    total: int = Field(..., description="Total de clientes encontrados", ge=0)


QuoteItemCreate.model_rebuild()
QuoteItemResponse.model_rebuild()
