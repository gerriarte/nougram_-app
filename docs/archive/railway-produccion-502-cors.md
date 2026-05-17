# Producción: 502 y CORS en qaback.nougram.co

## Qué está pasando

- **Frontend (early.nougram.co)** hace peticiones a **Backend (qaback.nougram.co)**.
- El backend **no responde**: Railway devuelve **502 Bad Gateway** ("Application failed to respond").
- La preflight (OPTIONS) recibe ese 502 **sin headers CORS** → el navegador muestra error de CORS y bloquea login.

**Conclusión:** No es un fallo de configuración CORS en código; es que la app del backend no está respondiendo en producción.

---

## Qué revisar en Railway

### 1. Servicio backend (comfortable-courtesy) en entorno **Production**

- **Deployments:** ¿El último deploy está en verde (Success)? Si está Failed o Canceled, el backend no está corriendo.
- **Logs:** Abrir la pestaña Logs del servicio. Buscar:
  - Errores al arrancar (excepciones, `alembic upgrade head` fallido, `ModuleNotFoundError`, etc.).
  - Si no hay logs recientes, el contenedor puede no estar arrancando.
- **Variables:** En Variables, confirmar que existen y son correctas:
  - `CORS_ORIGINS` = `https://early.nougram.co`
  - `DATABASE_URL` (y que la BD esté accesible desde production).

### 2. Dominio qaback.nougram.co

- En el **mismo** servicio backend → **Settings** → **Networking / Domains**.
- Verificar que **qaback.nougram.co** está asignado a este servicio y al entorno **Production**.
- Si el dominio está en otro servicio o en Staging, las peticiones no llegarán al backend correcto.

### 3. Redeploy

- Si el último deploy es antiguo o falló: **Redeploy** del último deployment o **Deploy** desde la rama correcta (p. ej. `main`).
- Esperar a que el deploy termine y el servicio pase a "Active" / "Running".

### 4. Comprobar que responde

En terminal (o Postman):

```bash
curl -s https://qaback.nougram.co/health
```

- **Correcto:** `{"status":"healthy"}` y HTTP 200.
- **Problema:** 502 o JSON con `"message":"Application failed to respond"` → el backend sigue sin responder; revisar de nuevo Logs y Deployments.

---

## Cuando el backend responda 200

Las peticiones OPTIONS y GET/POST llegarán a tu app FastAPI. Ahí sí se aplicará:

- `CORS_ORIGINS` con `https://early.nougram.co`
- Middleware CORS y el fallback que añadimos

Si el backend responde 200 al `/health`, el login desde early.nougram.co debería funcionar (prueba en ventana de incógnito para evitar caché).

---

## Resumen

| Síntoma en el navegador | Causa real | Acción |
|-------------------------|------------|--------|
| CORS: "No 'Access-Control-Allow-Origin' header" en preflight | Backend devuelve 502 (no responde) | Arreglar en Railway: logs, deploy, dominio y comprobar `/health` hasta ver 200. |
