# Estado de Documentos en Raíz de `/docs`

**Fecha:** 2026-01-25  
**Total de archivos:** 27 archivos

---

## 📋 Categorización de Documentos

### ✅ Documentos Principales (Mantener en Raíz)
Estos documentos son de referencia general y deben permanecer en la raíz:

1. **`2026-02-07-README.md`** ✅ - Índice principal de documentación
2. **`2025-12-13-PRD.md`** ✅ - Product Requirements Document (documento principal)
3. **`PRD_UX_UI.md`** ✅ - PRD específico de UX/UI
4. **`PRODUCTION_READINESS.md`** ✅ - Checklist de producción
5. **`TROUBLESHOOTING.md`** ✅ - Guía de solución de problemas
6. **`INICIO_RAPIDO.md`** ✅ - Guía de inicio rápido (útil para nuevos desarrolladores)

**Total: 6 archivos - Mantener en raíz**

---

### 📚 Documentación de API (Mover a `api/`)
Documentación de endpoints de API que debería organizarse en una carpeta:

7. **`API_AI.md`** ⚠️ - Documentación API de IA → Mover a `api/API_AI.md`
8. **`API_BILLING.md`** ⚠️ - Documentación API de Billing → Mover a `api/API_BILLING.md`
9. **`API_FORMATO_DECIMAL.md`** ⚠️ - Formato decimal en API → Mover a `api/API_FORMATO_DECIMAL.md`
10. **`API_ORGANIZATIONS.md`** ⚠️ - Documentación API de Organizaciones → Mover a `api/API_ORGANIZATIONS.md`

**Total: 4 archivos - Crear `docs/api/` y mover**

---

### 🧪 Documentación de Testing (Mover a `testing/`)
Documentación relacionada con pruebas y testing:

11. **`TESTING_AI_SUGGESTIONS.md`** ⚠️ - Testing de sugerencias IA → Mover a `testing/TESTING_AI_SUGGESTIONS.md`
12. **`TESTING_FRONTEND.md`** ⚠️ - Testing frontend → Mover a `testing/TESTING_FRONTEND.md`
13. **`TESTING_TENANT_ISOLATION.md`** ⚠️ - Testing multi-tenant → Mover a `testing/TESTING_TENANT_ISOLATION.md`
14. **`PRUEBA_FRONTEND.md`** ⚠️ - Guía de prueba frontend → Mover a `testing/PRUEBA_FRONTEND.md`

**Total: 4 archivos - Crear `docs/testing/` y mover**

---

### ⚙️ Guías de Configuración (Mover a `development/guides/`)
Guías de configuración y setup:

15. **`CELERY_SETUP.md`** ⚠️ - Configuración Celery → Mover a `development/guides/CELERY_SETUP.md`
16. **`CONFIGURACION_MONEDA_PRIMARIA.md`** ⚠️ - Configuración moneda → Mover a `development/guides/CONFIGURACION_MONEDA_PRIMARIA.md`
17. **`I18N_SETUP.md`** ⚠️ - Configuración i18n → Mover a `development/guides/I18N_SETUP.md`
18. **`I18N_MIGRATION_EXAMPLE.md`** ⚠️ - Ejemplo migración i18n → Mover a `development/guides/I18N_MIGRATION_EXAMPLE.md`
19. **`LOGGING_FORMAT.md`** ⚠️ - Formato de logging → Mover a `development/guides/LOGGING_FORMAT.md`
20. **`MIGRACION_BASE_DATOS.md`** ⚠️ - Migración BD → Mover a `development/guides/MIGRACION_BASE_DATOS.md`
21. **`FRONTEND_BACKEND_SETUP.md`** ⚠️ - Setup frontend/backend → Mover a `development/guides/FRONTEND_BACKEND_SETUP.md`

**Total: 7 archivos - Crear `docs/development/guides/` y mover**

---

### 📖 Documentación de Conceptos (Mover a `development/concepts/`)
Documentación sobre conceptos y modelos del sistema:

22. **`CAPACIDADES_ROLES.md`** ⚠️ - Capacidades y roles → Mover a `development/concepts/CAPACIDADES_ROLES.md`
23. **`MODELO_FACTURACION.md`** ⚠️ - Modelo de facturación → Mover a `development/concepts/MODELO_FACTURACION.md`
24. **`MULTI_TENANT_ADMIN.md`** ⚠️ - Admin multi-tenant → Mover a `development/concepts/MULTI_TENANT_ADMIN.md`
25. **`FRONTEND_DASHBOARDS.md`** ⚠️ - Dashboards frontend → Mover a `development/FRONTEND_DASHBOARDS.md`
26. **`IMPLEMENTACION_DESIGN_SYSTEM.md`** ⚠️ - Design system → Mover a `development/IMPLEMENTACION_DESIGN_SYSTEM.md`

