# Plan de Trabajo: Campos Extendidos del Perfil de Usuario

**Versión:** 1.0  
**Fecha:** 2026-01-23  
**Objetivo:** Implementar campos extendidos del perfil de usuario en el backend para soportar funcionalidades de gestión de usuarios y propuestas.

---

## Resumen Ejecutivo

Este plan detalla la implementación de campos extendidos en el modelo `User` para soportar:
- Información de perfil profesional (bio, foto, especialidad, cargo)
- Redes sociales (LinkedIn, Portfolio, GitHub, Behance) para propuestas
- Preferencias de usuario (timezone, idioma)

**Campos a Implementar:**
- `bio` (String, opcional, max 500 caracteres)
- `photo_url` (String, opcional, URL válida)
- `specialty` (String, opcional)
- `job_title` (String, opcional)
- `linkedin_url` (String, opcional, URL válida)
- `portfolio_url` (String, opcional, URL válida)
- `github_url` (String, opcional, URL válida)
- `behance_url` (String, opcional, URL válida)
- `timezone` (String, opcional, formato IANA timezone)
- `language` (String, opcional, código ISO 639-1)

---

## Fase 1: Migración de Base de Datos

### 1.1 Crear Migración Alembic

**Archivo:** `backend/alembic/versions/XXXX_add_user_profile_extended_fields.py`

**Descripción:** Agregar columnas nuevas a la tabla `users` con valores por defecto NULL (opcionales).

**Script de Migración:**

```python
"""add_user_profile_extended_fields

Revision ID: XXXX
Revises: [previous_revision]
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'XXXX'
down_revision = '[previous_revision]'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar campos de perfil profesional
    op.add_column('users', sa.Column('bio', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('photo_url', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('specialty', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('job_title', sa.String(length=100), nullable=True))
    
    # Agregar campos de redes sociales
    op.add_column('users', sa.Column('linkedin_url', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('portfolio_url', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('github_url', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('behance_url', sa.String(length=500), nullable=True))
    
    # Agregar campos de preferencias
    op.add_column('users', sa.Column('timezone', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('language', sa.String(length=10), nullable=True))
    
    # Crear índices para búsquedas comunes (opcional, pero recomendado)
    op.create_index('ix_users_specialty', 'users', ['specialty'])
    op.create_index('ix_users_job_title', 'users', ['job_title'])


def downgrade():
    # Eliminar índices
    op.drop_index('ix_users_job_title', table_name='users')
    op.drop_index('ix_users_specialty', table_name='users')
    
    # Eliminar columnas
    op.drop_column('users', 'language')
    op.drop_column('users', 'timezone')
    op.drop_column('users', 'behance_url')
    op.drop_column('users', 'github_url')
    op.drop_column('users', 'portfolio_url')
    op.drop_column('users', 'linkedin_url')
    op.drop_column('users', 'job_title')
    op.drop_column('users', 'specialty')
    op.drop_column('users', 'photo_url')
    op.drop_column('users', 'bio')
```

**Tareas:**
- [ ] Crear archivo de migración con Alembic
- [ ] Ejecutar migración en entorno de desarrollo
- [ ] Verificar que las columnas se crearon correctamente
- [ ] Probar rollback (downgrade) de la migración

**Comando:**
```bash
cd backend
python -m alembic revision -m "add_user_profile_extended_fields"
```

---

## Fase 2: Actualización del Modelo User

### 2.1 Modificar Modelo SQLAlchemy

**Archivo:** `backend/app/models/user.py`

**Cambios:**

```python
"""
User model for authentication
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """
    User model for authentication and authorization
    """
    __tablename__ = "users"
    
    # Campos existentes
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    google_refresh_token = Column(String, nullable=True)  # Encrypted
    role = Column(String(32), nullable=True, index=True)
    role_type = Column(String(16), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # NUEVOS CAMPOS: Perfil profesional
    bio = Column(String(500), nullable=True)  # Biografía profesional (max 500 caracteres)
    photo_url = Column(String(500), nullable=True)  # URL de foto de perfil
    specialty = Column(String(100), nullable=True, index=True)  # Especialidad (ej: "Diseño UI/UX")
    job_title = Column(String(100), nullable=True, index=True)  # Cargo/Título (ej: "Senior Designer")
    
    # NUEVOS CAMPOS: Redes sociales (para propuestas)
    linkedin_url = Column(String(500), nullable=True)  # URL de LinkedIn
    portfolio_url = Column(String(500), nullable=True)  # URL de portfolio personal
    github_url = Column(String(500), nullable=True)  # URL de GitHub
    behance_url = Column(String(500), nullable=True)  # URL de Behance
    
    # NUEVOS CAMPOS: Preferencias
    timezone = Column(String(50), nullable=True)  # Zona horaria IANA (ej: "America/Bogota")
    language = Column(String(10), nullable=True)  # Código ISO 639-1 (ej: "es", "en")
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    team_member = relationship("TeamMember", back_populates="user", uselist=False)
```

