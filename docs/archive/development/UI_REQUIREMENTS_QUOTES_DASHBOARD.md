# Documento de Requerimientos de UI - Dashboard Comercial y Pipeline de Envío

**Versión:** 1.0  
**Fecha:** 2026-01-25  
**Propósito:** Especificaciones técnicas para diseño UI del Dashboard de Cotizaciones, Pipeline de Ventas y Proceso de Envío  
**Audiencia:** Diseñadores UI/UX, Desarrolladores Frontend, Figma Make

---

## Resumen Ejecutivo

Este documento especifica los requerimientos de interfaz de usuario para el **Dashboard Comercial y Pipeline de Envío de Cotizaciones** de Nougram. El sistema está diseñado para maximizar la conversión mediante trazabilidad completa, métricas claras y un proceso de envío que genera confianza.

**Objetivo Principal:** Proporcionar visibilidad total del pipeline de ventas, métricas de rentabilidad y un proceso de envío que permita seguimiento detallado de cada cotización.

**Principios de Diseño:**
- **Sense of Urgency:** Las cotizaciones que requieren atención deben destacarse visualmente
- **Trazabilidad Total:** El usuario siempre sabe qué pasó con cada cotización
- **Rentabilidad Visible:** Cada cotización muestra su margen de rentabilidad claramente
- **Preview Real:** El usuario ve exactamente qué recibirá el cliente antes de enviar

---

## ⭐ El "Viewed" es el Rey: El Superpoder de Nougram

**Problema que Resuelve:**
Saber que el cliente abrió la propuesta 5 veces en la última hora es la señal que el usuario necesita para llamar y cerrar el trato. Es el "Superpoder" de Nougram.

**Solución:**
- **Pixel de Seguimiento:** Cada email incluye un pixel invisible de 1x1px que registra cuando se abre
- **URL Única por Cotización:** Cada PDF tiene una URL única que registra descargas
- **Tracking en Tiempo Real:** El dashboard muestra aperturas y descargas en tiempo real
- **Alertas Inteligentes:** Notificar cuando una cotización se abre múltiples veces

**Impacto:**
- Usuarios que hacen seguimiento basado en tracking tienen 3x más probabilidad de cerrar
- Reducción del tiempo de respuesta a cotizaciones activas
- Mayor comprensión del interés del cliente

---

## 💡 Rentabilidad a la Vista: No es Solo una Lista de Precios

**Problema que Resuelve:**
Una cotización de $20M puede dejar el 40% o el 5% de utilidad real. Sin ver el margen, es solo una lista de precios.

**Solución:**
- **Indicador de Margen Visual:** Cada cotización muestra su margen de rentabilidad con código de colores
- **Comparación con BCR:** Mostrar si la cotización está por encima o debajo del BCR objetivo
- **Análisis de Rentabilidad:** Desglose completo de costos vs. precio final

**Código de Colores:**
- 🟢 Verde (>30%): Rentabilidad saludable
- 🟡 Amarillo (15-30%): Rentabilidad aceptable
- 🔴 Rojo (<15%): Rentabilidad crítica

---

## 📊 ESTADOS DE COTIZACIÓN

### Estados Técnicos Definidos

| Estado | Descripción | Trigger | Color UI |
|--------|-------------|---------|----------|
| **Draft** | Borrador, no enviado | Estado inicial al crear | Gris |
| **Sent** | Enviada al cliente | Al enviar email | Azul |
| **Viewed** | Cliente abrió el email/PDF | Pixel de tracking detecta apertura | Amarillo |
| **Accepted** | Cliente aceptó la cotización | Usuario marca manualmente | Verde |
| **Rejected** | Cliente rechazó la cotización | Usuario marca manualmente | Rojo |
| **Expired** | Cotización expiró (30 días) | Sistema marca automáticamente | Gris oscuro |

### Transiciones de Estado

```
Draft → Sent → Viewed → Accepted
                    ↓
                 Rejected
                    ↓
                 Expired (después de 30 días)
```

**Nota Técnica:** 
- El estado actual en el backend es `Project.status` con valores: Draft, Sent, Won, Lost
- Se requiere agregar estados: Viewed, Accepted, Rejected, Expired
- O usar un modelo separado `QuoteStatus` para tracking más granular

### Campos de Tracking Requeridos

**En Modelo Quote (o nuevo modelo QuoteTracking):**
- `sent_at`: DateTime - Cuándo se envió
- `viewed_at`: DateTime - Primera vez que se abrió
- `viewed_count`: Integer - Cuántas veces se abrió
- `last_viewed_at`: DateTime - Última vez que se abrió
- `downloaded_count`: Integer - Cuántas veces se descargó el PDF
- `last_downloaded_at`: DateTime - Última descarga
- `expires_at`: DateTime - Fecha de expiración (30 días desde envío)
- `accepted_at`: DateTime - Cuándo se aceptó
- `rejected_at`: DateTime - Cuándo se rechazó

---

## 🎨 ESPECIFICACIONES DE PANTALLAS Y COMPONENTES

---

## 1. LISTA MAESTRA DE COTIZACIONES (Pipeline Kanban)

### 1.1 Objetivo

Visualizar todas las cotizaciones en un formato tipo Kanban que permita identificar rápidamente cuáles requieren atención. Diseñado para generar "Sense of Urgency".

