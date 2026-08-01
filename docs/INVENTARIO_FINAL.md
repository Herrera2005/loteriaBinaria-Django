# Inventario vigente del proyecto hasta P-27

Este inventario reemplaza el inventario temprano que describía Vendors y
Lottery como apps vacías.

## Raíz y configuración

| Ruta | Responsabilidad |
|---|---|
| `.env.example` | SQLite por defecto y variables futuras de MySQL, sin secretos |
| `.gitignore` | excluye entorno, secretos, bases locales, bytecode y collectstatic |
| `requirements.txt` | dependencias de fase SQLite |
| `requirements-mysql.txt` | driver exclusivo de la segunda fase |
| `config/settings.py` | apps, templates, static, seguridad y allowlist SQLite/MySQL |
| `config/urls.py` | integra admin, accounts, core, vendors y lottery |
| `scripts/audit_project.py` | auditoría estática hasta P-27 |
| `scripts/verify.ps1` | SQLite limpia, suite, smoke y static |

## Apps

| App | Estado hasta P-27 |
|---|---|
| `accounts` | usuario personalizado, términos, autenticación, modos y CRUD administrativo |
| `core` | landing, dashboards, contexto de navegación y seeds |
| `vendors` | modelos, migración, admin, forms, servicio, CRUD de perfiles y solicitudes read-only |
| `lottery` | productos/eventos, tickets/resultados protegidos, migración, admin, forms, servicios y CRUD P-27 |
| `finance` | frontera creada; funcionalidad read-only pendiente para P-28 |

## Templates activos

- base común Bootstrap 5.3;
- Accounts: lista, detalle, crear, editar y confirmación;
- Vendors: lista, detalle, form, confirmación y solicitudes read-only;
- Lottery: `product_*` y `event_*` completos;
- dashboards de Cliente, Vendedor y Administrador;
- páginas 403/404 y partials de mensajes/modal.

Todas las páginas hoja extienden `base.html`, cargan static y contienen un solo
`h1`.

## Pruebas

Se inventarían **167 pruebas diseñadas**:

- Accounts: modelos, forms, registro, autenticación, modos, admin y CRUD;
- Core: configuración, seeds, landing y dashboards;
- Vendors: modelos, permisos, CRUD y solicitudes read-only;
- Lottery: modelos, forms, permisos, CRUD, filtros, paginación, CSRF,
  inmutabilidad y eliminaciones protegidas.

La cifra describe el inventario estático. La evidencia dinámica definitiva se
genera con `scripts/verify.ps1`.

## Fuera del runtime

- frontend antiguo en `respaldo_frontend/`;
- no hay `index.html`/`pages/` activos;
- no hay JSON/localStorage/fetch de negocio;
- no hay `.env`, SQLite local, `.venv`, `staticfiles`, `__pycache__` ni `.pyc`
  en el paquete de entrega.

## Siguiente archivo de autoridad operativa

Consulta:

- `docs/AUDITORIA_P27_2026-08-01.md`;
- `docs/GUIA_CONTINUACION_DESDE_P27.md`;
- `docs/MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md`.
