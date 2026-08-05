# Guía de aplicación P-28 oficial

## 1. Respaldo

```powershell
git branch --show-current
git status --short
git add .
git commit -m "Cierra P-28A antes de vistas read-only"
```

La rama esperada es:

```text
feature/taller3-p28-finance-core
```

## 2. Aplicar archivos

Copiar el paquete incremental sobre la raíz del proyecto y aceptar reemplazo
solo para los archivos incluidos.

No copiar `.env`, `db.sqlite3`, `.venv`, `__pycache__` ni `staticfiles`.

## 3. Verificación de sintaxis

```powershell
python -m py_compile `
    .\apps\finance\views.py `
    .\apps\finance\urls.py `
    .\apps\core\views.py `
    .\apps\core\urls.py `
    .\apps\finance\tests\test_views.py `
    .\apps\core\tests\test_views.py
```

## 4. Comprobaciones Django

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
```

Esperado:

```text
System check identified no issues (0 silenced).
No changes detected
```

P-28 no cambia modelos ni crea migraciones.

## 5. Pruebas por módulo

```powershell
python manage.py test apps.finance -v 2
python manage.py test apps.core -v 2
```

Después:

```powershell
python manage.py test -v 2
```

El paquete incorpora `apps/finance/tests/__init__.py`, por lo que las pruebas de
Finance que antes no se descubrían deben aparecer ahora en la salida.

## 6. Auditoría reproducible

```powershell
python scripts/audit_project.py
.\scripts\verify.ps1
```

Esperado:

```text
AUDITORÍA ESTÁTICA P-28: OK
=== Verificación completada correctamente ===
```

## 7. Prueba manual

```powershell
python manage.py runserver
```

Revisar:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/finance/wallets/
http://127.0.0.1:8000/finance/movements/
http://127.0.0.1:8000/audit/
```

Casos:

1. CLIENTE: wallet/movimientos 200; auditoría 403.
2. VENDEDOR: wallet/movimientos 200; auditoría 403.
3. ADMINISTRADOR en modo ADMINISTRADOR: auditoría 200.
4. ADMINISTRADOR en otro modo: auditoría 403.
5. Cambiar `?user=<pk-ajeno>`: no cambia los datos mostrados.
6. Enviar POST a list/detail: 405.
7. Probar 360, 390, 768, 1024 y 1440 px.

## 8. Cierre

```powershell
git status --short
git add .
git commit -m "Implementa P-28 consultas read-only de Finance y Core"
git push origin feature/taller3-p28-finance-core
```

No avanzar a operaciones financieras. El siguiente bloque es P-29.
