# Plan de Implementación: Equipment Amortization bajo Arquitectura MVC

**Fecha:** 2026-01-25  
**Base:** `BACKEND_IMPLEMENTATION_STATUS_EQUIPMENT_AMORTIZATION.md`  
**Arquitectura:** MVC + Repository/Service (`.cursorrules/nougram_backend_rules.md`)

---

## 🎯 Resumen Ejecutivo

El módulo de **Equipment Amortization** NO está implementado. Este documento detalla qué falta implementar siguiendo la **nueva arquitectura MVC + Repository/Service** establecida en la refactorización reciente.

**Arquitectura Requerida:**
```
Endpoint → Controller → Service → Repository → ORM → Database
                    ↓
                  View (transformación de datos)
```

---

## 📋 Componentes a Implementar

### 1. ✅ Modelo (`backend/app/models/equipment.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**
```python
from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class EquipmentAmortization(BaseModel):
    """
    Equipment Amortization Model
    NO debe contener queries SQL ni lógica de negocio
    """
    __tablename__ = "equipment_amortization"
    
    # Campos básicos
    name = Column(String, nullable=False)
    description = Column(String)
    category = Column(String, nullable=False)  # Hardware, Software, Vehicles, Office Equipment
    
    # Información financiera
    purchase_price = Column(Numeric(15, 2), nullable=False)
    purchase_date = Column(Date, nullable=False)
    currency = Column(String(3), nullable=False)
    exchange_rate_at_purchase = Column(Numeric(10, 4))  # ⚠️ CRÍTICO: TRM histórica
    
    # Parámetros de depreciación
    useful_life_months = Column(Integer, nullable=False)
    salvage_value = Column(Numeric(15, 2), default=0)  # ⚠️ CRÍTICO: Valor de salvamento
    depreciation_method = Column(String, nullable=False)  # "straight_line" o "declining_balance"
    
    # Valores calculados (se calculan dinámicamente, no se almacenan)
    # monthly_depreciation, total_depreciated, remaining_value se calculan en Service
    
    # Estado
    is_active = Column(Boolean, default=True)
    
    # Relaciones
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    deleted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Soft delete
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="equipment")
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])
```

**Migración Alembic:** Crear migración para tabla `equipment_amortization`

---

### 2. ✅ Schemas (`backend/app/schemas/equipment.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**
```python
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date
from decimal import Decimal
from typing import Optional, List

class EquipmentAmortizationBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str  # Hardware, Software, Vehicles, Office Equipment
    purchase_price: Decimal = Field(gt=0)
    purchase_date: date
    currency: str
    exchange_rate_at_purchase: Optional[Decimal] = None
    useful_life_months: int = Field(gt=0)
    salvage_value: Decimal = Field(ge=0, default=0)
    depreciation_method: str  # "straight_line" o "declining_balance"
    is_active: bool = True

class EquipmentAmortizationCreate(EquipmentAmortizationBase):
    @model_validator(mode='after')
    def validate_exchange_rate(self):
        # Validación: exchange_rate_at_purchase requerido si currency != primary_currency
        # Esta validación se hace en Service usando organization settings
        return self
    
    @field_validator('purchase_date')
    def validate_purchase_date(cls, v):
        if v > date.today():
            raise ValueError("Purchase date cannot be in the future")
        return v
    
    @field_validator('salvage_value')
    def validate_salvage_value(cls, v, info):
        if 'purchase_price' in info.data and v >= info.data['purchase_price']:
            raise ValueError("Salvage value must be less than purchase price")
        return v

class EquipmentAmortizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    # ... otros campos opcionales
    # Si cambian purchase_price, useful_life_months, salvage_value, depreciation_method
    # → Service debe recalcular monthly_depreciation

class EquipmentAmortizationResponse(EquipmentAmortizationBase):
    id: int
    organization_id: int
    # Campos calculados (se agregan en View)
    months_depreciated: int
    months_remaining: int
    percentage_depreciated: Decimal
    monthly_depreciation: Decimal
    total_depreciated: Decimal
    remaining_value: Decimal
    created_at: datetime
    updated_at: datetime

class EquipmentAmortizationListResponse(BaseModel):
    items: List[EquipmentAmortizationResponse]
    total: int
    page: int
    page_size: int

class DepreciationScheduleEntry(BaseModel):
    month_number: int
    month_date: str  # ISO 8601
    depreciation_amount: Decimal
    accumulated_depreciation: Decimal
    remaining_value: Decimal
    percentage_depreciated: Decimal

class DepreciationScheduleResponse(BaseModel):
    equipment_id: int
    equipment_name: str
    schedule: List[DepreciationScheduleEntry]
```

---

