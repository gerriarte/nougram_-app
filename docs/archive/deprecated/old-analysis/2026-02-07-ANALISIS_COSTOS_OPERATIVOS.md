# 🔍 Análisis: Problemas con Cálculos de Costos Operativos

**Problema reportado:** Los costos de operación de la empresa no se muestran correctamente.

---

## 📊 Estado Actual del Sistema

### Datos Configurados:
- **Miembros del equipo:** 1 activo
  - Salario: 500,000 COP/mes → 125 USD/mes (normalizado)
  - Horas facturables/semana: 40
  - Horas facturables/mes: 173.20
- **Costos fijos:** 1 costo
  - Monto: 10,900 USD/mes
  - Categoría: "general" (no reconocida)
- **Blended Cost Rate calculado:** 63.65 USD/hora

### Cálculo Correcto:
```
Total Costos Mensuales = Salarios + Costos Fijos
Total Costos Mensuales = 125 + 10,900 = 11,025 USD

Blended Cost Rate = Total Costos / Total Horas
Blended Cost Rate = 11,025 / 173.20 = 63.65 USD/hora
```

---

## 🐛 Problemas Identificados

### Problema 1: Inconsistencia en Cálculo de Horas

**Ubicación:** `backend/app/api/v1/endpoints/costs.py` línea 485

**Problema:**
El endpoint `/calculations/agency-cost-hour` calcula las horas sin considerar `non_billable_hours_percentage`:

```python
# Línea 485 - INCORRECTO
total_hours = sum(member.billable_hours_per_week * 4.33 for member in team_members)
```

Pero la función `calculate_blended_cost_rate()` sí lo considera:

```python
# Línea 122 en calculations.py - CORRECTO
hours_per_month = sum(
    member.billable_hours_per_week * 4.33 * (1 - (getattr(member, 'non_billable_hours_percentage', 0.0) or 0.0))
    for member in team_members
)
```

**Impacto:**
- Si un miembro tiene `non_billable_hours_percentage > 0`, el endpoint mostrará más horas de las reales
- Esto causará que el BCR mostrado sea menor que el real
- Los valores en el frontend no coincidirán con los cálculos reales

**Solución:**
Aplicar el mismo cálculo que en `calculate_blended_cost_rate()`:

```python
total_hours = sum(
    member.billable_hours_per_week * 4.33 * (1 - (member.non_billable_hours_percentage or 0.0))
    for member in team_members
)
```

---

### Problema 2: Categorización de Costos Fijos

**Ubicación:** `backend/app/api/v1/endpoints/costs.py` línea 437-443

**Problema:**
La categorización busca keywords en minúsculas pero no reconoce todas las categorías:

```python
category_lower = (cost.category or "").lower()
is_tool = any(keyword in category_lower for keyword in ['software', 'saas', 'herramienta', 'tool', 'licencia'])
```

**Categorías no reconocidas:**
- "general" → Se cuenta como Overhead (correcto por defecto)
- "Overhead" → Se cuenta como Overhead (correcto)
- Pero falta validación explícita

**Impacto:**
- Costos con categorías no estándar pueden no categorizarse correctamente
- La separación entre Overhead y Tools puede ser incorrecta

**Solución:**
Mejorar la lógica de categorización:

```python
# Categorías explícitas para Tools/SaaS
tools_keywords = ['software', 'saas', 'herramienta', 'tool', 'licencia', 'license', 'subscription', 'suscripcion']
# Categorías explícitas para Overhead
overhead_keywords = ['overhead', 'infrastructure', 'office', 'utilities', 'rent', 'alquiler', 'general']

category_lower = (cost.category or "").lower()
is_tool = any(keyword in category_lower for keyword in tools_keywords)
is_overhead = any(keyword in category_lower for keyword in overhead_keywords)

if is_tool:
    total_tools_costs += normalized
elif is_overhead or not is_tool:  # Por defecto, si no es tool, es overhead
    total_fixed_overhead += normalized
```

---

### Problema 3: Normalización de Monedas en Salarios

**Ubicación:** `backend/app/api/v1/endpoints/costs.py` línea 475-481

**Problema:**
El endpoint aplica el multiplicador de cargas sociales ANTES de normalizar:

```python
# Línea 475 - Aplica multiplicador antes de normalizar
real_monthly_cost = member.salary_monthly_brute * social_charges_multiplier

# Línea 477-481 - Normaliza después
normalized = normalize_to_primary_currency(
    real_monthly_cost,
    member.currency or "USD",
    primary_currency
)
```

Pero en `calculate_blended_cost_rate()` se normaliza PRIMERO y luego se aplica el multiplicador:

