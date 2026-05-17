# API de Inteligencia Artificial - Documentación

Esta documentación describe los endpoints de la API para funcionalidades de IA, incluyendo sugerencias de configuración, parsing de documentos y procesamiento de comandos en lenguaje natural.

**Versión:** 1.0  
**Base URL:** `/api/v1/ai`

---

## Índice

1. [Configuración](#configuración)
2. [Endpoints de IA](#endpoints-de-ia)
   - [Sugerencias de Configuración](#1-sugerencias-de-configuración)
   - [Parsing de Documentos](#2-parsing-de-documentos)
   - [Procesamiento de Comandos](#3-procesamiento-de-comandos)
3. [Rate Limiting](#rate-limiting)
4. [Caché](#caché)
5. [Privacidad y Anonimización](#privacidad-y-anonimización)
6. [Códigos de Estado HTTP](#códigos-de-estado-http)
7. [Ejemplos de Uso](#ejemplos-de-uso)

---

## Configuración

### Variables de Entorno Requeridas

```env
OPENAI_API_KEY=sk-...
```

### Modelo de IA

El sistema utiliza **GPT-4 Turbo** (`gpt-4-turbo-preview`) para todas las operaciones de IA con:
- **Structured Outputs** para respuestas JSON consistentes
- **Temperature** configurado según el tipo de operación:
  - Sugerencias: `0.7` (más creativo)
  - Parsing: `0.3` (más preciso)
  - Comandos: `0.5` (balanceado)

---

## Endpoints de IA

### 1. Sugerencias de Configuración

Genera sugerencias automáticas de configuración inicial basadas en industria, región y moneda.

**Endpoint:** `POST /api/v1/ai/suggest-config`

**Autenticación:** Requerida  
**Permisos:** Todos los usuarios autenticados  
**Rate Limit:** Ver [Rate Limiting](#rate-limiting)

**Request Body:**
```json
{
  "industry": "Marketing Digital",
  "region": "US",
  "currency": "USD",
  "custom_context": "Agencia especializada en e-commerce"
}
```

**Campos:**
- `industry` (string, requerido): Tipo de industria (ej: "Marketing Digital", "Desarrollo Web", "Diseño Gráfico")
- `region` (string, opcional, default: "US"): Código de región (ej: "US", "CO", "MX", "AR")
- `currency` (string, opcional, default: "USD"): Moneda principal (ej: "USD", "COP", "ARS", "EUR")
- `custom_context` (string, opcional): Contexto adicional sobre el negocio

**Response 200 OK:**
```json
{
  "suggested_roles": [
    {
      "name": "John Doe",
      "role": "Senior Developer",
      "salary_monthly_brute": 5000,
      "currency": "USD",
      "billable_hours_per_week": 40,
      "is_active": true
    }
  ],
  "suggested_services": [
    {
      "name": "Web Development",
      "description": "Custom web development services",
      "default_margin_target": 0.30,
      "pricing_type": "hourly",
      "is_active": true
    }
  ],
  "suggested_fixed_costs": [
    {
      "name": "AWS Hosting",
      "amount_monthly": 200,
      "currency": "USD",
      "category": "Tools",
      "description": "Cloud hosting services"
    }
  ],
  "confidence_scores": {
    "roles": 0.9,
    "services": 0.85,
    "costs": 0.8
  },
  "reasoning": "Based on industry standards for digital marketing agencies in the US"
}
```

**Response 400 Bad Request:**
```json
{
  "detail": "Industry is required"
}
```

**Response 401 Unauthorized:**
```json
{
  "detail": "Not authenticated"
}
```

**Response 429 Too Many Requests:**
```json
{
  "detail": "Rate limit exceeded: 10 requests per minute"
}
```

**Notas:**
- Las sugerencias se cachean por 24 horas usando la clave: `{industry}:{region}:{currency}`
- Si se proporciona `custom_context`, se incluye un hash en la clave de caché
- Los salarios sugeridos están ajustados a la región especificada

---

### 2. Parsing de Documentos

Extrae información estructurada de documentos desordenados (nóminas, gastos, etc.).

**Endpoint:** `POST /api/v1/ai/parse-document`

**Autenticación:** Requerida  
**Permisos:** Todos los usuarios autenticados  
**Rate Limit:** Ver [Rate Limiting](#rate-limiting)

**Request Body:**
```json
{
  "text": "John Doe, Senior Developer, $5000/month\nJane Smith, Designer, $4000/month\nAWS Hosting: $200/month",
  "document_type": "payroll"
}
```

**Campos:**
- `text` (string, requerido): Contenido del documento (máximo 10,000 caracteres)
- `document_type` (string, opcional): Tipo de documento ("payroll", "expenses", "mixed")

**Response 200 OK:**
```json
{
  "team_members": [
    {
      "name": "John Doe",
      "role": "Senior Developer",
      "salary_monthly_brute": 5000,
      "currency": "USD",
      "billable_hours_per_week": 40
    },
    {
      "name": "Jane Smith",
      "role": "Designer",
      "salary_monthly_brute": 4000,
      "currency": "USD",
      "billable_hours_per_week": 40
    }
  ],
  "fixed_costs": [
    {
      "name": "AWS Hosting",
      "amount_monthly": 200,
      "currency": "USD",
      "category": "Tools"
    }
  ],
  "subscriptions": [],
  "confidence_scores": {
    "team_members": 0.85,
    "fixed_costs": 0.9,
    "subscriptions": 0.8
  },
  "warnings": [
    "Could not determine billable hours for Jane Smith, using default 40"
  ]
}
```

**Response 400 Bad Request:**
```json
{
  "detail": "Text content is required and cannot be empty"
}
```

```json
{
  "detail": "Text content is too long. Maximum 10000 characters allowed."
}
```

**Notas:**
- El texto se procesa directamente sin anonimización (el usuario proporciona explícitamente estos datos)
- Los montos se normalizan a mensuales cuando es necesario
- Las ambigüedades se reportan en el campo `warnings`

---

### 3. Procesamiento de Comandos

Procesa comandos en lenguaje natural y genera acciones estructuradas.

**Endpoint:** `POST /api/v1/ai/process-command`

**Autenticación:** Requerida  
**Permisos:** Todos los usuarios autenticados  
**Rate Limit:** Ver [Rate Limiting](#rate-limiting)

**Request Body:**
```json
{
  "command": "Add a Senior Designer named Bob Johnson with salary $4500/month",
  "context": {
    "existing_services": ["Web Development", "SEO"],
    "currency": "USD"
  }
}
```

**Campos:**
- `command` (string, requerido): Comando en lenguaje natural
- `context` (object, opcional): Contexto actual de la organización (se construye automáticamente si no se proporciona)

**Response 200 OK:**
```json
{
  "action": "add_team_member",
  "data": {
    "name": "Bob Johnson",
    "role": "Senior Designer",
    "salary_monthly_brute": 4500,
    "currency": "USD",
    "billable_hours_per_week": 40
  },
  "confidence": 0.9,
  "reasoning": "Command clearly requests adding a team member with specified details"
}
```

**Acciones Posibles:**
- `add_team_member`: Agregar miembro del equipo
- `add_service`: Agregar servicio
- `add_fixed_cost`: Agregar costo fijo
- `update_team_member`: Actualizar miembro del equipo
- `update_service`: Actualizar servicio
- `update_fixed_cost`: Actualizar costo fijo

**Response 400 Bad Request:**
```json
{
  "detail": "Command is required and cannot be empty"
}
```

**Notas:**
- Si no se proporciona `context`, se construye automáticamente con:
  - Nombres y roles de miembros del equipo (anonimizados)
  - Nombres de servicios existentes
  - Información de costos fijos (sin montos)
- Los nombres en el context automático se anonimizan antes de enviar a OpenAI

---

## Rate Limiting

Los endpoints de IA tienen rate limiting configurado por plan de suscripción:

| Plan | Límite |
|------|--------|
| Free | 5 requests/minuto |
| Starter | 10 requests/minuto |
| Professional | 20 requests/minuto |
| Enterprise | 50 requests/minuto |

**Comportamiento:**
- El rate limiting se aplica por tenant (organización)
- Si se excede el límite, se retorna `429 Too Many Requests`
- El límite se resetea cada minuto

**Headers de Respuesta:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 8
X-RateLimit-Reset: 1640995200
```

---

## Caché

### Sugerencias de Configuración

Las sugerencias de configuración se cachean por 24 horas usando la siguiente clave:
```
ai_suggestion:{industry}:{region}:{currency}
```

**Ejemplo:**
```
ai_suggestion:marketing digital:us:usd
```

**Comportamiento:**
- Si se proporciona `custom_context`, se incluye un hash MD5 en la clave
- Solo se cachean sugerencias sin `custom_context` o con `custom_context` corto (< 200 caracteres)
- Los hits de caché retornan `usage.cached: true` y no consumen tokens de OpenAI

**Response con Caché:**
```json
{
  "suggested_roles": [...],
  "suggested_services": [...],
  "suggested_fixed_costs": [...],
  "confidence_scores": {...},
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "estimated_cost": 0.0,
    "cached": true
  }
}
```

---

## Privacidad y Anonimización

### Datos Anonimizados

Los siguientes datos se anonimizan automáticamente antes de enviar a OpenAI:

1. **Nombres de miembros del equipo** (en context automático de `process-command`)
   - Se reemplazan con identificadores genéricos (ej: "Team Member 1", "Team Member 2")
   - Los salarios y otros datos sensibles NO se incluyen en el context

2. **Nombres de clientes** (si se implementa en el futuro)

### Datos NO Anonimizados

Los siguientes datos se envían directamente a OpenAI (el usuario los proporciona explícitamente):

1. **Texto de documentos** (`parse-document`)
   - El usuario pega explícitamente el contenido del documento
   - Se asume que el usuario tiene permiso para procesar estos datos

2. **Comandos en lenguaje natural** (`process-command`)
   - El usuario escribe explícitamente el comando
   - Puede incluir nombres reales si el usuario lo desea

---

## Códigos de Estado HTTP

| Código | Descripción |
|--------|-------------|
| 200 | Éxito |
| 201 | Creado |
| 400 | Solicitud inválida (validación, texto vacío, etc.) |
| 401 | No autenticado |
| 403 | Sin permisos |
| 429 | Rate limit excedido |
| 500 | Error interno del servidor |
| 503 | Servicio de IA no disponible (OPENAI_API_KEY no configurado) |

---

## Ejemplos de Uso

### Ejemplo 1: Obtener Sugerencias de Configuración

```bash
curl -X POST "https://api.example.com/api/v1/ai/suggest-config" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "industry": "Marketing Digital",
    "region": "US",
    "currency": "USD"
  }'
```

### Ejemplo 2: Parsear Documento de Nómina

```bash
curl -X POST "https://api.example.com/api/v1/ai/parse-document" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "John Doe, Senior Developer, $5000/month\nJane Smith, Designer, $4000/month",
    "document_type": "payroll"
  }'
```

### Ejemplo 3: Procesar Comando en Lenguaje Natural

```bash
curl -X POST "https://api.example.com/api/v1/ai/process-command" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "Add a Senior Designer named Bob Johnson with salary $4500/month",
    "context": null
  }'
```

### Ejemplo 4: Manejo de Errores

```bash
# Rate limit excedido
curl -X POST "https://api.example.com/api/v1/ai/suggest-config" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"industry": "Marketing Digital"}'

# Response 429:
{
  "detail": "Rate limit exceeded: 10 requests per minute"
}
```

---

## Notas de Implementación

- Todas las operaciones de IA requieren que el usuario esté autenticado
- Los endpoints están protegidos por rate limiting basado en el plan de suscripción
- Las sugerencias de configuración se cachean para reducir costos de API
- Los nombres en context automático se anonimizan para proteger privacidad
- El sistema utiliza Structured Outputs de OpenAI para garantizar respuestas JSON válidas
- Los errores de parsing JSON se manejan gracefully con mensajes de error claros

---

## Costos Estimados

**Modelo:** GPT-4 Turbo

**Precios aproximados (Enero 2025):**
- Input: $10.00 / 1M tokens
- Output: $30.00 / 1M tokens

**Ejemplos de uso:**
- Sugerencia de configuración: ~500 tokens input + ~300 tokens output = ~$0.02
- Parsing de documento: ~600 tokens input + ~400 tokens output = ~$0.03
- Procesamiento de comando: ~400 tokens input + ~200 tokens output = ~$0.01

**Optimizaciones:**
- Caché de sugerencias reduce costos en ~80% para solicitudes repetidas
- Rate limiting previene abuso y controla costos
- Structured Outputs reducen necesidad de re-parsing

---

**Última actualización:** Enero 2025  
**Versión de API:** 1.0
