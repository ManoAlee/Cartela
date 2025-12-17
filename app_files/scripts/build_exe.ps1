```powershell
# Powershell script to build a single-file exe using PyInstaller
# Usage: run from repo root: .\app_files\scripts\build_exe.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# repo root is two levels up from app_files/scripts
$repoRoot = Resolve-Path (Join-Path $scriptDir '..\..')
$appRoot = Join-Path $repoRoot 'app_files'

$venv = Join-Path $repoRoot '.venv\Scripts\Activate.ps1'
if (Test-Path $venv) {
    Write-Host "Activating venv..."
    & $venv
}

# Ensure pyinstaller is available in the venv
$pyinstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyinstaller) {
    Write-Host "PyInstaller não encontrado. Instale com: python -m pip install -r requirements-build.txt"
    exit 1
}

# Files/data to bundle (add more as needed)
$dataFile = Join-Path $appRoot 'data\mega_cache.json'
$resourcesDir = Join-Path $appRoot 'resources'
$entry = Join-Path $appRoot 'run_app.py'


$adds = @(
    "$dataFile;.",
    "$(Join-Path $appRoot 'data');data",
    "$(Join-Path $appRoot 'resources');resources"
)

# Build: construct argument array to avoid newline/Out-String issues
$icon = (Join-Path $resourcesDir 'bingo.ico')
$baseArgs = @('--noconfirm','--onefile','--name','Cartela','--windowed','--icon',$icon)
$addArgs = @()
foreach ($a in $adds) { $addArgs += '--add-data'; $addArgs += $a }
$args = $baseArgs + $addArgs + @($entry)

Write-Host 'Running pyinstaller with args:' ($args -join ' ')
& pyinstaller @args

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build concluído. Verifique dist\Cartela.exe"
} else {
    Write-Host "Build falhou com código $LASTEXITCODE"
}

```