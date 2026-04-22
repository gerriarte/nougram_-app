"""
Industry Template model for onboarding new organizations
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.organization import FlexibleJSON


class IndustryTemplate(Base):
    """
    Industry template model for onboarding

    Pre-configured templates with suggested roles, services, and fixed costs
    for different industry types (Branding, Web Development, Audiovisual, etc.)
    """

    __tablename__ = "industry_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template identification
    industry_type = Column(
        String, unique=True, nullable=False, index=True
    )  # "branding", "web_development", etc.
    name = Column(String, nullable=False)  # "Agencia de Branding"
    description = Column(Text, nullable=True)  # Detailed description of the template

    # Suggested data stored as JSON (using FlexibleJSON for PostgreSQL/SQLite compatibility)
    suggested_roles = Column(
        FlexibleJSON, nullable=True
    )  # Array of role suggestions with salaries, seniority, billable hours
    suggested_services = Column(
        FlexibleJSON, nullable=True
    )  # Array of service suggestions with target margins
    suggested_fixed_costs = Column(FlexibleJSON, nullable=True)  # Array of fixed cost suggestions

    # Template metadata
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    icon = Column(String, nullable=True)  # Icon identifier for UI
    color = Column(String, nullable=True)  # Color code for UI

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<IndustryTemplate(id={self.id}, type={self.industry_type}, name={self.name})>"

    def to_dict(self):
        """Convert template to dictionary for API responses"""
        return {
            "id": self.id,
            "industry_type": self.industry_type,
            "name": self.name,
            "description": self.description,
            "suggested_roles": self.suggested_roles,
            "suggested_services": self.suggested_services,
            "suggested_fixed_costs": self.suggested_fixed_costs,
            "is_active": self.is_active,
            "icon": self.icon,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
