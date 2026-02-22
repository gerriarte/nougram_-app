# Documento de Requerimientos de UI - Manejo de Pagos y Créditos

**Versión:** 1.0  
**Fecha:** 2026-01-25  
**Propósito:** Especificaciones técnicas para diseño UI del sistema de pagos, suscripciones y gestión de créditos de IA  
**Audiencia:** Diseñadores UI/UX, Desarrolladores Frontend, Figma Make

---

## Resumen Ejecutivo

Este documento especifica los requerimientos de interfaz de usuario para el **sistema de pagos, suscripciones y créditos de IA** de Nougram. El sistema está diseñado para maximizar la conversión mediante transparencia, claridad en el consumo de créditos y paywalls amigables que guían al usuario hacia la actualización de plan en lugar de bloquearlo.

**Objetivo Principal:** Proporcionar una experiencia fluida y transparente para gestionar suscripciones, visualizar consumo de créditos de IA y manejar pagos, con especial atención al mercado colombiano.

**Principios de Diseño:**

- **Transparencia Total:** El usuario siempre sabe cuántos créditos tiene, cuántos ha usado y cuándo se recargan
- **Paywall Amigable:** En lugar de errores, mostrar oportunidades de upgrade con mensajes claros
- **Localización Colombia:** Precios en COP con IVA incluido, manejo de errores de pago comunes
- **Créditos Granulares:** Cada acción de IA tiene un costo claro y visible

---

## ⭐ Filosofía de Créditos: No Regales la IA

**Problema que Resuelve:**
El costo real de modelos como Claude o GPT-4o es significativo. Un sistema de créditos granular permite:

- Controlar costos operacionales
- Educar al usuario sobre el valor de la IA
- Crear incentivos claros para upgrade

**Mapeo de Acciones a Créditos:**

| Acción | Créditos | Justificación |
|--------|----------|---------------|
| Crear cotización manual | 0 | No usa IA |
| Generar propuesta estratégica con IA | 5 | Análisis profundo, contexto extenso |
| Sugerencias de onboarding (IA) | 2 | Consulta rápida con contexto limitado |
| Análisis financiero con IA | 3 | Procesamiento de datos estructurados |
| Optimización de cotización (IA) | 4 | Cálculos complejos y recomendaciones |

**Regla de Oro:**

- **Acciones manuales = 0 créditos** (no penalizar el uso básico)
- **Acciones con IA = Créditos proporcionales al costo real** (transparencia total)

---

## 🔄 Sistema de Créditos: Mensual y Recargable

**Ciclo de Créditos:**

- Los créditos se otorgan **mensualmente** según el plan
- Se resetean el mismo día cada mes (basado en `next_reset_at`)
- Los créditos no usados **NO se acumulan** (use it or lose it)
- Los créditos adicionales pueden comprarse como "top-up" (futuro)

**Estados del Sistema:**

1. **Créditos Disponibles:** `credits_available` (puede ser mayor a `credits_per_month` si hay bonos manuales)
2. **Créditos Usados Este Mes:** `credits_used_this_month` (se resetea mensualmente)
3. **Créditos Totales Usados:** `credits_used_total` (historial acumulado)
4. **Asignación Mensual:** `credits_per_month` (según plan, NULL = ilimitado)

---

## 📊 Catálogo de Planes

### Estructura de Planes

| Plan | Precio Mensual | Precio Anual | Créditos/mes | Usuarios | Proyectos | Servicios | Miembros Equipo |
|------|---------------|--------------|--------------|----------|-----------|-----------|-----------------|
| **Free** | $0 | $0 | 10 | 1 | 5 | 10 | 3 |
| **Starter** | $29.99 USD | $299.99 USD | 100 | 5 | 25 | 50 | 10 |
| **Professional** | $99.99 USD | $999.99 USD | 500 | 20 | 100 | 200 | 50 |
| **Enterprise** | Contactar | Contactar | Ilimitado | Ilimitado | Ilimitado | Ilimitado | Ilimitado |

**Nota de Precios para Colombia:**

- Los precios en COP deben calcularse dinámicamente según tasa de cambio
- Mostrar IVA incluido si aplica (19% en Colombia)
- Ejemplo: Starter = $29.99 USD ≈ $120,000 COP (con IVA incluido)

### Límites por Plan

**Free:**

- Ideal para probar Nougram
- Limitado a uso personal
- Sin soporte prioritario

**Starter:**

- Ideal para equipos pequeños
- Incluye todas las funciones básicas
- Soporte por email

**Professional:**

- Para agencias en crecimiento
- Funciones avanzadas
- Soporte prioritario
- Templates personalizados

**Enterprise:**

- Para grandes organizaciones
- Todo ilimitado
- Soporte dedicado
- Integraciones personalizadas
- SLA garantizado

---

## 🎨 ESPECIFICACIONES DE PANTALLAS Y COMPONENTES

---

## 1. SELECTOR DE PLANES (Pricing Table)

