# Plan siguiente desde P-28 oficial

## Estado cerrado

- P-27: tres CRUD evaluables y reglas Lottery.
- P-28A: Wallet, Movement y AuditEvent, migraciones, admin read-only y backfill.
- P-28 oficial: wallet propia, movimientos propios paginados, auditoría administrativa y dashboards con datos reales.

## Siguiente bloque autorizado: P-29

Integrar y auditar la navegación completa sin crear funciones nuevas:

1. revisar `apps/core/context_processors.py`;
2. mostrar en navbar/offcanvas solo enlaces válidos para el modo activo;
3. marcar correctamente la ruta activa;
4. comprobar que CLIENTE no ve enlaces de VENDEDOR/ADMINISTRADOR;
5. comprobar que VENDEDOR no ve compra de boletos;
6. comprobar que ADMINISTRADOR ve auditoría y módulos administrativos permitidos;
7. revisar todos los `{% url %}` y eliminar enlaces muertos;
8. ejecutar pruebas de reverse, 403, 404 y responsive.

## Aún no autorizado

- recarga REAL;
- conversión VIRTUAL a REAL;
- transferencia VIRTUAL;
- compra mayorista;
- acciones sobre solicitudes;
- compra de boleto;
- publicación de resultado.

Estas operaciones requieren modelo/servicio transaccional, pruebas de rollback e idempotencia y POST con CSRF antes de mostrar botones.
