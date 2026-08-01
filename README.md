# Lotería Binaria — Taller #3 Django

Proyecto académico desarrollado con Django para el Taller #3. El estado de
esta entrega llega hasta **P-27**: tres CRUD evaluables implementados en
`accounts`, `vendors` y `lottery`, sobre SQLite para la primera fase y con
configuración portable a MySQL para la segunda.

## Autoridad y alcance

1. Enunciado del Taller #3.
2. Cinco documentos canónicos en `docs/referencias/`.
3. Guía docente VideoClub.
4. ZIP legado únicamente como referencia visual.

No se usa PostgreSQL. Tampoco se incluyen pagos reales, tarjetas, API REST,
Celery, Redis ni microservicios.

## Estado actual

- Usuario personalizado creado antes de las migraciones generales.
- Autenticación, registro, términos, roles y selección de modo.
- CRUD administrativo de usuarios.
- CRUD administrativo de perfiles vendedores y consulta read-only de
  solicitudes de conversión.
- CRUD administrativo de productos y eventos de lotería.
- `Ticket` y `DrawResult` protegidos como historia y sin CRUD genérico.
- Bootstrap 5.3 real con identidad azul profundo/dorada.
- 167 pruebas automatizadas diseñadas en el árbol actual.

`finance` permanece pendiente para **P-28**. La compra de boletos todavía no
forma parte de P-27 y no se expone en la interfaz.

## Requisitos

- Python 3.12 recomendado.
- SQLite incluido con Python.
- MySQL 8 para la segunda fase, solo después de cerrar SQLite.

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

También existe inicio guiado:

```powershell
.\scripts\run_local.ps1
```

## Datos demo opcionales

No existe una contraseña versionada. Define una clave local fuerte:

```env
DJANGO_DEMO_PASSWORD=su-clave-local-no-versionada
```

Después:

```powershell
python manage.py seed_demo
```

El comando solo se permite con `DEBUG=True` y no imprime credenciales.

## Rutas implementadas

| Ruta | Uso |
|---|---|
| `/` | landing pública |
| `/accounts/login/` | inicio de sesión |
| `/accounts/logout/` | cierre mediante POST |
| `/accounts/register/` | registro de cliente adulto |
| `/accounts/mode/` | selección de modo asignado |
| `/dashboard/client/` | panel CLIENTE |
| `/dashboard/vendor/` | panel VENDEDOR |
| `/dashboard/admin/` | panel ADMINISTRADOR |
| `/accounts/users/` | CRUD administrativo de usuarios |
| `/vendors/` | CRUD administrativo de perfiles vendedores |
| `/vendors/requests/` | solicitudes de conversión read-only |
| `/lottery/products/` | CRUD de productos de lotería |
| `/lottery/events/` | CRUD protegido de eventos |
| `/admin/` | administración Django para staff |

Las rutas de `vendors` y `lottery` exigen cuenta administrativa activa y modo
`ADMINISTRADOR`.

## Reglas Lottery cerradas hasta P-27

- OCTAL: `0-7`, cuatro símbolos únicos.
- DECIMAL: `0-9`, cinco símbolos únicos.
- HEXADECIMAL: `0-9/A-F`, seis símbolos únicos.
- Cierre de ventas: exactamente diez minutos antes de `draw_at`.
- Montos: `BigIntegerField` con sufijo `_minor`.
- `Ticket`: combinación única por evento y no eliminable.
- `DrawResult`: `OneToOne`, protegido e inmutable.
- Producto con eventos: no eliminable y configuración estructural protegida.
- Evento fuera de Borrador: producto, fechas, precio, premio y estado no se
  alteran mediante el CRUD normal.
- Evento: solo eliminable en Borrador, sin tickets y sin resultado.

## Verificación completa

```powershell
.\scripts\verify.ps1
```

El script crea una base SQLite temporal, ejecuta auditoría estática,
`check`, migraciones, seeds, smoke test, suite Django y verificación de
archivos estáticos. No modifica `db.sqlite3`.

Validación manual equivalente:

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

No cambies de motor mientras SQLite no esté completamente verde.

```powershell
pip install -r requirements-mysql.txt
```

Luego configura `DATABASE_URL` para MySQL, aplica las mismas migraciones y
repite toda la suite. No uses `migrate --fake` para ocultar errores.

## Auditoría y continuación

- Resultado de la revisión P-27:
  `docs/AUDITORIA_P27_2026-08-01.md`.
- Guía operativa para validar y continuar:
  `docs/GUIA_CONTINUACION_DESDE_P27.md`.
- Matriz vigente:
  `docs/MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md`.

El siguiente bloque del manual es **P-28: Finance y Core sin CRUD
destructivo**. No corresponde avanzar a P-29 ni a compra de boletos antes de
cerrar la puerta de salida de P-27.

## Respaldo visual

El frontend antiguo se conserva en `respaldo_frontend/`. No se carga en el
runtime Django y no se utiliza como fuente de usuarios, roles, saldos,
boletos, solicitudes o resultados.
