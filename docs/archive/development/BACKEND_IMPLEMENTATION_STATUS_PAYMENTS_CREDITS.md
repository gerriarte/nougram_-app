# Estado de Implementación Backend - Pagos y Créditos

**Fecha:** 2026-01-25  
**Documento Base:** `UI_REQUIREMENTS_PAYMENTS_CREDITS.md`

Este documento compara los requerimientos de UI con la implementación actual del backend para identificar qué está implementado y qué falta.

---

## ✅ IMPLEMENTADO COMPLETAMENTE

### 1. Sistema de Créditos (Core)

**✅ Modelos de Datos:**
- `CreditAccount`: Modelo completo con todos los campos requeridos
  - `credits_available`, `credits_used_total`, `credits_used_this_month`
  - `credits_per_month`, `next_reset_at`, `last_reset_at`
  - `manual_credits_bonus` y tracking de asignación manual
  
- `CreditTransaction`: Modelo completo para historial
  - `transaction_type`: subscription_grant, manual_adjustment, consumption, refund
  - `amount`, `reason`, `reference_id`, `performed_by`
  - Timestamps y relaciones

**✅ Servicio de Créditos (`CreditService`):**
- `get_or_create_credit_account()` - Crear/obtener cuenta de créditos
- `get_credit_balance()` - Obtener balance completo
- `validate_and_consume_credits()` - Validar y consumir créditos (retorna HTTP 402 si insuficientes)
- `grant_subscription_credits()` - Otorgar créditos mensuales según plan
- `grant_manual_credits()` - Otorgar créditos manuales (admin)
- `refund_credits()` - Reembolsar créditos

**✅ Endpoints de Créditos:**
- `GET /api/v1/credits/me/balance` - Obtener balance del usuario
- `GET /api/v1/credits/me/history` - Historial de transacciones (con paginación)
- `GET /api/v1/credits/admin/{org_id}/balance` - Balance admin
- `POST /api/v1/credits/admin/{org_id}/grant` - Otorgar créditos manuales
- `GET /api/v1/credits/admin/{org_id}/transactions` - Historial admin
- `POST /api/v1/credits/admin/{org_id}/reset` - Reset manual mensual

**✅ Lógica de Consumo:**
- Consumo de créditos al crear proyectos (1 crédito para product_manager)
- Validación de créditos suficientes antes de consumir
- Error HTTP 402 cuando no hay créditos suficientes
- Soporte para créditos ilimitados (NULL en `credits_per_month`)

---

### 2. Sistema de Planes y Límites

**✅ Configuración de Planes (`plan_limits.py`):**
- `PLAN_LIMITS`: Límites por plan (free, starter, professional, enterprise)
  - max_users, max_projects, max_services, max_team_members
  - credits_per_month
  
- `PLAN_INFO`: Información completa de planes
  - display_name, description
  - monthly_price, yearly_price
  - features, limits

**✅ Validación de Límites:**
- `check_limit()` - Validar límite y retornar HTTP 403 si se excede
- `validate_user_limit()` - Validar límite de usuarios
- `validate_project_limit()` - Validar límite de proyectos
- `validate_service_limit()` - Validar límite de servicios
- `validate_team_member_limit()` - Validar límite de miembros

**✅ Endpoint de Planes:**
- `GET /api/v1/billing/plans` - Listar todos los planes disponibles

---

### 3. Sistema de Suscripciones

**✅ Modelo de Suscripción (`Subscription`):**
- Campos completos: plan, status, current_period_start, current_period_end
- Estados: active, cancelled, past_due, trialing, incomplete, incomplete_expired
- Integración Stripe: stripe_subscription_id, stripe_customer_id, stripe_price_id
- Trial: trial_start, trial_end
- Cancelación: cancel_at_period_end, canceled_at
- Payment: latest_invoice_id, default_payment_method

**✅ Endpoints de Suscripción:**
- `GET /api/v1/billing/subscription` - Obtener suscripción actual
- `PUT /api/v1/billing/subscription` - Actualizar suscripción (cambiar plan)
- `POST /api/v1/billing/subscription/cancel` - Cancelar suscripción
- `POST /api/v1/billing/checkout-session` - Crear sesión de checkout

