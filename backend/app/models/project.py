"""
Project and quote models
"""

import enum

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base

# Association table for many-to-many relationship between Project and Tax
project_taxes = Table(
    "project_taxes",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("tax_id", Integer, ForeignKey("taxes.id"), primary_key=True),
)


class ProjectStatus(enum.StrEnum):
    """Project status enumeration"""

    DRAFT = "Draft"
    SENT = "Sent"
    WON = "Won"
    LOST = "Lost"


class Project(Base):
    """
    Project model
    """

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    client_name = Column(String, nullable=False)
    client_email = Column(String, nullable=True)
    status = Column(String, default="Draft")
    currency = Column(String, default="USD")  # USD, COP, ARS, EUR
    # Provenance: NULL = created manually, "quote_agent" = created by the AI quote agent.
    source = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Soft delete fields
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Multi-tenant: organization relationship
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    # Client master catalog (nullable; client_name/client_email kept for snapshot/compat)
    client_id = Column(
        Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # The quote version accepted by the client when the project is Won. Drives
    # committed revenue and resource utilization in the dashboard. Nullable FK.
    accepted_quote_id = Column(
        Integer,
        ForeignKey("quotes.id", use_alter=True, name="fk_projects_accepted_quote"),
        nullable=True,
    )

    # Relationships
    client = relationship("Client", backref="projects")
    quotes = relationship(
        "Quote",
        back_populates="project",
        cascade="all, delete-orphan",
        foreign_keys="Quote.project_id",
    )
    taxes = relationship("Tax", secondary="project_taxes", back_populates="projects")
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])


class Quote(Base):
    """
    Quote model for projects
    """

    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    version = Column(Integer, default=1)
    total_internal_cost = Column(
        Numeric(precision=19, scale=4), nullable=True
    )  # ESTÁNDAR NOUGRAM: Numeric
    total_client_price = Column(
        Numeric(precision=19, scale=4), nullable=True
    )  # ESTÁNDAR NOUGRAM: Numeric
    margin_percentage = Column(
        Numeric(precision=10, scale=4), nullable=True
    )  # Calculated margin (result) - ESTÁNDAR NOUGRAM: Numeric
    target_margin_percentage = Column(
        Numeric(precision=10, scale=4), nullable=True
    )  # Target margin - ESTÁNDAR NOUGRAM: Numeric (0-1, e.g., 0.40 = 40%)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Sprint 16: Revision fields
    revisions_included = Column(Integer, default=2, nullable=False)  # Number of included revisions
    revision_cost_per_additional = Column(
        Numeric(precision=19, scale=4), nullable=True
    )  # ESTÁNDAR NOUGRAM: Numeric  # Cost per additional revision
    contingency_description = Column(String, nullable=True)
    contingency_type = Column(String, nullable=True)  # fixed | percentage
    contingency_value = Column(Numeric(precision=19, scale=4), nullable=True)
    is_active = Column(Integer, nullable=False, default=1, server_default="1", index=True)
    deletion_requested_at = Column(DateTime(timezone=True), nullable=True)
    deletion_requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    deletion_request_reason = Column(String, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="quotes", foreign_keys=[project_id])
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")
    expenses = relationship("QuoteExpense", back_populates="quote", cascade="all, delete-orphan")
    deletion_requested_by = relationship("User", foreign_keys=[deletion_requested_by_id])


