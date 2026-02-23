# Nougram

API REST + Dashboard. Python 3.11 | FastAPI | Next.js | PostgreSQL 15 | Redis.

## Estructura

```
nougram_-app/
├── backend/          # Core Financiero + API
│   ├── app/
│   │   ├── core/     # Motor fiscal, cálculos, config
│   │   ├── api/      # Endpoints REST
│   │   ├── models/   # ORM
│   │   ├── services/
│   │   └── repositories/
│   ├── alembic/      # Migraciones
│   └── main.py
├── nougram_front/    # Frontend principal (Next.js)
├── frontend/         # Frontend legacy (en retiro controlado)
│   └── src/
├── docker-compose.yml
└── docker-compose.prod.yml
```

## Ambientes

| Ambiente   | Uso                    |
|-----------|------------------------|
| development | Local (.env)         |
| staging   | Pre-producción        |
| production| Clientes reales       |

## Quick Start

```bash
# 1. Variables de entorno (copiar .env.example)
cp backend/.env.production.example backend/.env
# Editar DATABASE_URL, SECRET_KEY, GOOGLE_*, CORS_ORIGINS

# 2. Infraestructura
docker-compose up -d

# 3. Backend
cd backend && pip install -r requirements.txt && alembic upgrade head && gunicorn main:app -c gunicorn_config.py

# 4. Frontend principal
cd nougram_front && npm install && npm run build && npm start
```

## Requisitos

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+ (opcional, para Celery)

## Puertos

| Puerto | Servicio   |
|--------|------------|
| 8000   | API Backend|
| 3000   | Frontend   |
| 5432   | PostgreSQL |
| 6379   | Redis      |

## Correo transaccional (estado actual)

Implementado en backend:
- Envio de invitaciones (`/organizations/{id}/invitations`)
- Envio de cotizaciones (`/projects/{project_id}/quotes/{quote_id}/send-email`)
- Recuperacion de contrasena:
  - `POST /api/v1/auth/forgot-password`
  - `POST /api/v1/auth/reset-password`
- Correo de bienvenida al registrar organizacion (`POST /api/v1/organizations/register`)

Variables obligatorias para produccion:
- `SMTP_HOST`
- `SMTP_PORT` (normalmente `587`)
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`
- `SMTP_FROM_NAME`
- `SMTP_USE_TLS` (`true`)
- `FRONTEND_URL` (base URL para links de reset/invitacion)
- `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` (ej. `60`)

Pendiente para finalizar despues:
- Verificar entregabilidad de dominio (SPF, DKIM, DMARC)
- Configurar proveedor final SMTP (SES/SendGrid/Resend) con credenciales productivas
- Ejecutar smoke test E2E en produccion:
  - Registro nuevo tenant -> correo de bienvenida
  - Forgot password -> reset con enlace
  - Invitacion owner -> recepcion y aceptacion
  - Envio de cotizacion con adjuntos
