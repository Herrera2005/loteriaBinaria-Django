#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "=== Lotería Binaria - inicio local SQLite ==="
python manage.py check
python manage.py migrate --noinput
python manage.py seed_baseline
echo "Abre http://127.0.0.1:8000/"
echo "Detén el servidor con Ctrl+C."
python manage.py runserver