### 1.2 Estructura Visual (Vista Kanban)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Pipeline de Cotizaciones                                    [Filtros] [Buscar] │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  [Draft] (3)    [Sent] (5)    [Viewed] (2)    [Accepted] (1)  [Rejected] │
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │ Proyecto │  │ Proyecto │  │ Proyecto │  │ Proyecto │                │
│  │ Web App  │  │ E-commerce│  │ Landing  │  │ Branding │                │
│  │          │  │          │  │ Page     │  │          │                │
│  │ Cliente: │  │ Cliente: │  │ Cliente: │  │ Cliente: │                │
│  │ Acme Inc │  │ TechCorp │  │ StartupX │  │ DesignCo │                │
│  │          │  │          │  │          │  │          │                │
│  │ $15,000  │  │ $25,000  │  │ $8,000   │  │ $12,000  │                │
│  │ 🟢 42%   │  │ 🟡 22%   │  │ 🔴 8%    │  │ 🟢 35%   │                │
│  │          │  │          │  │          │  │          │                │
│  │ v1       │  │ v2       │  │ v1       │  │ v1       │                │
│  │          │  │          │  │          │  │          │                │
│  │ Enviado: │  │ Enviado: │  │ Enviado: │  │ Enviado: │                │
│  │ Hace 2d  │  │ Hace 5d  │  │ Hace 1d  │  │ Hace 3d  │                │
│  │          │  │          │  │          │  │          │                │
│  │          │  │ ⚠️ Vence │  │ 👁️ 5x   │  │ ✅ Aceptada│                │
│  │          │  │ en 2 días│  │ abierta  │  │          │                │
│  │          │  │          │  │          │  │          │                │
│  │ [Editar] │  │ [Ver]    │  │ [Seguir] │  │ [Ver]    │                │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Estructura Visual (Vista Lista)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Cotizaciones                                                               │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  [Filtros: Todos | Draft | Sent | Viewed | Accepted | Rejected | Expired] │
│  [Buscar: Nombre de proyecto, cliente...]                                 │
│  [Ordenar: Más reciente | Monto | Margen | Estado]                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ [Badge: Viewed]  Landing Page - StartupX          [🟡 22%]           │ │
│  │ ─────────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │ Cliente: StartupX                    Monto: $8,000 USD               │ │
│  │ Versión: v1                          Margen: 22% (Aceptable)          │ │
│  │                                                                       │ │
│  │ Enviado: Hace 1 día                  Vence: En 29 días               │ │
│  │ Abierta: 5 veces (última: hace 2h)  Descargas: 2                    │ │
│  │                                                                       │ │
│  │ 👁️ Esta cotización ha sido abierta 5 veces. Considera hacer         │ │
│  │    seguimiento activo.                                               │ │
│  │                                                                       │ │
│  │ [Ver Detalle] [Enviar Recordatorio] [Marcar como Aceptada]          │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ [Badge: Sent]  E-commerce - TechCorp              [🟢 42%]           │ │
│  │ ─────────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │ Cliente: TechCorp                   Monto: $25,000 USD               │ │
│  │ Versión: v2                         Margen: 42% (Excelente)          │ │
│  │                                                                       │ │
│  │ Enviado: Hace 5 días                 Vence: En 25 días               │ │
│  │ Abierta: 0 veces                    Descargas: 0                    │ │
│  │                                                                       │ │
│  │ ⚠️ Esta cotización vence en 2 días y no ha sido abierta.             │ │
│  │    Considera enviar un recordatorio.                                 │ │
│  │                                                                       │ │
│  │ [Ver Detalle] [Enviar Recordatorio] [Duplicar]                       │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  [Página 1 de 5] [< Anterior] [Siguiente >]                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.4 Componentes Requeridos

**Card de Cotización:**
- Badge de estado (color según estado)
- Nombre del proyecto
- Nombre del cliente
- Monto total (con moneda)
- Indicador de margen (código de colores)
- Versión (v1, v2, etc.)
- Fechas relevantes (enviado, vence, última apertura)
- Contadores (aperturas, descargas)
- Alertas contextuales (si requiere atención)
- Botones de acción según estado

