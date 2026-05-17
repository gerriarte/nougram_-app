# Lista de Pendientes - "A:BRA Quote"

**Última actualización:** Enero 2025

## 🔴 Prioridad Alta

### 1. Exportación de Cotizaciones ✅ COMPLETADO
- [x] Generar PDF de cotizaciones
- [x] Plantilla profesional de cotización
- [x] Incluir desglose de servicios, impuestos y totales
- [ ] Opción de enviar por email directamente desde la plataforma (Sprint 2)
- [ ] Formato exportable adicional (DOCX) (Sprint 2)

**Estado:** ✅ PDF funcional. Email y DOCX pendientes para Sprint 2
**Impacto:** Alto - Funcionalidad esencial para uso en producción
**Esfuerzo estimado:** Completado (3 días)

---

### 2. Completar Integraciones
- [ ] **Google Sheets:**
  - [ ] Implementar importación masiva de costos fijos
  - [ ] Implementar importación masiva de miembros del equipo
  - [ ] Plantilla de Google Sheets para importación
  - [ ] Validación de datos importados
  - [ ] UI para gestionar sincronización

- [ ] **Google Calendar:**
  - [ ] Lectura de calendarios del equipo
  - [ ] Cálculo de horas facturables reales basado en disponibilidad
  - [ ] Actualización automática de horas disponibles
  - [ ] UI para conectar calendarios

- [ ] **Apollo.io:**
  - [ ] Autocompletado de información de cliente en formularios
  - [ ] Búsqueda integrada en formulario de proyecto
  - [ ] Guardar datos de Apollo en proyecto

**Impacto:** Alto - Mejora significativa en UX y automatización
**Esfuerzo estimado:** 5-7 días

---

### 3. Mejoras en Dashboard ✅ PARCIALMENTE COMPLETADO
- [ ] Más KPIs avanzados:
  - [ ] Tasa de conversión (Sent → Won)
  - [ ] Valor promedio por proyecto
  - [ ] Proyectos por cliente
  - [ ] Tendencias temporales (mes a mes)
  
- [x] Filtros de fecha:
  - [x] Selección de rango de fechas
  - [ ] Comparación período anterior (Sprint 2)
  - [ ] Filtros por moneda (Sprint 2)
  
- [ ] Gráficos mejorados:
  - [ ] Gráfico de líneas para tendencias
  - [ ] Gráfico de área para ingresos/costos
  - [ ] Tabla interactiva con ordenamiento

**Estado:** ✅ Filtros básicos completados. KPIs avanzados y gráficos pendientes
**Impacto:** Medio-Alto - Mejora insights y toma de decisiones
**Esfuerzo estimado:** 1-2 días restantes (de 3-4 días totales)

---

## 🟡 Prioridad Media

### 4. Testing y Calidad
- [ ] Tests unitarios backend (Pytest):
  - [ ] Tests de modelos
  - [ ] Tests de cálculos (blended cost rate, quote totals)
  - [ ] Tests de endpoints API
  
- [ ] Tests de integración:
  - [ ] Flujo completo de creación de proyecto
  - [ ] Flujo de cálculo de cotizaciones
  - [ ] Flujo de versionado
  
- [ ] Tests E2E frontend (Playwright/Cypress):
  - [ ] Flujo de creación de proyecto
  - [ ] Flujo de edición de cotización
  - [ ] Dashboard y visualizaciones

**Impacto:** Alto - Asegura calidad y reduce bugs
**Esfuerzo estimado:** 5-7 días

---

### 5. Optimizaciones de Rendimiento
- [ ] Optimización de queries:
  - [ ] Revisar eager loading en endpoints
  - [ ] Agregar índices faltantes en BD
  - [ ] Implementar paginación en listados largos
  
- [ ] Caché:
  - [ ] Caché de Blended Cost Rate (invalidar cuando cambien costos)
  - [ ] Caché de datos de dashboard
  - [ ] Caché de servicios activos
  
- [ ] Optimización frontend:
  - [ ] Lazy loading de componentes pesados
  - [ ] Optimización de imágenes
  - [ ] Code splitting mejorado

**Impacto:** Medio - Mejora experiencia de usuario
**Esfuerzo estimado:** 3-4 días

---

### 6. Validaciones y Manejo de Errores ⏳ EN PROGRESO (Sprint 1)
- [ ] Validaciones adicionales:
  - [ ] Validar que no se eliminen servicios/costos usados en proyectos activos (Sprint 1 - Pendiente)
  - [ ] Validar coherencia de monedas
  - [ ] Validar rangos de horas facturables
  