**Tareas:**
- [ ] Agregar campos nuevos al modelo User
- [ ] Verificar que los tipos de datos coinciden con la migración
- [ ] Actualizar docstrings si es necesario

---

## Fase 3: Actualización de Schemas Pydantic

### 3.1 Actualizar UserUpdate Schema

**Archivo:** `backend/app/schemas/auth.py`

**Cambios:**

```python
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, HttpUrl, validator
import re


class UserUpdate(BaseModel):
    """Schema for updating current user profile"""
    full_name: Optional[str] = Field(None, description="User full name", min_length=1, max_length=255)
    
    # NUEVOS CAMPOS: Perfil profesional
    bio: Optional[str] = Field(None, description="Professional biography", max_length=500)
    photo_url: Optional[str] = Field(None, description="Profile photo URL", max_length=500)
    specialty: Optional[str] = Field(None, description="Professional specialty", max_length=100)
    job_title: Optional[str] = Field(None, description="Job title", max_length=100)
    
    # NUEVOS CAMPOS: Redes sociales
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL", max_length=500)
    portfolio_url: Optional[str] = Field(None, description="Portfolio URL", max_length=500)
    github_url: Optional[str] = Field(None, description="GitHub profile URL", max_length=500)
    behance_url: Optional[str] = Field(None, description="Behance profile URL", max_length=500)
    
    # NUEVOS CAMPOS: Preferencias
    timezone: Optional[str] = Field(None, description="IANA timezone (e.g., 'America/Bogota')", max_length=50)
    language: Optional[str] = Field(None, description="ISO 639-1 language code (e.g., 'es', 'en')", max_length=10)
    
    @validator('photo_url', 'linkedin_url', 'portfolio_url', 'github_url', 'behance_url')
    def validate_url(cls, v):
        """Validate URL format"""
        if v is None or v == '':
            return None
        
        # Validar formato básico de URL
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(v):
            raise ValueError(f"Invalid URL format: {v}")
        
        return v
    
    @validator('timezone')
    def validate_timezone(cls, v):
        """Validate IANA timezone format"""
        if v is None or v == '':
            return None
        
        # Lista de timezones comunes (puede expandirse)
        valid_timezones = [
            'America/Bogota', 'America/Mexico_City', 'America/New_York',
            'America/Los_Angeles', 'America/Chicago', 'America/Sao_Paulo',
            'Europe/Madrid', 'Europe/London', 'Asia/Tokyo', 'UTC'
        ]
        
        # Validación básica: debe tener formato "Continent/City"
        if '/' not in v:
            raise ValueError(f"Invalid timezone format. Expected format: 'Continent/City' (e.g., 'America/Bogota')")
        
        # Opcional: validar contra lista conocida (puede ser más permisivo)
        # if v not in valid_timezones:
        #     raise ValueError(f"Unknown timezone: {v}. Valid timezones: {valid_timezones}")
        
        return v
    
    @validator('language')
    def validate_language(cls, v):
        """Validate ISO 639-1 language code"""
        if v is None or v == '':
            return None
        
        # Códigos de idioma comunes
        valid_languages = ['es', 'en', 'pt', 'fr', 'de', 'it', 'ja', 'zh']
        
        if v not in valid_languages:
            raise ValueError(f"Invalid language code: {v}. Valid codes: {valid_languages}")
        
        return v
    
    @validator('bio')
    def validate_bio_length(cls, v):
        """Validate bio length"""
        if v is None:
            return None
        
        if len(v) > 500:
            raise ValueError("Bio must be 500 characters or less")
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "full_name": "Juan Pérez",
                "bio": "Diseñador UI/UX con 5 años de experiencia",
                "photo_url": "https://example.com/photo.jpg",
                "specialty": "Diseño UI/UX",
                "job_title": "Senior Designer",
                "linkedin_url": "https://linkedin.com/in/juanperez",
                "portfolio_url": "https://juanperez.design",
                "github_url": "https://github.com/juanperez",
                "behance_url": "https://behance.net/juanperez",
                "timezone": "America/Bogota",
                "language": "es"
            }
        }
```

