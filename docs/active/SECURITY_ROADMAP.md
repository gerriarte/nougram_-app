# Security Roadmap — Nougram Backend

Auditoría realizada: 2026-05-17  
Metodología: análisis estático del código fuente  
Rama base: `develop` @ `6ac2106`

---

## Leyenda

| Estado | Significado |
|--------|-------------|
| ✅ Resuelto | Implementado y en producción |
| 🔄 En progreso | En desarrollo activo |
| ⏳ Pendiente | Priorizado, no iniciado |
| 💤 Backlog | Identificado, sin fecha |
| ❌ Descartado | Revisado y descartado con justificación |

---

## Hallazgos críticos

### SEC-001 — `.env` expuesto en repositorio
**Severidad:** CRÍTICO → ❌ Descartado (falso positivo)  
**Archivo:** `backend/.env`

El agente detectó el archivo `.env` local con claves reales. Verificado con `git ls-files` y `git log`: el archivo **nunca fue commiteado**. El `.gitignore` raíz tiene la regla `.env.*` activa desde el inicio del repositorio.

**Acción tomada:** ninguna — el control ya existe.  
**Recomendación activa:** si la `OPENAI_API_KEY` se compartió por canales externos (Slack, email, Notion), rotar de forma preventiva.

---

### SEC-002 — `SECRET_KEY` débil en producción
**Severidad:** CRÍTICO → ⏳ Pendiente (acción en Railway)  
**Aplica a:** Railway prod + Railway staging

El `.env` local usa `dev-secret-key-change-in-production`. No está en git, pero hay que confirmar que Railway esté usando una clave fuerte.

**Clave generada (256 bits):**
```
77ddf0e5dc09aba947beea75283bb01e19e20acb19bb4b1ab72523c2a2d648e6
```

**Pasos:**
1. Railway → servicio backend prod → Variables → `SECRET_KEY` = valor de arriba
2. Railway → servicio backend staging → Variables → generar uno diferente
3. Todos los JWT activos se invalidan al reiniciar — usuarios deben volver a hacer login

**Nota:** `config.py` no valida entropía mínima del `SECRET_KEY`. Si se quiere agregar validación:
```python
@validator("SECRET_KEY")
def validate_secret_key(cls, v):
    if len(v) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters")
    return v
```

---

## Hallazgos altos

### SEC-003 — Raw SQL con rol por defecto en `users.py`
**Severidad:** ALTO → ⏳ Pendiente  
**Archivo:** `backend/app/api/v1/endpoints/users.py:47-54`

Raw SQL que asigna `product_manager` a cualquier usuario con rol `NULL`:
```sql
COALESCE(role::text, 'product_manager') as role
```
Bypasea validación ORM. Si un usuario tiene rol NULL por error de datos, queda con permisos de `product_manager` de forma silenciosa.

**Fix:** reemplazar el raw SQL con una query SQLAlchemy estándar y manejar el NULL explícitamente en la capa de permisos (ya existe `ensure_role_string()` en `permissions.py`).

---

### SEC-004 — Stripe webhook: `organization_id` del metadata no validado
**Severidad:** ALTO → ⏳ Pendiente  
**Archivo:** `backend/app/api/v1/endpoints/stripe_webhooks.py:93`

El `organization_id` se toma directamente del metadata del evento de Stripe sin verificar que corresponda a un tenant real y activo:
```python
organization_id = int(organization_id)  # del metadata, sin validación
```
Un webhook forjado o con metadata manipulado podría afectar el estado de billing de una org arbitraria.

**Fix:**
1. Verificar firma del webhook con `stripe.Webhook.construct_event()` (ya implementado, confirmar)
2. Después de extraer `organization_id`, hacer `SELECT` para confirmar que la org existe y el Stripe customer ID coincide con el evento

---

### SEC-005 — Sin revocación de refresh tokens
**Severidad:** ALTO → 💤 Backlog  
**Archivo:** `backend/app/core/security.py:52-64`

Los refresh tokens (7 días de vida) no se pueden invalidar server-side. Un token robado da acceso por hasta una semana aunque el usuario cambie su contraseña.

**Fix (opción mínima):** agregar tabla `revoked_tokens` con el JTI del token y verificar en `decode_refresh_token()`.  
**Fix (opción completa):** Redis blacklist para O(1) lookup.  
**Bloqueante:** requiere Redis en producción (ya configurado en Railway según `.env.production.example`).

---

## Hallazgos medios

### SEC-006 — Rate limiter en memoria (no persiste entre restarts)
**Severidad:** MEDIO → 💤 Backlog  
**Archivo:** `backend/app/core/rate_limiting.py:16`

Slowapi usa almacenamiento en memoria. Cada deploy de Railway reinicia el proceso y resetea los contadores.

**Fix:** configurar slowapi con backend Redis:
```python
from slowapi.util import get_remote_address
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
```
**Bloqueante:** requiere que `REDIS_URL` esté disponible en todos los entornos.

---

### SEC-007 — Endpoints de recursos sin rate limit explícito
**Severidad:** MEDIO → 💤 Backlog  
**Afecta:** proyectos, cotizaciones, servicios, plantillas, equipos

Solo endpoints de auth y AI tienen `@limiter.limit()`. El resto depende únicamente del límite global de Nginx/Railway.

**Fix:** agregar decoradores a endpoints de escritura críticos:
```python
@limiter.limit("30/minute")  # creación de proyectos
@limiter.limit("10/minute")  # envío de emails/cotizaciones
```

---

