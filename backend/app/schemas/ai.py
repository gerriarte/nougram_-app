"""
Schemas for AI-powered configuration assistance
"""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_serializer

from app.core.pydantic_config import DECIMAL_CONFIG
from app.schemas.cost import CostFixedCreate
from app.schemas.service import ServiceCreate
from app.schemas.team import TeamMemberCreate


class OnboardingSuggestionRequest(BaseModel):
    """Request for AI-powered onboarding suggestions"""

    industry: str = Field(
        ..., description="Industry type (e.g., 'Marketing Digital', 'Desarrollo Web')"
    )
    region: str = Field(default="US", description="Region code (e.g., 'US', 'CO', 'MX')")
    currency: str = Field(default="USD", description="Primary currency")
    custom_context: str | None = Field(None, description="Additional context about the business")


class OnboardingSuggestionResponse(BaseModel):
    """Response with AI-generated onboarding suggestions"""

    suggested_roles: list[TeamMemberCreate] = Field(
        default_factory=list, description="Suggested team members"
    )
    suggested_services: list[ServiceCreate] = Field(
        default_factory=list, description="Suggested services"
    )
    suggested_fixed_costs: list[CostFixedCreate] = Field(
        default_factory=list, description="Suggested fixed costs"
    )
    confidence_scores: dict[str, float] = Field(
        default_factory=dict, description="Confidence scores for each suggestion category"
    )
    reasoning: str | None = Field(None, description="AI reasoning for the suggestions")


class DocumentParseRequest(BaseModel):
    """Request for parsing unstructured document data"""

    text: str = Field(..., description="Text content from document (PDF, CSV, etc.)")
    document_type: str | None = Field(
        None, description="Type of document: 'payroll', 'expenses', 'mixed'"
    )


class DocumentParseResponse(BaseModel):
    """Response with parsed structured data from document"""

    team_members: list[TeamMemberCreate] = Field(
        default_factory=list, description="Extracted team members"
    )
    fixed_costs: list[CostFixedCreate] = Field(
        default_factory=list, description="Extracted fixed costs"
    )
    subscriptions: list[dict] = Field(default_factory=list, description="Extracted subscriptions")
    confidence_scores: dict[str, float] = Field(
        default_factory=dict, description="Confidence scores for extracted data"
    )
    warnings: list[str] = Field(default_factory=list, description="Warnings about parsing issues")


class NaturalLanguageCommandRequest(BaseModel):
    """Request for processing natural language configuration commands"""

    command: str = Field(
        ...,
        description="Natural language command (e.g., 'Añade un Senior Designer que gana 45k anuales')",
    )
    context: dict | None = Field(None, description="Current configuration context")


class NaturalLanguageCommandResponse(BaseModel):
    """Response with structured action from natural language command"""

    action_type: str = Field(
        ..., description="Type of action: 'add_team_member', 'add_service', 'add_fixed_cost', etc."
    )
    action_data: dict = Field(..., description="Structured data for the action")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score for the parsed command"
    )
    requires_confirmation: bool = Field(
        default=True, description="Whether user confirmation is required"
    )
    reasoning: str | None = Field(None, description="AI reasoning for the parsed command")


class ExecutiveSummaryService(BaseModel):
    """Servicio para resumen ejecutivo"""

    service_id: int = Field(..., description="ID del servicio", gt=0)
    service_name: str = Field(..., description="Nombre del servicio", min_length=1)
    estimated_hours: float | None = Field(None, description="Horas estimadas", ge=0)
    client_price: Decimal = Field(..., description="Precio al cliente", gt=0)

    @field_serializer("client_price")
    def serialize_decimal(self, value: Decimal) -> str:
        return str(value)

    model_config = DECIMAL_CONFIG


class ExecutiveSummaryRequest(BaseModel):
    """Request para generar resumen ejecutivo"""

    project_name: str = Field(..., description="Nombre del proyecto", min_length=1)
    client_name: str = Field(..., description="Nombre del cliente", min_length=1)
    client_sector: str | None = Field(
        None, description="Sector del cliente (ej: 'Tecnología', 'Retail')"
    )
    services: list[ExecutiveSummaryService] = Field(
        ..., description="Lista de servicios incluidos", min_items=1
    )
    total_price: Decimal = Field(..., description="Precio total de la cotización", gt=0)
    currency: str = Field("USD", description="Moneda", min_length=3, max_length=3)
    language: str = Field("es", description="Idioma del resumen: 'es' o 'en'", pattern="^(es|en)$")

    @field_serializer("total_price")
    def serialize_decimal(self, value: Decimal) -> str:
        return str(value)

    model_config = DECIMAL_CONFIG


class ExecutiveSummaryResponse(BaseModel):
    """Response con resumen ejecutivo generado"""

    summary: str = Field(..., description="Resumen ejecutivo generado")
    provider: str = Field("openai", description="Proveedor de IA utilizado")
    usage: dict[str, Any] | None = Field(
        None, description="Información de uso de la API (tokens, costo estimado)"
    )
