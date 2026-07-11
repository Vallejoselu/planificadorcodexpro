param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)

    Write-Host ""
    Write-Host "== $Message =="
}

function Find-InnoSetup {

    $command = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue

    if ($command) {

        return $command.Source
    }

    $candidates = @(
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    )

    foreach ($candidate in $candidates) {

        if (Test-Path -LiteralPath $candidate) {

            return $candidate
        }
    }

    return $null
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

try {

    Write-Step "Comprobando Inno Setup"
    $InnoCompiler = Find-InnoSetup

    if (-not $InnoCompiler) {

        Write-Host "Inno Setup no está instalado."
        Write-Host "Instala Inno Setup 6 o añade ISCC.exe al PATH."
        exit 1
    }

    Write-Host "ISCC.exe encontrado en: $InnoCompiler"

    Write-Step "Generando ejecutable con PyInstaller"
    $buildArgs = @("-ExecutionPolicy", "Bypass", "-File", ".\build_windows.ps1")

    if ($Clean) {

        $buildArgs += "-Clean"
    }

    powershell @buildArgs

    if ($LASTEXITCODE -ne 0) {

        throw "La generacion del ejecutable con PyInstaller ha fallado."
    }

    $ExePath = Join-Path $Root "dist\PlanificadorDeliveryPro\PlanificadorDeliveryPro.exe"

    if (-not (Test-Path -LiteralPath $ExePath)) {

        throw "No se ha encontrado el ejecutable esperado: $ExePath"
    }

    Write-Host "Ejecutable listo: $ExePath"

    Write-Step "Compilando instalador con Inno Setup"
    $IssPath = Join-Path $Root "installer\PlanificadorDeliveryPro.iss"

    if (-not (Test-Path -LiteralPath $IssPath)) {

        throw "No se ha encontrado el script de Inno Setup: $IssPath"
    }

    & $InnoCompiler $IssPath

    if ($LASTEXITCODE -ne 0) {

        throw "La compilacion del instalador con Inno Setup ha fallado."
    }

    $Version = python -c "from app_info import VERSION; print(VERSION)"
    $InstallerPath = Join-Path $Root "installer_output\PlanificadorDeliveryPro-Setup-$Version.exe"

    if (-not (Test-Path -LiteralPath $InstallerPath)) {

        throw "No se ha generado el instalador esperado: $InstallerPath"
    }

    Write-Step "Proceso completado"
    Write-Host "Instalador generado correctamente:"
    Write-Host $InstallerPath
}
catch {

    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)"
    exit 1
}
