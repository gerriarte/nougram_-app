# Plan de Implementación: Backend para Creación de Cotización Paso a Paso

**Fecha:** 2026-02-08  
**Base:** [2026-02-07-PLAN_TRABAJO_COTIZACION_FRONTEND.md](./2026-02-07-PLAN_TRABAJO_COTIZACION_FRONTEND.md) (Frontend / Apple Style)  
**Arquitectura:** MVC + Repository/Service (`.cursorrules/nougram_backend_rules.md`)  
**Ubicación:** `backend/app/`

---

## 🎯 Resumen Ejecutivo

Implementar endpoints del backend para soportar el nuevo flujo de creación de cotización paso a paso con estilo Apple, permitiendo:

- **Búsqueda de clientes:** Autocompletado inteligente de clientes existentes basado en nombre o email
- **Resumen ejecutivo con IA:** Generación automática de resúmenes ejecutivos para cotizaciones usando IA
- **Compatibilidad total:** Mantener compatibilidad con endpoints existentes de creación de proyectos y cotizaciones

**Arquitectura Requerida:**
```
Endpoint → Controller → Service → Repository → ORM → Database
                    ↓
                  View (transformación de datos)
```

**Endpoints Nuevos Requeridos:**
1. `GET /api/v1/projects/clients/search` - Búsqueda de clientes existentes
2. `POST /api/v1/ai/generate-executive-summary` - Generación de resumen ejecutivo con IA

**Endpoints Existentes (Sin Modificaciones):**
- ✅ `POST /api/v1/projects/` - Crear proyecto con cotización inicial
- ✅ `POST /api/v1/quotes/calculate` - Calcular totales de cotización
- ✅ `PUT /api/v1/projects/{project_id}/quotes/{quote_id}` - Actualizar cotización
- ✅ `GET /api/v1/projects/{project_id}` - Obtener proyecto
- ✅ `GET /api/v1/services/` - Listar servicios disponibles

---

## 📊 Análisis de Estado Actual

### Endpoints Existentes y Suficientes

#### 1. Creación de Proyectos y Cotizaciones
- ✅ `POST /api/v1/projects/` (`ProjectCreateWithQuote`)
  - **Estado:** Funcional y completo
  - **Soporta:** Creación de proyecto con cotización inicial, múltiples tipos de pricing, revisiones
  - **Uso en nuevo flujo:** Se utilizará en el paso final para crear el proyecto completo

#### 2. Cálculo de Cotizaciones
- ✅ `POST /api/v1/quotes/calculate` (`QuoteCalculateRequest`)
  - **Estado:** Funcional y completo
  - **Soporta:** Cálculo de totales (costo interno, precio cliente, margen) con múltiples tipos de pricing
  - **Uso en nuevo flujo:** Se utilizará para cálculos en tiempo real durante la creación

#### 3. Actualización de Cotizaciones
- ✅ `PUT /api/v1/projects/{project_id}/quotes/{quote_id}` (`QuoteUpdate`)
  - **Estado:** Funcional y completo
  - **Soporta:** Actualización de items, notas, márgenes objetivo, revisiones
  - **Uso en nuevo flujo:** Se utilizará si el usuario quiere modificar una cotización existente

#### 4. Obtención de Servicios
- ✅ `GET /api/v1/services/`
  - **Estado:** Funcional y completo
  - **Soporta:** Listado de servicios activos con información de pricing
  - **Uso en nuevo flujo:** Se utilizará para poblar el Bento Grid de selección de servicios

### Limitaciones Identificadas

1. ❌ **No hay endpoint para búsqueda de clientes**
   - **Problema:** El frontend necesita autocompletado de clientes existentes
   - **Solución:** Implementar `GET /api/v1/projects/clients/search`

2. ❌ **No hay endpoint para generación de resumen ejecutivo con IA**
   - **Problema:** El frontend necesita generar resúmenes ejecutivos automáticamente
   - **Solución:** Implementar `POST /api/v1/ai/generate-executive-summary`

---

## 📋 Componentes a Implementar

### 1. ✅ Schemas (`backend/app/schemas/project.py`)

**Estado:** ⚠️ Parcialmente implementado (necesita nuevos schemas)

**Schemas Nuevos Requeridos:**

```python
# Agregar al final de backend/app/schemas/project.py

class ClientSearchResult(BaseModel):
    """Resultado de búsqueda de cliente"""
    name: str = Field(..., description="Nombre del cliente")
    email: Optional[str] = Field(None, description="Email del cliente")
    project_count: int = Field(..., description="Número de proyectos con este cliente", ge=0)
    last_project_date: Optional[datetime] = Field(None, description="Fecha del último proyecto")
    
    model_config = {"from_attributes": False}  # No es un modelo ORM


class ClientSearchResponse(BaseModel):
    """Respuesta de búsqueda de clientes"""
    clients: List[ClientSearchResult] = Field(..., description="Lista de clientes encontrados")
    total: int = Field(..., description="Total de clientes encontrados", ge=0)
```

---

### 2. ✅ Schemas (`backend/app/schemas/ai.py`)

