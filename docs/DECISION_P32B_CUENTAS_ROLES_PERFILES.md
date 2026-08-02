# P-32B — Matriz exacta de cuentas, roles y perfiles

Fecha: 2026-08-01  
Proyecto: Taller #3 — Lotería Binaria con Django  
Base de datos de esta fase: SQLite; la implementación debe mantenerse portable a MySQL.

## 1. Propósito

Cerrar las ambigüedades entre cuenta, rol, modo activo, `is_staff`,
`is_superuser`, permisos individuales y `VendorProfile` antes de comenzar las
operaciones financieras.

La autorización de negocio se decide en Django mediante:

1. cuenta autenticada;
2. `User.status == ACTIVE`;
3. `User.is_active == True`;
4. Group canónico realmente asignado;
5. `session["active_mode"]` coincidente;
6. requisitos adicionales del recurso o perfil.

Los permisos individuales de Django no sustituyen esta política.

## 2. Matriz de configuración

| Tipo de cuenta | Groups | `is_staff` | `is_superuser` | `VendorProfile` | Modos disponibles | Resultado operativo actual |
|---|---|---:|---:|---|---|---|
| Cliente | `CLIENTE` | No | No | No aplica | CLIENTE | Puede entrar al panel Cliente. Las operaciones financieras y compra de boletos se habilitan en fases posteriores. |
| Vendedor | `VENDEDOR` | No | No | Obligatorio para operar; estado `ACTIVE` | VENDEDOR | Puede seleccionar modo VENDEDOR. Sin perfil se muestra una advertencia y no existen asignaciones operativas. |
| Cliente + Vendedor | `CLIENTE`, `VENDEDOR` | No | No | Obligatorio para operar como Vendedor | CLIENTE / VENDEDOR | Cada modo mantiene navegación y permisos aislados. En CLIENTE conserva funciones completas de Cliente; en VENDEDOR no compra boletos. |
| Administrador de negocio | `ADMINISTRADOR` | Sí para CRUD actuales | No | No aplica | ADMINISTRADOR | El Group y el modo permiten dashboard/auditoría. Los CRUD visuales actuales de Usuarios, Vendedores y Lotería exigen además `is_staff`. |
| Cliente + Administrador | `CLIENTE`, `ADMINISTRADOR` | Sí | No | No aplica | CLIENTE / ADMINISTRADOR | Puede comprar únicamente cuando el modo CLIENTE esté activo; administra únicamente en modo ADMINISTRADOR. |
| Tres roles | `CLIENTE`, `VENDEDOR`, `ADMINISTRADOR` | Sí | No | Obligatorio para operar como Vendedor | Los tres | Debe cambiar de modo mediante POST; no se mezclan capacidades en una misma solicitud. |
| Maestro técnico | Según necesidad | Sí | Sí | Según roles de negocio | Según Groups | Administra `/admin/`. Ser superusuario no asigna automáticamente un modo de negocio. |

## 3. Reglas de la pantalla visual de usuarios

- Solo se muestran los tres Groups canónicos como casillas: `CLIENTE`,
  `VENDEDOR` y `ADMINISTRADOR`.
- No se muestran ni aceptan `user_permissions` ni `is_superuser` desde el panel
  visual.
- Los permisos técnicos individuales permanecen en Django Admin para el
  maestro técnico.
- El formulario visual exige marcar `is_staff` al seleccionar `ADMINISTRADOR` para evitar una cuenta administrativa incompleta: el dashboard/auditoría usan Group+modo, mientras los CRUD actuales de Usuarios, Vendedores y Lotería exigen además staff.
- Seleccionar `VENDEDOR` no crea un `VendorProfile` automáticamente.
- Después de guardar una cuenta con rol VENDEDOR, su detalle debe mostrar:
  - enlace para crear el perfil si no existe; o
  - enlace al perfil existente y su estado.
- Una cuenta no activa no puede operar aunque conserve Groups o perfil.

## 4. Fecha de nacimiento

Todos los formularios de Accounts que usan `<input type="date">` deben:

- renderizar valores existentes con formato ISO `YYYY-MM-DD`;
- aceptar el formato HTML5 enviado por el navegador;
- conservar la fecha si otro campo produce un error;
- rechazar un POST sin fecha porque el campo sigue siendo obligatorio.

La presentación visible puede seguir siendo localizada por el navegador, pero
el atributo HTML `value` debe estar siempre en ISO.

## 5. Separación entre rol VENDEDOR y perfil vendedor

| Elemento | Responsabilidad |
|---|---|
| Group `VENDEDOR` | Autoriza que el modo VENDEDOR pueda seleccionarse. |
| `VendorProfile` | Habilita la operación comercial simulada del vendedor y conserva su estado/historia. |
| Wallets REAL/VIRTUAL | Se provisionan por el flujo existente de roles, pero no reemplazan el perfil vendedor. |
| Permisos individuales | No crean perfil, no asignan modo y no habilitan solicitudes por sí solos. |

## 6. Evidencia automatizada requerida

- formularios de registro, administración, panel visual y perfil renderizan fecha ISO;
- la edición de Django Admin muestra la fecha existente;
- el panel visual usa `CheckboxSelectMultiple` para roles;
- solo aparecen Groups canónicos y en orden CLIENTE, VENDEDOR, ADMINISTRADOR;
- un Group no canónico enviado por POST se rechaza;
- `ADMINISTRADOR` sin `is_staff` se rechaza en el panel visual;
- `is_superuser` y `user_permissions` manipulados por POST no se aplican;
- VENDEDOR sin perfil muestra enlace de creación;
- VENDEDOR con perfil muestra enlace al detalle;
- un POST de perfil sin fecha se rechaza y conserva el valor almacenado.

## 7. Archivos de implementación

- `apps/accounts/forms.py`
- `apps/accounts/views.py`
- `templates/accounts/user_form.html`
- `templates/accounts/user_detail.html`
- `apps/accounts/tests/test_forms.py`
- `apps/accounts/tests/test_views.py`
- `apps/accounts/tests/test_admin.py`

No se modifican modelos, migraciones, `manage.py`, saldos ni operaciones
financieras en P-32B.
