# Plan de Trabajo Backend - Dashboard Comercial y Pipeline de Envío

**Versión:** 1.0  
**Fecha:** 2026-01-25  
**Documento Base:** `UI_REQUIREMENTS_QUOTES_DASHBOARD.md`  
**Estado:** Pendiente de Implementación

---

## Resumen Ejecutivo

Este documento detalla el plan de trabajo para implementar las funcionalidades de backend requeridas para el Dashboard Comercial y Pipeline de Envío de Cotizaciones. El plan está organizado por sprints con prioridades claras y estimaciones de tiempo.

**Objetivo:** Implementar sistema completo de tracking, estados extendidos, métricas avanzadas y gestión de versiones para cotizaciones.

**Duración Estimada Total:** 4-5 sprints (8-10 semanas)  
**Prioridad:** Alta (funcionalidad core del producto)

---

## 🎛️ ARQUITECTURA DEL FEATURE FLAG DE TRACKING

### Diseño del Módulo Activable/Desactivable

**Principio:** El tracking de cotizaciones debe ser un módulo completamente opcional que se puede activar/desactivar sin afectar la funcionalidad básica del sistema.

### Niveles de Configuración

**1. Nivel de Organización (Feature Flag Principal):**
```python
Organization.settings = {
    "quote_tracking": {
        "enabled": True  # Feature flag principal
    }
}
```

**2. Nivel de Cotización (Estado Individual):**
```python
Quote.tracking_enabled = True  # Indica si esta cotización específica tiene tracking
Quote.tracking_token = "abc123..."  # Token único (NULL si tracking desactivado)
```

**Lógica de Herencia:**
- Si `Organization.settings["quote_tracking"]["enabled"] = False` → Todas las cotizaciones nuevas NO tendrán tracking
- Si `Organization.settings["quote_tracking"]["enabled"] = True` → Las cotizaciones nuevas SÍ tendrán tracking
- Cotizaciones existentes mantienen su estado (`Quote.tracking_enabled`)

### Comportamiento cuando Tracking Desactivado

**Envío de Emails:**
- ✅ Email se envía normalmente
- ❌ NO se incluye pixel de tracking
- ❌ NO se genera `tracking_token`
- ❌ NO se registra evento "sent"
- ✅ PDF usa URL normal (sin token)

**Tracking de Aperturas:**
- ✅ Pixel endpoint existe (para compatibilidad con emails ya enviados)
- ❌ NO registra evento si tracking desactivado
- ✅ Retorna pixel 1x1px transparente (no rompe emails)

**Tracking de Descargas:**
- ✅ PDF se descarga normalmente
- ❌ NO registra evento si tracking desactivado
- ✅ Usa URL normal (sin token)

**Métricas y Dashboard:**
- ✅ Dashboard funciona normalmente
- ⚠️ Métricas basadas en tracking muestran valores por defecto
- ⚠️ Mensaje informativo: "Activa el tracking para ver métricas detalladas"
- ✅ Métricas que no dependen de tracking funcionan normalmente (Win Rate, Total Cotizado)

### Endpoint de Configuración

**Actualizar Configuración:**
```python
PUT /api/v1/organizations/{organization_id}/quote-tracking-config
Body: {
    "enabled": true,
    "track_email_opens": true,
    "track_pdf_downloads": true,
    "track_location": false,
    "track_device_info": true,
    "notify_on_events": true
}
```

**Obtener Configuración:**
```python
GET /api/v1/organizations/{organization_id}/quote-tracking-config
Response: {
    "enabled": true,
    "track_email_opens": true,
    ...
}
```

### Consideraciones de Privacidad

**GDPR Compliance:**
- Usuario debe ser informado sobre qué datos se recopilan
- Opción clara de desactivar completamente
- Cuando desactivado, NO se recopilan datos nuevos
- Datos existentes se pueden exportar/eliminar

**Transparencia:**
- Mostrar badge en UI: "Tracking activado" / "Tracking desactivado"
- Mensaje informativo cuando desactivado
- Explicar beneficios sin ser intrusivo

### Migración y Compatibilidad

**Organizaciones Existentes:**
- Default: `enabled = True` (tracking activado)
- Usuarios pueden desactivar desde configuración
- No requiere migración de datos

**Cotizaciones Existentes:**
- Mantienen su estado actual
- Si tenían tracking, siguen teniéndolo
- Si no tenían tracking, pueden activarlo para nuevas cotizaciones

**Emails ya Enviados:**
- Si email ya tiene pixel con token → Pixel funciona pero NO registra si tracking desactivado
- Si email tiene URL única → URL funciona pero NO registra si tracking desactivado
- No se rompen emails ya enviados

---

## 📊 ANÁLISIS DE ESTADO ACTUAL

### ✅ Implementado

1. **Modelos Básicos:**
   - `Project` con estados básicos (Draft, Sent, Won, Lost)
   - `Quote` con versiones (campo `version`)
   - `QuoteItem` y `QuoteExpense`
   - Relaciones entre modelos

2. **Sistema de Envío:**
   - Endpoint `POST /api/v1/projects/{project_id}/quotes/{quote_id}/send-email`
   - Generación de PDFs y DOCX
   - Templates de email HTML y texto
   - Soporte para CC, BCC, adjuntos

3. **Métricas Básicas:**
   - Endpoint `GET /api/v1/insights/dashboard`
   - Cálculo de conversion_rate (Sent → Won)
   - Total revenue, average margin
   - Filtros básicos (fecha, estado, cliente, moneda)

4. **Listado de Cotizaciones:**
   - Endpoint `GET /api/v1/projects/{project_id}/quotes`
   - Paginación básica