### 1.1 Objetivo

Permitir al usuario comparar planes y seleccionar/actualizar su suscripción. Diseñado para maximizar conversión destacando el plan "Professional" como el más popular.

### 1.2 Estructura Visual

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Planes y Precios                                                          │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  [Mensual]  [Anual] ← Toggle (Anual ahorra ~17%)                          │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    FREE      │  │   STARTER    │  │ PROFESSIONAL │  │  ENTERPRISE  │  │
│  │              │  │              │  │   ⭐ POPULAR │  │              │  │
│  │   $0         │  │  $29.99/mes  │  │  $99.99/mes  │  │  Contactar   │  │
│  │              │  │  $299.99/año │  │  $999.99/año │  │              │  │
│  │              │  │              │  │              │  │              │  │
│  │ ✓ 10 créditos│  │ ✓ 100 créditos│ │ ✓ 500 créditos│ │ ✓ Ilimitado │  │
│  │ ✓ 1 usuario  │  │ ✓ 5 usuarios  │ │ ✓ 20 usuarios │ │ ✓ Ilimitado │  │
│  │ ✓ 5 proyectos│  │ ✓ 25 proyectos │ │ ✓ 100 proyectos│ │ ✓ Ilimitado │  │
│  │ ✓ 10 servicios│ │ ✓ 50 servicios │ │ ✓ 200 servicios│ │ ✓ Ilimitado │  │
│  │ ✓ 3 miembros │  │ ✓ 10 miembros  │ │ ✓ 50 miembros  │ │ ✓ Ilimitado │  │
│  │              │  │              │  │              │  │              │  │
│  │ [Seleccionar]│  │ [Actualizar] │  │ [Actualizar] │  │ [Contactar]  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                                             │
│  💡 Todos los precios incluyen IVA (Colombia)                              │
│  💳 Aceptamos tarjetas de crédito y débito                                 │
│  🔒 Pago seguro procesado por Stripe                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Componentes Requeridos

**Card de Plan:**

- Header con nombre del plan
- Badge "POPULAR" para Professional (destacado visualmente)
- Precio mensual/anual con toggle
- Lista de características (checkmarks)
- Botón de acción (Seleccionar/Actualizar/Contactar)
- Estado visual si es el plan actual (borde destacado, badge "Plan Actual")

**Toggle Mensual/Anual:**

- Mostrar ahorro porcentual al seleccionar anual
- Ejemplo: "Ahorra 17% con facturación anual"

**Badge de Plan Actual:**

- Mostrar solo en el plan activo
- Texto: "Plan Actual" o "Tu Plan"
- Estilo: Outline con color primario

### 1.4 Estados del Componente

**Plan Gratuito (Free):**

- Botón: "Seleccionar Plan" (si no tiene plan) o "Plan Actual" (si ya lo tiene)
- Sin precio destacado
- Características básicas visibles

**Plan Starter/Professional:**

- Botón: "Actualizar Plan" (si tiene otro plan) o "Seleccionar Plan" (si no tiene)
- Precio destacado
- Si es plan actual: botón deshabilitado con texto "Plan Actual"

**Plan Enterprise:**

- Botón: "Contactar Ventas"
- Abre modal o redirige a formulario de contacto
- Precio: "Personalizado" o "Contactar"

### 1.5 Localización Colombia

**Precios en COP:**

- Mostrar precio en COP debajo del precio en USD
- Formato: "$120,000 COP/mes (IVA incluido)"
- Calcular dinámicamente según tasa de cambio

**IVA:**

- Mostrar claramente "IVA incluido" o "IVA no incluido" según corresponda
- Para Colombia: "IVA incluido (19%)"

**Métodos de Pago:**

- Mostrar logos de tarjetas aceptadas
- Incluir métodos locales si aplica (PSE, Nequi, etc.)

### 1.6 Interacciones

**Al hacer clic en "Seleccionar Plan" o "Actualizar Plan":**

1. Validar permisos del usuario (solo owner/admin pueden cambiar plan)
2. Si no tiene permisos: mostrar mensaje "Solo el propietario puede cambiar el plan"
3. Si tiene permisos: crear checkout session de Stripe
4. Redirigir a Stripe Checkout
5. Al regresar: mostrar mensaje de éxito/error según resultado

**Al hacer clic en "Contactar" (Enterprise):**

1. Abrir modal con formulario de contacto
2. Campos: Nombre, Email, Empresa, Mensaje
3. Enviar a endpoint de contacto/ventas

---

## 2. DASHBOARD DE CONSUMO DE CRÉDITOS (Credit Tracker)

### 2.1 Objetivo

Visualizar de manera clara y transparente el consumo de créditos de IA, mostrando créditos disponibles, usados este mes y fecha de recarga. Incluir alertas proactivas cuando el usuario se acerca al límite.

