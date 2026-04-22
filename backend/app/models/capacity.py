"""
Capacity tracking models (tentative/committed/actual) by source event.
"""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.organization import FlexibleJSON


class CapacityCommitment(Base):
    __tablename__ = "capacity_commitments"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "team_member_id",
            "source_type",
            "source_id",
            "state",
            "period_start",
            "period_end",
            name="uq_capacity_commitments_dedup",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    team_member_id = Column(Integer, ForeignKey("team_members.id"), nullable=False, index=True)
    cell_id = Column(Integer, ForeignKey("team_cells.id"), nullable=True, index=True)
    source_type = Column(String, nullable=False, index=True)  # proposal_link, quote, project
    source_id = Column(Integer, nullable=False, index=True)
    state = Column(String, nullable=False, index=True)  # tentative, committed, actual
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    hours = Column(Numeric(precision=19, scale=4), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization")
    team_member = relationship("TeamMember")
    cell = relationship("TeamCell")


class CapacityEvent(Base):
    __tablename__ = "capacity_events"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    source_type = Column(String, nullable=False, index=True)
    source_id = Column(Integer, nullable=False, index=True)
    payload = Column(FlexibleJSON, nullable=False, default={})
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    organization = relationship("Organization")
    created_by = relationship("User")
