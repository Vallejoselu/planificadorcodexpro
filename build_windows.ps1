param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if ($Clean) {
    Remove-Item -LiteralPath "$Root\build" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath "$Root\dist" -Recurse -Force -ErrorAction SilentlyContinue
}

$Version = python -c "from app_info import VERSION; print(VERSION)"
$Name = "PlanificadorDeliveryPro"
$ResourceArg = "resources;resources"
$IconPath = Join-Path $Root "resources\icons\app.ico"

$Args = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--windowed",
    "--name", $Name,
    "--add-data", $ResourceArg,
    "--distpath", "$Root\dist",
    "--workpath", "$Root\build",
    "main.py"
)

if (Test-Path $IconPath) {
    $Args = @(
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name", $Name,
        "--icon", $IconPath,
        "--add-data", $ResourceArg,
        "--distpath", "$Root\dist",
        "--workpath", "$Root\build",
        "main.py"
    )
}

python $Args

$OutputDir = Join-Path $Root "dist\$Name"
$ExePath = Join-Path $OutputDir "$Name.exe"

if (-not (Test-Path $ExePath)) {
    throw "No se ha generado el ejecutable esperado: $ExePath"
}

Write-Host ""
Write-Host "Planificador Delivery Pro $Version construido correctamente."
Write-Host "Ejecutable: $ExePath"
Write-Host "Los datos de usuario se guardaran en %LOCALAPPDATA%\PlanificadorDeliveryPro\delivery.db"
