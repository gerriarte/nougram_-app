# Análisis: Módulo Quotes - Arquitectura MVC

**Fecha:** 2026-01-25  
**Documento Base:** [2026-01-25-BACKEND_IMPLEMENTATION_STATUS_QUOTE_CRUD.md](./2026-01-25-BACKEND_IMPLEMENTATION_STATUS_QUOTE_CRUD.md)  
**Arquitectura:** MVC + Repository/Service (`.cursorrules/nougram_backend_rules.md`)

---

## 📊 Resumen Ejecutivo

El módulo **Quotes** está **PARCIALMENTE refactorizado** bajo la arquitectura MVC. Existen componentes (`QuoteController`, `QuoteView`), pero **NO se están utilizando** en los endpoints principales de cálculo.

### Estado Actual
- ✅ `QuoteController` existe y maneja operaciones CRUD básicas
- ✅ `QuoteView` existe y transforma datos
- ❌ **Endpoints de cálculo NO usan Controller/Service**
- ❌ **No existe `QuoteService`** para lógica de negocio de cálculos
- ❌ **Endpoints acceden directamente a DB** (violación de arquitectura)

---

## 🔍 Análisis Detallado

### 1. Endpoint `POST /api/v1/quotes/calculate` ❌

**Ubicación:** `backend/app/api/v1/endpoints/quotes.py:25`

**Problemas Identificados:**

#### ❌ Violación 1: Acceso Directo a Base de Datos
```python
# Líneas 50-58: Acceso directo a DB desde endpoint
result = await db.execute(
    select(Service).where(Service.id == item.service_id, Service.is_active == True)
)
service = result.scalar_one_or_none()
```

**Debería ser:**
- Usar `ServiceRepository` a través de `QuoteService`
- El endpoint solo debe delegar al Controller

#### ❌ Violación 2: Lógica de Negocio en Endpoint
```python
# Líneas 60-96: Validaciones de pricing types directamente en endpoint
effective_pricing_type = item.pricing_type or service.pricing_type or "hourly"
if effective_pricing_type == "hourly":
    if not item.estimated_hours or item.estimated_hours <= 0:
        raise HTTPException(...)
# ... más validaciones
```

**Debería ser:**
- Mover validaciones a `QuoteService.validate_quote_items()`
- El endpoint solo debe pasar datos al Controller

#### ❌ Violación 3: Cálculos Directos en Endpoint
```python
# Líneas 98-115: Obtención de configuración y cálculo de BCR
result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))
org = result.scalar_one_or_none()
# ...
blended_rate = await calculate_blended_cost_rate(db, ...)
```

**Debería ser:**
- Mover a `QuoteService.calculate_blended_cost_rate()`
- Usar `OrganizationRepository` a través del Service

#### ❌ Violación 4: Construcción de Respuesta Directa
```python
# Líneas 166-181: Construcción directa de respuesta
return QuoteCalculateResponse(
    total_internal_cost=Decimal(str(totals["total_internal_cost"])),
    # ... más campos
)
```

**Debería ser:**
- Usar `QuoteView.to_calculate_response()` para transformar datos
- El endpoint solo debe retornar lo que devuelve el Controller

**Líneas de Código con Lógica:** ~180 líneas que deberían estar en Service

---

### 2. Endpoint `GET /api/v1/quotes/{quote_id}/rentability` ❌

**Ubicación:** `backend/app/api/v1/endpoints/quotes.py:184`

**Problemas Identificados:**

#### ❌ Violación 1: Acceso Directo a Base de Datos
```python
# Líneas 200-202: Acceso directo a DB
result = await db.execute(select(Quote).filter(Quote.id == quote_id))
quote = result.scalar_one_or_none()
```

**Debería ser:**
- Usar `ProjectRepository.get_quote_by_id()` a través de `QuoteService`
- Validar permisos en el Service

#### ❌ Violación 2: Validación de Permisos en Endpoint
```python
# Líneas 212-222: Validación de organización directamente en endpoint
result = await db.execute(select(Project).where(Project.id == quote.project_id))
project = result.scalar_one_or_none()
if not project or project.organization_id != current_user.organization_id:
    raise HTTPException(...)
```

**Debería ser:**
- Mover validación a `QuoteService.get_quote_rentability()`
- El Service debe usar `TenantContext` para validar tenant

