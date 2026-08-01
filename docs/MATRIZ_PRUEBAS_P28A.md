# Matriz de pruebas P-28A

| ID | Componente | Caso | Resultado esperado |
|---|---|---|---|
| P28A-WAL-001 | Wallet | Asignar rol operativo | Se crean REAL y VIRTUAL |
| P28A-WAL-002 | Wallet | Ejecutar servicio dos veces | Continúan exactamente dos wallets |
| P28A-WAL-003 | Wallet | Usuario sin guardar | `ValidationError` |
| P28A-WAL-004 | Wallet | Usuario suspendido | Wallets suspendidas |
| P28A-WAL-005 | Wallet | Duplicar usuario+moneda | `IntegrityError` |
| P28A-WAL-006 | Wallet | Inspeccionar campos monetarios | `BigIntegerField`, no float/decimal |
| P28A-WAL-007 | Wallet | Saldo negativo por validación | Rechazado |
| P28A-WAL-008 | Wallet | Saldo negativo por UPDATE | Restricción de BD lo rechaza |
| P28A-WAL-009 | Wallet | Eliminar usuario con wallet | `ProtectedError` |
| P28A-WAL-010 | Backfill | Ejecutar dos veces | Sin duplicados |
| P28A-WAL-011 | Señal | Añadir segundo rol | Sin duplicados |
| P28A-MOV-001 | Movement | Campos monetarios | `BigIntegerField` |
| P28A-MOV-002 | Movement | Eliminar wallet usada | `ProtectedError` |
| P28A-MOV-003 | Movement | Mismo `operation_id` en varios efectos | Permitido y correlacionado |
| P28A-MOV-004 | Movement | Monto cero | Rechazado |
| P28A-MOV-005 | Movement | Segundo `save()` | Rechazado |
| P28A-MOV-006 | Movement | Delete individual/masivo | Rechazado |
| P28A-MOV-007 | Movement | Update/bulk_update | Rechazado |
| P28A-ADM-001 | Wallet admin | Add/change/delete | Denegados |
| P28A-ADM-002 | Movement admin | Add/change/delete | Denegados |
| P28A-AUD-001 | AuditEvent | Actor | FK `PROTECT` |
| P28A-AUD-002 | AuditEvent | Registro mínimo | Creado correctamente |
| P28A-AUD-003 | AuditEvent | Metadata con token/secret | Rechazada |
| P28A-AUD-004 | AuditEvent | Segundo `save()` | Rechazado |
| P28A-AUD-005 | AuditEvent | Delete individual/masivo | Rechazado |
| P28A-AUD-006 | AuditEvent | Update/bulk_update | Rechazado |
| P28A-AUD-007 | AuditEvent | Índices | Actor, acción y recurso presentes |
| P28A-ADM-003 | Audit admin | Add/change/delete | Denegados |
| P28A-REG-001 | Proyecto | Suite completa | P-27 sin regresiones |
| P28A-REG-002 | Migraciones | `--check --dry-run` | `No changes detected` |
| P28A-REG-003 | Portabilidad | `sqlmigrate` | Sin SQL PostgreSQL |