**Estado:** ⚠️ Parcialmente implementado (necesita nuevos schemas)

**Schemas Nuevos Requeridos:**

```python
# Agregar al final de backend/app/schemas/ai.py

class ExecutiveSummaryService(BaseModel):
    """Servicio para resumen ejecutivo"""
    service_id: int = Field(..., description="ID del servicio", gt=0)
    service_name: str = Field(..., description="Nombre del servicio", min_length=1)
    estimated_hours: Optional[float] = Field(None, description="Horas estimadas", ge=0)
    client_price: Decimal = Field(..., description="Precio al cliente", gt=0)
    
    @field_serializer('client_price')
    def serialize_decimal(self, value: Decimal) -> str:
        return str(value)
    
    model_config = DECIMAL_CONFIG


class ExecutiveSummaryRequest(BaseModel):
    """Request para generar resumen ejecutivo"""
    project_name: str = Field(..., description="Nombre del proyecto", min_length=1)
    client_name: str = Field(..., description="Nombre del cliente", min_length=1)
    client_sector: Optional[str] = Field(None, description="Sector del cliente (ej: 'Tecnología', 'Retail')")
    services: List[ExecutiveSummaryService] = Field(..., description="Lista de servicios incluidos", min_items=1)
    total_price: Decimal = Field(..., description="Precio total de la cotización", gt=0)
    currency: str = Field("USD", description="Moneda", min_length=3, max_length=3)
    language: str = Field("es", description="Idioma del resumen: 'es' o 'en'", pattern="^(es|en)$")
    
    @field_serializer('total_price')
    def serialize_decimal(self, value: Decimal) -> str:
        return str(value)
    
    model_config = DECIMAL_CONFIG


class ExecutiveSummaryResponse(BaseModel):
    """Response con resumen ejecutivo generado"""
    summary: str = Field(..., description="Resumen ejecutivo generado")
    provider: str = Field("openai", description="Proveedor de IA utilizado")
    usage: Optional[Dict[str, Any]] = Field(None, description="Información de uso de la API (tokens, costo estimado)")
```

**Nota:** Asegurarse de importar `DECIMAL_CONFIG` y `field_serializer` desde los módulos apropiados.

---

### 3. ✅ Repository Method (`backend/app/repositories/project_repository.py`)

**Estado:** ⚠️ Necesita nuevo método

**Método Nuevo Requerido:**

```python
# Agregar a la clase ProjectRepository en backend/app/repositories/project_repository.py

async def search_clients(
    self,
    search_query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Buscar clientes existentes por nombre o email
    
    Args:
        search_query: Query de búsqueda (nombre o email)
        limit: Límite de resultados (default: 10, max: 50)
    
    Returns:
        Lista de diccionarios con información de clientes:
        [
            {
                "name": "Cliente ABC",
                "email": "contacto@cliente.com",
                "project_count": 3,
                "last_project_date": datetime(...)
            },
            ...
        ]
    """
    from sqlalchemy import func, or_, desc
    
    # Validar límite
    limit = min(limit, 50)
    
    # Construir query de búsqueda (case-insensitive)
    search_pattern = f"%{search_query.lower()}%"
    
    # Query para buscar por nombre o email
    # Agrupar por nombre y email para evitar duplicados
    query = (
        select(
            Project.client_name,
            Project.client_email,
            func.count(Project.id).label('project_count'),
            func.max(Project.created_at).label('last_project_date')
        )
        .where(
            # Aplicar filtro de tenant
            Project.organization_id == self.tenant_id,
            # Excluir proyectos eliminados
            Project.deleted_at.is_(None),
            # Búsqueda case-insensitive en nombre o email
            or_(
                func.lower(Project.client_name).like(search_pattern),
                func.lower(Project.client_email).like(search_pattern) if Project.client_email.isnot(None) else False
            )
        )
        .group_by(Project.client_name, Project.client_email)
        .order_by(desc('last_project_date'))
        .limit(limit)
    )
    
    result = await self.db.execute(query)
    rows = result.all()
    
    # Convertir a lista de diccionarios
    clients = []
    for row in rows:
        clients.append({
            "name": row.client_name,
            "email": row.client_email,
            "project_count": row.project_count,
            "last_project_date": row.last_project_date
        })
    
    return clients
```

**Consideraciones:**
- ✅ Respeta tenant scoping (`organization_id`)
- ✅ Excluye proyectos eliminados (`deleted_at IS NULL`)
- ✅ Agrupa por nombre y email para evitar duplicados
- ✅ Ordena por fecha del último proyecto (más recientes primero)
- ✅ Limita resultados para evitar sobrecarga

---

### 4. ✅ Controller Method (`backend/app/controllers/project_controller.py`)

**Estado:** ⚠️ Necesita nuevo método

**Método Nuevo Requerido:**

