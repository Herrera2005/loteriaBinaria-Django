$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not $env:DATABASE_URL -or -not $env:DATABASE_URL.StartsWith("mysql://")) {
    throw "DATABASE_URL debe apuntar a una base MySQL de prueba vacía."
}
if (-not $env:DJANGO_DEMO_PASSWORD) {
    $env:DJANGO_DEMO_PASSWORD = "Demo-Only-MySQL-Verification-2026!"
}
$env:DJANGO_DEBUG = "True"

$commands = @(
    @("manage.py", "check"),
    @("manage.py", "makemigrations", "--check", "--dry-run"),
    @("manage.py", "migrate", "--noinput"),
    @("manage.py", "seed_baseline"),
    @("manage.py", "seed_baseline"),
    @("manage.py", "seed_demo"),
    @("manage.py", "seed_demo"),
    @("manage.py", "backfill_wallets"),
    @("manage.py", "backfill_wallets"),
    @("manage.py", "process_expired_requests"),
    @("manage.py", "process_expired_requests"),
    @("manage.py", "sync_lottery_event_states"),
    @("manage.py", "sync_lottery_event_states"),
    @("manage.py", "process_lottery_schedules"),
    @("manage.py", "process_lottery_schedules"),
    @("manage.py", "test", "--verbosity", "2")
)

foreach ($arguments in $commands) {
    & python @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Falló: python $($arguments -join ' ')"
    }
}
