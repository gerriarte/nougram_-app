# Configuración de Internacionalización (i18n)

## Estado Actual

El frontend está configurado para usar **Español** como idioma por defecto, pero está preparado para agregar **Inglés** en el futuro.

## Arquitectura

- **Librería**: `next-intl` (instalada)
- **Idioma por defecto**: Español (`es`)
- **Idiomas disponibles**: Español (`es`), Inglés (`en`)

## Estructura de Archivos

```
frontend/src/
├── i18n/
│   ├── config.ts          # Configuración de locales
│   ├── request.ts         # Configuración para next-intl (App Router)
│   └── client.ts          # Utilidades para client components
├── messages/
│   ├── es.json            # Traducciones en español
│   └── en.json            # Traducciones en inglés
└── lib/
    └── translations.ts    # Utilidades simples de traducción
```

## Cómo Usar Traducciones

### Opción 1: Hook `useTranslate` (Recomendado para migración gradual)

Para componentes client-side, usa el hook `useTranslate`:

```tsx
'use client';

import { useTranslate } from '@/lib/translations';

export default function MyComponent() {
  const t = useTranslate('organizations.detail');
  
  return (
    <div>
      <h1>{t('title')}</h1>
      <p>{t('description')}</p>
      <button>{t('edit')}</button>
    </div>
  );
}
```

### Opción 2: Función `translate` directa

Para casos simples:

```tsx
import { translate } from '@/lib/translations';

const message = translate('common.save');
const withParams = translate('organizations.detail.users.count', { count: 5 });
```

### Opción 3: next-intl (Para uso completo en el futuro)

Cuando el proyecto esté completamente migrado a next-intl:

```tsx
'use client';

import { useTranslations } from 'next-intl';

export default function MyComponent() {
  const t = useTranslations('organizations.detail');
  
  return <h1>{t('title')}</h1>;
}
```

## Estructura de Claves de Traducción

Las claves están organizadas por namespace:

```json
{
  "common": { ... },           // Textos comunes (save, cancel, etc.)
  "errors": { ... },           // Mensajes de error
  "organizations": {
    "detail": {
      "title": "...",
      "users": { ... },
      "stats": { ... }
    }
  }
}
```

## Migración de Componentes

### Antes (texto hardcodeado):

```tsx
<Button>Guardar</Button>
<h1>Información de la Organización</h1>
```

### Después (con traducciones):

```tsx
const t = useTranslate('organizations.detail');

<Button>{t('edit.save')}</Button>
<h1>{t('info.title')}</h1>
```

### Con parámetros:

```tsx
const t = useTranslate('organizations.detail.users');

<p>{t('count', { count: userCount })}</p>
// Resultado: "5 usuarios en la organización"
```

## Agregar Nuevas Traducciones

1. **Agregar clave en `messages/es.json`**:

```json
{
  "myFeature": {
    "title": "Mi Nueva Funcionalidad",
    "description": "Descripción de la funcionalidad"
  }
}
```

2. **Agregar traducción en inglés en `messages/en.json`**:

```json
{
  "myFeature": {
    "title": "My New Feature",
    "description": "Feature description"
  }
}
```

3. **Usar en el componente**:

```tsx
const t = useTranslate('myFeature');
<h1>{t('title')}</h1>
```

## Fechas y Números

Para formatear fechas y números según el locale, usa las funciones nativas de JavaScript:

```tsx
// Fechas
new Date().toLocaleDateString('es-ES', {
  year: 'numeric',
  month: 'long',
  day: 'numeric'
});

// Números
(1234.56).toLocaleString('es-ES', {
  style: 'currency',
  currency: 'USD'
});
```

## Mejores Prácticas

1. **No hardcodear textos**: Siempre usar claves de traducción
2. **Namespace organizados**: Agrupar traducciones por feature/módulo
3. **Nombres descriptivos**: Usar nombres claros para las claves
4. **Mantener consistencia**: Usar las mismas claves para textos similares
5. **Agregar inglés**: Siempre agregar la traducción en inglés cuando se agregue español

## Estado de Migración

- ✅ Sistema de i18n configurado
- ✅ Archivos de traducción creados (es, en)
- ✅ Utilidades de traducción implementadas
- ✅ Documentación completa
- ⏳ Migración gradual de componentes (puede hacerse cuando sea necesario)
- ❌ Cambio de idioma en UI (futuro - cuando se necesite)
- ❌ Routing con [locale] (futuro - opcional, no requerido)

## Próximos Pasos

1. **Migrar componentes gradualmente** a usar traducciones
2. **Agregar selector de idioma** en la UI (cuando sea necesario)
3. **Configurar routing con [locale]** si se necesita soporte multi-idioma completo
4. **Expandir traducciones** conforme se añaden nuevas features

## Ejemplo Completo

```tsx
'use client';

import { useTranslate } from '@/lib/translations';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function OrganizationDetail() {
  const t = useTranslate('organizations.detail');
  const tCommon = useTranslate('common');
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('info.title')}</CardTitle>
      </CardHeader>
      <CardContent>
        <Button>{tCommon('save')}</Button>
        <Button variant="outline">{tCommon('cancel')}</Button>
      </CardContent>
    </Card>
  );
}
```

## Notas Importantes

- Actualmente todo está en español por defecto
- El sistema está preparado para agregar inglés sin cambios estructurales
- Se puede migrar gradualmente sin romper funcionalidad existente
- Las traducciones están centralizadas en `messages/` para fácil mantenimiento
