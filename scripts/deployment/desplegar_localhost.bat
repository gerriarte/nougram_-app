@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  Despliegue en Localhost - Nougram
echo ========================================
echo.

REM Colores para mensajes
set "GREEN=[OK]"
set "YELLOW=[INFO]"
set "RED=[ERROR]"
set "BLUE=[STEP]"

REM Verificar Docker
echo %BLUE% Verificando Docker Desktop...
docker ps >nul 2>&1
if errorlevel 1 (
    echo %RED% Docker Desktop no esta corriendo.
    echo.
    echo %YELLOW% INSTRUCCIONES:
    echo 1. Abre Docker Desktop desde el menu de inicio
    echo 2. Espera a que Docker Desktop termine de iniciar completamente
    echo 3. Ejecuta este script nuevamente
    echo.
    echo %YELLOW% O ejecuta manualmente:
    echo    docker-compose up -d
    echo    iniciar_backend.bat
    echo    iniciar_frontend.bat
    echo.
    pause
    exit /b 1
)
echo %GREEN% Docker Desktop esta corriendo
echo.

REM Verificar si PostgreSQL esta corriendo
echo %BLUE% Verificando PostgreSQL...
docker-compose ps | findstr "postgres" >nul 2>&1
if errorlevel 1 (
    echo %YELLOW% PostgreSQL no esta corriendo. Iniciando...
    docker-compose up -d
    if errorlevel 1 (
        echo %RED% Error al iniciar PostgreSQL
        pause
        exit /b 1
    )
    echo %YELLOW% Esperando a que PostgreSQL este listo...
    timeout /t 5 /nobreak >nul
    echo %GREEN% PostgreSQL iniciado correctamente
) else (
    echo %GREEN% PostgreSQL ya esta corriendo
)
echo.

REM Verificar archivo .env del backend
echo %BLUE% Verificando configuracion del backend...
cd backend
if not exist .env (
    echo %YELLOW% Archivo .env no encontrado. Creando...
    if exist venv (
        call venv\Scripts\activate.bat
        python setup_env.py
        call venv\Scripts\deactivate.bat
    ) else (
        python setup_env.py
    )
    if errorlevel 1 (
        echo %RED% Error al crear el archivo .env
        cd ..
        pause
        exit /b 1
    )
    echo %GREEN% Archivo .env creado exitosamente
) else (
    echo %GREEN% Archivo .env ya existe
)
cd ..
echo.

REM Verificar entorno virtual del backend
echo %BLUE% Verificando entorno virtual del backend...
cd backend
if not exist venv (
    echo %YELLOW% Entorno virtual no encontrado. Creando...
    python -m venv venv
    if errorlevel 1 (
        echo %RED% Error al crear el entorno virtual
        cd ..
        pause
        exit /b 1
    )
    echo %GREEN% Entorno virtual creado
    echo %YELLOW% Instalando dependencias del backend...
    call venv\Scripts\activate.bat
    pip install --upgrade pip >nul 2>&1
    pip install -r requirements.txt
    if errorlevel 1 (
        echo %RED% Error al instalar dependencias del backend
        call venv\Scripts\deactivate.bat
        cd ..
        pause
        exit /b 1
    )
    call venv\Scripts\deactivate.bat
    echo %GREEN% Dependencias del backend instaladas
) else (
    echo %GREEN% Entorno virtual ya existe
)
cd ..
echo.

REM Verificar dependencias del frontend principal
echo %BLUE% Verificando dependencias del frontend...
cd nougram_front
if not exist node_modules (
    echo %YELLOW% Instalando dependencias del frontend...
    call npm install
    if errorlevel 1 (
        echo %RED% Error al instalar dependencias del frontend
        cd ..
        pause
        exit /b 1
    )
    echo %GREEN% Dependencias del frontend instaladas
) else (
    echo %GREEN% Dependencias del frontend ya instaladas
)
cd ..
echo.

REM Ejecutar migraciones de base de datos
echo %BLUE% Ejecutando migraciones de base de datos...
cd backend
if exist venv (
    call venv\Scripts\activate.bat
    alembic upgrade head
    if errorlevel 1 (
        echo %YELLOW% Advertencia: Error al ejecutar migraciones. Esto puede ser normal si la base de datos ya esta actualizada.
    )
    call venv\Scripts\deactivate.bat
) else (
    echo %RED% Entorno virtual no encontrado. Ejecuta primero desplegar_local.bat
    cd ..
    pause
    exit /b 1
)
cd ..
echo.

REM Iniciar servicios
echo.
echo ========================================
echo  Iniciando servicios...
echo ========================================
echo.

REM Iniciar Backend en nueva ventana
echo %BLUE% Iniciando Backend en nueva ventana...
start "Nougram Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python main.py"

REM Esperar un poco antes de iniciar el frontend
timeout /t 3 /nobreak >nul

REM Iniciar Frontend en nueva ventana
echo %BLUE% Iniciando Frontend en nueva ventana...
start "Nougram Frontend" cmd /k "cd /d %~dp0..\..\nougram_front && npm run dev"

echo.
echo ========================================
echo  Despliegue completado!
echo ========================================
echo.
echo %GREEN% Servicios iniciados en ventanas separadas:
echo.
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000
echo.
echo %YELLOW% Para detener los servicios:
echo    - Cierra las ventanas de Backend y Frontend
echo    - Para detener PostgreSQL: docker-compose down
echo.
echo %BLUE% Presiona cualquier tecla para cerrar esta ventana...
pause >nul