**Badges de Estado:**
- Draft: Gris (#6B7280)
- Sent: Azul (#3B82F6)
- Viewed: Amarillo (#F59E0B) - Con ícono de ojo
- Accepted: Verde (#10B981) - Con checkmark
- Rejected: Rojo (#EF4444) - Con X
- Expired: Gris oscuro (#374151) - Con reloj

**Indicador de Margen:**
- Círculo pequeño con color:
  - Verde: >30%
  - Amarillo: 15-30%
  - Rojo: <15%
- Tooltip al hover: "Margen: 42% | BCR: $50/hora"

**Alertas Contextuales:**
- "Esta cotización ha sido abierta 5 veces. Considera hacer seguimiento."
- "Esta cotización vence en 2 días y no ha sido abierta."
- "Esta cotización tiene baja rentabilidad (8%). Considera revisar costos."

### 1.5 Filtros y Búsqueda

**Filtros Disponibles:**
- Estado: Todos, Draft, Sent, Viewed, Accepted, Rejected, Expired
- Cliente: Dropdown con lista de clientes
- Rango de fechas: Date picker (desde - hasta)
- Rango de monto: Input numérico (mínimo - máximo)
- Nivel de rentabilidad: Todos, Saludable (>30%), Aceptable (15-30%), Crítica (<15%)
- Moneda: USD, COP, ARS, EUR

**Búsqueda:**
- Por nombre de proyecto (búsqueda parcial)
- Por nombre de cliente (búsqueda parcial)
- Por número de cotización/versión

**Ordenamiento:**
- Más reciente (default)
- Más antigua
- Mayor monto
- Menor monto
- Mayor margen
- Menor margen
- Estado (alfabético)

---

## 2. VISTA DE DETALLE DE ENVÍO (Ready to Send)

### 2.1 Objetivo

Permitir al usuario revisar y personalizar el email antes de enviarlo, con preview real de lo que recibirá el cliente. Generar confianza mediante transparencia total.

### 2.2 Estructura Visual

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Enviar Cotización: Landing Page - StartupX                                │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Información de Envío                                                │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  Para (Email del Cliente) *                                         │ │
│  │  [Input: cliente@startupx.com]                                       │ │
│  │  ℹ️ Este email recibirá la cotización                                │ │
│  │                                                                       │ │
│  │  CC (Opcional)                                                       │ │
│  │  [Input: ]                                                           │ │
│  │                                                                       │ │
│  │  CCO (Opcional)                                                      │ │
│  │  [Input: ]                                                           │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Asunto del Email *                                                  │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  [Input: Cotización para Landing Page - Versión 1]                  │ │
│  │  [Sugerencia: "Cotización para {project_name} - Versión {version}"] │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Mensaje Personalizado                                                │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  [Textarea: Escribe un mensaje personalizado para el cliente...]     │ │
│  │                                                                       │ │
│  │  💡 Este mensaje aparecerá en el cuerpo del email antes del          │ │
│  │     resumen de la cotización.                                        │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Adjuntos                                                             │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  ☑ Incluir PDF de cotización                                         │ │
│  │     📄 cotizacion_landing_page_v1.pdf                                │ │
│  │                                                                       │ │
│  │  ☐ Incluir DOCX de cotización                                        │ │
│  │                                                                       │ │
│  │  ☐ Adjuntos adicionales                                              │ │
│  │     [Botón: Agregar Archivo]                                         │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  📧 Preview del Email                                                 │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────┐   │ │
│  │  │  De: Nougram <noreply@nougram.com>                         │   │ │
│  │  │  Para: cliente@startupx.com                                │   │ │
│  │  │  Asunto: Cotización para Landing Page - Versión 1          │   │ │
│  │  ├─────────────────────────────────────────────────────────────┤   │ │
│  │  │                                                             │   │ │
│  │  │  Estimado StartupX,                                        │   │ │
│  │  │                                                             │   │ │
│  │  │  [Mensaje personalizado si se escribió]                    │   │ │
│  │  │                                                             │   │ │
│  │  │  Gracias por tu interés en nuestros servicios.             │   │ │
│  │  │  Adjunto encontrarás la cotización para Landing Page.      │   │ │
│  │  │                                                             │   │ │
│  │  │  Proyecto: Landing Page                                    │   │ │
│  │  │  Versión: 1                                                │   │ │
│  │  │  Total: $8,000 USD                                         │   │ │
│  │  │                                                             │   │ │
│  │  │  Esta cotización es válida por 30 días.                    │   │ │
│  │  │                                                             │   │ │
│  │  │  Saludos,                                                  │   │ │
│  │  │  Equipo Nougram                                            │   │ │
│  │  │                                                             │   │ │
│  │  └─────────────────────────────────────────────────────────────┘   │ │
│  │                                                                       │ │
│  │  📎 Adjuntos:                                                        │ │
│  │     • cotizacion_landing_page_v1.pdf                                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Configuración de Tracking                                            │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  ☑ Activar seguimiento de aperturas (pixel de tracking)             │ │
│  │     ℹ️ Sabrás cuándo el cliente abre el email                        │ │
│  │                                                                       │ │
│  │  ☑ Activar seguimiento de descargas (URL única)                     │ │
│  │     ℹ️ Sabrás cuándo el cliente descarga el PDF                     │ │
│  │                                                                       │ │
│  │  ☑ Enviar notificaciones cuando se abra o descargue                 │ │
│  │     ℹ️ Recibirás alertas en tiempo real                              │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  [Cancelar]                                              [Enviar Cotización] │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Componentes Requeridos

**Formulario de Envío:**
- Campo de email (requerido, validación de email)
- Campo CC (opcional, múltiples emails)
- Campo CCO (opcional, múltiples emails)
- Campo de asunto (requerido, con sugerencia automática)
- Textarea de mensaje personalizado (opcional)
- Checkboxes para adjuntos (PDF, DOCX)
- Upload de archivos adicionales (opcional)

**Preview del Email:**
- Vista previa real del email que recibirá el cliente
- Estilo idéntico al email real
- Actualización en tiempo real cuando cambia el mensaje
- Mostrar adjuntos que se incluirán

**Configuración de Tracking:**
- Checkbox para activar pixel de tracking
- Checkbox para activar tracking de descargas
- Checkbox para notificaciones en tiempo real
- Tooltips explicativos de cada opción

**Validaciones:**
- Email válido requerido
- Asunto requerido
- Al menos un adjunto (PDF o DOCX) requerido
- Mostrar errores en tiempo real

### 2.4 Estados del Componente

**Estado Inicial:**
- Email del cliente prellenado desde proyecto
- Asunto sugerido automáticamente
- PDF marcado por defecto
- Tracking activado por defecto

**Estado de Envío:**
- Botón "Enviar" muestra loading
- Deshabilitar formulario durante envío
- Mostrar progreso si es necesario

**Estado de Éxito:**
- Mensaje de confirmación
- Redirigir a vista de detalle de cotización
- Mostrar estado actualizado (Sent)

**Estado de Error:**
- Mostrar mensaje de error específico
- Mantener datos del formulario
- Permitir reintentar

---

## 3. WIDGETS DE RESUMEN DE VENTAS (Dashboard)

### 3.1 Objetivo

Mostrar métricas clave del pipeline de ventas en widgets destacados que permitan tomar decisiones rápidas.

### 3.2 Estructura Visual

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Dashboard Comercial                                                         │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Total        │  │ Pipeline     │  │ Win Rate     │  │ Margen       │  │
│  │ Cotizado     │  │ Value        │  │              │  │ Promedio     │  │
│  │              │  │              │  │              │  │              │  │
│  │ $248,000     │  │ $85,000      │  │ 35%          │  │ 28%          │  │
│  │ USD          │  │ USD          │  │              │  │              │  │
│  │              │  │              │  │ ↑ 5% vs mes  │  │ 🟢 Saludable  │  │
│  │ ↑ 12% vs mes│  │ (3 cotiz.)   │  │ anterior     │  │              │  │
│  │ anterior     │  │              │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Cotizaciones por Estado                                               │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  [Gráfico de Barras o Pie Chart]                                     │ │
│  │                                                                       │ │
│  │  Draft: 3    Sent: 5    Viewed: 2    Accepted: 1    Rejected: 0     │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Cotizaciones que Requieren Atención                                  │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  ⚠️ 2 cotizaciones vencen en los próximos 3 días                     │ │
│  │  👁️ 1 cotización abierta 5+ veces sin respuesta                     │ │
│  │  🔴 1 cotización con rentabilidad crítica (<15%)                     │ │
│  │                                                                       │ │
│  │  [Ver Todas →]                                                       │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Tendencia Mensual                                                    │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  [Gráfico de Líneas: Total Cotizado por Mes]                         │ │
│  │                                                                       │ │
│  │  Ene  Feb  Mar  Abr  May  Jun                                        │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Métricas Requeridas

**Total Cotizado:**
- Suma de `total_client_price` de todas las cotizaciones
- Filtrable por período (mes actual, mes anterior, año, personalizado)
- Comparación con período anterior (% de cambio)
- Formato: Moneda con símbolo, miles separados

**Pipeline Value:**
- Suma de `total_client_price` de cotizaciones en estado: Sent, Viewed
- Excluye: Draft, Accepted, Rejected, Expired
- Mostrar número de cotizaciones entre paréntesis
- Formato: Moneda con símbolo

**Win Rate (Tasa de Aceptación):**
- Fórmula: `(Accepted / (Accepted + Rejected)) * 100`
- Solo cuenta cotizaciones finalizadas (Accepted o Rejected)
- Comparación con período anterior
- Formato: Porcentaje con 1 decimal

**Margen Promedio:**
- Promedio de `margin_percentage` de todas las cotizaciones
- Filtrable por período
- Indicador de salud (verde/amarillo/rojo)
- Formato: Porcentaje con 1 decimal

**Cotizaciones por Estado:**
- Conteo agrupado por estado
- Gráfico visual (barras o pie)
- Click para filtrar por estado

**Cotizaciones que Requieren Atención:**
- Vencen en próximos 3 días
- Abiertas 5+ veces sin respuesta
- Rentabilidad crítica (<15%)
- Lista con links a cada cotización

**Tendencia Mensual:**
- Gráfico de líneas con total cotizado por mes
- Últimos 6-12 meses
- Opción de comparar con año anterior

### 3.4 Componentes Requeridos

**Widget de Métrica:**
- Título
- Valor grande y destacado
- Unidad (moneda, porcentaje)
- Comparación con período anterior (flecha arriba/abajo, porcentaje)
- Color según tendencia (verde = positivo, rojo = negativo)

**Widget de Gráfico:**
- Título
- Gráfico (barras, líneas, pie según métrica)
- Leyenda
- Tooltips al hover
- Opción de exportar (futuro)

**Widget de Alertas:**
- Lista de alertas con íconos
- Cada alerta es clickeable
- Link a acción relevante
- Contador de alertas en badge

---

## 4. TRAZABILIDAD (Tracking)

### 4.1 Objetivo

Registrar y mostrar toda la actividad relacionada con cada cotización: envíos, aperturas, descargas y cambios de estado.

### 4.2 Estructura Visual (Vista de Tracking)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Trazabilidad: Landing Page - StartupX                                      │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Resumen de Actividad                                                 │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  Estado Actual: Viewed                                               │ │
│  │  Enviada: 15 de Enero, 2026 a las 10:30 AM                          │ │
│  │  Primera Apertura: 15 de Enero, 2026 a las 2:15 PM                  │ │
│  │  Última Apertura: 25 de Enero, 2026 a las 3:45 PM                   │ │
│  │  Total de Aperturas: 5                                               │ │
│  │  Total de Descargas: 2                                               │ │
│  │  Vence: 14 de Febrero, 2026                                          │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Timeline de Eventos                                                 │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  ┌───────────────────────────────────────────────────────────────┐  │ │
│  │  │ ● 25 Ene 2026, 3:45 PM                                       │  │ │
│  │  │   Email abierto por cliente@startupx.com                      │  │ │
│  │  │   📍 Ubicación: Bogotá, Colombia                              │  │ │
│  │  │   💻 Dispositivo: Desktop (Chrome)                            │  │ │
│  │  └───────────────────────────────────────────────────────────────┘  │ │
│  │                                                                       │ │
│  │  ┌───────────────────────────────────────────────────────────────┐  │ │
│  │  │ ● 24 Ene 2026, 10:20 AM                                      │  │ │
│  │  │   PDF descargado                                              │  │ │
│  │  │   📄 cotizacion_landing_page_v1.pdf                           │  │ │
│  │  └───────────────────────────────────────────────────────────────┘  │ │
│  │                                                                       │ │
│  │  ┌───────────────────────────────────────────────────────────────┐  │ │
│  │  │ ● 20 Ene 2026, 4:30 PM                                       │  │ │
│  │  │   Email abierto (4ta vez)                                     │  │ │
│  │  └───────────────────────────────────────────────────────────────┘  │ │
│  │                                                                       │ │
│  │  ┌───────────────────────────────────────────────────────────────┐  │ │
│  │  │ ● 18 Ene 2026, 11:15 AM                                      │  │ │
│  │  │   PDF descargado (1ra vez)                                    │  │ │
│  │  └───────────────────────────────────────────────────────────────┘  │ │
│  │                                                                       │ │
│  │  ┌───────────────────────────────────────────────────────────────┐  │ │
│  │  │ ● 15 Ene 2026, 2:15 PM                                       │  │ │
│  │  │   Email abierto por primera vez                               │  │ │
│  │  │   📍 Ubicación: Bogotá, Colombia                              │  │ │
│  │  └───────────────────────────────────────────────────────────────┘  │ │
│  │                                                                       │ │
│  │  ┌───────────────────────────────────────────────────────────────┐  │ │
│  │  │ ● 15 Ene 2026, 10:30 AM                                      │  │ │
│  │  │   Cotización enviada por Juan Pérez                            │  │ │
│  │  │   📧 Para: cliente@startupx.com                               │  │ │
│  │  │   📎 Adjuntos: PDF                                            │  │ │
│  │  └───────────────────────────────────────────────────────────────┘  │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Análisis de Interés                                                  │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  📊 Esta cotización muestra señales de alto interés:                 │ │
│  │                                                                       │ │
│  │  • Abierta 5 veces en los últimos 10 días                           │ │
│  │  • PDF descargado 2 veces                                           │ │
│  │  • Última apertura hace menos de 2 horas                            │ │
│  │                                                                       │ │
│  │  💡 Recomendación: Considera hacer seguimiento activo. El cliente    │ │
│  │     está revisando la propuesta activamente.                         │ │
│  │                                                                       │ │
│  │  [Enviar Recordatorio] [Llamar Cliente] [Marcar como Aceptada]     │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Implementación Técnica del Tracking

**Pixel de Seguimiento (Email Opens):**
```html
<!-- En el HTML del email -->
<img src="https://api.nougram.com/tracking/pixel/{quote_id}/{unique_token}" 
     width="1" height="1" style="display:none;" />
```

**URL Única para PDF (Downloads):**
```
https://api.nougram.com/quotes/{quote_id}/pdf/{unique_token}
```

**Endpoint de Tracking:**
```python
GET /api/v1/tracking/pixel/{quote_id}/{token}
# Registra apertura, retorna 1x1px transparente

GET /api/v1/quotes/{quote_id}/pdf/{token}
# Registra descarga, retorna PDF
```

**Datos a Capturar:**
- Timestamp
- IP address (para ubicación aproximada)
- User-Agent (para dispositivo/navegador)
- Referer (si aplica)
- Email del destinatario (si se puede identificar)

### 4.4 Componentes Requeridos

**Timeline de Eventos:**
- Lista cronológica inversa (más reciente primero)
- Iconos por tipo de evento
- Información contextual (ubicación, dispositivo)
- Fechas formateadas (relativas: "hace 2 horas", absolutas: "25 Ene 2026, 3:45 PM")

**Análisis de Interés:**
- Algoritmo que analiza patrones de apertura/descarga
- Señales de alto interés (múltiples aperturas, descargas recientes)
- Recomendaciones accionables
- Botones de acción rápida

**Gráficos de Actividad:**
- Gráfico de aperturas por día
- Gráfico de descargas por día
- Heatmap de actividad (qué días/horas hay más actividad)

---

## 5. VERSIÓN DE COTIZACIONES

### 5.1 Objetivo

Permitir crear múltiples versiones de una cotización sin ensuciar el dashboard. Cada versión mantiene su propio tracking.

### 5.2 Estructura Visual

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Versiones de Cotización: Landing Page - StartupX                           │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Versión Actual: v2                                                  │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  Estado: Viewed                                                      │ │
│  │  Monto: $8,500 USD (cambio: +$500 vs v1)                            │ │
│  │  Margen: 25% (cambio: +3% vs v1)                                     │ │
│  │  Enviada: 20 de Enero, 2026                                         │ │
│  │  Abierta: 2 veces                                                    │ │
│  │                                                                       │ │
│  │  [Ver Detalle] [Enviar] [Duplicar como v3]                          │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Historial de Versiones                                              │ │
│  │  ───────────────────────────────────────────────────────────────────  │ │
│  │                                                                       │ │
│  │  ┌───────────────────────────────────────────────────────────────┐  │ │
│  │  │ v2 - Actual                    [Badge: Viewed]                │  │ │
│  │  │ ─────────────────────────────────────────────────────────────  │  │ │
│  │  │                                                               │  │ │
│  │  │ Monto: $8,500 USD  |  Margen: 25%  |  Enviada: 20 Ene 2026  │  │ │
│  │  │ Abierta: 2 veces    |  Descargas: 0                           │  │ │
│  │  │                                                               │  │ │
│  │  │ Cambios vs v1:                                                 │  │ │
│  │  │ • Precio aumentado en $500                                    │  │ │
│  │  │ • Servicio "SEO" agregado                                     │  │ │
│  │  │                                                               │  │ │
│  │  │ [Ver] [Comparar con v1]                                       │  │ │
│  │  └───────────────────────────────────────────────────────────────┘  │ │
│  │                                                                       │ │
│  │  ┌───────────────────────────────────────────────────────────────┐  │ │
│  │  │ v1                            [Badge: Viewed]                │  │ │
│  │  │ ─────────────────────────────────────────────────────────────  │  │ │
│  │  │                                                               │  │ │
│  │  │ Monto: $8,000 USD  |  Margen: 22%  |  Enviada: 15 Ene 2026  │  │ │
│  │  │ Abierta: 5 veces    |  Descargas: 2                          │  │ │
│  │  │                                                               │  │ │
│  │  │ [Ver] [Comparar con v2] [Duplicar]                           │  │ │
│  │  └───────────────────────────────────────────────────────────────┘  │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  [Crear Nueva Versión]                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Funcionalidades Requeridas

**Crear Nueva Versión:**
- Botón "Duplicar como v3" en versión actual
- Copiar todos los items y configuración
- Incrementar número de versión automáticamente
- Mantener historial de versiones anteriores

**Comparar Versiones:**
- Vista side-by-side de dos versiones
- Resaltar diferencias (precios, items agregados/eliminados)
- Mostrar cambios en monto y margen

**Tracking por Versión:**
- Cada versión tiene su propio tracking
- No mezclar aperturas/descargas entre versiones
- Dashboard muestra solo versión actual por defecto

---

## 6. FILTROS Y BÚSQUEDA AVANZADA

### 6.1 Parámetros de Filtrado

**Por Cliente:**
- Dropdown con lista de clientes únicos
- Búsqueda dentro del dropdown
- Opción "Todos los clientes"

**Por Rango de Fechas:**
- Date picker para fecha inicio
- Date picker para fecha fin
- Presets rápidos:
  - Últimos 7 días
  - Último mes
  - Últimos 3 meses
  - Este año
  - Año anterior

**Por Monto:**
- Input numérico mínimo
- Input numérico máximo
- Selector de moneda
- Validación: mínimo <= máximo

**Por Nivel de Rentabilidad:**
- Radio buttons o checkboxes:
  - Todos
  - Saludable (>30%)
  - Aceptable (15-30%)
  - Crítica (<15%)
- Mostrar número de cotizaciones por categoría

**Por Estado:**
- Checkboxes múltiples:
  - Draft
  - Sent
  - Viewed
  - Accepted
  - Rejected
  - Expired
- Mostrar contador por estado

**Por Moneda:**
- Checkboxes múltiples:
  - USD
  - COP
  - ARS
  - EUR

### 6.2 Búsqueda

**Campos de Búsqueda:**
- Nombre de proyecto (búsqueda parcial, case-insensitive)
- Nombre de cliente (búsqueda parcial, case-insensitive)
- Número de cotización (búsqueda exacta)
- Versión (búsqueda exacta)

**Búsqueda Inteligente:**
- Un solo campo de búsqueda que busca en todos los campos
- Autocompletado con sugerencias
- Resaltar términos encontrados en resultados

### 6.3 Guardar Filtros

**Filtros Guardados:**
- Permitir guardar combinaciones de filtros como "vistas"
- Nombre personalizado para cada vista guardada
- Acceso rápido desde dropdown
- Opción de compartir vistas (futuro)

---

## 7. INTEGRACIÓN CON BACKEND

### 7.1 Endpoints Requeridos

**Listar Cotizaciones:**
```
GET /api/v1/projects/{project_id}/quotes
GET /api/v1/quotes?status=viewed&client=startupx&min_amount=5000&max_amount=10000
```

**Obtener Detalle:**
```
GET /api/v1/projects/{project_id}/quotes/{quote_id}
```

**Enviar Cotización:**
```
POST /api/v1/projects/{project_id}/quotes/{quote_id}/send-email
Body: {
  to_email: string,
  subject?: string,
  message?: string,
  cc?: string[],
  bcc?: string[],
  include_pdf: boolean,
  include_docx: boolean,
  enable_tracking: boolean
}
```

**Tracking:**
```
GET /api/v1/tracking/pixel/{quote_id}/{token}
GET /api/v1/quotes/{quote_id}/pdf/{token}
GET /api/v1/quotes/{quote_id}/tracking
```

**Métricas:**
```
GET /api/v1/insights/dashboard?start_date=2026-01-01&end_date=2026-01-31
GET /api/v1/insights/quotes-metrics?status=sent,viewed
```

**Versiones:**
```
GET /api/v1/projects/{project_id}/quotes/{quote_id}/versions
POST /api/v1/projects/{project_id}/quotes/{quote_id}/duplicate
GET /api/v1/projects/{project_id}/quotes/{quote_id}/compare?version1=1&version2=2
```

### 7.2 Modelos de Datos Requeridos

**Quote (Extendido):**
```python
class Quote(Base):
    # Campos existentes...
    version = Column(Integer, default=1)
    
    # Nuevos campos de tracking
    sent_at = Column(DateTime(timezone=True), nullable=True)
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    viewed_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime(timezone=True), nullable=True)
    downloaded_count = Column(Integer, default=0)
    last_downloaded_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    tracking_token = Column(String, unique=True, nullable=True)  # Token único para tracking
```

**QuoteTrackingEvent (Nuevo):**
```python
class QuoteTrackingEvent(Base):
    id = Column(Integer, primary_key=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"))
    event_type = Column(String)  # "sent", "opened", "downloaded", "accepted", "rejected"
    occurred_at = Column(DateTime(timezone=True))
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    location = Column(String, nullable=True)  # Ciudad, País
    device_type = Column(String, nullable=True)  # Desktop, Mobile, Tablet
```

---

## 8. CONSIDERACIONES ESPECIALES

### 8.1 Privacidad y Tracking

**Transparencia:**
- Informar al usuario que se está usando tracking
- Opción de desactivar tracking (aunque no recomendado)
- Cumplir con GDPR/privacidad de datos

**Datos Sensibles:**
- No almacenar IP completa (solo primeros 3 octetos)
- No almacenar información personal del cliente sin consentimiento
- Anonimizar datos después de X tiempo

### 8.2 Performance

**Caching:**
- Cachear métricas del dashboard (2 minutos TTL)
- Cachear lista de cotizaciones con filtros comunes
- Invalidar cache cuando hay cambios

**Paginación:**
- Máximo 50 cotizaciones por página
- Lazy loading para timeline de eventos
- Virtual scrolling para listas largas

### 8.3 Notificaciones en Tiempo Real

**WebSockets o Polling:**
- Notificar cuando se abre una cotización
- Notificar cuando se descarga un PDF
- Badge de notificaciones en tiempo real
- Opción de desactivar notificaciones

---

## 9. FLUJOS DE USUARIO COMPLETOS

### 9.1 Flujo: Enviar Cotización

```
1. Usuario en lista de cotizaciones
   ↓
2. Click en "Enviar" en cotización Draft
   ↓
3. Abre vista "Ready to Send"
   ↓
4. Revisa email del cliente (prellenado)
   ↓
5. Personaliza asunto y mensaje (opcional)
   ↓
6. Selecciona adjuntos (PDF por defecto)
   ↓
7. Revisa preview del email
   ↓
8. Confirma configuración de tracking
   ↓
9. Click en "Enviar Cotización"
   ↓
10. Sistema envía email y registra evento
    ↓
11. Redirige a vista de detalle con tracking
    ↓
12. Estado cambia a "Sent"
```

### 9.2 Flujo: Tracking de Apertura

```
1. Cliente recibe email con pixel de tracking
   ↓
2. Cliente abre email
   ↓
3. Navegador carga pixel invisible
   ↓
4. Backend registra evento "opened"
   ↓
5. Si es primera apertura, cambia estado a "Viewed"
   ↓
6. Incrementa contador viewed_count
   ↓
7. Actualiza last_viewed_at
   ↓
8. Si notificaciones activas, envía notificación a usuario
   ↓
9. Dashboard se actualiza en tiempo real (WebSocket)
```

### 9.3 Flujo: Seguimiento Activo

```
1. Usuario ve alerta: "Cotización abierta 5 veces"
   ↓
2. Click en cotización para ver detalle
   ↓
3. Revisa timeline de eventos
   ↓
4. Ve análisis de interés: "Alto interés detectado"
   ↓
5. Click en "Enviar Recordatorio"
   ↓
6. Abre vista de envío con mensaje prellenado
   ↓
7. Personaliza mensaje de seguimiento
   ↓
8. Envía recordatorio
   ↓
9. Sistema registra nuevo envío (mantiene versión)
```

---

## 10. ACCESIBILIDAD Y UX

### 10.1 Accesibilidad

- Todos los componentes accesibles por teclado
- Contraste de colores según WCAG AA
- Labels descriptivos para screen readers
- Focus visible en elementos interactivos
- Tooltips accesibles

### 10.2 Responsive Design

**Mobile:**
- Vista Kanban en scroll horizontal
- Cards apiladas verticalmente
- Filtros en drawer lateral
- Preview de email a pantalla completa

**Tablet:**
- Vista Kanban en 2-3 columnas
- Cards más compactas
- Filtros en sidebar

**Desktop:**
- Vista Kanban en 4-5 columnas
- Cards completas con toda la información
- Filtros siempre visibles

### 10.3 Loading States

- Skeleton loaders para lista de cotizaciones
- Loading spinner durante envío
- Progress bar para generación de PDFs
- Mensajes claros durante procesos asíncronos

---

## 11. TESTING Y VALIDACIÓN

### 11.1 Casos de Prueba Críticos

1. **Envío de Cotización:**
   - Email válido requerido
   - Asunto se genera automáticamente si está vacío
   - Preview muestra contenido correcto
   - Tracking se activa correctamente

2. **Tracking de Aperturas:**
   - Pixel se carga correctamente
   - Evento se registra en backend
   - Estado cambia a "Viewed" en primera apertura
   - Contador se incrementa correctamente

3. **Tracking de Descargas:**
   - URL única funciona correctamente
   - PDF se descarga sin problemas
   - Evento se registra
   - Contador se incrementa

4. **Métricas del Dashboard:**
   - Total Cotizado calcula correctamente
   - Win Rate usa fórmula correcta
   - Pipeline Value excluye estados correctos
   - Filtros funcionan correctamente

---

## 12. PRÓXIMOS PASOS Y MEJORAS FUTURAS

### 12.1 Funcionalidades Futuras

1. **Recordatorios Automáticos:**
   - Enviar recordatorio si no se abre en X días
   - Enviar recordatorio si vence en X días
   - Configuración de reglas de recordatorio

2. **Templates de Email:**
   - Guardar mensajes personalizados como templates
   - Variables dinámicas ({client_name}, {project_name})
   - Biblioteca de templates

3. **Análisis Predictivo:**
   - Predecir probabilidad de aceptación basado en historial
   - Sugerir mejor momento para enviar
   - Recomendaciones de precio basadas en datos

4. **Integración con CRM:**
   - Sincronizar con HubSpot, Salesforce, etc.
   - Crear oportunidades automáticamente
   - Sincronizar estados bidireccionalmente

---

## 13. GLOSARIO

**Pixel de Tracking:** Imagen invisible de 1x1px incluida en emails que registra cuando se abre.

**URL Única:** URL específica para cada cotización que permite rastrear descargas.

**Win Rate:** Porcentaje de cotizaciones aceptadas vs rechazadas.

**Pipeline Value:** Valor total de cotizaciones pendientes (Sent + Viewed).

**BCR:** Blended Cost Rate - Costo promedio por hora de la agencia.

**Margen de Rentabilidad:** Diferencia entre precio al cliente y costo interno, expresado como porcentaje.

---

## 14. REFERENCIAS TÉCNICAS

### 14.1 Modelos de Backend

**Project:**
- `status`: Draft, Sent, Won, Lost (requiere extender con Viewed, Accepted, Rejected, Expired)
- `client_name`, `client_email`
- `created_at`, `updated_at`

**Quote:**
- `version`: Número de versión (1, 2, 3...)
- `total_client_price`: Precio total al cliente
- `total_internal_cost`: Costo interno total
- `margin_percentage`: Margen calculado
- `created_at`, `updated_at`

**QuoteTrackingEvent (Nuevo):**
- `quote_id`: ID de la cotización
- `event_type`: Tipo de evento
- `occurred_at`: Cuándo ocurrió
- `ip_address`, `user_agent`, `location`: Datos de tracking

### 14.2 Endpoints de API

**Cotizaciones:**
- `GET /api/v1/projects/{project_id}/quotes` - Listar cotizaciones
- `GET /api/v1/projects/{project_id}/quotes/{quote_id}` - Detalle
- `POST /api/v1/projects/{project_id}/quotes/{quote_id}/send-email` - Enviar

**Tracking:**
- `GET /api/v1/tracking/pixel/{quote_id}/{token}` - Pixel de tracking
- `GET /api/v1/quotes/{quote_id}/pdf/{token}` - PDF con tracking
- `GET /api/v1/quotes/{quote_id}/tracking` - Historial de tracking

**Métricas:**
- `GET /api/v1/insights/dashboard` - Métricas del dashboard
- `GET /api/v1/insights/quotes-metrics` - Métricas de cotizaciones

---

**Fin del Documento**

---

## Notas para Figma Make

Al diseñar estos componentes en Figma, considera:

1. **Material Design:** Usar componentes de Material Design 3
2. **Sense of Urgency:** Colores vibrantes para estados que requieren atención
3. **Preview Real:** El preview del email debe ser idéntico al email real
4. **Tracking Visible:** Los indicadores de tracking deben ser claros pero no intrusivos
5. **Rentabilidad Destacada:** El margen debe ser visible en cada cotización
6. **Versiones Claras:** Diferenciar visualmente entre versiones
7. **Responsive:** Diseñar para mobile, tablet y desktop
8. **Accesibilidad:** Contraste adecuado, tamaños táctiles

**Prioridad de Diseño:**
1. Lista Maestra de Cotizaciones (Pipeline Kanban) - Alta prioridad
2. Vista de Detalle de Envío (Ready to Send) - Alta prioridad
3. Widgets de Resumen de Ventas - Alta prioridad
4. Vista de Trazabilidad (Tracking) - Media prioridad
5. Gestión de Versiones - Media prioridad