### 3. ✅ Repository (`backend/app/repositories/equipment_repository.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**
```python
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.equipment import EquipmentAmortization

class EquipmentRepository(BaseRepository[EquipmentAmortization]):
    """
    Repository para Equipment Amortization
    SOLO contiene queries SQLAlchemy, NO lógica de negocio
    """
    
    def __init__(self, db, tenant_id: Optional[int] = None):
        super().__init__(db, EquipmentAmortization, tenant_id)
    
    async def get_all_active(self) -> List[EquipmentAmortization]:
        """Obtener todos los equipos activos"""
        query = select(EquipmentAmortization).where(
            EquipmentAmortization.deleted_at.is_(None),
            EquipmentAmortization.is_active == True
        )
        query = self._apply_tenant_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_category(self, category: str) -> List[EquipmentAmortization]:
        """Filtrar por categoría"""
        query = select(EquipmentAmortization).where(
            EquipmentAmortization.category == category,
            EquipmentAmortization.deleted_at.is_(None)
        )
        query = self._apply_tenant_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_depreciation_method(self, method: str) -> List[EquipmentAmortization]:
        """Filtrar por método de depreciación"""
        query = select(EquipmentAmortization).where(
            EquipmentAmortization.depreciation_method == method,
            EquipmentAmortization.deleted_at.is_(None)
        )
        query = self._apply_tenant_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_active_equipment_for_bcr(self) -> List[EquipmentAmortization]:
        """
        Obtener equipos activos para cálculo de BCR
        Usado por calculate_blended_cost_rate()
        """
        query = select(EquipmentAmortization).where(
            EquipmentAmortization.deleted_at.is_(None),
            EquipmentAmortization.is_active == True
        )
        query = self._apply_tenant_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
```

**Registro en Factory:**
```python
# backend/app/repositories/factory.py
@staticmethod
def create_equipment_repository(db: AsyncSession, tenant_id: int) -> EquipmentRepository:
    """Create EquipmentRepository with tenant context"""
    return EquipmentRepository(db, tenant_id=tenant_id)
```

---

### 4. ✅ Service de Cálculo (`backend/app/services/depreciation_service.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**
```python
from typing import List, Dict
from datetime import date, datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta

class DepreciationService:
    """
    Servicio de cálculo de depreciación
    Contiene TODA la lógica de negocio de cálculos
    NO accede directamente a DB, solo hace cálculos
    """
    
    @staticmethod
    def calculate_straight_line(
        purchase_price: Decimal,
        salvage_value: Decimal,
        useful_life_months: int
    ) -> Decimal:
        """
        Calcular depreciación mensual método línea recta
        Formula: (purchase_price - salvage_value) / useful_life_months
        """
        depreciable_base = purchase_price - salvage_value
        return depreciable_base / Decimal(str(useful_life_months))
    
    @staticmethod
    def calculate_declining_balance(
        purchase_price: Decimal,
        salvage_value: Decimal,
        useful_life_months: int,
        month_number: int
    ) -> Decimal:
        """
        Calcular depreciación mensual método saldo decreciente
        No depreciar por debajo del valor de salvamento
        """
        # Implementar lógica de saldo decreciente
        # ...
        pass
    
    @staticmethod
    def generate_depreciation_schedule(
        purchase_price: Decimal,
        purchase_date: date,
        salvage_value: Decimal,
        useful_life_months: int,
        depreciation_method: str,
        months: Optional[int] = None
    ) -> List[Dict]:
        """
        Generar cronograma de depreciación mes a mes
        Incluye fechas ISO 8601 y porcentajes depreciados
        """
        schedule = []
        months_to_calculate = months or useful_life_months
        accumulated = Decimal('0')
        
        for month_num in range(1, months_to_calculate + 1):
            month_date = purchase_date + relativedelta(months=month_num - 1)
            
            if depreciation_method == "straight_line":
                monthly_dep = DepreciationService.calculate_straight_line(
                    purchase_price, salvage_value, useful_life_months
                )
            else:
                monthly_dep = DepreciationService.calculate_declining_balance(
                    purchase_price, salvage_value, useful_life_months, month_num
                )
            
            # No depreciar por debajo del valor de salvamento
            remaining = purchase_price - accumulated - monthly_dep
            if remaining < salvage_value:
                monthly_dep = purchase_price - accumulated - salvage_value
                if monthly_dep < 0:
                    monthly_dep = Decimal('0')
            
            accumulated += monthly_dep
            remaining_value = purchase_price - accumulated
            
            depreciable_base = purchase_price - salvage_value
            percentage = (accumulated / depreciable_base * 100) if depreciable_base > 0 else Decimal('0')
            
            schedule.append({
                "month_number": month_num,
                "month_date": month_date.isoformat(),
                "depreciation_amount": monthly_dep,
                "accumulated_depreciation": accumulated,
                "remaining_value": remaining_value,
                "percentage_depreciated": percentage
            })
        
        return schedule
    
    @staticmethod
    def calculate_depreciation_progress(
        purchase_date: date,
        useful_life_months: int,
        purchase_price: Decimal,
        salvage_value: Decimal,
        depreciation_method: str
    ) -> Dict:
        """
        Calcular progreso actual de depreciación
        Retorna: months_depreciated, months_remaining, percentage_depreciated, etc.
        """
        today = date.today()
        months_depreciated = min(
            (today.year - purchase_date.year) * 12 + (today.month - purchase_date.month),
            useful_life_months
        )
        months_remaining = max(0, useful_life_months - months_depreciated)
        
        # Calcular total depreciado hasta hoy
        schedule = DepreciationService.generate_depreciation_schedule(
            purchase_price, purchase_date, salvage_value,
            useful_life_months, depreciation_method, months_depreciated
        )
        total_depreciated = schedule[-1]["accumulated_depreciation"] if schedule else Decimal('0')
        
        depreciable_base = purchase_price - salvage_value
        percentage_depreciated = (total_depreciated / depreciable_base * 100) if depreciable_base > 0 else Decimal('0')
        
        monthly_depreciation = DepreciationService.calculate_straight_line(
            purchase_price, salvage_value, useful_life_months
        ) if depreciation_method == "straight_line" else Decimal('0')
        
        return {
            "months_depreciated": months_depreciated,
            "months_remaining": months_remaining,
            "percentage_depreciated": percentage_depreciated,
            "total_depreciated": total_depreciated,
            "remaining_value": purchase_price - total_depreciated,
            "monthly_depreciation": monthly_depreciation
        }
```

