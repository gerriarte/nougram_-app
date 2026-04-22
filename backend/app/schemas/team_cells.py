"""
Schemas for team groups/cells and version publishing.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer

from app.core.pydantic_config import DECIMAL_CONFIG


class TeamGroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str | None = Field(None, max_length=500)
    is_active: bool = True


class TeamGroupCreate(TeamGroupBase):
    pass


class TeamGroupUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    description: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class TeamGroupResponse(TeamGroupBase):
    id: int
    organization_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TeamGroupListResponse(BaseModel):
    items: list[TeamGroupResponse]
    total: int


class TeamCellBase(BaseModel):
    group_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=120)
    description: str | None = Field(None, max_length=500)
    is_active: bool = True


class TeamCellCreate(TeamCellBase):
    pass


class TeamCellUpdate(BaseModel):
    group_id: int | None = Field(None, gt=0)
    name: str | None = Field(None, min_length=1, max_length=120)
    description: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class TeamCellResponse(TeamCellBase):
    id: int
    organization_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TeamCellListResponse(BaseModel):
    items: list[TeamCellResponse]
    total: int


class TeamCellVersionMemberInput(BaseModel):
    team_member_id: int = Field(..., gt=0)
    weight: Decimal = Field(default=Decimal("1.0"), gt=0)
    role_override: str | None = Field(None, max_length=120)
    is_active: bool = True

    @field_serializer("weight")
    def serialize_weight(self, value: Decimal) -> str:
        return str(value)

    model_config = DECIMAL_CONFIG


class TeamCellPublishVersionRequest(BaseModel):
    members: list[TeamCellVersionMemberInput] = Field(default_factory=list, min_items=1)
    notes: str | None = Field(None, max_length=1000)


class TeamCellVersionMemberResponse(BaseModel):
    id: int
    team_member_id: int
    weight: Decimal
    role_override: str | None = None
    is_active: bool = True

    @field_serializer("weight")
    def serialize_weight(self, value: Decimal) -> str:
        return str(value)

    model_config = {**DECIMAL_CONFIG, "from_attributes": True}


class TeamCellVersionResponse(BaseModel):
    id: int
    organization_id: int
    cell_id: int
    version_number: int
    status: str
    notes: str | None = None
    published_at: datetime | None = None
    published_by: int | None = None
    created_at: datetime | None = None
    members: list[TeamCellVersionMemberResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TeamCellVersionListResponse(BaseModel):
    items: list[TeamCellVersionResponse]
    total: int


class CapacityMemberOverviewResponse(BaseModel):
    team_member_id: int
    name: str
    role: str
    capacity_hours: Decimal = Decimal("0")
    tentative_hours: Decimal = Decimal("0")
    committed_hours: Decimal = Decimal("0")
    actual_hours: Decimal = Decimal("0")
    total_hours: Decimal = Decimal("0")
    utilization_ratio: Decimal = Decimal("0")

    @field_serializer(
        "capacity_hours",
        "tentative_hours",
        "committed_hours",
        "actual_hours",
        "total_hours",
        "utilization_ratio",
    )
    def serialize_decimal(self, value: Decimal) -> str:
        return str(value)

    model_config = DECIMAL_CONFIG


class CapacityCellOverviewResponse(BaseModel):
    cell_id: int
    cell_name: str
    tentative_hours: Decimal = Decimal("0")
    committed_hours: Decimal = Decimal("0")
    actual_hours: Decimal = Decimal("0")
    total_hours: Decimal = Decimal("0")

    @field_serializer("tentative_hours", "committed_hours", "actual_hours", "total_hours")
    def serialize_decimal(self, value: Decimal) -> str:
        return str(value)

    model_config = DECIMAL_CONFIG


class CapacityTotalsResponse(BaseModel):
    tentative_hours: Decimal = Decimal("0")
    committed_hours: Decimal = Decimal("0")
    actual_hours: Decimal = Decimal("0")
    total_hours: Decimal = Decimal("0")

    @field_serializer("tentative_hours", "committed_hours", "actual_hours", "total_hours")
    def serialize_decimal(self, value: Decimal) -> str:
        return str(value)

    model_config = DECIMAL_CONFIG


class CapacityOverviewResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    months_count: int
    states: list[str]
    members: list[CapacityMemberOverviewResponse]
    cells: list[CapacityCellOverviewResponse]
    totals: CapacityTotalsResponse