### SEC-008 — Variables de usuario sin escapar HTML en templates de email
**Severidad:** MEDIO → ⏳ Pendiente  
**Archivo:** `backend/app/core/email.py:240-241`

`full_name` y `organization.name` se interpolan directamente en HTML de emails sin escapar. Un valor como `<script>alert(1)</script>` en el nombre podría ejecutarse en clientes de correo permisivos.

**Fix:** escapar con `html.escape()` antes de interpolar:
```python
import html
safe_name = html.escape(user.full_name or "")
safe_org = html.escape(organization.name or "")
```
**Alcance:** `email.py` y todas las plantillas inline en `proposal_portal.py`, `proposals.py`, `projects.py`.

---

### SEC-009 — URLs de perfil sin validación de formato
**Severidad:** MEDIO → 💤 Backlog  
**Archivo:** `backend/app/api/v1/endpoints/auth.py:509-515`  
**Campos:** `linkedin_url`, `portfolio_url`, `instagram_url`, `behance_url`

Se aceptan con `.strip()` pero sin validar que sean URLs válidas. Si el frontend las renderiza sin sanitizar, hay riesgo de XSS via `javascript:` URLs.

**Fix:** validador Pydantic en el schema:
```python
from pydantic import AnyHttpUrl
linkedin_url: AnyHttpUrl | None = None
```

---

### SEC-010 — Portal de propuestas comparte `SECRET_KEY` con JWT de usuarios
**Severidad:** MEDIO → 💤 Backlog  
**Archivo:** `backend/app/api/v1/endpoints/proposal_portal.py:86`

Los tokens del portal de clientes usan la misma `SECRET_KEY` que los JWT de usuarios internos. Un atacante que comprometa la clave puede forjar sesiones de portal.

**Mitigación existente:** los tokens de portal tienen `purpose: "proposal_client_portal"` verificado explícitamente.  
**Fix completo:** usar una clave separada `PROPOSAL_PORTAL_SECRET_KEY` para estos tokens, o JWT con firma asimétrica (RS256).  
**Prioridad real:** baja si SEC-002 está resuelto (clave fuerte en prod).

---

### SEC-011 — AI endpoint filtra detalle de excepción al cliente
**Severidad:** MEDIO → ⏳ Pendiente  
**Archivo:** `backend/app/api/v1/endpoints/ai.py:134-139`

```python
except Exception as e:
    import traceback
    traceback.print_exc()          # stdout visible en logs de Railway
    ...
    raise HTTPException(detail=f"Error during analysis: {str(e)}")  # fuga al cliente
```

**Fix:**
```python
except Exception:
    logger.exception("AI analysis failed", ...)
    raise HTTPException(status_code=500, detail="Error al procesar la solicitud")
```

---

## Hallazgos bajos / informativos

### SEC-012 — `openai` library desactualizada
**Severidad:** BAJO → 💤 Backlog  
**Archivo:** `backend/requirements.txt`

`openai==1.3.5` (Nov 2023). Versión actual: `1.x`. Actualizar para recibir parches de seguridad.

```
openai>=1.12.0
```

---

### SEC-013 — `slowapi` sin mantenimiento activo
**Severidad:** BAJO → 💤 Backlog  
**Archivo:** `backend/requirements.txt`

Último release de `slowapi`: 2023. Evaluar alternativas como `fastapi-limiter` (Redis-native) cuando se implemente SEC-006.

---

### SEC-014 — Token backward compatibility acepta `organization_id` ausente
**Severidad:** INFO → ❌ Descartado por diseño  
**Archivo:** `backend/app/core/security.py:173-175`

El decoder acepta tokens sin `organization_id` para soportar usuarios de soporte (super_admin, support_manager). Es comportamiento intencional, no una vulnerabilidad.

---

## Resumen ejecutivo

| ID | Descripción | Severidad | Estado |
|----|-------------|-----------|--------|
| SEC-001 | `.env` en repositorio | CRÍTICO | ❌ Falso positivo |
| SEC-002 | `SECRET_KEY` débil en prod | CRÍTICO | ⏳ Pendiente |
| SEC-003 | Raw SQL con rol por defecto | ALTO | ⏳ Pendiente |
| SEC-004 | Stripe webhook org_id sin validar | ALTO | ⏳ Pendiente |
| SEC-005 | Sin revocación de refresh tokens | ALTO | 💤 Backlog |
| SEC-006 | Rate limiter in-memory | MEDIO | 💤 Backlog |
| SEC-007 | Endpoints sin rate limit | MEDIO | 💤 Backlog |
| SEC-008 | HTML sin escapar en emails | MEDIO | ⏳ Pendiente |
| SEC-009 | URLs de perfil sin validar | MEDIO | 💤 Backlog |
| SEC-010 | Portal comparte SECRET_KEY | MEDIO | 💤 Backlog |
| SEC-011 | AI endpoint fuga de excepciones | MEDIO | ⏳ Pendiente |
| SEC-012 | `openai` desactualizada | BAJO | 💤 Backlog |
| SEC-013 | `slowapi` sin mantenimiento | BAJO | 💤 Backlog |
| SEC-014 | Token backward compat. | INFO | ❌ Descartado |

### Por estado
- ✅ Resuelto: 0
- ⏳ Pendiente (prioridad sprint actual): SEC-002, SEC-003, SEC-004, SEC-008, SEC-011
- 💤 Backlog: SEC-005, SEC-006, SEC-007, SEC-009, SEC-010, SEC-012, SEC-013
- ❌ Descartado: SEC-001, SEC-014
