"""
Organization model for multi-tenant architecture
"""

from sqlalchemy import JSON, Column, DateTime, Integer, String, TypeDecorator, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class FlexibleJSON(TypeDecorator):
    """
    JSON type that uses JSONB for PostgreSQL and JSON for other databases (like SQLite for tests)
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


class Organization(Base):
    """
    Organization model for multi-tenant architecture
    Each organization is a separate tenant with isolated data
    """

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)

    # Subscription management
    subscription_plan = Column(
        String, default="free", nullable=False
    )  # free, starter, professional, enterprise
    subscription_status = Column(
        String, default="active", nullable=False
    )  # active, cancelled, past_due, trialing

    # Tenant-specific settings stored as JSONB (PostgreSQL) or JSON (SQLite/other)
    settings = Column(FlexibleJSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="organization", lazy="dynamic")
    subscriptions = relationship("Subscription", back_populates="organization", lazy="dynamic")
    credit_account = relationship(
        "CreditAccount", back_populates="organization", uselist=False, cascade="all, delete-orphan"
    )
    equipment = relationship("EquipmentAmortization", back_populates="organization", lazy="dynamic")
