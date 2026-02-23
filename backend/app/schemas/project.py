"""
Pydantic schemas for Projects
"""
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_serializer
from app.core.pydantic_config import DECIMAL_CONFIG


class ProjectBase(BaseModel):
    """Base schema for projects"""
    name: str = Field(..., description="Project name", min_length=1)
    client_id: Optional[int] = Field(None, description="Client master catalog ID (preferred)")
    client_name: str = Field(..., description="Client name (snapshot or when no client_id)", min_length=1)
    client_email: Optional[str] = Field(None, description="Client email")
    currency: str = Field("USD", description="Currency code (USD, COP, ARS, EUR)")
    tax_ids: Optional[List[int]] = Field(default_factory=list, description="List of tax IDs to apply")


class ProjectCreate(ProjectBase):
    """Schema for creating a project"""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    name: Optional[str] = Field(None, min_length=1)
    client_id: Optional[int] = Field(None, description="Client master catalog ID")
    client_name: Optional[str] = Field(None, min_length=1)
    client_email: Optional[str] = None
    status: Optional[str] = None
    currency: Optional[str] = None
    tax_ids: Optional[List[int]] = Field(None, description="List of tax IDs to apply")


class ProjectResponse(ProjectBase):
    """Schema for project response"""
    id: int
    status: str
    client_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[int] = None
    deleted_by_name: Optional[str] = None
    deleted_by_email: Optional[str] = None
    taxes: Optional[List[dict]] = Field(default_factory=list, description="Applied taxes")

    class Config:
        from_attributes = True


class QuoteResponse(BaseModel):
    """Schema for quote response (without items) - Sprint 16: includes revision fields
    ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
    """
    id: int
    project_id: int
    version: int
    total_internal_cost: Optional[Decimal] = None
    total_client_price: Optional[Decimal] = None
    margin_percentage: Optional[Decimal] = None  # Calculated margin (result)
    target_margin_percentage: Optional[Decimal] = None  # Target margin for the quote (0-1)
    notes: Optional[str] = None
    revisions_included: int = Field(default=2, description="Number of included revisions")
    revision_cost_per_additional: Optional[Decimal] = Field(None, description="Cost per additional revision", ge=0)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer('total_internal_cost', 'total_client_price', 'margin_percentage',
                      'target_margin_percentage', 'revision_cost_per_additional')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[str]:
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
    estimated_hours: Optional[float] = Field(None, description="Estimated hours (required for hourly pricing)", ge=0)
    pricing_type: Optional[str] = Field(None, description="Pricing type: 'hourly', 'fixed', 'recurring', 'project_value' (overrides service default)")
    fixed_price: Optional[Decimal] = Field(None, description="Fixed price (required for fixed pricing)", ge=0)
    quantity: Optional[Decimal] = Field(Decimal('1.0'), description="Quantity for fixed/recurring pricing", ge=0)
    recurring_price: Optional[Decimal] = Field(None, description="Recurring price (required for recurring pricing)", ge=0)
    billing_frequency: Optional[str] = Field(None, description="Billing frequency: 'monthly', 'annual' (for recurring pricing)")
    project_value: Optional[Decimal] = Field(None, description="Project value (for project_value pricing)", ge=0)
    allocations: List['QuoteItemAllocationCreate'] = Field(default_factory=list, description="Resource allocations for this quote item")
    
    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer('fixed_price', 'quantity', 'recurring_price', 'project_value')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[str]:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None
    
    model_config = DECIMAL_CONFIG


class QuoteItemResponse(BaseModel):
    """Schema for quote item response
    ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
    """
    id: int
    service_id: int
    service_name: Optional[str] = None
    estimated_hours: float
    internal_cost: Optional[Decimal] = None
    client_price: Optional[Decimal] = None
    margin_percentage: Optional[Decimal] = None
    pricing_type: Optional[str] = None
    fixed_price: Optional[Decimal] = None
    quantity: Optional[Decimal] = None
    recurring_price: Optional[Decimal] = None
    billing_frequency: Optional[str] = None
    project_value: Optional[Decimal] = None
    allocations: List['QuoteItemAllocationResponse'] = Field(default_factory=list)
    
    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer('internal_cost', 'client_price', 'margin_percentage', 'fixed_price', 'quantity', 'recurring_price', 'project_value')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[str]:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None
    
    model_config = DECIMAL_CONFIG


