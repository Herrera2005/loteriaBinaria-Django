# Matriz de auditoría CRUD — Taller #3 Lotería Binaria

Fecha de revisión: 2026-08-01  
App auditada en esta respuesta: `accounts`  
Base de datos de esta fase: SQLite; la implementación se mantiene portable a MySQL.

## Diagnóstico ejecutivo

El CRUD administrativo de `accounts.User` ya contiene las cinco operaciones evaluables: listar, ver, crear, editar y eliminar/desactivar. Usa formularios Django, permisos por cuenta administrativa activa y modo `ADMINISTRADOR`, plantillas que extienden `base.html`, Bootstrap 5.3, mensajes, CSRF, paginación, búsqueda y pruebas automatizadas.

Se encontró un hueco real: `apps/accounts/tests/test_services.py` ya esperaba el servicio `delete_or_deactivate_user()`, pero `apps/accounts/services.py` no lo contenía y la lógica sensible seguía duplicada dentro de `views.py`. La corrección mínima mueve la baja física/desactivación lógica a un servicio atómico y deja la vista únicamente como coordinadora HTTP.

## Matriz CRUD — `accounts.User`

| Operación | Ruta y nombre | Vista | Formulario | Validaciones | Permisos | Template Bootstrap | Mensaje | Prueba automatizada |
|---|---|---|---|---|---|---|---|---|
| Listar | `/accounts/users/` — `accounts:user_list` | `UserListView` | Consulta GET `q` | Búsqueda por `username`, `email`, `document`, `first_name`, `last_name`; orden por usuario; paginación de 15 | `AdministratorModeRequiredMixin`: autenticado, cuenta activa, `is_staff`, rol `ADMINISTRADOR` asignado y modo activo `ADMINISTRADOR` | `templates/accounts/user_list.html`; card de filtros, `table-responsive`, badges, paginación y estado vacío | No modifica datos | `UserCrudAccessTests`; `test_list_supports_search`; `test_list_is_paginated` |
| Ver detalle | `/accounts/users/<pk>/` — `accounts:user_detail` | `UserDetailView` | No aplica | Obtiene el usuario; precarga grupos y aceptaciones legales | Mismo permiso administrativo | `templates/accounts/user_detail.html`; cards, badges, datos personales, roles, historial legal y acciones | No modifica datos | `test_administrator_mode_can_access_all_crud_pages` y pruebas de acceso |
| Crear | `/accounts/users/create/` — `accounts:user_create` | `UserCreateView` | `UserAdminCreationForm` | Usuario, correo y documento únicos sin distinguir mayúsculas; mayoría de edad; coherencia `status/is_active`; contraseña mediante `UserCreationForm`/`set_password()` | Mismo permiso; un no superusuario no recibe campos reservados de superusuario/permisos | `templates/accounts/user_form.html`; grid, labels, ayuda, errores por campo, CSRF y botones responsive | `Usuario <username> creado correctamente.` | `test_create_hashes_password_and_redirects_to_detail`; pruebas de `UserAdminCreationForm`; `test_crud_post_requires_csrf` |
| Editar | `/accounts/users/<pk>/edit/` — `accounts:user_update` | `UserUpdateView` | `UserAdminChangeForm` | Reutiliza unicidad y mayoría de edad; conserva el hash de contraseña; no superusuario no puede editar cuentas superusuario | Mismo permiso administrativo | `templates/accounts/user_form.html`; Bootstrap, CSRF, errores claros y cancelar | `Usuario <username> actualizado correctamente.` | `test_update_changes_allowed_fields_and_preserves_password`; pruebas de `UserAdminChangeForm` |
| Eliminar / desactivar | `/accounts/users/<pk>/delete/` — `accounts:user_delete` | `UserDeleteDeactivateView` + `delete_or_deactivate_user()` | Confirmación POST | Bloquea propia cuenta y superusuarios; elimina físicamente solo sin historia; con historia desactiva; captura relaciones `PROTECT`; usa `transaction.atomic` y bloqueo `select_for_update()` | Mismo permiso administrativo | `templates/accounts/user_confirm_delete.html`; alerta de acción sensible, explicación de baja física/lógica, CSRF y botón deshabilitado cuando corresponde | Éxito al eliminar; advertencia al desactivar; error al intentar propia cuenta o superusuario | `UserCrudTests`; `UserRemovalServiceTests` |