### 2.2 Estructura Visual

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Créditos de IA                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │                    [Medidor Circular]                                │ │
│  │                                                                       │ │
│  │                     80 / 100                                          │ │
│  │                   Créditos Usados                                    │ │
│  │                                                                       │ │
│  │                   20 disponibles                                      │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Resumen del Mes                                                      │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  Créditos Disponibles:        20                                     │ │
│  │  Créditos Usados Este Mes:    80                                     │ │
│  │  Asignación Mensual:          100                                    │ │
│  │  Próxima Recarga:             15 de Febrero, 2026                   │ │
│  │                                                                       │ │
│  │  [Barra de Progreso: ████████████████████░░░░ 80%]                   │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ⚠️ Te quedan 20 créditos este mes. Considera actualizar tu plan.        │
│  [Recargar Créditos] [Actualizar Plan]                                     │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Actividad Reciente                                                   │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  • Generación de propuesta estratégica    -5 créditos  Hace 2 horas │ │
│  │  • Análisis financiero con IA              -3 créditos  Ayer         │ │
│  │  • Sugerencias de onboarding               -2 créditos  Hace 3 días  │ │
│  │                                                                       │ │
│  │  [Ver Historial Completo →]                                           │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Componentes Requeridos

**Medidor Circular (Circular Progress):**

- Visualización principal del consumo
- Porcentaje usado vs disponible
- Color dinámico:
  - Verde (0-70%): Normal
  - Amarillo (70-90%): Advertencia
  - Rojo (90-100%): Crítico
- Número grande en el centro: "80 / 100"
- Texto pequeño debajo: "Créditos Usados"

**Barra de Progreso Lineal:**

- Complemento al medidor circular
- Muestra progreso visual del mes
- Mismo sistema de colores que el medidor

**Card de Resumen:**

- Créditos Disponibles (número grande)
- Créditos Usados Este Mes
- Asignación Mensual
- Próxima Recarga (fecha formateada)

**Alertas Proactivas:**

- Mostrar cuando el uso está entre 70-90%
- Mensaje: "Te quedan X créditos este mes. Considera actualizar tu plan."
- Botones de acción: "Recargar Créditos" y "Actualizar Plan"

**Lista de Actividad Reciente:**

- Últimas 5 transacciones de consumo
- Formato: Acción - Créditos - Tiempo relativo
- Link a historial completo

### 2.4 Estados del Componente

**Estado Normal (0-70% usado):**

- Medidor verde
- Sin alertas
- Botones de acción opcionales

**Estado Advertencia (70-90% usado):**

- Medidor amarillo
- Alerta suave: "Te quedan X créditos"
- Botones de acción visibles pero no intrusivos

**Estado Crítico (90-100% usado):**

- Medidor rojo
- Alerta destacada: "¡Últimos créditos disponibles!"
- Botones de acción prominentes
- Considerar modal de upgrade

**Plan Ilimitado (Enterprise):**

- Mostrar "Ilimitado" en lugar de medidor
- Sin barras de progreso
- Mensaje: "Tu plan Enterprise incluye créditos ilimitados"

### 2.5 Lógica de Recarga

**Cuándo Mostrar Botón "Recargar Créditos":**

- Cuando el uso está por encima del 70%
- O cuando el usuario tiene 0 créditos disponibles
- (Futuro: permitir compra de créditos adicionales)

**Acción del Botón:**

- Si está disponible: abrir modal de compra de créditos
- Si no está disponible: redirigir a página de planes con mensaje: "Actualiza tu plan para obtener más créditos mensuales"

### 2.6 Ubicación en la App

**Dashboard Principal:**

- Widget pequeño en la parte superior derecha
- Muestra solo medidor circular pequeño y créditos disponibles
- Click para expandir a vista completa

**Página de Configuración:**

- Vista completa del dashboard de créditos
- Incluye historial completo y configuración

**Sidebar/Navbar:**

- Indicador pequeño siempre visible
- Muestra créditos disponibles como badge
- Color cambia según estado (verde/amarillo/rojo)

---

## 3. ESTADO DE SUSCRIPCIÓN

### 3.1 Objetivo

Mostrar información clara sobre el estado actual de la suscripción: plan activo, fecha de renovación, método de pago y estado (Activa, Vencida, Trial, Past Due).

### 3.2 Estructura Visual

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Tu Suscripción                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Plan Actual                                                          │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  [Badge: Professional]  [Badge: Activa]                              │ │
│  │                                                                       │ │
│  │  $99.99 USD/mes                                                       │ │
│  │  Próximo pago: 15 de Febrero, 2026                                   │ │
│  │                                                                       │ │
│  │  ✓ 500 créditos de IA por mes                                        │ │
│  │  ✓ Hasta 20 usuarios                                                  │ │
│  │  ✓ Hasta 100 proyectos                                                │ │
│  │  ✓ Soporte prioritario                                                │ │
│  │                                                                       │ │
│  │  [Cambiar Plan] [Gestionar Pago]                                     │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Método de Pago                                                       │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  💳 •••• •••• •••• 4242                                               │ │
│  │  Expira: 12/2025                                                      │ │
│  │                                                                       │ │
│  │  [Actualizar Método de Pago]                                          │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Período de Facturación                                               │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  Período Actual: 15 Ene 2026 - 15 Feb 2026                            │ │
│  │  Próxima Factura: 15 Feb 2026                                        │ │
│  │                                                                       │ │
│  │  [Ver Facturas Anteriores →]                                          │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Acciones                                                              │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  [Cancelar Suscripción]                                               │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Estados de Suscripción

