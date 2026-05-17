# 💳 Modelo de Facturación - Nougram

**Versión:** 1.0  
**Fecha:** 2025-12-30  
**Estado:** ✅ Implementado

---

## 📋 Resumen Ejecutivo

Nougram utiliza un modelo de **suscripción SaaS** con sistema de **créditos** para controlar el uso de recursos. La facturación se gestiona mediante **Stripe** y ofrece 4 planes de suscripción con diferentes límites y características.

---

## 💰 Planes de Suscripción

### 🆓 Plan Free (Gratuito)

**Precio:**
- Mensual: **$0 USD**
- Anual: **$0 USD**

**Límites:**
- ✅ **1 usuario**
- ✅ **5 proyectos**
- ✅ **10 servicios**
- ✅ **3 miembros del equipo**
- ✅ **10 créditos/mes**

**Características:**
- Generación básica de propuestas
- Exportación a PDF
- Acceso a funciones básicas

**Ideal para:** Usuarios individuales que quieren probar la herramienta

---

### 🚀 Plan Starter

**Precio:**
- Mensual: **$29.99 USD**
- Anual: **$299.99 USD** (ahorro de ~2 meses)

**Límites:**
- ✅ **5 usuarios**
- ✅ **25 proyectos**
- ✅ **50 servicios**
- ✅ **10 miembros del equipo**
- ✅ **100 créditos/mes**

**Características:**
- Todo lo del plan Free
- Generación avanzada de propuestas
- Exportación PDF y DOCX
- Envío de propuestas por email
- Analytics básicos

**Ideal para:** Equipos pequeños que están comenzando

---

### 💼 Plan Professional

**Precio:**
- Mensual: **$99.99 USD**
- Anual: **$999.99 USD** (ahorro de ~2 meses)

**Límites:**
- ✅ **20 usuarios**
- ✅ **100 proyectos**
- ✅ **200 servicios**
- ✅ **50 miembros del equipo**
- ✅ **500 créditos/mes**

**Características:**
- Todo lo del plan Starter
- Analytics avanzados
- Plantillas personalizadas
- Soporte prioritario

**Ideal para:** Agencias en crecimiento y equipos medianos

---

### 🏢 Plan Enterprise

**Precio:**
- Mensual: **Contactar para precio**
- Anual: **Contactar para precio**

**Límites:**
- ✅ **Usuarios ilimitados**
- ✅ **Proyectos ilimitados**
- ✅ **Servicios ilimitados**
- ✅ **Miembros del equipo ilimitados**
- ✅ **Créditos ilimitados**

**Características:**
- Todo lo del plan Professional
- Soporte dedicado
- Integraciones personalizadas
- SLA garantizado
- Opciones de despliegue on-premise

**Ideal para:** Grandes organizaciones con necesidades específicas

---

## 🎫 Sistema de Créditos

### ¿Qué son los Créditos?

Los créditos son unidades de consumo que se utilizan para controlar el uso de ciertas acciones en la plataforma. Cada plan incluye una cantidad mensual de créditos que se renuevan automáticamente cada mes.

### Créditos por Plan

| Plan | Créditos/Mes |
|------|--------------|
| Free | 10 |
| Starter | 100 |
| Professional | 500 |
| Enterprise | Ilimitados |

### ¿Qué Consume Créditos?

Actualmente, el sistema de créditos está implementado pero puede ser configurado para consumir créditos en acciones específicas como:
- Generación de propuestas
- Exportaciones avanzadas
- Envíos de emails masivos
- Operaciones de análisis avanzado

### Renovación de Créditos

- Los créditos se renuevan automáticamente cada mes
- La renovación ocurre en la fecha de facturación de la suscripción
- Los créditos no utilizados **NO** se acumulan (se resetean cada mes)
- Los créditos adicionales pueden ser otorgados manualmente por administradores

---

## 💳 Métodos de Pago

### Integración con Stripe

Nougram utiliza **Stripe** como procesador de pagos, lo que permite:

- ✅ Pagos seguros con tarjeta de crédito/débito
- ✅ Facturación automática mensual/anual
- ✅ Gestión de suscripciones
- ✅ Portal de facturación para clientes
- ✅ Webhooks para sincronización automática

### Formas de Pago Aceptadas

- 💳 Tarjetas de crédito (Visa, Mastercard, American Express)
- 💳 Tarjetas de débito
- 🔄 Pago automático recurrente

### Facturación

- **Mensual:** Se factura el mismo día cada mes
- **Anual:** Se factura el mismo día cada año
- **Prorrateo:** Si cambias de plan, se aplica prorrateo automático
- **Facturas:** Disponibles en el portal de Stripe

---

## 🔄 Gestión de Suscripciones

### Cambio de Plan

**Proceso:**
1. Usuario selecciona nuevo plan en la configuración
2. Sistema actualiza suscripción en Stripe
3. Stripe aplica prorrateo automático
4. Cambio efectivo inmediatamente
5. Próxima factura refleja el nuevo plan

**Prorrateo:**
- Si subes de plan: Se cobra la diferencia proporcional
- Si bajas de plan: Se acredita la diferencia proporcional
- El crédito se refleja en la próxima factura

### Cancelación

**Opciones:**
- **Cancelar al final del período:** Continúas usando el plan hasta el final del período pagado
- **Cancelar inmediatamente:** Acceso revocado de inmediato, sin reembolso

