# Evaluación: Sistema de Tokens/Credits para Nougram

**Fecha:** Diciembre 2025  
**Versión:** 1.0  
**Estado:** Análisis de Viabilidad

---

## 1. Resumen Ejecutivo

### 1.1 Conclusión Principal

**Recomendación: NO RECOMENDADO** para la mayoría de funcionalidades, pero **VIABLE CON MODIFICACIONES** para funcionalidades específicas de alto costo.

### 1.2 Razones Clave

1. **Naturaleza del Producto:** Herramienta de gestión continua, no servicio de procesamiento
2. **Modelo Actual:** Suscripciones funcionan mejor para este tipo de SaaS
3. **Fricción de Usuario:** Sistema de tokens añade complejidad y ansiedad
4. **Costo de Implementación:** Alto costo de desarrollo vs. beneficio limitado

### 1.3 Alternativa Recomendada

**Modelo Híbrido:** Suscripciones base + Tokens para funcionalidades premium específicas (IA avanzada, exportaciones masivas, integraciones costosas)

---

## 2. Análisis del Contexto Actual

### 2.1 Naturaleza del Producto

**Nougram es:**
- Plataforma de gestión de cotizaciones
- Herramienta de trabajo diario para agencias
- Sistema de cálculo y análisis financiero
- Dashboard de BI con insights

**NO es:**
- Servicio de procesamiento por transacción
- API de uso esporádico
- Herramienta de uso ocasional
- Servicio de "pay-per-use" tradicional

### 2.2 Modelo Actual (Plan Multi-Tenant)

**Planes de Suscripción:**
- Free: Limitado
- Starter: Básico
- Professional: Completo
- Enterprise: Sin límites

**Límites por Plan:**
- Número de usuarios
- Número de proyectos
- Almacenamiento (futuro)
- Features premium

### 2.3 Funcionalidades Principales

**Operaciones Core (Sin Costo Variable):**
1. Crear/editar proyectos
2. Crear/editar cotizaciones
3. Gestionar servicios
4. Gestionar equipo
5. Gestionar costos
6. Ver dashboard básico
7. Exportar PDF/DOCX (costo mínimo)

**Operaciones con Costo Variable Potencial:**
1. **Asistente IA:** Costo por consulta (API de IA)
2. **Exportaciones masivas:** Procesamiento
3. **Integraciones:** Google Sheets, Calendar, Apollo.io
4. **Análisis avanzados:** Cálculos complejos

---

## 3. Análisis de Viabilidad

### 3.1 Viabilidad Técnica

#### ✅ Factible Técnicamente

**Implementación Requerida:**

1. **Modelo de Datos:**
```python
# Nuevos modelos
class TokenBalance(Base):
    organization_id: int
    balance: Decimal
    currency: str
    updated_at: DateTime

class TokenTransaction(Base):
    organization_id: int
    amount: Decimal  # Positivo (recarga) o negativo (consumo)
    transaction_type: str  # 'purchase', 'consumption', 'refund'
    reference_type: str  # 'quote_creation', 'ai_query', 'export'
    reference_id: int
    created_at: DateTime

class TokenPrice(Base):
    action_type: str  # 'create_quote', 'ai_query', 'export_pdf'
    price: Decimal
    currency: str
```

2. **Endpoints Necesarios:**
- `POST /api/v1/organizations/{id}/tokens/purchase` - Recargar tokens
- `GET /api/v1/organizations/{id}/tokens/balance` - Ver balance
- `GET /api/v1/organizations/{id}/tokens/transactions` - Historial
- `POST /api/v1/organizations/{id}/tokens/consume` - Consumir tokens (interno)

3. **Middleware de Validación:**
```python
async def check_token_balance(
    action_type: str,
    organization_id: int,
    db: AsyncSession
) -> bool:
    # Verificar balance suficiente
    # Retornar True/False
```