#### ❌ Violación 3: Llamada Directa a Función de Cálculo
```python
# Línea 225: Llamada directa sin pasar por Service
analysis = await calculate_rentability_analysis(db, quote_id, current_user.organization_id)
```

**Debería ser:**
- Mover a `QuoteService.calculate_rentability_analysis()`
- El Service debe manejar errores y transformar respuestas

**Líneas de Código con Lógica:** ~50 líneas que deberían estar en Service

---

## ✅ Componentes Existentes (Correctos)

### `QuoteController` ✅
**Ubicación:** `backend/app/controllers/quote_controller.py`

**Estado:** Correctamente implementado para operaciones CRUD
- ✅ `get_quote()` - Usa Repository y View
- ✅ `list_project_quotes()` - Usa Repository y View
- ✅ `create_new_version()` - Delega a `ProjectService`
- ✅ `send_quote_email()` - Delega a `ProjectService`

**Limitación:** Solo maneja operaciones relacionadas con Projects, no cálculos independientes.

### `QuoteView` ✅
**Ubicación:** `backend/app/views/quote_view.py`

**Estado:** Correctamente implementado
- ✅ `to_response()` - Transforma Quote a QuoteResponse
- ✅ `to_response_with_items()` - Transforma Quote a QuoteResponseWithItems

**Limitación:** No tiene método para transformar respuestas de cálculo (`QuoteCalculateResponse`).

---

## ❌ Componentes Faltantes

### 1. `QuoteService` ❌

**Necesario para:**
- Validar items de quote según tipo de pricing
- Calcular BCR antes de calcular quote
- Ejecutar cálculos de quote usando `calculate_quote_totals_enhanced`
- Calcular rentabilidad usando `calculate_rentability_analysis`
- Manejar errores de negocio y transformarlos en excepciones apropiadas

**Métodos Requeridos:**
```python
class QuoteService:
    async def validate_quote_items(self, items: List[QuoteItemCreate]) -> None
    async def calculate_quote_totals(self, request: QuoteCalculateRequest) -> QuoteCalculateResponse
    async def get_quote_rentability(self, quote_id: int) -> RentabilitySummaryResponse
    async def _get_blended_cost_rate(self) -> float
    async def _get_organization_settings(self) -> Dict[str, Any]
```

---

### 2. Métodos Faltantes en `QuoteView` ❌

**Necesario agregar:**
```python
class QuoteView:
    def to_calculate_response(self, totals: Dict[str, Any]) -> QuoteCalculateResponse
    def to_rentability_response(self, analysis: Dict[str, Any]) -> RentabilitySummaryResponse
```

---

### 3. Métodos Faltantes en `QuoteController` ❌

**Necesario agregar:**
```python
class QuoteController:
    async def calculate_quote(self, request: QuoteCalculateRequest) -> QuoteCalculateResponse
    async def get_quote_rentability(self, quote_id: int) -> RentabilitySummaryResponse
```

---

## 📋 Plan de Refactorización

### Paso 1: Crear `QuoteService` ✅ Prioridad Alta

**Archivo:** `backend/app/services/quote_service.py`

**Responsabilidades:**
1. Validar items de quote (servicios existentes, campos requeridos según pricing type)
2. Obtener configuración de organización (moneda primaria, configuración social)
3. Calcular BCR antes de calcular quote
4. Ejecutar cálculos usando `calculate_quote_totals_enhanced`
5. Calcular rentabilidad usando `calculate_rentability_analysis`
6. Manejar errores y transformarlos en excepciones apropiadas

**Dependencias:**
- `ServiceRepository` - Para validar servicios
- `OrganizationRepository` - Para obtener configuración
- `app.core.calculations` - Para cálculos (ya existe)

---

### Paso 2: Extender `QuoteView` ✅ Prioridad Alta

**Archivo:** `backend/app/views/quote_view.py`

**Agregar métodos:**
- `to_calculate_response()` - Transformar resultado de cálculo a `QuoteCalculateResponse`
- `to_rentability_response()` - Transformar análisis de rentabilidad a `RentabilitySummaryResponse`

---

### Paso 3: Extender `QuoteController` ✅ Prioridad Alta

**Archivo:** `backend/app/controllers/quote_controller.py`

