# Guía de Pruebas Realistas

Cómo probar Nougram de forma que simule uso real en producción.

---

## 1. Entorno de pruebas: Stack producción local

La forma más fiel de probar es usar el mismo stack que en producción:

```bash
# Crear .env para pruebas (ya configurado para localhost)
cp .env.test-local.example .env.test-local

# Levantar todo
docker compose -f docker-compose.prod.yml --env-file .env.test-local up -d --build

# Comprobar que responde
./scripts/test-prod-local.sh http://localhost
# Windows: .\scripts\test-prod-local.ps1 http://localhost
```

Abre **http://localhost** en el navegador (nginx hace proxy; el puerto 80 debe estar libre).

---

## 2. Flujos críticos a probar (checklist manual)

### 2.1 Registro y primer acceso

| # | Acción | Verificación |
|---|--------|--------------|
| 1 | Ir a `/` | Redirige a login o onboarding |
| 2 | Crear organización en `/register` o flujo de invitación | Nombre, slug, moneda |
| 3 | Registrar usuario (email, contraseña) | Sin errores |
| 4 | Login | Token guardado, redirección correcta |

### 2.2 Onboarding

| # | Acción | Verificación |
|---|--------|--------------|
| 5 | Completar onboarding (perfil, tipo agencia) | BCR calculado o en 0 |
| 6 | Añadir 1–2 miembros de equipo con salarios | Aparecen en resumen |
| 7 | Añadir gastos fijos (ej. Slack, oficina) | Total de costos actualizado |
| 8 | Configurar cargas sociales (salud, pensión) si aplica | Multiplicador aplicado |
| 9 | Finalizar onboarding | Redirige a dashboard |

### 2.3 Operación diaria

| # | Acción | Verificación |
|---|--------|--------------|
| 10 | Crear servicio (ej. “Diseño UI”, hora, $50) | Servicio listado |
| 11 | Crear proyecto con cliente | Proyecto visible |
| 12 | Crear cotización con 2–3 servicios | Montos calculados |
| 13 | Añadir gastos a la cotización | Rentabilidad actualizada |
| 14 | Editar cotización existente | Cambios guardados |
| 15 | Ver dashboard | KPIs, gráficos sin errores |

### 2.4 Configuración y admin

| # | Acción | Verificación |
|---|--------|--------------|
| 16 | Ir a Settings → Team | Lista de miembros, BCR |
| 17 | Ir a Settings → Costs | Gastos fijos |
| 18 | Cambiar moneda primaria | Se refleja en cálculos |
| 19 | Crear impuesto (ej. IVA 19%) | Aplica en cotizaciones |

### 2.5 Casos límite

| # | Acción | Verificación |
|---|--------|--------------|
| 20 | Cerrar sesión y volver a entrar | Sesión restaurada |
| 21 | Crear cotización sin servicios | Validación o mensaje claro |
| 22 | Montos grandes (millones) | Sin errores de precisión |
| 23 | Diferentes monedas (USD, COP) | Conversiones coherentes |

---

## 3. Datos de prueba realistas

Usa datos que se parezcan a producción:

**Organización**
- Nombre: "Agencia Digital Test"
- Moneda: USD o COP según tu región

**Equipo**
- Diseñador UI: $2,500/mes
- Desarrollador: $3,200/mes
- Project Manager: $2,800/mes

**Gastos fijos**
- Slack: $12/mes
- Figma: $15/mes
- Servidor: $50/mes

**Servicios**
- Diseño UI: $75/hora
- Desarrollo frontend: $90/hora
- Consultoría: $120/hora

**Proyecto**
- Cliente: "Empresa XYZ"
- Cotización: 20h diseño + 40h desarrollo + 10h PM

---

## 4. Pruebas de API (backend)

Para validar la lógica sin pasar por el frontend:

```bash
cd backend
# Tests unitarios e integración (BD en memoria)
pytest tests/ -v

# Probar contra BD real (postgres del compose)
# Primero: DATABASE_URL apuntando a localhost:5432 desde el host
pytest tests/integration/ -v --tb=short
```

---

## 5. Pruebas E2E automatizadas (opcional)

Si quieres automatizar los flujos críticos:

1. **Playwright** (recomendado): instalación con `npm init playwright@latest` en frontend.
2. **Script de smoke**: login → onboarding → crear proyecto → crear cotización.
3. Ejecutar contra `http://localhost` con el stack levantado.

Ejemplo de estructura:
```
frontend/
  e2e/
    auth.spec.ts      # Login, registro
    onboarding.spec.ts
    projects.spec.ts  # CRUD proyectos y cotizaciones
```

---

## 6. Pruebas de carga (avanzado)

Para simular varios usuarios concurrentes:

- **k6** o **Locust**: scripts contra `/api/v1/...`
- Endpoints a probar: login, listar proyectos, calcular BCR, crear cotización
- Empezar con 5–10 usuarios virtuales y subir progresivamente

---

## 7. VPS de pruebas (staging)

Si quieres una réplica de producción:

1. VPS económico (ej. DigitalOcean, Hetzner)
2. Dominio de prueba: `staging.tudominio.com`
3. Desplegar con `docker-compose.prod` + Let's Encrypt
4. Usar solo para pruebas; no datos reales de clientes

---

## 8. Resumen rápido

| Objetivo | Acción |
|----------|--------|
| Probar como usuario real | Stack Docker local + checklist manual |
| Validar lógica backend | `pytest tests/` |
| Automatizar flujos clave | Playwright en `frontend/e2e/` |
| Simular carga | k6/Locust contra API |
| Réplica de producción | VPS staging con mismo compose |