```python
# Agregar a la clase ProjectController en backend/app/controllers/project_controller.py

async def search_clients(
    self,
    search_query: str,
    limit: int = 10
) -> ClientSearchResponse:
    """
    Buscar clientes existentes
    
    Args:
        search_query: Query de búsqueda (mínimo 2 caracteres)
        limit: Límite de resultados (default: 10, max: 50)
    
    Returns:
        ClientSearchResponse con lista de clientes encontrados
    
    Raises:
        HTTPException: Si search_query es muy corto o hay error en la búsqueda
    """
    from app.schemas.project import ClientSearchResult, ClientSearchResponse
    
    # Validar query mínimo
    if len(search_query.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must be at least 2 characters long"
        )
    
    # Validar límite
    limit = min(max(limit, 1), 50)
    
    self._log_info(
        "Searching clients",
        search_query=search_query,
        limit=limit
    )
    
    try:
        # Llamar al repository
        clients_data = await self.project_service.search_clients(
            search_query=search_query,
            limit=limit
        )
        
        # Convertir a schemas de respuesta
        clients = [
            ClientSearchResult(
                name=client["name"],
                email=client["email"],
                project_count=client["project_count"],
                last_project_date=client["last_project_date"]
            )
            for client in clients_data
        ]
        
        return ClientSearchResponse(
            clients=clients,
            total=len(clients)
        )
        
    except Exception as e:
        self._log_error(f"Error searching clients: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search clients: {str(e)}"
        )
```

**Nota:** Este método delega al `ProjectService`, que a su vez llama al `ProjectRepository`.

---

### 5. ✅ Service Method (`backend/app/services/project_service.py`)

**Estado:** ⚠️ Necesita nuevo método

**Método Nuevo Requerido:**

```python
# Agregar a la clase ProjectService en backend/app/services/project_service.py

async def search_clients(
    self,
    search_query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Buscar clientes existentes por nombre o email
    
    Args:
        search_query: Query de búsqueda
        limit: Límite de resultados
    
    Returns:
        Lista de diccionarios con información de clientes
    """
    return await self.project_repo.search_clients(
        search_query=search_query,
        limit=limit
    )
```

**Nota:** Este método simplemente delega al repository, manteniendo la separación de responsabilidades.

---

### 6. ✅ AI Service Method (`backend/app/services/ai_service.py`)

**Estado:** ⚠️ Necesita nuevo método

**Método Nuevo Requerido:**

```python
# Agregar a la clase AIService en backend/app/services/ai_service.py

async def generate_executive_summary(
    self,
    request: "ExecutiveSummaryRequest"
) -> Dict[str, Any]:
    """
    Generar resumen ejecutivo para una cotización usando IA
    
    Args:
        request: ExecutiveSummaryRequest con datos del proyecto y servicios
    
    Returns:
        Dictionary con:
        {
            "success": bool,
            "summary": str,  # Resumen ejecutivo generado
            "usage": dict,    # Información de uso de la API
            "error": str      # Solo si success=False
        }
    """
    if not self.is_available():
        return {
            "success": False,
            "error": "AI service not configured. Please set OPENAI_API_KEY in environment variables."
        }
    
    try:
        # Construir prompt
        prompt = self._build_executive_summary_prompt(request)
        
        # Determinar idioma del sistema
        system_language = "español" if request.language == "es" else "english"
        
        # Llamar a OpenAI
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": f"""Eres un experto en redacción de propuestas comerciales y resúmenes ejecutivos para agencias digitales.

Tu objetivo es crear un resumen ejecutivo profesional, conciso y persuasivo que:
1. Presente el proyecto de manera clara y profesional
2. Destaque el valor de los servicios propuestos
3. Sea apropiado para presentar a ejecutivos y tomadores de decisión
4. Mantenga un tono profesional pero accesible

Responde SIEMPRE en {system_language}.
El resumen debe tener entre 150-250 palabras.
Sé específico con los servicios pero evita jerga técnica excesiva.
Enfócate en beneficios y resultados esperados."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        summary = response.choices[0].message.content
        
        return {
            "success": True,
            "summary": summary.strip(),
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "estimated_cost": self._estimate_cost(response.usage)
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating executive summary: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Error generating executive summary: {str(e)}"
        }


def _build_executive_summary_prompt(
    self,
    request: "ExecutiveSummaryRequest"
) -> str:
    """
    Construir prompt para generación de resumen ejecutivo
    
    Args:
        request: ExecutiveSummaryRequest con datos del proyecto
    
    Returns:
        String con el prompt completo
    """
    # Construir lista de servicios
    services_text = []
    for service in request.services:
        service_line = f"- {service.service_name}"
        if service.estimated_hours:
            service_line += f" ({service.estimated_hours} horas)"
        service_line += f": {request.currency} {service.client_price:,.2f}"
        services_text.append(service_line)
    
    services_list = "\n".join(services_text)
    
    # Construir prompt
    prompt = f"""Genera un resumen ejecutivo para la siguiente propuesta comercial:

**Proyecto:** {request.project_name}
**Cliente:** {request.client_name}
{f"**Sector:** {request.client_sector}" if request.client_sector else ""}

**Servicios Incluidos:**
{services_list}

**Inversión Total:** {request.currency} {request.total_price:,.2f}

El resumen debe:
- Presentar el proyecto de manera profesional
- Destacar el valor y beneficios de los servicios
- Ser apropiado para presentar a ejecutivos
- Tener entre 150-250 palabras
- Mantener un tono profesional pero accesible
"""
    
    return prompt
```

