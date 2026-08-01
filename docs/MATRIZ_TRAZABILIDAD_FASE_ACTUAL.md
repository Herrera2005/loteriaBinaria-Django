# Matriz de trazabilidad — estado hasta P-27

## Estados

- **IMPLEMENTADA:** existe código correlacionado.
- **VERIFICADA ESTÁTICAMENTE:** pasó compilación y auditoría estática.
- **PENDIENTE SUITE FINAL:** requiere ejecutar `scripts/verify.ps1` en el
  entorno local con Django instalado.
- **PARCIAL:** existe la base, pero el flujo pertenece a una fase posterior.
- **PENDIENTE:** todavía no se implementó ni se expone falsamente.

| Regla / requisito | Implementación principal | Evidencia automatizada | Estado |
|---|---|---|---|
| SQLite fase 1; MySQL fase 2 | `config/settings.py`, requirements separados | configuración, migración limpia | IMPLEMENTADA; suite final pendiente |
| PostgreSQL excluido | allowlist de motores + auditor | configuración y subprocess | VERIFICADA ESTÁTICAMENTE |
| Usuario personalizado temprano | `accounts.User`, `AUTH_USER_MODEL` | migraciones y tests de integridad | IMPLEMENTADA; suite final pendiente |
| Registro adulto, términos y privacidad | forms/services/models Accounts | tests de registro, aceptación y carreras | IMPLEMENTADA; suite final pendiente |
| Roles y modo activo backend | Groups, sesión, decoradores/mixins | tests de login, selector y 403 | IMPLEMENTADA; suite final pendiente |
| CRUD Accounts | views/urls/forms/templates/services | búsqueda, paginación, C/R/U/D, CSRF, historia | IMPLEMENTADA; suite final pendiente |
| CRUD VendorProfile | Vendors completo | filtros, paginación, C/R/U/D, 404, CSRF | IMPLEMENTADA; suite final pendiente |
| ConversionRequest read-only | lista administrativa protegida | GET permitido, POST 405, sin editar/eliminar | IMPLEMENTADA; suite final pendiente |
| Producto OCTAL | `01234567`, 4 únicos | model/form tests | IMPLEMENTADA; suite final pendiente |
| Producto DECIMAL | `0123456789`, 5 únicos | model/form tests | IMPLEMENTADA; suite final pendiente |
| Producto HEXADECIMAL | `0123456789ABCDEF`, 6 únicos | rechazo de longitud 4 y repetidos | IMPLEMENTADA; suite final pendiente |
| Configuración de producto con eventos protegida | model, form y manager | save y bulk update rechazados | IMPLEMENTADA; suite final pendiente |
| CRUD LotteryProduct | lista/filtro/detalle/crear/editar/eliminar | permisos, filtro, CSRF, 404 y protección | IMPLEMENTADA; suite final pendiente |
| Cierre evento = `draw_at - 10 min` | model y form backend | model/form/CRUD tests | IMPLEMENTADA; suite final pendiente |
| Evento publicado no cambia configuración | model, form y tests | POST manipulado, save y bulk update | IMPLEMENTADA; suite final pendiente |
| Evento solo se elimina en Borrador sin historia | service transaccional | draft, publicado, ticket y resultado | IMPLEMENTADA; suite final pendiente |
| CRUD DrawEvent | lista/filtros/paginación/detalle/forms/delete | permisos, filtros, paginación, CSRF, 404 | IMPLEMENTADA; suite final pendiente |
| Ticket único por evento/combinación | constraint + normalización | IntegrityError y validaciones 4/5/6 | IMPLEMENTADA; suite final pendiente |
| Ticket histórico no eliminable | manager/model + PROTECT | delete individual y masivo | IMPLEMENTADA; suite final pendiente |
| DrawResult OneToOne e inmutable | model/manager/admin read-only | segundo resultado, save/update/delete | IMPLEMENTADA; suite final pendiente |
| Bootstrap 5.3 real | base, navbar/offcanvas, cards, forms, tables | auditoría de templates | VERIFICADA ESTÁTICAMENTE |
| Responsive 360/390/768/1024/1440 | grid, offcanvas, tablas y CSS complementario | matriz manual | IMPLEMENTADA; comprobación visual pendiente |
| CSRF en acciones sensibles | middleware + forms POST | auditor y clientes CSRF | VERIFICADA ESTÁTICAMENTE; suite final pendiente |
| Sin JSON/localStorage/fetch de negocio | runtime nuevo + auditor | búsqueda estática | VERIFICADA ESTÁTICAMENTE |
| ZIP legado fuera del runtime | `respaldo_frontend/` | inventario/hash | VERIFICADA ESTÁTICAMENTE |
| Finance read-only | app base todavía sin modelos funcionales cerrados | P-28 | PENDIENTE |
| Navegación completa por rol | contexto base mínimo | P-29 | PARCIAL |
| Compra de boletos | no expuesta | fase posterior | PENDIENTE |
| Migración MySQL | requirements y configuración listos | repetir suite con MySQL | PENDIENTE SEGUNDA FASE |

## Puerta P-27

P-27 solo queda **cerrado dinámicamente** cuando:

```powershell
.\scripts\verify.ps1
```

termina sin errores y se guardan capturas de productos, eventos, filtros,
formularios, detalle, bloqueo de edición y bloqueo de eliminación.
