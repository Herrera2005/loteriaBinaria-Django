# P-33 — Finanzas del Cliente

> **DOCUMENTO HISTÓRICO / DE FASE.** Evidencia de P-33. Las frases “pasos posteriores” se refieren a esa fecha; hoy esos módulos existen. Para el estado vigente consulte `docs/INDICE_DOCUMENTACION.md`, `README.md` y `docs/MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md`.


## Alcance implementado
- Recarga REAL académica 1:1, sin comisión ni datos de tarjeta.
- Conversión VIRTUAL → REAL: débito bruto VIRTUAL, comisión 10 %, crédito neto REAL 90 %.
- Transferencia exclusivamente VIRTUAL entre cuentas CLIENTE activas; sin autoenvío.
- Retiro académico desde REAL, sin segunda comisión.
- `operation_id` único, operaciones históricas inmutables y movimientos correlacionados.
- Formularios POST con CSRF y autorización por modo CLIENTE.

## Matriz
| Operación | Moneda origen | Moneda destino | Tarifa | Modo |
|---|---|---|---|---|
| Recarga | Externa simulada | REAL | 0 % | CLIENTE |
| Conversión | VIRTUAL | REAL | 10 % | CLIENTE |
| Transferencia | VIRTUAL | VIRTUAL de otro cliente | 0 % | CLIENTE |
| Retiro | REAL | Externa simulada | 0 % adicional | CLIENTE |

## Seguridad
Las vistas no aceptan usuario, saldo, tarifa ni moneda como autoridad. Los servicios vuelven a consultar cuenta, roles, wallets y saldos dentro de `transaction.atomic()`. Las wallets se bloquean con `select_for_update()` cuando la base lo soporta.

## Fuera de este bloque
Compra mayorista del vendedor, solicitudes Cliente–Vendedor y compra de boletos corresponden a pasos posteriores.
