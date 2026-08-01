# Plan siguiente desde la preparación P-28A

## Estado actual

P-27 está cerrado. La preparación P-28A incorpora:

- `finance.Wallet` por usuario y moneda REAL/VIRTUAL;
- `finance.Movement` append-only;
- `core.AuditEvent` append-only;
- admin read-only;
- servicio idempotente `ensure_user_wallets`;
- señal al asignar roles;
- migración y backfill de usuarios existentes;
- pruebas de modelos, inmutabilidad y permisos de admin.

## Primero: validar P-28A en SQLite

1. Aplicar los archivos sobre la rama `feature/taller3-p28-finance-core`.
2. Revisar las migraciones generadas para SQLite/MySQL portable.
3. Ejecutar migraciones.
4. Ejecutar `backfill_wallets` dos veces y comprobar idempotencia.
5. Ejecutar las pruebas específicas y la regresión completa.
6. Confirmar `No changes detected`.
7. Hacer commit antes de iniciar vistas.

## Después: P-28 oficial, no P-29 todavía

Implementar únicamente consultas seguras de Finance/Core:

1. wallet propia read-only;
2. movimientos propios paginados;
3. auditoría administrativa list/detail read-only;
4. dashboards con datos reales del backend;
5. ninguna edición directa de balance;
6. ninguna recarga o conversión en esta primera entrega visual;
7. pruebas de propiedad, autenticación, modo y paginación;
8. Bootstrap 5.3 y responsive en cinco anchos.

## Orden obligatorio para reglas sensibles futuras

1. modelo y migración;
2. servicio con `transaction.atomic`;
3. pruebas de éxito, rechazo, idempotencia y rollback;
4. formulario POST con CSRF;
5. vista y URL;
6. template Bootstrap;
7. prueba manual y responsive;
8. actualización de matriz.

No crear botones, saldos ficticios, timers ni compra de boletos sin backend persistente.
