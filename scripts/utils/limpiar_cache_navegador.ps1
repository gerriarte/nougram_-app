# Script para limpiar caché del navegador y verificar configuración

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   LIMPIEZA DE CACHÉ Y VERIFICACIÓN" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar backend
Write-Host "1. Verificando Backend..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri 'http://localhost:8000/health' -Method Get -TimeoutSec 5
    Write-Host "   OK - Backend corriendo en puerto 8000" -ForegroundColor Green
} catch {
    Write-Host "   ERROR - Backend no responde en puerto 8000" -ForegroundColor Red
    Write-Host "   Por favor inicia el backend primero" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Verificar frontend
Write-Host "2. Verificando Frontend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri 'http://localhost:3000' -Method Get -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "   OK - Frontend corriendo en puerto 3000" -ForegroundColor Green
    }
} catch {
    Write-Host "   ADVERTENCIA - Frontend no responde" -ForegroundColor Yellow
    Write-Host "   Esto es normal si aun no lo has iniciado" -ForegroundColor Gray
}

Write-Host ""

# Instrucciones para limpiar caché
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "   INSTRUCCIONES PARA LIMPIAR CACHÉ" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""

Write-Host "OPCIÓN 1: Hard Refresh (Más Rápido)" -ForegroundColor Cyan
Write-Host "  1. Abre http://localhost:3000 en tu navegador" -ForegroundColor White
Write-Host "  2. Presiona Ctrl + Shift + R (Windows) o Cmd + Shift + R (Mac)" -ForegroundColor White
Write-Host "  3. Esto forzará la recarga sin caché" -ForegroundColor Gray
Write-Host ""

Write-Host "OPCIÓN 2: Modo Incógnito (Recomendado)" -ForegroundColor Cyan
Write-Host "  1. Abre una ventana incógnita:" -ForegroundColor White
Write-Host "     - Chrome/Edge: Ctrl + Shift + N" -ForegroundColor Gray
Write-Host "     - Firefox: Ctrl + Shift + P" -ForegroundColor Gray
Write-Host "  2. Ve a http://localhost:3000" -ForegroundColor White
Write-Host "  3. Esto evita completamente el caché" -ForegroundColor Gray
Write-Host ""

Write-Host "OPCIÓN 3: Limpiar Caché Manualmente" -ForegroundColor Cyan
Write-Host "  1. Abre DevTools (F12)" -ForegroundColor White
Write-Host "  2. Click derecho en el botón Refresh" -ForegroundColor White
Write-Host "  3. Selecciona 'Empty Cache and Hard Reload'" -ForegroundColor White
Write-Host ""

Write-Host "=================================================================" -ForegroundColor Green
Write-Host "   VERIFICACIÓN POST-LIMPIEZA" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Después de limpiar el caché:" -ForegroundColor Yellow
Write-Host "  1. Abre DevTools (F12)" -ForegroundColor White
Write-Host "  2. Ve a la pestaña 'Network'" -ForegroundColor White
Write-Host "  3. Recarga la página (F5)" -ForegroundColor White
Write-Host "  4. Busca peticiones a /api/v1/..." -ForegroundColor White
Write-Host "  5. Verifica que TODAS apunten a:" -ForegroundColor White
Write-Host "     http://localhost:8000/api/v1/..." -ForegroundColor Green
Write-Host ""

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   ESTADO ACTUAL" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "API URL:  http://localhost:8000/api/v1" -ForegroundColor Green
Write-Host ""
Write-Host "Correcciones aplicadas:" -ForegroundColor Yellow
Write-Host "  + Endpoint delete-requests corregido" -ForegroundColor White
Write-Host "  + Manejo graceful de tabla inexistente" -ForegroundColor White
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