- [ ] Manejo de errores mejorado:
  - [ ] Mensajes de error más descriptivos (Sprint 1 - Pendiente)
  - [ ] Logging estructurado completo
  - [ ] Manejo de errores de red en frontend (Sprint 1 - Pendiente)
  - [ ] Retry automático para requests fallidos (Sprint 1 - Pendiente)

**Estado:** ⏳ En progreso - Sprint 1 (67% completado)  
**Impacto:** Medio - Mejora robustez del sistema  
**Esfuerzo estimado:** 1-2 días restantes (de 2-3 días totales)  
**Ver:** `SPRINT1_INSTRUCCIONES.md` para detalles de implementación

---

### 7. Documentación de API
- [ ] Documentación OpenAPI/Swagger completa
- [ ] Ejemplos de requests/responses
- [ ] Documentación de autenticación
- [ ] Guía de integración para desarrolladores

**Impacto:** Medio - Facilita mantenimiento y onboarding
**Esfuerzo estimado:** 2 días

---

## 🟢 Prioridad Baja

### 8. Funcionalidades Adicionales
- [ ] **Historial de cambios:**
  - [ ] Audit log de cambios en proyectos
  - [ ] Historial de versiones de cotizaciones
  - [ ] Comparación entre versiones
  
- [ ] **Notificaciones:**
  - [ ] Notificaciones cuando márgenes son bajos
  - [ ] Recordatorios de proyectos pendientes
  - [ ] Notificaciones de cambios en costos
  
- [ ] **Búsqueda y Filtros:**
  - [ ] Búsqueda avanzada de proyectos
  - [ ] Filtros múltiples combinados
  - [ ] Guardar filtros favoritos
  
- [ ] **Plantillas:**
  - [ ] Plantillas de proyectos comunes
  - [ ] Plantillas de cotizaciones
  - [ ] Duplicar proyectos existentes

**Impacto:** Bajo-Medio - Mejora UX pero no crítico
**Esfuerzo estimado:** 5-7 días

---

### 9. Mejoras de UI/UX
- [ ] Modo oscuro
- [ ] Personalización de dashboard (drag & drop widgets)
- [ ] Accesibilidad mejorada (ARIA labels, navegación por teclado)
- [ ] Responsive design mejorado para móviles
- [ ] Animaciones y transiciones suaves

**Impacto:** Bajo - Mejora estética y experiencia
**Esfuerzo estimado:** 3-5 días

---

### 10. Internacionalización
- [ ] Soporte multi-idioma (i18n)
- [ ] Traducción de interfaz
- [ ] Formato de fechas/números por región
- [ ] Detección automática de idioma

**Impacto:** Bajo - Solo necesario si hay usuarios internacionales
**Esfuerzo estimado:** 3-4 días

---

## 🔧 Mejoras Técnicas

### 11. Infraestructura
- [ ] Setup de CI/CD completo
- [ ] Ambientes de staging y producción
- [ ] Monitoreo y alertas (Sentry, DataDog)
- [ ] Backup automático de base de datos
- [ ] Health checks y métricas

**Impacto:** Alto - Crítico para producción
**Esfuerzo estimado:** 5-7 días

---

### 12. Seguridad
- [ ] Rate limiting en API
- [ ] Validación de inputs más estricta
- [ ] Protección CSRF
- [ ] Auditoría de seguridad
- [ ] Encriptación de datos sensibles

**Impacto:** Alto - Crítico para producción
**Esfuerzo estimado:** 3-5 días

---

## 📊 Resumen de Pendientes

| Prioridad | Cantidad | Esfuerzo Estimado |
|-----------|----------|-------------------|
| 🔴 Alta | 3 | 11-16 días |
| 🟡 Media | 4 | 12-16 días |
| 🟢 Baja | 2 | 8-11 días |
| 🔧 Técnicas | 2 | 8-12 días |
| **Total** | **11** | **39-55 días** |

---

## 🎯 Recomendación de Priorización

**Sprint 1 (Siguiente):**
1. Exportación de cotizaciones (PDF)
2. Mejoras en Dashboard (filtros de fecha)
3. Validaciones adicionales

**Sprint 2:**
1. Completar Google Sheets integration
2. Testing básico (unitarios críticos)
3. Optimizaciones de rendimiento

**Sprint 3:**
1. Google Calendar integration
2. Apollo.io autocompletado
3. Documentación API

**Sprint 4:**
1. Infraestructura (CI/CD, staging)
2. Seguridad avanzada
3. Testing completo

---

## 📝 Notas

- Los esfuerzos estimados son aproximados y pueden variar según complejidad real
- Las prioridades pueden cambiar según necesidades del negocio
- Se recomienda revisar y actualizar esta lista semanalmente


