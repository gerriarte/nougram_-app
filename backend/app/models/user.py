"""
User model for authentication
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, text
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """
    User model for authentication and authorization
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    email_verified = Column(Boolean, nullable=False, server_default=text("true"))
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    google_refresh_token = Column(String, nullable=True)  # Encrypted
    # Extended profile fields
    job_title = Column(String(120), nullable=True)
    specialty = Column(String(120), nullable=True)
    bio = Column(String(1000), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    portfolio_url = Column(String(255), nullable=True)
    instagram_url = Column(String(255), nullable=True)
    behance_url = Column(String(255), nullable=True)
    timezone = Column(String(64), nullable=True)
    language = Column(String(8), nullable=True)
    # Roles: non-disruptive string-based role (nullable, defaults handled at DB/migration)
    role = Column(String(32), nullable=True, index=True)
    
    # Role type: "support" (multi-tenant manager) or "tenant" (client user)
    # NULL means "tenant" for backward compatibility
    role_type = Column(String(16), nullable=True, index=True)
    
    # Multi-tenant: organization relationship
    # If role_type == "support", organization_id can be NULL
    # If role_type == "tenant" or NULL, organization_id is REQUIRED
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    team_member = relationship("TeamMember", back_populates="user", uselist=False)
    # Note: delete_requests relationships disabled (rollback from roles system)


