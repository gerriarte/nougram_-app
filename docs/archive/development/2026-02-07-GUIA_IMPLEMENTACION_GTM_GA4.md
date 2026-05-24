# Guía de implementación – GTM y GA4 (Nougram)

**Fecha:** 2026-02-07  
**Requisito:** Haber leído el [Plan de Tagging](./2026-02-07-PLAN_TAGGING_GTM_GA4.md).

Esta guía describe los pasos para implementar Google Tag Manager (GTM) y Google Analytics 4 (GA4) en el frontend Nougram, incluyendo identificación de usuarios, navegación y eventos de propuestas.

---

## 1. Requisitos previos

- Cuenta en [Google Analytics](https://analytics.google.com/) y [Google Tag Manager](https://tagmanager.google.com/).
- Propiedad **GA4** creada y **Measurement ID** (formato `G-XXXXXXXXXX`).
- Contenedor **GTM** creado para web y **ID de contenedor** (formato `GTM-XXXXXXX`).

---

## 2. Variables de entorno

Añadir en el frontend (por ejemplo en `.env.local` y en el entorno de producción) las siguientes variables. **No** hardcodear los IDs en el código.

```env
# Google Tag Manager - ID del contenedor (ej. GTM-XXXXXXX)
NEXT_PUBLIC_GTM_ID=GTM-XXXXXXX

# Opcional: GA4 Measurement ID (si se usa también gtag directo; con GTM suele no ser necesario en el código)
# NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

Solo `NEXT_PUBLIC_GTM_ID` es obligatorio para cargar GTM; GA4 se configura dentro de GTM usando el Measurement ID.

---

## 3. Cargar GTM en el layout

Objetivo: inyectar el script de GTM en todas las páginas y inicializar `dataLayer` antes de cualquier tag.

**Archivo:** `nougram_front/src/app/layout.tsx`

1. Declarar `dataLayer` y el script de GTM en el `<head>` (o justo después de `<body>` según la plantilla recomendada por GTM).
2. Usar la variable de entorno `NEXT_PUBLIC_GTM_ID`; si está vacía, no inyectar el script (para entornos locales sin GTM).

Ejemplo de estructura (Next.js App Router):

```tsx
// En layout.tsx, dentro de <html>:
<head>
  {/* dataLayer debe existir antes del script de GTM */}
  <script
    dangerouslySetInnerHTML={{
      __html: `
        window.dataLayer = window.dataLayer || [];
      `,
    }}
  />
</head>
<body>
  {/* Fragmento de GTM (noscript) suele ir justo después de <body> */}
  {process.env.NEXT_PUBLIC_GTM_ID && (
    <noscript>
      <iframe
        src={`https://www.googletagmanager.com/ns.html?id=${process.env.NEXT_PUBLIC_GTM_ID}`}
        height="0"
        width="0"
        style={{ display: 'none', visibility: 'hidden' }}
      />
    </noscript>
  )}
  <NougramCoreProvider>
    {children}
  </NougramCoreProvider>
</body>
```

Para el **script asíncrono de GTM** (que va en `<head>`), se puede usar el componente `Script` de `next/script` con `strategy="afterInteractive"` y la URL:

`https://www.googletagmanager.com/gtag/js?id=${NEXT_PUBLIC_GTM_ID}`

En realidad GTM se carga con un fragmento de dos partes (script + noscript). El fragmento oficial que proporciona GTM al crear el contenedor debe colocarse tal cual; la única sustitución es el ID por `process.env.NEXT_PUBLIC_GTM_ID`. Se puede crear un componente cliente `GoogleTagManager.tsx` que lea `NEXT_PUBLIC_GTM_ID` y renderice el fragmento para mantener el layout en servidor.

---

## 4. Componente de GTM (recomendado)

Crear un componente que inyecte el fragmento de GTM y que solo se renderice en cliente con el ID desde env.

**Archivo sugerido:** `nougram_front/src/components/analytics/GoogleTagManager.tsx`

- Leer `process.env.NEXT_PUBLIC_GTM_ID`.
- Si no hay ID, no renderizar nada.
- Insertar el primer fragmento de GTM (script que define `dataLayer` y carga `gtm.js`) en un `<Script>` de Next o con `dangerouslySetInnerHTML` según convenga.
- El noscript puede ir en el mismo componente o en el layout.

Incluir este componente en el layout raíz (dentro de `<body>`).

Documentación oficial del fragmento: [GTM - Instalación web](https://developers.google.com/tag-platform/tag-manager/web).

---

## 5. Enviar identificación de usuario

Cuando el usuario esté logueado, enviar un único evento de identificación por sesión para que GTM/GA4 asocie los eventos al User ID.

**Dónde:** Donde se tenga acceso al usuario actual, por ejemplo:

- Un componente de layout que envuelva las rutas protegidas (por ejemplo el que usa `AdminLayout` o el provider de auth), o
- Un efecto en un componente raíz que use `useAuth()` y, cuando `user` esté disponible, haga el `push`.

Ejemplo de lógica (en un componente cliente con `useAuth()`):

```ts
const { user } = useAuth();

useEffect(() => {
  if (!user?.id || typeof window === 'undefined' || !window.dataLayer) return;
  window.dataLayer.push({
    event: 'user_identify',
    user_id: String(user.id),
    user_role: user.role ?? undefined,
    // organization_id: orgId si está disponible
  });
}, [user?.id, user?.role]);
```

Evitar múltiples pushes del mismo usuario en la misma sesión (por ejemplo guardando en sessionStorage que ya se envió `user_identify` para ese `user.id`).

---

## 6. Navegación (page_view)

En Next.js App Router las transiciones son client-side; hay que disparar `page_view` al cambiar de ruta.

**Dónde:** Un componente cliente que use `usePathname()` de `next/navigation` y que esté montado en el árbol de layout (por ejemplo dentro de `AdminLayout` o del layout raíz).

Ejemplo:

```ts
'use client';
import { usePathname } from 'next/navigation';
import { useEffect } from 'react';

export function PageViewTracker() {
  const pathname = usePathname();

  useEffect(() => {
    if (typeof window === 'undefined' || !window.dataLayer) return;
    window.dataLayer.push({
      event: 'page_view',
      page_path: pathname ?? window.location.pathname,
      page_title: document.title || '',
    });
  }, [pathname]);

  return null;
}
```

Incluir `<PageViewTracker />` en el layout o en un layout de dashboard para que todas las rutas lo tengan.

---

## 7. Eventos de propuestas

### 7.1 Propuesta creada

**Dónde:** Donde se llame a `quoteService.create()` y se reciba la respuesta con `project_id`.  
En el código actual, `quoteService.create()` devuelve el `project_id` (como string). Tras una creación exitosa, obtener los totales de la cotización recién creada (por ejemplo con `quoteService.getByProjectId(projectId)` o desde el estado del formulario) y hacer:

```ts
if (window.dataLayer) {
  window.dataLayer.push({
    event: 'propuesta_creada',
    project_id: projectId,
    status: 'Draft',
    total_client_price: totalClientPrice,   // número
    total_internal_cost: totalInternalCost, // opcional
    currency: currency ?? 'USD',
    margin_percentage: marginPercent,       // opcional
    user_id: user?.id ? String(user.id) : undefined,
    organization_id: organizationId ?? undefined,
  });
}
```

Colocar este bloque justo después de que `quoteService.create()` resuelva y se tengan los datos (totales pueden venir del estado del builder o de un get posterior).

### 7.2 Cambio de estado de propuesta

**Dónde:** Donde se llame a `quoteService.updateStatus()` o `quoteService.setProjectStatus()` y la llamada sea exitosa.

Ejemplo tras `setProjectStatus(projectId, newStatus)`:

```ts
if (window.dataLayer) {
  window.dataLayer.push({
    event: 'propuesta_estado_cambiado',
    project_id: projectId,
    old_status: previousStatus,  // Draft | Sent | Won | Lost
    new_status: newStatus,
    total_client_price: totalClientPrice, // opcional
    currency: currency ?? 'USD',
    user_id: user?.id ? String(user.id) : undefined,
    organization_id: organizationId ?? undefined,
  });
}
```

Asegurarse de tener `previousStatus` antes de actualizar (del estado local o de la respuesta del listado/detalle).

---

## 8. Tipado de `dataLayer` (TypeScript)

Para evitar errores y tener autocompletado, se puede declarar la interfaz del dataLayer:

**Archivo sugerido:** `nougram_front/src/types/gtm.d.ts`

```ts
export interface DataLayerEventMap {
  user_identify: {
    event: 'user_identify';
    user_id: string;
    organization_id?: string;
    user_role?: string;
  };
  page_view: {
    event: 'page_view';
    page_path: string;
    page_title?: string;
  };
  propuesta_creada: {
    event: 'propuesta_creada';
    project_id: string;
    status: string;
    total_client_price?: number;
    total_internal_cost?: number;
    currency?: string;
    margin_percentage?: number;
    user_id?: string;
    organization_id?: string;
  };
  propuesta_estado_cambiado: {
    event: 'propuesta_estado_cambiado';
    project_id: string;
    old_status: string;
    new_status: string;
    total_client_price?: number;
    currency?: string;
    user_id?: string;
    organization_id?: string;
  };
}

declare global {
  interface Window {
    dataLayer: Array<Record<string, unknown>>;
  }
}
```

Así se puede tipar cada `push` según el evento.

---

## 9. Configuración en Google Tag Manager

### 9.1 Variables

Crear variables de tipo **Capa de datos (Data Layer)** para leer los parámetros enviados desde el sitio:

| Nombre sugerido | Variable Data Layer | Nombre del dato |
|-----------------|---------------------|------------------|
| DLV - User ID | Capa de datos | `user_id` |
| DLV - Event | Capa de datos | `event` |
| DLV - Page Path | Capa de datos | `page_path` |
| DLV - Project ID | Capa de datos | `project_id` |
| DLV - New Status | Capa de datos | `new_status` |
| DLV - Total Client Price | Capa de datos | `total_client_price` |
| (Otras según necesidad) | Capa de datos | mismo nombre del parámetro |

Para User ID en GA4, usar la variable que lee `user_id` de la capa de datos (puede ser la misma para el evento `user_identify` y para el tag de GA4 si se configura User ID en cada disparo).

### 9.2 Triggers

| Nombre | Tipo | Configuración |
|--------|------|----------------|
| T - user_identify | Evento personalizado | Nombre del evento: `user_identify` |
| T - page_view | Evento personalizado | Nombre del evento: `page_view` |
| T - propuesta_creada | Evento personalizado | Nombre del evento: `propuesta_creada` |
| T - propuesta_estado_cambiado | Evento personalizado | Nombre del evento: `propuesta_estado_cambiado` |
| T - All GA4 Events | Evento personalizado | Nombre del evento: coincide con expresión regular `.*` o listar cada evento |

### 9.3 Tag de GA4

- **Tipo:** Google Analytics: GA4 Configuration + GA4 Event.
- **Measurement ID:** El de la propiedad GA4 (G-XXXXXXXXXX).
- **User ID:** Variable que lee `user_id` de la capa de datos (opcional pero recomendado).
- **Disparo:** 
  - Opción A: Un tag de configuración GA4 que se dispare en “All Pages” (o en un evento inicial) y tags de evento GA4 que se disparen con los triggers de cada evento (`user_identify`, `page_view`, `propuesta_creada`, etc.), enviando los mismos parámetros que llegan en el dataLayer.
  - Opción B: Un solo tag GA4 Event que se dispare con el trigger “All GA4 Events” y use la variable DLV - Event como nombre de evento y el resto de variables de dataLayer como parámetros del evento.

En GA4, en “Definir eventos personalizados” no es obligatorio crear los eventos por adelantado; al recibir el evento con parámetros, GA4 los registrará. Sí conviene crear **dimensiones personalizadas** (o parámetros de evento) para `project_id`, `old_status`, `new_status`, `total_client_price`, `currency`, `organization_id`, etc., si se quieren usar en informes.

---

## 10. Comprobaciones

1. **Sin GTM en local:** Con `NEXT_PUBLIC_GTM_ID` vacío, la app no debe cargar GTM ni mostrar errores.
2. **dataLayer:** En la consola del navegador, `window.dataLayer` debe existir y contener los objetos enviados con `push`.
3. **GTM Preview:** Usar la vista previa de GTM para comprobar que los eventos se disparan y que el tag de GA4 se activa.
4. **GA4 DebugView:** En GA4, activar “Modo depuración” (o usar el parámetro `debug_mode=true`) y comprobar en Tiempo real / Depuración que lleguen `user_identify`, `page_view`, `propuesta_creada` y `propuesta_estado_cambiado` con los parámetros esperados.
5. **User ID:** En GA4, comprobar que los eventos tengan User ID cuando el usuario esté logueado (en las propiedades del evento en DebugView o en informes con dimensión User ID).

---

## 11. Resumen de archivos a tocar

| Archivo / recurso | Cambio |
|-------------------|--------|
| `.env.example` o documentación | Documentar `NEXT_PUBLIC_GTM_ID`. |
| `nougram_front/src/app/layout.tsx` | Inicializar `dataLayer` e incluir componente/script de GTM (y noscript). |
| `nougram_front/src/components/analytics/GoogleTagManager.tsx` | Nuevo: inyección del fragmento GTM. |
| `nougram_front/src/components/analytics/PageViewTracker.tsx` | Nuevo: envío de `page_view` en cada cambio de ruta. |
| Componente/layout con auth | Efecto que envía `user_identify` cuando hay usuario. |
| Llamada a `quoteService.create()` | Tras éxito, `dataLayer.push` de `propuesta_creada`. |
| Llamada a `quoteService.setProjectStatus` / `updateStatus` | Tras éxito, `dataLayer.push` de `propuesta_estado_cambiado`. |
| `nougram_front/src/types/gtm.d.ts` | Nuevo: tipado de `dataLayer` y `Window`. |
| GTM (interfaz web) | Variables, triggers y tag GA4 según secciones 9.1–9.3. |
| GA4 (interfaz web) | Parámetros/dimensiones personalizadas y User ID. |

---

## 12. Referencias

- [GTM - Instalación web](https://developers.google.com/tag-platform/tag-manager/web)
- [GA4 - Configurar User ID](https://support.google.com/analytics/answer/9213390)
- [GA4 - Eventos personalizados](https://support.google.com/analytics/answer/9322688)
- Plan de tagging: [2026-02-07-PLAN_TAGGING_GTM_GA4.md](./2026-02-07-PLAN_TAGGING_GTM_GA4.md)
