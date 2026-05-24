# 📊 Análisis: Cálculo de Margen por Propuesta

**Problema actual:** El margen se calcula por servicio usando `service.default_margin_target`, pero debería configurarse a nivel de propuesta.

---

## 🔍 Estado Actual

### Cálculo Actual (Por Servicio)

**Ubicación:** `backend/app/core/pricing_strategies.py` y `backend/app/core/calculations.py`

**Proceso:**
1. Cada servicio tiene `default_margin_target` (por defecto 40% = 0.40)
2. Para cada item en la propuesta:
   - Se calcula `internal_cost` según el tipo de pricing
   - Se calcula `client_price = internal_cost / (1 - service.default_margin_target)`
3. El margen final de la propuesta es el resultado agregado:
   ```python
   margin_percentage = (total_client_price - total_internal_cost) / total_client_price
   ```

**Ejemplo:**
```
Servicio A: internal_cost = $100, margin_target = 40% → client_price = $166.67
Servicio B: internal_cost = $200, margin_target = 30% → client_price = $285.71
Total: internal_cost = $300, client_price = $452.38, margin = 33.7%
```

**Problema:**
- El margen final no es controlable directamente
- Depende de la combinación de servicios y sus márgenes individuales
- No se puede establecer un margen objetivo para toda la propuesta

---

## ✅ Solución Propuesta: Margen por Propuesta

### Cambios Necesarios

#### 1. Modelo de Base de Datos

**Archivo:** `backend/app/models/project.py`

**Cambio:**
```python
class Quote(Base):
    # ... campos existentes ...
    margin_percentage = Column(Float, nullable=True)  # Margen calculado (resultado)
    target_margin_percentage = Column(Float, nullable=True)  # NUEVO: Margen objetivo de la propuesta
```

#### 2. Schemas

**Archivo:** `backend/app/schemas/quote.py`

**Cambio:**
```python
class QuoteCalculateRequest(BaseModel):
    items: List[QuoteItemRequest]
    tax_ids: List[int] = Field(default_factory=list)
    target_margin_percentage: Optional[float] = Field(None, ge=0, le=1, description="Target margin for the quote (0-1)")
    # ... otros campos ...

class QuoteResponse(BaseModel):
    # ... campos existentes ...
    target_margin_percentage: Optional[float] = None
    margin_percentage: float  # Margen calculado real
```

#### 3. Cálculo de Precios

**Archivo:** `backend/app/core/calculations.py`

**Cambio en `calculate_quote_totals_enhanced`:**
```python
async def calculate_quote_totals_enhanced(
    db: AsyncSession,
    items: List[Dict],
    blended_cost_rate: float,
    tax_ids: List[int] = None,
    expenses: List[Dict] = None,
    target_margin_percentage: Optional[float] = None,  # NUEVO parámetro
    # ... otros parámetros ...
) -> Dict:
    # Calcular total_internal_cost (sin margen)
    total_internal_cost = 0.0
    for item in items:
        # ... calcular internal_cost por item ...
        total_internal_cost += internal_cost
    
    # Calcular expenses cost
    total_expenses_cost = 0.0
    # ... calcular expenses ...
    total_internal_cost += total_expenses_cost
    
    # Calcular total_client_price usando margen de propuesta
    if target_margin_percentage is not None and 0 < target_margin_percentage < 1:
        # Aplicar margen objetivo a toda la propuesta
        total_client_price = total_internal_cost / (1 - target_margin_percentage)
    else:
        # Fallback: usar márgenes individuales de servicios (comportamiento actual)
        total_client_price = 0.0
        for item in items:
            # ... calcular client_price usando service.default_margin_target ...
            total_client_price += client_price
    
    # Calcular margen real
    if total_client_price > 0:
        margin_percentage = (total_client_price - total_internal_cost) / total_client_price
    else:
        margin_percentage = 0.0
    
    return {
        "total_internal_cost": total_internal_cost,
        "total_client_price": total_client_price,
        "margin_percentage": margin_percentage,
        "target_margin_percentage": target_margin_percentage,
        # ... otros campos ...
    }
```

