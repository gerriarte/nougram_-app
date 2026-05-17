# 📋 Sprint 2 - Plan de Trabajo

**Fecha de Inicio:** 12 de Diciembre, 2025  
**Estado:** 🟡 En Progreso

---

## 🎯 Objetivos del Sprint 2

1. **Testing Básico** - Implementar tests unitarios críticos
2. **Optimizaciones de Rendimiento** - Mejorar queries y agregar caché
3. **Mejoras en Dashboard** - Filtros avanzados y comparaciones
4. **Exportación Mejorada** - Email y formato DOCX para cotizaciones

---

## ✅ Tareas del Sprint 2

### Sprint 2.1: Testing Básico (Prioridad Alta)

**Objetivo:** Implementar tests unitarios para funcionalidades críticas

#### 2.1.1: Setup de Testing
- [ ] Configurar Pytest en backend
- [ ] Configurar estructura de tests
- [ ] Crear fixtures para base de datos de prueba
- [ ] Configurar coverage

#### 2.1.2: Tests de Cálculos
- [ ] Test de Blended Cost Rate
- [ ] Test de cálculo de cotizaciones
- [ ] Test de aplicación de impuestos
- [ ] Test de conversión de monedas

#### 2.1.3: Tests de Repositorios
- [ ] Tests de BaseRepository
- [ ] Tests de CostRepository
- [ ] Tests de ServiceRepository
- [ ] Tests de TaxRepository

#### 2.1.4: Tests de Endpoints Críticos
- [ ] Test de login
- [ ] Test de creación de proyecto
- [ ] Test de cálculo de cotización
- [ ] Test de soft delete

**Esfuerzo estimado:** 2-3 días

---

### Sprint 2.2: Optimizaciones de Rendimiento (Prioridad Alta)

**Objetivo:** Mejorar el rendimiento de queries y agregar caché

#### 2.2.1: Optimización de Queries
- [ ] Revisar eager loading en endpoints
- [ ] Agregar índices faltantes en BD
- [ ] Implementar paginación en listados largos
- [ ] Optimizar queries N+1

#### 2.2.2: Implementar Caché
- [ ] Caché de Blended Cost Rate (invalidar cuando cambien costos)
- [ ] Caché de datos de dashboard
- [ ] Caché de servicios activos
- [ ] Sistema de invalidación de caché

#### 2.2.3: Optimización Frontend
- [ ] Lazy loading de componentes pesados
- [ ] Optimización de imágenes
- [ ] Code splitting mejorado

**Esfuerzo estimado:** 2-3 días

---

### Sprint 2.3: Mejoras en Dashboard (Prioridad Media)

**Objetivo:** Agregar filtros avanzados y comparaciones

#### 2.3.1: Filtros Avanzados
- [ ] Comparación período anterior
- [ ] Filtros por moneda
- [ ] Filtros por cliente
- [ ] Filtros por estado de proyecto

#### 2.3.2: KPIs Avanzados
- [ ] Tasa de conversión (Sent → Won)
- [ ] Valor promedio por proyecto
- [ ] Proyectos por cliente
- [ ] Tendencias temporales (mes a mes)

#### 2.3.3: Gráficos Mejorados
- [ ] Gráfico de líneas para tendencias
- [ ] Gráfico de área para ingresos/costos
- [ ] Tabla interactiva con ordenamiento

**Esfuerzo estimado:** 2-3 días

---

### Sprint 2.4: Exportación Mejorada (Prioridad Media)

**Objetivo:** Agregar email y formato DOCX para cotizaciones

#### 2.4.1: Envío por Email
- [ ] Configurar servicio de email (SMTP/SendGrid)
- [ ] Endpoint para enviar cotización por email
- [ ] UI para enviar desde la plataforma
- [ ] Plantilla de email

#### 2.4.2: Exportación DOCX
- [ ] Instalar librería para DOCX (python-docx)
- [ ] Generar DOCX desde cotización
- [ ] Botón de descarga DOCX
- [ ] Validar formato

**Esfuerzo estimado:** 2-3 días

---

## 📊 Resumen

| Tarea | Prioridad | Esfuerzo | Estado |
|-------|-----------|----------|--------|
| 2.1: Testing Básico | Alta | 2-3 días | ⏳ Pendiente |
| 2.2: Optimizaciones | Alta | 2-3 días | ⏳ Pendiente |
| 2.3: Dashboard | Media | 2-3 días | ⏳ Pendiente |
| 2.4: Exportación | Media | 2-3 días | ⏳ Pendiente |
| **Total** | - | **8-12 días** | - |

---

## 🎯 Orden de Implementación Recomendado

1. **Sprint 2.1** - Testing Básico (fundación para todo)
2. **Sprint 2.2** - Optimizaciones (mejora rendimiento inmediato)
3. **Sprint 2.3** - Dashboard (mejora UX)
4. **Sprint 2.4** - Exportación (funcionalidad adicional)

---

## 📝 Notas

- Las tareas pueden ejecutarse en paralelo según disponibilidad
- Priorizar testing y optimizaciones antes de nuevas funcionalidades
- Mantener documentación actualizada durante el desarrollo

---

**Última actualización:** 12 de Diciembre, 2025