**Nota:** Asegurarse de importar `ExecutiveSummaryRequest` desde `app.schemas.ai` (usar string para evitar importación circular).

---

### 7. ✅ Endpoint: Búsqueda de Clientes (`backend/app/api/v1/endpoints/projects.py`)

**Estado:** ⚠️ Necesita nuevo endpoint

**Endpoint Nuevo Requerido:**

```python
# Agregar después de los endpoints existentes en backend/app/api/v1/endpoints/projects.py

@router.get("/clients/search", response_model=ClientSearchResponse, summary="Search existing clients")
async def search_clients(
    q: str = Query(..., min_length=2, description="Search query (client name or email)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search existing clients by name or email
    
    This endpoint provides autocomplete functionality for client selection
    in the quote creation flow. It searches across all projects in the organization
    and returns unique clients matching the search query.
    
    **Permissions:**
    - All authenticated users can search clients for their organization
    
    **Query Parameters:**
    - `q`: Search query (minimum 2 characters) - searches in client name and email
    - `limit`: Maximum number of results (1-50, default: 10)
    
    **Returns:**
    - `200 OK`: List of matching clients
    - `400 Bad Request`: Search query too short
    - `500 Internal Server Error`: Error searching clients
    
    **Response includes:**
    - `clients`: List of matching clients with:
      - `name`: Client name
      - `email`: Client email (if available)
      - `project_count`: Number of projects with this client
      - `last_project_date`: Date of the most recent project
    - `total`: Total number of clients found
    
    **Example:**
    ```
    GET /api/v1/projects/clients/search?q=Tech&limit=5
    ```
    """
    from app.schemas.project import ClientSearchResponse
    
    controller = ProjectController(db, tenant, current_user)
    return await controller.search_clients(
        search_query=q,
        limit=limit
    )
```

**Nota:** Asegurarse de importar `ClientSearchResponse` desde `app.schemas.project`.

---

### 8. ✅ Endpoint: Generación de Resumen Ejecutivo (`backend/app/api/v1/endpoints/ai.py`)

**Estado:** ⚠️ Necesita nuevo endpoint

**Endpoint Nuevo Requerido:**

```python
# Agregar después de los endpoints existentes en backend/app/api/v1/endpoints/ai.py

@router.post("/generate-executive-summary", response_model=ExecutiveSummaryResponse, summary="Generate executive summary for quote")
@limiter.limit(AI_RATE_LIMIT, key_func=get_tenant_identifier)  # Rate limit: 10 requests per minute per tenant
async def generate_executive_summary(
    request: Request,
    payload: ExecutiveSummaryRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user)
):
    """
    Generate an executive summary for a quote using AI
    
    This endpoint uses OpenAI to generate a professional executive summary
    for a quote, suitable for presenting to executives and decision-makers.
    
    **Permissions:**
    - All authenticated users can generate summaries for their organization
    
    **Rate Limiting:**
    - Limited to 10 requests per minute per tenant (to control API costs)
    
    **Request Body:**
    - `project_name`: Name of the project
    - `client_name`: Name of the client
    - `client_sector`: Optional client sector (e.g., 'Technology', 'Retail')
    - `services`: List of services included in the quote (min 1)
      - `service_id`: Service ID
      - `service_name`: Service name
      - `estimated_hours`: Optional estimated hours
      - `client_price`: Price for this service
    - `total_price`: Total quote price
    - `currency`: Currency code (default: "USD")
    - `language`: Language for summary: "es" or "en" (default: "es")
    
    **Returns:**
    - `200 OK`: Executive summary generated successfully
    - `400 Bad Request`: Invalid request data
    - `503 Service Unavailable`: AI service not configured
    - `500 Internal Server Error`: Error generating summary
    
    **Response includes:**
    - `summary`: Generated executive summary (150-250 words)
    - `provider`: AI provider used ("openai")
    - `usage`: API usage information (tokens, estimated cost)
    
    **Example Request:**
    ```json
    {
      "project_name": "Rediseño de E-commerce",
      "client_name": "TechStore Inc",
      "client_sector": "Retail",
      "services": [
        {
          "service_id": 1,
          "service_name": "Diseño UI/UX",
          "estimated_hours": 80,
          "client_price": 12000
        },
        {
          "service_id": 2,
          "service_name": "Desarrollo Frontend",
          "estimated_hours": 120,
          "client_price": 18000
        }
      ],
      "total_price": 30000,
      "currency": "USD",
      "language": "es"
    }
    ```
    """
    from app.schemas.ai import ExecutiveSummaryRequest, ExecutiveSummaryResponse
    
    if not ai_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=translate_error(ErrorCode.AI_SERVICE_UNAVAILABLE)
        )
    
    try:
        # Validar request
        if not payload.services or len(payload.services) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one service is required"
            )
        
        # Llamar al servicio de IA
        result = await ai_service.generate_executive_summary(payload)
        
        if not result.get('success'):
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"AI service error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=translate_error(ErrorCode.AI_PROCESSING_ERROR, detail=error_msg)
            )
        
        # Construir respuesta
        response = ExecutiveSummaryResponse(
            summary=result.get('summary', ''),
            provider="openai",
            usage=result.get('usage')
        )
        
        logger.info(
            f"Executive summary generated for project={payload.project_name}",
            extra={
                "organization_id": tenant.organization_id,
                "user_id": current_user.id,
                "project_name": payload.project_name,
                "services_count": len(payload.services),
                "language": payload.language,
                "usage": result.get('usage', {})
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_executive_summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=translate_error(ErrorCode.UNKNOWN_ERROR)
        )
```