**✅ Integración Stripe:**
- `StripeService` completo con métodos:
  - `create_customer()` - Crear cliente en Stripe
  - `create_checkout_session()` - Crear sesión de checkout
  - `create_subscription()` - Crear suscripción
  - `update_subscription()` - Actualizar suscripción
  - `cancel_subscription()` - Cancelar suscripción
  - `get_price_id()` - Obtener price ID por plan e intervalo

**✅ Webhooks de Stripe:**
- `POST /api/v1/billing/webhook` - Endpoint de webhooks
- Manejo de eventos:
  - `checkout.session.completed` ✅
  - `customer.subscription.created` ✅
  - `customer.subscription.updated` ✅
  - `customer.subscription.deleted` ✅
  - `invoice.payment_succeeded` ✅
  - `invoice.payment_failed` ✅ (actualiza estado a `past_due`)

---

## ⚠️ IMPLEMENTADO PARCIALMENTE

### 1. Mapeo de Acciones a Créditos

**⚠️ Estado Actual:**
- Solo se consume 1 crédito al crear proyecto con cotización (product_manager)
- No hay mapeo granular de diferentes acciones de IA

**❌ Falta Implementar:**
- Generar propuesta estratégica con IA = 5 créditos
- Sugerencias de onboarding (IA) = 2 créditos
- Análisis financiero con IA = 3 créditos
- Optimización de cotización (IA) = 4 créditos

**📝 Recomendación:**
Crear constante o configuración con mapeo de acciones a créditos:
```python
AI_CREDIT_COSTS = {
    "quote_creation": 0,  # Manual
    "strategic_proposal": 5,
    "onboarding_suggestions": 2,
    "financial_analysis": 3,
    "quote_optimization": 4,
}
```

---

### 2. Historial de Facturas/Invoices

**⚠️ Estado Actual:**
- El modelo `Subscription` tiene `latest_invoice_id` (solo el último)
- Los webhooks manejan eventos de invoice pero no almacenan historial completo
- No hay endpoint para listar facturas

**❌ Falta Implementar:**
- Modelo `Invoice` para almacenar historial completo
- Endpoint `GET /api/v1/billing/invoices` - Listar facturas
- Endpoint `GET /api/v1/billing/invoices/{invoice_id}` - Detalles de factura
- Endpoint `GET /api/v1/billing/invoices/{invoice_id}/pdf` - Descargar PDF
- Filtros por estado (succeeded, pending, failed, void)
- Búsqueda por número, fecha, monto

**📝 Recomendación:**
Crear modelo `Invoice` y sincronizar desde Stripe:
```python
class Invoice(Base):
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    stripe_invoice_id = Column(String, unique=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    status = Column(String)  # succeeded, pending, failed, void
    amount = Column(Numeric)
    currency = Column(String)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    paid_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    # ... más campos
```

---

### 3. Stripe Customer Portal

**⚠️ Estado Actual:**
- No hay endpoint para crear sesión del Customer Portal
- El schema `BillingPortalResponse` existe pero no se usa

**❌ Falta Implementar:**
- Endpoint `POST /api/v1/billing/portal-session` - Crear sesión del portal
- Redirigir a Stripe Customer Portal para:
  - Actualizar método de pago
  - Ver historial de facturas
  - Actualizar información de facturación

**📝 Código Necesario:**
```python
@router.post("/portal-session", response_model=BillingPortalResponse)
async def create_portal_session(...):
    session = stripe.billingPortal.Session.create(
        customer=customer_id,
        return_url=return_url
    )
    return BillingPortalResponse(url=session.url)
```

---

### 4. Período de Gracia para Pagos Fallidos

**⚠️ Estado Actual:**
- Cuando falla un pago, el estado cambia a `past_due` inmediatamente
- No hay lógica de período de gracia de 3 días
- No hay contador de días restantes

**❌ Falta Implementar:**
- Campo `past_due_since` en modelo `Subscription` para trackear cuándo empezó la mora
- Lógica para calcular días restantes de gracia
- Cambio automático a `incomplete_expired` después de 3 días
- Endpoint o campo en respuesta que indique días restantes

