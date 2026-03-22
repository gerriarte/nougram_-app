"""
Team groups/cells models for reusable staffing structures.
"""
from sqlalchemy import (
    Boolean,
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


class TeamGroup(Base):
    __tablename__ = "team_groups"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_team_groups_org_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true", default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    cells = relationship("TeamCell", back_populates="group")


class TeamCell(Base):
    __tablename__ = "team_cells"
    __table_args__ = (
        UniqueConstraint("organization_id", "group_id", "name", name="uq_team_cells_org_group_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("team_groups.id", ondelete="RESTRICT"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true", default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    group = relationship("TeamGroup", back_populates="cells")
    versions = relationship("TeamCellVersion", back_populates="cell", cascade="all, delete-orphan")


class TeamCellVersion(Base):
    __tablename__ = "team_cell_versions"
    __table_args__ = (
        UniqueConstraint("cell_id", "version_number", name="uq_team_cell_versions_cell_version"),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    cell_id = Column(Integer, ForeignKey("team_cells.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    status = Column(String(16), nullable=False, server_default="published", default="published")
    notes = Column(String(1000), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    published_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cell = relationship("TeamCell", back_populates="versions")
    members = relationship("TeamCellMemberVersion", back_populates="cell_version", cascade="all, delete-orphan")


class TeamCellMemberVersion(Base):
    __tablename__ = "team_cell_member_versions"
    __table_args__ = (
        UniqueConstraint("cell_version_id", "team_member_id", name="uq_team_cell_member_versions_unique_member"),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    cell_version_id = Column(Integer, ForeignKey("team_cell_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    team_member_id = Column(Integer, ForeignKey("team_members.id", ondelete="RESTRICT"), nullable=False, index=True)
    weight = Column(Numeric(precision=10, scale=4), nullable=False, server_default="1.0", default=1.0)
    role_override = Column(String(120), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true", default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cell_version = relationship("TeamCellVersion", back_populates="members")
    team_member = relationship("TeamMember")
