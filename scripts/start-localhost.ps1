# Script PowerShell para iniciar la aplicación completa en localhost
# Sin mocks ni hardcoding - Todo conectado al backend real

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 Iniciando Nougram en Localhost" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar dependencias
Write-Host "📋 Verificando dependencias..." -ForegroundColor Yellow

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python no encontrado" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js no encontrado" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️  Docker no encontrado - Se asume que PostgreSQL ya está corriendo" -ForegroundColor Yellow
} else {
    Write-Host "✅ Docker encontrado" -ForegroundColor Green
}

Write-Host ""

# Verificar PostgreSQL
Write-Host "🔍 Verificando PostgreSQL..." -ForegroundColor Yellow
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $postgresRunning = docker ps | Select-String "nougram-postgres"
    if ($postgresRunning) {
        Write-Host "✅ PostgreSQL está corriendo en Docker" -ForegroundColor Green
    } else {
        Write-Host "⚠️  PostgreSQL no está corriendo" -ForegroundColor Yellow
        Write-Host "Iniciando PostgreSQL..."
        docker-compose up -d postgres
        Write-Host "Esperando a que PostgreSQL esté listo..."
        Start-Sleep -Seconds 5
    }
} else {
    Write-Host "⚠️  Verificando conexión a PostgreSQL manualmente..." -ForegroundColor Yellow
}

Write-Host ""

# Verificar .env del backend
Write-Host "🔍 Verificando configuración del backend..." -ForegroundColor Yellow
if (-not (Test-Path "backend\.env")) {
    Write-Host "⚠️  Archivo .env no encontrado en backend\" -ForegroundColor Yellow
    Write-Host "Creando archivo .env desde ejemplo..."
    Set-Location backend
    python setup_env.py
    Set-Location ..
}

# Verificar .env.local del frontend principal
Write-Host "🔍 Verificando configuración del frontend..." -ForegroundColor Yellow
if (-not (Test-Path "nougram_front\.env.local")) {
    Write-Host "⚠️  Archivo .env.local no encontrado en nougram_front\" -ForegroundColor Yellow
    Write-Host "Creando archivo .env.local..."
    "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" | Out-File -FilePath "nougram_front\.env.local" -Encoding utf8
}

Write-Host ""

# Instalar dependencias del backend
Write-Host "📦 Verificando dependencias del backend..." -ForegroundColor Yellow
Set-Location backend

if (-not (Test-Path "venv")) {
    Write-Host "Creando entorno virtual..."
    python -m venv venv
}

& "venv\Scripts\Activate.ps1"

# Verificar si fastapi está instalado
try {
    python -c "import fastapi" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Instalando dependencias del backend..."
        pip install -r requirements.txt
    }
} catch {
    Write-Host "Instalando dependencias del backend..."
    pip install -r requirements.txt
}

# Ejecutar migraciones
Write-Host ""
Write-Host "🗄️  Ejecutando migraciones de base de datos..." -ForegroundColor Yellow
python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Error en migraciones - continuando..." -ForegroundColor Yellow
}

Set-Location ..

# Instalar dependencias del frontend principal
Write-Host ""
Write-Host "📦 Verificando dependencias del frontend..." -ForegroundColor Yellow
Set-Location nougram_front

if (-not (Test-Path "node_modules")) {
    Write-Host "Instalando dependencias del frontend..."
    npm install
}

Set-Location ..

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Preparación completada" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para iniciar los servicios:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Terminal 1 - Backend:" -ForegroundColor White
Write-Host "    cd backend" -ForegroundColor Gray
Write-Host "    .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "    python -m uvicorn main:app --reload --port 8000" -ForegroundColor Gray
Write-Host ""
Write-Host "  Terminal 2 - Frontend:" -ForegroundColor White
Write-Host "    cd nougram_front" -ForegroundColor Gray
Write-Host "    npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "Luego abre: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