### ❌ No Implementado (Crítico)

1. **Sistema de Tracking:**
   - Pixel de seguimiento para emails
   - URLs únicas para PDFs
   - Modelo `QuoteTrackingEvent`
   - Campos de tracking en `Quote`

2. **Estados Extendidos:**
   - Viewed, Accepted, Rejected, Expired
   - Lógica de transición de estados
   - Expiración automática (30 días)

3. **Métricas Avanzadas:**
   - Pipeline Value (Sent + Viewed)
   - Win Rate específico de cotizaciones
   - Cotizaciones que requieren atención
   - Análisis de interés

4. **Filtros Avanzados:**
   - Por nivel de rentabilidad
   - Por rango de monto
   - Búsqueda inteligente
   - Ordenamiento avanzado

5. **Gestión de Versiones:**
   - Comparación de versiones
   - Duplicación de cotizaciones
   - Historial de versiones

---

## 🎯 PLAN DE TRABAJO POR SPRINTS

---

## SPRINT 1: Sistema de Tracking Core (Prioridad: CRÍTICA)

**Duración:** 2 semanas  
**Objetivo:** Implementar sistema completo de tracking de aperturas y descargas como módulo activable/desactivable

### Tarea 1.0: Configuración de Feature Flag de Tracking (NUEVA)

**Archivo:** `backend/app/models/organization.py` y `backend/app/schemas/organization.py`

**Objetivo:** Permitir activar/desactivar tracking a nivel de organización

**Cambios en Organization.settings:**
```python
# En settings JSON de Organization:
{
    "quote_tracking": {
        "enabled": True,  # Feature flag principal
        "track_email_opens": True,  # Pixel de tracking
        "track_pdf_downloads": True,  # URLs únicas
        "track_location": False,  # Geolocalización (opcional, más sensible)
        "track_device_info": True,  # User-Agent, dispositivo
        "notify_on_events": True  # Notificaciones en tiempo real
    }
}
```

**Schema:**
```python
class QuoteTrackingConfig(BaseModel):
    """Schema for quote tracking configuration"""
    enabled: bool = Field(default=True, description="Enable quote tracking module")
    track_email_opens: bool = Field(default=True, description="Track email opens with pixel")
    track_pdf_downloads: bool = Field(default=True, description="Track PDF downloads with unique URLs")
    track_location: bool = Field(default=False, description="Track approximate location (IP-based)")
    track_device_info: bool = Field(default=True, description="Track device and browser info")
    notify_on_events: bool = Field(default=True, description="Send notifications on tracking events")
```

**Endpoint para Gestionar Configuración:**
```python
@router.put("/{organization_id}/quote-tracking-config")
async def update_quote_tracking_config(
    organization_id: int,
    config: QuoteTrackingConfig,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualizar configuración de tracking de cotizaciones
    Solo owner/admin puede modificar
    """
```

**Utilidad para Verificar Configuración:**
```python
# backend/app/core/quote_tracking_config.py (nuevo)
def is_tracking_enabled(organization: Organization) -> bool:
    """Check if tracking is enabled for organization"""
    if not organization.settings:
        return True  # Default: enabled
    tracking_config = organization.settings.get("quote_tracking", {})
    return tracking_config.get("enabled", True)

def get_tracking_config(organization: Organization) -> Dict:
    """Get tracking configuration with defaults"""
    if not organization.settings:
        return {"enabled": True, "track_email_opens": True, ...}
    return organization.settings.get("quote_tracking", {
        "enabled": True,
        "track_email_opens": True,
        "track_pdf_downloads": True,
        "track_location": False,
        "track_device_info": True,
        "notify_on_events": True
    })
```

**Estimación:** 3 horas  
**Dependencias:** Ninguna  
**Prioridad:** CRÍTICA (debe hacerse primero)

---

### Tarea 1.1: Extender Modelo Quote con Campos de Tracking

**Archivo:** `backend/app/models/project.py`

**Cambios:**
```python
class Quote(Base):
    # ... campos existentes ...
    
    # Tracking fields
    sent_at = Column(DateTime(timezone=True), nullable=True, index=True)
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    viewed_count = Column(Integer, default=0, nullable=False)
    last_viewed_at = Column(DateTime(timezone=True), nullable=True)
    downloaded_count = Column(Integer, default=0, nullable=False)
    last_downloaded_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    tracking_token = Column(String(64), unique=True, nullable=True, index=True)
    tracking_enabled = Column(Boolean, default=True, nullable=False)
```

**Estimación:** 2 horas  
**Dependencias:** Tarea 1.0

---

### Tarea 1.2: Crear Modelo QuoteTrackingEvent

**Archivo:** `backend/app/models/quote_tracking.py` (nuevo)

**Código:**
```python
class QuoteTrackingEvent(Base):
    __tablename__ = "quote_tracking_events"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False, index=True)
    event_type = Column(String(32), nullable=False, index=True)  # sent, opened, downloaded, accepted, rejected
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Tracking metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(512), nullable=True)
    location = Column(String(255), nullable=True)  # Ciudad, País
    device_type = Column(String(32), nullable=True)  # Desktop, Mobile, Tablet
    browser = Column(String(64), nullable=True)  # Chrome, Firefox, Safari
    email_address = Column(String(255), nullable=True)  # Email del destinatario
    
    # Relationships
    quote = relationship("Quote", back_populates="tracking_events")
```

**Estimación:** 1 hora  
**Dependencias:** Tarea 1.1

---

### Tarea 1.3: Crear Migración de Base de Datos

**Archivo:** `backend/alembic/versions/XXXX_add_quote_tracking.py` (nuevo)

