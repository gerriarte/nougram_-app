# Guía para Probar el Frontend

## Servidor de Desarrollo

El servidor de desarrollo de Next.js debería estar iniciándose automáticamente. Si no está corriendo, ejecuta:

```bash
cd frontend
npm run dev
```

El frontend estará disponible en: **http://localhost:3000**

## Requisitos Previos

### 1. Backend corriendo

El backend debe estar activo en `http://localhost:5000`. Para iniciarlo:

```bash
cd backend
python -m uvicorn main:app --reload --port 5000
```

Verifica que esté funcionando visitando: `http://localhost:5000/docs`

### 2. Base de datos PostgreSQL

Asegúrate de que PostgreSQL esté corriendo:

```bash
docker-compose up -d
```

## Flujo de Prueba

### 1. Página de Login

- Abre `http://localhost:3000`
- Deberías ver la página de login con el diseño del design system
- Inicia sesión con un usuario existente

### 2. Redirección

Después del login:
- Si el usuario no ha completado onboarding → `/onboarding`
- Si ya completó onboarding → `/dashboard`

### 3. Onboarding (si aplica)

- Paso 1: Confirmar información de organización
- Paso 2: Seleccionar plantilla de industria
- Paso 3: Personalización (opcional, actualmente se omite)
- Paso 4: Confirmar y aplicar plantilla

### 4. Dashboard

- Deberías ver el dashboard con métricas
- Verifica que los componentes se vean correctamente

## Componentes Implementados del Design System

### ✅ Disponibles

1. **LoginPage** - Página de login con diseño del design system
2. **KPICard** - Tarjetas de métricas (usar en dashboard)
3. **StatusBadge** - Badges de estado para proyectos
4. **EmptyState** - Estados vacíos con iconos

### 🔄 En Progreso

- Layout principal (Sidebar y Header) - Usando componentes existentes, pueden necesitar ajustes
- DashboardPage - Puede necesitar actualización para usar KPICard
- ProjectsPage - Puede necesitar actualización para usar StatusBadge

## Verificación Visual

### Login Page

Deberías ver:
- Logo con icono DollarSign en un círculo azul
- Título "Welcome to Nougram"
- Formulario de login estilizado
- Colores consistentes con el design system (grey-50 background, primary-500 buttons)

### Dashboard (después del login)

- Sidebar a la izquierda
- Header en la parte superior
- Contenido principal en el centro

## Solución de Problemas

### Error: "Cannot connect to backend"

1. Verifica que el backend esté corriendo: `http://localhost:5000/docs`
2. Verifica la URL de la API en `frontend/src/lib/api-client.ts`
3. Verifica CORS en el backend

### Error: "401 Unauthorized"

1. Limpia el localStorage: `localStorage.clear()` en la consola del navegador
2. Intenta iniciar sesión nuevamente
3. Verifica que el token se esté guardando correctamente

### Los estilos no se ven correctamente

1. Verifica que `globals.css` tenga las variables CSS del design system
2. Verifica que `tailwind.config.ts` tenga los colores configurados
3. Reinicia el servidor de desarrollo

### Error: "Module not found"

1. Ejecuta `npm install` en el directorio `frontend`
2. Verifica que todas las dependencias estén instaladas

## Próximos Pasos

Después de probar:

1. **Reportar problemas visuales** - Si algo no coincide con el design system
2. **Probar funcionalidad** - Verificar que todas las acciones funcionen
3. **Probar responsive** - Verificar en diferentes tamaños de pantalla

## Notas

- El design system usa colores específicos (grey-*, primary-*, etc.)
- Los componentes deben seguir el sistema de espaciado de 8px
- Las elevaciones (shadows) están definidas en `globals.css`













