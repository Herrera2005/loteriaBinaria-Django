# Taller #3 — Lotería Binaria con Django

Aplicación académica monolítica desarrollada con Django 5.2, templates del servidor y Bootstrap 5.3. El proyecto se organiza en cinco apps: `accounts`, `core`, `finance`, `vendors` y `lottery`.

## Estado ejecutable vigente

El árbol actual corresponde al cierre **P-36E**, más las reparaciones de auditoría integral y de UX/accesibilidad. Están implementados y cubiertos por pruebas:

- usuario personalizado, registro adulto, términos versionados, login, logout y cambio de contraseña;
- roles `CLIENTE`, `VENDEDOR` y `ADMINISTRADOR`, con un único modo activo por sesión;
- CRUD visuales de usuarios, perfiles vendedores, productos y eventos;
- wallets REAL/VIRTUAL y movimientos históricos;
- recargas simuladas, retiros, conversión VIRTUAL→REAL, transferencias y compra mayorista de inventario;
- solicitudes Cliente–Vendedor: creación, reserva, asignación, liberación, confirmación, cancelación y expiración;
- catálogo de sorteos, compra directa de boletos, unicidad de combinación, cancelación y reembolso;
- publicación manual o automática de resultados, evaluación y acreditación idempotente de premios;
- series de eventos manuales/automáticas, limitadas o sin límite, con pausa, reactivación, archivo lógico y observabilidad;
- historial e inmutabilidad de movimientos, auditoría, boletos, resultados y transiciones;
- interfaz responsive y accesible para 320, 375, 768, 1024 y 1440 px.

La ejecución real más reciente encontró y aprobó **458 pruebas**:

```text
Ran 458 tests
OK
```

La cifra proviene de una ejecución completa con Django 5.2.16 y un hasher rápido externo usado únicamente para acelerar la auditoría. El código productivo y sus settings no fueron modificados para obtenerla.

## Bases de datos

- **Fase 1:** SQLite para desarrollo, migraciones, pruebas y entrega inicial.
- **Fase 2:** MySQL con `utf8mb4` y modo estricto.
- **PostgreSQL no forma parte de este taller.** Las referencias originales que lo mencionan se conservan en `docs/referencias/` como documentación de origen, pero son sustituidas operativamente por `docs/DECISION_T3_001_SQLITE_MYSQL.md`.

La migración más reciente es:

```text
lottery.0011_portable_series_sequence_unique
```

No se editan migraciones ya aplicadas; cualquier cambio de esquema requiere una migración nueva.

## Instalación en PowerShell

```powershell
cd D:\github\loteriaBinaria-Django
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py seed_baseline
$env:DJANGO_DEMO_PASSWORD = "UnaClaveLocalSegura"
python manage.py seed_demo
python manage.py runserver
```

No se deben incluir en el ZIP de entrega: `.venv`, `.env`, bases locales, `staticfiles`, logs, `__pycache__`, `.pyc` o `.pyo`.

## Rutas principales

| Área | Ruta base | Nombres URL principales |
|---|---|---|
| Público | `/` | `core:home`, `core:start` |
| Cuentas | `/accounts/` | `login`, `logout`, `register`, `choose_mode`, `profile`, CRUD de usuarios |
| Dashboards | `/dashboard/` | `core:client_dashboard`, `core:vendor_dashboard`, `core:admin_dashboard` |
| Finanzas | `/finance/` | wallets, movimientos, operaciones REAL, conversión, transferencia e inventario |
| Vendedores | `/vendors/` | CRUD de perfiles y solicitudes propias/globales |
| Lotería | `/lottery/` | productos, eventos, boletos, resultados y series |
| Auditoría | `/audit/` | `core:audit_list`, `core:audit_detail` |
| Admin técnico | `/admin/` | Django Admin para usuarios `is_staff` |

La visibilidad de enlaces no concede permisos: cada vista vuelve a validar autenticación, cuenta activa, rol, modo y recurso.

## Comandos de operación

```powershell
python manage.py seed_baseline
python manage.py seed_demo
python manage.py backfill_wallets
python manage.py process_expired_requests
python manage.py sync_lottery_event_states
python manage.py process_lottery_schedules
```

- `seed_baseline`, `seed_demo` y `backfill_wallets` son repetibles sin duplicar datos esperados.
- `process_expired_requests` resuelve solicitudes vencidas sin Celery.
- `sync_lottery_event_states` actualiza estados temporales; las páginas GET no escriben estados.
- `process_lottery_schedules` genera eventos de series y procesa resultados automáticos. Cada serie se procesa de forma aislada para que una serie inválida no revierta las válidas.

## Series y resultados automáticos

`DrawEventSeries` permite:

- frecuencia y próxima fecha (`next_draw_at`);
- generación limitada (`remaining_occurrences`) o sin límite;
- modo de resultado manual o automático (`result_mode`);
- pausa/reactivación sin modificar eventos ya creados;
- archivo lógico con conservación del historial;
- `last_synced_at` como observabilidad del último intento real de procesamiento;
- relación con eventos generados y secuencia única portable `(series, series_sequence)`.

Editar una serie afecta únicamente generaciones futuras. Los eventos ya generados conservan producto, fechas, precio, premio y anticipación originales.

Los resultados son únicos por evento e inmutables. La liquidación y la acreditación de premios son idempotentes y se realizan mediante servicios transaccionales.

## Verificación integral

### SQLite

```powershell
.\scripts\verify.ps1
```

Equivalente Bash:

```bash
./scripts/verify.sh
```

La puerta incluye inventario del entorno, manifiesto, auditoría estática, `check`, migraciones, seeds/comandos repetidos, una batería funcional explícita posterior a P-28, smoke test, suite completa, static y `check --deploy` con variables seguras temporales.

El cierre demostrable de esta fase se documenta en:

- `docs/REPORTE_FINAL_SQLITE.md`;
- `docs/CIERRE_SQLITE_EVIDENCIA_REQUISITO.md`;
- `docs/CIERRE_SQLITE_CHECKLIST_CAPTURAS.md`;
- `docs/CIERRE_SQLITE_COMANDOS_EVIDENCIA.md`;
- `docs/DEMOSTRACION_SQLITE_10_15_MIN.md`.

### MySQL

```powershell
python -m pip install -r requirements-mysql.txt
$env:DATABASE_URL = "mysql://usuario:clave@127.0.0.1:3306/loteria_taller3_test"
.\scripts\verify_mysql.ps1
```

MySQL no se considera aprobado hasta ejecutar esa puerta sobre un servidor MySQL real y repetir las pruebas críticas de concurrencia.

## Documentación

El índice y la autoridad documental están en:

- `docs/INDICE_DOCUMENTACION.md`
- `docs/MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md`
- `docs/INVENTARIO_FINAL.md`
- `docs/ARCHIVOS_Y_RESPONSABILIDADES.md`

Los documentos de fases intermedias se conservan por trazabilidad, pero no sustituyen al estado vigente.