## Validaciones y seguridad del formulario

| Regla | Estado | Evidencia actual |
|---|---|---|
| `username` único sin distinguir mayúsculas | Cumple | `UserIdentityValidationMixin.clean_username()` y tests de formularios/registro |
| `email` único sin distinguir mayúsculas | Cumple | `clean_email()` y tests |
| `document` único sin distinguir mayúsculas | Cumple | `clean_document()` y tests |
| Mayoría de edad | Cumple | `clean_birth_date()` usando `age_cutoff()` |
| Contraseña nunca se guarda en texto plano | Cumple | `UserAdminCreationForm` hereda de `UserCreationForm`; prueba con `check_password()` |
| Coherencia de estado y acceso | Cumple | formulario rechaza estado no activo con `is_active=True` |
| Protección de historia legal | Cumple | `TermsAcceptance` usa `PROTECT` e inmutabilidad; la baja histórica desactiva |
| Operación sensible fuera de la vista | Corregido | `delete_or_deactivate_user()` en `services.py`, atómico |

## Interfaz y experiencia

| Requisito | Estado | Evidencia |
|---|---|---|
| Base común | Cumple | Los cuatro templates CRUD extienden `base.html` |
| `{% url %}` y `{% static %}` | Cumple | Navegación y recursos mediante tags Django |
| CSRF | Cumple | Crear, editar y eliminar usan `{% csrf_token %}` |
| Messages | Cumple | Crear, editar, eliminar/desactivar y errores sensibles |
| Bootstrap 5.3 real | Cumple | cards, grid, forms, alerts, badges, `table-responsive`, pagination y botones |
| Estado vacío | Cumple | Lista sin resultados; roles y aceptaciones sin registros |
| Confirmación sensible | Cumple | Página de confirmación de eliminación/desactivación |
| Navegación por modo | Cumple | Acceso protegido por backend; no depende de JavaScript |
| Responsive | Pendiente de evidencia manual | La estructura es responsive; deben guardarse capturas en 360, 390, 768, 1024 y 1440 px |

## Correcciones mínimas de esta respuesta

1. `apps/accounts/services.py`
   - Añade `UserRemovalResult`.
   - Añade `user_has_related_history()`.
   - Añade `delete_or_deactivate_user()` con `@transaction.atomic`, `select_for_update()` y tratamiento de `ProtectedError`.

2. `apps/accounts/views.py`
   - Elimina la fórmula de baja/desactivación de la vista.
   - Reutiliza el servicio.
   - Conserva exactamente las rutas, templates y mensajes del CRUD.

3. `apps/accounts/tests/test_services.py`
   - Ya existía y cubre las cuatro ramas necesarias; no requiere cambios.

## Huecos que no se corrigen en esta respuesta

- `vendors` y `lottery` aún no se auditan aquí, porque el trabajo debe hacerse una app por respuesta.
- La prueba responsive necesita capturas manuales; no se declara aprobada hasta obtenerlas.
- El perfil propio es una mejora separada del CRUD administrativo. El ZIP entregado contiene templates de perfil, pero sus rutas no aparecen en `apps/accounts/urls.py`; no se mezcla esa tarea con esta auditoría.

## Puerta de salida de accounts

No continuar con `vendors` hasta confirmar:

- las cinco rutas CRUD responden correctamente;
- un usuario no administrativo recibe 403 o redirección según corresponda;
- la contraseña creada está hasheada;
- duplicados de usuario, correo y documento muestran errores;
- usuario sin historia se elimina;
- usuario con historia se desactiva y conserva aceptaciones;
- propia cuenta y superusuarios permanecen protegidos;
- pruebas de `apps.accounts` terminan en `OK`;
- capturas responsive fueron guardadas.