---

### 5. ✅ Service de Negocio (`backend/app/services/equipment_service.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**
```python
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.repositories.factory import RepositoryFactory
from app.services.depreciation_service import DepreciationService
from app.models.equipment import EquipmentAmortization
from app.schemas.equipment import (
    EquipmentAmortizationCreate,
    EquipmentAmortizationUpdate,
    EquipmentAmortizationResponse
)
from app.core.exceptions import BusinessLogicError, ResourceNotFoundError

class EquipmentService:
    """
    Service para gestión de Equipment Amortization
    Contiene TODA la lógica de negocio
    NO accede directamente a DB, usa Repository
    """
    
    def __init__(self, db: AsyncSession, organization_id: int):
        self.db = db
        self.organization_id = organization_id
        self.equipment_repo = RepositoryFactory.create_equipment_repository(db, organization_id)
    
    async def list_equipment(
        self,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[EquipmentAmortization], int]:
        """
        Listar equipos con filtros
        Lógica de negocio: aplicar filtros, paginación
        """
        # Usar repository para obtener datos
        if include_deleted:
            equipment = await self.equipment_repo.get_all()
        elif is_active is not None:
            if is_active:
                equipment = await self.equipment_repo.get_all_active()
            else:
                # Implementar método en repository
                equipment = await self.equipment_repo.get_all_inactive()
        else:
            equipment = await self.equipment_repo.get_all()
        
        # Filtrar por categoría si se especifica
        if category:
            equipment = [e for e in equipment if e.category == category]
        
        # Paginación
        total = len(equipment)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = equipment[start:end]
        
        return paginated, total
    
    async def get_equipment_by_id(self, equipment_id: int) -> EquipmentAmortization:
        """Obtener equipo por ID"""
        equipment = await self.equipment_repo.get_by_id(equipment_id)
        if not equipment:
            raise ResourceNotFoundError("Equipment", equipment_id)
        return equipment
    
    async def create_equipment(self, data: EquipmentAmortizationCreate) -> EquipmentAmortization:
        """
        Crear nuevo equipo
        Validaciones de negocio:
        - Validar exchange_rate_at_purchase si currency != primary_currency
        - Calcular monthly_depreciation automáticamente
        """
        # Obtener moneda principal de la organización
        from app.repositories.factory import RepositoryFactory
        org_repo = RepositoryFactory.create_organization_repository(self.db)
        org = await org_repo.get_by_id(self.organization_id)
        primary_currency = org.primary_currency if org else "USD"
        
        # Validar exchange_rate_at_purchase
        if data.currency != primary_currency and not data.exchange_rate_at_purchase:
            raise BusinessLogicError(
                f"exchange_rate_at_purchase is required when currency ({data.currency}) "
                f"differs from primary currency ({primary_currency})"
            )
        
        # Calcular monthly_depreciation
        monthly_depreciation = DepreciationService.calculate_straight_line(
            data.purchase_price,
            data.salvage_value,
            data.useful_life_months
        ) if data.depreciation_method == "straight_line" else DepreciationService.calculate_declining_balance(
            data.purchase_price,
            data.salvage_value,
            data.useful_life_months,
            1  # Primer mes
        )
        
        # Crear equipo usando repository
        equipment_dict = data.model_dump()
        equipment_dict['organization_id'] = self.organization_id
        equipment = EquipmentAmortization(**equipment_dict)
        
        created = await self.equipment_repo.create(equipment)
        
        # Invalidar cache de BCR
        from app.core.cache import get_cache
        cache = get_cache()
        cache.invalidate_pattern("blended_cost_rate:*")
        
        return created
    
    async def update_equipment(
        self,
        equipment_id: int,
        data: EquipmentAmortizationUpdate
    ) -> EquipmentAmortization:
        """
        Actualizar equipo
        Si cambian parámetros de depreciación, recalcular monthly_depreciation
        """
        equipment = await self.get_equipment_by_id(equipment_id)
        
        # Si cambian parámetros de depreciación, recalcular
        recalculate = any([
            data.purchase_price and data.purchase_price != equipment.purchase_price,
            data.salvage_value and data.salvage_value != equipment.salvage_value,
            data.useful_life_months and data.useful_life_months != equipment.useful_life_months,
            data.depreciation_method and data.depreciation_method != equipment.depreciation_method
        ])
        
        # Actualizar campos
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(equipment, key, value)
        
        # Recalcular si es necesario
        if recalculate:
            monthly_depreciation = DepreciationService.calculate_straight_line(
                equipment.purchase_price,
                equipment.salvage_value,
                equipment.useful_life_months
            ) if equipment.depreciation_method == "straight_line" else Decimal('0')
            # monthly_depreciation se calcula dinámicamente, no se almacena
        
        updated = await self.equipment_repo.update(equipment)
        
        # Invalidar cache de BCR
        from app.core.cache import get_cache
        cache = get_cache()
        cache.invalidate_pattern("blended_cost_rate:*")
        
        return updated
    
    async def delete_equipment(self, equipment_id: int, user_id: int) -> None:
        """Eliminar equipo (soft delete)"""
        equipment = await self.get_equipment_by_id(equipment_id)
        await self.equipment_repo.soft_delete(equipment, user_id)
        
        # Invalidar cache de BCR
        from app.core.cache import get_cache
        cache = get_cache()
        cache.invalidate_pattern("blended_cost_rate:*")
    
    async def restore_equipment(self, equipment_id: int) -> EquipmentAmortization:
        """Restaurar equipo eliminado"""
        equipment = await self.get_equipment_by_id(equipment_id)
        restored = await self.equipment_repo.restore(equipment)
        
        # Invalidar cache de BCR
        from app.core.cache import get_cache
        cache = get_cache()
        cache.invalidate_pattern("blended_cost_rate:*")
        
        return restored
    
    async def get_depreciation_schedule(
        self,
        equipment_id: int,
        months: Optional[int] = None
    ) -> List[Dict]:
        """Obtener cronograma de depreciación"""
        equipment = await self.get_equipment_by_id(equipment_id)
        
        return DepreciationService.generate_depreciation_schedule(
            equipment.purchase_price,
            equipment.purchase_date,
            equipment.salvage_value,
            equipment.useful_life_months,
            equipment.depreciation_method,
            months
        )
    
    async def get_depreciation_progress(self, equipment_id: int) -> Dict:
        """Obtener progreso actual de depreciación"""
        equipment = await self.get_equipment_by_id(equipment_id)
        
        return DepreciationService.calculate_depreciation_progress(
            equipment.purchase_date,
            equipment.useful_life_months,
            equipment.purchase_price,
            equipment.salvage_value,
            equipment.depreciation_method
        )
```