**Nota:** Asegurarse de importar `ExecutiveSummaryRequest` y `ExecutiveSummaryResponse` desde `app.schemas.ai`.

---

## 🧪 Tests a Implementar

### 9. ✅ Tests Unitarios: Repository (`backend/tests/unit/test_project_repository.py`)

**Estado:** ⚠️ Necesita nuevos tests

**Tests Nuevos Requeridos:**

```python
# Agregar a backend/tests/unit/test_project_repository.py

import pytest
from datetime import datetime
from app.repositories.project_repository import ProjectRepository
from app.models.project import Project


@pytest.mark.asyncio
async def test_search_clients_by_name(db_session, test_organization):
    """Test búsqueda de clientes por nombre"""
    repo = ProjectRepository(db_session, tenant_id=test_organization.id)
    
    # Crear proyectos de prueba
    project1 = Project(
        name="Proyecto 1",
        client_name="TechStore Inc",
        client_email="contacto@techstore.com",
        organization_id=test_organization.id,
        currency="USD"
    )
    project2 = Project(
        name="Proyecto 2",
        client_name="TechStore Inc",
        client_email="contacto@techstore.com",
        organization_id=test_organization.id,
        currency="USD"
    )
    project3 = Project(
        name="Proyecto 3",
        client_name="Retail Corp",
        client_email="info@retail.com",
        organization_id=test_organization.id,
        currency="USD"
    )
    
    db_session.add_all([project1, project2, project3])
    await db_session.commit()
    
    # Buscar "Tech"
    results = await repo.search_clients("Tech", limit=10)
    
    assert len(results) == 1
    assert results[0]["name"] == "TechStore Inc"
    assert results[0]["email"] == "contacto@techstore.com"
    assert results[0]["project_count"] == 2


@pytest.mark.asyncio
async def test_search_clients_by_email(db_session, test_organization):
    """Test búsqueda de clientes por email"""
    repo = ProjectRepository(db_session, tenant_id=test_organization.id)
    
    # Crear proyecto de prueba
    project = Project(
        name="Proyecto 1",
        client_name="Cliente ABC",
        client_email="contacto@cliente.com",
        organization_id=test_organization.id,
        currency="USD"
    )
    
    db_session.add(project)
    await db_session.commit()
    
    # Buscar por email
    results = await repo.search_clients("contacto@cliente", limit=10)
    
    assert len(results) == 1
    assert results[0]["name"] == "Cliente ABC"
    assert results[0]["email"] == "contacto@cliente.com"


@pytest.mark.asyncio
async def test_search_clients_respects_tenant(db_session, test_organization, other_organization):
    """Test que la búsqueda respeta tenant scoping"""
    repo = ProjectRepository(db_session, tenant_id=test_organization.id)
    
    # Crear proyectos en diferentes organizaciones
    project1 = Project(
        name="Proyecto Org 1",
        client_name="Cliente Org 1",
        organization_id=test_organization.id,
        currency="USD"
    )
    project2 = Project(
        name="Proyecto Org 2",
        client_name="Cliente Org 2",
        organization_id=other_organization.id,
        currency="USD"
    )
    
    db_session.add_all([project1, project2])
    await db_session.commit()
    
    # Buscar "Cliente"
    results = await repo.search_clients("Cliente", limit=10)
    
    # Solo debe encontrar clientes de test_organization
    assert len(results) == 1
    assert results[0]["name"] == "Cliente Org 1"


@pytest.mark.asyncio
async def test_search_clients_excludes_deleted(db_session, test_organization):
    """Test que la búsqueda excluye proyectos eliminados"""
    repo = ProjectRepository(db_session, tenant_id=test_organization.id)
    
    from datetime import datetime
    
    # Crear proyecto activo y eliminado
    project1 = Project(
        name="Proyecto Activo",
        client_name="Cliente Activo",
        organization_id=test_organization.id,
        currency="USD"
    )
    project2 = Project(
        name="Proyecto Eliminado",
        client_name="Cliente Eliminado",
        organization_id=test_organization.id,
        currency="USD",
        deleted_at=datetime.utcnow()
    )
    
    db_session.add_all([project1, project2])
    await db_session.commit()
    
    # Buscar "Cliente"
    results = await repo.search_clients("Cliente", limit=10)
    
    # Solo debe encontrar cliente activo
    assert len(results) == 1
    assert results[0]["name"] == "Cliente Activo"


@pytest.mark.asyncio
async def test_search_clients_limit(db_session, test_organization):
    """Test que el límite de resultados funciona correctamente"""
    repo = ProjectRepository(db_session, tenant_id=test_organization.id)
    
    # Crear múltiples proyectos con diferentes clientes
    for i in range(15):
        project = Project(
            name=f"Proyecto {i}",
            client_name=f"Cliente {i}",
            organization_id=test_organization.id,
            currency="USD"
        )
        db_session.add(project)
    
    await db_session.commit()
    
    # Buscar con límite de 5
    results = await repo.search_clients("Cliente", limit=5)
    
    assert len(results) <= 5
```

