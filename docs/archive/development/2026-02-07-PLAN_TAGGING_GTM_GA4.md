# Plan de Tagging – GTM y GA4 (Nougram)

**Fecha:** 2026-02-07  
**Objetivo:** Definir eventos, parámetros y criterios para medir navegación, usuarios y acciones de negocio (propuestas/cotizaciones) con Google Tag Manager y Google Analytics 4.

---

## 1. Objetivos de medición

| Objetivo | Descripción |
|----------|-------------|
| **Navegación** | Rutas visitadas, tiempo en página, flujo entre secciones (dashboard, cotizaciones, proyectos, analytics). |
| **Identificación de usuarios** | Asociar eventos al usuario logueado (User ID) y, opcionalmente, a la organización (multi-tenant). |
| **Acciones de negocio** | Creación de propuestas, cambio de estado (Draft → Sent → Won/Lost), valores (total cliente, margen). |
| **Engagement** | Export PDF/DOCX, envío por email, generación de enlace público. |

---

## 2. Identificación de usuarios

La app tiene registro y login; el backend expone `/auth/me` con `id`, `email`, `full_name`, `role`.  
No enviar PII (email/nombre) a GA4 como dimensiones; usar identificadores anónimos para reporting.

| Dato | Uso en GA4/GTM | Notas |
|------|----------------|-------|
| **User ID** (`id` numérico del usuario) | Configurar como **User ID** de GA4. | Permite análisis por usuario y cruce de sesiones. |
| **Organization ID** | Parámetro/dimensión personalizada (ej. `organization_id`). | Si el backend lo devuelve en `/auth/me` o en contexto. |
| **Rol** | Opcional: dimensión personalizada (ej. `user_role`: owner, admin_financiero, etc.). | Para segmentar por tipo de usuario. |

**Cuándo enviar:** Tras login o al cargar sesión (cuando `useAuth().user` esté disponible). Un único `dataLayer.push` de identificación por sesión es suficiente.

---

## 3. Eventos de navegación

| Evento GA4 | Cuándo disparar | Parámetros recomendados |
|------------|-----------------|-------------------------|
| **page_view** | En cada cambio de ruta (App Router). | `page_path`, `page_title` (opcional). |

En una SPA (Next.js), las vistas no recargan; hay que enviar un `page_view` en cada transición de ruta (por ejemplo desde un componente que use `usePathname()` y haga `dataLayer.push` al cambiar `pathname`).

---

## 4. Eventos de propuestas / cotizaciones

El dominio usa **proyectos** (`Project`) con **cotizaciones** (`Quote`). Los estados de proyecto son: **Draft**, **Sent**, **Won**, **Lost**.

### 4.1 Propuesta creada

| Campo | Valor / descripción |
|-------|----------------------|
| **Nombre del evento** | `propuesta_creada` |
| **Cuándo** | Tras crear proyecto/cotización con éxito (respuesta 200 de `POST /projects/`). |
| **Parámetros** | Ver tabla siguiente. |

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `project_id` | string | ID del proyecto (propuesta). |
| `status` | string | Siempre `Draft` al crear. |
| `total_client_price` | number | Valor total al cliente (ej. `total_client_price` de la quote). |
| `total_internal_cost` | number | Costo interno total (opcional). |
| `currency` | string | Moneda (USD, COP, etc.). |
| `margin_percentage` | number | Margen % (opcional). |
| `user_id` | string | ID del usuario (para consistencia). |
| `organization_id` | string | (Opcional) Si está disponible. |

### 4.2 Cambio de estado de propuesta

| Campo | Valor / descripción |
|-------|----------------------|
| **Nombre del evento** | `propuesta_estado_cambiado` |
| **Cuándo** | Tras actualizar estado del proyecto (Draft → Sent, Sent → Won/Lost) con éxito. |
| **Parámetros** | Ver tabla siguiente. |

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `project_id` | string | ID del proyecto. |
| `old_status` | string | Estado anterior: `Draft`, `Sent`, `Won`, `Lost`. |
| `new_status` | string | Estado nuevo. |
| `total_client_price` | number | Valor actual de la cotización (opcional pero recomendado). |
| `currency` | string | Moneda. |
| `user_id` | string | ID del usuario. |
| `organization_id` | string | (Opcional). |

### 4.3 Otros eventos de cotización (opcional)