**Tareas:**
- [ ] Actualizar UserUpdate con nuevos campos
- [ ] Agregar validadores para URLs, timezone, language
- [ ] Agregar ejemplos en schema_extra
- [ ] Probar validaciones con casos edge (URLs inválidas, timezones desconocidos)

### 3.2 Actualizar UserResponse Schema

**Archivo:** `backend/app/schemas/auth.py`

**Cambios:**

```python
class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    email: EmailStr
    full_name: str
    has_calendar_connected: bool = False
    role: str = Field(default="product_manager", description="User role")
    organization_id: Optional[int] = Field(None, description="Organization ID for multi-tenant support")
    
    # NUEVOS CAMPOS: Perfil profesional
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    specialty: Optional[str] = None
    job_title: Optional[str] = None
    
    # NUEVOS CAMPOS: Redes sociales
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    behance_url: Optional[str] = None
    
    # NUEVOS CAMPOS: Preferencias
    timezone: Optional[str] = None
    language: Optional[str] = None

    class Config:
        from_attributes = False  # Disable to avoid enum issues
```

**Tareas:**
- [ ] Agregar nuevos campos a UserResponse
- [ ] Verificar que todos los campos opcionales tienen `Optional[str] = None`

### 3.3 Crear UserProfileExtended Schema (Opcional)

**Archivo:** `backend/app/schemas/auth.py`

**Descripción:** Schema completo para respuestas de perfil extendido (puede usarse en endpoints específicos de perfil).

```python
class UserProfileExtended(UserResponse):
    """Extended user profile schema with all fields"""
    
    # Puede incluir campos adicionales como:
    # created_at, updated_at, last_login_at (si se implementan)
    
    class Config:
        from_attributes = True
```

**Tareas:**
- [ ] Crear UserProfileExtended si se necesita un schema separado
- [ ] O usar UserResponse directamente si es suficiente

---

## Fase 4: Actualización de Endpoints

### 4.1 Actualizar Endpoint PUT /auth/me

**Archivo:** `backend/app/api/v1/endpoints/auth.py`

**Cambios:**

```python
@router.put("/me", response_model=UserResponse)
async def update_current_user_info(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user profile information.
    
    **Permissions:**
    - Usuario autenticado puede actualizar su propio perfil
    - Solo puede actualizar campos de su propio perfil (no roles, organización, etc.)
    """
    from app.core.permissions import get_user_role
    from app.core.logging import get_logger
    
    logger = get_logger(__name__)
    
    # Actualizar solo campos proporcionados (exclude_unset=True)
    update_data = payload.model_dump(exclude_unset=True)
    
    # Actualizar campos en el modelo
    for field, value in update_data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    user_role = get_user_role(current_user)
    
    logger.info(
        "User profile updated",
        user_id=current_user.id,
        updated_fields=list(update_data.keys())
    )
    
    # Construir respuesta con todos los campos
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        has_calendar_connected=current_user.google_refresh_token is not None,
        role=user_role,
        organization_id=current_user.organization_id,
        # NUEVOS CAMPOS
        bio=getattr(current_user, 'bio', None),
        photo_url=getattr(current_user, 'photo_url', None),
        specialty=getattr(current_user, 'specialty', None),
        job_title=getattr(current_user, 'job_title', None),
        linkedin_url=getattr(current_user, 'linkedin_url', None),
        portfolio_url=getattr(current_user, 'portfolio_url', None),
        github_url=getattr(current_user, 'github_url', None),
        behance_url=getattr(current_user, 'behance_url', None),
        timezone=getattr(current_user, 'timezone', None),
        language=getattr(current_user, 'language', None),
    )
```

**Tareas:**
- [ ] Actualizar endpoint PUT /auth/me para aceptar nuevos campos
- [ ] Usar `exclude_unset=True` para actualizar solo campos proporcionados
- [ ] Agregar logging de campos actualizados
- [ ] Verificar que la respuesta incluye todos los campos nuevos

### 4.2 Actualizar Endpoint GET /auth/me

**Archivo:** `backend/app/api/v1/endpoints/auth.py`