#### 4. Estrategias de Pricing

**Archivo:** `backend/app/core/pricing_strategies.py`

**Cambio:**
- Las estrategias solo calculan `internal_cost`
- El `client_price` se calcula a nivel de propuesta usando `target_margin_percentage`

```python
class HourlyPricingStrategy(PricingStrategy):
    def calculate(
        self,
        item: Dict,
        service: Service,
        blended_cost_rate: float
    ) -> Dict[str, float]:
        # Solo calcular internal_cost
        estimated_hours = item.get("estimated_hours", 0)
        internal_cost = blended_cost_rate * estimated_hours
        
        return {
            "internal_cost": internal_cost,
            "client_price": 0.0  # Se calculará a nivel de propuesta
        }
```

#### 5. Frontend: Campo de Margen en Formulario

**Archivo:** `frontend/src/app/(app)/projects/new/page.tsx`

**Cambio:**
```typescript
const [targetMargin, setTargetMargin] = useState<number>(0.40) // 40% por defecto

// En el formulario:
<div>
  <label>Target Margin (%)</label>
  <Input
    type="number"
    min="0"
    max="100"
    value={(targetMargin * 100).toFixed(1)}
    onChange={(e) => setTargetMargin(parseFloat(e.target.value) / 100)}
  />
</div>

// Al calcular:
const result = await calculateQuoteMutation.mutateAsync({
  items: quoteItems,
  tax_ids: selectedTaxIds,
  target_margin_percentage: targetMargin,  // NUEVO
})
```

---

## 📋 Flujo Propuesto

### 1. Creación de Propuesta

1. Usuario agrega servicios a la propuesta
2. Usuario configura margen objetivo (ej: 40%)
3. Sistema calcula:
   - `total_internal_cost` = suma de costos internos de todos los servicios
   - `total_client_price` = `total_internal_cost / (1 - target_margin_percentage)`
   - `margin_percentage` = margen real calculado

### 2. Cálculo por Item

**Opción A: Distribución Proporcional**
- Cada item recibe un precio proporcional basado en su costo interno
- `item.client_price = (item.internal_cost / total_internal_cost) * total_client_price`

**Opción B: Mantener Precios Individuales**
- Los items mantienen sus precios calculados con margen de servicio
- El margen de propuesta se aplica como ajuste global

**Recomendación:** Opción A (distribución proporcional) es más simple y consistente.

---

## 🎯 Beneficios

1. **Control Directo:** El usuario puede establecer el margen objetivo de toda la propuesta
2. **Simplicidad:** No necesita ajustar márgenes por servicio
3. **Flexibilidad:** Puede cambiar el margen sin modificar servicios individuales
4. **Consistencia:** Todas las propuestas pueden tener el mismo margen objetivo

---

## ⚠️ Consideraciones

1. **Compatibilidad:** Mantener fallback al comportamiento actual si no se especifica `target_margin_percentage`
2. **Servicios:** Los servicios pueden mantener `default_margin_target` como valor por defecto
3. **UI:** Agregar campo de margen objetivo en el formulario de creación de propuesta
4. **Validación:** Validar que `target_margin_percentage` esté entre 0 y 1 (0% y 100%)

---

## 📝 Plan de Implementación

### Fase 1: Backend
1. ✅ Agregar `target_margin_percentage` al modelo `Quote`
2. ✅ Modificar `calculate_quote_totals_enhanced` para aceptar `target_margin_percentage`
3. ✅ Actualizar estrategias de pricing para solo calcular `internal_cost`
4. ✅ Actualizar schemas y endpoints

### Fase 2: Frontend
1. ✅ Agregar campo de margen objetivo en formulario de propuesta
2. ✅ Actualizar llamadas al endpoint de cálculo
3. ✅ Mostrar margen objetivo y margen real en la UI

### Fase 3: Migración
1. ✅ Crear migración para agregar `target_margin_percentage` a tabla `quotes`
2. ✅ Actualizar datos existentes si es necesario

---

**Última actualización:** 30 de Diciembre, 2025

