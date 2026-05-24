# Plan de Trabajo: Preparación para Producción (Docker + VPS)

**Fecha:** 16 de febrero de 2026  
**Objetivo:** Dockerizar el proyecto completo (frontend + backend) y prepararlo para despliegue en VPS.

---

## 1. Resumen de alcance

| Componente | Stack | Puerto interno |
|------------|-------|----------------|
| Frontend | Next.js 16 | 3000 |
| Backend API | FastAPI + Gunicorn | 8000 |
| Base de datos | PostgreSQL 15 | 5432 |
| Cache/Cola | Redis 7 | 6379 |
| Tareas async | Celery Worker + Beat | - |

---

## 2. Fases del plan

### Fase 1: Dockerización del Frontend
| # | Tarea | Descripción | Archivos |
|---|-------|-------------|----------|
| 1.1 | Crear Dockerfile frontend | Imagen multi-stage: build con Node, serve con standalone/nginx | `frontend/Dockerfile` |
| 1.2 | Crear `.dockerignore` frontend | Excluir node_modules, .next, etc. | `frontend/.dockerignore` |
| 1.3 | Configurar Next.js para standalone | Output standalone para build optimizado | `frontend/next.config.ts` o `.js` |
| 1.4 | Variable API en build | Asegurar `NEXT_PUBLIC_API_URL` se inyecte en build time | - |

### Fase 2: Orquestación Docker Compose
| # | Tarea | Descripción | Archivos |
|---|-------|-------------|----------|
| 2.1 | Crear docker-compose.prod unificado | Incluir frontend, backend, postgres, redis, celery | `docker-compose.prod.yml` |
| 2.2 | Configurar redes y variables | Red interna, variables de entorno por servicio | - |
| 2.3 | Añadir reverse proxy (nginx) | Terminar TLS, rutear /api al backend, / al frontend | `nginx/nginx.conf`, `docker-compose.prod.yml` |
| 2.4 | Healthchecks en todos los servicios | Evitar arranque si dependencias no están listas | - |

### Fase 3: Ajustes de Backend
| # | Tarea | Descripción | Archivos |
|---|-------|-------------|----------|
| 3.1 | Eliminar endpoint de test BCR | Quitar o proteger `/calculations/agency-cost-hour-test` | `backend/app/api/v1/endpoints/costs.py` |
| 3.2 | Cambiar create_all por migraciones | Usar Alembic en startup o script de migración separado | `backend/main.py`, `backend/alembic/` |
| 3.3 | Ajustar healthcheck backend | Usar script Python en vez de curl (no instalado en slim) | `backend/Dockerfile`, `docker-compose.prod.yml` |
| 3.4 | Quitar logs de debug | Eliminar regiones de agent log en costs.py | `backend/app/api/v1/endpoints/costs.py` |

### Fase 4: Configuración y Secretos
| # | Tarea | Descripción | Archivos |
|---|-------|-------------|----------|
| 4.1 | Crear `.env.production.example` raíz | Plantilla con todas las variables para VPS | `.env.production.example` |
| 4.2 | Script de validación de variables | Verificar variables obligatorias antes de levantar | `scripts/check-env.sh` o `.py` |
| 4.3 | Documentar comando de despliegue | README o DEPLOY.md con pasos exactos | `docs/DEPLOY_VPS.md` |

### Fase 5: Seguridad y Producción
| # | Tarea | Descripción | Archivos |
|---|-------|-------------|----------|
| 5.1 | Deshabilitar /docs en producción | O proteger con auth; evitar exposición de API docs | `backend/main.py` |
| 5.2 | Rate limiting en nginx (opcional) | Proteger contra abuso | `nginx/nginx.conf` |
| 5.3 | Headers de seguridad | HSTS, X-Content-Type-Options, etc. | `nginx/nginx.conf` |
| 5.4 | Logs estructurados | Salida JSON para agregación (opcional) | - |

### Fase 6: Testing y Validación
| # | Tarea | Descripción |
|---|-------|-------------|
| 6.1 | Probar stack local con docker-compose.prod | `docker compose -f docker-compose.prod.yml up` |
| 6.2 | Verificar flujo: registro → login → onboarding → admin | E2E manual o script |
| 6.3 | Probar reinicio y healthchecks | Reiniciar servicios y validar recuperación |

---

## 3. Orden recomendado de ejecución

```
Fase 1 (Frontend Docker)  →  Fase 2 (Compose + Nginx)  →  Fase 3 (Backend fixes)
         ↓                            ↓                              ↓
    Fase 4 (Config/Env)  ←——  Fase 5 (Seguridad)  ←——  Fase 6 (Testing)
```

---

## 4. Estructura de archivos objetivo

```
Cotizador/
├── docker-compose.prod.yml      # Orquestación completa
├── .env.production.example      # Plantilla de variables
├── nginx/
│   └── nginx.conf               # Reverse proxy + TLS
├── frontend/
│   ├── Dockerfile
│   └── .dockerignore
├── backend/
│   ├── Dockerfile               # (existente, revisar)
│   └── gunicorn_config.py       # (existente)
├── scripts/
│   └── check-env.sh             # Validación pre-deploy
└── docs/
    ├── PLAN_PREPARACION_PRODUCCION.md  # Este plan
    └── DEPLOY_VPS.md                   # Guía de despliegue
```

---

## 5. Variables de entorno obligatorias (resumen)

| Variable | Servicio | Ejemplo |
|----------|----------|---------|
| `DATABASE_URL` | backend, celery | `postgresql+asyncpg://user:pass@postgres:5432/db` |
| `SECRET_KEY` | backend, celery | ≥32 chars |
| `CORS_ORIGINS` | backend | `https://tudominio.com` |
| `FRONTEND_URL` | backend | `https://tudominio.com` |
| `NEXT_PUBLIC_API_URL` | frontend | `https://tudominio.com/api` |
| `POSTGRES_PASSWORD` | postgres | - |
| `REDIS_URL` (opcional) | backend, celery | `redis://redis:6379/0` |

---

## 6. Criterios de cierre

- [ ] `docker compose -f docker-compose.prod.yml up --build` levanta todo
- [ ] Frontend carga y redirige a login
- [ ] Registro y login funcionan
- [ ] Onboarding persiste en BD
- [ ] Admin (nómina, gastos) lee/escribe en API
- [ ] BCR se calcula correctamente
- [ ] Nginx sirve frontend y hace proxy a /api
- [ ] No hay endpoints de test ni logs de debug expuestos
- [ ] Documentación de despliegue actualizada

---

## 7. Estimación aproximada

| Fase | Esfuerzo |
|------|----------|
| 1 | 2-3 h |
| 2 | 3-4 h |
| 3 | 1-2 h |
| 4 | 1 h |
| 5 | 1-2 h |
| 6 | 2 h |
| **Total** | **10-14 h** |
