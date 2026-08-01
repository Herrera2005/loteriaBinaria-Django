# Inventario vigente del proyecto hasta preparación P-28A

Este inventario conserva P-27 y agrega los modelos base de Finance/Core sin introducir vistas ni operaciones financieras fuera del alcance.

## Raíz y configuración

| Ruta | Responsabilidad |
|---|---|
| `.env.example` | SQLite por defecto y variables futuras de MySQL, sin secretos |
| `.gitignore` | excluye entorno, secretos, bases locales, bytecode y collectstatic |
| `requirements.txt` | dependencias de fase SQLite |
| `requirements-mysql.txt` | driver exclusivo de la segunda fase |
| `config/settings.py` | apps, templates, static, seguridad y allowlist SQLite/MySQL |
| `config/urls.py` | integra admin, accounts, core, vendors y lottery |
| `scripts/audit_project.py` | auditoría estática hasta P-28A |
| `scripts/verify.ps1` | SQLite limpia, suite, smoke y static |

## Apps

| App | Estado vigente |
|---|---|
| `accounts` | usuario personalizado, términos, autenticación, modos y CRUD administrativo |
| `core` | landing, dashboards, navegación, seeds y `AuditEvent` append-only |
| `vendors` | modelos, migración, admin, forms, servicio, CRUD de perfiles y solicitudes read-only |
| `lottery` | productos/eventos, tickets/resultados protegidos, migración, admin, forms, servicios y CRUD P-27 |
| `finance` | `Wallet`, `Movement`, admin read-only, provisión, señal, backfill, migración y tests P-28A |

## Finance/Core agregados en P-28A

```text
apps/finance/models.py
apps/finance/admin.py
apps/finance/apps.py
apps/finance/services.py
apps/finance/signals.py
apps/finance/migrations/0001_initial.py
apps/finance/management/commands/backfill_wallets.py
apps/finance/tests/test_models.py

apps/core/models.py
apps/core/admin.py
apps/core/migrations/0001_initial.py
apps/core/tests/test_models.py
```

## Templates activos

Se conservan los templates de P-27. P-28A no agrega templates.

- base común Bootstrap 5.3;
- Accounts: lista, detalle, crear, editar y confirmación;
- Vendors: lista, detalle, form, confirmación y solicitudes read-only;
- Lottery: `product_*` y `event_*` completos;
- dashboards de Cliente, Vendedor y Administrador;
- páginas 403/404 y partials de mensajes/modal.

## Pruebas

El árbol contiene **195 pruebas diseñadas**:

- Accounts: 55;
- Core: 29, incluidas 8 de AuditEvent;
- Finance: 20;
- Vendors: 37;
- Lottery: 54.

La ejecución definitiva de P-28A debe realizarse con Django 5.2.16 mediante `scripts/verify.ps1`.

## Fuera del runtime

- frontend antiguo en `respaldo_frontend/`;
- no hay `index.html`/`pages/` activos;
- no hay JSON/localStorage/fetch de negocio;
- no se entregan `.env`, SQLite local, `.venv`, `staticfiles`, `__pycache__` ni `.pyc`.

## Documentos operativos

- `docs/DECISION_P28A_MODELOS_FINANCE_AUDITORIA.md`;
- `docs/GUIA_APLICACION_P28A.md`;
- `docs/MATRIZ_PRUEBAS_P28A.md`;
- `docs/RESULTADO_IMPLEMENTACION_P28A.md`;
- `docs/MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md`.
