# Solución al Problema de Parpadeo

## Fecha: 2026-02-14

## Problema Identificado

La aplicación estaba parpadeando constantemente debido a:

1. **Loop de navegación infinito**: El componente `page.tsx` tenía un `useEffect` que redirigía entre `/` y `/dashboard` constantemente
2. **Re-renders infinitos**: El cálculo de BCR en `NougramCoreContext` se ejecutaba repetidamente debido a comparaciones de punto flotante
3. **Error de Tailwind CSS**: Next.js estaba buscando módulos en el directorio raíz incorrecto

## Correcciones Aplicadas

### 1. Fix del Loop de Navegación (`frontend/src/app/page.tsx`)

**Antes:**
```typescript
useEffect(() => {
  if (!state.isHydrated) return;
  if (state.financials.bcr === 0) {
    router.push('/onboarding');
  } else {
    router.replace('/dashboard');
  }
}, [state.isHydrated, state.financials.bcr, router]);
```

**Después:**
```typescript
const hasNavigated = useRef(false);
const pathname = usePathname();

useEffect(() => {
  if (!state.isHydrated) return;
  if (hasNavigated.current) return; // Prevenir múltiples navegaciones
  
  if (state.financials.bcr === 0) {
    if (pathname !== '/onboarding') {
      hasNavigated.current = true;
      router.push('/onboarding');
    }
  } else {
    if (pathname !== '/dashboard' && pathname !== '/onboarding') {
      hasNavigated.current = true;
      router.replace('/dashboard');
    }
  }
}, [state.isHydrated, state.financials.bcr, pathname, router]);
```

**Cambios:**
- Agregado `useRef` para prevenir múltiples navegaciones
- Agregado `usePathname` para verificar la ruta actual antes de navegar
- Verificación de ruta antes de navegar para evitar loops

### 2. Fix del Re-render Infinito (`frontend/src/context/NougramCoreContext.tsx`)

**Antes:**
```typescript
if (state.financials.bcr !== newBCR || state.financials.equipmentAmortization !== totalAmortization) {
  setState(...);
}
```

**Después:**
```typescript
const bcrChanged = Math.abs(state.financials.bcr - newBCR) > 0.01;
const amortizationChanged = Math.abs(state.financials.equipmentAmortization - totalAmortization) > 0.01;

if (bcrChanged || amortizationChanged) {
  setState(...);
}
```

**Cambios:**
- Uso de tolerancia para comparaciones de punto flotante (0.01)
- Evita actualizaciones innecesarias por diferencias mínimas

### 3. Configuración de Next.js (`frontend/next.config.ts`)

- Eliminada configuración inválida de `turbopack`
- Simplificada la configuración experimental
- Mantenidas las optimizaciones necesarias

## Estado Actual

✅ **Loop de navegación**: Resuelto
✅ **Re-renders infinitos**: Resuelto  
✅ **Configuración Next.js**: Corregida

## Verificación

La aplicación debería:
- Cargar sin parpadeos
- Navegar correctamente según el estado del BCR
- No recargar constantemente

## Si el Problema Persiste

1. **Limpiar caché del navegador**: Ctrl+Shift+R o Ctrl+F5
2. **Verificar consola del navegador**: F12 > Console para ver errores
3. **Verificar logs del frontend**: Revisar terminal donde corre `npm run dev`
4. **Reiniciar servicios**: Detener y volver a iniciar frontend y backend