| Evento | Cuándo | Parámetros sugeridos |
|--------|--------|----------------------|
| `propuesta_export_pdf` | Usuario exporta PDF. | `project_id`, `user_id`. |
| `propuesta_export_docx` | Usuario exporta DOCX. | `project_id`, `user_id`. |
| `propuesta_email_enviado` | Envío de cotización por email exitoso. | `project_id`, `user_id`. |
| `propuesta_enlace_publico` | Usuario genera enlace público. | `project_id`, `user_id`. |

---

## 5. Resumen de eventos y dataLayer

Formato genérico de `dataLayer.push` para GTM:

```js
window.dataLayer = window.dataLayer || [];
window.dataLayer.push({
  event: 'nombre_del_evento',
  // parámetros según el evento
});
```

### 5.1 Identificación de usuario (una vez por sesión)

```js
dataLayer.push({
  event: 'user_identify',
  user_id: '123',           // id del usuario (string)
  organization_id: '456',  // opcional
  user_role: 'owner'       // opcional
});
```

### 5.2 Propuesta creada

```js
dataLayer.push({
  event: 'propuesta_creada',
  project_id: '42',
  status: 'Draft',
  total_client_price: 15000.50,
  total_internal_cost: 9000,
  currency: 'USD',
  margin_percentage: 40,
  user_id: '123',
  organization_id: '456'
});
```

### 5.3 Propuesta estado cambiado

```js
dataLayer.push({
  event: 'propuesta_estado_cambiado',
  project_id: '42',
  old_status: 'Draft',
  new_status: 'Sent',
  total_client_price: 15000.50,
  currency: 'USD',
  user_id: '123',
  organization_id: '456'
});
```

### 5.4 Navegación (vista de página)

```js
dataLayer.push({
  event: 'page_view',
  page_path: '/dashboard/quotes',
  page_title: 'Cotizaciones'
});
```

---

## 6. Configuración en GA4

- **User ID:** Configurar en el tag de GA4 usando la variable de dataLayer `user_id` (enviada en `user_identify` y, si se desea, en cada evento).
- **Eventos personalizados:** Los eventos `propuesta_creada`, `propuesta_estado_cambiado`, etc. se crean como eventos personalizados en GA4; no hace falta registrarlos por adelantado si se envían con el tag estándar de GA4.
- **Parámetros de evento:** Registrar como **parámetros de evento** (o **dimensiones personalizadas**) en GA4 los que quieras usar en informes: `project_id`, `old_status`, `new_status`, `total_client_price`, `currency`, `organization_id`, `user_role`, etc.
- **Métricas:** `total_client_price` puede usarse como métrica (suma de valor de propuestas creadas o ganadas) creando una métrica personalizada a partir del parámetro.

---

## 7. Puntos de implementación en código (referencia)

| Acción | Dónde en el frontend |
|--------|----------------------|
| Cargar GTM + enviar `user_identify` | Layout raíz (`nougram_front/src/app/layout.tsx`) o componente que tenga acceso al usuario logueado (ej. dentro de `NougramCoreProvider` o tras validar `useAuth().user`). |
| `page_view` en cada ruta | Componente cliente que use `usePathname()` (Next.js) y haga `dataLayer.push` cuando cambie `pathname`. |
| `propuesta_creada` | Donde se llame a `quoteService.create()` y se reciba la respuesta con `project_id` y totales (ej. después de crear proyecto en flujo stepped o en el contexto del quote builder). |
| `propuesta_estado_cambiado` | Donde se llame a `quoteService.updateStatus()` o `quoteService.setProjectStatus()` con éxito. |
| Eventos opcionales (export, email, enlace) | Handlers de los botones/acciones correspondientes tras la llamada exitosa al API. |

---

## 8. Próximos pasos

1. Implementar capa `dataLayer` y script GTM en el frontend (ver guía de implementación).
2. Configurar en GTM: variables de dataLayer, tag GA4 (con User ID), triggers por nombre de evento.
3. En GA4: definir parámetros/dimensiones personalizadas y métricas si se desea valor total.
4. Probar en entorno de desarrollo/staging con GA4 en modo debug antes de producción.

Documento relacionado: [2026-02-07-GUIA_IMPLEMENTACION_GTM_GA4.md](./2026-02-07-GUIA_IMPLEMENTACION_GTM_GA4.md).
