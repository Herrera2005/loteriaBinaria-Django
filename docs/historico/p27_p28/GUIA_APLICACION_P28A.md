# Guía de aplicación y comprobación P-28A

## 1. Rama correcta

```powershell
git branch --show-current
git status
```

La rama esperada es:

```text
feature/taller3-p28-finance-core
```

El árbol debe estar limpio antes de copiar el paquete.

## 2. Archivos que se aplican

```text
apps/finance/models.py
apps/finance/admin.py
apps/finance/apps.py
apps/finance/services.py
apps/finance/signals.py
apps/finance/migrations/0001_initial.py
apps/finance/management/__init__.py
apps/finance/management/commands/__init__.py
apps/finance/management/commands/backfill_wallets.py
apps/finance/tests/__init__.py
apps/finance/tests/test_models.py

apps/core/models.py
apps/core/admin.py
apps/core/migrations/0001_initial.py
apps/core/tests/test_models.py

scripts/audit_project.py
README.md
docs/DECISION_P28A_MODELOS_FINANCE_AUDITORIA.md
docs/GUIA_APLICACION_P28A.md
docs/MATRIZ_PRUEBAS_P28A.md
docs/RESULTADO_IMPLEMENTACION_P28A.md
docs/PLAN_SIGUIENTE_TRABAJO.md
```

No se modifican vistas, URLs ni templates en P-28A.

## 3. Revisión previa

```powershell
python -m py_compile `
    .\apps\finance\models.py `
    .\apps\finance\services.py `
    .\apps\finance\signals.py `
    .\apps\finance\admin.py `
    .\apps\core\models.py `
    .\apps\core\admin.py

python manage.py check
```

## 4. Verificar migraciones

Los archivos `0001_initial.py` están incluidos para revisión y deben coincidir con los modelos.

```powershell
python manage.py makemigrations --check --dry-run
python manage.py showmigrations finance core
python manage.py sqlmigrate finance 0001
python manage.py sqlmigrate core 0001
```

Esperado antes de aplicar:

```text
[ ] 0001_initial
```

No debe aparecer SQL exclusivo de PostgreSQL.

## 5. Aplicar en SQLite

```powershell
python manage.py migrate
```

Esperado:

```text
Applying finance.0001_initial... OK
Applying core.0001_initial... OK
```

## 6. Backfill idempotente

```powershell
python manage.py backfill_wallets
python manage.py backfill_wallets
```

La segunda ejecución debe crear cero wallets nuevas.

Verificación:

```powershell
python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.finance.models import Wallet

User = get_user_model()
print('USERS:', User.objects.count())
print('WALLETS:', Wallet.objects.count())
for user in User.objects.order_by('pk'):
    print(user.username, list(user.wallets.values_list('currency', flat=True)))
"
```

Cada usuario existente debe mostrar REAL y VIRTUAL.

## 7. Pruebas específicas

```powershell
python manage.py test apps.finance.tests.test_models -v 2
python manage.py test apps.core.tests.test_models -v 2
```

Después:

```powershell
python manage.py test apps.finance apps.core -v 2
```

## 8. Regresión completa

```powershell
python manage.py test -v 2
python manage.py check
python manage.py makemigrations --check --dry-run
```

El inventario esperado del paquete es de 195 pruebas diseñadas.

## 9. Auditoría estática

```powershell
python scripts/audit_project.py
```

Debe terminar en:

```text
AUDITORÍA ESTÁTICA P-28A: OK
```

Luego:

```powershell
.\scripts\verify.ps1
```

## 10. Prueba del admin read-only

Con un superusuario abre:

```text
/admin/finance/wallet/
/admin/finance/movement/
/admin/core/auditevent/
```

Comprueba:

- se pueden consultar listas y detalles;
- no existe botón Añadir;
- no existe formulario editable;
- no existe eliminación;
- los saldos no se modifican desde el admin.

## 11. Cierre en Git

```powershell
git status --short
git diff --stat
git add apps/finance apps/core scripts/audit_project.py README.md docs
git status
git commit -m "Implementa preparación P-28A Finance y auditoría"
git push origin feature/taller3-p28-finance-core
```

No agregar `.env`, `db.sqlite3`, `.venv`, `__pycache__`, `*.pyc` ni `staticfiles`.

## 12. Siguiente paso

Solo cuando toda la puerta esté verde se inicia el P-28 oficial:

- wallet propia read-only;
- movimientos propios paginados;
- auditoría administrativa list/detail;
- dashboards con datos reales;
- pruebas de propiedad y permisos;
- Bootstrap 5.3;
- sin recargas ni conversiones todavía.
