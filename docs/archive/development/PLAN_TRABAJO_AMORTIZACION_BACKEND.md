# Plan de Trabajo - Implementación de Amortización de Equipos (Backend)

**Versión:** 2.0  
**Fecha:** 2026-01-25  
**Objetivo:** Implementar soporte completo para amortización de equipos en el backend, alineado con los requerimientos de UI especificados en `UI_REQUIREMENTS_EQUIPMENT_AMORTIZATION.md`

**Estado:** ❌ NO IMPLEMENTADO - Este plan detalla la implementación completa del módulo

---

## Resumen Ejecutivo

Este plan detalla la implementación del módulo de amortización de equipos que permitirá:
- Registrar equipos con información de compra y parámetros de depreciación
- Calcular automáticamente la amortización mensual usando diferentes métodos
- Integrar la amortización en el cálculo del Blended Cost Rate (BCR)
- Proporcionar endpoints RESTful para CRUD completo

---

## 1. ANÁLISIS DE REQUERIMIENTOS

### 1.1 Requerimientos del Frontend (UI_REQUIREMENTS_EQUIPMENT_AMORTIZATION.md)

```typescript
interface EquipmentAmortizationCreate {
  // Información Básica
  name: string;                        // Nombre del equipo (requerido, min 1 carácter)
  description?: string;                // Descripción (opcional)
  category: "Hardware" | "Software" | "Vehicles" | "Office Equipment";  // Categoría (requerido)
  
  // Información de Compra
  purchase_price: string;              // Precio de compra (Decimal como string, requerido, > 0)
  purchase_date: string;                // Fecha de compra (ISO 8601: YYYY-MM-DD, requerido, no futura)
  currency: "USD" | "COP" | "EUR" | "ARS";  // Moneda de compra (requerido, default: "USD")
  exchange_rate_at_purchase?: string;   // TRM del día de compra (Decimal como string, opcional, requerido si currency != primary_currency)
  
  // Parámetros de Depreciación
  useful_life_months: number;          // Vida útil en meses (requerido, > 0, típicamente 12-120)
  salvage_value: string;               // Valor de salvamento (Decimal como string, requerido, >= 0, < purchase_price)
  depreciation_method: "straight_line" | "declining_balance";  // Método de depreciación (requerido, default: "straight_line")
  
  // Estado
  is_active?: boolean;                 // Si está activo y generando depreciación (default: true)
}
```

**NUEVOS REQUERIMIENTOS (v2.0):**
- ✅ Campo `exchange_rate_at_purchase` para TRM histórica (crítico para precisión)
- ✅ Validación: `purchase_date` no puede ser futura
- ✅ Validación: `salvage_value < purchase_price`
- ✅ Validación condicional: `exchange_rate_at_purchase` requerido si `currency !== primary_currency`
- ✅ Campos calculados adicionales: `months_depreciated`, `months_remaining`, `percentage_depreciated`

### 1.2 Requerimientos Funcionales

1. **Modelo de Datos:**
   - Crear tabla `equipment_amortization` con todos los campos necesarios
   - Soporte multi-tenant (organization_id)
   - Soft delete
   - Campos de auditoría (created_at, updated_at, deleted_at, deleted_by_id)

2. **Cálculo de Amortización:**
   - Método línea recta: `(purchase_price - salvage_value) / useful_life_months`
   - Método saldo decreciente: Implementar fórmula estándar
   - Calcular automáticamente `monthly_depreciation` al crear/actualizar

3. **Integración con BCR:**
   - La amortización mensual debe sumarse a los gastos fijos en el cálculo del BCR
   - Categorizar equipos como "Overhead" o "Tools" según su categoría

4. **Endpoints API:**
   - `GET /api/v1/settings/equipment` - Listar equipos
   - `POST /api/v1/settings/equipment` - Crear equipo
   - `GET /api/v1/settings/equipment/{id}` - Obtener equipo
   - `PUT /api/v1/settings/equipment/{id}` - Actualizar equipo
   - `DELETE /api/v1/settings/equipment/{id}` - Eliminar equipo (soft delete)
   - `GET /api/v1/settings/equipment/{id}/depreciation-schedule` - Ver cronograma de depreciación

---

## 2. ARQUITECTURA Y DISEÑO

### 2.1 Modelo de Datos

```python
class EquipmentAmortization(Base):
    """
    Equipment amortization model
    ESTÁNDAR NOUGRAM: Campos monetarios usan Numeric para precisión grado bancario
    """
    __tablename__ = "equipment_amortization"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    category = Column(String, nullable=False)  # "Hardware", "Software", "Vehicles", "Office Equipment"
    
    # Purchase information
    purchase_price = Column(Numeric(precision=19, scale=4), nullable=False)  # ESTÁNDAR NOUGRAM: Numeric
    purchase_date = Column(DateTime(timezone=True), nullable=False)
    currency = Column(String, default="USD", nullable=False)  # USD, COP, ARS, EUR
    exchange_rate_at_purchase = Column(Numeric(precision=19, scale=4), nullable=True)  # ESTÁNDAR NOUGRAM: TRM histórica (requerido si currency != primary_currency)
    
    # Depreciation parameters
    useful_life_months = Column(Integer, nullable=False)  # Vida útil en meses
    salvage_value = Column(Numeric(precision=19, scale=4), nullable=False, default=0)  # ESTÁNDAR NOUGRAM: Numeric
    depreciation_method = Column(String, nullable=False, default="straight_line")  # "straight_line", "declining_balance"
    
    # Calculated fields (read-only, calculated on save/update)
    monthly_depreciation = Column(Numeric(precision=19, scale=4), nullable=True)  # ESTÁNDAR NOUGRAM: Numeric - Depreciación mensual
    total_depreciated = Column(Numeric(precision=19, scale=4), nullable=True, default=0)  # ESTÁNDAR NOUGRAM: Numeric - Depreciación acumulada hasta la fecha
    remaining_value = Column(Numeric(precision=19, scale=4), nullable=True)  # ESTÁNDAR NOUGRAM: Numeric - Valor en libros actual
    
    # Computed fields (calculados dinámicamente, no almacenados)
    # months_depreciated: Calculado como diferencia entre purchase_date y fecha actual
    # months_remaining: Calculado como useful_life_months - months_depreciated
    # percentage_depreciated: Calculado como (total_depreciated / depreciable_base) × 100
    
    # Status
    is_active = Column(Boolean, default=True)  # Si está activo y generando depreciación
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Relationships
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])
```

