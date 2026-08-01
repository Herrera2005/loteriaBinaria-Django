$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "=== Lotería Binaria - inicio local SQLite ===" -ForegroundColor Cyan
python manage.py check
if ($LASTEXITCODE -ne 0) { throw "Falló manage.py check." }

python manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { throw "Falló migrate." }

python manage.py seed_baseline
if ($LASTEXITCODE -ne 0) { throw "Falló seed_baseline." }

python manage.py backfill_wallets
if ($LASTEXITCODE -ne 0) { throw "Falló backfill_wallets." }

Write-Host "Abre http://127.0.0.1:8000/" -ForegroundColor Green
Write-Host "Detén el servidor con Ctrl+C." -ForegroundColor Yellow
python manage.py runserver
