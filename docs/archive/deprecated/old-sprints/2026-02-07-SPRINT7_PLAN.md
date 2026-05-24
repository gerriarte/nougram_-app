# Sprint 7: Facturación y Suscripciones - Plan

**Fecha de inicio:** 15 de Diciembre, 2025  
**Duración:** 2 semanas  
**Estado:** En planificación  
**Dependencias:** Sprint 6 completado ✅

---

## Objetivo

Implementar sistema completo de facturación y suscripciones con integración de Stripe, permitiendo a las organizaciones gestionar sus planes de suscripción y pagos.

---

## Alcance

### Backend
1. **Modelo de Subscription** - Historial de cambios de suscripción
2. **Integración Stripe** - API y webhooks
3. **Endpoints de facturación** - Checkout, gestión de suscripciones
4. **Configuración de planes** - Precios y límites por plan

### Frontend (Opcional para este sprint)
- Página de planes y precios
- Dashboard de facturación
- Gestión de suscripción

---

## Tareas Detalladas

### 1. Modelo de Subscription

**Archivo:** `backend/app/models/subscription.py` (nuevo)

```python
class Subscription(Base):
    """
    Subscription history and billing information
    Tracks subscription changes, payments, and billing cycles
    """
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Stripe integration
    stripe_subscription_id = Column(String, unique=True, nullable=True, index=True)
    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_price_id = Column(String, nullable=True)
    
    # Subscription details
    plan = Column(String, nullable=False)  # free, starter, professional, enterprise
    status = Column(String, nullable=False)  # active, cancelled, past_due, trialing, incomplete
    
    # Billing information
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Payment information
    latest_invoice_id = Column(String, nullable=True)
    default_payment_method = Column(String, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional Stripe metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="subscriptions")
```

**Campos clave:**
- `stripe_subscription_id`: ID único de Stripe
- `stripe_customer_id`: ID del cliente en Stripe
- `plan` y `status`: Estado actual de la suscripción
- `current_period_start/end`: Período de facturación actual
- `cancel_at_period_end`: Si está cancelada al final del período

**Migración:**
- Crear tabla `subscriptions`
- Agregar relación en `Organization` model
- Índices para búsquedas frecuentes

---

### 2. Integración Stripe

**Archivo:** `backend/app/core/stripe_service.py` (nuevo)

**Funcionalidades:**

#### 2.1 Configuración
- Variables de entorno:
  - `STRIPE_SECRET_KEY`
  - `STRIPE_PUBLISHABLE_KEY`
  - `STRIPE_WEBHOOK_SECRET`
  - `STRIPE_PRICE_IDS` (JSON con price IDs por plan)

#### 2.2 Cliente Stripe
```python
import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY
```

#### 2.3 Funciones principales

**create_customer()**
- Crear cliente en Stripe
- Asociar email y metadata de organización
- Retornar `customer_id`

**create_subscription()**
- Crear suscripción en Stripe
- Asociar precio según plan
- Configurar período de prueba si aplica
- Retornar `subscription_id`

**update_subscription()**
- Cambiar plan de suscripción
- Manejar upgrade/downgrade
- Pro-rate si necesario

**cancel_subscription()**
- Cancelar suscripción inmediata o al final del período
- Manejar diferentes tipos de cancelación

**get_subscription()**
- Obtener información actualizada de Stripe
- Sincronizar estado con base de datos

**create_checkout_session()**
- Crear sesión de checkout para nuevos usuarios
- URL de éxito/cancelación
- Metadata de organización

---

### 3. Webhook Handler

**Archivo:** `backend/app/api/v1/endpoints/stripe_webhooks.py` (nuevo)

**Eventos a manejar:**

#### 3.1 Eventos de Suscripción
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `customer.subscription.trial_will_end`

#### 3.2 Eventos de Pago
- `invoice.payment_succeeded`
- `invoice.payment_failed`
- `invoice.payment_action_required`

#### 3.3 Eventos de Cliente
- `customer.created`
- `customer.updated`
- `customer.deleted`

**Flujo:**
1. Recibir webhook de Stripe
2. Verificar firma del webhook
3. Procesar evento según tipo
4. Actualizar base de datos
5. Sincronizar estado con Organization

**Seguridad:**
- Verificación de firma de webhook
- Idempotencia (evitar procesar eventos duplicados)
- Logging de todos los eventos

---

### 4. Endpoints de Facturación

**Archivo:** `backend/app/api/v1/endpoints/billing.py` (nuevo)

#### 4.1 Checkout y Suscripción

**POST /api/v1/billing/create-checkout-session**
- Crear sesión de checkout de Stripe
- Redirigir a Stripe para pago
- Metadata: organization_id, plan, user_id

**POST /api/v1/billing/create-portal-session**
- Crear sesión de portal de cliente de Stripe
- Permitir gestionar suscripción, facturas, métodos de pago

**POST /api/v1/billing/subscribe**
- Suscribir organización a un plan
- Crear customer si no existe
- Crear suscripción en Stripe
- Actualizar Organization y crear Subscription

**PUT /api/v1/billing/subscription/{subscription_id}**
- Actualizar suscripción (cambiar plan)
- Manejar upgrade/downgrade
- Validar límites del nuevo plan

**DELETE /api/v1/billing/subscription/{subscription_id}**
- Cancelar suscripción
- Opción: cancelación inmediata vs al final del período

#### 4.2 Consulta de Estado

