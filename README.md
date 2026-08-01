# Lotería Binaria — Taller #3 Django

Proyecto académico con Django. Esta versión consolida la fase SQLite, el
usuario personalizado, términos, autenticación, selección de modo y la base
Bootstrap 5.3.

## Autoridad y alcance

1. Enunciado del Taller #3.
2. Cinco documentos canónicos en `docs/referencias/`.
3. Guía docente VideoClub.
4. ZIP legado solo como referencia visual.

Decisión específica: SQLite en fase 1 y MySQL en fase 2. Consulte
`docs/DECISION_T3_001_SQLITE_MYSQL.md`.

## Requisitos

- Python 3.12 recomendado.
- SQLite incluido con Python.
- MySQL 8 únicamente para la segunda fase.

## Instalación SQLite

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py seed_baseline
python manage.py createsuperuser
python manage.py runserver
```

También puede usar el inicio guiado:

```powershell
.\scripts\run_local.ps1
```

## Datos demo opcionales

No existe contraseña hardcodeada. Defina una contraseña local fuerte:

```env
DJANGO_DEMO_PASSWORD=su-clave-local-no-versionada
```

y ejecute:

```powershell
python manage.py seed_demo
```

El comando solo funciona con `DEBUG=True` y no imprime credenciales.

## Rutas verificables

| Ruta | Uso |
|---|---|
| `/` | landing pública |
| `/accounts/login/` | inicio de sesión |
| `/accounts/logout/` | cierre mediante POST |
| `/accounts/register/` | registro de cliente adulto |
| `/accounts/mode/` | selector de roles asignados |
| `/dashboard/client/` | panel aislado CLIENTE |
| `/dashboard/vendor/` | panel aislado VENDEDOR |
| `/dashboard/admin/` | panel aislado ADMINISTRADOR |
| `/admin/` | administración Django para staff |

## Verificación

```powershell
.\scripts\verify.ps1
```

o manualmente:

```powershell
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
```

## MySQL — segunda fase

No cambiar todavía si SQLite no está completamente verde.

```powershell
pip install -r requirements-mysql.txt
```

Después se cambia `DATABASE_URL`, se ejecutan las mismas migraciones y se
comparan conteos; nunca se usa `migrate --fake` para ocultar errores.

## Módulos pendientes

`finance`, `vendors` y `lottery` están creados como límites arquitectónicos,
pero sus modelos y flujos de negocio no se implementan en este bloque. Los
dashboards muestran estados vacíos reales y no simulan persistencia.

## Respaldo visual

El ZIP original se conserva en `respaldo_frontend/`. No se carga desde Django
ni desde el navegador y no debe eliminarse.

## Estado de verificación del paquete

La auditoría estática, la compilación de Python y la sintaxis JavaScript fueron
ejecutadas al generar el paquete. La puerta definitiva es `scripts/verify.ps1`,
que crea una base SQLite temporal, aplica todas las migraciones, ejecuta las 48 pruebas de la
suite, inicia temporalmente `runserver`, comprueba la landing y elimina la evidencia temporal sin tocar `db.sqlite3`.


## Continuidad según el Manual Intercalado v4.0

La correspondencia de fases, dependencias y orden de crecimiento está en
`docs/ESCALABILIDAD_MANUAL_V4.md`. La prueba reproducible de la página está en
`docs/VERIFICACION_RUNSERVER.md`.
