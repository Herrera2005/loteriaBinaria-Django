# Cambios aplicados durante la auditoría P-27

## Código corregido

| Ruta | Cambio |
|---|---|
| `apps/accounts/views.py` | Las eliminaciones con PK inexistente responden 404 en lugar de producir una excepción no controlada. |
| `apps/accounts/tests/test_views.py` | Añadida cobertura del 404 de eliminación. |
| `apps/vendors/views.py` | Las eliminaciones con PK inexistente responden 404. |
| `apps/vendors/tests/test_views.py` | Añadidas pruebas del detalle real de vendedor y del 404. |
| `apps/lottery/models.py` | Reforzada la configuración oficial de productos con eventos y la inmutabilidad crítica de eventos publicados; bloqueados `update()` masivos peligrosos. |
| `apps/lottery/forms.py` | Conserva valores críticos exactos, incluidos microsegundos; protege el estado fuera de Borrador y mantiene el cierre calculado por backend. |
| `apps/lottery/views.py` | Añadidos 404 consistentes, conteos históricos y contexto de eliminación; filtros y paginación conservados. |
| `apps/lottery/tests/test_models.py` | Añadidas pruebas de bypass mediante `save()` y `QuerySet.update()`. |
| `apps/lottery/tests/test_crud.py` | Añadidas pruebas de modo, CSRF, 404, filtros combinados e inmutabilidad; corregida la prueba de filtro que confundía el texto “Decimal” con un registro. |

## Templates corregidos

| Ruta | Cambio |
|---|---|
| `templates/vendors/vendorprofile_detail.html` | Restaurado el detalle de perfil; antes era una copia del listado de solicitudes. |
| `templates/lottery/event_list.html` | Restaurado el listado filtrable/paginado; antes era una copia del formulario. |
| `templates/lottery/product_confirm_delete.html` | CSRF válido, confirmación clara y botón deshabilitado cuando la operación está bloqueada. |
| `templates/lottery/event_confirm_delete.html` | Confirmación sensible, CSRF y regla visual consistente con backend. |
| `templates/lottery/product_detail.html` | Configuración, eventos asociados y acciones permitidas. |
| `templates/lottery/event_detail.html` | Fechas, montos, historia, resultado y eliminación permitida/bloqueada. |
| `templates/403.html`, `templates/404.html` | Integración consistente con la base y recursos static. |

## Entrega y control

- añadido `.gitignore` para excluir secretos, SQLite local, entornos, bytecode y `collectstatic`;
- actualizado `README.md` al estado real P-27;
- actualizadas matriz, inventario y plan siguiente;
- ampliado `scripts/audit_project.py` hasta Accounts, Vendors y Lottery;
- añadida guía de verificación con SQLite temporal;
- inventariadas 167 pruebas automatizadas;
- conservado el ZIP legado fuera del runtime.

## Elementos no implementados deliberadamente

- compra de boletos;
- balances y movimientos funcionales de Finance;
- navegación final completa por rol (P-29);
- MySQL activo (segunda fase);
- pagos reales, tarjetas, API REST, Celery, Redis o microservicios.
