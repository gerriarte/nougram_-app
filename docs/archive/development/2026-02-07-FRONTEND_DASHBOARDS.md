# Guía de Dashboards Frontend

Esta guía explica cómo usar los nuevos dashboards implementados en el Sprint 17.

## Dashboard de Créditos

**Ruta:** `/credits`

**Acceso:** Disponible para todos los usuarios autenticados

### Características

- **Balance de Créditos**: Muestra créditos disponibles, usados este mes, total usados y próxima fecha de reseteo
- **Gráfico de Uso**: Visualización temporal del consumo de créditos
- **Historial de Transacciones**: Tabla completa con todas las transacciones de créditos
- **Filtros**: Filtro por tipo de transacción (subscripción, ajuste manual, consumo, reembolso)
- **Paginación**: Navegación por páginas del historial

### Uso

1. Accede desde el menú lateral "Créditos"
2. Visualiza tu balance actual en las tarjetas superiores
3. Revisa el gráfico de uso para ver tendencias
4. Explora el historial de transacciones con filtros y paginación

### Componentes Clave

- `CreditsBalanceCard`: Tarjetas con métricas de créditos
- `CreditsUsageChart`: Gráfico de línea temporal
- `CreditsHistoryTable`: Tabla de transacciones con filtros

## Dashboard Admin de Créditos

**Ruta:** `/admin/organizations/[id]/credits`

**Acceso:** Solo para `super_admin`

### Características

- **Gestión de Créditos**: Ver y gestionar créditos de cualquier organización
- **Otorgar Créditos Manualmente**: Diálogo para agregar créditos con razón
- **Forzar Reseteo Mensual**: Ejecutar reseteo mensual antes del tiempo programado
- **Historial Completo**: Ver todas las transacciones de la organización

### Uso

1. Desde `/settings/organizations`, haz clic en "Créditos" en la columna de acciones
2. Visualiza el balance de la organización
3. Usa "Otorgar Créditos Manualmente" para agregar créditos adicionales
4. Usa "Forzar Reseteo Mensual" si necesitas ejecutar un reseteo manualmente

### Acceso

- Solo usuarios con rol `super_admin` pueden acceder
- Se accede desde la página de organizaciones

## Dashboard de Soporte

**Ruta:** `/support`

**Acceso:** Roles: `super_admin`, `support_manager`, `data_analyst`

### Características

- **Lista de Organizaciones**: Vista completa de todas las organizaciones
- **Datos Anonimizados**: Para roles no super_admin, los datos sensibles están anonimizados
- **Métricas Agregadas**: Total de organizaciones, usuarios y distribución por plan
- **Filtros**: Por plan de suscripción, estado y búsqueda por nombre
- **Navegación a Detalles**: Enlace a vista detallada de cada organización

### Uso

1. Accede desde el menú lateral "Soporte" (solo visible para roles de soporte)
2. Visualiza métricas agregadas en las tarjetas superiores
3. Usa los filtros para encontrar organizaciones específicas
4. Haz clic en "Ver Detalles" para ver información detallada de una organización

### Anonimización

Para roles `support_manager` y `data_analyst`:
- Los salarios exactos se muestran como rangos
- Los costos se muestran como rangos
- Los montos de cotizaciones están anonimizados
- Los nombres de organizaciones pueden estar parcialmente ocultos

Para `super_admin`:
- Todos los datos se muestran sin anonimización

## Detalle de Organización (Soporte)

**Ruta:** `/support/organizations/[id]`

**Acceso:** Roles: `super_admin`, `support_manager`, `data_analyst`

### Características

- **Información Básica**: Nombre, slug, plan, estado
- **Métricas de Uso**: Usuarios, proyectos, cotizaciones, créditos
- **Pestañas**: Organización de información en pestañas (Uso, Detalles)
- **Datos Anonimizados**: Según el rol del usuario

### Uso

1. Desde el dashboard de soporte, haz clic en "Ver Detalles" de una organización
2. Revisa la información básica y métricas
3. Navega entre pestañas para ver diferentes tipos de información

