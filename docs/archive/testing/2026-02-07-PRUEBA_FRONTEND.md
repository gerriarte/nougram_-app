# Guía para Probar el Frontend

## Requisitos Previos

1. **Backend corriendo**: El servidor FastAPI debe estar activo en `http://localhost:5000`
2. **Base de datos**: PostgreSQL debe estar corriendo (Docker Compose)
3. **Dependencias instaladas**: Node.js y npm instalados

## Pasos para Probar el Frontend

### 1. Iniciar el Backend

Abre una terminal y ejecuta:

```bash
cd backend
# Activa el entorno virtual si es necesario
python -m uvicorn main:app --reload --port 5000
```

O si usas un script de inicio:

```bash
cd backend
python main.py
```

Verifica que el backend esté corriendo visitando: `http://localhost:5000/docs`

### 2. Iniciar el Frontend

En otra terminal, ejecuta:

```bash
cd frontend
npm run dev
```

El servidor de desarrollo de Next.js se iniciará en: `http://localhost:3000`

### 3. Probar el Flujo de Onboarding

#### Paso 1: Login
1. Abre `http://localhost:3000` en tu navegador
2. Si no estás autenticado, serás redirigido a `/login`
3. Inicia sesión con un usuario existente

#### Paso 2: Verificar Redirección a Onboarding
- Si el usuario no ha completado el onboarding, serás redirigido automáticamente a `/onboarding`
- Si ya completó el onboarding, irás al `/dashboard`

#### Paso 3: Flujo de Onboarding
1. **Paso 1 - Confirmar Información**: 
   - Verás tu nombre y email
   - Haz clic en "Continue"

2. **Paso 2 - Seleccionar Plantilla**:
   - Verás 5 plantillas de industria disponibles:
     - Branding Agency
     - Web Development
     - Marketing Agency
     - Consulting
     - Video Production
   - Haz clic en "View Details" para ver más información
   - Selecciona una plantilla haciendo clic en la tarjeta
   - Haz clic en "Continue"

3. **Paso 3 - Personalización** (Opcional, actualmente se omite):
   - Este paso está preparado para futuras personalizaciones

4. **Paso 4 - Confirmación**:
   - Revisa el resumen de lo que se creará:
     - Número de roles de equipo
     - Número de servicios
     - Número de costos fijos
   - Selecciona la región (US, UK, COL, ARG, MEX, ESP, BR)
   - Selecciona la moneda (USD, EUR, COP, ARS, MXN, BRL)
   - Haz clic en "Launch Workspace"

5. **Resultado**:
   - Se aplicará la plantilla a tu organización
   - Se crearán los roles, servicios y costos sugeridos
   - Serás redirigido al dashboard

## Verificación de Funcionalidad

### Endpoints que se Utilizan

1. **GET /api/v1/templates/industries?active_only=true**
   - Obtiene la lista de plantillas disponibles
   - Debe retornar 5 plantillas

2. **GET /api/v1/templates/industries/{industry_type}**
   - Obtiene detalles de una plantilla específica
   - Se usa cuando haces clic en "View Details"

3. **POST /api/v1/templates/organizations/{organization_id}/apply-template**
   - Aplica una plantilla a una organización
   - Crea roles, servicios y costos

4. **GET /api/v1/auth/me**
   - Obtiene información del usuario actual
   - Incluye `organization_id` para el multi-tenant

### Verificación en la Base de Datos

Después de aplicar una plantilla, puedes verificar en PostgreSQL:

```sql
-- Ver roles creados
SELECT * FROM team_members WHERE organization_id = <tu_org_id>;

-- Ver servicios creados
SELECT * FROM services WHERE organization_id = <tu_org_id>;

-- Ver costos creados
SELECT * FROM costs_fixed WHERE organization_id = <tu_org_id> AND is_suggested = true;
```

## Solución de Problemas

### El frontend no se conecta al backend

1. Verifica que el backend esté corriendo: `http://localhost:5000/docs`
2. Verifica la URL de la API en `frontend/src/lib/api-client.ts`
3. Verifica que CORS esté configurado correctamente en el backend

### Error 401 (No autorizado)

1. Verifica que tengas un token de autenticación válido
2. Inicia sesión nuevamente
3. Verifica que el JWT incluya `organization_id`

### No se muestran las plantillas

1. Verifica que la migración de plantillas se haya ejecutado:
   ```bash
   cd backend
   alembic upgrade head
   ```
2. Verifica en la base de datos:
   ```sql
   SELECT * FROM industry_templates;
   ```

### Error al aplicar plantilla

1. Verifica que el usuario tenga `organization_id`
2. Verifica los logs del backend para ver el error específico
3. Asegúrate de que la organización exista y esté activa

## Próximos Pasos

- [ ] Agregar validación de formularios en el onboarding
- [ ] Implementar el paso de personalización (Paso 3)
- [ ] Agregar animaciones y transiciones
- [ ] Mejorar el manejo de errores con toasts
- [ ] Agregar indicadores de carga más detallados