### 2.2 Servicio de Cálculo de Amortización

```python
class DepreciationService:
    """
    Service for calculating equipment depreciation
    """
    
    @staticmethod
    def calculate_straight_line(
        purchase_price: Decimal,
        salvage_value: Decimal,
        useful_life_months: int
    ) -> Decimal:
        """
        Calculate monthly depreciation using straight-line method
        Formula: (purchase_price - salvage_value) / useful_life_months
        """
        if useful_life_months <= 0:
            return Decimal('0')
        depreciable_amount = purchase_price - salvage_value
        return depreciable_amount / Decimal(str(useful_life_months))
    
    @staticmethod
    def calculate_declining_balance(
        purchase_price: Decimal,
        salvage_value: Decimal,
        useful_life_months: int,
        depreciation_rate: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate monthly depreciation using declining balance method
        Default rate: 2x straight-line rate (double declining balance)
        Formula: (book_value * depreciation_rate) / 12
        """
        if useful_life_months <= 0:
            return Decimal('0')
        
        # Calculate straight-line rate
        straight_line_rate = Decimal('1') / Decimal(str(useful_life_months))
        
        # Use 2x rate for double declining balance (or custom rate)
        if depreciation_rate is None:
            depreciation_rate = straight_line_rate * Decimal('2')
        
        # For declining balance, we need current book value
        # First month: use purchase_price
        # Subsequent months: use remaining_value
        # This will be calculated per month in the schedule
        monthly_rate = depreciation_rate / Decimal('12')
        return purchase_price * monthly_rate
    
    @staticmethod
    def generate_depreciation_schedule(
        equipment: EquipmentAmortization,
        months: int = None,
        include_past_months: bool = True
    ) -> List[Dict]:
        """
        Generate depreciation schedule for equipment
        Returns list of monthly depreciation entries with dates
        
        Args:
            equipment: EquipmentAmortization instance
            months: Number of months to calculate (default: useful_life_months)
            include_past_months: Include months that have already passed (default: True)
        
        Returns:
            List of dicts with: month, month_date, depreciation, accumulated_depreciation, 
            book_value, percentage_depreciated
        """
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        schedule = []
        current_value = equipment.purchase_price
        total_depreciated = Decimal('0')
        depreciable_base = equipment.purchase_price - equipment.salvage_value
        
        # Determine number of months to calculate
        if months is None:
            months = equipment.useful_life_months
        
        # Calculate start date (purchase_date)
        purchase_date = equipment.purchase_date
        if isinstance(purchase_date, str):
            purchase_date = datetime.fromisoformat(purchase_date.replace('Z', '+00:00'))
        
        # Calculate current date for filtering past months
        current_date = datetime.now(purchase_date.tzinfo) if purchase_date.tzinfo else datetime.now()
        
        for month_num in range(1, months + 1):
            # Calculate date for this month
            month_date = purchase_date + relativedelta(months=month_num-1)
            
            # Skip past months if include_past_months is False
            if not include_past_months and month_date < current_date:
                # Still update current_value and total_depreciated for accuracy
                if equipment.depreciation_method == "straight_line":
                    monthly_dep = DepreciationService.calculate_straight_line(
                        equipment.purchase_price,
                        equipment.salvage_value,
                        equipment.useful_life_months
                    )
                else:
                    # Declining balance calculation
                    straight_line_rate = Decimal('1') / Decimal(str(equipment.useful_life_months))
                    depreciation_rate = straight_line_rate * Decimal('2')
                    monthly_rate = depreciation_rate / Decimal('12')
                    monthly_dep = current_value * monthly_rate
                    if current_value - monthly_dep < equipment.salvage_value:
                        monthly_dep = current_value - equipment.salvage_value
                
                total_depreciated += monthly_dep
                current_value -= monthly_dep
                continue
            
            # Calculate depreciation for this month
            if equipment.depreciation_method == "straight_line":
                monthly_dep = DepreciationService.calculate_straight_line(
                    equipment.purchase_price,
                    equipment.salvage_value,
                    equipment.useful_life_months
                )
            else:  # declining_balance
                # For declining balance, recalculate each month based on current book value
                straight_line_rate = Decimal('1') / Decimal(str(equipment.useful_life_months))
                depreciation_rate = straight_line_rate * Decimal('2')  # Double declining
                monthly_rate = depreciation_rate / Decimal('12')
                monthly_dep = current_value * monthly_rate
                
                # Don't depreciate below salvage value
                if current_value - monthly_dep < equipment.salvage_value:
                    monthly_dep = current_value - equipment.salvage_value
            
            total_depreciated += monthly_dep
            current_value -= monthly_dep
            
            # Calculate percentage depreciated
            percentage_depreciated = 0.0
            if depreciable_base > 0:
                percentage_depreciated = float((total_depreciated / depreciable_base) * 100)
            
            schedule.append({
                "month": month_num,
                "month_date": month_date.isoformat(),  # ISO 8601 format
                "depreciation": float(monthly_dep),
                "accumulated_depreciation": float(total_depreciated),
                "book_value": float(current_value),
                "percentage_depreciated": percentage_depreciated
            })
            
            # Stop if we've reached salvage value
            if current_value <= equipment.salvage_value:
                break
        
        return schedule
    
    @staticmethod
    def calculate_depreciation_progress(
        equipment: EquipmentAmortization
    ) -> Dict:
        """
        Calculate current depreciation progress for equipment
        
        Returns:
            Dict with: months_depreciated, months_remaining, percentage_depreciated,
            total_depreciated, remaining_value
        """
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        purchase_date = equipment.purchase_date
        if isinstance(purchase_date, str):
            purchase_date = datetime.fromisoformat(purchase_date.replace('Z', '+00:00'))
        
        current_date = datetime.now(purchase_date.tzinfo) if purchase_date.tzinfo else datetime.now()
        
        # Calculate months since purchase
        months_depreciated = 0
        if current_date > purchase_date:
            delta = relativedelta(current_date, purchase_date)
            months_depreciated = delta.years * 12 + delta.months
        
        # Cap at useful_life_months
        months_depreciated = min(months_depreciated, equipment.useful_life_months)
        months_remaining = max(0, equipment.useful_life_months - months_depreciated)
        
        # Calculate total depreciated and remaining value
        depreciable_base = equipment.purchase_price - equipment.salvage_value
        
        if equipment.depreciation_method == "straight_line":
            monthly_dep = DepreciationService.calculate_straight_line(
                equipment.purchase_price,
                equipment.salvage_value,
                equipment.useful_life_months
            )
            total_depreciated = monthly_dep * Decimal(str(months_depreciated))
        else:
            # For declining balance, need to calculate month by month
            # Use schedule generation for accuracy
            schedule = DepreciationService.generate_depreciation_schedule(
                equipment,
                months=months_depreciated,
                include_past_months=True
            )
            if schedule:
                total_depreciated = Decimal(str(schedule[-1]["accumulated_depreciation"]))
            else:
                total_depreciated = Decimal('0')
        
        # Cap total_depreciated at depreciable_base
        total_depreciated = min(total_depreciated, depreciable_base)
        remaining_value = equipment.purchase_price - total_depreciated
        
        # Ensure remaining_value doesn't go below salvage_value
        remaining_value = max(remaining_value, equipment.salvage_value)
        
        # Calculate percentage
        percentage_depreciated = 0.0
        if depreciable_base > 0:
            percentage_depreciated = float((total_depreciated / depreciable_base) * 100)
        
        return {
            "months_depreciated": months_depreciated,
            "months_remaining": months_remaining,
            "percentage_depreciated": percentage_depreciated,
            "total_depreciated": float(total_depreciated),
            "remaining_value": float(remaining_value)
        }
```