**Cambios:**

```python
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information
    """
    from app.core.permissions import get_user_role

    user_role = get_user_role(current_user)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        has_calendar_connected=current_user.google_refresh_token is not None,
        role=user_role,
        organization_id=current_user.organization_id,
        # NUEVOS CAMPOS
        bio=getattr(current_user, 'bio', None),
        photo_url=getattr(current_user, 'photo_url', None),
        specialty=getattr(current_user, 'specialty', None),
        job_title=getattr(current_user, 'job_title', None),
        linkedin_url=getattr(current_user, 'linkedin_url', None),
        portfolio_url=getattr(current_user, 'portfolio_url', None),
        github_url=getattr(current_user, 'github_url', None),
        behance_url=getattr(current_user, 'behance_url', None),
        timezone=getattr(current_user, 'timezone', None),
        language=getattr(current_user, 'language', None),
    )
```

**Tareas:**
- [ ] Actualizar GET /auth/me para incluir nuevos campos en la respuesta
- [ ] Usar `getattr` con valores por defecto para compatibilidad con usuarios existentes

### 4.3 Actualizar Endpoint GET /users/ (Opcional)

**Archivo:** `backend/app/api/v1/endpoints/users.py`

**Descripción:** Si se necesita mostrar información extendida en la lista de usuarios (solo para super_admin).

**Consideraciones:**
- Por privacidad, puede ser mejor NO incluir todos los campos en la lista
- Incluir solo campos básicos: `photo_url`, `specialty`, `job_title` (opcional)

**Tareas:**
- [ ] Decidir qué campos mostrar en lista de usuarios
- [ ] Actualizar UserListResponse si es necesario
- [ ] Actualizar endpoint GET /users/ si se requiere

---

## Fase 5: Validaciones y Utilidades

### 5.1 Crear Utilidad de Validación de URLs

**Archivo:** `backend/app/core/validators.py` (nuevo archivo)

**Descripción:** Funciones de validación reutilizables para URLs, timezones, etc.

```python
"""
Validation utilities for user profile fields
"""
import re
from typing import Optional
from pydantic import ValidationError


def validate_url(url: Optional[str]) -> Optional[str]:
    """
    Validate URL format
    
    Args:
        url: URL string to validate
        
    Returns:
        Validated URL or None
        
    Raises:
        ValueError: If URL format is invalid
    """
    if url is None or url == '':
        return None
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        raise ValueError(f"Invalid URL format: {url}")
    
    return url


def validate_timezone(timezone: Optional[str]) -> Optional[str]:
    """
    Validate IANA timezone format
    
    Args:
        timezone: Timezone string (e.g., 'America/Bogota')
        
    Returns:
        Validated timezone or None
        
    Raises:
        ValueError: If timezone format is invalid
    """
    if timezone is None or timezone == '':
        return None
    
    # Validación básica: debe tener formato "Continent/City"
    if '/' not in timezone:
        raise ValueError(f"Invalid timezone format. Expected format: 'Continent/City' (e.g., 'America/Bogota')")
    
    return timezone


def validate_language_code(language: Optional[str]) -> Optional[str]:
    """
    Validate ISO 639-1 language code
    
    Args:
        language: Language code (e.g., 'es', 'en')
        
    Returns:
        Validated language code or None
        
    Raises:
        ValueError: If language code is invalid
    """
    if language is None or language == '':
        return None
    
    valid_languages = ['es', 'en', 'pt', 'fr', 'de', 'it', 'ja', 'zh']
    
    if language not in valid_languages:
        raise ValueError(f"Invalid language code: {language}. Valid codes: {valid_languages}")
    
    return language
```

**Tareas:**
- [ ] Crear archivo `backend/app/core/validators.py`
- [ ] Implementar funciones de validación
- [ ] Agregar tests unitarios para validadores

### 5.2 Actualizar Validaciones en Schemas

**Tareas:**
- [ ] Usar funciones de validación de `validators.py` en schemas Pydantic
- [ ] Agregar mensajes de error descriptivos
- [ ] Probar casos edge (URLs malformadas, timezones inválidos)

---

## Fase 6: Tests

### 6.1 Tests Unitarios de Schemas

**Archivo:** `backend/tests/unit/test_user_profile_schemas.py` (nuevo)

**Tests a Implementar:**