4. **Integración con Stripe:**
- Crear productos de tokens
- Checkout para compra de tokens
- Webhook para actualizar balance

**Complejidad:** Media-Alta  
**Tiempo Estimado:** 3-4 semanas  
**Riesgo Técnico:** Bajo-Medio

#### ⚠️ Consideraciones Técnicas

- **Concurrencia:** Manejar race conditions en consumo de tokens
- **Transacciones:** Usar transacciones DB para atomicidad
- **Auditoría:** Logging completo de transacciones
- **Performance:** Índices en `organization_id` y `created_at`

### 3.2 Viabilidad de Negocio

#### ❌ Desventajas del Modelo de Tokens

**1. Fricción de Usuario:**
- Ansiedad por "quedarse sin tokens"
- Interrupciones en flujo de trabajo
- Necesidad de recargar constantemente
- Dificultad para predecir costos

**2. Modelo de Negocio:**
- **Suscripciones** son más predecibles para el cliente
- **Suscripciones** generan ingresos recurrentes más estables
- **Tokens** requieren más esfuerzo de venta
- **Tokens** pueden disuadir uso frecuente

**3. Competencia:**
- La mayoría de SaaS B2B usan suscripciones
- Tokens son más comunes en:
  - APIs de procesamiento
  - Servicios de IA por consulta
  - Herramientas de uso esporádico

**4. Pricing:**
- Difícil determinar precio "justo" por acción
- Usuarios pueden sentirse "cobrados dos veces" (suscripción + tokens)
- Complejidad en comunicación de precios

#### ✅ Ventajas Potenciales

**1. Para Funcionalidades Premium:**
- IA avanzada (costo variable alto)
- Exportaciones masivas
- Integraciones costosas

**2. Flexibilidad:**
- Usuarios ocasionales pueden pagar solo por uso
- No requiere compromiso mensual para features premium

**3. Escalabilidad de Costos:**
- Alinea costos operativos con ingresos
- Especialmente útil para funcionalidades con costo variable (IA)

### 3.3 Viabilidad de UX

#### ❌ Problemas de UX con Tokens

**1. Fricción Mental:**
```
Usuario: "¿Cuántos tokens tengo?"
Sistema: "Tienes 47 tokens"
Usuario: "¿Cuánto cuesta crear una cotización?"
Sistema: "5 tokens"
Usuario: "¿Cuántas cotizaciones puedo hacer?"
Usuario: *calcula mentalmente*
```

**2. Interrupciones:**
- "No tienes suficientes tokens para esta acción"
- Redirección a página de recarga
- Interrupción del flujo de trabajo

**3. Transparencia:**
- Usuarios necesitan entender:
  - Cuánto cuesta cada acción
  - Cuántos tokens tienen
  - Cuántos tokens quedan después de una acción
  - Cuándo necesitan recargar

**4. Predictibilidad:**
- Difícil predecir cuántos tokens se necesitan
- Puede generar ansiedad y uso conservador

#### ✅ Mejoras de UX Posibles

**1. Indicadores Visuales:**
- Balance visible en header
- Preview de costo antes de acción
- Alertas cuando balance es bajo

**2. Auto-recarga:**
- Configurar auto-recarga cuando balance < X
- Elimina fricción de recarga manual

**3. Bundles:**
- "Pack de 100 cotizaciones"
- Más fácil de entender que tokens abstractos

---

## 4. Análisis por Funcionalidad

### 4.1 Crear Cotización

**Costo Actual:** $0 (incluido en suscripción)  
**Costo con Tokens:** 5-10 tokens (~$0.50-$1.00)

**Análisis:**
- ❌ **NO RECOMENDADO**
- Es funcionalidad core, uso frecuente
- Cobrar por esto generaría alta fricción
- Usuarios esperan poder crear cotizaciones ilimitadas

**Alternativa:** Incluir en suscripción, límite por plan (ej: Free: 10/mes, Starter: 100/mes)

### 4.2 Asistente IA