### 2.3 Integración con BCR

Modificar `calculate_blended_cost_rate` en `backend/app/core/calculations.py`:

```python
# Agregar después de obtener fixed_costs:
# Get equipment amortization costs
from app.models.equipment import EquipmentAmortization
equipment_query = select(EquipmentAmortization).where(
    EquipmentAmortization.deleted_at.is_(None),
    EquipmentAmortization.is_active == True
)
if tenant_id is not None:
    equipment_query = equipment_query.where(
        EquipmentAmortization.organization_id == tenant_id
    )
equipment_result = await db.execute(equipment_query)
equipment_list = equipment_result.scalars().all()

# Convert equipment monthly depreciation to Money
# IMPORTANTE: Usar TRM histórica (exchange_rate_at_purchase) si existe
equipment_costs_money = []
for equipment in equipment_list:
    equipment_currency = equipment.currency or "USD"
    monthly_dep = equipment.monthly_depreciation or Decimal('0')
    
    # Si el equipo tiene TRM histórica y la moneda es diferente a la principal,
    # usar la TRM histórica para conversión (sin re-expresión mensual)
    if equipment.exchange_rate_at_purchase and equipment_currency != primary_currency:
        # Convertir usando TRM histórica
        if equipment_currency == "USD" and primary_currency == "COP":
            # USD a COP usando TRM histórica
            monthly_dep_primary = monthly_dep * equipment.exchange_rate_at_purchase
        elif equipment_currency == "COP" and primary_currency == "USD":
            # COP a USD usando TRM histórica (inversa)
            monthly_dep_primary = monthly_dep / equipment.exchange_rate_at_purchase
        else:
            # Para otras combinaciones, usar normalize_to_primary_currency con TRM histórica
            # Nota: Esto requiere modificar normalize_to_primary_currency para aceptar TRM histórica
            monthly_dep_primary = normalize_to_primary_currency(
                monthly_dep,
                equipment_currency,
                primary_currency,
                historical_exchange_rate=equipment.exchange_rate_at_purchase
            )
    else:
        # Sin TRM histórica o misma moneda, usar conversión estándar
        normalized = normalize_to_primary_currency(
            monthly_dep,
            equipment_currency,
            primary_currency
        )
        monthly_dep_primary = normalized
    
    # Convertir a Money
    if isinstance(monthly_dep_primary, Money):
        equipment_costs_money.append(monthly_dep_primary)
    else:
        equipment_costs_money.append(Money(monthly_dep_primary, primary_currency))

# Add equipment costs to fixed costs
all_costs = fixed_costs_money + salary_amounts + equipment_costs_money
```

