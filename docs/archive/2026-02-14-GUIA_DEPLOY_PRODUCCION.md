# Guía de Deployment a Producción

## Fecha: 2026-02-14

## Prerrequisitos

1. ✅ Código completo y probado
2. ✅ Migraciones de base de datos listas
3. ✅ Variables de entorno identificadas
4. ✅ Infraestructura preparada

---

## Paso 1: Preparar Variables de Entorno

### 1.1 Generar SECRET_KEY

```bash
cd backend
python scripts/generate_secret_key.py
```

**Guarda la clave generada de forma segura.**

### 1.2 Configurar Variables de Entorno

#### Backend
```bash
cd backend
cp .env.production.example .env.production
# Editar .env.production con valores reales
```

#### Frontend
```bash
cd frontend
cp .env.production.example .env.production
# Editar .env.production con valores reales
```

**Variables Críticas a Configurar:**
- `DATABASE_URL`: URL de conexión a PostgreSQL de producción
- `SECRET_KEY`: Clave generada en paso 1.1
- `CORS_ORIGINS`: Dominios exactos de producción (separados por comas)
- `FRONTEND_URL`: URL del frontend en producción
- `ENVIRONMENT=production`

---

## Paso 2: Preparar Base de Datos

### 2.1 Crear Base de Datos

```sql
CREATE DATABASE nougram_db;
CREATE USER nougram_user WITH PASSWORD 'password-seguro';
GRANT ALL PRIVILEGES ON DATABASE nougram_db TO nougram_user;
```

### 2.2 Ejecutar Migraciones

```bash
cd backend
# Configurar DATABASE_URL en .env.production primero
python -m alembic upgrade head
```

### 2.3 Verificar Migraciones

```bash
python -m alembic current
python -m alembic history
```

---

## Paso 3: Opción A - Deploy con Docker

### 3.1 Preparar Docker Compose

```bash
# En la raíz del proyecto
cp docker-compose.prod.yml docker-compose.yml
# Editar docker-compose.yml con variables de entorno
```

### 3.2 Build y Deploy

```bash
# Build de imágenes
docker-compose build

# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f backend
```

### 3.3 Verificar Servicios

```bash
# Health check
curl http://localhost:8000/health

# Verificar contenedores
docker-compose ps
```

---

## Paso 4: Opción B - Deploy Manual

### 4.1 Backend

#### Instalar Dependencias
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

#### Configurar Gunicorn
```bash
# Usar gunicorn_config.py incluido
gunicorn main:app -c gunicorn_config.py
```

#### Con systemd (Linux)
```ini
# /etc/systemd/system/nougram-backend.service
[Unit]
Description=Nougram Backend API
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/nougram/backend
Environment="PATH=/opt/nougram/backend/venv/bin"
ExecStart=/opt/nougram/backend/venv/bin/gunicorn main:app -c gunicorn_config.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable nougram-backend
sudo systemctl start nougram-backend
sudo systemctl status nougram-backend
```

### 4.2 Frontend

#### Build de Producción
```bash
cd frontend
npm install
npm run build
```

#### Deploy
```bash
# Opción 1: Next.js standalone
npm start

# Opción 2: Servidor estático
# Exportar como estático (requiere configuración en next.config.js)
npm run export
# Servir con nginx o similar
```

---

## Paso 5: Configurar Nginx (Reverse Proxy)

### 5.1 Configuración Nginx

```nginx
# /etc/nginx/sites-available/nougram
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.nougram.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.nougram.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }
}
```

### 5.2 Habilitar Sitio

```bash
sudo ln -s /etc/nginx/sites-available/nougram /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Paso 6: Configurar SSL/TLS

### 6.1 Con Let's Encrypt (Certbot)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d api.nougram.com
```

### 6.2 Renovación Automática

```bash
sudo certbot renew --dry-run
```

---

## Paso 7: Verificación Post-Deploy

### 7.1 Health Checks

```bash
# Backend
curl https://api.nougram.com/health

# Frontend
curl https://app.nougram.com
```

### 7.2 Endpoints Críticos

```bash
# Login
curl -X POST https://api.nougram.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# Dashboard KPIs
curl https://api.nougram.com/api/v1/dashboard/kpis?period=month \
  -H "Authorization: Bearer <token>"
```

### 7.3 Verificar Logs

```bash
# Docker
docker-compose logs -f backend

# Systemd
sudo journalctl -u nougram-backend -f

# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## Paso 8: Monitoreo y Mantenimiento

### 8.1 Configurar Monitoreo

- **Uptime**: UptimeRobot, Pingdom
- **Logs**: CloudWatch, Loggly, Papertrail
- **APM**: Sentry, Datadog, New Relic
- **Metrics**: Prometheus + Grafana

### 8.2 Backups

#### Base de Datos
```bash
# Backup diario
pg_dump -h localhost -U nougram_user nougram_db > backup_$(date +%Y%m%d).sql

# Restaurar
psql -h localhost -U nougram_user nougram_db < backup_20260214.sql
```

#### Automatizar Backups
```bash
# Crontab
0 2 * * * /usr/local/bin/backup_db.sh
```

### 8.3 Actualizaciones

```bash
# Pull cambios
git pull origin main

# Rebuild (Docker)
docker-compose build
docker-compose up -d

# Migraciones
cd backend
python -m alembic upgrade head
```

---

## Troubleshooting

### Error: Database Connection Refused
- Verificar `DATABASE_URL` en `.env.production`
- Verificar que PostgreSQL esté corriendo
- Verificar firewall/security groups

### Error: CORS
- Verificar `CORS_ORIGINS` incluye el dominio exacto del frontend
- Verificar que no haya trailing slashes
- Verificar headers en navegador (Network tab)

### Error: SECRET_KEY
- Verificar que `SECRET_KEY` esté configurada
- Verificar que no sea la misma de desarrollo
- Regenerar si es necesario

### Error: 502 Bad Gateway
- Verificar que backend esté corriendo
- Verificar configuración de Nginx
- Verificar logs de backend

---

## Checklist Final

- [ ] Variables de entorno configuradas
- [ ] Base de datos creada y migraciones aplicadas
- [ ] Backend corriendo y respondiendo
- [ ] Frontend build y deployado
- [ ] Nginx configurado y funcionando
- [ ] SSL/TLS configurado
- [ ] Health checks pasando
- [ ] Logs configurados y accesibles
- [ ] Backups configurados
- [ ] Monitoreo configurado
- [ ] Documentación actualizada

---

## Contacto y Soporte

Para problemas o preguntas sobre el deployment, consultar:
- Documentación: `docs/2026-02-14-ESTADO_PRODUCCION.md`
- Logs del sistema
- Equipo de desarrollo