```python
import pytest
from pydantic import ValidationError
from app.schemas.auth import UserUpdate


def test_user_update_valid_data():
    """Test UserUpdate with valid data"""
    data = {
        "full_name": "Juan Pérez",
        "bio": "Diseñador UI/UX",
        "photo_url": "https://example.com/photo.jpg",
        "specialty": "Diseño UI/UX",
        "job_title": "Senior Designer",
        "linkedin_url": "https://linkedin.com/in/juanperez",
        "timezone": "America/Bogota",
        "language": "es"
    }
    user_update = UserUpdate(**data)
    assert user_update.full_name == "Juan Pérez"
    assert user_update.bio == "Diseñador UI/UX"
    assert user_update.timezone == "America/Bogota"


def test_user_update_invalid_url():
    """Test UserUpdate with invalid URL"""
    with pytest.raises(ValidationError) as exc_info:
        UserUpdate(photo_url="not-a-url")
    assert "Invalid URL format" in str(exc_info.value)


def test_user_update_invalid_timezone():
    """Test UserUpdate with invalid timezone"""
    with pytest.raises(ValidationError) as exc_info:
        UserUpdate(timezone="InvalidTimezone")
    assert "Invalid timezone format" in str(exc_info.value)


def test_user_update_invalid_language():
    """Test UserUpdate with invalid language code"""
    with pytest.raises(ValidationError) as exc_info:
        UserUpdate(language="xx")
    assert "Invalid language code" in str(exc_info.value)


def test_user_update_bio_too_long():
    """Test UserUpdate with bio exceeding max length"""
    long_bio = "a" * 501
    with pytest.raises(ValidationError) as exc_info:
        UserUpdate(bio=long_bio)
    assert "500 characters" in str(exc_info.value)


def test_user_update_partial_update():
    """Test UserUpdate with only some fields"""
    data = {
        "full_name": "Juan Pérez",
        "specialty": "Diseño UI/UX"
    }
    user_update = UserUpdate(**data)
    assert user_update.full_name == "Juan Pérez"
    assert user_update.specialty == "Diseño UI/UX"
    assert user_update.bio is None
```

**Tareas:**
- [ ] Crear archivo de tests unitarios
- [ ] Implementar tests de validación
- [ ] Ejecutar tests y verificar que pasan

### 6.2 Tests de Integración de Endpoints

**Archivo:** `backend/tests/integration/test_user_profile_endpoints.py` (nuevo)

**Tests a Implementar:**

```python
import pytest
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.asyncio
async def test_update_user_profile_success(client: AsyncClient, test_user: User, auth_headers: dict):
    """Test successful user profile update"""
    data = {
        "full_name": "Juan Pérez Updated",
        "bio": "Updated bio",
        "specialty": "Diseño UI/UX",
        "timezone": "America/Bogota",
        "language": "es"
    }
    
    response = await client.put(
        "/api/v1/auth/me",
        json=data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["full_name"] == "Juan Pérez Updated"
    assert result["bio"] == "Updated bio"
    assert result["specialty"] == "Diseño UI/UX"
    assert result["timezone"] == "America/Bogota"


@pytest.mark.asyncio
async def test_update_user_profile_invalid_url(client: AsyncClient, test_user: User, auth_headers: dict):
    """Test user profile update with invalid URL"""
    data = {
        "photo_url": "not-a-url"
    }
    
    response = await client.put(
        "/api/v1/auth/me",
        json=data,
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_user_profile_with_extended_fields(client: AsyncClient, test_user: User, auth_headers: dict):
    """Test GET /auth/me returns extended profile fields"""
    # Primero actualizar perfil
    update_data = {
        "bio": "Test bio",
        "specialty": "Developer",
        "photo_url": "https://example.com/photo.jpg"
    }
    await client.put("/api/v1/auth/me", json=update_data, headers=auth_headers)
    
    # Luego obtener perfil
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    result = response.json()
    assert result["bio"] == "Test bio"
    assert result["specialty"] == "Developer"
    assert result["photo_url"] == "https://example.com/photo.jpg"


@pytest.mark.asyncio
async def test_update_user_profile_partial(client: AsyncClient, test_user: User, auth_headers: dict):
    """Test partial profile update (only some fields)"""
    # Actualizar solo bio
    data = {"bio": "New bio"}
    response = await client.put("/api/v1/auth/me", json=data, headers=auth_headers)
    
    assert response.status_code == 200
    result = response.json()
    assert result["bio"] == "New bio"
    # Otros campos no deberían cambiar
    assert result["full_name"] == test_user.full_name
```

