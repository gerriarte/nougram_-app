# 🧪 Guía de Pruebas - Sprint 1

## Verificación Rápida de Cambios

### 1. Verificar que el Backend Inicia Correctamente

```bash
cd backend
python main.py
```

**Esperado:** El servidor debe iniciar sin errores en `http://localhost:5000`

### 2. Verificar Endpoints Refactorizados

Una vez que el backend esté corriendo, puedes probar estos endpoints:

#### Costos Fijos
```bash
# Listar costos (requiere autenticación)
GET http://localhost:5000/api/v1/settings/costs/fixed
```

#### Servicios
```bash
# Listar servicios
GET http://localhost:5000/api/v1/services
```

#### Equipo
```bash
# Listar miembros del equipo
GET http://localhost:5000/api/v1/settings/team
```

#### Impuestos
```bash
# Listar impuestos
GET http://localhost:5000/api/v1/taxes
```

#### Usuarios
```bash
# Listar usuarios (requiere super_admin)
GET http://localhost:5000/api/v1/users/
```

#### Configuración
```bash
# Obtener configuración de moneda
GET http://localhost:5000/api/v1/settings/currency
```

### 3. Verificar Logs Estructurados

Al hacer peticiones a los endpoints, deberías ver logs estructurados en la consola del backend con formato:
```
2025-12-12 11:39:01 | INFO     | app.api.v1.endpoints.costs | list_fixed_costs | User gerriarte@abralatam.com listed 5 fixed costs.
```

### 4. Verificar Frontend

```bash
cd frontend
npm run dev
```

**Esperado:** 
- El frontend debe iniciar sin errores en `http://localhost:3000`
- No deberías ver `console.log` en la consola del navegador (excepto en desarrollo)
- Los errores siempre se mostrarán en la consola

### 5. Probar Funcionalidad Completa

1. **Iniciar sesión** con las credenciales por defecto:
   - Email: `gerriarte@abralatam.com`
   - Password: `Abracolombia`

2. **Navegar por las secciones:**
   - Servicios
   - Costos Fijos
   - Equipo
   - Impuestos
   - Configuración

3. **Crear/Editar/Eliminar elementos** en cada sección para verificar que todo funciona

### 6. Verificar que No Hay Errores

**Backend:**
- Revisar la consola del backend por errores
- Verificar que los logs se muestran correctamente

**Frontend:**
- Abrir DevTools (F12)
- Revisar la consola por errores
- Verificar que no hay warnings relacionados con `console.log`

## ✅ Checklist de Verificación

- [ ] Backend inicia sin errores
- [ ] Frontend inicia sin errores
- [ ] Puedo iniciar sesión correctamente
- [ ] Los endpoints de servicios funcionan
- [ ] Los endpoints de costos funcionan
- [ ] Los endpoints de equipo funcionan
- [ ] Los endpoints de impuestos funcionan
- [ ] Los logs estructurados aparecen en el backend
- [ ] No hay `console.log` innecesarios en el frontend (solo en desarrollo)
- [ ] Puedo crear/editar/eliminar elementos sin problemas

## 🐛 Si Encuentras Problemas

1. **Backend no inicia:**
   - Verificar que PostgreSQL está corriendo (Docker)
   - Verificar que el archivo `.env` existe y está configurado
   - Revisar los logs de error en la consola

2. **Errores de importación:**
   - Verificar que el entorno virtual está activado
   - Ejecutar: `pip install -r requirements.txt`

3. **Frontend no compila:**
   - Ejecutar: `npm install`
   - Limpiar caché: `rm -rf .next` (o `rmdir /s .next` en Windows)
   - Reintentar: `npm run dev`

4. **Errores de CORS:**
   - Verificar que `CORS_ORIGINS` en `.env` incluye `http://localhost:3000`
   - Verificar que el backend está en el puerto 5000

## 📝 Notas

- Los cambios son **backward compatible** - no deberían romper funcionalidad existente
- Los endpoints de `projects` y `quotes` **NO fueron refactorizados** aún (son más complejos)
- El logging estructurado está implementado pero puede mejorarse agregando más contexto según sea necesario