**Costo Actual:** $0 (incluido)  
**Costo Real:** Variable (API de IA: $0.01-$0.10 por consulta)  
**Costo con Tokens:** 10-50 tokens (~$1-$5)

**Análisis:**
- ✅ **RECOMENDADO PARA VERSIÓN PREMIUM**
- Costo variable alto
- Uso puede ser esporádico o intensivo
- Ideal para modelo de tokens

**Propuesta:**
- **Plan Free/Starter:** 10 consultas IA/mes incluidas
- **Plan Professional:** 100 consultas IA/mes incluidas
- **Tokens:** Para consultas adicionales o usuarios ocasionales

### 4.3 Exportar PDF/DOCX

**Costo Actual:** $0  
**Costo Real:** Mínimo (procesamiento local)  
**Costo con Tokens:** 1-2 tokens (~$0.10-$0.20)

**Análisis:**
- ❌ **NO RECOMENDADO**
- Funcionalidad básica esperada
- Costo real muy bajo
- Alta fricción para poco beneficio

**Alternativa:** Incluir en todos los planes

### 4.4 Exportaciones Masivas

**Costo Actual:** No existe  
**Costo Real:** Medio (procesamiento)  
**Costo con Tokens:** 20-50 tokens (~$2-$5)

**Análisis:**
- ✅ **RECOMENDADO**
- Funcionalidad premium
- Uso ocasional
- Justifica costo adicional

**Propuesta:** Feature premium, tokens o límite por plan

### 4.5 Integraciones (Google Sheets, Calendar, Apollo)

**Costo Actual:** No existe  
**Costo Real:** Variable (API calls)  
**Costo con Tokens:** 5-15 tokens por sincronización (~$0.50-$1.50)

**Análisis:**
- ⚠️ **CONSIDERAR PARA VERSIÓN PREMIUM**
- Costo variable
- Uso puede ser frecuente
- Puede incluirse en planes superiores

**Propuesta:** 
- Starter: No incluye
- Professional: Incluye con límites
- Enterprise: Ilimitado
- O tokens para uso adicional

### 4.6 Dashboard y Análisis

**Costo Actual:** $0  
**Costo Real:** Bajo (cálculos locales)  
**Costo con Tokens:** No aplica

**Análisis:**
- ❌ **NO APLICA**
- Funcionalidad core
- Sin costo variable significativo
- Debe estar en todos los planes

---

## 5. Modelos Alternativos

### 5.1 Modelo Actual (Suscripciones) - RECOMENDADO

**Ventajas:**
- ✅ Predictible para cliente
- ✅ Ingresos recurrentes estables
- ✅ Baja fricción de uso
- ✅ Estándar de la industria
- ✅ Fácil de comunicar

**Desventajas:**
- ⚠️ Costos variables (IA) pueden comer margen
- ⚠️ Usuarios ocasionales pagan de más

**Mejora Propuesta:**
- Límites por plan más claros
- Overage billing para uso excesivo (opcional)

### 5.2 Modelo Híbrido - ALTERNATIVA VIABLE

**Estructura:**
- **Suscripción Base:** Incluye funcionalidades core
- **Tokens para Premium:** Solo funcionalidades de alto costo

**Ejemplo:**
```
Plan Starter: $29/mes
- Cotizaciones ilimitadas
- 10 consultas IA/mes incluidas
- Exportaciones básicas
- Tokens adicionales: $10 por 100 tokens
  - Consulta IA: 10 tokens
  - Exportación masiva: 20 tokens
```

**Ventajas:**
- ✅ Combina lo mejor de ambos modelos
- ✅ Funcionalidades core sin fricción
- ✅ Premium paga por uso
- ✅ Escalable según necesidad

**Desventajas:**
- ⚠️ Complejidad de implementación
- ⚠️ Requiere educación del usuario

### 5.3 Modelo Puro de Tokens - NO RECOMENDADO

