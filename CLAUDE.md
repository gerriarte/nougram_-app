# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Nougram** is a multi-tenant SaaS platform for agency profitability management — quote calculation, cost tracking, and financial insights for digital agencies. Stack: Python 3.11 + FastAPI (backend), Next.js 16 + React 19 (frontend), PostgreSQL 15, Redis (optional, for Celery).

## Repository Structure

```
NougramApp/
├── backend/              # FastAPI REST API
│   ├── app/
│   │   ├── api/v1/endpoints/  # 25+ endpoint modules
│   │   ├── core/             # config, database, auth, permissions, email
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── repositories/     # Data access layer (~28 repos)
│   │   ├── schemas/          # Pydantic request/response models
│   │   └── services/         # Business logic (~16 services)
│   ├── alembic/          # DB migrations
│   ├── tests/            # unit/, integration/, contract/
│   └── main.py           # Entry point
├── frontend/        # Main frontend (Next.js 16)
├── frontend/             # Legacy frontend (being retired)
└── Nougram Landing/      # Marketing landing page (Next.js)
```

## Development Commands

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
alembic upgrade head

# Run
uvicorn main:app --reload      # Dev (port 8000)
gunicorn main:app -c gunicorn_config.py  # Prod

# Test (config in pyproject.toml — runs coverage by default)
pytest                         # All tests with coverage
pytest tests/unit/             # Unit tests only
pytest tests/integration/      # Integration tests only
pytest -k "test_name"          # Single test
pytest -m unit                 # By marker

# Lint
ruff check . --fix
ruff format .
```

### Frontend (frontend)

```bash
cd frontend
npm install
npm run dev         # Dev server (port 3000)
npm run build
npm run lint
npx tsc --noEmit    # Type check
npm run test:e2e    # Playwright E2E
```

### Infrastructure

```bash
docker-compose up -d           # Local PostgreSQL on :5435
```

## Architecture

### Multi-tenancy

Every request is scoped to an `org_id` extracted from the JWT. Repositories filter all queries by organization. Tenant isolation is enforced at the DB layer — never bypass `org_id` filters.

### Request Flow

```
HTTP → FastAPI → Depends(get_current_user) → Router → Endpoint → Service → Repository → DB
```

- **Auth**: JWT bearer tokens. `get_current_user()` in `app/core/security.py` validates the token and returns a `User` with `org_id`. Access tokens: 30 min; refresh tokens: 7 days.
- **Permissions**: RBAC via `app/core/permissions.py`. Roles include `SUPER_ADMIN`, `ADMIN_FINANCIERO`, `PRODUCT_MANAGER`, etc. Feature flags `FEATURE_ROLES` / `FEATURE_ROLES_ENFORCE` control enforcement.
- **Rate limiting**: slowapi middleware, configured per-endpoint.

### Backend Layers

- `endpoints/` — thin FastAPI handlers; validate input, call services, return schemas
- `services/` — business logic; orchestrate repositories and external APIs
- `repositories/` — SQLAlchemy async queries; always scoped to `org_id`
- `models/` — SQLAlchemy ORM; many models use soft-delete patterns
- `schemas/` — Pydantic v2 for validation and serialization

### Key Services

| Service | Responsibility |
|---------|---------------|
| `project_service.py` (~55KB) | Quote calculations, PDF/DOCX export, email delivery |
| `onboarding_service.py` (~63KB) | Setup wizard, Google Sheets import |
| `ai_service.py` (~35KB) | Document parsing, NLP config analysis, insights |
| `capacity_service.py` | Billable hours, team utilization |
| `credit_service.py` | Account credits and transactions |

### Email System

`app/core/email.py` sends transactional email exclusively through **Resend** (httpx against the Resend API) — the previous multi-provider abstraction (SMTP/MailerSend, selected via `EMAIL_PROVIDER`) was removed. All sends run as FastAPI background tasks. Configured via `RESEND_*` env vars in `app/core/config.py`:
- `RESEND_API_KEY` — API key
- `RESEND_FROM_EMAIL` / `RESEND_FROM_NAME` — sender identity (name defaults to `"Nougram"`)
- `RESEND_BASE_URL` — API base (defaults to `https://api.resend.com`)
- `RESEND_TEMPLATE_*_ID` — Resend template IDs (e.g. password reset)

### Database

Async SQLAlchemy 2.0 + asyncpg. Migrations via Alembic (always use `alembic upgrade head`, not `CREATE_SCHEMA_ON_STARTUP`). The `CREATE_SCHEMA_ON_STARTUP` flag is only for quick local bootstrapping and is disabled in production.

### API Docs

Available at `/docs` (Swagger) and `/redoc` in non-production environments only.

## Configuration

Settings are in `app/core/config.py` (Pydantic `BaseSettings`). Required env vars:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` |
| `SECRET_KEY` | JWT signing key (32+ chars) |
| `CORS_ORIGINS` | Comma-separated frontend URLs |
| `FRONTEND_URL` | For invitation/reset links |
| `RESEND_API_KEY` | Resend API key (transactional email) |
| `RESEND_FROM_EMAIL` | Verified sender address |
| `ENVIRONMENT` | `development` \| `staging` \| `production` |

Copy `backend/.env.production.example` to `backend/.env` for local setup.

## Git Branching (GitFlow)

| Branch | Environment | Purpose |
|--------|-------------|---------|
| `main` | Production (Railway prod) | Stable releases only |
| `develop` | Staging (Railway staging / `qa.nougram.co`) | Integration |
| `feature/*` | Local | New features → PR to develop |
| `fix/*` | Local | Bug fixes → PR to develop |
| `hotfix/*` | Local | Critical prod fixes → PR to main + merge to develop |

Always work from `develop`, never merge `develop` directly to `main`. Use `release/` branches to prepare production deploys.

## CI/CD

GitHub Actions workflows:
- **backend-tests.yml**: Pytest on Python 3.11 + PostgreSQL 15
- **backend-lint.yml**: Ruff check + format check
- **frontend-ci.yml**: ESLint + TypeScript + Next.js build

Railway auto-deploys: `main` → prod, `develop` → staging. The backend Dockerfile runs `alembic upgrade head` before starting Gunicorn.

## Testing Notes

- Test DB uses SQLite in-memory (`:memory:`) — async, no external service needed
- `backend/tests/conftest.py` contains fixtures for DB session, test client, and auth
- Test markers: `unit`, `integration`, `slow`
- Run a specific test file: `pytest tests/unit/test_auth.py -v`
