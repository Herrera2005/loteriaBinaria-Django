# Resultado de implementación P-28A

## Implementado

- `Wallet` separada por moneda REAL/VIRTUAL.
- Saldos disponibles y reservados en `BigIntegerField` `_minor`.
- Restricciones de unicidad y no negatividad.
- `Movement` append-only con correlación por `operation_id`.
- `AuditEvent` append-only con actor, modo, acción, recurso, motivo, IP y metadata no sensible.
- Admin read-only para los tres modelos.
- Servicio transaccional e idempotente de provisión.
- Señal al asignar roles.
- Migración de backfill para usuarios existentes.
- Comando `backfill_wallets` idempotente.
- 28 pruebas nuevas; inventario total diseñado: 195.
- Auditor estático ampliado a P-28A.

## No implementado intencionalmente

- vistas;
- URLs;
- templates;
- recarga;
- conversión;
- transferencia;
- compra mayorista;
- compra de boleto;
- edición de saldos;
- APIs o pagos reales.

## Referencia visual futura

Del ZIP legado se conservarán en P-28:

- cards separadas para REAL y VIRTUAL;
- indicadores disponible/reservado;
- tabla de movimientos;
- filtros por moneda y tipo;
- identidad azul profundo/dorado.

Se descartan:

- JSON/localStorage;
- comisión de recarga 5 %;
- conversión 15 %;
- regla 75 %;
- creación de wallets desde JavaScript;
- modificación de saldos desde el navegador.

## Límite de verificación en el entorno de preparación

Se ejecutó compilación sintáctica y auditoría estructural de los archivos generados. La ejecución Django completa debe realizarse en la `.venv` del proyecto con Django 5.2.16, siguiendo `GUIA_APLICACION_P28A.md`.