**Estructura:**
- Sin suscripción base
- Todo se paga con tokens
- Recargas mínimas

**Ventajas:**
- ✅ Solo pagas por lo que usas
- ✅ Sin compromiso

**Desventajas:**
- ❌ Alta fricción
- ❌ Ingresos impredecibles
- ❌ No estándar para este tipo de SaaS
- ❌ Ansiedad de usuario

---

## 6. Recomendación Final

### 6.1 Recomendación Principal

**NO implementar sistema de tokens para funcionalidades core.**

**Razones:**
1. Alta fricción de usuario
2. No alineado con naturaleza del producto
3. Modelo de suscripción funciona mejor
4. Costo de implementación alto vs. beneficio limitado

### 6.2 Recomendación Alternativa

**Implementar modelo híbrido para funcionalidades premium específicas:**

**Fase 1: Mejorar Modelo de Suscripción (Sprint 7)**
- Límites claros por plan
- Overage billing opcional
- Features premium bien definidas

**Fase 2: Tokens Solo para IA (Futuro, si es necesario)**
- Consultas IA básicas incluidas en plan
- Tokens para consultas adicionales
- Auto-recarga opcional

**Fase 3: Evaluar Otras Funcionalidades Premium**
- Exportaciones masivas
- Integraciones avanzadas
- Análisis avanzados

### 6.3 Plan de Implementación (Si se Decide por Tokens)

**Sprint 9: Sistema de Tokens (Opcional)**

**Tareas:**
1. Modelos de datos (TokenBalance, TokenTransaction)
2. Endpoints de gestión de tokens
3. Integración con Stripe para compra
4. Middleware de validación
5. UI de balance y recarga
6. Indicadores visuales
7. Auto-recarga opcional
8. Testing exhaustivo

**Duración:** 3-4 semanas  
**Prioridad:** Baja (solo si hay demanda clara)

---

## 7. Comparación de Modelos

| Aspecto | Suscripciones | Tokens Puro | Híbrido |
|---------|---------------|-------------|---------|
| **Fricción de Usuario** | ⭐⭐⭐⭐⭐ Baja | ⭐⭐ Alta | ⭐⭐⭐ Media |
| **Predictibilidad Cliente** | ⭐⭐⭐⭐⭐ Alta | ⭐⭐ Baja | ⭐⭐⭐⭐ Alta |
| **Ingresos Recurrentes** | ⭐⭐⭐⭐⭐ Estables | ⭐⭐ Variables | ⭐⭐⭐⭐ Estables |
| **Complejidad Técnica** | ⭐⭐⭐⭐ Media | ⭐⭐⭐ Media-Alta | ⭐⭐⭐⭐ Media-Alta |
| **Escalabilidad Costos** | ⭐⭐⭐ Media | ⭐⭐⭐⭐⭐ Alta | ⭐⭐⭐⭐ Alta |
| **Estándar Industria** | ⭐⭐⭐⭐⭐ Sí | ⭐⭐ No | ⭐⭐⭐⭐ Parcial |
| **Comunicación Precios** | ⭐⭐⭐⭐⭐ Fácil | ⭐⭐ Difícil | ⭐⭐⭐ Media |

---

## 8. Casos de Uso Específicos

### 8.1 Usuario Ocasional

**Escenario:** Usuario que crea 2-3 cotizaciones al mes

**Con Suscripción:**
- Paga $29/mes
- Puede sentirse caro para uso ocasional
- Pero tiene acceso completo

**Con Tokens:**
- Paga solo por uso (~$3-5/mes)
- Más económico
- Pero debe recargar cada vez

**Recomendación:** Plan Free con límites, o Starter con precio más bajo

### 8.2 Usuario Intensivo

**Escenario:** Usuario que crea 100+ cotizaciones al mes

**Con Suscripción:**
- Paga $99/mes (Professional)
- Uso ilimitado
- Predictible