```python
# Línea 110-114 - Normaliza primero
normalized = normalize_to_primary_currency(
    member.salary_monthly_brute,
    member_currency,
    primary_currency
)
# Línea 116 - Aplica multiplicador después
normalized_with_charges = normalized * social_charges_multiplier
```

**Impacto:**
- Si hay diferentes monedas, el orden importa
- Puede haber pequeñas diferencias por redondeo
- Los valores pueden no coincidir exactamente

**Solución:**
Normalizar primero, luego aplicar multiplicador (como en `calculate_blended_cost_rate()`):

```python
# Normalizar primero
normalized = normalize_to_primary_currency(
    member.salary_monthly_brute,
    member.currency or "USD",
    primary_currency
)
# Aplicar multiplicador después
real_monthly_cost = normalized * social_charges_multiplier
total_salaries += real_monthly_cost
```

---

### Problema 4: Falta de Validación de Datos

**Problema:**
No hay validación de que los valores sean razonables antes de mostrar:

- Salarios negativos o cero
- Horas facturables cero o negativas
- Costos fijos negativos
- BCR infinito o NaN

**Solución:**
Agregar validaciones y valores por defecto:

```python
# Validar horas
if total_hours <= 0:
    logger.warning("Total billable hours is zero or negative")
    total_hours = 0.0

# Validar salarios
if total_salaries < 0:
    logger.warning("Total salaries is negative")
    total_salaries = 0.0

# Validar BCR
if not (0 <= blended_rate < float('inf')):
    logger.error(f"Invalid blended cost rate: {blended_rate}")
    blended_rate = 0.0
```

---

## 🔧 Correcciones Propuestas

### Corrección 1: Unificar Cálculo de Horas

**Archivo:** `backend/app/api/v1/endpoints/costs.py`

**Cambio:**
```python
# ANTES (línea 485)
total_hours = sum(member.billable_hours_per_week * 4.33 for member in team_members)

# DESPUÉS
total_hours = sum(
    member.billable_hours_per_week * 4.33 * (1 - (member.non_billable_hours_percentage or 0.0))
    for member in team_members
)
```

### Corrección 2: Mejorar Categorización

**Archivo:** `backend/app/api/v1/endpoints/costs.py`

**Cambio:**
```python
# ANTES (línea 437-443)
category_lower = (cost.category or "").lower()
is_tool = any(keyword in category_lower for keyword in ['software', 'saas', 'herramienta', 'tool', 'licencia'])

if is_tool:
    total_tools_costs += normalized
else:
    total_fixed_overhead += normalized

# DESPUÉS
tools_keywords = ['software', 'saas', 'herramienta', 'tool', 'licencia', 'license', 'subscription', 'suscripcion']
overhead_keywords = ['overhead', 'infrastructure', 'office', 'utilities', 'rent', 'alquiler', 'general', 'otro']

category_lower = (cost.category or "").lower()
is_tool = any(keyword in category_lower for keyword in tools_keywords)
is_overhead = any(keyword in category_lower for keyword in overhead_keywords)

if is_tool:
    total_tools_costs += normalized
elif is_overhead or not is_tool:  # Por defecto es overhead
    total_fixed_overhead += normalized
```

### Corrección 3: Corregir Orden de Normalización

**Archivo:** `backend/app/api/v1/endpoints/costs.py`

**Cambio:**
```python
# ANTES (línea 475-481)
for member in team_members:
    real_monthly_cost = member.salary_monthly_brute * social_charges_multiplier
    normalized = normalize_to_primary_currency(
        real_monthly_cost,
        member.currency or "USD",
        primary_currency
    )
    total_salaries += normalized

# DESPUÉS
for member in team_members:
    # Normalizar primero
    normalized = normalize_to_primary_currency(
        member.salary_monthly_brute,
        member.currency or "USD",
        primary_currency
    )
    # Aplicar multiplicador después
    real_monthly_cost = normalized * social_charges_multiplier
    total_salaries += real_monthly_cost
```

---

## 📋 Checklist de Verificación

Después de aplicar las correcciones, verificar:

- [ ] El BCR mostrado coincide con el calculado por `calculate_blended_cost_rate()`
- [ ] Las horas mostradas consideran `non_billable_hours_percentage`
- [ ] Los costos se categorizan correctamente (Overhead vs Tools)
- [ ] Los salarios se normalizan correctamente antes de aplicar cargas sociales
- [ ] Los valores en el frontend coinciden con los del backend
- [ ] No hay valores negativos o infinitos
- [ ] Las monedas se convierten correctamente

---

## 🎯 Próximos Pasos

1. **Aplicar correcciones** en el endpoint `/calculations/agency-cost-hour`
2. **Agregar tests** para verificar los cálculos
3. **Validar** que los valores se muestren correctamente en el frontend
4. **Documentar** las categorías válidas para costos fijos

---

**Última actualización:** 30 de Diciembre, 2025

