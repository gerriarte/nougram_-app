# Análisis: Módulo Payments/Credits - Arquitectura MVC

**Fecha:** 2026-01-25  
**Última actualización:** 2026-01-25  
**Documento Base:** [2026-01-25-BACKEND_IMPLEMENTATION_STATUS_PAYMENTS_CREDITS.md](./2026-01-25-BACKEND_IMPLEMENTATION_STATUS_PAYMENTS_CREDITS.md)  
**Arquitectura:** MVC + Repository/Service (`.cursorrules/nougram_backend_rules.md`)

---

## 📊 Resumen Ejecutivo

El módulo **Payments/Credits** está **COMPLETAMENTE refactorizado** bajo la arquitectura MVC. Los módulos de **Credits** y **Billing** están correctamente refactorizados. La integración con **Stripe** ha sido removida y será reimplementada con el nuevo proveedor de pagos.

### Estado Actual
- ✅ **Credits Module** - 100% refactorizado (usa CreditController)
- ✅ **Billing Module** - 100% refactorizado (usa BillingController)
- ⏸️ **Webhooks Module** - Stripe removido, pendiente nueva implementación

---

## 🔍 Análisis Detallado

### 1. Credits Module ✅

**Ubicación:** `backend/app/api/v1/endpoints/credits.py`

**Estado:** ✅ **Correctamente Refactorizado**

**Verificación:**
- ✅ Endpoints delegan a `CreditController`
- ✅ Controller delega a `CreditService` (ya existente)
- ✅ View (`CreditView`) transforma respuestas
- ✅ Sin acceso directo a DB desde endpoints
- ✅ Sin lógica de negocio en endpoints

**Ejemplo:**
```python
@router.get("/me/balance", response_model=CreditBalanceResponse)
async def get_my_credit_balance(...):
    controller = CreditController(db, tenant, current_user)
    return await controller.get_credit_balance()
```

**Conclusión:** ✅ Cumple 100% con la arquitectura MVC

---

### 2. Billing Module ✅

**Ubicación:** `backend/app/api/v1/endpoints/billing.py`

**Estado:** ✅ **Correctamente Refactorizado**

**Verificación:**
- ✅ Endpoints delegan a `BillingController`
- ✅ Controller delega a `BillingService`
- ✅ View (`BillingView`) transforma respuestas
- ✅ Sin acceso directo a DB desde endpoints
- ✅ Sin lógica de negocio en endpoints

**Ejemplo:**
```python
@router.post("/checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(...):
    controller = BillingController(db, tenant, current_user)
    return await controller.create_checkout_session(checkout_data)
```

**Conclusión:** ✅ Cumple 100% con la arquitectura MVC

---

### 3. Webhooks Module ⏸️

**Ubicación:** `backend/app/api/v1/endpoints/stripe_webhooks.py`

**Estado:** ⏸️ **Stripe Removido - Pendiente Nueva Implementación**

**Nota:** La integración con Stripe ha sido removida. Este módulo será reimplementado
con el nuevo proveedor de pagos siguiendo la arquitectura MVC desde el inicio.

**Estado Anterior (Stripe):**
- ❌ Lógica de negocio directamente en funciones helper
- ❌ Acceso directo a repositorios
- ❌ No existía Controller/Service

**Estado Actual:**
- ✅ Código de Stripe removido
- ✅ Archivo limpiado y preparado para nueva implementación
- ✅ Pendiente implementación con nuevo proveedor siguiendo MVC desde el inicio

---

## 📋 Plan de Implementación Futura

**Nota:** La implementación se hará con el nuevo proveedor de pagos siguiendo MVC desde el inicio.

### Paso 1: Crear `WebhookService` ⏳ Prioridad Media

**Archivo:** `backend/app/services/webhook_service.py`

**Responsabilidades:**
1. Procesar eventos de webhook de Stripe
2. Sincronizar suscripciones desde Stripe
3. Manejar eventos de checkout, subscription, invoice
4. Otorgar créditos cuando corresponda
5. Actualizar estado de organizaciones

**Métodos Requeridos:**
```python
class WebhookService:
    async def process_webhook_event(self, event: dict) -> Dict[str, Any]
    async def handle_checkout_session_completed(self, event: dict) -> None
    async def handle_subscription_created(self, event: dict) -> None
    async def handle_subscription_updated(self, event: dict) -> None
    async def handle_subscription_deleted(self, event: dict) -> None
    async def handle_invoice_payment_succeeded(self, event: dict) -> None
    async def handle_invoice_payment_failed(self, event: dict) -> None
    async def sync_subscription_from_stripe(self, stripe_subscription: dict, organization_id: int) -> Subscription
```

**Dependencias:**
- `BillingService` - Para operaciones de suscripción
- `CreditService` - Para otorgar créditos
- `SubscriptionRepository` - Para acceso a datos
- `OrganizationRepository` - Para actualizar organización
- `stripe_service` - Para obtener datos de Stripe

