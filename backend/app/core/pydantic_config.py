"""
Pydantic configuration for Decimal serialization
ESTÁNDAR NOUGRAM: Decimal se serializa como string para mantener precisión
"""

from decimal import Decimal

from pydantic import ConfigDict

# Configuración base para schemas con Decimal
# ESTÁNDAR NOUGRAM: Decimal se serializa como string en JSON
# Incluye from_attributes para compatibilidad con SQLAlchemy models
DECIMAL_CONFIG = ConfigDict(
    from_attributes=True, json_encoders={Decimal: lambda v: str(v) if v is not None else None}
)
