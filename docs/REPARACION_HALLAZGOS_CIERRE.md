# Reparación autorizada de hallazgos de cierre

## Alcance

Se verificaron y repararon únicamente los IDs `AUD-CIERRE-001` a
`AUD-CIERRE-024` del informe aprobado.

| ID | Estado final | Archivos principales | Evidencia o prueba |
|---|---|---|---|
| AUD-CIERRE-001 | Reparado | paquete final, auditor, manifiesto | auditor `--package` rechaza `*.sqlite3` y `*.db` |
| AUD-CIERRE-002 | Reparado | paquete final, auditor, `.gitignore` | auditor `--package` rechaza `.venv`, `.env`, bytecode y cachés |
| AUD-CIERRE-003 | Reparado | `MANIFEST_SHA256.txt`, `scripts/manifest_project.py` | verificación SHA-256 sin faltantes ni diferencias |
| AUD-CIERRE-004 | Reparado | `apps/core/views.py`, `apps/lottery/views.py` | regresiones GET sin cambios de estado, historial ni `updated_at` |
| AUD-CIERRE-005 | Reparado | `apps/lottery/models.py` | pruebas de `update`, `delete` y `bulk_update` rechazados |
| AUD-CIERRE-006 | Reparado | `apps/lottery/services.py` | una serie inválida no revierte la válida |
| AUD-CIERRE-007 | Reparado | `apps/lottery/services.py` | intento fallido persiste `last_synced_at` sin efectos parciales |
| AUD-CIERRE-008 | Reparado | modelo y migración `0011` | constraint sin condición y migración limpia |
| AUD-CIERRE-009 | Reparado | README, matriz, inventario y resultados | auditor rechaza textos vigentes P-28 |
| AUD-CIERRE-010 | Reparado | `docs/historico/p27_p28/` | no quedan copias `(1)` en documentación vigente |
| AUD-CIERRE-011 | Reparado | `scripts/audit_project.py` | `AUDITORÍA ESTÁTICA DE CIERRE: OK` |
| AUD-CIERRE-012 | Reparado | `scripts/verify.ps1`, `scripts/verify.sh` | puerta incluye comandos repetidos, deploy y manifiesto |
| AUD-CIERRE-013 | Reparado | command de schedules | prueba exige `CommandError` cuando hay errores |
| AUD-CIERRE-014 | Reparado | servicios y vistas de lottery/core | sincronización global fuera de GET y sync dirigido para eventos nuevos |
| AUD-CIERRE-015 | Reparado | vistas/templates de core, vendors y lottery | pruebas de paginación y límite en base de datos |
| AUD-CIERRE-016 | Reparado | `lottery/urls.py`, `lottery/views.py` | ruta huérfana retirada y rutas restantes probadas |
| AUD-CIERRE-017 | Reparado | cuatro templates retirados | búsqueda de consumidores y auditor de templates muertos |
| AUD-CIERRE-018 | Reparado | `apps/core/date_utils.py`, vistas core/finance | pruebas de intervalo local `[inicio, día siguiente)` |
| AUD-CIERRE-019 | Preparado, validación externa pendiente | `verify_mysql.ps1/.sh` | requiere servidor MySQL real; no se simula aprobación |
| AUD-CIERRE-020 | Reparado | settings, `.env.example`, verify | `check --deploy` sin hallazgos con variables productivas |
| AUD-CIERRE-021 | Reparado | políticas, servicio y vista de compra | servicio rechaza rol CLIENTE cuando el modo es VENDEDOR |
| AUD-CIERRE-022 | Reparado | validadores compartidos en lottery/vendors | modelo y formulario rechazan los mismos casos |
| AUD-CIERRE-023 | Reparado | imports, URLs accounts y política vendor | suite completa y búsqueda estática de símbolos |
| AUD-CIERRE-024 | No requería cambio funcional | forms/views/tests accounts existentes | pruebas confirman que el panel no expone `is_superuser` ni permisos directos |

## Decisiones de implementación

- Una petición GET no modifica estados ni crea historial.
- `last_synced_at` representa el último intento real de una serie existente,
  incluso si la generación falla.
- El sello se confirma bajo `select_for_update()`; los efectos de negocio se
  ejecutan en un savepoint y se revierten por completo ante error.
- Cada serie se procesa en su propia transacción.
- Los errores parciales del comando producen código de salida no exitoso.
- La unicidad de secuencia se expresa sin índice parcial para SQLite/MySQL.
- Los filtros diarios usan el intervalo local `[inicio, día siguiente)`.
- MySQL sigue pendiente de ejecución sobre infraestructura real.

## Resultados ejecutados

- `python manage.py check`: **OK**.
- `python manage.py makemigrations --check --dry-run`: **No changes detected**.
- migración limpia hasta `lottery.0011`: **OK**.
- regresiones nuevas: **20 pruebas, OK**.
- suites con configuración original:
  - accounts: 100;
  - core: 49;
  - finance: 57;
  - vendors: 74;
  - lottery: 164.
- total por apps: **458 pruebas, OK**.
- suite conjunta con hasher rápido externo de auditoría: **458 pruebas, OK**.
- seeds y comandos ejecutados dos veces sobre SQLite limpia: **OK**.
- `check --deploy` con variables productivas: **0 hallazgos**.
- auditoría estática, auditoría estricta `--package` y manifiesto: **OK** después de la limpieza final.

No se ejecutó MySQL por ausencia de servidor en el entorno de reparación.