**Tareas:**
- [ ] Crear archivo de tests de integración
- [ ] Implementar tests de endpoints
- [ ] Ejecutar tests y verificar que pasan

### 6.3 Tests de Migración

**Tareas:**
- [ ] Probar migración en entorno de desarrollo
- [ ] Verificar que usuarios existentes siguen funcionando (campos NULL)
- [ ] Probar rollback de migración
- [ ] Verificar índices se crearon correctamente

---

## Fase 7: Documentación

### 7.1 Actualizar Documentación de API

**Archivo:** `docs/development/FRONTEND_API_INTEGRATION_GUIDE.md`

**Cambios:**
- Actualizar sección de "User Profile" con nuevos campos
- Agregar ejemplos de requests/responses
- Documentar validaciones

**Tareas:**
- [ ] Actualizar documentación de API
- [ ] Agregar ejemplos de uso
- [ ] Documentar validaciones y restricciones

### 7.2 Actualizar Documentación de UI Requirements

**Archivo:** `docs/development/UI_REQUIREMENTS_USER_MANAGEMENT.md`

**Cambios:**
- Actualizar sección "User Profile Data" indicando que los campos están implementados
- Agregar nota sobre campos disponibles

**Tareas:**
- [ ] Actualizar documento de UI Requirements
- [ ] Marcar campos como "implementado" en backend

---

## Checklist de Implementación

### Fase 1: Migración
- [ ] Crear migración Alembic
- [ ] Ejecutar migración en desarrollo
- [ ] Verificar columnas creadas
- [ ] Probar rollback

### Fase 2: Modelo
- [ ] Actualizar modelo User con nuevos campos
- [ ] Verificar tipos de datos

### Fase 3: Schemas
- [ ] Actualizar UserUpdate con nuevos campos y validaciones
- [ ] Actualizar UserResponse con nuevos campos
- [ ] Probar validaciones

### Fase 4: Endpoints
- [ ] Actualizar PUT /auth/me
- [ ] Actualizar GET /auth/me
- [ ] Probar endpoints manualmente

### Fase 5: Validaciones
- [ ] Crear archivo validators.py
- [ ] Implementar funciones de validación
- [ ] Integrar validaciones en schemas

### Fase 6: Tests
- [ ] Crear tests unitarios de schemas
- [ ] Crear tests de integración de endpoints
- [ ] Ejecutar todos los tests
- [ ] Verificar cobertura

### Fase 7: Documentación
- [ ] Actualizar documentación de API
- [ ] Actualizar UI Requirements
- [ ] Revisar documentación completa

---

## Consideraciones Adicionales

### Seguridad
- **URLs:** Validar que las URLs no contengan scripts maliciosos
- **Foto de Perfil:** Considerar almacenamiento seguro (S3, Cloudinary) en lugar de URLs externas
- **Datos Sensibles:** Los campos de redes sociales son públicos, no contienen información sensible

### Performance
- **Índices:** Los índices en `specialty` y `job_title` ayudan en búsquedas futuras
- **Campos Opcionales:** Todos los campos son opcionales (NULL), no afectan usuarios existentes

### Compatibilidad
- **Backward Compatibility:** Usuarios existentes seguirán funcionando (campos NULL)
- **Frontend:** El frontend debe manejar campos opcionales (null/undefined)

### Futuras Mejoras
- **Upload de Fotos:** Implementar endpoint para subir fotos directamente (no solo URL)
- **Validación de Timezone:** Usar librería `pytz` o `zoneinfo` para validación más robusta
- **Búsqueda por Especialidad:** Implementar endpoint de búsqueda de usuarios por especialidad
- **Perfil Público:** Considerar endpoint de perfil público para propuestas (solo campos públicos)

---

## Estimación de Tiempo

- **Fase 1 (Migración):** 1-2 horas
- **Fase 2 (Modelo):** 30 minutos
- **Fase 3 (Schemas):** 2-3 horas
- **Fase 4 (Endpoints):** 1-2 horas
- **Fase 5 (Validaciones):** 1-2 horas
- **Fase 6 (Tests):** 3-4 horas
- **Fase 7 (Documentación):** 1 hora

**Total Estimado:** 10-15 horas

---

**Última actualización:** 2026-01-23  
**Estado:** Pendiente de implementación
