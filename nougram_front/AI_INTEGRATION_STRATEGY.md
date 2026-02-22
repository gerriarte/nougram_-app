# Estrategia de Implementación de IA en Nougram

## 1. Visión Arquitectónica: "Agente Copiloto"

La mejor manera de implementar IA en Nougram no es un simple "chatbot", sino un **Copiloto Contextual** que vive en el Backend pero interactúa profundamente con la interfaz de cotización.

### Arquitectura Propuesta

```mermaid
graph TD
    UI[Frontend: Quote Builder] -->|Request: 'Sugerir Presupuesto'| API[FastAPI Backend]
    API -->|Get Context| DB[(PostgreSQL: Histórico)]
    API -->|Similar Quotes Search| VectorDB[(Pinecone/Pgvector)]
    
    subgraph "AI Brain"
        Orchestrator[AI Orchestrator (LangChain)]
        Orchestrator -->|Prompt + RAG Context| LLM[LLM Provider (Claude 3.5 Sonnet)]
    end
    
    API --> Orchestrator
    LLM -->|JSON Response| Orchestrator
    Orchestrator -->|Structured Data| API
    API -->|Populate State| UI
```

## 2. Casos de Uso de Alto Impacto

### A. "Smart Quote Initialization" (El más valioso)

**Problema:** "No sé cuánto cobrar por este proyecto nuevo".
**Solución:**

1. El usuario escribe: *"E-commerce para marca de ropa, ~50 productos, pasarela Wompi"*.
2. **RAG (Búsqueda Semántica):** El sistema busca las 5 cotizaciones *ganadas* más similares del último año.
3. **Inferencia:** El LLM analiza los promedios de esas cotizaciones (horas, roles, márgenes).
4. **Acción:** El LLM devuelve un JSON que **pre-llena** el Cotizador con items sugeridos.

### B. "Review & Optimizador de Margen"

**Función:** Antes de enviar, un botón "Analizar con IA".
**Lógica:** Compara la propuesta actual con el histórico de la empresa.
**Output:** "Estás cobrando 20% menos que el promedio para este tipo de cliente. Te sugiero subir el margen al 35% o agregar un fee de mantenimiento".

### C. "Generador de Propuestas Comerciales"

**Función:** Transformar los números fríos en persuasión.
**Input:** Items de la cotización + Descripción del cliente.
**Output:** Genera el texto de la carta de presentación ("Scope of Work") con tono persuasivo, explicando el valor de cada item técnico.

## 3. Guía de Implementación Técnica

### Fase 1: El "Cerebro" (Backend)

Usarás el stack que ya definimos (FastAPI):

1. **AI Gateway:** Un router dedicado `/api/v1/ai`.
2. **Modelos:** Usar **Claude 3.5 Sonnet** (excelente para razonamiento y JSON estructurado) o **GPT-4o**.
3. **Structured Output:** Forzar al LLM a responder SIEMPRE en JSON validado con Pydantic. **Nunca texto libre para datos**.

```python
class QuoteSuggestion(BaseModel):
    rationale: str
    suggested_margin: float
    items: List[QuoteItem]
```

### Fase 2: RAG (Memoria)

Para que la IA no alucine precios, debe conocer TUS precios verdaderos.

1. **Pgvector:** Activar la extensión vectorial en tu Postgres.
2. **Embedding:** Cada vez que se gana una cotización, generar un embedding de su descripción y guardarlo.
3. **Retrieval:** Al cotizar, recuperar contexto relevante.

### Fase 3: UX "No Intrusiva"

En el frontend (Next.js):

1. No usar popups molestos.
2. Usar **"Ghost Text"** o sugerencias laterales.
3. **Streaming:** Mostrar la respuesta de la IA mientras se genera para reducir la sensación de espera.

## 4. Privacy & Security

* **Anonymization:** Nunca enviar PII (emails, teléfonos) al LLM. Solo enviar industrias, tipos de proyecto y montos.
* **Tenant Isolation:** Asegurar que la IA de la "Agencia A" no aprenda ni sugiera datos basados en la "Agencia B".
