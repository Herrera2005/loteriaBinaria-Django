$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
$VerificationDatabase = Join-Path $ProjectRoot "verification.sqlite3"

$Previous = @{
    DATABASE_URL = $env:DATABASE_URL
    DJANGO_DEBUG = $env:DJANGO_DEBUG
    DJANGO_SECRET_KEY = $env:DJANGO_SECRET_KEY
    DJANGO_DEMO_PASSWORD = $env:DJANGO_DEMO_PASSWORD
    DJANGO_ALLOWED_HOSTS = $env:DJANGO_ALLOWED_HOSTS
    DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS = $env:DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS
    DJANGO_SECURE_HSTS_PRELOAD = $env:DJANGO_SECURE_HSTS_PRELOAD
    SMOKE_PORT = $env:SMOKE_PORT
}

function Invoke-CheckedPython {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Falló: python $($Arguments -join ' ')"
    }
}

Write-Host "=== Taller #3: verificación integral SQLite limpia ===" -ForegroundColor Cyan
Write-Host "Python:" -ForegroundColor DarkCyan
Invoke-CheckedPython "--version"
Invoke-CheckedPython "-m" "pip" "check"
Invoke-CheckedPython "-c" "import django, environ; print('Django', django.get_version()); print('django-environ', environ.__version__)"

try {
    if (Test-Path $VerificationDatabase) { Remove-Item $VerificationDatabase -Force }
    $env:DATABASE_URL = "sqlite:///verification.sqlite3"
    $env:DJANGO_DEBUG = "True"
    $env:DJANGO_DEMO_PASSWORD = "Demo-Only-Verification-2026!"

    Invoke-CheckedPython scripts/manifest_project.py
    Invoke-CheckedPython scripts/audit_project.py
    Invoke-CheckedPython manage.py check
    Invoke-CheckedPython manage.py makemigrations --check --dry-run
    Invoke-CheckedPython manage.py migrate --noinput
    Invoke-CheckedPython manage.py showmigrations

    foreach ($command in @("seed_baseline", "seed_demo", "backfill_wallets", "process_expired_requests", "sync_lottery_event_states", "process_lottery_schedules")) {
        Invoke-CheckedPython manage.py $command
        Invoke-CheckedPython manage.py $command
    }

    Write-Host "=== Pruebas funcionales demostrables posteriores a P-28 ===" -ForegroundColor Cyan
    Invoke-CheckedPython manage.py test `
        apps.accounts.tests.test_auth `
        apps.accounts.tests.test_auth_and_modes `
        apps.accounts.tests.test_views `
        apps.finance.tests.test_operations `
        apps.finance.tests.test_vendor_finance `
        apps.finance.tests.test_views `
        apps.vendors.tests.test_views `
        apps.vendors.tests.test_client_requests `
        apps.vendors.tests.test_vendor_assignment `
        apps.vendors.tests.test_vendor_settlement `
        apps.vendors.tests.test_request_closure `
        apps.lottery.tests.test_crud `
        apps.lottery.tests.test_ticket_purchase `
        apps.lottery.tests.test_result_publication `
        apps.lottery.tests.test_event_series `
        apps.lottery.tests.test_automatic_results `
        apps.lottery.tests.test_permissions `
        apps.core.tests.test_ux_accessibility `
        --verbosity 2

    Write-Host "=== Smoke test y suite completa ===" -ForegroundColor Cyan
    $env:SMOKE_PORT = "8876"
    Invoke-CheckedPython scripts/smoke_runserver.py
    Invoke-CheckedPython manage.py test --verbosity 2
    Invoke-CheckedPython manage.py findstatic css/app.css js/app.js img/logo-placeholder.png
    Invoke-CheckedPython manage.py collectstatic --noinput --clear

    $env:DJANGO_DEBUG = "False"
    $env:DJANGO_SECRET_KEY = "verification-only-long-secret-key-not-for-production-2026"
    $env:DJANGO_ALLOWED_HOSTS = "127.0.0.1,localhost"
    $env:DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS = "True"
    $env:DJANGO_SECURE_HSTS_PRELOAD = "True"
    Invoke-CheckedPython manage.py check --deploy

    Write-Host "=== Verificación integral completada correctamente ===" -ForegroundColor Green
}
finally {
    if (Test-Path $VerificationDatabase) { Remove-Item $VerificationDatabase -Force }
    $StaticFilesPath = Join-Path $ProjectRoot "staticfiles"
    if (Test-Path $StaticFilesPath) { Remove-Item $StaticFilesPath -Recurse -Force }
    Get-ChildItem $ProjectRoot -Recurse -Directory -Filter __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
    Get-ChildItem $ProjectRoot -Recurse -File -Include *.pyc,*.pyo -ErrorAction SilentlyContinue | Remove-Item -Force

    $env:DATABASE_URL = $Previous.DATABASE_URL
    $env:DJANGO_DEBUG = $Previous.DJANGO_DEBUG
    $env:DJANGO_SECRET_KEY = $Previous.DJANGO_SECRET_KEY
    $env:DJANGO_DEMO_PASSWORD = $Previous.DJANGO_DEMO_PASSWORD
    $env:DJANGO_ALLOWED_HOSTS = $Previous.DJANGO_ALLOWED_HOSTS
    $env:DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS = $Previous.DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS
    $env:DJANGO_SECURE_HSTS_PRELOAD = $Previous.DJANGO_SECURE_HSTS_PRELOAD
    $env:SMOKE_PORT = $Previous.SMOKE_PORT
}