**📝 Recomendación:**
```python
# En modelo Subscription
past_due_since = Column(DateTime(timezone=True), nullable=True)

# En servicio
def get_grace_period_remaining(subscription: Subscription) -> Optional[int]:
    if subscription.status != "past_due":
        return None
    if not subscription.past_due_since:
        return None
    days_past_due = (datetime.utcnow() - subscription.past_due_since).days
    return max(0, 3 - days_past_due)
```

---

### 5. Información de Método de Pago

**⚠️ Estado Actual:**
- El modelo tiene `default_payment_method` (ID de Stripe)
- No hay endpoint para obtener detalles del método de pago
- No se muestra información de tarjeta (últimos 4 dígitos, tipo, expiración)

**❌ Falta Implementar:**
- Endpoint `GET /api/v1/billing/payment-method` - Obtener método de pago actual
- Integración con Stripe para obtener detalles:
  - Últimos 4 dígitos de tarjeta
  - Tipo de tarjeta (Visa, Mastercard, etc.)
  - Fecha de expiración
  - Nombre en tarjeta

**📝 Código Necesario:**
```python
@router.get("/payment-method")
async def get_payment_method(...):
    if not subscription.default_payment_method:
        return None
    payment_method = stripe.PaymentMethod.retrieve(
        subscription.default_payment_method
    )
    return {
        "last4": payment_method.card.last4,
        "brand": payment_method.card.brand,
        "exp_month": payment_method.card.exp_month,
        "exp_year": payment_method.card.exp_year,
    }
```

---

## ❌ NO IMPLEMENTADO

### 1. Compra de Créditos Adicionales (Top-up)

**❌ Falta Implementar Completamente:**
- Endpoint para comprar créditos sin cambiar plan
- Integración con Stripe para pago único
- Lógica para agregar créditos adicionales que no expiran
- Precio por crédito (~$0.10 USD)

---

### 2. Localización Colombia (Backend)

**❌ Falta Implementar:**
- Conversión de precios USD a COP
- Cálculo de IVA (19%)
- Endpoint o campo en respuesta con precios en COP
- Manejo de errores específicos de Colombia (tarjeta rechazada por seguridad)

**📝 Recomendación:**
- Agregar campo `prices_cop` en respuesta de planes
- Usar API de cambio de moneda (ej: exchangerate-api.com)
- Calcular: `precio_usd * tasa_cambio * 1.19` (con IVA)

---

### 3. Paywall Logic (Respuesta Estructurada)

**⚠️ Estado Actual:**
- Los errores 403 y 402 se retornan con mensajes básicos
- No hay estructura de respuesta con información de upgrade

**❌ Falta Implementar:**
- Respuesta estructurada en errores 403/402 con:
  - `current_plan`
  - `limit_type`
  - `current_count`
  - `limit`
  - `upgrade_options` (array de planes disponibles)

**📝 Ejemplo de Respuesta Necesaria:**
```python
# En plan_limits.py
def check_limit_with_upgrade_info(...):
    if current_count >= limit:
        upgrade_options = get_upgrade_options(plan, limit_type)
        raise HTTPException(
            status_code=403,
            detail={
                "error": "plan_limit_exceeded",
                "current_plan": plan,
                "limit_type": limit_type,
                "current_count": current_count,
                "limit": limit,
                "upgrade_options": upgrade_options
            }
        )
```

---

### 4. Generación de PDFs de Facturas

**⚠️ Estado Actual:**
- Existe `generate_quote_pdf()` para cotizaciones
- No hay generador de PDFs para facturas/invoices

**❌ Falta Implementar:**
- Función `generate_invoice_pdf()` similar a `generate_quote_pdf()`
- Template de factura con:
  - Logo de Nougram
  - Número de factura
  - Información de organización
  - Desglose de cargos
  - Total con IVA
  - Información de pago

---

### 5. Reseteo Automático Mensual de Créditos

**⚠️ Estado Actual:**
- Existe `grant_subscription_credits()` que otorga créditos
- No hay tarea programada (Celery Beat) para resetear automáticamente

