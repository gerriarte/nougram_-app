# 💱 Configuración de Moneda Primaria

**Objetivo:** Unificar la moneda seleccionada en el onboarding como moneda principal de la herramienta, usándola en todos los formularios y permitiendo cambiarla solo desde Settings > Currency.

---

## 📋 Cambios Implementados

### 1. Hook para Moneda Primaria

**Archivo:** `frontend/src/hooks/usePrimaryCurrency.ts`

Hook creado para obtener la moneda primaria de la organización:

```typescript
export function usePrimaryCurrency(): string {
  const { data } = useGetCurrencySettings(false)
  return data?.primary_currency || 'USD'
}
```

**Uso:**
```typescript
import { usePrimaryCurrency } from '@/hooks/usePrimaryCurrency'

const primaryCurrency = usePrimaryCurrency()
```

---

### 2. Onboarding Guarda Moneda como Primary Currency

**Archivo:** `frontend/src/app/(app)/onboarding/page.tsx`

**Cambio:**
- El onboarding ahora guarda la moneda seleccionada usando el endpoint `/settings/currency`
- Esto asegura que la moneda se guarde como `primary_currency` en los settings de la organización
- El template también guarda `primary_currency` automáticamente

**Código:**
```typescript
// 1b. Update primary currency via currency settings endpoint
await updateCurrencySettings.mutateAsync({
  primary_currency: currency || 'USD'
});
```

---

### 3. Formularios Usan Moneda Primaria por Defecto

#### A. Formulario de Nuevo Proyecto

**Archivo:** `frontend/src/app/(app)/projects/new/page.tsx`

**Cambio:**
- El selector de moneda se inicializa con la moneda primaria
- El usuario puede cambiar la moneda del proyecto si lo necesita
- Si la moneda primaria cambia, se actualiza automáticamente (solo si no se ha modificado manualmente)

**Código:**
```typescript
const primaryCurrency = usePrimaryCurrency()
const [currency, setCurrency] = useState(primaryCurrency)

useEffect(() => {
  if (currency === primaryCurrency || !currency) {
    setCurrency(primaryCurrency)
  }
}, [primaryCurrency])
```

#### B. Formulario de Edición de Proyecto

**Archivo:** `frontend/src/app/(app)/projects/[id]/edit/page.tsx`

**Cambio:**
- Usa la moneda del proyecto si existe
- Si no existe, usa la moneda primaria como fallback

**Código:**
```typescript
const primaryCurrency = usePrimaryCurrency()
const [currency, setCurrency] = useState(primaryCurrency)

useEffect(() => {
  if (project) {
    setCurrency(project.currency || primaryCurrency)
  }
}, [project, primaryCurrency])
```

#### C. Formulario de Costos Fijos

**Archivo:** `frontend/src/components/costs/cost-form.tsx`

**Cambio:**
- El selector de moneda se inicializa con la moneda primaria
- Solo se actualiza si es un nuevo costo (no al editar)

**Código:**
```typescript
const primaryCurrency = usePrimaryCurrency()

defaultValues: defaultValues || {
  currency: primaryCurrency, // Usar moneda primaria por defecto
  // ...
}

useEffect(() => {
  if (!defaultValues && mode === "create") {
    setValue("currency", primaryCurrency)
  }
}, [primaryCurrency, defaultValues, mode, setValue])
```

#### D. Formulario de Miembros del Equipo

**Archivo:** `frontend/src/components/team/team-member-form.tsx`

**Cambio:**
- El selector de moneda se inicializa con la moneda primaria
- Solo se actualiza si es un nuevo miembro (no al editar)

**Código:**
```typescript
const primaryCurrency = usePrimaryCurrency()

defaultValues: defaultValues || {
  currency: primaryCurrency, // Usar moneda primaria por defecto
  // ...
}

useEffect(() => {
  if (!defaultValues && mode === "create") {
    setValue("currency", primaryCurrency)
  }
}, [primaryCurrency, defaultValues, mode, setValue])
```

---

## 🔄 Flujo de Moneda

### 1. Onboarding
1. Usuario selecciona moneda en el paso 1 del onboarding
2. Al finalizar, se guarda como `primary_currency` usando `/settings/currency`
3. El template también guarda `primary_currency` en los settings de la organización

### 2. Uso en Formularios
1. Todos los formularios obtienen la moneda primaria usando `usePrimaryCurrency()`
2. Los selectores de moneda se inicializan con la moneda primaria
3. El usuario puede cambiar la moneda en proyectos específicos si lo necesita
4. Los costos y miembros del equipo usan la moneda primaria por defecto

### 3. Cambio de Moneda
1. Solo se puede cambiar desde **Settings > Currency**
2. Al cambiar, se actualiza `primary_currency` en los settings de la organización
3. Los formularios se actualizan automáticamente para usar la nueva moneda primaria

---

## 📊 Backend

### Endpoints Relevantes

1. **GET `/settings/currency`**
   - Obtiene la configuración de moneda
   - Retorna `primary_currency` desde los settings de la organización

2. **PUT `/settings/currency`**
   - Actualiza la moneda primaria
   - Guarda en `organization.settings['primary_currency']`

3. **POST `/templates/organizations/{id}/apply-template`**
   - Aplica template y guarda `primary_currency` en los settings

---

## ✅ Beneficios

1. **Consistencia:** Todos los formularios usan la misma moneda por defecto
2. **Simplicidad:** El usuario solo selecciona la moneda una vez (en onboarding)
3. **Flexibilidad:** Se puede cambiar la moneda de proyectos específicos si es necesario
4. **Centralización:** Solo se puede cambiar la moneda principal desde un lugar (Settings)

---

## 🎯 Próximos Pasos

1. ✅ Onboarding guarda moneda como `primary_currency`
2. ✅ Formularios usan moneda primaria por defecto
3. ✅ Hook `usePrimaryCurrency()` disponible
4. ⏳ Verificar que todos los formularios estén usando el hook
5. ⏳ Probar el flujo completo de onboarding y creación de proyectos

---

**Última actualización:** 30 de Diciembre, 2025

