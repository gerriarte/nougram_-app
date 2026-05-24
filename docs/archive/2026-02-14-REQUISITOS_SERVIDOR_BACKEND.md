# Requisitos de Servidor - Backend (Consultar con Proveedor)

**Proyecto:** Cotizador / Nougram  
**Fecha:** 14 de febrero de 2026  
**Uso:** Documento resumido para solicitar cotización o validar oferta de hosting

---

## 1. Resumen Ejecutivo

Aplicación API REST (FastAPI + Python 3.11) con PostgreSQL y Redis. Requiere soporte para contenedores Docker o despliegue tradicional.

---

## 2. Especificaciones de Servidor

| Requisito | Especificación |
|-----------|----------------|
| **Sistema operativo** | Linux (Ubuntu 22.04 LTS, Debian 12, o similar) |
| **Python** | 3.11 o superior |
| **Memoria RAM** | Mínimo 1 GB; recomendado 2 GB |
| **CPUs** | 1 vCPU mínima; 2 vCPU recomendado para producción |
| **Disco** | 10 GB SSD mínimo |
| **Red** | Tráfico HTTPS (443) saliente; APIs externas (Google, OpenAI, Stripe) |

---

## 3. Infraestructura Requerida

| Servicio | Especificación |
|----------|----------------|
| **Base de datos** | PostgreSQL 15+ |
| **Cache/Cola** | Redis 7+ |
| **Puerto API** | 8000 (interno); exponer vía reverse proxy (80/443) |

---

## 4. Dependencias Externas (conectividad saliente)

- **Google APIs** (OAuth, Sheets): `*.googleapis.com`
- **OpenAI** (opcional): `api.openai.com`
- **Stripe** (opcional): `api.stripe.com`
- **SMTP** (opcional): puerto 587 (TLS)
- **Exchange rates** (opcional): `api.exchangerate-api.com`

---

## 5. Variables de Entorno Obligatorias

| Variable | Descripción |
|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/dbname` |
| `SECRET_KEY` | Clave secreta para JWT (≥32 caracteres) |
| `GOOGLE_CLIENT_ID` | OAuth Google |
| `GOOGLE_CLIENT_SECRET` | OAuth Google |
| `GOOGLE_SERVICE_ACCOUNT_PATH` | Ruta a JSON de service account |
| `GOOGLE_SHEETS_ID` | ID de hoja de cálculo |
| `CORS_ORIGINS` | Dominios frontend permitidos (ej: `https://app.example.com`) |
| `FRONTEND_URL` | URL base del frontend |
| `ENVIRONMENT` | `production` |

---

## 6. Variables Opcionales

| Variable | Descripción |
|---------|-------------|
| `SMTP_*` | Configuración de correo (envío de invitaciones, notificaciones) |
| `OPENAI_API_KEY` / `GOOGLE_AI_API_KEY` | IA para sugerencias |
| `STRIPE_*` | Facturación y suscripciones |
| `EXCHANGE_RATE_API_KEY` | Tasas de cambio |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | URL de Redis para tareas asíncronas |

---

## 7. Comando de Ejecución

```
gunicorn main:app -c gunicorn_config.py
```

O con variables Gunicorn:
- `GUNICORN_BIND=0.0.0.0:8000`
- `GUNICORN_WORKERS` (default: 2×CPUs + 1)
- `GUNICORN_TIMEOUT=120`

---

## 8. Requisitos del Entorno Python

```
Python 3.11
fastapi, uvicorn, gunicorn, sqlalchemy[asyncio], asyncpg
pydantic, python-jose, passlib[bcrypt]
```

Instalación típica: `pip install -r requirements.txt`

---

## 9. Migraciones de Base de Datos

- ORM: Alembic  
- Comando: `alembic upgrade head`  
- Ejecutar una vez tras el despliegue o como paso del pipeline de CI/CD.

---

## 10. Checklist para Proveedor

- [ ] PostgreSQL 15+ disponible
- [ ] Redis 7+ disponible (o compatible)
- [ ] Python 3.11 en el entorno
- [ ] Soporte Docker (opcional)
- [ ] SSL/TLS para HTTPS
- [ ] Salida a internet permitida (APIs externas)
- [ ] Mínimo 1–2 GB RAM
- [ ] Puerto 8000 interno (o mapeo configurado)

---

## 11. Referencia Rápida - Puertos

| Puerto | Servicio |
|--------|----------|
| 8000 | API Backend (interno) |
| 5432 | PostgreSQL |
| 6379 | Redis |

---

*Documento de referencia para consultas técnicas con proveedores de hosting.*