**GET /api/v1/billing/subscription**
- Obtener suscripción actual de la organización
- Incluir información de facturación
- Estado y fechas importantes

**GET /api/v1/billing/invoices**
- Listar facturas históricas
- Paginación
- Filtros por estado

**GET /api/v1/billing/plans**
- Listar planes disponibles
- Precios y límites
- Información de features

---

### 5. Schemas

**Archivo:** `backend/app/schemas/billing.py` (nuevo)

```python
class SubscriptionResponse(BaseModel):
    """Subscription information"""
    id: int
    organization_id: int
    plan: str
    status: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    stripe_subscription_id: Optional[str]
    stripe_customer_id: Optional[str]

class CheckoutSessionRequest(BaseModel):
    """Request to create checkout session"""
    plan: str
    success_url: str
    cancel_url: str

class CheckoutSessionResponse(BaseModel):
    """Response with checkout URL"""
    session_id: str
    url: str

class SubscriptionUpdateRequest(BaseModel):
    """Request to update subscription"""
    plan: Optional[str] = None
    cancel_at_period_end: Optional[bool] = None

class PlanResponse(BaseModel):
    """Available plan information"""
    id: str
    name: str
    price_monthly: Optional[float]
    price_yearly: Optional[float]
    features: List[str]
    limits: Dict[str, int]

class InvoiceResponse(BaseModel):
    """Invoice information"""
    id: str
    amount: float
    currency: str
    status: str
    created_at: datetime
    paid_at: Optional[datetime]
    invoice_url: Optional[str]
```

---

### 6. Repository

**Archivo:** `backend/app/repositories/subscription_repository.py` (nuevo)

**Métodos:**
- `get_active_subscription(organization_id)`
- `create_subscription(data)`
- `update_subscription(subscription_id, data)`
- `cancel_subscription(subscription_id, cancel_immediately)`
- `get_subscription_by_stripe_id(stripe_subscription_id)`
- `get_invoices(organization_id, limit, offset)`

---

### 7. Configuración de Planes

**Actualizar:** `backend/app/core/plan_limits.py`

**Agregar precios:**
```python
PLAN_PRICES = {
    "free": {
        "monthly": 0,
        "yearly": 0,
        "stripe_price_id_monthly": None,
        "stripe_price_id_yearly": None
    },
    "starter": {
        "monthly": 29.99,
        "yearly": 299.99,  # 2 meses gratis
        "stripe_price_id_monthly": "price_xxx",
        "stripe_price_id_yearly": "price_yyy"
    },
    "professional": {
        "monthly": 99.99,
        "yearly": 999.99,
        "stripe_price_id_monthly": "price_zzz",
        "stripe_price_id_yearly": "price_www"
    },
    "enterprise": {
        "monthly": None,  # Contactar para precio
        "yearly": None,
        "stripe_price_id_monthly": None,
        "stripe_price_id_yearly": None
    }
}
```

---

### 8. Actualización de Organization Model

**Modificar:** `backend/app/models/organization.py`

**Agregar relación:**
```python
subscriptions = relationship("Subscription", back_populates="organization", lazy="dynamic")
```

---

## Flujos Principales

### Flujo 1: Nueva Suscripción
1. Usuario selecciona plan
2. Frontend llama a `POST /billing/create-checkout-session`
3. Backend crea sesión en Stripe
4. Usuario completa pago en Stripe
5. Stripe envía webhook `checkout.session.completed`
6. Backend crea `Subscription` y actualiza `Organization`

### Flujo 2: Cambio de Plan
1. Usuario solicita cambio de plan
2. Frontend llama a `PUT /billing/subscription/{id}`
3. Backend actualiza suscripción en Stripe
4. Stripe envía webhook `customer.subscription.updated`
5. Backend sincroniza estado

### Flujo 3: Cancelación
1. Usuario cancela suscripción
2. Frontend llama a `DELETE /billing/subscription/{id}`
3. Backend cancela en Stripe (al final del período)
4. Stripe envía webhook `customer.subscription.updated`
5. Backend marca como cancelada

---

## Variables de Entorno Necesarias

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Price IDs (JSON)
STRIPE_PRICE_IDS={"starter_monthly":"price_xxx","starter_yearly":"price_yyy",...}
```

---

## Tests

### Tests Unitarios
- `test_stripe_service.py` - Funciones de Stripe
- `test_subscription_repository.py` - CRUD de subscriptions

### Tests de Integración
- `test_billing_endpoints.py` - Endpoints de facturación
- `test_stripe_webhooks.py` - Procesamiento de webhooks
- `test_subscription_flows.py` - Flujos completos

---

## Criterios de Aceptación

- [ ] Modelo Subscription creado y migrado
- [ ] Integración con Stripe funcionando
- [ ] Webhook handler procesando eventos correctamente
- [ ] Endpoints de facturación implementados
- [ ] Checkout session funcionando
- [ ] Portal de cliente funcionando
- [ ] Cambio de planes funcionando
- [ ] Cancelación de suscripción funcionando
- [ ] Sincronización automática con webhooks
- [ ] Tests pasando (unitarios e integración)
- [ ] Documentación de API actualizada

---

## Próximos Pasos

1. Instalar dependencia: `stripe`
2. Crear modelo Subscription
3. Crear migración
4. Implementar stripe_service.py
5. Crear endpoints de billing
6. Implementar webhook handler
7. Crear tests
8. Documentar API

---

**Última actualización:** 15 de Diciembre, 2025