**Contenido:**
- Agregar campos de tracking a tabla `quotes`
- Crear tabla `quote_tracking_events`
- Crear índices necesarios
- Migrar datos existentes (si aplica)

**Estimación:** 2 horas  
**Dependencias:** Tarea 1.1, 1.2

---

### Tarea 1.4: Crear Servicio de Tracking

**Archivo:** `backend/app/services/quote_tracking_service.py` (nuevo)

**Métodos Requeridos:**
```python
class QuoteTrackingService:
    @staticmethod
    async def is_tracking_enabled_for_quote(quote_id: int, db: AsyncSession) -> bool:
        """Check if tracking is enabled for quote's organization"""
    
    @staticmethod
    async def generate_tracking_token(quote_id: int) -> str
    
    @staticmethod
    async def record_email_sent(quote_id: int, email: str, user_id: int, db: AsyncSession)
    
    @staticmethod
    async def record_email_opened(
        quote_id: int, 
        token: str, 
        request: Request, 
        db: AsyncSession
    ):
        """
        Record email opened ONLY if tracking is enabled
        Returns early if disabled
        """
    
    @staticmethod
    async def record_pdf_downloaded(
        quote_id: int, 
        token: str, 
        request: Request, 
        db: AsyncSession
    ):
        """
        Record PDF download ONLY if tracking is enabled
        Returns early if disabled
        """
    
    @staticmethod
    async def get_tracking_summary(quote_id: int, db: AsyncSession) -> Dict:
        """
        Get tracking summary
        Returns empty/zero values if tracking disabled
        """
    
    @staticmethod
    async def get_tracking_timeline(quote_id: int, db: AsyncSession) -> List[Dict]:
        """
        Get tracking timeline
        Returns empty list if tracking disabled
        """
    
    @staticmethod
    async def analyze_interest_level(quote_id: int, db: AsyncSession) -> Dict:
        """
        Analyze interest level
        Returns default/low interest if tracking disabled
        """
```

**Lógica Condicional:**
- Todos los métodos deben verificar `is_tracking_enabled_for_quote()` primero
- Si tracking está desactivado:
  - `record_email_opened()` y `record_pdf_downloaded()` retornan sin hacer nada
  - `get_tracking_summary()` retorna valores por defecto (0 aperturas, 0 descargas)
  - `get_tracking_timeline()` retorna lista vacía
  - `analyze_interest_level()` retorna nivel "low" con mensaje explicativo

**Estimación:** 5 horas (incluye lógica condicional)  
**Dependencias:** Tarea 1.0, 1.2

---

### Tarea 1.5: Implementar Pixel de Tracking

**Archivo:** `backend/app/api/v1/endpoints/tracking.py` (nuevo)

**Endpoint:**
```python
@router.get("/pixel/{quote_id}/{token}")
async def tracking_pixel(
    quote_id: int,
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Pixel de tracking de 1x1px transparente
    Registra apertura de email y retorna imagen PNG
    
    IMPORTANTE: Si tracking está desactivado para la organización,
    retorna pixel sin registrar evento (para no romper emails ya enviados)
    """
    # Verificar si tracking está habilitado
    # Si no, retornar pixel sin registrar
    # Si sí, registrar evento y retornar pixel
```

**Comportamiento cuando Tracking Desactivado:**
- Retorna pixel 1x1px transparente (para no romper emails ya enviados)
- NO registra evento en base de datos
- NO actualiza contadores
- Log opcional para debugging

**Estimación:** 2.5 horas (incluye lógica condicional)  
**Dependencias:** Tarea 1.0, 1.4

---

### Tarea 1.6: Implementar URL Única para PDFs

**Archivo:** `backend/app/api/v1/endpoints/projects.py`

**Modificar endpoint existente:**
```python
@router.get("/{project_id}/quotes/{quote_id}/pdf/{token}")
async def download_quote_pdf_with_tracking(
    project_id: int,
    quote_id: int,
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Descargar PDF con tracking
    Registra descarga antes de retornar PDF
    
    IMPORTANTE: Si tracking está desactivado, retorna PDF sin registrar
    """
    # Verificar si tracking está habilitado
    # Si no, retornar PDF sin registrar evento
    # Si sí, registrar evento y retornar PDF
```

**Comportamiento cuando Tracking Desactivado:**
- Retorna PDF normalmente (funcionalidad básica no se afecta)
- NO registra evento de descarga
- NO actualiza contadores
- Log opcional para debugging

**Estimación:** 2.5 horas (incluye lógica condicional)  
**Dependencias:** Tarea 1.0, 1.4

---

### Tarea 1.7: Integrar Pixel en Templates de Email

**Archivo:** `backend/app/core/email.py`

**Modificar `generate_quote_email_html()`:**
```python
def generate_quote_email_html(
    project_name: str,
    client_name: str,
    quote_version: int,
    total_with_taxes: float,
    currency: str = "USD",
    notes: Optional[str] = None,
    agency_name: str = "Nougram",
    tracking_enabled: bool = True,  # NUEVO parámetro
    tracking_token: Optional[str] = None,  # NUEVO parámetro
    quote_id: Optional[int] = None  # NUEVO parámetro
) -> str:
    """
    Generar HTML de email con pixel de tracking condicional
    """
    html = f"""
    ...
    {f'<img src="{FRONTEND_URL}/api/v1/tracking/pixel/{quote_id}/{tracking_token}" width="1" height="1" style="display:none;" />' if tracking_enabled and tracking_token and quote_id else ''}
    ...
    """
```

**Lógica:**
- Solo incluir pixel si `tracking_enabled=True` Y `tracking_token` existe
- Si tracking desactivado, no incluir pixel (emails más limpios)

**Estimación:** 1.5 horas (incluye parámetros nuevos)  
**Dependencias:** Tarea 1.0, 1.5

---

### Tarea 1.8: Modificar Envío de Email para Usar URLs Únicas

**Archivo:** `backend/app/api/v1/endpoints/projects.py`

**Modificar `send_quote_email()`:**
```python
async def send_quote_email(...):
    # Obtener configuración de tracking de la organización
    organization = await get_organization(tenant.organization_id, db)
    tracking_config = get_tracking_config(organization)
    tracking_enabled = is_tracking_enabled(organization)
    
    # Generar tracking_token SOLO si tracking está habilitado
    tracking_token = None
    if tracking_enabled:
        tracking_token = await QuoteTrackingService.generate_tracking_token(quote_id)
        quote.tracking_token = tracking_token
        quote.tracking_enabled = True
    
    # Generar HTML con pixel condicional
    html_body = generate_quote_email_html(
        ...,
        tracking_enabled=tracking_enabled,
        tracking_token=tracking_token,
        quote_id=quote_id if tracking_enabled else None
    )
    
    # Usar URL única para PDF SOLO si tracking habilitado
    pdf_url = f"/quotes/{quote_id}/pdf/{tracking_token}" if tracking_enabled else f"/quotes/{quote_id}/pdf"
    
    # Registrar evento "sent" SOLO si tracking habilitado
    if tracking_enabled:
        await QuoteTrackingService.record_email_sent(...)
        quote.sent_at = datetime.utcnow()
        quote.expires_at = datetime.utcnow() + timedelta(days=30)
```

**Lógica Condicional:**
- Si tracking desactivado: usar URLs normales, no generar token, no registrar eventos
- Si tracking activado: usar URLs únicas, generar token, registrar eventos

**Estimación:** 4 horas (incluye lógica condicional completa)  
**Dependencias:** Tarea 1.0, 1.4, 1.6, 1.7

---

### Tarea 1.9: Endpoint para Obtener Tracking de Cotización

**Archivo:** `backend/app/api/v1/endpoints/projects.py`

**Endpoint:**
```python
@router.get("/{project_id}/quotes/{quote_id}/tracking")
async def get_quote_tracking(
    project_id: int,
    quote_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener resumen y timeline de tracking
    """
```

**Estimación:** 2 horas  
**Dependencias:** Tarea 1.4

---

### Tarea 1.10: Utilidad para Geolocalización (Opcional)

**Archivo:** `backend/app/core/geolocation.py` (nuevo)

**Funcionalidad:**
- Usar servicio de geolocalización por IP (ej: ipapi.co, MaxMind)
- Obtener ciudad y país desde IP
- Cachear resultados para evitar rate limits

**Estimación:** 3 horas  
**Dependencias:** Ninguna  
**Prioridad:** Media (puede hacerse después)

---

**Total Sprint 1:** ~25 horas (3.5 días de desarrollo)

**Nota Importante sobre Tracking Desactivado:**
- Cuando tracking está desactivado, el sistema debe funcionar normalmente
- Los emails se envían sin pixel de tracking
- Los PDFs usan URLs normales (sin token)
- No se registran eventos de tracking
- Las métricas muestran valores por defecto o mensaje "Tracking desactivado"
- El usuario puede activar/desactivar en cualquier momento desde configuración
- Los endpoints de tracking deben ser "graceful" (no fallar si tracking desactivado)

**Checklist de Implementación del Feature Flag:**
- [ ] Configuración en `Organization.settings`
- [ ] Schema `QuoteTrackingConfig`
- [ ] Endpoint para gestionar configuración
- [ ] Utilidad `is_tracking_enabled()` y `get_tracking_config()`
- [ ] Lógica condicional en todos los métodos de tracking
- [ ] Lógica condicional en envío de emails
- [ ] Lógica condicional en endpoints de pixel y PDF
- [ ] Mensajes informativos en métricas cuando tracking desactivado
- [ ] Tests para ambos casos (activado/desactivado)

---

## SPRINT 2: Estados Extendidos y Transiciones (Prioridad: ALTA)

**Duración:** 1.5 semanas  
**Objetivo:** Implementar estados Viewed, Accepted, Rejected, Expired y lógica de transiciones

### Tarea 2.1: Extender Estados de Project

**Archivo:** `backend/app/models/project.py`

**Modificar enum:**
```python
class ProjectStatus(str, enum.Enum):
    DRAFT = "Draft"
    SENT = "Sent"
    VIEWED = "Viewed"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    EXPIRED = "Expired"
    WON = "Won"  # Mantener para compatibilidad
    LOST = "Lost"  # Mantener para compatibilidad
```

**Estimación:** 1 hora  
**Dependencias:** Ninguna

---

### Tarea 2.2: Crear Servicio de Gestión de Estados

**Archivo:** `backend/app/services/quote_status_service.py` (nuevo)

**Métodos:**
```python
class QuoteStatusService:
    @staticmethod
    async def mark_as_viewed(quote_id: int, db: AsyncSession)
    
    @staticmethod
    async def mark_as_accepted(quote_id: int, user_id: int, db: AsyncSession)
    
    @staticmethod
    async def mark_as_rejected(quote_id: int, user_id: int, reason: Optional[str], db: AsyncSession)
    
    @staticmethod
    async def check_and_mark_expired(db: AsyncSession)
    
    @staticmethod
    async def can_transition(current_status: str, new_status: str) -> bool
```

**Estimación:** 3 horas  
**Dependencias:** Tarea 2.1

---

### Tarea 2.3: Integrar Cambio de Estado en Tracking

