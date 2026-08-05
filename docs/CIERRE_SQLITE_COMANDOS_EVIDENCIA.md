# Comandos exactos para producir evidencia SQLite

Ejecutar desde PowerShell en la raíz del repositorio.

## 1. Preparación y entorno

```powershell
cd D:\github\loteriaBinaria-Django
.\.venv\Scripts\Activate.ps1
New-Item -ItemType Directory -Force .\evidencias\04_cierre_sqlite | Out-Null
python --version
python -m pip check
python -c "import django, environ; print('Django', django.get_version()); print('django-environ', environ.__version__)"
```

## 2. Puerta automatizada completa

La puerta usa `verification.sqlite3`, no la base de trabajo, y la elimina al terminar.

```powershell
.\scripts\verify.ps1 2>&1 | Tee-Object .\evidencias\04_cierre_sqlite\verify_sqlite_completo.txt
```

## 3. Ejecución desglosada para capturas

```powershell
$env:DATABASE_URL = "sqlite:///evidencia_sqlite.sqlite3"
$env:DJANGO_DEBUG = "True"
$env:DJANGO_DEMO_PASSWORD = "Demo-Only-Evidence-2026!"
Remove-Item .\evidencia_sqlite.sqlite3 -Force -ErrorAction SilentlyContinue

python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
python manage.py showmigrations
```

## 4. Seeds e idempotencia

```powershell
python manage.py seed_baseline
python manage.py seed_baseline
python manage.py seed_demo
python manage.py seed_demo
python manage.py backfill_wallets
python manage.py backfill_wallets
```

Inventario de demo sin mostrar contraseñas:

```powershell
python manage.py shell -c "from django.contrib.auth import get_user_model; from django.contrib.auth.models import Group; from apps.finance.models import Wallet; from apps.lottery.models import LotteryProduct; print('usuarios=', get_user_model().objects.count()); print('roles=', Group.objects.count()); print('wallets=', Wallet.objects.count()); print('productos=', LotteryProduct.objects.count())"
```

## 5. Comandos temporales repetibles

```powershell
python manage.py process_expired_requests
python manage.py process_expired_requests
python manage.py sync_lottery_event_states
python manage.py sync_lottery_event_states
python manage.py process_lottery_schedules
python manage.py process_lottery_schedules
```

## 6. Smoke y servidor para demostración manual

```powershell
$env:SMOKE_PORT = "8876"
python scripts\smoke_runserver.py
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/`.

## 7. Pruebas funcionales demostrables

```powershell
python manage.py test `
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
  -v 2
```

## 8. Suite completa

```powershell
python manage.py test -v 2 2>&1 | Tee-Object .\evidencias\04_cierre_sqlite\suite_completa.txt
```

## 9. Static

```powershell
python manage.py findstatic css/app.css js/app.js img/logo-placeholder.png
python manage.py collectstatic --noinput --clear
```

## 10. Auditoría y manifiesto

Después de cerrar cualquier cambio documental:

```powershell
python scripts\manifest_project.py --write
python scripts\manifest_project.py
python scripts\audit_project.py
```

## 11. Responsive

Con el servidor activo, abrir DevTools y probar 320, 375, 768, 1024 y 1440 px. En consola del navegador:

```javascript
document.documentElement.scrollWidth === document.documentElement.clientWidth
```

Debe devolver `true`, salvo que el desplazamiento sea interno al contenedor de una tabla.

## 12. Limpieza local posterior

```powershell
Remove-Item .\evidencia_sqlite.sqlite3 -Force -ErrorAction SilentlyContinue
Remove-Item .\staticfiles -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:DJANGO_DEMO_PASSWORD -ErrorAction SilentlyContinue
```
