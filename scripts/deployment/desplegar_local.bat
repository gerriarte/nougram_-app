@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  Despliegue Local - Nougram
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
    echo %YELLOW% Por favor, abre Docker Desktop y espera a que termine de iniciar.
    echo %YELLOW% Luego ejecuta este script nuevamente.
    pause
    exit /b 1
)
echo %GREEN% Docker Desktop esta corriendo
echo.

REM Verificar Python
echo %BLUE% Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED% Python no esta instalado o no esta en el PATH.
    echo %YELLOW% Por favor, instala Python 3.11 o superior.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %GREEN% Python encontrado: !PYTHON_VERSION!
echo.

REM Verificar Node.js
echo %BLUE% Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo %RED% Node.js no esta instalado o no esta en el PATH.
    echo %YELLOW% Por favor, instala Node.js 18 o superior.
    pause
    exit /b 1
)
for /f %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
echo %GREEN% Node.js encontrado: !NODE_VERSION!
echo.

REM Configurar entorno del backend
echo %BLUE% Configurando entorno del backend...
cd backend
if not exist .env (
    echo %YELLOW% Archivo .env no encontrado. Creando...
    python setup_env.py
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

REM Instalar dependencias del backend
echo %BLUE% Instalando dependencias del backend...
cd backend
if not exist venv (
    echo %YELLOW% Creando entorno virtual de Python...
    python -m venv venv
    if errorlevel 1 (
        echo %RED% Error al crear el entorno virtual
        cd ..
        pause
        exit /b 1
    )
    echo %GREEN% Entorno virtual creado
) else (
    echo %GREEN% Entorno virtual ya existe
)

echo %YELLOW% Activando entorno virtual e instalando dependencias...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo %RED% Error al activar el entorno virtual
    cd ..
    pause
    exit /b 1
)
pip install --upgrade pip >nul 2>&1
echo %YELLOW% Instalando paquetes de Python (esto puede tardar unos minutos)...
pip install -r requirements.txt
if errorlevel 1 (
    echo %RED% Error al instalar dependencias del backend
    call venv\Scripts\deactivate.bat
    cd ..
    pause
    exit /b 1
)
echo %GREEN% Dependencias del backend instaladas
call venv\Scripts\deactivate.bat
cd ..
echo.

REM Instalar dependencias del frontend principal
echo %BLUE% Instalando dependencias del frontend...
cd nougram_front
if not exist node_modules (
    echo %YELLOW% Instalando dependencias de Node.js (esto puede tardar unos minutos)...
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

REM Iniciar PostgreSQL con Docker
echo %BLUE% Iniciando PostgreSQL con Docker...
docker-compose up -d
if errorlevel 1 (
    echo %RED% Error al iniciar PostgreSQL
    pause
    exit /b 1
)

REM Esperar a que PostgreSQL esté listo
echo %YELLOW% Esperando a que PostgreSQL este listo...
timeout /t 5 /nobreak >nul
docker-compose ps
echo %GREEN% PostgreSQL iniciado correctamente
echo.

REM Ejecutar migraciones de base de datos
echo %BLUE% Ejecutando migraciones de base de datos...
cd backend
call venv\Scripts\activate.bat
alembic upgrade head
if errorlevel 1 (
    echo %YELLOW% Advertencia: Error al ejecutar migraciones. Esto puede ser normal si la base de datos ya esta actualizada.
)
deactivate
cd ..
echo.

REM Mostrar instrucciones finales
echo.
echo ========================================
echo  Configuracion completada exitosamente!
echo ========================================
echo.
echo %GREEN% Proximos pasos:
echo.
echo 1. Abre una nueva ventana PowerShell y ejecuta:
echo    cd backend
echo    venv\Scripts\activate
echo    python main.py
echo.
echo 2. Abre otra ventana PowerShell y ejecuta:
echo    cd nougram_front
echo    npm run dev
echo.
echo 3. Abre tu navegador en: http://localhost:3000
echo.
echo %YELLOW% O puedes usar los scripts individuales:
echo    - iniciar_docker.bat (ya ejecutado)
echo    - iniciar_backend.bat
echo    - iniciar_frontend.bat
echo.
echo %BLUE% Para detener PostgreSQL: docker-compose down
echo.
pause

