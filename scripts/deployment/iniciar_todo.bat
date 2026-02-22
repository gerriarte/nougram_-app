@echo off
echo ========================================
echo  Iniciando Nougram (Backend + Frontend)
echo ========================================
echo.

REM Verificar Docker
docker ps >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop no esta corriendo.
    echo Por favor, abre Docker Desktop primero.
    pause
    exit /b 1
)

REM Iniciar PostgreSQL si no esta corriendo
docker-compose ps | findstr "postgres" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Iniciando PostgreSQL...
    docker-compose up -d
    timeout /t 3 /nobreak >nul
)

REM Iniciar Backend en nueva ventana
echo [INFO] Iniciando Backend...
start "Nougram Backend" cmd /k "cd /d %~dp0..\..\backend && if exist venv (call venv\Scripts\activate.bat && python main.py) else (echo [ERROR] Ejecuta primero desplegar_local.bat && pause)"

REM Esperar un poco antes de iniciar el frontend
timeout /t 2 /nobreak >nul

REM Iniciar Frontend en nueva ventana
echo [INFO] Iniciando Frontend...
start "Nougram Frontend" cmd /k "cd /d %~dp0..\..\nougram_front && npm run dev"

echo.
echo [OK] Servicios iniciados en ventanas separadas
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul

