# Script para ver los logs del backend

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   COMO VER LOS LOGS DEL BACKEND" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "OPCION 1: Ver la ventana de PowerShell del backend" -ForegroundColor Yellow
Write-Host "  1. Busca la ventana de PowerShell que se abrio cuando iniciamos el backend" -ForegroundColor White
Write-Host "  2. Deberias ver los logs en tiempo real ahi" -ForegroundColor White
Write-Host "  3. Busca el error completo con el stack trace" -ForegroundColor White
Write-Host "  4. El error deberia mostrar algo como:" -ForegroundColor Gray
Write-Host "     Traceback (most recent call last):" -ForegroundColor Gray
Write-Host "       File ..." -ForegroundColor Gray
Write-Host "     AttributeError: 'str' object has no attribute 'value'" -ForegroundColor Gray
Write-Host ""

Write-Host "OPCION 2: Hacer una peticion y ver el error detallado" -ForegroundColor Yellow
Write-Host "  Ejecutando peticion ahora..." -ForegroundColor White
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/users/' `
        -Headers @{Authorization='Bearer dev-bypass-token'} `
        -Method Get `
        -TimeoutSec 5 `
        -ErrorAction Stop
    
    Write-Host "OK - Endpoint funcionando!" -ForegroundColor Green
    Write-Host "Usuarios encontrados: $($response.Content | ConvertFrom-Json | Select-Object -ExpandProperty total)" -ForegroundColor White
} catch {
    Write-Host "ERROR CAPTURADO:" -ForegroundColor Red
    Write-Host ""
    Write-Host "Mensaje: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host ""
    
    if ($_.ErrorDetails) {
        Write-Host "Detalles del error:" -ForegroundColor Cyan
        Write-Host $_.ErrorDetails.Message -ForegroundColor White
        Write-Host ""
        
        try {
            $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "Error JSON parseado:" -ForegroundColor Cyan
            $errorJson | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor White
        } catch {
            Write-Host "No se pudo parsear como JSON" -ForegroundColor Gray
        }
    }
    
    if ($_.Exception.Response) {
        Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   INSTRUCCIONES PARA VER LOGS COMPLETOS" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para ver el stack trace completo del error:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Busca la ventana de PowerShell donde esta corriendo el backend" -ForegroundColor White
Write-Host "2. Deberias ver algo como esto cuando ocurre el error:" -ForegroundColor White
Write-Host ""
Write-Host "   ERROR:    Exception on /api/v1/users/ [GET]" -ForegroundColor Red
Write-Host "   Traceback (most recent call last):" -ForegroundColor Gray
Write-Host "     File '...', line X, in ..." -ForegroundColor Gray
Write-Host "     ..." -ForegroundColor Gray
Write-Host "   AttributeError: 'str' object has no attribute 'value'" -ForegroundColor Red
Write-Host ""
Write-Host "3. Copia el stack trace completo y compartelo" -ForegroundColor White
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

