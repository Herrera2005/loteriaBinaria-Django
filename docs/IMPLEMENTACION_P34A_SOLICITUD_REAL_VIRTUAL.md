# P-34A — Solicitud REAL → VIRTUAL

Este bloque permite que un Cliente cree una solicitud desde la pestaña REAL → VIRTUAL. El monto pasa de disponible a reservado en la wallet REAL. No se acredita VIRTUAL todavía.

## Alcance

- Formulario sin float y con operation_id.
- Servicio atómico e idempotente.
- Movimiento histórico de reserva.
- Listado y detalle exclusivos del Cliente propietario.
- Integración con la pantalla Conversión de wallets.
- Sin compra mayorista, asignación ni finalización por vendedor.
- Sin cambios de modelos ni migraciones.

## Puerta de salida

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test apps.vendors apps.finance -v 2`
- `python manage.py test -v 2`
- `python scripts/audit_project.py`
