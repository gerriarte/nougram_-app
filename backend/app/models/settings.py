"""
Settings and configuration models
"""
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class AgencySettings(Base):
    """
    Agency settings and configuration
    """
    __tablename__ = "agency_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    primary_currency = Column(String, default="USD", nullable=False)  # USD, COP, ARS, EUR, PEN, MXN
    currency_symbol = Column(String, default="$", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    