**Activa:**

- Badge verde: "Activa"
- Muestra fecha de próxima renovación
- Todos los botones disponibles

**Trialing (Periodo de Prueba):**

- Badge azul: "Periodo de Prueba"
- Muestra fecha de fin de prueba: "Tu prueba termina el 15 de Febrero"
- Mensaje: "Después de esta fecha se cobrará automáticamente"
- Botón destacado: "Actualizar Plan Ahora"

**Past Due (Mora):**

- Badge amarillo: "Pago Pendiente"
- Mensaje destacado: "Tu último pago falló. Por favor actualiza tu método de pago."
- Período de gracia: "Tienes 3 días para resolver el pago antes de que se suspenda tu cuenta"
- Botón destacado: "Actualizar Método de Pago"
- Mostrar fecha límite: "Debes resolver antes del [fecha]"

**Cancelled (Cancelada):**

- Badge gris: "Cancelada"
- Mensaje: "Tu suscripción se cancelará el [fecha]"
- Botón: "Reactivar Suscripción"

**Incomplete/Incomplete Expired:**

- Badge rojo: "Pago Incompleto"
- Mensaje: "No pudimos procesar tu pago. Por favor intenta nuevamente."
- Botón: "Completar Pago"

### 3.4 Manejo de Errores de Pago (Colombia)

**Problema Común:**
En Colombia, las tarjetas suelen rebotar por "seguridad" o límites de transacción internacional.

**Solución UI:**

1. **Detección Temprana:** Cuando el estado cambia a "past_due", mostrar inmediatamente un modal explicativo
2. **Mensaje Amigable:**

   ```
   "Tu banco rechazó el pago por seguridad. Esto es común en Colombia.
   
   ¿Qué puedes hacer?
   • Contacta a tu banco para autorizar transacciones internacionales
   • Actualiza tu método de pago con otra tarjeta
   • Usa una tarjeta prepago internacional
   
   Tienes 3 días para resolver esto antes de que se suspenda tu cuenta."
   ```

3. **Período de Gracia:** Mostrar contador de días restantes
4. **Opciones de Resolución:** Botones claros para cada acción

### 3.5 Componentes Requeridos

**Card de Plan Actual:**

- Nombre del plan (badge)
- Estado (badge con color según estado)
- Precio mensual/anual
- Fecha de próxima renovación
- Lista de características del plan
- Botones de acción

**Card de Método de Pago:**

- Últimos 4 dígitos de la tarjeta
- Tipo de tarjeta (Visa, Mastercard, etc.)
- Fecha de expiración
- Botón para actualizar

**Card de Período de Facturación:**

- Período actual (fecha inicio - fecha fin)
- Próxima fecha de facturación
- Link a historial de facturas

**Modal de Cancelación:**

- Confirmar cancelación
- Opciones: Cancelar al final del período o inmediatamente
- Encuesta opcional: "¿Por qué cancelas?"
- Botón de confirmación

---

## 4. HISTORIAL DE TRANSACCIONES (Facturación)

### 4.1 Objetivo

Listar todas las facturas/invoices de la suscripción con estados de pago, fechas y opción de descarga de comprobantes.

### 4.2 Estructura Visual

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Historial de Facturación                                                  │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  [Filtros: Todos | Pagadas | Pendientes | Fallidas]                       │
│  [Búsqueda: Buscar por fecha o monto...]                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Factura #INV-2026-001                    [Badge: Pagada]            │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  Plan: Professional                                                   │ │
│  │  Período: 15 Ene 2026 - 15 Feb 2026                                  │ │
│  │  Monto: $99.99 USD                                                    │ │
│  │  Fecha de Pago: 15 de Enero, 2026                                    │ │
│  │                                                                       │ │
│  │  [Descargar PDF] [Ver Detalles]                                      │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Factura #INV-2026-002                    [Badge: Pendiente]         │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  Plan: Professional                                                   │ │
│  │  Período: 15 Feb 2026 - 15 Mar 2026                                  │ │
│  │  Monto: $99.99 USD                                                    │ │
│  │  Vence: 15 de Febrero, 2026                                          │ │
│  │                                                                       │ │
│  │  [Pagar Ahora] [Ver Detalles]                                        │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Factura #INV-2026-003                    [Badge: Fallida]            │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  Plan: Professional                                                   │ │
│  │  Período: 15 Dic 2025 - 15 Ene 2026                                  │ │
│  │  Monto: $99.99 USD                                                    │ │
│  │  Fecha de Intento: 15 de Diciembre, 2025                             │ │
│  │                                                                       │ │
│  │  ⚠️ El pago falló. Por favor actualiza tu método de pago.           │ │
│  │                                                                       │ │
│  │  [Reintentar Pago] [Actualizar Método] [Ver Detalles]                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  [Página 1 de 3] [< Anterior] [Siguiente >]                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Estados de Factura

