# Railway Deploy Checklist (Front + Back)

## 1) Front service (`front-nougram_-app`)

- Build source root: `nougram_front/`
- Dockerfile: `nougram_front/Dockerfile`
- Start command in Railway service settings:
  - Preferred: **empty** (use Dockerfile `CMD`)
  - Explicit alternative: `node server.js`
- Required variable:
  - `NEXT_PUBLIC_API_URL=https://qaback.nougram.co/api/v1`

## 2) Backend service (`back-comfortable-courtesy`)

- Build source root: `backend/`
- Dockerfile: `backend/Dockerfile`
- Start command in Railway service settings:
  - Preferred: **empty** (use Dockerfile `CMD`)
  - Explicit alternative:
    `sh -c "alembic upgrade head && exec gunicorn main:app -c gunicorn_config.py -w 1 -b 0.0.0.0:${PORT:-8000}"`

## 3) Common pitfalls to avoid

- Do not set `cd ...` as start command directly (it fails as executable).
- If `cd` is required, wrap with `sh -c`.
- Do not share front start command with backend, or vice versa.

## 4) CLI quick validation

```bash
railway service status --all
railway deployment list --service "front-nougram_-app"
railway deployment list --service "back-comfortable-courtesy"
railway service logs --service "front-nougram_-app" --latest --lines 200
railway service logs --service "back-comfortable-courtesy" --latest --lines 200
```

