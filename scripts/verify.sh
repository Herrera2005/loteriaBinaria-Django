#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
VERIFY_DB="$ROOT/verification.sqlite3"
OLD_DATABASE_URL="${DATABASE_URL-}"
OLD_DEBUG="${DJANGO_DEBUG-}"

cleanup() {
  rm -f "$VERIFY_DB"
  rm -rf "$ROOT/staticfiles"
  if [[ -n "$OLD_DATABASE_URL" ]]; then
    export DATABASE_URL="$OLD_DATABASE_URL"
  else
    unset DATABASE_URL || true
  fi
  if [[ -n "$OLD_DEBUG" ]]; then
    export DJANGO_DEBUG="$OLD_DEBUG"
  else
    unset DJANGO_DEBUG || true
  fi
}
trap cleanup EXIT

rm -f "$VERIFY_DB"
export DATABASE_URL="sqlite:///verification.sqlite3"
export DJANGO_DEBUG="True"

echo "=== Taller #3: verificación completa SQLite limpia ==="
python scripts/audit_project.py
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
python manage.py showmigrations
python manage.py seed_baseline
python scripts/smoke_runserver.py
python manage.py test --verbosity 2
python manage.py findstatic css/app.css js/app.js img/logo-placeholder.png
python manage.py collectstatic --noinput --clear
echo "=== Verificación completada correctamente ==="
