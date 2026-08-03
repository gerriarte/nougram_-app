# Verificación post-deploy — v1.4.0 (moneda primaria y rigor de cálculo)

Correr esto **en staging primero**, y repetirlo en producción después del deploy.
Cada punto es un número que tiene que cerrar, no una impresión visual.

- **Staging:** `http://ej28mzf1397eiytyngmlmdnp.13.140.179.23.sslip.io` (backend, rama `develop`)
- **Producción:** `https://api.nougram.co` / `https://app.nougram.co` (rama `main`)

---

## 0. Que el deploy realmente haya entrado

El auto-deploy de Coolify **no dispara solo** (pasó igual con el PR #3). Un *Restart*
no sirve: reusa la imagen vieja. Hay que apretar **Deploy**.

```bash
# El backend tiene que estar arriba y con las rutas nuevas
curl -s https://api.nougram.co/health

# Confirmar que corrió alembic: la revisión actual tiene que ser v20260727c_bf_currency
# (en el contenedor del backend)
alembic current
```

---

## 1. El impuesto ya no grava la contingencia

Es el bug que le mostraba al cliente un número distinto del que ve la agencia.

1. Crear una cotización con **contingencia** (10%) y un **impuesto** (IVA 19%).
2. Anotar el **Total** que muestra la pantalla.
3. Enviar la propuesta por mail con PDF y DOCX adjuntos.

**Tienen que coincidir los cuatro:** pantalla, cuerpo del mail, PDF y DOCX.

Con 1.000.000 de base, 10% de contingencia e IVA 19%:

| | Valor |
|---|---|
| Base gravable | 1.000.000 |
| IVA 19% sobre la base | 190.000 |
| Precio con contingencia | 1.100.000 |
| **Total correcto** | **1.290.000** |
| Total del bug (gravaba la contingencia) | 1.309.000 |

Si aparece 1.309.000 en algún lado, el deploy no entró en ese servicio.

---

## 2. Blended Cost Rate y moneda primaria

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  https://api.nougram.co/api/v1/settings/calculations/agency-cost-hour
```

Verificar en la respuesta:

- `primary_currency` — la moneda real de la agencia, **no `USD` por defecto**.
- `active_team_members` — distinto de 0.
- `blended_cost_rate` — distinto de 0 y del orden de magnitud esperado.

Para la cuenta demo (Aurora Digital, `demo@nougram.co`, org 38): `COP`, 23 miembros,
BCR ≈ 97.756.

---

## 3. El backfill de moneda primaria (lo único que toca datos)

La migración rellena `primary_currency` donde falta, derivando de: `currency` →
`template_applied_currency` → país → la moneda de las filas de `team_members` y
`costs_fixed` si todas coinciden. **Las orgs con monedas mezcladas se dejan intactas
a propósito** — ahí no hay respuesta deducible.

Esas son las que hay que resolver a mano:

```sql
-- Orgs que quedaron SIN moneda primaria: siguen cotizando en USD
SELECT id, name, settings->>'primary_currency' AS primary_currency
FROM organizations
WHERE settings->>'primary_currency' IS NULL
ORDER BY id;

-- Para cada una, ver en qué moneda tiene cargada la plata realmente
SELECT organization_id, currency, count(*)
FROM team_members
WHERE organization_id IN (<ids del query anterior>)
GROUP BY organization_id, currency;
```

Para cada org de esa lista: mirar sus datos, decidir la moneda con criterio y
setearla desde la app (Configuración → moneda) o por API. **No inventar un default.**

> En local quedaban así las orgs 1, 3, 4 y 9 — y la org 1 (A:BRA Latam) tiene
> cotizaciones reales con datos en COP. En producción la lista puede ser otra.

---

## 4. Sanity de lo que no se tocó

- Dashboard: KPIs del período con números plausibles (la corrección de UTC puede
  mover levemente los totales de un período respecto de lo que se veía antes — es
  el fix, no un bug).
- `/insights/break-even`: para la demo, cobertura ~110% (en profit).
- Abrir una cotización vieja y **re-guardarla**: tiene que dejarse guardar sin exigir
  descripción en los ítems viejos (la exigencia aplica sólo a ítems nuevos).
- Que ninguna pantalla quede girando: si el backend tarda, ahora corta a los 30s con
  mensaje en vez de colgarse para siempre.

---

## Si algo falla

El rollback de código es redeploy del commit anterior en Coolify. **El backfill de
datos no se revierte** (`downgrade()` es un no-op deliberado: borrar
`primary_currency` devolvería a las orgs al bug). Si una org quedó con la moneda
equivocada, se corrige seteándola a mano, no revirtiendo la migración.
