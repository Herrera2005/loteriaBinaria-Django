# Decisión P-28A — Modelos Finance y Auditoría

Fecha: 2026-08-01  
Proyecto: Taller #3 Lotería Binaria con Django

## 1. Autoridad aplicada

1. Enunciado del Taller #3.
2. Cinco documentos canónicos.
3. Guía docente VideoClub.
4. ZIP legado únicamente como referencia visual.

La entrega usa SQLite en la primera fase y MySQL en la segunda. PostgreSQL no forma parte de este taller.

## 2. Alcance de esta decisión

P-28A prepara los modelos necesarios antes del P-28 oficial. No agrega vistas, URLs, templates ni operaciones financieras funcionales.

Se implementan únicamente:

- `finance.Wallet`;
- `finance.Movement`;
- `core.AuditEvent`;
- admin read-only;
- provisión idempotente de wallets;
- backfill para usuarios existentes;
- migraciones y pruebas.

## 3. Wallet

### Campos

| Campo | Tipo | Regla |
|---|---|---|
| `user` | FK `PROTECT` | Propietario del saldo |
| `currency` | `CharField` | `REAL` o `VIRTUAL` |
| `available_minor` | `BigIntegerField` | No negativo |
| `reserved_minor` | `BigIntegerField` | No negativo |
| `status` | `CharField` | Estado operativo |
| `created_at` | `DateTimeField` | Creación |
| `updated_at` | `DateTimeField` | Última actualización |

### Restricciones

- `UniqueConstraint(user, currency)`.
- Una wallet REAL y una VIRTUAL como máximo por usuario.
- Ningún monto usa `float` o `DecimalField`.
- El admin no permite añadir, cambiar ni eliminar.
- Los saldos solo podrán cambiar mediante servicios transaccionales futuros.

### Catálogo de estado

Se reutiliza el vocabulario ya existente en `accounts.User` para evitar un catálogo nuevo incompatible:

- `ACTIVE`;
- `SUSPENDED`;
- `BLOCKED`;
- `DISABLED`.

## 4. Movement

### Campos

| Campo | Tipo | Regla |
|---|---|---|
| `wallet` | FK `PROTECT` | Moneda derivada de la wallet |
| `operation_id` | UUID indexado | Correlaciona varios efectos de una operación |
| `type` | `CharField` | Tipo de efecto confirmado |
| `direction` | `CharField` | `CREDIT` o `DEBIT` |
| `amount_minor` | `BigIntegerField` | Mayor que cero |
| `balance_after_minor` | `BigIntegerField` | No negativo |
| `description` | `CharField` | Explicación breve |
| `created_at` | `DateTimeField` | Fecha inmutable |

`operation_id` no es único: una conversión o transferencia produce varios movimientos correlacionados.

### Catálogo de tipos preparado

El catálogo sale de las operaciones enumeradas en las reglas canónicas:

- `TOP_UP`;
- `VIRTUAL_TO_REAL`;
- `VIRTUAL_TRANSFER`;
- `WHOLESALE_PURCHASE`;
- `CONVERSION_REQUEST`;
- `TICKET_PURCHASE`;
- `PRIZE`;
- `REFUND`;
- `WITHDRAWAL`;
- `ADJUSTMENT`.

P-28A solo define el catálogo. No ejecuta ninguna de esas operaciones.

### Inmutabilidad

Se bloquean:

- segundo `save()` sobre una instancia existente;
- `delete()` individual;
- `QuerySet.update()`;
- `QuerySet.delete()`;
- `bulk_update()`.

## 5. AuditEvent

### Campos

| Campo | Tipo | Regla |
|---|---|---|
| `actor` | FK `PROTECT` | Usuario responsable |
| `active_mode` | `CharField` | CLIENTE/VENDEDOR/ADMINISTRADOR o vacío |
| `action` | `CharField` | Acción ejecutada |
| `resource_type` | `CharField` | Tipo de recurso |
| `resource_id` | `CharField` | PK numérica o UUID como texto |
| `reason` | `TextField` | Motivo cuando aplica |
| `metadata` | `TextField` | Complemento no sensible, nunca fuente de verdad |
| `ip_address` | `GenericIPAddressField` | IP aproximada cuando corresponda |
| `created_at` | `DateTimeField` | Fecha inmutable |

No se usa `JSONField`. Esto conserva portabilidad y evita usar JSON como autoridad de negocio.

### Protección de secretos

La validación rechaza metadata que declare contraseñas, tokens, secretos o claves de API. El modelo no almacena credenciales.

### Inmutabilidad

Se aplican los mismos bloqueos append-only de `Movement`.

## 6. Provisión de wallets

`finance.services.ensure_user_wallets(user)`:

- usa `transaction.atomic`;
- exige usuario persistido;
- usa `get_or_create`;
- crea REAL y VIRTUAL con saldo cero;
- es idempotente;
- no se ejecuta desde una vista GET.

La señal se activa cuando se asigna un rol operativo mediante `User.groups`. La migración y el comando `backfill_wallets` cubren usuarios anteriores.

## 7. Compatibilidad

La implementación utiliza exclusivamente elementos soportados por SQLite y MySQL:

- `BigIntegerField`;
- `UUIDField`;
- `CheckConstraint`;
- `UniqueConstraint`;
- `ForeignKey(PROTECT)`;
- índices convencionales;
- transacciones Django.

No hay tipos, extensiones o SQL exclusivos de PostgreSQL.