**Archivo:** `backend/app/services/quote_tracking_service.py`

**Modificar:**
- `record_email_opened()`: Si es primera apertura, cambiar estado a "Viewed"
- Actualizar `viewed_at` y `viewed_count`

**Estimación:** 1 hora  
**Dependencias:** Tarea 1.4, 2.2

---

### Tarea 2.4: Endpoints para Cambiar Estado Manualmente

**Archivo:** `backend/app/api/v1/endpoints/projects.py`

**Endpoints:**
```python
@router.post("/{project_id}/quotes/{quote_id}/accept")
async def accept_quote(...)

@router.post("/{project_id}/quotes/{quote_id}/reject")
async def reject_quote(...)
```

**Estimación:** 2 horas  
**Dependencias:** Tarea 2.2

---

### Tarea 2.5: Tarea Celery para Marcar Expiradas

**Archivo:** `backend/app/core/celery_app.py`

**Tarea:**
```python
@celery_app.task
async def check_expired_quotes():
    """
    Marcar cotizaciones como expiradas si expires_at < ahora
    Ejecutar diariamente
    """
```

**Estimación:** 2 horas  
**Dependencias:** Tarea 2.2

---

### Tarea 2.6: Actualizar Schemas de Quote

**Archivo:** `backend/app/schemas/project.py`

**Agregar campos de tracking:**
```python
class QuoteResponse(BaseModel):
    # ... campos existentes ...
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    viewed_count: int = 0
    last_viewed_at: Optional[datetime] = None
    downloaded_count: int = 0
    last_downloaded_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    tracking_token: Optional[str] = None
```

**Estimación:** 1 hora  
**Dependencias:** Tarea 1.1

---

**Total Sprint 2:** ~10 horas (1.5 días de desarrollo)

---

## SPRINT 3: Métricas Avanzadas y Dashboard (Prioridad: ALTA)

**Duración:** 1.5 semanas  
**Objetivo:** Implementar métricas específicas de cotizaciones y alertas

### Tarea 3.1: Extender Endpoint de Dashboard con Métricas de Cotizaciones

**Archivo:** `backend/app/api/v1/endpoints/insights.py`

**Agregar métricas:**
```python
@router.get("/quotes-metrics")
async def get_quotes_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Métricas específicas de cotizaciones:
    - Total Cotizado
    - Pipeline Value (Sent + Viewed)
    - Win Rate (Accepted / (Accepted + Rejected))
    - Margen Promedio
    - Cotizaciones por Estado
    """
```

**Estimación:** 4 horas  
**Dependencias:** Sprint 2

---

### Tarea 3.2: Implementar Pipeline Value

**Lógica:**
- Suma de `total_client_price` donde estado IN ('Sent', 'Viewed')
- Excluir Draft, Accepted, Rejected, Expired
- Contar número de cotizaciones

**Estimación:** 1 hora  
**Dependencias:** Tarea 3.1

---

### Tarea 3.3: Implementar Win Rate de Cotizaciones

**Lógica:**
- Contar Accepted y Rejected en período
- Fórmula: `(Accepted / (Accepted + Rejected)) * 100`
- Comparar con período anterior

**Estimación:** 2 horas  
**Dependencias:** Tarea 3.1

---

### Tarea 3.4: Endpoint de Cotizaciones que Requieren Atención

**Archivo:** `backend/app/api/v1/endpoints/projects.py`

**Endpoint:**
```python
@router.get("/quotes/attention-required")
async def get_quotes_requiring_attention(
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna cotizaciones que requieren atención:
    - Vencen en próximos 3 días
    - Abiertas 5+ veces sin respuesta (SOLO si tracking habilitado)
    - Rentabilidad crítica (<15%)
    
    NOTA: Alertas basadas en tracking solo se incluyen si tracking está habilitado
    """
    # Verificar si tracking está habilitado
    # Si no, excluir alertas basadas en tracking (aperturas, etc.)
    # Si sí, incluir todas las alertas
```

**Lógica Condicional:**
- Alertas de "abiertas 5+ veces" solo si tracking habilitado
- Alertas de "vencen en X días" siempre (no depende de tracking)
- Alertas de "rentabilidad crítica" siempre (no depende de tracking)

**Estimación:** 3.5 horas (incluye lógica condicional)  
**Dependencias:** Sprint 1, Sprint 2

---

### Tarea 3.5: Implementar Análisis de Interés

**Archivo:** `backend/app/services/quote_tracking_service.py`

**Método:**
```python
@staticmethod
async def analyze_interest_level(quote_id: int, db: AsyncSession) -> Dict:
    """
    Analiza patrones de apertura/descarga y determina nivel de interés
    Retorna: {
        "level": "high" | "medium" | "low" | "unknown",
        "signals": [...],
        "recommendation": "...",
        "tracking_enabled": bool
    }
    
    IMPORTANTE: Si tracking está desactivado, retorna:
    {
        "level": "unknown",
        "signals": [],
        "recommendation": "Activa el tracking para obtener análisis de interés",
        "tracking_enabled": False
    }
    """
    # Verificar si tracking está habilitado
    # Si no, retornar análisis por defecto
    # Si sí, analizar patrones reales
```

**Estimación:** 3.5 horas (incluye lógica condicional y mensajes informativos)  
**Dependencias:** Tarea 1.0, 1.4

---

### Tarea 3.6: Agregar Cálculo de Rentabilidad por Cotización

**Archivo:** `backend/app/services/quote_service.py` (nuevo o existente)

**Método:**
```python
@staticmethod
def calculate_profitability_status(margin_percentage: float) -> str:
    """
    Determina estado de rentabilidad:
    - "healthy" (>30%)
    - "acceptable" (15-30%)
    - "critical" (<15%)
    """
```

