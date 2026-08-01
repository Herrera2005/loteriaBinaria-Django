# Matriz de trazabilidad — fase actual corregida

## Estados usados

- **IMPLEMENTADA:** existe código correlacionado.
- **VERIFICADA ESTÁTICAMENTE:** además pasó el auditor estático o compilación.
- **PENDIENTE EJECUCIÓN DJANGO:** existe prueba automatizada, pero falta
  ejecutarla en un entorno con dependencias instaladas.
- **PARCIAL:** la política/base existe, pero el módulo funcional no.
- **PENDIENTE:** no se implementó y no se expone falsamente.

| Regla / requisito | Implementación | Evidencia diseñada | Estado actual |
|---|---|---|---|
| SQLite fase 1; MySQL fase 2 | `config/settings.py`, requirements separados, decisión T3-001 | configuración + script limpio | PENDIENTE EJECUCIÓN DJANGO |
| PostgreSQL excluido | allowlist de motores | subprocess con URL PostgreSQL | PENDIENTE EJECUCIÓN DJANGO |
| Usuario personalizado | `accounts.User`, `AUTH_USER_MODEL`, migraciones | migración limpia + tests | PENDIENTE EJECUCIÓN DJANGO |
| Username/email/documento normalizados | model, form y service | registro, login y duplicados case-insensitive | PENDIENTE EJECUCIÓN DJANGO |
| Mayoría de edad | form + service | menor rechazado | PENDIENTE EJECUCIÓN DJANGO |
| Términos/privacidad vigentes | models, form, service | ausencia y carrera de versión | PENDIENTE EJECUCIÓN DJANGO |
| Legal histórico inmutable | modelos, service y seeds | save/update/delete, carrera y rerun de seeds | PENDIENTE EJECUCIÓN DJANGO |
| Password solo por Django | `create_user`/`set_password` | `check_password` | PENDIENTE EJECUCIÓN DJANGO |
| Seed demo sin credencial fija | variable de entorno + validadores | tres pruebas del comando | PENDIENTE EJECUCIÓN DJANGO |
| Roles backend | Groups + `assigned_mode_codes` | login y selector | PENDIENTE EJECUCIÓN DJANGO |
| Selector solo roles asignados | `ModeSelectionForm`, POST | valor no asignado rechazado | PENDIENTE EJECUCIÓN DJANGO |
| Modo activo aislado | session + decorador | dashboard incorrecto 403 | PENDIENTE EJECUCIÓN DJANGO |
| Cuenta suspendida no opera | login form, selector y decorador | login/selector bloqueados | PENDIENTE EJECUCIÓN DJANGO |
| Logout POST | `LogoutView` restringida | GET 405, POST 302 | PENDIENTE EJECUCIÓN DJANGO |
| Conteos administrativos protegidos | staff + modo ADMINISTRADOR | no staff recibe `None` y sin cards | PENDIENTE EJECUCIÓN DJANGO |
| SQLite relativa determinista | `BASE_DIR / NAME` | test de configuración | PENDIENTE EJECUCIÓN DJANGO |
| Histórico legal protegido | `PROTECT`, admin read-only | admin tests | PENDIENTE EJECUCIÓN DJANGO |
| CLIENTE completo cuando exista backend | política de modo | multirrol y navegación | PARCIAL |
| VENDEDOR/ADMIN no compran en esos modos | navegación/templates sin compra | pruebas de dashboard | PENDIENTE EJECUCIÓN DJANGO |
| Bootstrap 5.3 real | CDN oficial con SRI + componentes | revisión template/manual | VERIFICADA ESTÁTICAMENTE |
| Responsive común | grid/offcanvas/cards/tables/utilities, 44 px | matriz de cinco anchos | VERIFICADA ESTÁTICAMENTE; manual pendiente |
| CSRF en POST | middleware + templates | auditor y cliente CSRF | VERIFICADA ESTÁTICAMENTE; Django pendiente |
| Sin JSON/localStorage/fetch | runtime nuevo + auditor | `audit_project.py` | VERIFICADA ESTÁTICAMENTE |
| Sin `pages/*.html` activos | solo ZIP de respaldo | `audit_project.py` | VERIFICADA ESTÁTICAMENTE |
| ZIP visual preservado | `respaldo_frontend/` | hash/inventario + test | VERIFICADA ESTÁTICAMENTE; Django pendiente |
| Python parseable | todos los `.py` | `compileall` | VERIFICADA ESTÁTICAMENTE |
| JavaScript parseable | `static/js/app.js` | `node --check` | VERIFICADA ESTÁTICAMENTE |
| Wallets/movimientos | no implementados | futuros tests de servicios | PENDIENTE |
| Vendedores/solicitudes | no implementados | futuros tests de flujo/concurrencia MySQL | PENDIENTE |
| Eventos/boletos/resultados | no implementados | futuros tests de lotería | PENDIENTE |

## Regla de actualización

Una fila solo pasa a **VERIFICADA** cuando su comando o prueba se ejecuta y la
evidencia se guarda. La presencia de un template nunca basta para verificar
una regla de negocio.
