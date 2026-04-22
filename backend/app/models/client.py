"""
Client model - master catalog for organizations (multi-tenant).
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Client(Base):
    """
    Client master catalog per organization.
    Projects reference client_id; client_name/client_email on project kept for snapshot/compat.
    """

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    display_name = Column(String, nullable=False)  # company name
    requester_name = Column(String, nullable=True)  # contact person
    email = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)  # active, inactive
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization", backref="clients")