**Estimación:** 1 hora  
**Dependencias:** Ninguna

---

**Total Sprint 3:** ~15 horas (2 días de desarrollo)

**Nota sobre Métricas con Tracking Desactivado:**
- Pipeline Value: Solo cuenta cotizaciones Sent (no puede contar Viewed sin tracking)
- Win Rate: Funciona normalmente (no depende de tracking)
- Análisis de Interés: Retorna "unknown" con mensaje informativo
- Alertas: Solo alertas que no dependen de tracking (vencimiento, rentabilidad)

---

## SPRINT 4: Filtros Avanzados y Búsqueda (Prioridad: MEDIA)

**Duración:** 1 semana  
**Objetivo:** Implementar filtros avanzados y búsqueda inteligente

### Tarea 4.1: Extender Endpoint de Listado con Filtros Avanzados

**Archivo:** `backend/app/api/v1/endpoints/projects.py`

**Modificar `list_projects()` o crear nuevo endpoint:**
```python
@router.get("/quotes")
async def list_quotes(
    # Filtros existentes
    status: Optional[str] = None,
    client_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    currency: Optional[str] = None,
    
    # Nuevos filtros
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    profitability_level: Optional[str] = None,  # healthy, acceptable, critical
    status_list: Optional[List[str]] = None,  # Múltiples estados
    
    # Búsqueda
    search: Optional[str] = None,  # Búsqueda inteligente
    
    # Ordenamiento
    sort_by: Optional[str] = None,  # created_at, amount, margin, status
    sort_order: Optional[str] = "desc",  # asc, desc
    
    # Paginación
    page: int = 1,
    page_size: int = 20,
    ...
):
```

**Estimación:** 4 horas  
**Dependencias:** Sprint 2

---

### Tarea 4.2: Implementar Filtro por Nivel de Rentabilidad

**Lógica:**
- Filtrar por `margin_percentage`:
  - healthy: > 0.30
  - acceptable: 0.15 - 0.30
  - critical: < 0.15

**Estimación:** 1 hora  
**Dependencias:** Tarea 4.1

---

### Tarea 4.3: Implementar Búsqueda Inteligente

**Lógica:**
- Buscar en: `project.name`, `project.client_name`, `quote.id`, `quote.version`
- Búsqueda parcial (ILIKE)
- Case-insensitive
- Resaltar términos encontrados (opcional, frontend)

**Estimación:** 2 horas  
**Dependencias:** Tarea 4.1

---

### Tarea 4.4: Implementar Ordenamiento Avanzado

**Campos soportados:**
- `created_at` (default)
- `total_client_price` (amount)
- `margin_percentage` (margin)
- `status`
- `viewed_count`
- `last_viewed_at`

**Estimación:** 2 horas  
**Dependencias:** Tarea 4.1

---

### Tarea 4.5: Optimizar Queries con Índices

**Archivo:** Migración de Alembic

**Índices a crear:**
- `quotes.sent_at`
- `quotes.expires_at`
- `quotes.viewed_count`
- `quotes.margin_percentage`
- `quote_tracking_events.quote_id, event_type, occurred_at`

**Estimación:** 1 hora  
**Dependencias:** Sprint 1

---

**Total Sprint 4:** ~10 horas (1.5 días de desarrollo)

---

## SPRINT 5: Gestión de Versiones (Prioridad: MEDIA)

**Duración:** 1 semana  
**Objetivo:** Implementar comparación y duplicación de versiones

### Tarea 5.1: Endpoint para Listar Versiones de Cotización

**Archivo:** `backend/app/api/v1/endpoints/projects.py`

**Endpoint:**
```python
@router.get("/{project_id}/quotes/{quote_id}/versions")
async def get_quote_versions(
    project_id: int,
    quote_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todas las versiones de una cotización
    Ordenadas por versión descendente
    """
```

**Estimación:** 2 horas  
**Dependencias:** Ninguna (campo version ya existe)

---

### Tarea 5.2: Endpoint para Duplicar Cotización

**Archivo:** `backend/app/api/v1/endpoints/projects.py`

**Endpoint:**
```python
@router.post("/{project_id}/quotes/{quote_id}/duplicate")
async def duplicate_quote(
    project_id: int,
    quote_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Duplica una cotización creando nueva versión
    Copia items, expenses, configuración
    Incrementa versión automáticamente
    """
```

**Estimación:** 4 horas  
**Dependencias:** Ninguna

---

### Tarea 5.3: Servicio para Comparar Versiones

**Archivo:** `backend/app/services/quote_service.py`

**Método:**
```python
@staticmethod
async def compare_quote_versions(
    quote_id_v1: int,
    quote_id_v2: int,
    db: AsyncSession
) -> Dict:
    """
    Compara dos versiones de cotización
    Retorna diferencias en:
    - Monto total
    - Margen
    - Items agregados/eliminados/modificados
    - Expenses agregados/eliminados/modificados
    """
```

**Estimación:** 4 horas  
**Dependencias:** Ninguna

---

### Tarea 5.4: Endpoint para Comparar Versiones

**Archivo:** `backend/app/api/v1/endpoints/projects.py`

**Endpoint:**
```python
@router.get("/{project_id}/quotes/compare")
async def compare_quotes(
    project_id: int,
    version1: int,
    version2: int,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Compara dos versiones de cotización
    Retorna diferencias detalladas
    """
```

**Estimación:** 2 horas  
**Dependencias:** Tarea 5.3

---

**Total Sprint 5:** ~12 horas (1.5 días de desarrollo)