**Succeeded (Pagada):**

- Badge verde: "Pagada"
- Muestra fecha de pago
- Botones: "Descargar PDF", "Ver Detalles"

**Pending (Pendiente):**

- Badge azul: "Pendiente"
- Muestra fecha de vencimiento
- Botones: "Pagar Ahora", "Ver Detalles"

**Failed (Fallida):**

- Badge rojo: "Fallida"
- Mensaje de error visible
- Botones: "Reintentar Pago", "Actualizar Método", "Ver Detalles"

**Void (Anulada):**

- Badge gris: "Anulada"
- Sin acciones disponibles

### 4.4 Componentes Requeridos

**Card de Factura:**

- Número de factura (formato: INV-YYYY-XXX)
- Badge de estado (color según estado)
- Información del plan
- Período facturado
- Monto (con moneda)
- Fecha relevante (pago, vencimiento, intento)
- Botones de acción según estado

**Filtros:**

- Todos
- Pagadas
- Pendientes
- Fallidas
- Anuladas

**Búsqueda:**

- Por número de factura
- Por rango de fechas
- Por monto

**Paginación:**

- 10-20 facturas por página
- Navegación anterior/siguiente
- Indicador de página actual

**Modal de Detalles:**

- Información completa de la factura
- Desglose de cargos
- Información de pago
- Opción de descargar PDF

### 4.5 Descarga de Comprobantes

**Formato PDF:**

- Incluir logo de Quotai
- Número de factura
- Información de la organización
- Desglose de cargos
- Total
- Información de pago
- Fecha de emisión

**Acción:**

- Botón "Descargar PDF" en cada factura
- Descarga directa del archivo
- Nombre de archivo: `factura_INV-YYYY-XXX.pdf`

---

## 5. PAYWALL LOGIC (Lógica de Paywall)

### 5.1 Objetivo

En lugar de mostrar errores de "Acceso Denegado", mostrar modales amigables que guíen al usuario hacia la actualización de plan o la compra de créditos adicionales.

### 5.2 Escenarios de Paywall

#### Escenario 1: Límite de Plan Alcanzado

**Trigger:** Usuario intenta crear un proyecto pero ya alcanzó el límite de su plan.

**UI:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ⚠️ Has alcanzado el límite de tu plan                                      │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Tu plan Free permite hasta 5 proyectos. Ya has creado 5 proyectos.        │
│                                                                             │
│  Para crear más proyectos, actualiza tu plan:                               │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   STARTER    │  │ PROFESSIONAL  │  │  ENTERPRISE   │                  │
│  │              │  │   ⭐ POPULAR  │  │               │                  │
│  │ 25 proyectos │  │ 100 proyectos │  │  Ilimitado    │                  │
│  │ $29.99/mes   │  │  $99.99/mes   │  │  Contactar   │                  │
│  │              │  │              │  │               │                  │
│  │ [Actualizar] │  │ [Actualizar] │  │ [Contactar]  │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                             │
│  [Cerrar]                                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Escenario 2: Créditos Insuficientes

**Trigger:** Usuario intenta usar una función de IA pero no tiene créditos suficientes.

**UI:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  💡 Créditos Insuficientes                                                 │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Esta acción requiere 5 créditos de IA, pero solo tienes 2 disponibles.    │
│                                                                             │
│  Opciones:                                                                  │
│                                                                             │
│  1. Actualizar Plan (Recomendado)                                          │
│     Obtén más créditos mensuales con un plan superior                      │
│     [Ver Planes]                                                           │
│                                                                             │
│  2. Esperar a la Recarga Mensual                                           │
│     Tus créditos se recargarán el 15 de Febrero, 2026                      │
│                                                                             │
│  3. Contactar Soporte                                                      │
│     Si necesitas créditos adicionales inmediatamente                       │
│     [Contactar]                                                             │
│                                                                             │
│  [Cerrar]                                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Escenario 3: Límite de Usuarios Alcanzado

**Trigger:** Usuario intenta agregar un miembro al equipo pero alcanzó el límite.

**UI:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  👥 Límite de Miembros del Equipo                                          │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Tu plan Free permite hasta 3 miembros del equipo. Ya has agregado 3.      │
│                                                                             │
│  Para agregar más miembros y colaborar con tu equipo:                      │
│                                                                             │
│  [Actualizar a Starter] - Hasta 10 miembros ($29.99/mes)                   │
│  [Actualizar a Professional] - Hasta 50 miembros ($99.99/mes)             │
│                                                                             │
│  [Cerrar]                                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Principios de Diseño del Paywall

