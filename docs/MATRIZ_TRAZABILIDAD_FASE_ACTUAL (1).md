# Matriz de trazabilidad — estado hasta P-28 oficial

## Estados

- **VERIFICADA:** código y suite confirmados en el equipo local.
- **IMPLEMENTADA; PENDIENTE PRUEBA LOCAL P-28:** código generado en este paquete y debe ejecutarse en la `.venv` local.
- **PARCIAL:** base técnica existente; falta una fase posterior.
- **PENDIENTE:** no implementado ni expuesto falsamente.

| Regla / requisito | Implementación principal | Evidencia | Estado |
|---|---|---|---|
| SQLite fase 1; MySQL fase 2 | `config/settings.py` | configuración y suite | VERIFICADA |
| PostgreSQL excluido | allowlist + test subprocess | Core configuration | VERIFICADA |
| Usuario personalizado temprano | `accounts.User` | migraciones/tests | VERIFICADA |
| Tres CRUD evaluables | Accounts, Vendors, Lottery | suite P-27 | VERIFICADA |
| Bootstrap 5.3 y base común | templates/base + CSS | auditor/templates | VERIFICADA |
| OCTAL 4, DECIMAL 5, HEXADECIMAL 6 | Lottery | modelos/forms/tests | VERIFICADA |
| Wallet única REAL/VIRTUAL | `finance.Wallet` | constraints/tests | VERIFICADA |
| Movement append-only | model/queryset/admin | tests de inmutabilidad | VERIFICADA |
| AuditEvent append-only y sin secretos | Core model/admin | tests | VERIFICADA |
| Wallet propia read-only | `finance.wallet_detail` | pruebas de propiedad/GET | IMPLEMENTADA; PENDIENTE PRUEBA LOCAL P-28 |
| Movimientos propios paginados | `finance.movement_list` | filtros, 15 por página, 405 | IMPLEMENTADA; PENDIENTE PRUEBA LOCAL P-28 |
| Auditoría admin list/detail | Core audit views | 403/404/405/paginación | IMPLEMENTADA; PENDIENTE PRUEBA LOCAL P-28 |
| Home con productos activos reales | `core.home` | prueba activo/inactivo | IMPLEMENTADA; PENDIENTE PRUEBA LOCAL P-28 |
| Dashboards con datos reales | Core dashboards | pruebas por rol | IMPLEMENTADA; PENDIENTE PRUEBA LOCAL P-28 |
| Navegación global completa por modo | context processor actual | P-29 | PARCIAL |
| Operaciones financieras POST | futuros services | P-34 | PENDIENTE |
| Compra de boletos | no expuesta | fase posterior | PENDIENTE |
| Migración MySQL | configuración lista | segunda fase | PENDIENTE |

## Puerta P-28

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.finance -v 2
python manage.py test apps.core -v 2
python manage.py test -v 2
python scripts/audit_project.py
.\scripts\verify.ps1
```

P-29 comienza únicamente cuando toda esta puerta termina en verde.