class QuoteItem(Base):
    """
    Quote item model (individual service in a quote)
    """

    __tablename__ = "quote_items"

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    estimated_hours = Column(
        Numeric(precision=10, scale=4), nullable=True
    )  # ESTÁNDAR NOUGRAM: Numeric - Nullable for fixed/recurring pricing
    internal_cost = Column(
        Numeric(precision=19, scale=4), nullable=True
    )  # ESTÁNDAR NOUGRAM: Numeric
    client_price = Column(
        Numeric(precision=19, scale=4), nullable=True
    )  # ESTÁNDAR NOUGRAM: Numeric
    margin_percentage = Column(
        Numeric(precision=10, scale=4), nullable=True
    )  # ESTÁNDAR NOUGRAM: Numeric

    # Pricing type fields (Sprint 14) - Can override service pricing_type
    pricing_type = Column(
        String, nullable=True
    )  # Overrides service pricing_type: "hourly", "fixed", "recurring", "project_value"
    custom_service_name = Column(
        String, nullable=True
    )  # User-defined service label persisted with the quote item
    description = Column(
        Text, nullable=True
    )  # Alcance del ítem: qué incluye, para que un tercero entienda la cotización
    client_price_override = Column(
        Numeric(precision=19, scale=4), nullable=True
    )  # Precio manual fijado por el usuario; pisa el precio derivado de costo × margen
    fixed_price = Column(
        Numeric(precision=19, scale=4), nullable=True
    )  # If pricing_type = "fixed" - ESTÁNDAR NOUGRAM: Numeric
    quantity = Column(
        Numeric(precision=10, scale=4), default=1.0
    )  # ESTÁNDAR NOUGRAM: Numeric - For modules/milestones (fixed pricing)
    recurring_price = Column(
        Numeric(precision=19, scale=4), nullable=True
    )  # If pricing_type = "recurring"
    billing_frequency = Column(String, nullable=True)  # monthly, annual
    project_value = Column(
        Numeric(precision=19, scale=4), nullable=True
    )  # If pricing_type = "project_value"

    # Relationships
    quote = relationship("Quote", back_populates="items")
    service = relationship("Service")
    allocations = relationship(
        "QuoteItemAllocation", back_populates="quote_item", cascade="all, delete-orphan"
    )
    cell_assignment = relationship(
        "QuoteItemCellAssignment",
        back_populates="quote_item",
        cascade="all, delete-orphan",
        uselist=False,
    )


class QuoteItemAllocation(Base):
    """
    Resource allocation for a quote item
    """

    __tablename__ = "quote_item_allocations"

    id = Column(Integer, primary_key=True, index=True)
    quote_item_id = Column(
        Integer, ForeignKey("quote_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    team_member_id = Column(
        Integer, ForeignKey("team_members.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    hours = Column(Numeric(precision=10, scale=4), nullable=False)
    role = Column(String, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    quote_item = relationship("QuoteItem", back_populates="allocations")
    team_member = relationship("TeamMember")


class QuoteItemCellAssignment(Base):
    """
    Cell-based assignment metadata for a quote item.
    """

    __tablename__ = "quote_item_cell_assignments"

    id = Column(Integer, primary_key=True, index=True)
    quote_item_id = Column(
        Integer, ForeignKey("quote_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cell_id = Column(
        Integer, ForeignKey("team_cells.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cell_version_id = Column(
        Integer,
        ForeignKey("team_cell_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    occupancy_percentage = Column(Numeric(precision=10, scale=4), nullable=False)
    duration_months = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    quote_item = relationship("QuoteItem", back_populates="cell_assignment")


class QuoteExpense(Base):
    """
    Quote expense model (third-party costs, materials, licenses with markup)
    Sprint 15: Support for third-party expenses with markup for creative sectors
    """

    __tablename__ = "quote_expenses"

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    cost = Column(
        Numeric(precision=19, scale=4), nullable=False
    )  # Real cost - ESTÁNDAR NOUGRAM: Numeric
    markup_percentage = Column(
        Numeric(precision=10, scale=4), default=0.0, nullable=False
    )  # Mark-up - ESTÁNDAR NOUGRAM: Numeric (0.10 = 10%)
    client_price = Column(
        Numeric(precision=19, scale=4), nullable=False
    )  # cost * quantity * (1 + markup) - ESTÁNDAR NOUGRAM: Numeric
    category = Column(String, nullable=True)  # "Third Party", "Materials", "Licenses"
    quantity = Column(
        Numeric(precision=10, scale=4), default=1.0, nullable=False
    )  # ESTÁNDAR NOUGRAM: Numeric
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    quote = relationship("Quote", back_populates="expenses")