**Agregar métodos:**
- `calculate_quote()` - Delegar a `QuoteService.calculate_quote_totals()`
- `get_quote_rentability()` - Delegar a `QuoteService.get_quote_rentability()`

**Responsabilidades:**
- Validar request HTTP
- Delegar a Service
- Manejar errores HTTP
- Usar View para transformar respuestas

---

### Paso 4: Refactorizar Endpoints ✅ Prioridad Alta

**Archivo:** `backend/app/api/v1/endpoints/quotes.py`

**Cambios:**
1. **Endpoint `POST /calculate`:**
   ```python
   @router.post("/calculate", response_model=QuoteCalculateResponse)
   async def calculate_quote(
       request: QuoteCalculateRequest,
       tenant: TenantContext = Depends(get_tenant_context),
       current_user: User = Depends(require_create_quotes),
       db: AsyncSession = Depends(get_db)
   ):
       controller = QuoteController(db, tenant, current_user)
       return await controller.calculate_quote(request)
   ```

2. **Endpoint `GET /{quote_id}/rentability`:**
   ```python
   @router.get("/{quote_id}/rentability", response_model=RentabilitySummaryResponse)
   async def get_quote_rentability(
       quote_id: int,
       tenant: TenantContext = Depends(get_tenant_context),
       current_user: User = Depends(get_current_user),
       db: AsyncSession = Depends(get_db)
   ):
       controller = QuoteController(db, tenant, current_user)
       return await controller.get_quote_rentability(quote_id)
   ```

**Resultado:** Endpoints de ~5-10 líneas cada uno, sin lógica de negocio.

---

## 📊 Comparación: Antes vs Después

### Antes (Actual) ❌
```
Endpoint (180 líneas)
├── Acceso directo a DB
├── Validaciones de negocio
├── Cálculos directos
└── Construcción de respuesta
```

### Después (Objetivo) ✅
```
Endpoint (5 líneas)
└── Controller (10 líneas)
    └── Service (100 líneas)
        ├── Repository
        └── Calculations
    └── View (transformación)
```

---

## ✅ Checklist de Refactorización

- [ ] Crear `QuoteService` con métodos de cálculo
- [ ] Agregar métodos a `QuoteView` para respuestas de cálculo
- [ ] Agregar métodos a `QuoteController` para cálculos
- [ ] Refactorizar endpoint `POST /calculate` para usar Controller
- [ ] Refactorizar endpoint `GET /{quote_id}/rentability` para usar Controller
- [ ] Eliminar acceso directo a DB desde endpoints
- [ ] Mover todas las validaciones a Service
- [ ] Mover todos los cálculos a Service
- [ ] Usar View para todas las transformaciones de respuesta
- [ ] Verificar que no hay errores de linter
- [ ] Actualizar documentación de estado

---

## 🎯 Impacto Esperado

### Beneficios
1. **Separación de Responsabilidades:** Lógica de negocio centralizada en Service
2. **Testabilidad:** Fácil testear Service sin necesidad de HTTP
3. **Reutilización:** Service puede ser usado por otros componentes
4. **Mantenibilidad:** Código más organizado y fácil de mantener
5. **Consistencia:** Mismo patrón que otros módulos refactorizados

### Métricas
- **Líneas de código en endpoints:** Reducción de ~230 líneas a ~15 líneas
- **Líneas de código en Service:** ~150 líneas nuevas (lógica movida)
- **Cobertura de arquitectura:** 100% (actualmente ~30%)

---

## 📝 Notas Técnicas

### Dependencias Existentes
- ✅ `app.core.calculations` - Funciones de cálculo ya implementadas
- ✅ `ServiceRepository` - Ya existe y funciona
- ✅ `OrganizationRepository` - Ya existe y funciona
- ✅ `ProjectRepository` - Ya existe con métodos para quotes

### Consideraciones
1. **BCR Calculation:** Ya existe `calculate_blended_cost_rate()` en `app.core.calculations`, solo necesita ser llamado desde Service
2. **Quote Totals:** Ya existe `calculate_quote_totals_enhanced()` en `app.core.calculations`, solo necesita ser llamado desde Service
3. **Rentability:** Ya existe `calculate_rentability_analysis()` en `app.core.calculations`, solo necesita ser llamado desde Service
4. **Tenant Scoping:** El Service debe usar `organization_id` del `TenantContext` para todas las operaciones

---

**Fin del Documento**
