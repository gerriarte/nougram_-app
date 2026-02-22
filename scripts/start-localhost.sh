#!/bin/bash

# Script para iniciar la aplicación completa en localhost
# Sin mocks ni hardcoding - Todo conectado al backend real

set -e

echo "=========================================="
echo "🚀 Iniciando Nougram en Localhost"
echo "=========================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar dependencias
echo "📋 Verificando dependencias..."
if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 no encontrado${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js no encontrado${NC}"
    exit 1
fi

if ! command_exists docker; then
    echo -e "${YELLOW}⚠️  Docker no encontrado - Se asume que PostgreSQL ya está corriendo${NC}"
else
    echo -e "${GREEN}✅ Docker encontrado${NC}"
fi

echo ""

# Verificar si PostgreSQL está corriendo
echo "🔍 Verificando PostgreSQL..."
if command_exists docker; then
    if docker ps | grep -q nougram-postgres; then
        echo -e "${GREEN}✅ PostgreSQL está corriendo en Docker${NC}"
    else
        echo -e "${YELLOW}⚠️  PostgreSQL no está corriendo${NC}"
        echo "Iniciando PostgreSQL..."
        docker-compose up -d postgres
        echo "Esperando a que PostgreSQL esté listo..."
        sleep 5
    fi
else
    echo -e "${YELLOW}⚠️  Verificando conexión a PostgreSQL manualmente...${NC}"
fi

echo ""

# Verificar variables de entorno del backend
echo "🔍 Verificando configuración del backend..."
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado en backend/${NC}"
    echo "Creando archivo .env desde ejemplo..."
    cd backend
    python3 setup_env.py || echo "Error al crear .env"
    cd ..
fi

# Verificar variables de entorno del frontend principal
echo "🔍 Verificando configuración del frontend..."
if [ ! -f "nougram_front/.env.local" ]; then
    echo -e "${YELLOW}⚠️  Archivo .env.local no encontrado en nougram_front/${NC}"
    echo "Creando archivo .env.local..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > nougram_front/.env.local
fi

echo ""

# Instalar dependencias del backend si es necesario
echo "📦 Verificando dependencias del backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

source venv/bin/activate 2>/dev/null || . venv/bin/activate 2>/dev/null || echo "Activando venv..."

if ! python -c "import fastapi" 2>/dev/null; then
    echo "Instalando dependencias del backend..."
    pip install -r requirements.txt
fi

# Ejecutar migraciones
echo ""
echo "🗄️  Ejecutando migraciones de base de datos..."
python -m alembic upgrade head || echo -e "${YELLOW}⚠️  Error en migraciones - continuando...${NC}"

cd ..

# Instalar dependencias del frontend principal si es necesario
echo ""
echo "📦 Verificando dependencias del frontend..."
cd nougram_front
if [ ! -d "node_modules" ]; then
    echo "Instalando dependencias del frontend..."
    npm install
fi
cd ..

echo ""
echo "=========================================="
echo "✅ Preparación completada"
echo "=========================================="
echo ""
echo "Para iniciar los servicios:"
echo ""
echo "  Terminal 1 - Backend:"
echo "    cd backend"
echo "    source venv/bin/activate"
echo "    python -m uvicorn main:app --reload --port 8000"
echo ""
echo "  Terminal 2 - Frontend:"
echo "    cd nougram_front"
echo "    npm run dev"
echo ""
echo "Luego abre: http://localhost:3000"
echo ""
echo "=========================================="