**1. Transparencia Total:**

- Siempre mostrar qué límite se alcanzó
- Mostrar qué plan actual tiene el usuario
- Mostrar qué planes permiten la acción deseada

**2. Mensajes Positivos:**

- En lugar de "No puedes hacer esto"
- Usar "Para hacer esto, actualiza tu plan"
- Enfocarse en la solución, no en la restricción

**3. Opciones Claras:**

- Siempre mostrar al menos 2 opciones
- Destacar la opción recomendada
- Incluir opción de "Cerrar" sin presión

**4. Contexto Relevante:**

- Mostrar información específica del usuario
- Ejemplo: "Ya has creado 5 proyectos de 5 permitidos"
- Mostrar fecha de recarga si aplica

### 5.4 Implementación Técnica

**Backend Response:**

```json
{
  "error": "plan_limit_exceeded",
  "detail": "Plan limit exceeded: projects. Current: 5, Limit: 5.",
  "current_plan": "free",
  "limit_type": "max_projects",
  "current_count": 5,
  "limit": 5,
  "upgrade_options": [
    {
      "plan": "starter",
      "display_name": "Starter",
      "limit": 25,
      "price": 29.99
    },
    {
      "plan": "professional",
      "display_name": "Professional",
      "limit": 100,
      "price": 99.99
    }
  ]
}
```

**Frontend Logic:**

1. Capturar error 403 (Forbidden) o 402 (Payment Required)
2. Parsear respuesta del backend
3. Mostrar modal de paywall con información específica
4. Permitir upgrade directo desde el modal

---

## 6. COMPONENTES REUTILIZABLES

### 6.1 CreditBadge Component

**Props:**

```typescript
interface CreditBadgeProps {
  credits: number;
  isUnlimited?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}
```

**Uso:**

- Sidebar: mostrar créditos disponibles
- Dashboard: indicador rápido
- Header: siempre visible

### 6.2 PlanCard Component

**Props:**

```typescript
interface PlanCardProps {
  plan: PlanInfo;
  isCurrentPlan?: boolean;
  isPopular?: boolean;
  onSelect: (plan: string) => void;
  billingInterval: 'month' | 'year';
}
```

**Uso:**

- Pricing table
- Paywall modals
- Upgrade flows

### 6.3 CreditMeter Component

**Props:**

```typescript
interface CreditMeterProps {
  used: number;
  total: number;
  size?: 'sm' | 'md' | 'lg';
  showNumbers?: boolean;
  showLabel?: boolean;
}
```

**Uso:**

- Dashboard de créditos
- Widgets pequeños
- Modales de paywall

### 6.4 SubscriptionStatusBadge Component

**Props:**

```typescript
interface SubscriptionStatusBadgeProps {
  status: 'active' | 'trialing' | 'past_due' | 'cancelled' | 'incomplete';
  showIcon?: boolean;
}
```

**Uso:**

- Estado de suscripción
- Lista de facturas
- Header de configuración

---

## 7. FLUJOS DE USUARIO COMPLETOS

### 7.1 Flujo: Actualizar Plan

```
1. Usuario en página de Planes
   ↓
2. Selecciona nuevo plan (ej: Professional)
   ↓
3. Click en "Actualizar Plan"
   ↓
4. Validación de permisos
   ├─ Si no tiene permisos → Mostrar mensaje
   └─ Si tiene permisos → Continuar
   ↓
5. Crear checkout session en Stripe
   ↓
6. Redirigir a Stripe Checkout
   ↓
7. Usuario completa pago en Stripe
   ↓
8. Redirigir a success_url con ?success=true
   ↓
9. Mostrar mensaje de éxito
   ↓
10. Actualizar UI con nuevo plan
    ↓
11. Otorgar créditos del nuevo plan
```

### 7.2 Flujo: Manejo de Pago Fallido

```
1. Webhook de Stripe: invoice.payment_failed
   ↓
2. Backend actualiza estado a "past_due"
   ↓
3. Frontend detecta cambio de estado
   ↓
4. Mostrar modal de alerta inmediatamente
   ↓
5. Usuario ve mensaje explicativo
   ↓
6. Opciones:
   ├─ Actualizar método de pago → Stripe Customer Portal
   ├─ Contactar soporte → Formulario
   └─ Cerrar (con recordatorio)
   ↓
7. Si usuario actualiza método:
   ├─ Stripe reintenta pago automáticamente
   └─ Si éxito → Estado vuelve a "active"
   ↓
8. Si pasan 3 días sin resolver:
   ├─ Estado cambia a "incomplete_expired"
   └─ Mostrar mensaje de suspensión
```

### 7.3 Flujo: Consumo de Créditos