**Total: 5 archivos - Crear `docs/development/concepts/` y mover (o mantener algunos en raíz)**

---

### 🗑️ Documentos Deprecados (Mover a `deprecated/`)
Documentos que ya no aplican o están obsoletos:

27. **`ORGANIZACION_DOCUMENTACION.md`** ❌ - Documento sobre organización antigua (12 Dic 2025) que describe estructura que ya no aplica → Mover a `deprecated/old-analysis/ORGANIZACION_DOCUMENTACION.md`

**Total: 1 archivo - Mover a deprecated**

---

## 📊 Resumen de Acciones Recomendadas

### Estructura Propuesta:

```
docs/
├── README.md                          # Índice principal
├── PRD.md                            # PRD principal
├── PRD_UX_UI.md                      # PRD UX/UI
├── PRODUCTION_READINESS.md           # Checklist producción
├── TROUBLESHOOTING.md                # Solución problemas
├── INICIO_RAPIDO.md                  # Guía inicio rápido
│
├── api/                              # 📚 NUEVA: Documentación API
│   ├── API_AI.md
│   ├── API_BILLING.md
│   ├── API_FORMATO_DECIMAL.md
│   └── API_ORGANIZATIONS.md
│
├── testing/                          # 🧪 NUEVA: Documentación Testing
│   ├── TESTING_AI_SUGGESTIONS.md
│   ├── TESTING_FRONTEND.md
│   ├── TESTING_TENANT_ISOLATION.md
│   └── PRUEBA_FRONTEND.md
│
├── development/
│   ├── guides/                       # ⚙️ NUEVA: Guías configuración
│   │   ├── CELERY_SETUP.md
│   │   ├── CONFIGURACION_MONEDA_PRIMARIA.md
│   │   ├── I18N_SETUP.md
│   │   ├── I18N_MIGRATION_EXAMPLE.md
│   │   ├── LOGGING_FORMAT.md
│   │   ├── MIGRACION_BASE_DATOS.md
│   │   └── FRONTEND_BACKEND_SETUP.md
│   │
│   └── concepts/                    # 📖 NUEVA: Conceptos sistema
│       ├── CAPACIDADES_ROLES.md
│       ├── MODELO_FACTURACION.md
│       └── MULTI_TENANT_ADMIN.md
│
└── deprecated/
    └── old-analysis/
        └── ORGANIZACION_DOCUMENTACION.md  # ❌ Movido
```

### Archivos a Mover:

- **API (4 archivos)** → `docs/api/`
- **Testing (4 archivos)** → `docs/testing/`
- **Guías (7 archivos)** → `docs/development/guides/`
- **Conceptos (5 archivos)** → `docs/development/concepts/` o `development/`
- **Deprecados (1 archivo)** → `docs/deprecated/old-analysis/`

**Total a mover: 21 archivos**  
**Total a mantener en raíz: 6 archivos**

---

## 🎯 Prioridad de Reorganización

### 🔴 Alta Prioridad (Hacer ahora):
1. Mover `ORGANIZACION_DOCUMENTACION.md` a deprecated (obsoleto)
2. Crear `docs/api/` y mover archivos `API_*.md` (4 archivos)
3. Crear `docs/testing/` y mover archivos `TESTING_*.md` y `PRUEBA_FRONTEND.md` (4 archivos)

### 🟡 Media Prioridad (Hacer después):
4. Crear `docs/development/guides/` y mover guías de configuración (7 archivos)
5. Crear `docs/development/concepts/` y mover conceptos (3 archivos)
6. Mover `FRONTEND_DASHBOARDS.md` y `IMPLEMENTACION_DESIGN_SYSTEM.md` a `development/` (2 archivos)

### 🟢 Baja Prioridad (Opcional):
- Revisar si algunos conceptos deberían permanecer en raíz
- Considerar crear un índice en cada nueva carpeta

---

## ✅ Estado Actual

- ✅ **6 archivos** permanecen en raíz (documentos principales)
- ⚠️ **21 archivos** necesitan reorganización
- ❌ **1 archivo** debe moverse a deprecated

---

**Última actualización:** 2026-01-25
