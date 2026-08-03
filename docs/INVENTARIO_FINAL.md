# Inventario técnico vigente

## 1. Raíz y configuración

| Ruta | Responsabilidad |
|---|---|
| `manage.py` | entrada estándar de Django; no contiene lógica de negocio |
| `config/settings.py` | configuración SQLite/MySQL, seguridad, templates y static |
| `config/urls.py` | montaje de Admin y namespaces de las cinco apps |
| `.env.example` | variables ficticias y documentadas, sin secretos |
| `requirements.txt` | dependencias base de la fase SQLite |
| `requirements-mysql.txt` | driver requerido únicamente para MySQL |
| `MANIFEST_SHA256.txt` | integridad de los archivos entregables |

## 2. Apps

### `apps/accounts/`

Usuario personalizado, términos/privacidad, autenticación, modo activo, perfil y CRUD administrativo de usuarios.

### `apps/core/`

Landing, redirección inicial, dashboards, auditoría, utilidades de fechas, contexto global y seeds.

### `apps/finance/`

Wallets REAL/VIRTUAL, movimientos y operaciones simuladas: recarga, retiro, conversión, transferencia e inventario vendedor.

### `apps/vendors/`

Perfil vendedor, solicitudes Cliente–Vendedor, asignaciones, liberación, liquidación, cancelación y expiración.

### `apps/lottery/`

Productos, eventos, transiciones, boletos, resultados, premios, series y automatización.

## 3. Migraciones reales

| App | Última migración |
|---|---|
| accounts | `0002_alter_termsacceptance_id_alter_termsversion_id.py` |
| core | `0001_initial.py` |
| finance | `0004_vendorinventorypurchase.py` |
| vendors | `0001_initial.py` |
| lottery | `0011_portable_series_sequence_unique.py` |

Migraciones destacadas de lottery:

- `0007_event_series.py`: series y relación con eventos;
- `0008_series_limits_and_archive.py`: límites, pausa/archivo lógico;
- `0009_automatic_results.py`: modo de resultado automático;
- `0010_draweventseries_last_synced_at.py`: última sincronización;
- `0011_portable_series_sequence_unique.py`: unicidad portable de secuencia.

## 4. Comandos de management

| Comando | Responsabilidad |
|---|---|
| `seed_baseline` | Groups canónicos y versiones legales |
| `seed_demo` | usuarios/datos académicos reproducibles |
| `backfill_wallets` | completa wallets faltantes sin duplicar |
| `process_expired_requests` | resuelve solicitudes vencidas |
| `sync_lottery_event_states` | aplica transiciones temporales de eventos |
| `process_lottery_schedules` | genera series y resultados automáticos |

## 5. Templates y static

- `templates/base.html`: Bootstrap 5.3, navegación, offcanvas, mensajes, modal y skip link.
- `templates/accounts/`: autenticación, perfil, modo y usuarios.
- `templates/dashboards/`: Cliente, Vendedor y Administrador.
- `templates/finance/`: pantallas financieras unificadas.
- `templates/vendors/`: perfiles y solicitudes.
- `templates/lottery/`: productos, eventos, compra, boletos, resultados y series.
- `templates/403.html`, `404.html`: recuperación accesible.
- `static/css/app.css`: identidad azul/dorada, responsive y foco.
- `static/js/app.js`: interacción progresiva; nunca decide permisos, saldos o estados.

## 6. Pruebas

Hay **458 pruebas ejecutadas correctamente** en la última verificación documental. Se distribuyen en:

- `apps/accounts/tests/`
- `apps/core/tests/`
- `apps/finance/tests/`
- `apps/vendors/tests/`
- `apps/lottery/tests/`

La cifra no se mantiene manualmente como constante: debe actualizarse solo después de otra ejecución completa.

## 7. Scripts

| Script | Uso |
|---|---|
| `audit_project.py` | estructura, residuos, documentación vigente y controles estáticos |
| `manifest_project.py` | genera/verifica SHA-256 |
| `verify.ps1`, `verify.sh` | puerta integral SQLite |
| `verify_mysql.ps1`, `verify_mysql.sh` | puerta dedicada MySQL |
| `smoke_runserver.py` | arranque HTTP local reproducible |
| `run_local.ps1`, `run_local.sh` | ayuda operativa local |

## 8. Documentación y referencias

- `docs/INDICE_DOCUMENTACION.md`: autoridad y clasificación.
- `docs/referencias/`: originales preservados.
- `docs/historico/`: documentación explícitamente histórica.
- documentos de implementación P-33/P-34/P-36: evidencia de su fase, no estado global.

## 9. Exclusiones del ZIP final

- `.venv/`, `venv/`, `env/`;
- `.env`;
- `db.sqlite3`, `*.sqlite3`, `*.db`;
- `__pycache__/`, `*.pyc`, `*.pyo`;
- `staticfiles/`;
- logs y copias temporales.