**Con Tokens:**
- Paga ~$50-100/mes (según uso)
- Variable
- Puede ser más económico, pero impredecible

**Recomendación:** Suscripción es mejor (predictibilidad)

### 8.3 Usuario con Alto Uso de IA

**Escenario:** Usuario que hace 500+ consultas IA/mes

**Con Suscripción:**
- Paga $99/mes
- Costo real de IA: $50-100
- Margen negativo para la empresa

**Con Tokens (Híbrido):**
- Paga $99/mes + tokens adicionales
- 100 consultas incluidas
- 400 adicionales: $40-80 en tokens
- Margen positivo

**Recomendación:** Modelo híbrido justificado aquí

---

## 9. Impacto en Desarrollo

### 9.1 Complejidad Adicional

**Backend:**
- +3 modelos de datos
- +5 endpoints
- Middleware de validación
- Integración Stripe adicional
- Sistema de auditoría

**Frontend:**
- UI de balance
- UI de recarga
- Indicadores visuales
- Modales de confirmación
- Historial de transacciones

**Testing:**
- Tests de concurrencia
- Tests de transacciones
- Tests de edge cases
- Tests de integración Stripe

**Tiempo Total:** 3-4 semanas desarrollo + 1 semana testing

### 9.2 Mantenimiento

**Ongoing:**
- Monitoreo de transacciones
- Resolución de disputas
- Soporte de usuarios confundidos
- Ajustes de precios
- Reportes financieros

---

## 10. Conclusión y Siguientes Pasos

### 10.1 Conclusión

**Para Nougram, el sistema de tokens NO es recomendado como modelo principal** debido a:

1. **Naturaleza del producto:** Herramienta de gestión continua
2. **Fricción de usuario:** Interrumpe flujo de trabajo
3. **Modelo actual:** Suscripciones funcionan mejor
4. **Costo-beneficio:** Alto costo de desarrollo, beneficio limitado

**PERO**, puede ser viable para:
- Funcionalidades premium específicas (IA avanzada)
- Usuarios con necesidades muy específicas
- Como complemento a suscripciones (modelo híbrido)

### 10.2 Siguientes Pasos Recomendados

**Corto Plazo (Sprint 7):**
1. ✅ Implementar sistema de suscripciones completo
2. ✅ Definir límites claros por plan
3. ✅ Implementar overage billing opcional
4. ✅ Monitorear uso de funcionalidades costosas (IA)

**Medio Plazo (Post-Sprint 8):**
1. Analizar datos de uso real
2. Identificar funcionalidades con costo variable alto
3. Evaluar demanda de modelo de tokens
4. Si hay demanda, considerar modelo híbrido

**Largo Plazo:**
1. Implementar tokens solo para IA (si es necesario)
2. Evaluar otras funcionalidades premium
3. Ajustar modelo según feedback de usuarios

### 10.3 Métricas para Evaluar

**Si se implementa tokens, medir:**
- Tasa de conversión de recargas
- Frecuencia de recargas
- Abandono por falta de tokens
- Satisfacción del usuario
- Ingresos vs. modelo de suscripción

**Si NO se implementa, monitorear:**
- Uso de funcionalidades costosas (IA)
- Costos operativos por tenant
- Margen por plan
- Feedback de usuarios sobre límites

---

## 11. Referencias y Ejemplos

### 11.1 SaaS con Suscripciones (Éxito)
- Notion
- Slack
- Asana
- Monday.com
- HubSpot

### 11.2 SaaS con Tokens (Casos Específicos)
- OpenAI API (tokens para IA)
- Twilio (tokens para SMS/llamadas)
- SendGrid (tokens para emails)

### 11.3 SaaS Híbridos
- Zapier (plan base + tasks adicionales)
- Stripe (plan base + transaction fees)
- AWS (instancias + uso adicional)

---

**Última actualización:** Diciembre 2025  
**Próxima revisión:** Después de Sprint 7 (implementación de suscripciones)