---

### 6. ✅ View (`backend/app/views/equipment_view.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**
```python
from typing import List
from app.views.base import BaseView
from app.models.equipment import EquipmentAmortization
from app.schemas.equipment import (
    EquipmentAmortizationResponse,
    EquipmentAmortizationListResponse
)
from app.services.depreciation_service import DepreciationService

class EquipmentView(BaseView[EquipmentAmortization, EquipmentAmortizationResponse]):
    """
    View para transformar Equipment models a schemas
    Agrega campos calculados dinámicamente
    """
    
    def __init__(self):
        super().__init__(EquipmentAmortizationResponse)
    
    def to_response(self, model: EquipmentAmortization) -> EquipmentAmortizationResponse:
        """Transformar modelo a response con campos calculados"""
        if model is None:
            return None
        
        # Calcular progreso de depreciación
        progress = DepreciationService.calculate_depreciation_progress(
            model.purchase_date,
            model.useful_life_months,
            model.purchase_price,
            model.salvage_value,
            model.depreciation_method
        )
        
        # Construir dict con todos los campos
        equipment_dict = {
            "id": model.id,
            "name": model.name,
            "description": model.description,
            "category": model.category,
            "purchase_price": model.purchase_price,
            "purchase_date": model.purchase_date,
            "currency": model.currency,
            "exchange_rate_at_purchase": model.exchange_rate_at_purchase,
            "useful_life_months": model.useful_life_months,
            "salvage_value": model.salvage_value,
            "depreciation_method": model.depreciation_method,
            "is_active": model.is_active,
            "organization_id": model.organization_id,
            # Campos calculados
            "months_depreciated": progress["months_depreciated"],
            "months_remaining": progress["months_remaining"],
            "percentage_depreciated": progress["percentage_depreciated"],
            "monthly_depreciation": progress["monthly_depreciation"],
            "total_depreciated": progress["total_depreciated"],
            "remaining_value": progress["remaining_value"],
            "created_at": model.created_at,
            "updated_at": model.updated_at
        }
        
        return EquipmentAmortizationResponse.model_validate(equipment_dict)
    
    def to_paginated_response(
        self,
        models: List[EquipmentAmortization],
        total: int,
        page: int,
        page_size: int
    ) -> EquipmentAmortizationListResponse:
        """Transformar lista de modelos a response paginado"""
        items = [self.to_response(model) for model in models]
        return EquipmentAmortizationListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
```