**❌ Falta Implementar:**
- Tarea Celery Beat que ejecute mensualmente
- Lógica para identificar organizaciones que necesitan reset
- Reset basado en `next_reset_at` de cada cuenta

**📝 Código Necesario:**
```python
# En celery_app.py
@celery_app.task
async def reset_monthly_credits():
    # Obtener todas las cuentas donde next_reset_at <= ahora
    # Para cada una, llamar grant_subscription_credits()
    pass

# En celery beat schedule
CELERY_BEAT_SCHEDULE = {
    'reset-monthly-credits': {
        'task': 'reset_monthly_credits',
        'schedule': crontab(hour=0, minute=0),  # Diario a medianoche
    },
}
```

---

## 📊 RESUMEN DE COBERTURA

| Funcionalidad | Estado | Prioridad |
|--------------|--------|-----------|
| **Sistema de Créditos Core** | ✅ Completo | Alta |
| **Modelos de Datos** | ✅ Completo | Alta |
| **Endpoints de Créditos** | ✅ Completo | Alta |
| **Sistema de Planes** | ✅ Completo | Alta |
| **Validación de Límites** | ✅ Completo | Alta |
| **Suscripciones Básicas** | ✅ Completo | Alta |
| **Integración Stripe** | ✅ Completo | Alta |
| **Webhooks Stripe** | ✅ Completo | Alta |
| **Mapeo Acciones→Créditos** | ⚠️ Parcial | Media |
| **Historial de Facturas** | ❌ No implementado | Alta |
| **Stripe Customer Portal** | ❌ No implementado | Media |
| **Período de Gracia** | ❌ No implementado | Alta |
| **Método de Pago (Detalles)** | ❌ No implementado | Media |
| **Top-up Créditos** | ❌ No implementado | Baja |
| **Localización Colombia** | ❌ No implementado | Media |
| **Paywall Response Estructurada** | ⚠️ Parcial | Alta |
| **PDFs de Facturas** | ❌ No implementado | Media |
| **Reset Automático Créditos** | ❌ No implementado | Media |

---

## 🎯 PRIORIDADES DE IMPLEMENTACIÓN

### Prioridad Alta (Bloqueantes para UI)

1. **Historial de Facturas** - Necesario para pantalla de facturación
2. **Período de Gracia** - Requerido para manejo de pagos fallidos en Colombia
3. **Paywall Response Estructurada** - Necesario para modales de paywall
4. **Mapeo Acciones→Créditos** - Necesario para consumo granular

### Prioridad Media (Mejoras UX)

5. **Stripe Customer Portal** - Mejora experiencia de gestión de pago
6. **Método de Pago (Detalles)** - Necesario para mostrar información de tarjeta
7. **PDFs de Facturas** - Necesario para descarga de comprobantes
8. **Reset Automático Créditos** - Necesario para recarga mensual automática
9. **Localización Colombia** - Mejora experiencia para mercado objetivo

### Prioridad Baja (Futuro)

10. **Top-up Créditos** - Funcionalidad adicional, no crítica

---

## 📝 NOTAS TÉCNICAS

### Endpoints que Faltan

```python
# Billing
GET    /api/v1/billing/invoices              # Listar facturas
GET    /api/v1/billing/invoices/{id}          # Detalles de factura
GET    /api/v1/billing/invoices/{id}/pdf     # Descargar PDF
POST   /api/v1/billing/portal-session         # Customer Portal
GET    /api/v1/billing/payment-method        # Método de pago

# Credits (futuro)
POST   /api/v1/credits/me/purchase            # Comprar créditos adicionales
```

### Modelos que Faltan

```python
class Invoice(Base):
    """Modelo para almacenar historial de facturas de Stripe"""
    # Ver sección de recomendaciones arriba
```

### Servicios que Faltan

```python
class InvoiceService:
    """Servicio para gestionar facturas"""
    - sync_invoices_from_stripe()
    - get_invoices_by_organization()
    - generate_invoice_pdf()
```

---

**Última Actualización:** 2026-01-25