## Badge de Créditos en Header

**Ubicación:** Header de la aplicación (parte superior derecha)

**Acceso:** Solo visible para usuarios con rol `product_manager` (que consumen créditos)

### Características

- **Balance en Tiempo Real**: Muestra créditos disponibles actualizados
- **Clickeable**: Al hacer clic, navega a `/credits`
- **Responsive**: Se adapta a pantallas pequeñas (oculta texto "créditos" en móvil)
- **Estados de Carga**: Muestra spinner mientras carga

### Comportamiento

- Solo se muestra para usuarios que consumen créditos (`product_manager`)
- Se oculta para `owner` y `admin_financiero`
- Se actualiza automáticamente cuando cambia el balance

## Mejoras UX Implementadas

### Loading States

- **Skeleton Loaders**: Componentes `LoadingSkeleton` para diferentes tipos de contenido
- **Spinners Consistentes**: Uso de `Loader2` de lucide-react de forma consistente
- **Estados de Carga por Sección**: Cada sección muestra su propio estado de carga

### Error Handling

- **ErrorDisplay Component**: Componente reutilizable para mostrar errores
- **Retry Automático**: Botones de reintento en mensajes de error
- **ErrorBoundary**: Captura de errores a nivel de aplicación
- **Mensajes Claros**: Mensajes de error descriptivos y accionables

### Responsive Design

- **Grids Adaptativos**: Uso de `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4` para adaptación
- **Tablas con Scroll**: Tablas envueltas en `overflow-x-auto` para móvil
- **Paginación Responsive**: Layout flexible para botones de paginación
- **Filtros Apilados**: Filtros se apilan verticalmente en móvil

### Accesibilidad

- **Labels ARIA**: Agregados `aria-label` y `aria-hidden` donde corresponde
- **Roles Semánticos**: Uso de `role="main"` en contenido principal
- **Navegación por Teclado**: Todos los botones y enlaces son accesibles por teclado
- **Contraste Mejorado**: Colores con suficiente contraste para legibilidad

## Componentes Reutilizables

### LoadingSkeleton

```tsx
<LoadingSkeleton type="card" count={4} />
<LoadingSkeleton type="table" count={5} />
<LoadingSkeleton type="list" count={3} />
<LoadingSkeleton type="chart" />
```

### ErrorDisplay

```tsx
<ErrorDisplay
  error={error}
  onRetry={() => refetch()}
  title="Error al cargar datos"
  description="Descripción opcional del error"
/>
```

### ErrorBoundary

```tsx
<ErrorBoundary>
  <YourComponent />
</ErrorBoundary>
```

## Integración con Backend

Todos los dashboards usan hooks de React Query definidos en `frontend/src/lib/queries.ts`:

- `useGetMyCreditBalance()`: Balance de créditos del usuario
- `useGetMyCreditHistory()`: Historial de transacciones
- `useGetAdminCreditBalance()`: Balance de créditos (admin)
- `useGetAdminCreditHistory()`: Historial de transacciones (admin)
- `useGetSupportOrganizations()`: Lista de organizaciones (soporte)
- `useGetSupportOrganization()`: Detalle de organización (soporte)
- `useGetSupportOrganizationUsage()`: Métricas de uso (soporte)

## Permisos y Seguridad

- Los dashboards verifican permisos antes de mostrar contenido
- Los endpoints del backend validan roles y permisos
- Los datos anonimizados se aplican automáticamente según el rol
- Los errores de permisos se muestran claramente al usuario

## Troubleshooting

### No se muestra el badge de créditos

- Verifica que tu rol sea `product_manager`
- Verifica que la organización tenga créditos configurados
- Revisa la consola del navegador para errores

### Error al cargar datos

- Verifica la conexión a la API
- Revisa los logs del backend
- Usa el botón "Reintentar" en el mensaje de error

### Datos no se actualizan

- Los datos se actualizan automáticamente con React Query
- Puedes forzar actualización con `refetch()`
- Verifica que no haya errores en la consola