---

### 10. ✅ Tests Unitarios: Service (`backend/tests/unit/test_project_service.py`)

**Estado:** ⚠️ Necesita nuevos tests

**Tests Nuevos Requeridos:**

```python
# Agregar a backend/tests/unit/test_project_service.py

import pytest
from app.services.project_service import ProjectService
from app.models.project import Project


@pytest.mark.asyncio
async def test_search_clients_delegates_to_repository(db_session, test_organization, mocker):
    """Test que el servicio delega correctamente al repository"""
    service = ProjectService(db_session, test_organization.id)
    
    # Mock del repository
    mock_results = [
        {
            "name": "Cliente Test",
            "email": "test@cliente.com",
            "project_count": 2,
            "last_project_date": None
        }
    ]
    
    mocker.patch.object(
        service.project_repo,
        'search_clients',
        return_value=mock_results
    )
    
    # Llamar al servicio
    results = await service.search_clients("Cliente", limit=10)
    
    # Verificar que se llamó al repository
    service.project_repo.search_clients.assert_called_once_with("Cliente", limit=10)
    assert results == mock_results
```

---

### 11. ✅ Tests Unitarios: AI Service (`backend/tests/unit/test_ai_service.py`)

**Estado:** ⚠️ Necesita nuevos tests

**Tests Nuevos Requeridos:**

```python
# Agregar a backend/tests/unit/test_ai_service.py

import pytest
from decimal import Decimal
from app.services.ai_service import AIService
from app.schemas.ai import ExecutiveSummaryRequest, ExecutiveSummaryService


@pytest.mark.asyncio
async def test_generate_executive_summary_success(mocker):
    """Test generación exitosa de resumen ejecutivo"""
    # Mock de OpenAI client
    mock_client = mocker.MagicMock()
    mock_response = mocker.MagicMock()
    mock_response.choices = [mocker.MagicMock()]
    mock_response.choices[0].message.content = "Este es un resumen ejecutivo de prueba."
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150
    
    mock_client.chat.completions.create = mocker.AsyncMock(return_value=mock_response)
    
    # Crear servicio con mock
    service = AIService()
    service.client = mock_client
    
    # Crear request
    request = ExecutiveSummaryRequest(
        project_name="Proyecto Test",
        client_name="Cliente Test",
        client_sector="Tecnología",
        services=[
            ExecutiveSummaryService(
                service_id=1,
                service_name="Desarrollo Frontend",
                estimated_hours=80,
                client_price=Decimal("12000")
            )
        ],
        total_price=Decimal("12000"),
        currency="USD",
        language="es"
    )
    
    # Llamar al servicio
    result = await service.generate_executive_summary(request)
    
    # Verificar resultado
    assert result["success"] is True
    assert "summary" in result
    assert result["summary"] == "Este es un resumen ejecutivo de prueba."
    assert "usage" in result
    assert result["usage"]["total_tokens"] == 150


@pytest.mark.asyncio
async def test_generate_executive_summary_ai_not_available():
    """Test que retorna error cuando IA no está disponible"""
    service = AIService()
    service.client = None  # Simular que no está configurado
    
    request = ExecutiveSummaryRequest(
        project_name="Proyecto Test",
        client_name="Cliente Test",
        services=[
            ExecutiveSummaryService(
                service_id=1,
                service_name="Servicio Test",
                client_price=Decimal("1000")
            )
        ],
        total_price=Decimal("1000"),
        currency="USD"
    )
    
    result = await service.generate_executive_summary(request)
    
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_build_executive_summary_prompt():
    """Test construcción de prompt para resumen ejecutivo"""
    service = AIService()
    
    request = ExecutiveSummaryRequest(
        project_name="Proyecto Test",
        client_name="Cliente Test",
        client_sector="Tecnología",
        services=[
            ExecutiveSummaryService(
                service_id=1,
                service_name="Desarrollo Frontend",
                estimated_hours=80,
                client_price=Decimal("12000")
            ),
            ExecutiveSummaryService(
                service_id=2,
                service_name="Diseño UI/UX",
                client_price=Decimal("8000")
            )
        ],
        total_price=Decimal("20000"),
        currency="USD",
        language="es"
    )
    
    prompt = service._build_executive_summary_prompt(request)
    
    # Verificar que el prompt contiene información relevante
    assert "Proyecto Test" in prompt
    assert "Cliente Test" in prompt
    assert "Tecnología" in prompt
    assert "Desarrollo Frontend" in prompt
    assert "Diseño UI/UX" in prompt
    assert "USD" in prompt
    assert "20,000" in prompt or "20000" in prompt
```

