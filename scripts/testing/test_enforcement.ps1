# Script de Prueba - Enforcement de Roles
# Verifica que los permisos bloquean correctamente

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PRUEBA DE ENFORCEMENT DE ROLES" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$headers = @{
    Authorization = 'Bearer dev-bypass-token'
    'Content-Type' = 'application/json'
}

# Verificar usuario actual
Write-Host "Usuario actual:" -ForegroundColor Yellow
try {
    $user = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/me" -Method Get -Headers $headers -ErrorAction Stop
    Write-Host "  Email: $($user.email)" -ForegroundColor White
    Write-Host "  Rol: $($user.role)" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "  ERROR - No se pudo obtener usuario" -ForegroundColor Red
    exit 1
}

# Probar crear un servicio (debería funcionar si es Super Admin)
Write-Host "Prueba 1: Crear un servicio..." -ForegroundColor Yellow
$serviceData = @{
    name = "Test Service Enforcement"
    description = "Servicio de prueba para enforcement"
    default_margin_target = 0.4
    is_active = $true
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod `
        -Uri "$baseUrl/api/v1/services/" `
        -Method Post `
        -Headers $headers `
        -Body $serviceData `
        -ErrorAction Stop
    
    Write-Host "  OK - Servicio creado exitosamente" -ForegroundColor Green
    Write-Host "  ID: $($result.id)" -ForegroundColor Gray
    Write-Host "  Esto confirma que tienes permisos de Super Admin" -ForegroundColor Gray
    
    # Intentar eliminar el servicio de prueba
    try {
        Invoke-RestMethod `
            -Uri "$baseUrl/api/v1/services/$($result.id)" `
            -Method Delete `
            -Headers $headers `
            -ErrorAction Stop | Out-Null
        Write-Host "  Servicio de prueba eliminado" -ForegroundColor Gray
    } catch {
        Write-Host "  No se pudo eliminar servicio de prueba" -ForegroundColor Yellow
    }
    
} catch {
    if ($_.Exception.Response.StatusCode -eq 403) {
        Write-Host "  BLOQUEADO - Error 403 Forbidden" -ForegroundColor Red
        Write-Host "  No tienes permisos para crear servicios" -ForegroundColor Yellow
        Write-Host "  Esto confirma que el enforcement esta funcionando" -ForegroundColor Green
    } else {
        Write-Host "  ERROR - $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# Resumen
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  RESUMEN DE PRUEBA" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Rol actual: $($user.role)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para probar con diferentes roles:" -ForegroundColor Yellow
Write-Host "  1. Ejecuta: .\cambiar_rol.ps1 -rol 'product_manager'" -ForegroundColor White
Write-Host "  2. Cambia el rol en PostgreSQL" -ForegroundColor White
Write-Host "  3. Reinicia el backend" -ForegroundColor White
Write-Host "  4. Ejecuta este script nuevamente" -ForegroundColor White
Write-Host "  5. Deberias ver ERROR 403 al intentar crear servicios" -ForegroundColor Red
Write-Host ""
Write-Host "Comportamiento esperado:" -ForegroundColor Cyan
Write-Host "  - Super Admin: Todo funciona" -ForegroundColor Green
Write-Host "  - Admin Financiero: Puede crear servicios, costs, etc." -ForegroundColor Green
Write-Host "  - Product Manager: Solo puede crear quotes (403 en otros)" -ForegroundColor Yellow
Write-Host ""