---

## 3. PLAN DE IMPLEMENTACIÓN

### Fase 1: Modelo y Migración de Base de Datos

#### Tarea 1.1: Crear Modelo EquipmentAmortization
**Archivo:** `backend/app/models/equipment.py`

**Pasos:**
1. Crear nuevo archivo `equipment.py` en `backend/app/models/`
2. Definir clase `EquipmentAmortization` con todos los campos especificados
3. Agregar relaciones con `User` y `Organization`
4. Agregar métodos helper para cálculos

**Criterios de Aceptación:**
- [ ] Modelo creado con todos los campos requeridos
- [ ] Campos monetarios usan `Numeric(precision=19, scale=4)`
- [ ] Soporte multi-tenant (organization_id)
- [ ] Soft delete implementado
- [ ] Relaciones definidas correctamente

#### Tarea 1.2: Crear Migración de Alembic
**Archivo:** `backend/alembic/versions/XXXX_add_equipment_amortization.py`

**Pasos:**
1. Generar migración: `alembic revision -m "add_equipment_amortization"`
2. Crear tabla `equipment_amortization` con todos los campos
3. Crear índices necesarios:
   - `ix_equipment_amortization_id`
   - `ix_equipment_amortization_organization_id`
   - `ix_equipment_amortization_category`
   - `ix_equipment_amortization_deleted_at`
4. Crear foreign keys:
   - `organization_id` → `organizations.id`
   - `deleted_by_id` → `users.id`

**Criterios de Aceptación:**
- [ ] Migración creada y probada
- [ ] Tabla creada correctamente
- [ ] Índices creados
- [ ] Foreign keys creados
- [ ] Migración es reversible (downgrade funciona)

#### Tarea 1.3: Registrar Modelo en __init__.py
**Archivo:** `backend/app/models/__init__.py`

**Pasos:**
1. Importar `EquipmentAmortization`
2. Agregar a `__all__` si existe

**Criterios de Aceptación:**
- [ ] Modelo importado correctamente
- [ ] No hay errores de importación circular

---

### Fase 2: Schemas y Validaciones

#### Tarea 2.1: Crear Schemas Pydantic
**Archivo:** `backend/app/schemas/equipment.py`

**Schemas a crear:**
1. `EquipmentAmortizationBase` - Campos base
2. `EquipmentAmortizationCreate` - Para crear (con validación de TRM)
3. `EquipmentAmortizationUpdate` - Para actualizar (todos opcionales)
4. `EquipmentAmortizationResponse` - Para respuesta (incluye campos calculados: months_depreciated, months_remaining, percentage_depreciated)
5. `EquipmentAmortizationListResponse` - Para lista paginada
6. `DepreciationScheduleResponse` - Para cronograma de depreciación (con fechas específicas)
7. `DepreciationScheduleEntry` - Entrada del cronograma (mes, fecha, depreciación, acumulada, valor en libros, porcentaje)

**Características:**
- Campos monetarios serializados como string (Decimal)
- Validaciones: purchase_price > 0, salvage_value >= 0 y < purchase_price, useful_life_months > 0
- Validación de fecha: purchase_date debe ser fecha válida y **no futura**
- Validación de método: solo "straight_line" o "declining_balance"
- Validación condicional: exchange_rate_at_purchase requerido si currency != primary_currency
- Validación de categoría: solo "Hardware", "Software", "Vehicles", "Office Equipment"

**Criterios de Aceptación:**
- [ ] Todos los schemas creados
- [ ] Validaciones implementadas
- [ ] Serialización Decimal como string funciona
- [ ] Schemas pasan validación de Pydantic

#### Tarea 2.2: Crear Servicio de Cálculo
**Archivo:** `backend/app/services/depreciation_service.py`

**Pasos:**
1. Crear clase `DepreciationService`
2. Implementar `calculate_straight_line`
3. Implementar `calculate_declining_balance`
4. Implementar `generate_depreciation_schedule` (con fechas y porcentajes)
5. Implementar `calculate_depreciation_progress` (para barras de vida útil)
6. Agregar tests unitarios

**Criterios de Aceptación:**
- [ ] Método línea recta calcula correctamente
- [ ] Método saldo decreciente calcula correctamente
- [ ] Cronograma se genera correctamente con fechas ISO 8601
- [ ] Cronograma incluye porcentaje depreciado por mes
- [ ] No se deprecia por debajo del valor de salvamento
- [ ] `calculate_depreciation_progress` calcula meses transcurridos correctamente
- [ ] `calculate_depreciation_progress` calcula porcentaje depreciado correctamente
- [ ] Tests unitarios pasan

---

### Fase 3: Repository Layer

#### Tarea 3.1: Crear EquipmentRepository
**Archivo:** `backend/app/repositories/equipment_repository.py`

**Métodos a implementar:**
- `get_all_active()` - Obtener equipos activos
- `get_by_category()` - Filtrar por categoría
- `get_by_depreciation_method()` - Filtrar por método
- `get_active_equipment_for_bcr()` - Obtener equipos activos para cálculo BCR

**Criterios de Aceptación:**
- [ ] Repository hereda de `BaseRepository`
- [ ] Tenant scoping funciona correctamente
- [ ] Soft delete respetado
- [ ] Métodos de filtrado funcionan

#### Tarea 3.2: Registrar Repository en Factory
**Archivo:** `backend/app/repositories/factory.py`

**Pasos:**
1. Agregar método `create_equipment_repository`
2. Importar `EquipmentRepository`

**Criterios de Aceptación:**
- [ ] Factory puede crear instancia de repository
- [ ] Tenant scoping aplicado automáticamente

