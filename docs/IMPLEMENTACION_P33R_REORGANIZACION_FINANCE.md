# P-33R — Reorganización de Finanzas Cliente

> **DOCUMENTO HISTÓRICO / DE FASE.** Evidencia de reorganización P-33R; se conserva por trazabilidad. Para el estado vigente consulte `docs/INDICE_DOCUMENTACION.md`, `README.md` y `docs/MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md`.


## Decisión

- Recarga y retiro REAL comparten `/finance/real-operations/` y se presentan mediante pestañas.
- VIRTUAL→REAL y la explicación de REAL→VIRTUAL comparten `/finance/wallet-conversion/`.
- REAL→VIRTUAL no ejecuta una operación directa: pertenece al flujo de solicitud Cliente–Vendedor del Paso 4.
- Transferir VIRTUAL permanece en `/finance/transfer/`.
- Toda pantalla operativa muestra saldos REAL y VIRTUAL, disponibles y reservados.
- Las rutas antiguas se conservan únicamente como redirecciones GET para no romper marcadores.

## Fuera de alcance de P-33R

No se crea todavía `ConversionRequest`, no se reserva REAL y no se implementa recepción por vendedores. Esas acciones corresponden a P-34.

## Puerta de salida

- Las tres páginas agrupadas funcionan solo en modo CLIENTE.
- Los saldos mostrados pertenecen al usuario autenticado.
- Recarga, retiro, conversión VIRTUAL→REAL y transferencia mantienen sus servicios atómicos.
- La pestaña REAL→VIRTUAL no crea registros ni altera saldos.
- Suite completa y auditor estático en verde.