**Después de cancelar:**
- Plan cambia automáticamente a "Free"
- Límites se ajustan a los del plan Free
- Datos se conservan por 30 días
- Puedes reactivar en cualquier momento

### Períodos de Prueba

- Los planes pagos pueden incluir períodos de prueba
- Durante la prueba, no se cobra
- Al finalizar la prueba, se inicia la facturación automática
- Puedes cancelar antes del final de la prueba sin cargo

---

## 📊 Límites y Restricciones

### Límites por Recurso

Cada plan tiene límites específicos para:

1. **Usuarios:** Número máximo de usuarios en la organización
2. **Proyectos:** Número máximo de proyectos activos
3. **Servicios:** Número máximo de servicios definidos
4. **Miembros del Equipo:** Número máximo de miembros del equipo para cálculos de BCR

### Comportamiento al Exceder Límites

- ⚠️ **Validación en tiempo real:** El sistema valida límites antes de crear recursos
- 🚫 **Error 403:** Si excedes un límite, recibes un error explicativo
- 💡 **Sugerencia de upgrade:** El mensaje de error sugiere actualizar el plan
- 📈 **Sin pérdida de datos:** Los recursos existentes se conservan

### Límites Ilimitados (Enterprise)

- El plan Enterprise tiene límites ilimitados (`-1` en el sistema)
- No hay validaciones de límites para este plan
- Acceso completo a todas las funcionalidades

---

## 🔐 Seguridad y Privacidad

### Datos de Pago

- ✅ **Nunca almacenamos información de tarjetas** en nuestros servidores
- ✅ **Stripe maneja toda la información sensible** (PCI-DSS compliant)
- ✅ **Tokens seguros** para identificar métodos de pago
- ✅ **Cifrado end-to-end** en todas las transacciones

### Facturación

- ✅ Todas las facturas se generan automáticamente
- ✅ Historial completo de pagos en Stripe
- ✅ Portal de facturación seguro para clientes
- ✅ Exportación de facturas en PDF

---

## 📈 Escalabilidad

### Upgrade de Plan

**Cuándo considerar upgrade:**
- Necesitas más usuarios
- Estás alcanzando límites de proyectos/servicios
- Requieres más créditos mensuales
- Necesitas funcionalidades avanzadas

**Proceso de upgrade:**
1. Selecciona nuevo plan
2. Confirma cambio
3. Pago prorrateado automático
4. Límites actualizados inmediatamente

### Downgrade de Plan

**Consideraciones:**
- Verifica que no excedas límites del nuevo plan
- Los recursos existentes se conservan
- Puede requerir eliminar recursos para cumplir límites
- Créditos se ajustan al nuevo plan

---

## 🛠️ Implementación Técnica

### Endpoints de Facturación

**Crear Checkout:**
```
POST /api/v1/billing/checkout-session
```

**Obtener Suscripción:**
```
GET /api/v1/billing/subscription
```

**Actualizar Suscripción:**
```
PUT /api/v1/billing/subscription
```

**Cancelar Suscripción:**
```
POST /api/v1/billing/subscription/cancel
```

**Listar Planes:**
```
GET /api/v1/billing/plans
```

### Webhooks de Stripe

El sistema sincroniza automáticamente con Stripe mediante webhooks:

- `checkout.session.completed` - Checkout completado
- `customer.subscription.created` - Suscripción creada
- `customer.subscription.updated` - Suscripción actualizada
- `customer.subscription.deleted` - Suscripción cancelada
- `invoice.payment_succeeded` - Pago exitoso
- `invoice.payment_failed` - Pago fallido

### Validación de Límites

El sistema valida límites automáticamente en:
- Creación de usuarios
- Creación de proyectos
- Creación de servicios
- Adición de miembros del equipo
- Consumo de créditos

---

## 📞 Soporte y Ayuda

### Preguntas Frecuentes

**¿Puedo cambiar de plan en cualquier momento?**
- Sí, puedes cambiar de plan en cualquier momento. Se aplica prorrateo automático.

**¿Qué pasa si excedo los límites?**
- No podrás crear nuevos recursos hasta que actualices el plan o elimines recursos existentes.

**¿Los créditos se acumulan?**
- No, los créditos se renuevan cada mes y no se acumulan.

**¿Puedo cancelar y reactivar después?**
- Sí, puedes cancelar y reactivar en cualquier momento. Tus datos se conservan por 30 días.

**¿Hay descuentos por pago anual?**
- Sí, el pago anual incluye aproximadamente 2 meses gratis comparado con el pago mensual.

### Contacto

Para preguntas sobre facturación o planes Enterprise:
- 📧 Email: billing@nougram.com
- 💬 Chat en la aplicación (planes Professional y Enterprise)
- 📞 Teléfono: Disponible para planes Enterprise

---

## 📚 Referencias

- [API de Facturación](./API_BILLING.md) - Documentación técnica completa
- [Sistema de Créditos](./EVALUACION_SISTEMA_TOKENS.md) - Detalles del sistema de créditos
- [Stripe Documentation](https://stripe.com/docs) - Documentación oficial de Stripe

---

**Última actualización:** 2025-12-30  
**Mantenedor:** Equipo de Desarrollo Nougram