---

### Fase 4: Endpoints API

#### Tarea 4.1: Crear Endpoints CRUD
**Archivo:** `backend/app/api/v1/endpoints/equipment.py`

**Endpoints a crear:**
1. `GET /api/v1/settings/equipment` - Listar equipos (con paginación, filtros por categoría)
2. `POST /api/v1/settings/equipment` - Crear equipo (con validación de TRM)
3. `GET /api/v1/settings/equipment/{id}` - Obtener equipo por ID (incluye campos calculados)
4. `PUT /api/v1/settings/equipment/{id}` - Actualizar equipo (recalcula depreciación)
5. `DELETE /api/v1/settings/equipment/{id}` - Eliminar equipo (soft delete)
6. `POST /api/v1/settings/equipment/{id}/restore` - Restaurar equipo
7. `GET /api/v1/settings/equipment/{id}/depreciation-schedule` - Cronograma de depreciación (con query param `months` opcional)
8. `GET /api/v1/settings/equipment/{id}/progress` - Progreso actual de depreciación (meses, porcentaje, etc.)

**Características:**
- Permisos: Requiere `can_modify_costs` para crear/editar/eliminar
- Validaciones: Todos los campos requeridos validados
  - `purchase_date` no puede ser futura
  - `salvage_value < purchase_price`
  - `exchange_rate_at_purchase` requerido si `currency != primary_currency`
- Cálculo automático: `monthly_depreciation` se calcula al guardar
- Cálculo de progreso: `months_depreciated`, `months_remaining`, `percentage_depreciated` se calculan dinámicamente
- Cache invalidation: Invalidar cache de BCR al crear/editar/eliminar
- Respuesta incluye campos calculados para UI (barra de vida útil, gráfico de valor)

**Criterios de Aceptación:**
- [ ] Todos los endpoints creados
- [ ] Permisos aplicados correctamente
- [ ] Validaciones funcionan
- [ ] Cálculo de amortización automático
- [ ] Cache de BCR se invalida
- [ ] Respuestas en formato correcto (Decimal como string)

#### Tarea 4.2: Registrar Router
**Archivo:** `backend/app/api/v1/router.py`

**Pasos:**
1. Importar router de equipment
2. Agregar `api_router.include_router(equipment.router, prefix="/settings", tags=["equipment"])`

**Criterios de Aceptación:**
- [ ] Router registrado correctamente
- [ ] Endpoints accesibles en `/api/v1/settings/equipment`

---

### Fase 5: Integración con BCR

#### Tarea 5.1: Modificar calculate_blended_cost_rate
**Archivo:** `backend/app/core/calculations.py`

**Pasos:**
1. Importar `EquipmentAmortization`
2. Agregar query para obtener equipos activos (solo no eliminados y `is_active=True`)
3. Convertir `monthly_depreciation` a Money usando TRM histórica si existe
4. Agregar a `all_costs` antes de calcular BCR
5. Categorizar equipos:
   - Hardware, Vehicles, Office Equipment → Overhead
   - Software → Tools/SaaS
6. Actualizar desglose en respuesta (agregar `total_equipment_depreciation`)
7. Actualizar `BlendedCostRateResponse` para incluir breakdown de equipos

**Criterios de Aceptación:**
- [ ] Equipos se incluyen en cálculo de BCR
- [ ] Amortización mensual se suma correctamente
- [ ] Normalización de moneda funciona
- [ ] Desglose incluye equipos
- [ ] Tests de cálculo pasan

#### Tarea 5.2: Actualizar BlendedCostRateResponse
**Archivo:** `backend/app/schemas/quote.py`

**Pasos:**
1. Agregar campo `total_equipment_depreciation` a `BlendedCostRateResponse`
2. Agregar campo `equipment_breakdown` (opcional) con lista de equipos y su depreciación mensual
3. Serializar como Decimal string
4. Incluir categorización (Overhead vs Tools)

**Criterios de Aceptación:**
- [ ] Campo agregado al schema
- [ ] Serialización funciona correctamente
- [ ] Frontend puede leer el valor

---

### Fase 6: Tests

#### Tarea 6.1: Tests Unitarios del Servicio
**Archivo:** `backend/tests/unit/test_depreciation_service.py`

**Tests a crear:**
1. `test_calculate_straight_line_basic` - Cálculo básico línea recta
2. `test_calculate_straight_line_with_salvage` - Con valor de salvamento
3. `test_calculate_declining_balance_basic` - Cálculo básico saldo decreciente
4. `test_generate_depreciation_schedule_straight_line` - Cronograma línea recta con fechas
5. `test_generate_depreciation_schedule_declining_balance` - Cronograma saldo decreciente con fechas
6. `test_depreciation_below_salvage_value` - No deprecia por debajo de salvamento
7. `test_calculate_depreciation_progress` - Cálculo de progreso (meses, porcentaje)
8. `test_schedule_includes_percentage_depreciated` - Cronograma incluye porcentajes
9. `test_schedule_filters_past_months` - Filtrado de meses pasados funciona

**Criterios de Aceptación:**
- [ ] Todos los tests pasan
- [ ] Cobertura > 90%
- [ ] Casos edge cubiertos

#### Tarea 6.2: Tests de Integración de Endpoints
**Archivo:** `backend/tests/integration/test_equipment_endpoints.py`