---

## 📋 TAREAS ADICIONALES (Mejoras y Optimizaciones)

### Tarea A.1: Caching de Métricas

**Archivo:** `backend/app/api/v1/endpoints/insights.py`

**Implementar:**
- Cachear métricas del dashboard (2 minutos TTL)
- Cachear lista de cotizaciones con filtros comunes
- Invalidar cache cuando hay cambios relevantes

**Estimación:** 2 horas  
**Prioridad:** Media

---

### Tarea A.2: Notificaciones en Tiempo Real (WebSockets)

**Archivo:** `backend/app/api/v1/endpoints/websockets.py` (nuevo)

**Implementar:**
- WebSocket para notificaciones de tracking
- Notificar cuando se abre cotización
- Notificar cuando se descarga PDF
- Badge de notificaciones

**Estimación:** 6 horas  
**Prioridad:** Baja (puede usar polling inicialmente)

---

### Tarea A.3: Recordatorios Automáticos

**Archivo:** `backend/app/core/celery_app.py`

**Tarea Celery:**
```python
@celery_app.task
async def send_quote_reminders():
    """
    Enviar recordatorios automáticos:
    - Si no se abre en X días
    - Si vence en X días
    """
```

**Estimación:** 4 horas  
**Prioridad:** Baja (futuro)

---

### Tarea A.4: Tests Unitarios e Integración

**Archivos:** `backend/tests/unit/test_quote_tracking.py`, `backend/tests/integration/test_quotes_dashboard.py`

**Cubrir:**
- Tracking de aperturas (con y sin tracking habilitado)
- Tracking de descargas (con y sin tracking habilitado)
- Feature flag de tracking (activar/desactivar)
- Comportamiento cuando tracking desactivado
- Cambios de estado
- Métricas (con y sin tracking)
- Filtros y búsqueda
- Versiones

**Casos de Prueba Específicos para Feature Flag:**
- Email se envía sin pixel cuando tracking desactivado
- PDF usa URL normal cuando tracking desactivado
- No se registran eventos cuando tracking desactivado
- Métricas muestran valores por defecto cuando tracking desactivado
- Análisis de interés retorna "unknown" cuando tracking desactivado
- Activar/desactivar tracking funciona correctamente

**Estimación:** 10 horas (incluye tests de feature flag)  
**Prioridad:** Alta (debe hacerse en cada sprint)

---

## 📊 RESUMEN DE ESTIMACIONES

| Sprint | Tareas | Horas Estimadas | Días Desarrollo | Prioridad |
|--------|--------|-----------------|-----------------|-----------|
| **Sprint 1** | Tracking Core + Feature Flag | 25h | 3.5 días | CRÍTICA |
| **Sprint 2** | Estados Extendidos | 10h | 1.5 días | ALTA |
| **Sprint 3** | Métricas Avanzadas | 15h | 2 días | ALTA |
| **Sprint 4** | Filtros y Búsqueda | 10h | 1.5 días | MEDIA |
| **Sprint 5** | Gestión Versiones | 12h | 1.5 días | MEDIA |
| **Adicionales** | Mejoras | 20h | 2.5 días | Variable |
| **TOTAL** | | **92 horas** | **~13 días** | |

**Nota:** Las horas aumentaron ligeramente por la implementación del feature flag y lógica condicional en todos los métodos de tracking.

---

## 🎯 PRIORIZACIÓN Y DEPENDENCIAS

### Fase 1 (Crítica - Sprint 1-2): Fundación
- Sistema de tracking completo
- Estados extendidos
- **Sin esto, el dashboard no puede funcionar**

### Fase 2 (Alta - Sprint 3): Métricas
- Métricas avanzadas
- Alertas y análisis
- **Necesario para valor del producto**

### Fase 3 (Media - Sprint 4-5): Mejoras UX
- Filtros avanzados
- Gestión de versiones
- **Mejora experiencia pero no bloqueante**

---

## 🔧 CONSIDERACIONES TÉCNICAS

### Feature Flag de Tracking

**Configuración:**
- Almacenada en `Organization.settings["quote_tracking"]`
- Configurable por organización (multi-tenant)
- Default: `enabled=True` (tracking activado por defecto)
- Solo owner/admin puede modificar

**Granularidad:**
- `enabled`: Feature flag principal (activa/desactiva todo)
- `track_email_opens`: Control específico de pixel
- `track_pdf_downloads`: Control específico de URLs únicas
- `track_location`: Control de geolocalización (más sensible)
- `track_device_info`: Control de información de dispositivo
- `notify_on_events`: Control de notificaciones

**Comportamiento cuando Desactivado:**
- Emails se envían normalmente (sin pixel)
- PDFs usan URLs normales (sin token)
- No se registran eventos de tracking
- Métricas muestran valores por defecto o mensajes informativos
- Dashboard funciona normalmente (sin datos de tracking)

**Migración de Datos:**
- Organizaciones existentes: Tracking activado por defecto
- Usuarios pueden desactivar desde configuración
- Datos de tracking existentes se mantienen (solo lectura)

**Privacidad y GDPR:**
- Usuario debe ser informado sobre tracking
- Opción clara de desactivar
- Datos de tracking se pueden exportar/eliminar
- Cumplimiento con regulaciones de privacidad

### Base de Datos

**Migraciones Requeridas:**
1. Agregar campos de tracking a `quotes`
2. Crear tabla `quote_tracking_events`
3. Crear índices para performance
4. Migrar datos existentes (si aplica)

**Índices Críticos:**
- `quotes.tracking_token` (único)
- `quotes.sent_at` (filtros por fecha)
- `quotes.expires_at` (tarea de expiración)
- `quote_tracking_events.quote_id, event_type, occurred_at` (queries de timeline)

