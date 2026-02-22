@echo off
echo ========================================
echo  Verificacion de Servicios - Nougram
echo ========================================
echo.

echo [INFO] Verificando servicios...
echo.

REM Verificar PostgreSQL
echo [STEP] Verificando PostgreSQL (puerto 5432)...
netstat -ano | findstr :5432 >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PostgreSQL no esta corriendo
    echo [SOLUCION] Ejecuta: iniciar_docker.bat
) else (
    echo [OK] PostgreSQL esta corriendo
)
echo.

REM Verificar Backend
echo [STEP] Verificando Backend (puerto 8000)...
netstat -ano | findstr :8000 >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Backend no esta corriendo
    echo [SOLUCION] Ejecuta: iniciar_backend.bat
) else (
    echo [OK] Backend esta corriendo
    echo [INFO] Puedes acceder a: http://localhost:8000
    echo [INFO] Documentacion API: http://localhost:8000/docs
)
echo.

REM Verificar Frontend
echo [STEP] Verificando Frontend (puerto 3000)...
netstat -ano | findstr :3000 >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Frontend no esta corriendo
    echo [SOLUCION] Ejecuta: iniciar_frontend.bat
) else (
    echo [OK] Frontend esta corriendo
    echo [INFO] Puedes acceder a: http://localhost:3000
)
echo.

echo ========================================
echo  Resumen
echo ========================================
echo.
echo Si todos los servicios estan corriendo:
echo 1. Abre tu navegador en: http://localhost:3000
echo 2. Haz clic en "Bypass Auth (Dev Only)" para iniciar sesion
echo.
echo Si algun servicio no esta corriendo, ejecuta los scripts correspondientes.
echo.
pause