**Tests a crear:**
1. `test_create_equipment` - Crear equipo
2. `test_create_equipment_calculates_depreciation` - Verificar cálculo automático
3. `test_list_equipment` - Listar equipos
4. `test_get_equipment` - Obtener equipo
5. `test_update_equipment` - Actualizar equipo
6. `test_delete_equipment` - Eliminar equipo (soft delete)
7. `test_equipment_tenant_isolation` - Aislamiento multi-tenant
8. `test_equipment_permissions` - Verificar permisos
9. `test_get_depreciation_schedule` - Obtener cronograma
10. `test_get_depreciation_progress` - Obtener progreso actual
11. `test_create_equipment_with_exchange_rate` - Crear equipo con TRM histórica
12. `test_create_equipment_requires_exchange_rate` - Validación de TRM cuando currency != primary
13. `test_purchase_date_not_future` - Validación de fecha no futura
14. `test_salvage_value_less_than_purchase_price` - Validación de valor de salvamento

**Criterios de Aceptación:**
- [ ] Todos los tests pasan
- [ ] Tenant isolation funciona
- [ ] Permisos funcionan
- [ ] Cálculos son correctos

#### Tarea 6.3: Tests de Integración con BCR
**Archivo:** `backend/tests/integration/test_bcr_with_equipment.py`

**Tests a crear:**
1. `test_bcr_includes_equipment_depreciation` - BCR incluye amortización
2. `test_bcr_excludes_inactive_equipment` - No incluye equipos inactivos
3. `test_bcr_excludes_deleted_equipment` - No incluye equipos eliminados
4. `test_bcr_normalizes_equipment_currency` - Normaliza moneda de equipos
5. `test_bcr_uses_historical_exchange_rate` - Usa TRM histórica para conversión (sin re-expresión)
6. `test_bcr_categorizes_equipment` - Categoriza correctamente (Hardware → Overhead, Software → Tools)

**Criterios de Aceptación:**
- [ ] Todos los tests pasan
- [ ] BCR se calcula correctamente con equipos
- [ ] Filtros funcionan

---

### Fase 7: Documentación

#### Tarea 7.1: Actualizar Documentación de API
**Archivo:** Endpoints ya tienen docstrings, verificar que sean completos

**Pasos:**
1. Verificar docstrings en todos los endpoints
2. Agregar ejemplos de request/response
3. Documentar códigos de error

**Criterios de Aceptación:**
- [ ] Docstrings completos
- [ ] Ejemplos incluidos
- [ ] Swagger UI muestra documentación correcta

#### Tarea 7.2: Actualizar FRONTEND_API_INTEGRATION_GUIDE.md
**Archivo:** `docs/development/FRONTEND_API_INTEGRATION_GUIDE.md`

**Pasos:**
1. Agregar sección "Equipos y Amortización"
2. Documentar todos los endpoints
3. Agregar ejemplos de uso
4. Documentar integración con BCR

**Criterios de Aceptación:**
- [ ] Sección agregada
- [ ] Endpoints documentados
- [ ] Ejemplos incluidos

---

## 4. ESTRUCTURA DE ARCHIVOS

```
backend/
├── app/
│   ├── models/
│   │   └── equipment.py                    # NUEVO: Modelo EquipmentAmortization
│   ├── schemas/
│   │   └── equipment.py                    # NUEVO: Schemas Pydantic
│   ├── repositories/
│   │   └── equipment_repository.py         # NUEVO: Repository para equipos
│   ├── services/
│   │   └── depreciation_service.py         # NUEVO: Servicio de cálculos
│   ├── api/v1/endpoints/
│   │   └── equipment.py                    # NUEVO: Endpoints REST
│   ├── core/
│   │   └── calculations.py                 # MODIFICAR: Integrar equipos en BCR
│   └── repositories/
│       └── factory.py                      # MODIFICAR: Agregar create_equipment_repository
├── alembic/versions/
│   └── XXXX_add_equipment_amortization.py  # NUEVO: Migración
└── tests/
    ├── unit/
    │   └── test_depreciation_service.py    # NUEVO: Tests unitarios
    └── integration/
        ├── test_equipment_endpoints.py      # NUEVO: Tests de endpoints
        └── test_bcr_with_equipment.py      # NUEVO: Tests de integración BCR
```

---

## 5. DETALLES TÉCNICOS

### 5.1 Fórmulas de Depreciación

#### Línea Recta (Straight Line)
```
monthly_depreciation = (purchase_price - salvage_value) / useful_life_months
```

**Ejemplo:**
- Precio compra: $12,000,000 COP
- Valor salvamento: $2,000,000 COP
- Vida útil: 36 meses
- Amortización mensual: ($12,000,000 - $2,000,000) / 36 = $277,778 COP/mes

#### Saldo Decreciente (Declining Balance)
```
# Tasa de depreciación = 2 × (1 / useful_life_months)  [Double Declining Balance]
monthly_rate = depreciation_rate / 12
monthly_depreciation = current_book_value × monthly_rate

# No deprecia por debajo del valor de salvamento
if (current_book_value - monthly_depreciation) < salvage_value:
    monthly_depreciation = current_book_value - salvage_value
```

**Ejemplo (Primer mes):**
- Precio compra: $12,000,000 COP
- Vida útil: 36 meses
- Tasa anual: 2 × (1/36) = 5.56% mensual
- Amortización mes 1: $12,000,000 × 0.0556 = $667,200 COP

### 5.2 Integración con BCR

**Fórmula Actualizada:**
```
BCR = Total Monthly Costs / Total Billable Hours Available

Donde:
Total Monthly Costs = 
    (Salarios con Cargas) + 
    (Gastos Fijos) + 
    (Amortización de Equipos)  ← NUEVO
```

**Categorización:**
- Equipos con categoría "Hardware", "Vehicles", "Office Equipment" → Overhead
- Equipos con categoría "Software" → Tools/SaaS

### 5.3 Validaciones

#### Validaciones de Entrada
- `purchase_price`: Debe ser > 0
- `salvage_value`: Debe ser >= 0 y **< purchase_price** (crítico para competitividad)
- `useful_life_months`: Debe ser > 0 (típicamente 12-120 meses, validación de advertencia)
- `purchase_date`: Debe ser fecha válida, **no futura** (validación estricta)
- `depreciation_method`: Solo "straight_line" o "declining_balance"
- `category`: Debe ser una de: "Hardware", "Software", "Vehicles", "Office Equipment"
- `exchange_rate_at_purchase`: Requerido si `currency != primary_currency`, debe ser > 0
- `currency`: Debe ser una de: "USD", "COP", "EUR", "ARS"

#### Validaciones de Negocio
- No se puede eliminar equipo si tiene depreciación acumulada > 0 (opcional, puede ser soft delete)
- Al actualizar `useful_life_months`, recalcular `monthly_depreciation` y `total_depreciated`
- Al actualizar `purchase_price` o `salvage_value`, recalcular `monthly_depreciation` y `total_depreciated`
- Al actualizar `depreciation_method`, regenerar cronograma completo
- Al actualizar `exchange_rate_at_purchase`, recalcular `monthly_depreciation` en moneda principal (solo si cambia)
- Si `remaining_value <= salvage_value`, marcar como completamente depreciado (opcional: `is_active = False`)

### 5.4 Cache y Performance

- **Cache de BCR:** Se invalida automáticamente al crear/editar/eliminar equipo
- **Índices:** Crear índices en `organization_id`, `category`, `is_active`, `deleted_at`
- **Queries:** Usar `selectinload` si se necesitan relaciones

---

## 6. CRONOGRAMA ESTIMADO

### Sprint 1: Modelo y Migración (2-3 días)
- Tarea 1.1: Crear modelo (4 horas)
- Tarea 1.2: Crear migración (2 horas)
- Tarea 1.3: Registrar modelo (30 minutos)

### Sprint 2: Schemas y Servicio (2-3 días)
- Tarea 2.1: Crear schemas (3 horas)
- Tarea 2.2: Crear servicio de cálculo (4 horas)
- Tests unitarios del servicio (3 horas)

### Sprint 3: Repository y Endpoints (3-4 días)
- Tarea 3.1: Crear repository (2 horas)
- Tarea 3.2: Registrar en factory (1 hora)
- Tarea 4.1: Crear endpoints (6 horas)
- Tarea 4.2: Registrar router (30 minutos)

### Sprint 4: Integración BCR (2 días)
- Tarea 5.1: Modificar calculate_blended_cost_rate (4 horas)
- Tarea 5.2: Actualizar response schema (1 hora)
- Tests de integración (3 horas)

### Sprint 5: Tests y Documentación (2 días)
- Tarea 6.1: Tests unitarios (3 horas)
- Tarea 6.2: Tests de endpoints (4 horas)
- Tarea 6.3: Tests de integración BCR (2 horas)
- Tarea 7.1: Documentación API (2 horas)
- Tarea 7.2: Actualizar guía frontend (2 horas)

**Total Estimado:** 13-16 días de desarrollo (incluye manejo de TRM histórica y campos calculados adicionales)

---

## 7. CHECKLIST DE IMPLEMENTACIÓN

### Fase 1: Modelo y Migración
- [ ] Modelo `EquipmentAmortization` creado
- [ ] Migración de Alembic creada y probada
- [ ] Modelo registrado en `__init__.py`
- [ ] Migración aplicada en desarrollo

### Fase 2: Schemas y Servicio
- [ ] Schemas Pydantic creados (incluye `exchange_rate_at_purchase`)
- [ ] Validaciones implementadas (fecha no futura, TRM condicional, valor de salvamento)
- [ ] `DepreciationService` implementado (con `calculate_depreciation_progress`)
- [ ] `generate_depreciation_schedule` incluye fechas y porcentajes
- [ ] Tests unitarios del servicio pasan

### Fase 3: Repository
- [ ] `EquipmentRepository` creado
- [ ] Métodos de filtrado implementados
- [ ] Registrado en `RepositoryFactory`

### Fase 4: Endpoints
- [ ] Todos los endpoints CRUD creados
- [ ] Permisos aplicados
- [ ] Validaciones funcionan
- [ ] Cálculo automático de amortización
- [ ] Router registrado

### Fase 5: Integración BCR
- [ ] `calculate_blended_cost_rate` modificado
- [ ] Equipos incluidos en cálculo usando TRM histórica
- [ ] Categorización de equipos (Hardware → Overhead, Software → Tools)
- [ ] `BlendedCostRateResponse` actualizado (con breakdown de equipos)
- [ ] Cache se invalida correctamente
- [ ] Normalización de moneda con TRM histórica funciona (sin re-expresión mensual)

### Fase 6: Tests
- [ ] Tests unitarios del servicio pasan
- [ ] Tests de endpoints pasan
- [ ] Tests de integración BCR pasan
- [ ] Cobertura > 80%

### Fase 7: Documentación
- [ ] Docstrings completos en endpoints
- [ ] `FRONTEND_API_INTEGRATION_GUIDE.md` actualizado
- [ ] Swagger UI muestra documentación correcta

---

## 8. RIESGOS Y MITIGACIONES

### Riesgo 1: Cambios en Equipos Afectan BCR Histórico
**Mitigación:** 
- Los equipos solo afectan el BCR actual, no histórico
- Las cotizaciones guardadas mantienen su BCR original
- Documentar que cambios en equipos afectan futuras cotizaciones

