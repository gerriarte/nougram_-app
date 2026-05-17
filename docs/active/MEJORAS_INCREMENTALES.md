# Mejoras incrementales — Nougram

Registrado: 2026-05-17  
Estado: backlog abierto — sin orden de prioridad asignado aún

---

## Eje 1 — Observabilidad operacional

### OBS-001 — Webhooks de eventos de email (Resend)
Resend expone webhooks para `email.delivered`, `email.bounced`, `email.opened`, `email.complained`.
Conectarlos daría visibilidad real sobre si los correos llegan, rebotan o van a spam.

**Impacto:** alto — hoy un email fallido es invisible después del log de envío  
**Esfuerzo estimado:** bajo (1-2 días)  
**Referencias:** Resend docs → Webhooks; crear endpoint `POST /webhooks/resend`

---

### OBS-002 — Health checks más ricos
El endpoint `/health/ready` verifica DB pero no Redis ni Resend. Un worker puede estar "healthy" y aun así no enviar emails ni procesar tareas Celery.

**Fix:** agregar checks para:
- Redis: ping con timeout
- Resend: validar que `RESEND_API_KEY` y `RESEND_FROM_EMAIL` estén configurados (sin hacer llamada HTTP en cada health check)
- Celery workers: verificar que al menos un worker esté consumiendo la cola

**Esfuerzo estimado:** bajo (medio día)

---

### OBS-003 — Alertas en Railway
No hay alertas configuradas para crash loops ni errores 5xx sostenidos.

**Acciones:**
- Configurar webhook de Railway hacia un canal de Slack/Discord para eventos de crash
- Definir umbrales de error rate aceptables por entorno (prod vs staging)

**Esfuerzo estimado:** muy bajo (configuración, sin código)

---

## Eje 2 — Resiliencia del sistema de emails

### EMAIL-001 — Reintentos automáticos vía Celery
Con BackgroundTasks, si el proceso muere durante el envío el email se pierde silenciosamente. Celery (ya configurado en el proyecto) daría reintentos automáticos y visibilidad de la cola.

**Ruta de migración:**
1. Crear tasks Celery en `backend/app/tasks/email_tasks.py`
2. Reemplazar `background_tasks.add_task(send_email, ...)` por `send_email_task.delay(...)`
3. Mantener BackgroundTasks como fallback si Celery no está disponible

**Esfuerzo estimado:** medio (2-3 días + infra Redis en prod)  
**Bloqueante:** requiere Redis configurado y worker Celery deployado en Railway

---

### EMAIL-002 — Audit trail de envíos en DB
Tabla `email_log` con registro de cada intento: destinatario, evento, estado, timestamp, contexto de negocio.

**Esquema mínimo:**
```
id, to_email, subject, email_event, status (queued/sent/failed),
provider_message_id, org_id, created_at
```

**Valor:** permite reenviar manualmente, auditar deliverability, correlacionar con acciones de negocio  
**Esfuerzo estimado:** medio (1-2 días)

---

## Eje 3 — Cobertura de tests

### TEST-001 — Tests de `project_service.py`
Cobertura actual: ~10%. Es el corazón del cálculo de cotizaciones y el servicio más crítico del sistema.

**Áreas prioritarias:**
- Cálculo de precio con impuestos y márgenes
- Lógica de cotizaciones recurrentes
- Generación de PDF/DOCX (smoke tests)

---

### TEST-002 — Tests de integración para billing y Stripe
Los endpoints de billing y el handler de Stripe webhooks tienen cobertura casi nula.

**Prioridad:** verificar que el flujo de activación/cancelación de plan funcione correctamente end-to-end con Stripe mocked.

---

### TEST-003 — Convención: un test de integración por feature nueva
No es un cambio de código sino una práctica de equipo: cada endpoint o flujo nuevo debe incluir al menos un test de integración happy path.

---

## Eje 4 — Madurez multi-tenant

### MT-001 — Audit log visible para administradores
`AuditService` ya escribe eventos en DB. Exponerlos en la UI sería un win rápido y de alto valor para admins de organización.

**Endpoints necesarios:** `GET /organizations/{id}/audit-log` con filtros por usuario, acción, fecha  
**Esfuerzo estimado:** bajo-medio (el dato ya existe)

---

### MT-002 — Limits por plan más granulares
`validate_user_limit()` controla usuarios, pero no hay enforcement de cotizaciones activas, proyectos, o uso de AI por plan.

**Referencia:** `backend/app/core/plan_limits.py`  
**Esfuerzo estimado:** medio (requiere definir límites por plan con producto)

---

### MT-003 — Exportación de datos (CSV/Excel)
Primer pedido habitual de clientes enterprise: "dame todo mi data". Proyectos, cotizaciones, gastos, equipo.

**Approach mínimo:** endpoints `GET /projects/export?format=csv` con generación en background y descarga por link firmado (S3/Contabo ya disponible)  
**Esfuerzo estimado:** medio por módulo

---

### MT-004 — Onboarding guiado — validar completitud del flujo UX
`onboarding_service.py` existe (63KB, bien desarrollado). Revisar qué tan completo está el flujo UX y si hay gaps entre lo que el backend soporta y lo que el frontend expone.

---

## Resumen

| ID | Descripción | Eje | Esfuerzo | Estado |
|----|-------------|-----|----------|--------|
| OBS-001 | Webhooks de Resend | Observabilidad | Bajo | ⏳ Backlog |
| OBS-002 | Health checks ricos | Observabilidad | Bajo | ⏳ Backlog |
| OBS-003 | Alertas en Railway | Observabilidad | Mínimo | ⏳ Backlog |
| EMAIL-001 | Reintentos Celery | Emails | Medio | ⏳ Backlog |
| EMAIL-002 | Audit trail de emails | Emails | Medio | ⏳ Backlog |
| TEST-001 | Tests project_service | Tests | Medio | ⏳ Backlog |
| TEST-002 | Tests billing/Stripe | Tests | Medio | ⏳ Backlog |
| TEST-003 | Convención test por feature | Tests | Mínimo | ⏳ Backlog |
| MT-001 | Audit log en UI | Multi-tenant | Bajo-medio | ⏳ Backlog |
| MT-002 | Limits por plan | Multi-tenant | Medio | ⏳ Backlog |
| MT-003 | Exportación CSV/Excel | Multi-tenant | Medio | ⏳ Backlog |
| MT-004 | Validar flujo onboarding | Multi-tenant | Bajo | ⏳ Backlog |