---

### Paso 2: Crear `WebhookController` ✅ Prioridad Alta

**Archivo:** `backend/app/controllers/webhook_controller.py`

**Responsabilidades:**
1. Validar webhook signature (ya hecho por stripe_service)
2. Delegar procesamiento a WebhookService
3. Manejar errores HTTP
4. Retornar respuestas apropiadas

**Métodos Requeridos:**
```python
class WebhookController(BaseController):
    async def process_webhook(self, payload: bytes, sig_header: str) -> Dict[str, str]
```

---

### Paso 3: Refactorizar Endpoint ✅ Prioridad Alta

**Archivo:** `backend/app/api/v1/endpoints/stripe_webhooks.py`

**Cambios:**
1. **Endpoint `POST /webhook`:**
   ```python
   @router.post("/webhook")
   async def stripe_webhook(
       request: Request,
       db: AsyncSession = Depends(get_db)
   ):
       payload = await request.body()
       sig_header = request.headers.get("stripe-signature")
       
       if not sig_header:
           raise HTTPException(...)
       
       # Crear controller (sin tenant/current_user porque es webhook externo)
       controller = WebhookController(db)
       return await controller.process_webhook(payload, sig_header)
   ```

2. **Eliminar funciones helper:**
   - Eliminar `handle_checkout_session_completed`
   - Eliminar `handle_subscription_created`
   - Eliminar `handle_subscription_updated`
   - Eliminar `handle_subscription_deleted`
   - Eliminar `handle_invoice_payment_succeeded`
   - Eliminar `handle_invoice_payment_failed`
   - Eliminar `sync_subscription_from_stripe`
   - Eliminar `_extract_plan_from_metadata`

**Resultado:** Endpoint de ~15 líneas, sin lógica de negocio.

---

## 📊 Comparación: Antes vs Después

### Antes (Actual) ❌
```
Endpoint (80 líneas)
├── Verificación de signature
├── Switch de eventos
└── Funciones helper (240 líneas)
    ├── Acceso directo a repositorios
    ├── Lógica de negocio compleja
    └── Sincronización de suscripciones
```

### Después (Objetivo) ✅
```
Endpoint (15 líneas)
└── Controller (20 líneas)
    └── Service (200 líneas)
        ├── BillingService
        ├── CreditService
        └── Repositories
```

---

## ✅ Checklist de Refactorización

- [ ] Crear `WebhookService` con métodos de procesamiento
- [ ] Crear `WebhookController` para HTTP handling
- [ ] Mover `sync_subscription_from_stripe` a Service
- [ ] Mover todas las funciones `handle_*` a Service
- [ ] Refactorizar endpoint para usar Controller
- [ ] Eliminar acceso directo a repositorios desde funciones helper
- [ ] Mover toda la lógica de negocio a Service
- [ ] Verificar que no hay errores de linter
- [ ] Actualizar documentación de estado

---

## 🎯 Impacto Esperado

### Beneficios
1. **Separación de Responsabilidades:** Lógica de webhooks centralizada en Service
2. **Testabilidad:** Fácil testear Service sin necesidad de HTTP
3. **Reutilización:** Service puede ser usado por otros componentes
4. **Mantenibilidad:** Código más organizado y fácil de mantener
5. **Consistencia:** Mismo patrón que otros módulos refactorizados

### Métricas
- **Líneas de código en endpoint:** Reducción de ~80 líneas a ~15 líneas
- **Líneas de código en funciones helper:** ~240 líneas movidas a Service
- **Cobertura de arquitectura:** 100% (actualmente ~0% para webhooks)

---

## 📝 Notas Técnicas

### Consideraciones Especiales

1. **Webhooks No Requieren Autenticación:**
   - Los webhooks de Stripe no tienen `current_user` ni `tenant`
   - El `WebhookController` debe manejar esto apropiadamente
   - La validación de signature se hace antes de procesar

2. **Dependencias Existentes:**
   - ✅ `BillingService` - Ya existe y funciona
   - ✅ `CreditService` - Ya existe y funciona
   - ✅ `SubscriptionRepository` - Ya existe y funciona
   - ✅ `OrganizationRepository` - Ya existe y funciona
   - ✅ `stripe_service` - Ya existe y funciona

3. **Manejo de Errores:**
   - Los webhooks deben ser idempotentes
   - Los errores no deben fallar el webhook (Stripe reintentará)
   - Logging detallado es crítico para debugging

---

## 📊 Resumen por Módulo

| Módulo | Estado | Controller | Service | Repository | View | Endpoints | Cumple MVC |
|--------|--------|------------|---------|------------|------|-----------|------------|
| Credits | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ 100% |
| Billing | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ 100% |
| Webhooks | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ 0% |

---

**Fin del Documento**
