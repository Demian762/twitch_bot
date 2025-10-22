# ============================================================================
# Script de Empaquetado - Bot del Estadio
# ============================================================================
# Este script crea el paquete ZIP para distribuir a usuarios finales
# 
# Uso: .\setup_distribution.ps1
# 
# Genera: BotDelEstadio_vX.X.zip listo para distribuir
# ============================================================================

param(
    [string]$Version = "1.0"
)

# Configuracion
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$DistDir = Join-Path $ScriptDir "package"
$OutputZip = Join-Path $ProjectRoot "BotDelEstadio_v$Version.zip"

# Colores para output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-ErrorMsg { Write-Host $args -ForegroundColor Red }

Clear-Host
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "     BOT DEL ESTADIO - Generador de Distribucion              " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 1. Verificar requisitos
# ============================================================================
Write-Info "[1/6] Verificando requisitos..."

# Verificar que estamos en la rama correcta
$currentBranch = git rev-parse --abbrev-ref HEAD 2>$null
if ($currentBranch -ne "master") {
    Write-Warning "    Advertencia: No estas en la rama master (actual: $currentBranch)"
    Write-Warning "    La distribucion deberia hacerse desde master"
    $continue = Read-Host "    Continuar de todos modos? (S/N)"
    if ($continue -ne "S" -and $continue -ne "s") {
        Write-ErrorMsg "Cancelado por el usuario"
        exit 1
    }
}

Write-Success "    [OK] Requisitos verificados"
Write-Host ""

# ============================================================================
# 2. Limpiar carpeta de distribucion anterior
# ============================================================================
Write-Info "[2/6] Preparando carpeta de distribucion..."

if (Test-Path $DistDir) {
    Remove-Item -Path $DistDir -Recurse -Force
    Write-Info "    Carpeta anterior eliminada"
}

New-Item -ItemType Directory -Path $DistDir -Force | Out-Null
Write-Success "    [OK] Carpeta de distribucion creada"
Write-Host ""

# ============================================================================
# 3. Copiar archivos esenciales
# ============================================================================
Write-Info "[3/6] Copiando archivos de distribucion..."

# Copiar launcher y documentacion
Copy-Item -Path (Join-Path $ScriptDir "INICIAR_BOT.bat") -Destination $DistDir
Copy-Item -Path (Join-Path $ScriptDir "LEEME.txt") -Destination $DistDir

# Copiar carpeta config con template
$configDest = Join-Path $DistDir "config"
New-Item -ItemType Directory -Path $configDest -Force | Out-Null
Copy-Item -Path (Join-Path $ProjectRoot "config\config_template.ini") -Destination $configDest
Copy-Item -Path (Join-Path $ProjectRoot "config\README.md") -Destination $configDest

# Crear carpeta logs vacia (con .gitkeep para que se incluya)
$logsDest = Join-Path $DistDir "logs"
New-Item -ItemType Directory -Path $logsDest -Force | Out-Null
"" | Out-File -FilePath (Join-Path $logsDest ".gitkeep") -Encoding UTF8

Write-Success "    [OK] Archivos copiados"
Write-Host ""

# ============================================================================
# 4. Incluir FFmpeg
# ============================================================================
Write-Info "[4/6] Incluyendo FFmpeg..."

$ffmpegSource = Join-Path $ProjectRoot "ffmpeg"
$ffmpegDest = Join-Path $DistDir "ffmpeg"

if (Test-Path $ffmpegSource) {
    Copy-Item -Path $ffmpegSource -Destination $ffmpegDest -Recurse
    Write-Success "    [OK] FFmpeg incluido"
} else {
    Write-Warning "    [!] FFmpeg no encontrado en $ffmpegSource"
    Write-Warning "    El usuario debera descargarlo manualmente o el bot lo descargara automaticamente"
}
Write-Host ""

# ============================================================================
# 5. Python embebido (opcional)
# ============================================================================
Write-Info "[5/6] Python embebido..."

$pythonEmbedSource = Join-Path $ProjectRoot "python-embedded"
$pythonEmbedDest = Join-Path $DistDir "python-embedded"

if (Test-Path $pythonEmbedSource) {
    Write-Info "    Copiando Python embebido (esto puede tardar un poco)..."
    Copy-Item -Path $pythonEmbedSource -Destination $pythonEmbedDest -Recurse
    Write-Success "    [OK] Python embebido incluido"
} else {
    Write-Warning "    [!] Python embebido no encontrado"
    Write-Info "    El usuario debera tener Python instalado en su sistema"
}
Write-Host ""

# ============================================================================
# 6. Crear archivo ZIP
# ============================================================================
Write-Info "[6/6] Generando archivo ZIP..."

if (Test-Path $OutputZip) {
    Remove-Item -Path $OutputZip -Force
}

# Comprimir
Add-Type -Assembly "System.IO.Compression.FileSystem"
[System.IO.Compression.ZipFile]::CreateFromDirectory($DistDir, $OutputZip)

# Obtener tamaño del archivo
$zipSize = (Get-Item $OutputZip).Length / 1MB
$zipSizeStr = "{0:N2} MB" -f $zipSize

Write-Success "    [OK] ZIP creado exitosamente"
Write-Host ""

# ============================================================================
# Resumen
# ============================================================================
Write-Host "================================================================" -ForegroundColor Green
Write-Host "         DISTRIBUCION GENERADA EXITOSAMENTE                     " -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Archivo generado:" -ForegroundColor Cyan
Write-Host "  $OutputZip" -ForegroundColor White
Write-Host ""
Write-Host "Tamaño: $zipSizeStr" -ForegroundColor Cyan
Write-Host ""
Write-Host "Contenido del paquete:" -ForegroundColor Cyan
Write-Host "  - INICIAR_BOT.bat       - Launcher principal"
Write-Host "  - LEEME.txt             - Instrucciones para usuarios"
Write-Host "  - config/               - Plantilla de configuracion"
Write-Host "  - ffmpeg/               - Procesador de audio (si existe)"
Write-Host "  - python-embedded/      - Python portable (si existe)"
Write-Host "  - logs/                 - Carpeta para logs"
Write-Host ""
Write-Host "Proximos pasos:" -ForegroundColor Yellow
Write-Host "  1. Probar el ZIP en un entorno limpio"
Write-Host "  2. Distribuir a los usuarios"
Write-Host "  3. Los usuarios deben:"
Write-Host "     - Descomprimir el ZIP"
Write-Host "     - Configurar config/config.ini"
Write-Host "     - Ejecutar INICIAR_BOT.bat"
Write-Host ""

# Preguntar si abrir la carpeta
$openFolder = Read-Host "Abrir carpeta del ZIP? (S/N)"
if ($openFolder -eq "S" -or $openFolder -eq "s") {
    explorer.exe (Split-Path -Parent $OutputZip)
}

# Limpiar carpeta temporal
Write-Info "Limpiando archivos temporales..."
Remove-Item -Path $DistDir -Recurse -Force
Write-Success "[OK] Listo!"
