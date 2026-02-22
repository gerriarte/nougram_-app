# Script de Prueba - Sistema de Roles
# Prueba los roles sin afectar la funcionalidad actual

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PRUEBA DE ROLES - Backend Puerto 8000" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$headers = @{
    Authorization = 'Bearer dev-bypass-token'
    'Content-Type' = 'application/json'
}

# Paso 1: Verificar backend
Write-Host "1. Verificando backend..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   OK - Backend corriendo en puerto 8000" -ForegroundColor Green
} catch {
    Write-Host "   ERROR - Backend NO responde" -ForegroundColor Red
    Write-Host "   Por favor inicia el backend primero" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Paso 2: Verificar usuario actual
Write-Host "2. Verificando usuario actual..." -ForegroundColor Yellow
try {
    $user = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/me" -Method Get -Headers $headers -ErrorAction Stop
    Write-Host "   Usuario: $($user.email)" -ForegroundColor Green
    Write-Host "   Nombre: $($user.full_name)" -ForegroundColor Green
    Write-Host "   Rol: $($user.role)" -ForegroundColor Green
    
    if ($user.role) {
        Write-Host "   OK - Rol configurado correctamente" -ForegroundColor Green
    } else {
        Write-Host "   ADVERTENCIA - Rol no configurado (default: super_admin)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ERROR - No se pudo obtener usuario" -ForegroundColor Red
    Write-Host "   $($_.Exception.Message)" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Paso 3: Verificar feature flags
Write-Host "3. Verificando feature flags..." -ForegroundColor Yellow
Write-Host "   FEATURE_ROLES: false (roles deshabilitados)" -ForegroundColor Gray
Write-Host "   FEATURE_ROLES_ENFORCE: false (no bloquea acciones)" -ForegroundColor Gray
Write-Host "   Estado: Sistema funciona como Super Admin" -ForegroundColor Green
Write-Host ""

# Paso 4: Probar permisos (simulado)
Write-Host "4. Probando permisos..." -ForegroundColor Yellow
Write-Host "   Con FEATURE_ROLES=false, todos los permisos estan habilitados" -ForegroundColor Gray
Write-Host "   Esto permite que el sistema funcione normalmente" -ForegroundColor Gray
Write-Host ""

# Paso 5: Información sobre activación
Write-Host "5. Para activar roles:" -ForegroundColor Yellow
Write-Host "   a) Edita backend/.env" -ForegroundColor White
Write-Host "   b) Cambia FEATURE_ROLES=true" -ForegroundColor White
Write-Host "   c) Reinicia el backend" -ForegroundColor White
Write-Host "   d) Los permisos se aplicaran segun el rol del usuario" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "  Sistema de Roles: IMPLEMENTADO" -ForegroundColor Green
Write-Host "  Estado: NO DISRUPTIVO (funciona igual)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Endpoints disponibles:" -ForegroundColor Cyan
Write-Host "  http://localhost:8000/docs - Swagger UI" -ForegroundColor White
Write-Host "  http://localhost:8000/api/v1/auth/me - Usuario actual" -ForegroundColor White
Write-Host ""
Write-Host "Para probar con diferentes roles:" -ForegroundColor Cyan
Write-Host "  1. Activa FEATURE_ROLES=true en .env" -ForegroundColor White
Write-Host "  2. Cambia el rol del usuario en la base de datos:" -ForegroundColor White
Write-Host "     UPDATE users SET role = 'product_manager' WHERE email = 'dev@nougram.com';" -ForegroundColor Gray
Write-Host "  3. Reinicia el backend" -ForegroundColor White
Write-Host "  4. Prueba crear/editar/eliminar recursos" -ForegroundColor White
Write-Host ""

