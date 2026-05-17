# Solución al Parpadeo - Versión 3 (Final)

## Problema Identificado

El parpadeo persistía debido a un loop infinito de navegación entre `/` y `/dashboard`. El componente `page.tsx` se ejecutaba repetidamente cada vez que había una navegación.

## Causas Raíz

1. **Re-renders constantes**: El `useEffect` en `page.tsx` se ejecutaba cada vez que el componente se montaba, incluso después de navegar a `/dashboard`.

2. **Dependencias del useEffect**: Incluir `state.financials.bcr` en las dependencias causaba que el efecto se ejecutara cada vez que el BCR cambiaba (incluso por mínimas diferencias de punto flotante).

3. **Falta de protección global**: No había un mecanismo global para prevenir múltiples redirecciones simultáneas.

## Soluciones Implementadas

### 1. Componente `RootRedirect` Separado

- **Cambio**: Movida la lógica de redirección a un componente separado `RootRedirect.tsx` que se incluye en el `layout.tsx`.
- **Razón**: Separar la lógica de redirección del componente de página evita que se ejecute cada vez que el componente se monta.
- **Implementación**: 
  ```typescript
  // Componente que no renderiza nada (return null)
  // Usa window.location.href para redirección hard que evita re-renders
  // Flag global con timestamp para prevenir ejecuciones múltiples
  ```

### 2. Simplificación de `page.tsx`

- **Cambio**: Eliminada toda la lógica de redirección de `page.tsx`. Ahora solo muestra un loading.
- **Razón**: La redirección se maneja completamente en `RootRedirect`, evitando conflictos.

### 3. Optimización del BCR Recalculation

- **Cambio**: Removidas `state.financials.bcr` y `state.financials.equipmentAmortization` de las dependencias del `useEffect` en `NougramCoreContext`.
- **Razón**: Incluir estos valores en las dependencias causaba que el efecto se ejecutara cada vez que se actualizaban, creando un ciclo.
- **Implementación**: Solo dependencias de los valores que realmente afectan el cálculo: `baseMonthlyCost`, `billableHours`, y `equipment.length`.

### 4. Flag Global con Timestamp

- **Cambio**: Agregado un flag global `redirectLock` con timestamp para prevenir ejecuciones múltiples.
- **Razón**: El timestamp permite resetear el flag después de un tiempo, permitiendo redirecciones futuras si es necesario.
- **Implementación**:
  ```typescript
  const redirectLock = { 
    executed: false,
    timestamp: 0
  };
  
  // Verifica tiempo desde última ejecución
  const timeSinceLastRedirect = Date.now() - redirectLock.timestamp;
  if (redirectLock.executed && timeSinceLastRedirect < 2000) return;
  ```

### 5. Redirección Hard con `window.location.href`

- **Cambio**: Usar `window.location.href` en lugar de `router.replace()`.
- **Razón**: `window.location.href` hace una redirección completa del navegador que no causa re-renders de React, evitando loops.
- **Implementación**:
  ```typescript
  window.location.href = targetPath; // Hard redirect, no re-renders
  ```

## Archivos Modificados

1. **`frontend/src/components/RootRedirect.tsx`** (NUEVO)
   - Componente dedicado para manejar redirecciones desde root
   - Usa `window.location.href` para redirección hard
   - Flag global con timestamp para prevenir loops

2. **`frontend/src/app/layout.tsx`**
   - Agregado `<RootRedirect />` al layout
   - Se ejecuta una vez por carga de página

3. **`frontend/src/app/page.tsx`**
   - Simplificado completamente - solo muestra loading
   - Eliminada toda lógica de redirección

4. **`frontend/src/context/NougramCoreContext.tsx`**
   - Optimizadas las dependencias del `useEffect` de recálculo de BCR
   - Removidas dependencias circulares (`bcr` y `equipmentAmortization`)

## Verificación

Para verificar que el problema está resuelto:

1. Abre la aplicación en `http://localhost:3000`
2. Observa los logs del servidor Next.js
3. Deberías ver solo una redirección inicial, no un loop constante
4. La aplicación debería cargar sin parpadeos

## Notas Adicionales

- **`window.location.href` vs `router.replace()`**: La diferencia clave es que `window.location.href` hace una redirección completa del navegador, recargando la página completamente. Esto evita que React intente re-renderizar componentes, eliminando el loop.

- **Flag con timestamp**: El uso de un timestamp permite que el flag se resetee después de 2 segundos, permitiendo redirecciones futuras si el usuario navega manualmente de vuelta a `/`.

- **Componente separado**: Al separar la lógica de redirección en un componente dedicado en el layout, evitamos que se ejecute cada vez que `page.tsx` se monta o desmonta.

- **React Strict Mode**: En desarrollo, React monta componentes dos veces. El flag global con timestamp previene que esto cause problemas.

## Si el Problema Persiste

Si después de estos cambios el parpadeo continúa, verifica:

1. **Caché del navegador**: Limpia la caché completamente (Ctrl+Shift+Delete)
2. **React DevTools**: Verifica si hay componentes re-renderizando constantemente
3. **Console del navegador**: Busca errores o warnings que puedan estar causando re-renders
4. **Network tab**: Verifica si hay requests repetitivos a la API que puedan estar causando actualizaciones de estado
