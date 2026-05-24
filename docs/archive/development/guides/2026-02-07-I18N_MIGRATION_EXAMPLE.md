# Ejemplo de Migración a i18n

Este documento muestra cómo migrar un componente existente para usar el sistema de traducciones.

## Componente Original (sin i18n)

```tsx
'use client';

export default function OrganizationDetailPage() {
  return (
    <div>
      <h1>Detalles de la Organización</h1>
      <p>Detalles y configuración de la organización</p>
      <button>Editar</button>
      <button>Volver</button>
    </div>
  );
}
```

## Componente Migrado (con i18n)

```tsx
'use client';

import { useTranslate } from '@/lib/translations';

export default function OrganizationDetailPage() {
  const t = useTranslate('organizations.detail');
  const tCommon = useTranslate('common');
  
  return (
    <div>
      <h1>{t('title')}</h1>
      <p>{t('description')}</p>
      <button>{t('edit')}</button>
      <button>{tCommon('back')}</button>
    </div>
  );
}
```

## Paso a Paso

### 1. Importar el hook

```tsx
import { useTranslate } from '@/lib/translations';
```

### 2. Crear instancia del traductor con namespace

```tsx
const t = useTranslate('organizations.detail'); // Para traducciones del módulo
const tCommon = useTranslate('common'); // Para traducciones comunes
```

### 3. Reemplazar textos hardcodeados

**Antes:**
```tsx
<h1>Información de la Organización</h1>
```

**Después:**
```tsx
<h1>{t('info.title')}</h1>
```

### 4. Usar parámetros cuando sea necesario

**Antes:**
```tsx
<p>5 usuarios en la organización</p>
```

**Después:**
```tsx
const t = useTranslate('organizations.detail.users');
<p>{t('count', { count: 5 })}</p>
```

Con pluralización:
```tsx
import { translatePlural } from '@/lib/translations';
<p>{translatePlural('organizations.detail.users.count', userCount, { count: userCount })}</p>
```

## Casos Especiales

### Mensajes de Toast/Notificaciones

**Antes:**
```tsx
toast({
  title: "Error",
  description: "Error al actualizar la organización",
});
```

**Después:**
```tsx
const t = useTranslate('organizations.detail.edit');
const tCommon = useTranslate('common');

toast({
  title: tCommon('error'),
  description: t('edit.error'),
});
```

### Textos en atributos

**Antes:**
```tsx
<Input placeholder="Nombre de la organización" />
```

**Después:**
```tsx
const t = useTranslate('organizations.detail.edit');
<Input placeholder={t('namePlaceholder')} />
```

### Formateo de fechas (mantener código)

Las fechas deben formatearse usando `toLocaleDateString`:

```tsx
new Date(organization.created_at).toLocaleDateString('es-ES', {
  year: 'numeric',
  month: 'long',
  day: 'numeric'
});
```

## Checklist de Migración

- [ ] Importar `useTranslate` o `translate`
- [ ] Identificar todos los textos hardcodeados en el componente
- [ ] Verificar que las claves existen en `messages/es.json` y `messages/en.json`
- [ ] Reemplazar textos estáticos con llamadas a traducción
- [ ] Manejar parámetros dinámicos si es necesario
- [ ] Probar que el componente funciona correctamente
- [ ] Verificar que los textos se muestran en español correctamente

## Beneficios de la Migración

1. **Preparado para multi-idioma**: Fácil agregar inglés más adelante
2. **Mantenimiento centralizado**: Todos los textos en un solo lugar
3. **Consistencia**: Mismos textos usados en múltiples lugares
4. **Fácil actualización**: Cambiar un texto en un lugar actualiza toda la app
