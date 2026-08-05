#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
VERIFY_DB="$ROOT/verification.sqlite3"
OLD_DATABASE_URL="${DATABASE_URL-}"
OLD_DEBUG="${DJANGO_DEBUG-}"
OLD_SECRET="${DJANGO_SECRET_KEY-}"
OLD_PASSWORD="${DJANGO_DEMO_PASSWORD-}"
OLD_HOSTS="${DJANGO_ALLOWED_HOSTS-}"
OLD_HSTS_SUBDOMAINS="${DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS-}"
OLD_HSTS_PRELOAD="${DJANGO_SECURE_HSTS_PRELOAD-}"
OLD_SMOKE_PORT="${SMOKE_PORT-}"

cleanup() {
  rm -f "$VERIFY_DB"
  rm -rf "$ROOT/staticfiles"
  find "$ROOT" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
  find "$ROOT" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete 2>/dev/null || true
  [[ -n "$OLD_DATABASE_URL" ]] && export DATABASE_URL="$OLD_DATABASE_URL" || unset DATABASE_URL || true
  [[ -n "$OLD_DEBUG" ]] && export DJANGO_DEBUG="$OLD_DEBUG" || unset DJANGO_DEBUG || true
  [[ -n "$OLD_SECRET" ]] && export DJANGO_SECRET_KEY="$OLD_SECRET" || unset DJANGO_SECRET_KEY || true
  [[ -n "$OLD_PASSWORD" ]] && export DJANGO_DEMO_PASSWORD="$OLD_PASSWORD" || unset DJANGO_DEMO_PASSWORD || true
  [[ -n "$OLD_HOSTS" ]] && export DJANGO_ALLOWED_HOSTS="$OLD_HOSTS" || unset DJANGO_ALLOWED_HOSTS || true
  [[ -n "$OLD_HSTS_SUBDOMAINS" ]] && export DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS="$OLD_HSTS_SUBDOMAINS" || unset DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS || true
  [[ -n "$OLD_HSTS_PRELOAD" ]] && export DJANGO_SECURE_HSTS_PRELOAD="$OLD_HSTS_PRELOAD" || unset DJANGO_SECURE_HSTS_PRELOAD || true
  [[ -n "$OLD_SMOKE_PORT" ]] && export SMOKE_PORT="$OLD_SMOKE_PORT" || unset SMOKE_PORT || true
}
trap cleanup EXIT

rm -f "$VERIFY_DB"
export DATABASE_URL="sqlite:///verification.sqlite3"
export DJANGO_DEBUG="True"
export DJANGO_DEMO_PASSWORD="Demo-Only-Verification-2026!"

echo "=== Taller #3: verificación integral SQLite limpia ==="
python --version
python -m pip check
python -c "import django, environ; print('Django', django.get_version()); print('django-environ', environ.__version__)"
python scripts/manifest_project.py
python scripts/audit_project.py
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
python manage.py showmigrations
python manage.py seed_baseline
python manage.py seed_baseline
python manage.py seed_demo
python manage.py seed_demo
python manage.py backfill_wallets
python manage.py backfill_wallets
python manage.py process_expired_requests
python manage.py process_expired_requests
python manage.py sync_lottery_event_states
python manage.py sync_lottery_event_states
python manage.py process_lottery_schedules
python manage.py process_lottery_schedules
echo "=== Pruebas funcionales demostrables posteriores a P-28 ==="
python manage.py test \
  apps.accounts.tests.test_auth \
  apps.accounts.tests.test_auth_and_modes \
  apps.accounts.tests.test_views \
  apps.finance.tests.test_operations \
  apps.finance.tests.test_vendor_finance \
  apps.finance.tests.test_views \
  apps.vendors.tests.test_views \
  apps.vendors.tests.test_client_requests \
  apps.vendors.tests.test_vendor_assignment \
  apps.vendors.tests.test_vendor_settlement \
  apps.vendors.tests.test_request_closure \
  apps.lottery.tests.test_crud \
  apps.lottery.tests.test_ticket_purchase \
  apps.lottery.tests.test_result_publication \
  apps.lottery.tests.test_event_series \
  apps.lottery.tests.test_automatic_results \
  apps.lottery.tests.test_permissions \
  apps.core.tests.test_ux_accessibility \
  --verbosity 2

echo "=== Smoke test y suite completa ==="
export SMOKE_PORT=8876
python scripts/smoke_runserver.py
python manage.py test --verbosity 2
python manage.py findstatic css/app.css js/app.js img/logo-placeholder.png
python manage.py collectstatic --noinput --clear

export DJANGO_DEBUG="False"
export DJANGO_SECRET_KEY="verification-only-long-secret-key-not-for-production-2026"
export DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost"
export DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS="True"
export DJANGO_SECURE_HSTS_PRELOAD="True"
python manage.py check --deploy

echo "=== Verificación integral completada correctamente ==="
