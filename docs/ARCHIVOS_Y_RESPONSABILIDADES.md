# Archivos y responsabilidades actuales

## Configuración

- `config/settings.py`: motores SQLite/MySQL, seguridad, sesiones, templates, static y variables de entorno.
- `config/urls.py`: `/admin/` y namespaces `accounts`, `core`, `finance`, `vendors`, `lottery`.
- `requirements.txt`: entorno base del taller.
- `requirements-mysql.txt`: soporte adicional de MySQL.

## Accounts

- `models.py`: `User`, `TermsVersion`, `TermsAcceptance` y QuerySets históricos.
- `forms.py`: login/registro, perfil y formularios administrativos protegidos.
- `services.py`: registro atómico y eliminación/desactivación controlada.
- `access.py`, `policies.py`, `mixins.py`, `decorators.py`: autorización por cuenta, Group y modo activo.
- `views.py`, `urls.py`: autenticación, perfil, selector de modo y CRUD de usuarios.
- `admin.py`: administración técnica sin debilitar historia.

## Core

- `models.py`: `AuditEvent` append-only.
- `views.py`, `urls.py`: home, dashboards y auditoría.
- `context_processors.py`: navegación derivada del backend.
- `date_utils.py`: límites diarios locales portables.
- `seed.py` y comandos `seed_baseline`/`seed_demo`: datos reproducibles.

## Finance

- `models.py`: wallets, movimientos y operaciones financieras simuladas.
- `services.py`: todas las mutaciones de saldo bajo transacción/locks.
- `forms.py`: entrada y presentación; no reemplaza validación del servicio.
- `views.py`, `urls.py`: consultas y operaciones por modo.
- `signals.py`: provisión controlada relacionada con roles/usuarios.
- `backfill_wallets.py`: reparación idempotente de wallets faltantes.

## Vendors

- `models.py`: `VendorProfile`, `ConversionRequest`, `ConversionAssignment` e historia protegida.
- `services.py`: creación, asignación, confirmación, liberación, cancelación y expiración.
- `views.py`, `urls.py`: CRUD administrador, cola vendedor y solicitudes propias cliente.
- `process_expired_requests.py`: tarea temporal programable.

## Lottery

- `models.py`: `LotteryProduct`, `DrawEventSeries`, `DrawEvent`, `DrawEventStatusTransition`, `Ticket`, `DrawResult`.
- `services.py`: compra, transiciones, reembolsos, resultados, series y automatización.
- `availability.py`: disponibilidad/canonicalización de combinaciones.
- `forms.py`: CRUD, compra, resultados y series.
- `views.py`, `urls.py`: panel administrador, catálogo Cliente, boletos, resultados públicos y series.
- `process_lottery_schedules.py`, `sync_lottery_event_states.py`: tareas programables sin Celery.

## Interfaz

- `templates/base.html`: Bootstrap 5.3, navegación por modo, mensajes, offcanvas y modal.
- `templates/includes/`: componentes comunes accesibles.
- `static/css/app.css`: identidad y responsive.
- `static/js/app.js`: mejoras progresivas de UI, sin autoridad de negocio.

## Pruebas y verificación

- `apps/*/tests/`: 458 pruebas ejecutadas en el estado documentado.
- `scripts/audit_project.py`: auditoría estática de cierre.
- `scripts/manifest_project.py`: integridad SHA-256.
- `scripts/verify.*`: puerta completa SQLite.
- `scripts/verify_mysql.*`: puerta MySQL.
- `docs/PRUEBAS_RESPONSIVE.md`: matriz de UX/accesibilidad.