---

### 12. ✅ Tests de Integración: Endpoints (`backend/tests/integration/test_quote_creation_endpoints.py`)

**Estado:** ⚠️ Archivo nuevo

**Tests Nuevos Requeridos:**

```python
# Crear archivo backend/tests/integration/test_quote_creation_endpoints.py

import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from app.models.project import Project


@pytest.mark.asyncio
async def test_search_clients_endpoint_success(client: TestClient, auth_headers, test_organization):
    """Test endpoint de búsqueda de clientes - éxito"""
    # Crear proyectos de prueba
    project1 = Project(
        name="Proyecto 1",
        client_name="TechStore Inc",
        client_email="contacto@techstore.com",
        organization_id=test_organization.id,
        currency="USD"
    )
    project2 = Project(
        name="Proyecto 2",
        client_name="TechStore Inc",
        client_email="contacto@techstore.com",
        organization_id=test_organization.id,
        currency="USD"
    )
    
    # Guardar proyectos (usar fixture de db_session)
    # ... código para guardar proyectos ...
    
    # Llamar al endpoint
    response = client.get(
        "/api/v1/projects/clients/search?q=Tech&limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "clients" in data
    assert "total" in data
    assert len(data["clients"]) > 0
    assert data["clients"][0]["name"] == "TechStore Inc"


@pytest.mark.asyncio
async def test_search_clients_endpoint_query_too_short(client: TestClient, auth_headers):
    """Test endpoint de búsqueda - query muy corto"""
    response = client.get(
        "/api/v1/projects/clients/search?q=T&limit=10",
        headers=auth_headers
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_generate_executive_summary_endpoint_success(client: TestClient, auth_headers, mocker):
    """Test endpoint de generación de resumen ejecutivo - éxito"""
    # Mock de OpenAI (requiere configuración de API key en tests)
    # ... código de mock ...
    
    payload = {
        "project_name": "Proyecto Test",
        "client_name": "Cliente Test",
        "client_sector": "Tecnología",
        "services": [
            {
                "service_id": 1,
                "service_name": "Desarrollo Frontend",
                "estimated_hours": 80,
                "client_price": "12000"
            }
        ],
        "total_price": "12000",
        "currency": "USD",
        "language": "es"
    }
    
    response = client.post(
        "/api/v1/ai/generate-executive-summary",
        json=payload,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "provider" in data
    assert data["provider"] == "openai"


@pytest.mark.asyncio
async def test_generate_executive_summary_endpoint_ai_not_available(client: TestClient, auth_headers, mocker):
    """Test endpoint de generación - IA no disponible"""
    # Mock para simular que IA no está disponible
    # ... código de mock ...
    
    payload = {
        "project_name": "Proyecto Test",
        "client_name": "Cliente Test",
        "services": [
            {
                "service_id": 1,
                "service_name": "Servicio Test",
                "client_price": "1000"
            }
        ],
        "total_price": "1000",
        "currency": "USD"
    }
    
    response = client.post(
        "/api/v1/ai/generate-executive-summary",
        json=payload,
        headers=auth_headers
    )
    
    assert response.status_code == 503
```

---

## 🔧 Consideraciones Técnicas

### 1. **Tenant Scoping**
- ✅ Todos los nuevos endpoints respetan tenant scoping automáticamente
- ✅ `ProjectRepository.search_clients()` filtra por `organization_id`
- ✅ Los tests verifican que no se filtren datos entre organizaciones

### 2. **Rate Limiting**
- ✅ El endpoint de IA tiene rate limiting: `10 requests/minute per tenant`
- ✅ Usa `@limiter.limit()` decorator con `get_tenant_identifier`
- ✅ Previene abuso y controla costos de API

### 3. **Validación de Datos**
- ✅ Búsqueda de clientes: mínimo 2 caracteres
- ✅ Límite de resultados: 1-50 (default: 10)
- ✅ Resumen ejecutivo: al menos 1 servicio requerido
- ✅ Idioma: solo "es" o "en"

### 4. **Manejo de Errores**
- ✅ Errores de validación: `400 Bad Request`
- ✅ IA no disponible: `503 Service Unavailable`
- ✅ Errores de procesamiento: `500 Internal Server Error`
- ✅ Logging estructurado en todos los niveles

### 5. **Performance**
- ✅ Búsqueda de clientes: usa `GROUP BY` y `LIMIT` para eficiencia
- ✅ Ordenamiento por fecha más reciente (índice recomendado en `created_at`)
- ✅ Cache no requerido inicialmente (puede agregarse después si es necesario)

