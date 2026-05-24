# Guía de Prueba - Sugerencias de IA (Fase 1)

## Prerrequisitos

1. **Backend corriendo** en `http://localhost:8000`
2. **Frontend corriendo** en `http://localhost:3000`
3. **OPENAI_API_KEY configurada** en las variables de entorno del backend

### Configurar OPENAI_API_KEY

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-tu-api-key-aqui"
```

**Windows (CMD):**
```cmd
set OPENAI_API_KEY=sk-tu-api-key-aqui
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY="sk-tu-api-key-aqui"
```

O agregar al archivo `.env` del backend:
```
OPENAI_API_KEY=sk-tu-api-key-aqui
```

## Opción 1: Prueba desde el Frontend (Recomendado)

1. **Iniciar el backend:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Iniciar el frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Acceder al onboarding:**
   - Navegar a `http://localhost:3000/onboarding`
   - Debes estar autenticado como `owner`

4. **Probar la funcionalidad:**
   - En el **Paso 1 (Localización)**:
     - Ingresar una industria (ej: "Marketing Digital", "Desarrollo Web")
     - Seleccionar país/región (ej: Colombia, Estados Unidos)
     - Seleccionar moneda (ej: COP, USD)
     - Hacer clic en el botón **"✨ Usar IA"**
     - Revisar las sugerencias generadas
     - Aplicar las sugerencias seleccionadas

## Opción 2: Prueba del Endpoint Directamente

### Verificar estado del servicio de IA

```bash
curl http://localhost:8000/api/v1/ai/status
```

Respuesta esperada:
```json
{
  "available": true,
  "message": "AI service is ready"
}
```

### Probar el endpoint de sugerencias

**Con autenticación (requiere token JWT):**

```bash
curl -X POST http://localhost:8000/api/v1/ai/suggest-config \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_JWT" \
  -d '{
    "industry": "Marketing Digital",
    "region": "CO",
    "currency": "COP",
    "custom_context": "Agencia enfocada en SEO y contenido"
  }'
```

## Opción 3: Script de Prueba Python

Ejecutar el script de prueba:

```bash
cd backend
python -m scripts.manual_tests.test_ai_suggestions
```

Este script:
- Verifica que el servicio de IA esté disponible
- Genera sugerencias de ejemplo
- Muestra los resultados en consola

## Respuesta Esperada

El endpoint retorna un objeto `OnboardingSuggestionResponse` con:

```json
{
  "suggested_roles": [
    {
      "name": "Juan Pérez",
      "role": "SEO Specialist",
      "salary_monthly_brute": 3500000,
      "currency": "COP",
      "billable_hours_per_week": 32,
      "is_active": true
    }
  ],
  "suggested_services": [
    {
      "name": "Auditoría SEO",
      "description": "Análisis completo de SEO",
      "default_margin_target": 0.40,
      "pricing_type": "hourly",
      "is_active": true
    }
  ],
  "suggested_fixed_costs": [
    {
      "name": "Ahrefs",
      "amount_monthly": 99,
      "currency": "USD",
      "category": "Software",
      "description": "Herramienta de SEO"
    }
  ],
  "confidence_scores": {
    "roles": 0.85,
    "services": 0.90,
    "costs": 0.75
  },
  "reasoning": "Basado en la industria de Marketing Digital..."
}
```

## Troubleshooting

### Error: "AI service not configured"

**Causa:** `OPENAI_API_KEY` no está configurada.

**Solución:**
1. Verificar que la variable de entorno esté configurada
2. Reiniciar el servidor backend
3. Verificar que el archivo `.env` tenga la clave (si se usa)

### Error: "Invalid response format from AI service"

**Causa:** La respuesta de OpenAI no coincide con el schema esperado.

**Solución:**
1. Verificar los logs del backend para más detalles
2. El servicio debería manejar esto automáticamente, pero si persiste, revisar el prompt en `ai_service.py`

### Error: "Network error" en el frontend

**Causa:** El backend no está corriendo o hay un problema de CORS.

**Solución:**
1. Verificar que el backend esté corriendo en `http://localhost:8000`
2. Verificar la consola del navegador para más detalles
3. Verificar que el token JWT sea válido

### Las sugerencias no se aplican

**Causa:** Problema con el store de onboarding o la función `handleApplyAISuggestions`.

**Solución:**
1. Verificar la consola del navegador para errores
2. Verificar que el store de onboarding esté funcionando correctamente
3. Revisar los logs del backend

## Próximos Pasos

Una vez que la Fase 1 esté funcionando correctamente:
- **Fase 2:** Parsing de documentos (nómina/gastos)
- **Fase 3:** Chat de comandos en lenguaje natural