### Riesgo 2: Equipos con Vida Útil Muy Larga
**Mitigación:**
- Validar que `useful_life_months` sea razonable (máximo 120 meses)
- Permitir marcar equipos como inactivos cuando se completa la depreciación

### Riesgo 3: Múltiples Métodos de Depreciación
**Mitigación:**
- Implementar solo línea recta inicialmente
- Saldo decreciente como opción avanzada
- Documentar diferencias y cuándo usar cada uno

### Riesgo 4: Performance con Muchos Equipos
**Mitigación:**
- Usar índices en queries
- Cachear BCR (ya implementado)
- Filtrar solo equipos activos y no eliminados

### Riesgo 5: Manejo de TRM Histórica
**Mitigación:**
- Validar que `exchange_rate_at_purchase` se capture al crear equipo
- Documentar que la TRM histórica evita re-expresión mensual
- Si no se proporciona TRM y currency != primary, usar TRM actual como fallback (con warning)
- Considerar integración con API de tasas de cambio históricas (futuro)

---

## 9. DECISIONES DE DISEÑO

### Decisión 1: Tabla Separada vs Extensión de CostFixed
**Decisión:** Tabla separada `equipment_amortization`
**Razón:** 
- Equipos tienen campos específicos (fecha compra, vida útil, método)
- Permite queries específicas para equipos
- Facilita reportes de depreciación
- Mantiene `CostFixed` simple para gastos recurrentes

### Decisión 2: Cálculo Automático vs Manual
**Decisión:** Cálculo automático de `monthly_depreciation` al guardar
**Razón:**
- Consistencia en cálculos
- Menos errores del usuario
- Actualización automática al cambiar parámetros

### Decisión 3: Métodos de Depreciación
**Decisión:** Implementar ambos métodos (línea recta y saldo decreciente)
**Razón:**
- Flexibilidad para diferentes necesidades contables
- Línea recta es más común y simple
- Saldo decreciente para casos específicos

### Decisión 4: Integración con BCR
**Decisión:** Incluir amortización mensual en cálculo de BCR
**Razón:**
- La amortización es un costo operacional real
- Debe reflejarse en el costo por hora
- Alinea con principios contables

### Decisión 5: TRM Histórica vs Re-expresión Mensual
**Decisión:** Usar TRM histórica del día de compra (sin re-expresión mensual)
**Razón:**
- Los activos no se re-expresan cada mes en el flujo de caja operativo
- La amortización debe ser fija y predecible
- Evita variaciones del dólar que afecten el BCR mensualmente
- Alinea con principios contables (costo histórico)

### Decisión 6: Campos Calculados Dinámicos
**Decisión:** Calcular `months_depreciated`, `months_remaining`, `percentage_depreciated` dinámicamente (no almacenar)
**Razón:**
- Estos valores cambian cada mes automáticamente
- Evita necesidad de actualización periódica
- Siempre refleja el estado actual del equipo
- Facilita visualización de barras de vida útil y gráficos

---

## 10. PRÓXIMOS PASOS

1. **Revisar y Aprobar Plan:** Validar con equipo que el plan es correcto
2. **Crear Branch:** `feature/equipment-amortization`
3. **Implementar Fase 1:** Modelo y migración
4. **Code Review:** Revisar modelo antes de continuar
5. **Implementar Fases Restantes:** Seguir plan secuencialmente
6. **Testing:** Ejecutar suite completa de tests
7. **Documentación:** Actualizar guías y Swagger
8. **Merge a Main:** Después de aprobación

---

---

## 11. ACTUALIZACIONES v2.0 (2026-01-25)

### Nuevos Requerimientos del UI

**Basado en:** `UI_REQUIREMENTS_EQUIPMENT_AMORTIZATION.md`

**Cambios Principales:**

1. **Campo `exchange_rate_at_purchase` (TRM Histórica):**
   - Agregado al modelo `EquipmentAmortization`
   - Validación condicional: requerido si `currency != primary_currency`
   - Uso en conversión de moneda: usar TRM histórica en lugar de TRM actual
   - Sin re-expresión mensual: el valor no cambia con fluctuaciones cambiarias

2. **Campos Calculados Adicionales:**
   - `months_depreciated`: Meses transcurridos desde `purchase_date`
   - `months_remaining`: Meses restantes de vida útil
   - `percentage_depreciated`: Porcentaje depreciado (0-100)
   - Calculados dinámicamente en `DepreciationService.calculate_depreciation_progress()`

3. **Cronograma Mejorado:**
   - Incluye `month_date` (fecha específica del mes en ISO 8601)
   - Incluye `percentage_depreciated` por mes
   - Filtro opcional `include_past_months` para mostrar solo meses futuros

4. **Validaciones Adicionales:**
   - `purchase_date` no puede ser futura
   - `salvage_value < purchase_price` (validación estricta)
   - `exchange_rate_at_purchase` requerido condicionalmente

5. **Integración BCR Mejorada:**
   - Uso de TRM histórica para conversión de moneda
   - Categorización explícita (Hardware → Overhead, Software → Tools)
   - Breakdown de equipos en `BlendedCostRateResponse`

6. **Nuevo Endpoint:**
   - `GET /api/v1/settings/equipment/{id}/progress` - Progreso actual de depreciación

---

**Última actualización:** 2026-01-25  
**Versión:** 2.0  
**Autor:** AI Assistant  
**Revisión Requerida:** Sí  
**Documento UI Base:** `UI_REQUIREMENTS_EQUIPMENT_AMORTIZATION.md`