---

### 7. ✅ Controller (`backend/app/controllers/equipment_controller.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**
```python
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Query

from app.controllers.base import BaseController
from app.core.tenant import TenantContext
from app.models.user import User
from app.schemas.equipment import (
    EquipmentAmortizationCreate,
    EquipmentAmortizationUpdate,
    EquipmentAmortizationResponse,
    EquipmentAmortizationListResponse,
    DepreciationScheduleResponse
)
from app.services.equipment_service import EquipmentService
from app.views.equipment_view import EquipmentView

class EquipmentController(BaseController):
    """
    Controller para Equipment Amortization
    Maneja HTTP requests y delega a Service
    NO contiene lógica de negocio
    """
    
    def __init__(self, db: AsyncSession, tenant: TenantContext, current_user: User):
        super().__init__(db, tenant, current_user)
        self.equipment_service = EquipmentService(db, tenant.organization_id)
        self.equipment_view = EquipmentView()
    
    async def list_equipment(
        self,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> EquipmentAmortizationListResponse:
        """Listar equipos"""
        try:
            equipment, total = await self.equipment_service.list_equipment(
                category=category,
                is_active=is_active,
                include_deleted=include_deleted,
                page=page,
                page_size=page_size
            )
            return self.equipment_view.to_paginated_response(
                equipment, total, page, page_size
            )
        except Exception as e:
            self._log_error(f"Error listing equipment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_equipment(self, equipment_id: int) -> EquipmentAmortizationResponse:
        """Obtener equipo por ID"""
        try:
            equipment = await self.equipment_service.get_equipment_by_id(equipment_id)
            return self.equipment_view.to_response(equipment)
        except ResourceNotFoundError as e:
            self._handle_not_found("Equipment", equipment_id)
        except Exception as e:
            self._log_error(f"Error getting equipment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    async def create_equipment(
        self,
        data: EquipmentAmortizationCreate
    ) -> EquipmentAmortizationResponse:
        """Crear equipo"""
        try:
            equipment = await self.equipment_service.create_equipment(data)
            self._log_info(f"Created equipment: {equipment.id}")
            return self.equipment_view.to_response(equipment)
        except BusinessLogicError as e:
            self._handle_business_error(str(e))
        except Exception as e:
            self._log_error(f"Error creating equipment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    async def update_equipment(
        self,
        equipment_id: int,
        data: EquipmentAmortizationUpdate
    ) -> EquipmentAmortizationResponse:
        """Actualizar equipo"""
        try:
            equipment = await self.equipment_service.update_equipment(equipment_id, data)
            self._log_info(f"Updated equipment: {equipment.id}")
            return self.equipment_view.to_response(equipment)
        except ResourceNotFoundError:
            self._handle_not_found("Equipment", equipment_id)
        except BusinessLogicError as e:
            self._handle_business_error(str(e))
        except Exception as e:
            self._log_error(f"Error updating equipment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete_equipment(self, equipment_id: int) -> None:
        """Eliminar equipo"""
        try:
            await self.equipment_service.delete_equipment(equipment_id, self.current_user.id)
            self._log_info(f"Deleted equipment: {equipment_id}")
        except ResourceNotFoundError:
            self._handle_not_found("Equipment", equipment_id)
        except Exception as e:
            self._log_error(f"Error deleting equipment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    async def restore_equipment(self, equipment_id: int) -> EquipmentAmortizationResponse:
        """Restaurar equipo"""
        try:
            equipment = await self.equipment_service.restore_equipment(equipment_id)
            self._log_info(f"Restored equipment: {equipment_id}")
            return self.equipment_view.to_response(equipment)
        except ResourceNotFoundError:
            self._handle_not_found("Equipment", equipment_id)
        except Exception as e:
            self._log_error(f"Error restoring equipment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_depreciation_schedule(
        self,
        equipment_id: int,
        months: Optional[int] = None
    ) -> DepreciationScheduleResponse:
        """Obtener cronograma de depreciación"""
        try:
            equipment = await self.equipment_service.get_equipment_by_id(equipment_id)
            schedule = await self.equipment_service.get_depreciation_schedule(
                equipment_id, months
            )
            return DepreciationScheduleResponse(
                equipment_id=equipment.id,
                equipment_name=equipment.name,
                schedule=schedule
            )
        except ResourceNotFoundError:
            self._handle_not_found("Equipment", equipment_id)
        except Exception as e:
            self._log_error(f"Error getting schedule: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_depreciation_progress(self, equipment_id: int) -> dict:
        """Obtener progreso actual de depreciación"""
        try:
            return await self.equipment_service.get_depreciation_progress(equipment_id)
        except ResourceNotFoundError:
            self._handle_not_found("Equipment", equipment_id)
        except Exception as e:
            self._log_error(f"Error getting progress: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
```

