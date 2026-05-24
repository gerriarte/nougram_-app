# Guía de Despliegue en VPS

Guía para desplegar Nougram en un VPS usando Docker Compose.

## Requisitos

- VPS con Ubuntu 22.04 LTS (o similar)
- Docker 24+ y Docker Compose v2
- Dominio apuntando al IP del VPS
- Certificado SSL (Let's Encrypt recomendado)

## 1. Preparar el servidor

```bash
# Instalar Docker (Ubuntu)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar para aplicar el grupo

# Verificar
docker --version
docker compose version
```

## 2. Clonar y configurar variables

```bash
git clone <repo-url> nougram
cd nougram

# Copiar plantilla
cp .env.production.example .env.production
nano .env.production  # o vim, etc.
```

### Variables obligatorias

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | `mi-password-seguro` |
| `DATABASE_URL` | URL de conexión (host=postgres) | `postgresql+asyncpg://postgres:PASS@postgres:5432/nougram_db` |
| `SECRET_KEY` | Clave JWT (≥32 chars) | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `CORS_ORIGINS` | Orígenes permitidos | `https://app.tudominio.com` |
| `FRONTEND_URL` | URL del frontend | `https://app.tudominio.com` |
| `NEXT_PUBLIC_API_URL` | URL API (mismo dominio) | `https://app.tudominio.com/api/v1` |

### Validar variables

```bash
# Linux/Mac
chmod +x scripts/check-env.sh
./scripts/check-env.sh .env.production

# Windows o alternativa
python scripts/check-env.py .env.production
```

## 3. Configurar SSL (HTTPS)

### Opción A: Let's Encrypt con script incluido

```bash
# Instalar certbot
sudo apt install certbot

# Obtener certificados (puerto 80 debe estar libre)
SSL_DOMAIN=app.tudominio.com SSL_EMAIL=tu@email.com ./scripts/setup-letsencrypt.sh

# Añadir a .env.production
echo "SSL_DOMAIN=app.tudominio.com" >> .env.production

# Levantar con HTTPS
docker compose -f docker-compose.prod.yml -f docker-compose.prod.ssl.yml --env-file .env.production up -d
```

El script genera certificados en `./certbot/` y el override `docker-compose.prod.ssl.yml` monta nginx con TLS (puertos 80→301 a HTTPS, 443).

### Opción B: Nginx en el host + Certbot

1. Instalar certbot: `sudo apt install certbot`
2. Obtener certificado: `sudo certbot certonly --standalone -d app.tudominio.com`
3. Configurar nginx en el host para proxy a `localhost:80` del compose

## 4. Levantar el stack

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

### Verificar servicios

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend  # ver logs
```

El backend ejecuta `alembic upgrade head` antes de arrancar Gunicorn. Las migraciones se aplican automáticamente.

### Primera ejecución: creación de la base de datos

1. **PostgreSQL** crea la BD `nougram_db` al iniciar (variable `POSTGRES_DB`).
2. **Backend** ejecuta `alembic upgrade head` al arrancar, creando tablas y datos iniciales (plantillas, etc.).
3. No hace falta ningún paso manual adicional.

## 5. Probar la aplicación

1. Abrir `https://app.tudominio.com` (o `http://IP:80` si no hay TLS)
2. Debe redirigir a login
3. Registrar organización y usuario
4. Completar onboarding
5. Verificar dashboard y admin (nómina, gastos)

## 6. Comandos útiles

```bash
# Ver logs
docker compose -f docker-compose.prod.yml logs -f

# Reiniciar un servicio
docker compose -f docker-compose.prod.yml restart backend

# Parar todo
docker compose -f docker-compose.prod.yml down

# Parar y eliminar volúmenes (¡CUIDADO! borra datos)
docker compose -f docker-compose.prod.yml down -v
```

## 7. Actualizar la aplicación

```bash
git pull
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

Las migraciones se ejecutan en cada arranque del backend.

## 8. Backups

```bash
# Backup manual (Linux/Mac)
./scripts/backup-postgres.sh

# Backup manual (Windows)
.\scripts\backup-postgres.ps1

# Automatizar con cron (diario a las 2:00)
# 0 2 * * * /ruta/nougram/scripts/backup-postgres.sh /ruta/backups
```

Los backups se guardan en `./backups/` por defecto. Configura retención (ej. borrar >30 días) o envía a S3/restic.

## 9. Monitoreo

- **`/health`**: Comprueba que la app responde.
- **`/health/ready`**: Verifica conexión a BD (ideal para Kubernetes o UptimeRobot).

### UptimeRobot (gratuito)

1. Crear monitor HTTP(s) apuntando a `https://app.tudominio.com/health/ready`
2. Intervalo: 5 minutos
3. Alertar si responde 503 o timeout

## 10. Probar localmente antes de desplegar

```bash
# Configurar .env.production con localhost (CORS_ORIGINS, FRONTEND_URL, NEXT_PUBLIC_API_URL)
# Levantar stack
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# Ejecutar chequeos
./scripts/test-prod-local.sh http://localhost
# o en Windows: .\scripts\test-prod-local.ps1 http://localhost
```

## 11. Notas importantes

- **Backend**: En producción no se usa `create_all`; solo Alembic. Las migraciones se aplican al iniciar el contenedor.
- **Docs de API**: `/docs` y `/redoc` están deshabilitados en producción.
- **Google OAuth/Sheets**: Opcionales; pueden dejarse vacíos si no se usan.

## 12. Solución de problemas

| Problema | Solución |
|----------|----------|
| Backend no arranca | Revisar logs: `docker compose -f docker-compose.prod.yml logs backend` |
| Error de conexión a BD | Verificar `DATABASE_URL` y que el servicio `postgres` esté healthy |
| CORS | Asegurar que `CORS_ORIGINS` incluya la URL exacta del frontend |
| 502 Bad Gateway | Backend o frontend no están listos; esperar healthchecks |
