# Matriz de trazabilidad — estado hasta preparación P-28A

## Estados

- **IMPLEMENTADA:** existe código correlacionado.
- **VERIFICADA:** el usuario confirmó suite verde hasta P-27.
- **PENDIENTE PRUEBA LOCAL P-28A:** código generado; falta ejecutar migraciones y suite en la `.venv` del proyecto.
- **PARCIAL:** existe base técnica, pero la interfaz o flujo pertenece a una fase posterior.
- **PENDIENTE:** no implementado ni expuesto falsamente.

| Regla / requisito | Implementación principal | Evidencia | Estado |
|---|---|---|---|
| SQLite fase 1; MySQL fase 2 | `config/settings.py`, requirements separados | configuración y suite P-27 | VERIFICADA |
| PostgreSQL excluido | allowlist de motores + auditor | test subprocess | VERIFICADA |
| Usuario personalizado temprano | `accounts.User`, `AUTH_USER_MODEL` | migraciones y tests | VERIFICADA |
| Registro, términos, roles y modos | Accounts | suite P-27 | VERIFICADA |
| Tres CRUD evaluables | Accounts, Vendors, Lottery | 167 pruebas P-27 | VERIFICADA |
| Bootstrap 5.3, CSRF y navegación por modo | base/templates/contexto | suite y auditor P-27 | VERIFICADA; responsive manual vigente |
| OCTAL 4, DECIMAL 5, HEXADECIMAL 6 | Lottery | model/form/CRUD | VERIFICADA |
| Cierre de evento 10 minutos antes | Lottery model/form | pruebas P-27 | VERIFICADA |
| Ticket y resultado históricos | managers/model/admin | pruebas P-27 | VERIFICADA |
| Wallet única por usuario y moneda | `finance.Wallet` | constraint y tests P28A-WAL | IMPLEMENTADA; PENDIENTE PRUEBA LOCAL P-28A |
| Saldos disponibles/reservados no negativos | checks + validators | P28A-WAL-006/007/008 | IMPLEMENTADA; PENDIENTE PRUEBA LOCAL P-28A |
| Montos `BigIntegerField` `_minor` | Wallet/Movement | inspección de campos | IMPLEMENTADA; PENDIENTE PRUEBA LOCAL P-28A |
| Provisión REAL/VIRTUAL idempotente | `ensure_user_wallets`, señal y backfill | tests de servicio/comando | IMPLEMENTADA; PENDIENTE PRUEBA LOCAL P-28A |
| Movement append-only | model/queryset/admin | save/update/delete/bulk tests | IMPLEMENTADA; PENDIENTE PRUEBA LOCAL P-28A |
| Movimientos correlacionados | `operation_id` indexado no único | dos efectos misma operación | IMPLEMENTADA; PENDIENTE PRUEBA LOCAL P-28A |
| AuditEvent append-only | core model/queryset/admin | tests de inmutabilidad | IMPLEMENTADA; PENDIENTE PRUEBA LOCAL P-28A |
| Auditoría sin secretos | validación de metadata | rechazo de token/secret | IMPLEMENTADA; PENDIENTE PRUEBA LOCAL P-28A |
| Admin financiero/auditoría read-only | admin mixins | pruebas de permisos | IMPLEMENTADA; PENDIENTE PRUEBA LOCAL P-28A |
| Wallet propia y movimientos paginados | vistas/templates P-28 | todavía no creados | PENDIENTE |
| Auditoría administrativa list/detail | vistas/templates P-28 | todavía no creados | PENDIENTE |
| Navegación completa por rol | contexto base mínimo | P-29 | PARCIAL |
| Operaciones financieras | futuros servicios POST | P-34 | PENDIENTE |
| Compra de boletos | no expuesta | fase posterior | PENDIENTE |
| Migración MySQL | configuración lista | repetir suite | PENDIENTE SEGUNDA FASE |

## Puerta P-28A

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations finance core
python manage.py sqlmigrate finance 0001
python manage.py sqlmigrate core 0001
python manage.py migrate
python manage.py backfill_wallets
python manage.py backfill_wallets
python manage.py test apps.finance.tests.test_models -v 2
python manage.py test apps.core.tests.test_models -v 2
python manage.py test -v 2
python scripts/audit_project.py
.\scripts\verify.ps1
```

P-28 oficial comienza únicamente cuando toda esta puerta termina en verde.