---

### 8. ✅ Endpoints (`backend/app/api/v1/endpoints/equipment.py`)

**Estado:** ❌ No implementado

**Implementación Requerida:**
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant import get_tenant_context, TenantContext
from app.core.permission_middleware import require_modify_costs
from app.models.user import User
from app.controllers.equipment_controller import EquipmentController
from app.schemas.equipment import (
    EquipmentAmortizationCreate,
    EquipmentAmortizationUpdate,
    EquipmentAmortizationResponse,
    EquipmentAmortizationListResponse,
    DepreciationScheduleResponse
)

router = APIRouter()


@router.get("/equipment", response_model=EquipmentAmortizationListResponse)
async def list_equipment(
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    include_deleted: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user)
):
    """Listar equipos"""
    controller = EquipmentController(db, tenant, current_user)
    return await controller.list_equipment(
        category=category,
        is_active=is_active,
        include_deleted=include_deleted,
        page=page,
        page_size=page_size
    )


@router.post("/equipment", response_model=EquipmentAmortizationResponse, status_code=status.HTTP_201_CREATED)
async def create_equipment(
    data: EquipmentAmortizationCreate,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs)
):
    """Crear equipo"""
    controller = EquipmentController(db, tenant, current_user)
    return await controller.create_equipment(data)


@router.get("/equipment/{equipment_id}", response_model=EquipmentAmortizationResponse)
async def get_equipment(
    equipment_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user)
):
    """Obtener equipo"""
    controller = EquipmentController(db, tenant, current_user)
    return await controller.get_equipment(equipment_id)


@router.put("/equipment/{equipment_id}", response_model=EquipmentAmortizationResponse)
async def update_equipment(
    equipment_id: int,
    data: EquipmentAmortizationUpdate,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs)
):
    """Actualizar equipo"""
    controller = EquipmentController(db, tenant, current_user)
    return await controller.update_equipment(equipment_id, data)


@router.delete("/equipment/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment(
    equipment_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs)
):
    """Eliminar equipo"""
    controller = EquipmentController(db, tenant, current_user)
    await controller.delete_equipment(equipment_id)


@router.post("/equipment/{equipment_id}/restore", response_model=EquipmentAmortizationResponse)
async def restore_equipment(
    equipment_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs)
):
    """Restaurar equipo"""
    controller = EquipmentController(db, tenant, current_user)
    return await controller.restore_equipment(equipment_id)


@router.get("/equipment/{equipment_id}/depreciation-schedule", response_model=DepreciationScheduleResponse)
async def get_depreciation_schedule(
    equipment_id: int,
    months: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user)
):
    """Obtener cronograma de depreciación"""
    controller = EquipmentController(db, tenant, current_user)
    return await controller.get_depreciation_schedule(equipment_id, months)


@router.get("/equipment/{equipment_id}/progress")
async def get_depreciation_progress(
    equipment_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user)
):
    """Obtener progreso actual de depreciación"""
    controller = EquipmentController(db, tenant, current_user)
    return await controller.get_depreciation_progress(equipment_id)
```

**Registro en Router:**
```python
# backend/app/api/v1/router.py
from app.api.v1.endpoints import equipment

