# build_exe.ps1
# Script para generar automáticamente ejecutables desde scripts Python

param(
    [string]$Script,
    [string]$ExeName,
    [switch]$Help
)

$PythonExe = "C:/Users/chave/AppData/Local/Microsoft/WindowsApps/python3.13.exe"
$CurrentDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($Help) {
    Write-Host @"
USO: .\build_exe.ps1 -Script "script.py" -ExeName "NombreExe"
"@
    exit 0
}

if (-not $Script) {
    Write-Host "Selecciona un script Python:" -ForegroundColor Yellow
    $PythonScripts = @(Get-ChildItem $CurrentDir -Filter "*.py" -File | Select-Object -ExpandProperty Name)
    for ($i = 0; $i -lt $PythonScripts.Count; $i++) {
        Write-Host "$($i+1). $($PythonScripts[$i])"
    }
    [int]$choice = Read-Host "Numero"
    if ($choice -lt 1 -or $choice -gt $PythonScripts.Count) { exit 1 }
    $Script = $PythonScripts[$choice - 1]
}

if (-not $ExeName) {
    $ExeName = $Script -replace '\.py$', ''
}

$ScriptName = $Script

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  COMPILADOR DE EJECUTABLES PYTHON" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📄 Script: $ScriptName" -ForegroundColor White
Write-Host "📦 Ejecutable: $ExeName.exe" -ForegroundColor White
Write-Host ""

if (-not (Test-Path "$CurrentDir\$ScriptName")) {
    Write-Host "❌ Error: No se encuentra '$ScriptName'" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Script encontrado" -ForegroundColor Green

Write-Host "`nVerificando PyInstaller..." -ForegroundColor Yellow
$PyInstallerCheck = & $PythonExe -m pip show pyinstaller 2>$null
if ($null -eq $PyInstallerCheck) {
    & $PythonExe -m pip install pyinstaller -q
}
Write-Host "✅ PyInstaller disponible" -ForegroundColor Green

Write-Host "`nLimpiando builds anteriores..." -ForegroundColor Yellow
@("build", "dist") | ForEach-Object {
    if (Test-Path "$CurrentDir\$_") {
        Remove-Item "$CurrentDir\$_" -Recurse -Force -ErrorAction SilentlyContinue
    }
}
if (Test-Path "$CurrentDir\${ExeName}.spec") {
    Remove-Item "$CurrentDir\${ExeName}.spec" -Force -ErrorAction SilentlyContinue
}
Write-Host "✅ Limpieza completada" -ForegroundColor Green

Write-Host "`nGenerando ejecutable..." -ForegroundColor Yellow
Write-Host "─" * 60

& $PythonExe -m PyInstaller --onefile --console -n $ExeName $ScriptName 2>&1 | Where-Object { $_ -match "completed successfully" }

Write-Host ""

if (Test-Path "$CurrentDir\dist\${ExeName}.exe") {
    $ExeSize = (Get-Item "$CurrentDir\dist\${ExeName}.exe").Length / 1MB
    Write-Host "=" * 60
    Write-Host "[OK] Ejecutable generado" -ForegroundColor Green
    Write-Host "=" * 60
    Write-Host "`nUbicacion: .\dist\${ExeName}.exe" -ForegroundColor Cyan
    Write-Host "Tamanio: $([math]::Round($ExeSize, 2)) MB" -ForegroundColor Cyan
    Write-Host "`n[OK] Mantiene consola abierta" -ForegroundColor Green
    Write-Host "[OK] Distribuible en cualquier Windows" -ForegroundColor Green
    
    Write-Host "`nAbrir carpeta? (S/N): " -ForegroundColor Yellow -NoNewline
    $response = Read-Host
    if ($response -eq "S" -or $response -eq "s") {
        Start-Process explorer.exe "$CurrentDir\dist"
    }
} else {
    Write-Host "[ERROR] No se pudo generar el ejecutable" -ForegroundColor Red
    exit 1
}

Write-Host ""
