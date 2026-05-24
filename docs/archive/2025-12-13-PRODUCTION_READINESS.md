# Production Readiness Checklist

This document summarizes the remaining work required to exercise the tool in a production-like environment.

## 1. Environment Configuration (.env)

### Backend (`backend/.env`)

| Variable | Description |
| --- | --- |
| `ENVIRONMENT=production` | Used by FastAPI to toggle prod behaviours. |
| `SECRET_KEY=<generate 32+ random chars>` | JWT signing key (keep secret). |
| `ACCESS_TOKEN_EXPIRE_MINUTES=30` | Token lifetime. |
| `DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DB_NAME` | Production Postgres DSN. |
| `CORS_ORIGINS=https://app.example.com` | Comma-separated allowed origins. |
| `FEATURE_ROLES=true` / `FEATURE_ROLES_ENFORCE=true` | Re-enable RBAC when ready. |
| `OPENAI_API_KEY=<optional>` | Only if AI advisor remains enabled. |
| `LOG_LEVEL=info` | Desired logging verbosity. |

### Frontend (`frontend/.env.production`)

| Variable | Description |
| --- | --- |
| `NEXT_PUBLIC_API_URL=https://api.example.com/api/v1` | Public API endpoint. |
| `NEXT_PUBLIC_APP_URL=https://app.example.com` | Base UI URL (used for redirects). |

> Generate production secrets with a password manager or `openssl rand -base64 48` and store them in your deployment platform’s secrets manager.

## 2. Containerization & CI/CD

1. **Dockerfiles**
   - Backend: build from `python:3.11`, copy code, install requirements (use `pip install --no-cache-dir -r requirements.txt`), run `alembic upgrade head`, start `uvicorn`.
   - Frontend: build static bundle using `node:18`, then serve with `nginx` / `vercel` / `next start` depending on hosting.
2. **Docker Compose (staging)**
   - Services: `backend`, `frontend`, `postgres`, `pgadmin` (optional).
   - Mount `alembic` migrations and ensure health checks (e.g., `/health`).
3. **CI Pipeline**
   - Lint + type check (e.g., `flake8`/`ruff`, `mypy`, `eslint`).
   - Run unit tests (if available) and smoke tests against ephemeral DB.
   - Build Docker images and push to registry (tag with `git sha`).
4. **CD Pipeline**
   - Deploy to staging automatically on merge to `main`.
   - Manual promotion to production with approvals.
   - Run post-deploy smoke test (e.g., curl login, dashboard).

## 3. Database Provisioning

1. **Provision Postgres** (managed service such as RDS/Azure PG).
   - Create database, enable automated backups (>= 7 days retention) and PITR.
   - Enforce SSL connections.
2. **Run migrations**
   ```bash
   cd backend
   alembic upgrade head
   ```
3. **Seed initial data**
   - Ensure admin user exists. With the new hashed password column:
     ```sql
     INSERT INTO users (email, full_name, role, hashed_password)
     VALUES (
       'gerriarte@abralatam.com',
       'Gerri Arte',
       'super_admin',
       '$2b$12$XumK9TnQwcU44P6IGNto4uq8RspSdvGcxeiUNCqHuAHcZXI5G9bWi' -- hash for "Abracolombia"
     )
     ON CONFLICT (email) DO UPDATE
       SET full_name = EXCLUDED.full_name,
           role = EXCLUDED.role,
           hashed_password = EXCLUDED.hashed_password;
     ```
   - Rotate the password after first login.

## 4. HTTPS, CORS, Logging & Monitoring

- **HTTPS**: terminate TLS at a reverse proxy/load balancer (e.g., AWS ALB, Nginx). Obtain certificates via ACM/Let’s Encrypt.
- **CORS**: restrict to production domains in `CORS_ORIGINS`. For staging, use environment-specific domain.
- **Logging**:
  - Backend: configure structured JSON logs (e.g., `LOG_LEVEL=info`, add uvicorn access logs).
  - Frontend: integrate browser error logging (Sentry/LogRocket) if desired.
- **Monitoring**:
  - Use APM/metrics (Datadog, Prometheus/Grafana) for CPU, memory, request latency, error rate.
  - Set up health-check endpoint (`/health`) for uptime monitoring.
- **Backups**:
  - Verify automated DB snapshots.
  - Store infrastructure-as-code or runbook for manual restore.

## 5. Operational Documentation

- **Credentials & Access**
  - Store secrets in a vault (AWS Secrets Manager, HashiCorp Vault).
  - Maintain list of on-call engineers with access rights.
- **Support Procedures**
  - Document how to:
    - Restart services (Docker compose, Kubernetes rollout, etc.).
    - Run migrations on deploy.
    - Reset user passwords (SQL update using bcrypt hash).
    - Disable user accounts.
- **Incident Response**
  - Define severity levels and communication channels (Slack, email).
  - Provide checklist for capturing logs/metrics.
- **Change Management**
  - Require PR reviews and automated checks.
  - Use feature flags (`FEATURE_ROLES`, etc.) for controlled rollouts.

Keeping this checklist up-to-date ensures everyone knows the remaining gap between “works locally” and “production-ready”.