class QuoteItemAllocationCreate(BaseModel):
    """Schema for creating quote item allocation"""
    team_member_id: int = Field(..., gt=0)
    hours: Decimal = Field(..., gt=0)
    role: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_serializer('hours')
    def serialize_hours(self, value: Optional[Decimal]) -> Optional[str]:
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class QuoteItemAllocationResponse(BaseModel):
    """Schema for quote item allocation response"""
    id: int
    team_member_id: int
    hours: Decimal
    role: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_serializer('hours')
    def serialize_hours(self, value: Optional[Decimal]) -> Optional[str]:
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class ProjectCreateWithQuote(ProjectCreate):
    """Schema for creating a project with initial quote - Sprint 16: includes revision fields"""
    quote_items: List[QuoteItemCreate] = Field(..., description="List of quote items", min_items=1)
    target_margin_percentage: Optional[Decimal] = Field(None, ge=0, le=1, description="Target margin for the quote (0-1, e.g., 0.40 = 40%)")
    revisions_included: Optional[int] = Field(default=2, description="Number of included revisions", ge=0)
    revision_cost_per_additional: Optional[float] = Field(None, description="Cost per additional revision", ge=0)
    allow_low_margin: Optional[bool] = Field(False, description="Allow creating quote even if margin is below threshold")


class QuoteResponseWithItems(QuoteResponse):
    """Schema for quote response with items"""
    items: List[QuoteItemResponse] = Field(default_factory=list)


class QuoteUpdate(BaseModel):
    """Schema for updating a quote - Sprint 16: includes revision fields
    ESTÁNDAR NOUGRAM: Campos monetarios y porcentajes usan Decimal serializado como string
    """
    items: List[QuoteItemCreate] = Field(..., description="List of quote items", min_items=1)
    notes: Optional[str] = Field(None, description="Notes for the quote")
    target_margin_percentage: Optional[Decimal] = Field(None, ge=0, le=1, description="Target margin for the quote (0-1, e.g., 0.40 = 40%)")
    revisions_included: Optional[int] = Field(None, description="Number of included revisions", ge=0)
    revision_cost_per_additional: Optional[Decimal] = Field(None, description="Cost per additional revision", ge=0)
    allow_low_margin: Optional[bool] = Field(False, description="Allow creating quote even if margin is below threshold")
    
    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer('target_margin_percentage', 'revision_cost_per_additional')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[str]:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None
    
    model_config = DECIMAL_CONFIG


class QuoteCreateNewVersion(BaseModel):
    """Schema for creating a new version of a quote - Sprint 16: includes revision fields
    ESTÁNDAR NOUGRAM: Campos monetarios y porcentajes usan Decimal serializado como string
    """
    items: List[QuoteItemCreate] = Field(..., description="List of quote items", min_items=1)
    notes: Optional[str] = Field(None, description="Notes for the new version")
    target_margin_percentage: Optional[Decimal] = Field(None, ge=0, le=1, description="Target margin for the quote (0-1, e.g., 0.40 = 40%)")
    revisions_included: Optional[int] = Field(None, description="Number of included revisions", ge=0)
    revision_cost_per_additional: Optional[Decimal] = Field(None, description="Cost per additional revision", ge=0)
    allow_low_margin: Optional[bool] = Field(False, description="Allow creating quote even if margin is below threshold")
    
    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer('target_margin_percentage', 'revision_cost_per_additional')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[str]:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None
    
    model_config = DECIMAL_CONFIG


class ClientSearchResult(BaseModel):
    """Resultado de búsqueda de cliente"""
    name: str = Field(..., description="Nombre del cliente")
    email: Optional[str] = Field(None, description="Email del cliente")
    project_count: int = Field(..., description="Número de proyectos con este cliente", ge=0)
    last_project_date: Optional[datetime] = Field(None, description="Fecha del último proyecto")
    
    model_config = {"from_attributes": False}  # No es un modelo ORM


class ClientSearchResponse(BaseModel):
    """Respuesta de búsqueda de clientes"""
    clients: List[ClientSearchResult] = Field(..., description="Lista de clientes encontrados")
    total: int = Field(..., description="Total de clientes encontrados", ge=0)


QuoteItemCreate.model_rebuild()
QuoteItemResponse.model_rebuild()