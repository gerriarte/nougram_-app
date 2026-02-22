# Script para cambiar el rol de un usuario y probar permisos
# Uso: .\cambiar_rol.ps1 -rol "product_manager"

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("super_admin", "admin_financiero", "product_manager")]
    [string]$rol
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CAMBIAR ROL DE USUARIO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$headers = @{
    Authorization = 'Bearer dev-bypass-token'
    'Content-Type' = 'application/json'
}

# Obtener usuario actual
Write-Host "Usuario actual:" -ForegroundColor Yellow
try {
    $user = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/me" -Method Get -Headers $headers -ErrorAction Stop
    Write-Host "  Email: $($user.email)" -ForegroundColor White
    Write-Host "  Rol actual: $($user.role)" -ForegroundColor White
} catch {
    Write-Host "  ERROR - No se pudo obtener usuario" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Cambiando rol a: $rol" -ForegroundColor Cyan
Write-Host ""
Write-Host "NOTA: Este script solo muestra el comando SQL." -ForegroundColor Yellow
Write-Host "Debes ejecutarlo manualmente en PostgreSQL:" -ForegroundColor Yellow
Write-Host ""
Write-Host "COMANDO SQL:" -ForegroundColor Green
Write-Host "UPDATE users SET role = '$rol' WHERE email = '$($user.email)';" -ForegroundColor White
Write-Host ""
Write-Host "Despues de ejecutar el SQL:" -ForegroundColor Cyan
Write-Host "  1. Reinicia el backend o espera a que recargue" -ForegroundColor Gray
Write-Host "  2. Prueba los endpoints en http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "  3. Verifica que los permisos funcionan correctamente" -ForegroundColor Gray
Write-Host ""

# Mostrar permisos del nuevo rol
Write-Host "PERMISOS DEL ROL '$rol':" -ForegroundColor Cyan
Write-Host ""

switch ($rol) {
    "super_admin" {
        Write-Host "  + Crear: TODO" -ForegroundColor Green
        Write-Host "  + Editar: TODO" -ForegroundColor Green
        Write-Host "  + Eliminar: TODO (inmediato)" -ForegroundColor Green
    }
    "admin_financiero" {
        Write-Host "  + Crear: costs, services, taxes, projects, quotes" -ForegroundColor Green
        Write-Host "  + Editar: costs, services, taxes, projects, quotes" -ForegroundColor Green
        Write-Host "  + Eliminar: Requiere aprobacion" -ForegroundColor Yellow
        Write-Host "  - NO puede: Gestionar usuarios" -ForegroundColor Red
    }
    "product_manager" {
        Write-Host "  + Crear: quotes solamente" -ForegroundColor Green
        Write-Host "  + Editar: quotes solamente" -ForegroundColor Green
        Write-Host "  + Eliminar: quotes (requiere aprobacion)" -ForegroundColor Yellow
        Write-Host "  - NO puede: costs, services, taxes, projects" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Para activar enforcement (bloquear realmente):" -ForegroundColor Cyan
Write-Host "  Edita backend/.env y cambia:" -ForegroundColor White
Write-Host "  FEATURE_ROLES_ENFORCE=true" -ForegroundColor White
Write-Host ""