### Performance

**Optimizaciones:**
- Usar `selectinload` para cargar relaciones
- Paginación en todos los listados
- Cachear métricas calculadas
- Índices en campos de filtrado frecuente

**Límites:**
- Máximo 50 cotizaciones por página
- Timeout de 30s para queries complejas
- Rate limiting en endpoints de tracking

### Seguridad

**Tracking:**
- Validar token antes de registrar evento
- No exponer información sensible en tracking
- Anonimizar IPs (solo primeros 3 octetos)
- Rate limiting en pixel de tracking

**Permisos:**
- Solo usuarios de la organización pueden ver tracking
- Validar tenant en todos los endpoints
- Auditoría de cambios de estado

### Privacidad

**GDPR Compliance:**
- **Feature Flag Principal:** Usuario puede desactivar tracking completamente
- Informar sobre tracking en términos de servicio
- Opción clara y visible de desactivar desde configuración
- Anonimizar datos después de X tiempo
- Exportar/eliminar datos de tracking
- Cuando tracking desactivado, no se recopilan datos nuevos

**Transparencia:**
- Mostrar claramente en UI si tracking está activado/desactivado
- Mensaje informativo cuando tracking está desactivado: "Activa el tracking para ver cuándo los clientes abren tus cotizaciones"
- Explicar beneficios del tracking sin ser intrusivo

---

## 📝 NOTAS DE IMPLEMENTACIÓN

### Orden de Implementación Recomendado

1. **Semana 1-2:** Sprint 1 (Tracking Core)
   - Modelos y migraciones primero
   - Servicios después
   - Endpoints al final

2. **Semana 3:** Sprint 2 (Estados)
   - Extender enum primero
   - Servicio de estados
   - Integrar con tracking

3. **Semana 4:** Sprint 3 (Métricas)
   - Endpoints de métricas
   - Lógica de análisis
   - Alertas

4. **Semana 5:** Sprint 4-5 (Filtros y Versiones)
   - Filtros primero (más usado)
   - Versiones después

### Testing Strategy

**Unit Tests:**
- Servicios de tracking
- Servicios de estados
- Cálculos de métricas
- Comparación de versiones

**Integration Tests:**
- Flujo completo de envío → tracking → cambio de estado
- Endpoints de métricas con datos reales
- Filtros y búsqueda

**E2E Tests:**
- Flujo de usuario completo
- Tracking de aperturas/descargas
- Cambios de estado

### Documentación Requerida

1. **API Documentation:**
   - Actualizar OpenAPI/Swagger con nuevos endpoints
   - Documentar schemas de respuesta
   - Ejemplos de requests/responses

2. **Guía de Desarrollo:**
   - Cómo agregar nuevos eventos de tracking
   - Cómo extender métricas
   - Cómo crear nuevas versiones

3. **Guía de Usuario (Backend):**
   - Cómo interpretar métricas
   - Cómo usar análisis de interés
   - Mejores prácticas de tracking

---

## 🚀 CRITERIOS DE ÉXITO

### Definición de "Done"

**Sprint 1 (Tracking):**
- ✅ Pixel de tracking funciona y registra aperturas (cuando habilitado)
- ✅ URLs únicas funcionan y registran descargas (cuando habilitado)
- ✅ Timeline de eventos se muestra correctamente
- ✅ Feature flag funciona (activar/desactivar)
- ✅ Sistema funciona normalmente cuando tracking desactivado
- ✅ Tests pasan (cobertura >80%)

**Sprint 2 (Estados):**
- ✅ Estados Viewed, Accepted, Rejected, Expired funcionan
- ✅ Transiciones de estado son correctas
- ✅ Tarea de expiración funciona correctamente
- ✅ Tests pasan

**Sprint 3 (Métricas):**
- ✅ Todas las métricas se calculan correctamente
- ✅ Pipeline Value excluye estados correctos
- ✅ Win Rate usa fórmula correcta
- ✅ Alertas se generan correctamente

**Sprint 4 (Filtros):**
- ✅ Todos los filtros funcionan correctamente
- ✅ Búsqueda encuentra resultados relevantes
- ✅ Ordenamiento funciona en todos los campos
- ✅ Performance aceptable (<500ms para queries)

**Sprint 5 (Versiones):**
- ✅ Duplicación crea nueva versión correctamente
- ✅ Comparación muestra diferencias correctas
- ✅ Historial de versiones se muestra correctamente

---

## 📈 MÉTRICAS DE SEGUIMIENTO

### KPIs del Proyecto

- **Velocidad:** Tareas completadas por sprint
- **Calidad:** Cobertura de tests (>80%)
- **Performance:** Tiempo de respuesta de endpoints (<500ms)
- **Bugs:** Bugs críticos encontrados en producción

### Métricas de Código

- **Líneas de código:** ~2000-3000 líneas nuevas
- **Archivos nuevos:** ~8-10 archivos
- **Endpoints nuevos:** ~12-15 endpoints
- **Migraciones:** 2-3 migraciones

---

## 🔄 REVISIÓN Y AJUSTES

**Checkpoints:**
- Al final de cada sprint: Revisión de código y tests
- Semanal: Standup de progreso
- Al completar Fase 1: Demo interna
- Al completar Fase 2: Demo con stakeholders

**Ajustes:**
- Prioridades pueden cambiar según feedback
- Estimaciones pueden ajustarse según velocidad real
- Nuevas tareas pueden agregarse según necesidades

---

**Última Actualización:** 2026-01-25  
**Próxima Revisión:** Al inicio de cada sprint