### 6. **Seguridad**
- ✅ Autenticación requerida en todos los endpoints (`get_current_user`)
- ✅ Tenant scoping automático (no se pueden ver datos de otras organizaciones)
- ✅ Validación de entrada en todos los niveles (Pydantic + manual)

### 7. **Compatibilidad**
- ✅ **No afecta endpoints existentes:** Todos los cambios son aditivos
- ✅ **No modifica schemas existentes:** Solo agrega nuevos schemas
- ✅ **No cambia comportamiento existente:** Los nuevos métodos son independientes

---

## 📝 Plan de Implementación por Fases

### **Fase 1: Schemas y Repository (Día 1)**
1. ✅ Agregar `ClientSearchResult` y `ClientSearchResponse` a `schemas/project.py`
2. ✅ Agregar `ExecutiveSummaryService`, `ExecutiveSummaryRequest`, `ExecutiveSummaryResponse` a `schemas/ai.py`
3. ✅ Implementar `ProjectRepository.search_clients()`
4. ✅ Tests unitarios del repository

### **Fase 2: Services y Controllers (Día 1-2)**
1. ✅ Implementar `ProjectService.search_clients()`
2. ✅ Implementar `ProjectController.search_clients()`
3. ✅ Implementar `AIService.generate_executive_summary()` y `_build_executive_summary_prompt()`
4. ✅ Tests unitarios de services y controllers

### **Fase 3: Endpoints (Día 2)**
1. ✅ Implementar `GET /api/v1/projects/clients/search`
2. ✅ Implementar `POST /api/v1/ai/generate-executive-summary`
3. ✅ Tests de integración de endpoints

### **Fase 4: Testing y Documentación (Día 2-3)**
1. ✅ Ejecutar suite completa de tests
2. ✅ Verificar cobertura de tests
3. ✅ Actualizar documentación de API (si aplica)
4. ✅ Code review

### **Fase 5: Deployment (Día 3)**
1. ✅ Merge a branch de desarrollo
2. ✅ Testing en ambiente de staging
3. ✅ Deploy a producción

---

## ✅ Checklist de Implementación

### Schemas
- [ ] `ClientSearchResult` y `ClientSearchResponse` en `schemas/project.py`
- [ ] `ExecutiveSummaryService`, `ExecutiveSummaryRequest`, `ExecutiveSummaryResponse` en `schemas/ai.py`
- [ ] Imports correctos y `DECIMAL_CONFIG` aplicado

### Repository
- [ ] `ProjectRepository.search_clients()` implementado
- [ ] Tenant scoping verificado
- [ ] Exclusión de proyectos eliminados verificada
- [ ] Tests unitarios del repository pasando

### Services
- [ ] `ProjectService.search_clients()` implementado
- [ ] `AIService.generate_executive_summary()` implementado
- [ ] `AIService._build_executive_summary_prompt()` implementado
- [ ] Manejo de errores (IA no disponible)
- [ ] Tests unitarios de services pasando

### Controllers
- [ ] `ProjectController.search_clients()` implementado
- [ ] Validación de entrada
- [ ] Logging estructurado
- [ ] Manejo de excepciones

### Endpoints
- [ ] `GET /api/v1/projects/clients/search` implementado
- [ ] `POST /api/v1/ai/generate-executive-summary` implementado
- [ ] Rate limiting en endpoint de IA
- [ ] Documentación de endpoints (docstrings)
- [ ] Tests de integración pasando

### Testing
- [ ] Tests unitarios del repository (5+ tests)
- [ ] Tests unitarios del service (2+ tests)
- [ ] Tests unitarios del AI service (3+ tests)
- [ ] Tests de integración de endpoints (4+ tests)
- [ ] Cobertura de tests > 80%

### Documentación
- [ ] Docstrings completos en todos los métodos
- [ ] Ejemplos de uso en docstrings de endpoints
- [ ] README actualizado (si aplica)

---

## 🚀 Próximos Pasos

1. **Implementar Fase 1:** Schemas y Repository
2. **Implementar Fase 2:** Services y Controllers
3. **Implementar Fase 3:** Endpoints
4. **Implementar Fase 4:** Testing completo
5. **Implementar Fase 5:** Deployment

---

## 📚 Referencias

- **Arquitectura:** `.cursorrules/nougram_backend_rules.md`
- **Frontend Plan:** [2026-02-07-PLAN_TRABAJO_COTIZACION_FRONTEND.md](./2026-02-07-PLAN_TRABAJO_COTIZACION_FRONTEND.md)
- **Onboarding Backend Plan:** [2026-02-07-PLAN_TRABAJO_ONBOARDING_BACKEND.md](./2026-02-07-PLAN_TRABAJO_ONBOARDING_BACKEND.md) (referencia de estructura)
- **Endpoints Existentes:** `backend/app/api/v1/endpoints/projects.py`, `backend/app/api/v1/endpoints/quotes.py`
- **AI Service:** `backend/app/services/ai_service.py`

---

**Nota Final:** Este plan está diseñado para ser **completamente compatible** con el código existente. Todos los cambios son **aditivos** y **no modifican** funcionalidades previamente desarrolladas.