api_router.include_router(equipment.router, prefix="/settings", tags=["equipment"])
```

---

### 9. ✅ Integración con BCR (`backend/app/core/calculations.py`)

**Estado:** ❌ No implementado

**Modificación Requerida en `calculate_blended_cost_rate()`:**

```python
# Agregar después de obtener fixed_costs y team_members

# Get active equipment for BCR calculation
from app.repositories.factory import RepositoryFactory
equipment_repo = RepositoryFactory.create_equipment_repository(db, tenant_id)
equipment_list = await equipment_repo.get_active_equipment_for_bcr()

# Convert equipment depreciation to primary currency using historical TRM
equipment_costs_money = []
for equipment in equipment_list:
    # ⚠️ CRÍTICO: Usar TRM histórica (exchange_rate_at_purchase)
    # NO re-expresar mensualmente
    if equipment.currency != primary_currency:
        if equipment.exchange_rate_at_purchase:
            # Usar TRM histórica para convertir
            historical_rate = equipment.exchange_rate_at_purchase
            # Convertir monthly_depreciation a moneda principal
            monthly_dep_money = Money(equipment.monthly_depreciation, equipment.currency)
            # Normalizar usando TRM histórica
            normalized = normalize_to_primary_currency(
                monthly_dep_money.amount,
                equipment.currency,
                primary_currency,
                historical_exchange_rate=historical_rate  # ⚠️ NUEVO PARÁMETRO
            )
            equipment_costs_money.append(Money(normalized, primary_currency))
        else:
            # Si no hay TRM histórica, usar TRM actual (fallback)
            normalized = normalize_to_primary_currency(
                equipment.monthly_depreciation,
                equipment.currency,
                primary_currency
            )
            equipment_costs_money.append(Money(normalized, primary_currency))
    else:
        # Misma moneda, usar directamente
        equipment_costs_money.append(
            Money(equipment.monthly_depreciation, primary_currency)
        )

# Agregar equipment costs a all_costs
all_costs = fixed_costs_money + salary_amounts + equipment_costs_money  # ⚠️ AGREGAR
```

**Modificar `normalize_to_primary_currency()` en `backend/app/core/currency.py`:**

```python
def normalize_to_primary_currency(
    amount: Decimal | Money,
    source_currency: str,
    target_currency: str,
    historical_exchange_rate: Optional[Decimal] = None  # ⚠️ NUEVO PARÁMETRO
) -> Decimal | Money:
    """
    Normalizar moneda usando TRM actual o histórica
    
    Args:
        historical_exchange_rate: Si se proporciona, usar esta TRM en lugar de la actual
    """
    if historical_exchange_rate:
        # Usar TRM histórica
        rate = historical_exchange_rate
    else:
        # Usar TRM actual (comportamiento existente)
        rate = EXCHANGE_RATES_TO_USD.get(source_currency, 1.0)
    
    # ... resto de la lógica
```

**Actualizar `BlendedCostRateResponse` schema:**

```python
# backend/app/schemas/quote.py
class EquipmentBreakdown(BaseModel):
    equipment_id: int
    equipment_name: str
    category: str
    monthly_depreciation: Decimal
    currency: str

class BlendedCostRateResponse(BaseModel):
    # ... campos existentes ...
    total_equipment_depreciation: Decimal  # ⚠️ NUEVO
    equipment_breakdown: Optional[List[EquipmentBreakdown]] = None  # ⚠️ NUEVO
