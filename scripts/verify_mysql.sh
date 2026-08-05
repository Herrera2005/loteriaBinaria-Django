#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "${DATABASE_URL-}" != mysql://* && "${DATABASE_URL-}" != mysql2://* ]]; then
  echo "DATABASE_URL debe apuntar a una base MySQL de prueba vacía." >&2
  exit 2
fi

export DJANGO_DEBUG="True"
export DJANGO_DEMO_PASSWORD="${DJANGO_DEMO_PASSWORD:-Demo-Only-MySQL-Verification-2026!}"

python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
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
python manage.py test --verbosity 2