```
1. Usuario intenta acción que requiere créditos (ej: generar propuesta IA)
   ↓
2. Frontend valida créditos disponibles (opcional, para UX)
   ↓
3. Enviar request al backend
   ↓
4. Backend valida créditos:
   ├─ Si suficientes → Consumir créditos y ejecutar acción
   └─ Si insuficientes → Retornar error 402
   ↓
5. Si éxito:
   ├─ Mostrar confirmación
   └─ Actualizar UI de créditos
   ↓
6. Si error 402:
   ├─ Mostrar modal de paywall
   └─ Ofrecer upgrade o esperar recarga
```

---

## 8. CONSIDERACIONES ESPECIALES PARA COLOMBIA

### 8.1 Precios y Moneda

**Conversión Dinámica:**

- Mostrar precios en COP basados en tasa de cambio actual
- Actualizar automáticamente cuando cambie la tasa
- Fuente de tasa: API de cambio (ej: exchangerate-api.com)

**IVA:**

- Mostrar claramente "IVA incluido (19%)" para Colombia
- Calcular precio con IVA: `precio_usd * tasa_cambio * 1.19`
- Ejemplo: $29.99 USD → ~$120,000 COP (con IVA)

### 8.2 Métodos de Pago

**Tarjetas Internacionales:**

- Visa, Mastercard, American Express
- Mostrar logos de tarjetas aceptadas

**Métodos Locales (Futuro):**

- PSE (Pagos Seguros en Línea)
- Nequi
- Daviplata
- Integración con pasarelas locales

### 8.3 Manejo de Errores Comunes

**Tarjeta Rechazada por Seguridad:**

- Mensaje específico: "Tu banco rechazó el pago por seguridad. Esto es común en Colombia."
- Instrucciones claras: "Contacta a tu banco para autorizar transacciones internacionales"
- Opciones alternativas: Otra tarjeta, tarjeta prepago

**Límite de Transacción:**

- Detectar límite común en Colombia (~$200 USD)
- Sugerir dividir pago o usar método alternativo

**Problemas de Red:**

- Timeout común en conexiones colombianas
- Reintentos automáticos
- Mensaje claro si falla después de reintentos

### 8.4 Período de Gracia para Pagos

**Implementación:**

- 3 días de gracia después de pago fallido
- Contador visible en UI
- Recordatorios diarios por email
- No bloquear cuenta durante período de gracia

**UI del Contador:**

```
⚠️ Tu último pago falló. Tienes 2 días para resolverlo antes de que se suspenda tu cuenta.

[Actualizar Método de Pago] [Contactar Soporte]
```

---

## 9. INTEGRACIÓN CON STRIPE

### 9.1 Endpoints Utilizados

**Checkout Session:**

- `POST /api/v1/billing/checkout-session`
- Crea sesión de checkout en Stripe
- Redirige a Stripe Hosted Checkout

**Subscription:**

- `GET /api/v1/billing/subscription` - Obtener suscripción actual
- `PUT /api/v1/billing/subscription` - Actualizar suscripción
- `POST /api/v1/billing/subscription/cancel` - Cancelar suscripción

**Plans:**

- `GET /api/v1/billing/plans` - Listar planes disponibles

**Webhooks:**

- Stripe envía eventos a `/api/v1/billing/webhook`
- Eventos importantes:
  - `checkout.session.completed`
  - `customer.subscription.updated`
  - `invoice.payment_succeeded`
  - `invoice.payment_failed`

### 9.2 Customer Portal de Stripe

**Uso:**

- Permitir al usuario gestionar su método de pago
- Ver historial de facturas
- Actualizar información de facturación

**Implementación:**

- Crear portal session: `stripe.billingPortal.sessions.create()`
- Redirigir a URL del portal
- El usuario gestiona todo desde Stripe

---

## 10. MÉTRICAS Y ANALYTICS

### 10.1 Eventos a Trackear

**Conversión:**

- Click en "Actualizar Plan"
- Completar checkout
- Upgrade exitoso

**Paywall:**

- Paywall mostrado (por tipo)
- Click en upgrade desde paywall
- Cierre de paywall sin acción

**Créditos:**

- Consumo de créditos (por tipo de acción)
- Alerta mostrada (70%, 90%)
- Click en "Recargar Créditos"

**Errores:**

- Pago fallido
- Tarjeta rechazada
- Timeout de pago

### 10.2 KPIs Importantes

- **Tasa de Conversión:** % de usuarios que upgrade desde paywall
- **Tiempo hasta Upgrade:** Días desde registro hasta primer upgrade
- **Churn Rate:** % de cancelaciones mensuales
- **ARPU:** Ingreso promedio por usuario
- **LTV:** Valor de vida del cliente

---

## 11. ACCESIBILIDAD Y UX

### 11.1 Accesibilidad

- Todos los componentes deben ser accesibles por teclado
- Contraste de colores según WCAG AA
- Labels descriptivos para screen readers
- Focus visible en todos los elementos interactivos

### 11.2 Responsive Design

**Mobile:**