```

---

## 📊 Checklist de Implementación bajo MVC

### Fase 1: Modelo y Migración
- [ ] Crear `backend/app/models/equipment.py` con modelo `EquipmentAmortization`
- [ ] Incluir campo `exchange_rate_at_purchase` (Numeric, nullable)
- [ ] Incluir campo `salvage_value` (Numeric, default=0)
- [ ] Crear migración Alembic
- [ ] Crear índices necesarios
- [ ] Registrar modelo en `__init__.py`

### Fase 2: Schemas y Servicio de Cálculo
- [ ] Crear `backend/app/schemas/equipment.py` con todos los schemas
- [ ] Implementar validaciones (fecha no futura, TRM condicional, valor de salvamento)
- [ ] Crear `backend/app/services/depreciation_service.py`
- [ ] Implementar `calculate_straight_line()`
- [ ] Implementar `calculate_declining_balance()`
- [ ] Implementar `generate_depreciation_schedule()` (con fechas y porcentajes)
- [ ] Implementar `calculate_depreciation_progress()`

### Fase 3: Repository
- [ ] Crear `backend/app/repositories/equipment_repository.py`
- [ ] Heredar de `BaseRepository[EquipmentAmortization]`
- [ ] Implementar métodos: `get_all_active()`, `get_by_category()`, `get_by_depreciation_method()`, `get_active_equipment_for_bcr()`
- [ ] Registrar en `RepositoryFactory.create_equipment_repository()`

### Fase 4: Service de Negocio
- [ ] Crear `backend/app/services/equipment_service.py`
- [ ] Implementar `list_equipment()` - usar repository, aplicar filtros y paginación
- [ ] Implementar `get_equipment_by_id()` - usar repository
- [ ] Implementar `create_equipment()` - validar TRM, calcular depreciación, usar repository
- [ ] Implementar `update_equipment()` - recalcular si cambian parámetros, usar repository
- [ ] Implementar `delete_equipment()` - soft delete usando repository
- [ ] Implementar `restore_equipment()` - usar repository
- [ ] Implementar `get_depreciation_schedule()` - usar DepreciationService
- [ ] Implementar `get_depreciation_progress()` - usar DepreciationService
- [ ] Invalidar cache de BCR en create/update/delete/restore

### Fase 5: View
- [ ] Crear `backend/app/views/equipment_view.py`
- [ ] Heredar de `BaseView[EquipmentAmortization, EquipmentAmortizationResponse]`
- [ ] Implementar `to_response()` - agregar campos calculados usando DepreciationService
- [ ] Implementar `to_paginated_response()` - usar método base

### Fase 6: Controller
- [ ] Crear `backend/app/controllers/equipment_controller.py`
- [ ] Heredar de `BaseController`
- [ ] Inicializar `EquipmentService` y `EquipmentView`
- [ ] Implementar métodos: `list_equipment()`, `get_equipment()`, `create_equipment()`, `update_equipment()`, `delete_equipment()`, `restore_equipment()`, `get_depreciation_schedule()`, `get_depreciation_progress()`
- [ ] Manejar errores usando métodos base (`_handle_not_found()`, `_handle_business_error()`)
- [ ] Logging usando métodos base (`_log_info()`, `_log_error()`)

### Fase 7: Endpoints
- [ ] Crear `backend/app/api/v1/endpoints/equipment.py`
- [ ] Implementar 8 endpoints: list, create, get, update, delete, restore, schedule, progress
- [ ] Endpoints solo instancian Controller y delegan
- [ ] Aplicar permisos correctos (`require_modify_costs` para create/update/delete)
- [ ] Registrar router en `backend/app/api/v1/router.py`

### Fase 8: Integración BCR
- [ ] Modificar `normalize_to_primary_currency()` en `currency.py` para aceptar `historical_exchange_rate`
- [ ] Modificar `calculate_blended_cost_rate()` en `calculations.py`
- [ ] Agregar query de equipos usando `EquipmentRepository`
- [ ] Implementar conversión con TRM histórica (sin re-expresión mensual)
- [ ] Implementar categorización (Hardware → Overhead, Software → Tools)
- [ ] Agregar equipos a `all_costs`
- [ ] Actualizar `BlendedCostRateResponse` schema con `total_equipment_depreciation` y `equipment_breakdown`

### Fase 9: Tests
- [ ] Tests unitarios de `DepreciationService`
- [ ] Tests unitarios de `EquipmentService` (mockeando repository)
- [ ] Tests unitarios de `EquipmentView`
- [ ] Tests de integración de endpoints
- [ ] Tests de integración BCR con equipos

---

## ⚠️ Puntos Críticos bajo Nueva Arquitectura

### 1. **NO acceder directamente a DB desde Service**
- ✅ Usar `EquipmentRepository` para todas las queries
- ❌ NO usar `db.execute(select(...))` en Service

### 2. **NO acceder directamente a DB desde Controller**
- ✅ Usar `EquipmentService` para toda la lógica
- ❌ NO usar `db.execute()` ni `Repository` directamente en Controller

### 3. **NO poner lógica de negocio en Endpoints**
- ✅ Endpoints solo instancian Controller y delegan
- ❌ NO validaciones, cálculos, o transformaciones en endpoints

### 4. **NO poner transformación de datos en Service**
- ✅ Service retorna Models
- ✅ View transforma Models a Schemas
- ❌ NO usar `model_dump()` o transformaciones en Service

### 5. **Imports absolutos**
- ✅ `from app.models.equipment import EquipmentAmortization`
- ❌ `from ..models.equipment import EquipmentAmortization`

---

## 📚 Referencias

- **Arquitectura:** `.cursorrules/nougram_backend_rules.md`
- **Estado Actual:** `docs/development/BACKEND_IMPLEMENTATION_STATUS_EQUIPMENT_AMORTIZATION.md`
- **Ejemplos MVC:** `backend/app/controllers/project_controller.py`, `backend/app/services/service_service.py`, `backend/app/views/project_view.py`

---

**Última actualización:** 2026-01-25  
**Estado:** ❌ No implementado - Listo para desarrollo bajo arquitectura MVC
