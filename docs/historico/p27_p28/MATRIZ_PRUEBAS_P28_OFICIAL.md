# Matriz de pruebas P-28 oficial

## Finance

| Código | Caso | Resultado esperado |
|---|---|---|
| P28-FIN-001 | Anónimo abre wallet/movimientos | Redirección a login |
| P28-FIN-002 | Usuario sin modo activo | Redirección a selector |
| P28-FIN-003 | CLIENTE/VENDEDOR/ADMINISTRADOR | Acceso a finanzas propias |
| P28-FIN-004 | Parámetro `user` ajeno | Se ignora; solo datos propios |
| P28-FIN-005 | GET con wallets faltantes | No crea wallets |
| P28-FIN-006 | POST a wallet | 405 |
| P28-FIN-007 | Ruta wallet con PK inventado | 404 |
| P28-FIN-008 | Movimientos ajenos | No aparecen |
| P28-FIN-009 | Filtros válidos | Moneda/tipo/dirección correctos |
| P28-FIN-010 | 16 movimientos | Paginación 15 + 1 |
| P28-FIN-011 | POST a movimientos | 405 |

## Core y dashboards

| Código | Caso | Resultado esperado |
|---|---|---|
| P28-CORE-001 | Home público | 200 y template correcto |
| P28-CORE-002 | Productos activos/inactivos | Solo activos visibles |
| P28-CORE-003 | Dashboard Cliente | Saldos/movimientos reales propios |
| P28-CORE-004 | Dashboard Vendedor | Wallets y asignaciones reales |
| P28-CORE-005 | Dashboard Administrador | Auditoría reciente y enlaces reales |
| P28-CORE-006 | Acción inexistente | No se muestra compra/recarga |

## Auditoría

| Código | Caso | Resultado esperado |
|---|---|---|
| P28-AUD-001 | Anónimo | Login |
| P28-AUD-002 | CLIENTE/VENDEDOR | 403 |
| P28-AUD-003 | Admin en modo CLIENTE | 403 |
| P28-AUD-004 | Admin en modo ADMINISTRADOR | 200 |
| P28-AUD-005 | Filtros | Acción/recurso/modo correctos |
| P28-AUD-006 | 21 eventos | Paginación 20 + 1 |
| P28-AUD-007 | Detalle existente | 200 read-only |
| P28-AUD-008 | Detalle inexistente | 404 |
| P28-AUD-009 | POST list/detail | 405 |