- Pricing table en columna única
- Modales a pantalla completa
- Botones de tamaño táctil (min 44x44px)

**Tablet:**

- Pricing table en 2 columnas
- Modales centrados

**Desktop:**

- Pricing table en 4 columnas
- Modales modales estándar

### 11.3 Loading States

- Mostrar skeleton loaders mientras carga información
- Botones con estado de loading durante acciones
- Mensajes claros durante procesos asíncronos

---

## 12. TESTING Y VALIDACIÓN

### 12.1 Casos de Prueba Críticos

1. **Actualización de Plan:**
   - Usuario sin permisos no puede cambiar plan
   - Checkout session se crea correctamente
   - Redirección a Stripe funciona
   - Webhook actualiza estado correctamente

2. **Consumo de Créditos:**
   - Créditos se consumen correctamente
   - Error 402 se muestra cuando no hay créditos
   - Paywall se muestra con información correcta

3. **Pago Fallido:**
   - Estado cambia a "past_due"
   - Modal de alerta se muestra
   - Período de gracia funciona correctamente
   - Suspensión después de 3 días

4. **Localización Colombia:**
   - Precios se muestran en COP
   - IVA se calcula correctamente
   - Mensajes de error son claros

---

## 13. PRÓXIMOS PASOS Y MEJORAS FUTURAS

### 13.1 Funcionalidades Futuras

1. **Compra de Créditos Adicionales (Top-up):**
   - Permitir comprar créditos sin cambiar plan
   - Precio por crédito: ~$0.10 USD
   - Créditos adicionales no expiran

2. **Programa de Referidos:**
   - Usuario gana créditos por referir amigos
   - Dashboard de referidos
   - Tracking de conversiones

3. **Descuentos y Promociones:**
   - Códigos de descuento
   - Promociones estacionales
   - Descuentos por pago anual

4. **Facturación Empresarial:**
   - Facturas con NIT
   - Opción de facturación manual
   - Integración con sistemas contables

---

## 14. GLOSARIO

**Crédito de IA:** Unidad de consumo para funciones que utilizan inteligencia artificial. Cada acción de IA tiene un costo en créditos.

**Paywall:** Barrera virtual que aparece cuando el usuario alcanza un límite de su plan, ofreciendo opciones de upgrade.

**Período de Gracia:** Tiempo adicional (3 días) después de un pago fallido antes de suspender la cuenta.

**Stripe Checkout:** Página de pago hospedada por Stripe donde el usuario completa su compra de forma segura.

**Webhook:** Notificación enviada por Stripe al backend cuando ocurre un evento (pago exitoso, fallido, etc.).

---

## 15. REFERENCIAS TÉCNICAS

### 15.1 Modelos de Backend

**Subscription:**

- `plan`: free, starter, professional, enterprise
- `status`: active, cancelled, past_due, trialing, incomplete, incomplete_expired
- `current_period_start`, `current_period_end`
- `trial_start`, `trial_end`

**CreditAccount:**

- `credits_available`: Créditos disponibles actualmente
- `credits_used_this_month`: Créditos usados este mes
- `credits_per_month`: Asignación mensual (NULL = ilimitado)
- `next_reset_at`: Fecha de próxima recarga

**CreditTransaction:**

- `transaction_type`: subscription_grant, manual_adjustment, consumption, refund
- `amount`: Cantidad (positivo = agregado, negativo = consumido)
- `reason`: Razón de la transacción
- `reference_id`: ID de referencia (ej: quote_id)

### 15.2 Endpoints de API

**Billing:**

- `GET /api/v1/billing/subscription` - Obtener suscripción
- `PUT /api/v1/billing/subscription` - Actualizar suscripción
- `POST /api/v1/billing/subscription/cancel` - Cancelar
- `POST /api/v1/billing/checkout-session` - Crear checkout
- `GET /api/v1/billing/plans` - Listar planes

**Credits:**

- `GET /api/v1/credits/me/balance` - Obtener balance
- `GET /api/v1/credits/me/history` - Historial de transacciones

---

**Fin del Documento**

---

## Notas para Figma Make

Al diseñar estos componentes en Figma, considera:

1. **Material Design:** Usar componentes de Material Design 3
2. **Colores:** Paleta minimalista y estética moderna
3. **Tipografía:** Jerarquía clara, tamaños consistentes
4. **Espaciado:** Generoso, respiración visual
5. **Iconografía:** Consistente, clara
6. **Estados:** Diseñar todos los estados (hover, active, disabled, loading)
7. **Responsive:** Diseñar para mobile, tablet y desktop
8. **Accesibilidad:** Contraste adecuado, tamaños táctiles

**Prioridad de Diseño:**

1. Pricing Table (Selector de Planes) - Alta prioridad
2. Credit Tracker (Dashboard de Créditos) - Alta prioridad
3. Paywall Modals - Alta prioridad
4. Estado de Suscripción - Media prioridad
5. Historial de Facturas - Media prioridad
