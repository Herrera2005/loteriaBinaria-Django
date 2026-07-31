# Plan de implementación por aplicaciones — Taller #3 Lotería Binaria con Django

## 1. Diagnóstico breve

Este plan corresponde exclusivamente al **Taller #3 de Lotería Binaria con Django**.

Orden de autoridad aplicado:

1. enunciado del Taller #3 para forma de entrega;
2. cinco documentos canónicos del MVP Django para reglas de negocio e interfaz;
3. guía docente VideoClub para el procedimiento;
4. ZIP legado únicamente como referencia visual y de flujos.

Decisiones confirmadas:

- primera fase con SQLite;
- segunda fase con MySQL;
- Bootstrap 5.3 como framework principal de interfaz;
- cinco apps canónicas: `accounts`, `core`, `finance`, `vendors` y `lottery`;
- CRUD evaluable en `accounts`, `vendors` y `lottery`;
- login, logout, roles y protección de rutas como mejora adicional;
- usuario personalizado antes de la primera migración general;
- montos enteros en campos `*_minor`;
- reglas críticas en `services.py` con `transaction.atomic`;
- operaciones históricas sin delete genérico;
- sin PostgreSQL, API REST, Celery, Redis, microservicios ni pagos reales.

Contradicciones resueltas:

| Contradicción | Decisión del Taller #3 |
|---|---|
| Documentos canónicos orientados originalmente a PostgreSQL | Adaptación obligatoria SQLite → MySQL |
| ZIP basado en JSON y `localStorage` | Solo referencia visual |
| Reglas antiguas 5 %, 15 %, 75 % y Hexadecimal de 4 | Se descartan |
| Posible eliminación física de historia | Se usa `PROTECT`, desactivación o cancelación |
| Proyecto empresarial completo | Queda fuera del taller |
| CSS propio dominante | Bootstrap 5.3 es la base; CSS solo complementa |

---

# 2. Principios generales de implementación

## 2.1 Orden obligatorio

1. preparar entorno y proyecto;
2. crear `accounts.User`;
3. configurar `AUTH_USER_MODEL`;
4. revisar y ejecutar primera migración;
5. completar `accounts`;
6. completar `core`;
7. completar `finance`;
8. completar `vendors`;
9. completar `lottery`;
10. terminar tres CRUD evaluables;
11. integrar login, roles y modo activo;
12. completar pruebas en SQLite;
13. migrar a MySQL;
14. repetir pruebas y evidencias.

## 2.2 Regla de avance

No avanzar de una etapa si:

- `python manage.py check` falla;
- existen migraciones inconsistentes;
- el CRUD actual no completa crear, listar, detalle, editar y eliminar seguro;
- una vista modifica directamente reglas críticas;
- faltan pruebas básicas;
- existen rutas rotas;
- Bootstrap no se usa realmente;
- hay datos sensibles en JSON, `localStorage` o JavaScript.

## 2.3 Orden interno por app

Cada app se implementará en este orden:

1. `models.py`;
2. migraciones;
3. `admin.py`;
4. `forms.py`;
5. `services.py` si aplica;
6. `views.py`;
7. `urls.py`;
8. templates;
9. tests;
10. evidencia;
11. puerta de salida.

---

# 3. Etapa previa — entorno y esqueleto

## Objetivo

Preparar el proyecto sin ejecutar todavía una migración general.

## Tareas

- crear entorno virtual;
- instalar Django;
- crear proyecto `config`;
- crear carpeta `apps`;
- crear las cinco apps;
- registrar apps;
- configurar templates;
- configurar archivos estáticos;
- dejar SQLite como base activa;
- configurar zona horaria;
- preparar `.env`;
- excluir `.env`;
- definir `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"`.

## Archivos previstos

```text
manage.py
config/settings.py
config/urls.py
apps/__init__.py
apps/accounts/
apps/core/
apps/finance/
apps/vendors/
apps/lottery/
templates/
static/
docs/
```

## Comandos de salida

```powershell
python --version
python -m django --version
python manage.py check
```

## Evidencia

- captura de versión de Python;
- captura de versión de Django;
- estructura del proyecto;
- `python manage.py check` sin errores;
- configuración SQLite visible.

## Puerta de salida

Avanzar únicamente si:

- las cinco apps existen;
- no se ejecutó `migrate`;
- `accounts.User` todavía no ha sido omitido;
- SQLite está activa;
- no existe configuración PostgreSQL.

---

# 4. App `accounts`

## 4.1 Dependencias

Puede depender de:

- Django Auth;
- Django Groups;
- sesiones;
- `core` únicamente para auditoría posterior.

Las demás apps usarán:

```text
settings.AUTH_USER_MODEL
```

No deben importar directamente `User`.

---

## 4.2 Models

### Modelos

- `User`;
- `TermsVersion`;
- `TermsAcceptance`.

### Tareas

- implementar `User` basado en `AbstractUser`;
- agregar `document`, `phone`, `birth_date`, `status`, `created_at`, `updated_at`;
- garantizar unicidad de `username`, `email` y `document`;
- definir `TextChoices` de estado;
- configurar `AUTH_USER_MODEL`;
- implementar términos y aceptaciones;
- usar `PROTECT` para aceptaciones;
- no guardar roles en un campo JSON;
- usar Django Groups para roles.

### Validaciones pendientes de formularios o servicios

- mayoría de edad;
- normalización de correo;
- documento no vacío;
- desactivación segura.

---

## 4.3 Migrations

### Orden

1. revisar `accounts/models.py`;
2. confirmar `AUTH_USER_MODEL`;
3. ejecutar migración inicial solo de `accounts`;
4. revisar SQL;
5. ejecutar migración general.

### Comandos

```powershell
python manage.py makemigrations accounts
python manage.py sqlmigrate accounts 0001
python manage.py migrate
python manage.py showmigrations
```

### Pruebas

- tabla de usuario personalizada creada;
- `AUTH_USER_MODEL` correcto;
- no existe migración anterior con `auth.User` como usuario principal;
- constraints y campos correctos.

---

## 4.4 Admin

### Tareas

- registrar `User` con `UserAdmin` personalizado;
- mostrar username, email, document, status, is_active;
- filtros por status e is_active;
- búsqueda por username, email y document;
- registrar `TermsVersion`;
- registrar `TermsAcceptance` como solo lectura;
- ocultar o bloquear eliminación de aceptaciones.

---

## 4.5 Forms

### Formularios

- registro;
- creación administrativa;
- edición administrativa;
- actualización de perfil;
- términos;
- selección de modo.

### Validaciones

- mayoría de edad;
- correo normalizado;
- duplicados;
- contraseña por mecanismos de Django;
- no permitir estado inválido;
- no permitir autoasignación de rol no autorizado.

---

## 4.6 Views CRUD y acciones

### CRUD evaluable

- lista de usuarios;
- detalle;
- crear;
- editar;
- eliminar seguro o desactivar.

### Acciones

- login;
- logout por POST;
- registro;
- selector de modo;
- cambio de modo;
- cambio de contraseña.

### Reglas

- rutas administrativas protegidas;
- usuario común no accede por URL directa;
- si hay historia, se desactiva;
- las vistas no borran aceptaciones ni auditoría.

---

## 4.7 URLs

Namespace recomendado:

```text
accounts
```

Rutas previstas:

```text
/accounts/login/
/accounts/logout/
/accounts/register/
/accounts/mode/
/accounts/users/
/accounts/users/create/
/accounts/users/<id>/
/accounts/users/<id>/edit/
/accounts/users/<id>/delete/
```

---

## 4.8 Templates

```text
templates/accounts/
├── login.html
├── register.html
├── choose_mode.html
├── user_list.html
├── user_detail.html
├── user_form.html
├── user_confirm_delete.html
├── terms_list.html
└── terms_detail.html
```

### Bootstrap obligatorio

- `form-control`;
- `form-select`;
- `alert`;
- `table-responsive`;
- `pagination`;
- `badge`;
- botones y confirmaciones;
- navegación responsive.

---

## 4.9 Tests

### Modelos

- usuario válido;
- username duplicado;
- email duplicado;
- document duplicado;
- aceptación duplicada;
- representación `__str__`.

### Formularios

- mayoría de edad;
- correo normalizado;
- contraseña segura;
- campos obligatorios.

### Vistas

- login correcto;
- logout por POST;
- usuario no autenticado redirigido;
- usuario sin permiso recibe rechazo;
- CRUD completo;
- desactivación con historia.

---

## 4.10 Evidencia

- migración inicial;
- admin;
- creación de superusuario;
- registro válido e inválido;
- login;
- listado;
- detalle;
- edición;
- desactivación;
- ruta protegida;
- capturas Bootstrap.

## Comando de salida

```powershell
python manage.py check
python manage.py test apps.accounts
```

## Puerta de salida

`accounts` queda aprobado cuando:

- `User` es el usuario activo del proyecto;
- las migraciones funcionan desde base vacía;
- CRUD completo aprobado;
- login y logout funcionan;
- roles base pueden crearse;
- no se borra historia;
- tests pasan.

---

# 5. App `core`

## 5.1 Dependencias

Puede consultar:

- `accounts`;
- `finance`;
- `vendors`;
- `lottery`.

No debe contener reglas de esas apps.

---

## 5.2 Models

### Modelo

- `AuditEvent`.

### Tareas

- modelo append-only;
- actor opcional;
- modo activo;
- acción;
- recurso;
- motivo;
- metadata no sensible;
- fecha;
- `PROTECT` para actor;
- índices por actor, recurso y fecha.

---

## 5.3 Migrations

```powershell
python manage.py makemigrations core
python manage.py sqlmigrate core 0001
python manage.py migrate
```

Verificar:

- tabla creada;
- FK correcta;
- índices creados;
- no hay cascade destructivo.

---

## 5.4 Admin

- registrar auditoría;
- campos de solo lectura;
- filtros por acción, modo y fecha;
- búsqueda por recurso;
- sin botón de eliminación;
- sin edición.

---

## 5.5 Forms

No requiere formulario CRUD de auditoría.

Puede incluir únicamente formularios de búsqueda o filtros.

---

## 5.6 Views y acciones

- landing;
- dashboard cliente;
- dashboard vendedor;
- dashboard administrador;
- acceso denegado;
- lista administrativa de auditoría;
- detalle read-only.

Las vistas solo componen información.

---

## 5.7 URLs

```text
/
/dashboard/
/dashboard/client/
/dashboard/vendor/
/dashboard/admin/
/audit/
```

---

## 5.8 Templates

```text
templates/base.html
templates/includes/_navbar.html
templates/includes/_messages.html
templates/includes/_pagination.html
templates/core/home.html
templates/core/access_denied.html
templates/core/audit_list.html
templates/core/audit_detail.html
templates/dashboards/client.html
templates/dashboards/vendor.html
templates/dashboards/admin.html
```

---

## 5.9 Tests

- landing pública;
- dashboard protegido;
- redirección por modo;
- auditoría visible solo para administrador;
- evento de auditoría no editable;
- template Bootstrap carga correctamente.

---

## 5.10 Evidencia

- landing;
- navbar responsive;
- tres dashboards;
- acceso denegado;
- auditoría read-only;
- móvil 360 px y escritorio.

## Comando de salida

```powershell
python manage.py check
python manage.py test apps.core
```

## Puerta de salida

`core` queda aprobado cuando:

- la navegación funciona;
- los dashboards responden según rol y modo;
- auditoría no se edita ni elimina;
- Bootstrap 5.3 está integrado;
- tests pasan.

---

# 6. App `finance`

## 6.1 Dependencias

Depende de:

- `accounts`;
- `core`.

`vendors` y `lottery` podrán usar servicios de `finance`.

---

## 6.2 Models

### Modelos

- `Wallet`;
- `Movement`.

### Tareas

- una wallet por usuario y moneda;
- monedas REAL y VIRTUAL;
- `available_minor`;
- `reserved_minor`;
- estados;
- saldos no negativos;
- movimientos append-only;
- UUID de operación;
- `PROTECT`.

---

## 6.3 Migrations

```powershell
python manage.py makemigrations finance
python manage.py sqlmigrate finance 0001
python manage.py migrate
```

Verificar:

- unique user + currency;
- checks de no negativos;
- FK con `PROTECT`;
- índices de operación y fecha.

---

## 6.4 Admin

### Wallet

- solo consulta de saldos;
- no editar montos directamente;
- filtros por moneda y estado.

### Movement

- solo lectura;
- búsqueda por operation_id;
- filtros por tipo y dirección;
- sin eliminación.

---

## 6.5 Forms

No usar `ModelForm` genérico para editar wallets.

Formularios futuros:

- recarga simulada;
- conversión;
- compra mayorista.

Solo deben solicitar datos de entrada, no saldos finales.

---

## 6.6 Services

Archivo:

```text
apps/finance/services.py
```

Servicios planificados:

- recarga REAL 1:1;
- conversión VIRTUAL → REAL 90/10;
- compra mayorista 0.90/1.00;
- reserva;
- liberación;
- débito;
- crédito;
- movimiento compensatorio.

Todos con:

```text
transaction.atomic
```

---

## 6.7 Views y acciones

- detalle de wallet propia;
- lista de movimientos;
- detalle;
- consulta administrativa;
- formularios de operación solamente después de probar servicios.

Las vistas:

- validan permisos;
- llaman servicios;
- muestran mensajes;
- no duplican fórmulas.

---

## 6.8 URLs

```text
/finance/wallets/
/finance/movements/
/finance/movements/<id>/
/finance/top-up/
/finance/convert/
```

---

## 6.9 Templates

```text
templates/finance/
├── wallet_detail.html
├── movement_list.html
├── movement_detail.html
├── topup_form.html
├── conversion_form.html
└── operation_result.html
```

---

## 6.10 Tests

### Modelos

- wallet duplicada;
- saldo negativo;
- movement de monto cero;
- FK protegida.

### Servicios

- recarga 1:1;
- conversión 90/10;
- compra 90/100;
- rollback por saldo insuficiente;
- movimientos correlacionados.

### Vistas

- usuario ve solo sus wallets;
- administrador consulta;
- saldo no editable por formulario;
- movimientos no eliminables.

---

## 6.11 Evidencia

- wallets REAL/VIRTUAL;
- historial;
- operación simulada;
- rechazo por saldo insuficiente;
- rollback;
- admin read-only.

## Comando de salida

```powershell
python manage.py check
python manage.py test apps.finance
```

## Puerta de salida

`finance` queda aprobado cuando:

- no existe `float`;
- no se editan saldos directamente;
- movimientos son append-only;
- fórmulas están en servicios;
- pruebas transaccionales pasan;
- no hay pagos reales.

---

# 7. App `vendors`

## 7.1 Dependencias

Depende de:

- `accounts`;
- `finance`;
- `core`.

---

## 7.2 Models

### Modelos

- `VendorProfile`;
- `ConversionRequest`;
- `ConversionAssignment`.

### Tareas

- perfil uno a uno;
- estados;
- solicitud con `amount_minor`;
- UUID de operación;
- expiración;
- asignaciones históricas;
- `PROTECT`;
- una sola asignación activa controlada en servicios.

---

## 7.3 Migrations

```powershell
python manage.py makemigrations vendors
python manage.py sqlmigrate vendors 0001
python manage.py migrate
```

Verificar:

- one-to-one;
- FKs protegidas;
- checks de montos;
- índices de estado y expiración.

---

## 7.4 Admin

### VendorProfile

- listado;
- filtros;
- búsqueda;
- activar, suspender o desactivar mediante acciones controladas.

### Requests y assignments

- solo lectura para estados críticos;
- filtros;
- sin delete;
- sin edición libre.

---

## 7.5 Forms

### CRUD evaluable

- creación de perfil;
- edición de perfil;
- filtros.

### Acciones

- crear solicitud;
- confirmar acción;
- no editar estados con `ModelForm`.

---

## 7.6 Services

Archivo:

```text
apps/vendors/services.py
```

Servicios:

- crear solicitud;
- reservar saldo;
- asignar vendedor;
- liberar asignación;
- completar;
- cancelar;
- expirar;
- completar por plataforma;
- fallar por liquidez.

Todos con transacción y auditoría.

---

## 7.7 Views CRUD y acciones

### CRUD `VendorProfile`

- lista;
- detalle;
- crear;
- editar;
- eliminar seguro o desactivar.

### Solicitudes

- lista administrativa;
- lista del cliente;
- lista del vendedor;
- detalle;
- acciones POST específicas.

No usar `UpdateView` genérico para estados.

---

## 7.8 URLs

```text
/vendors/
/vendors/create/
/vendors/<id>/
/vendors/<id>/edit/
/vendors/<id>/delete/
/vendors/requests/
/vendors/requests/<id>/
/vendors/requests/<id>/assign/
/vendors/requests/<id>/complete/
/vendors/requests/<id>/cancel/
```

---

## 7.9 Templates

```text
templates/vendors/
├── vendorprofile_list.html
├── vendorprofile_detail.html
├── vendorprofile_form.html
├── vendorprofile_confirm_delete.html
├── request_list.html
├── request_detail.html
├── request_form.html
├── request_confirm_action.html
└── assignment_detail.html
```

---

## 7.10 Tests

### CRUD

- crear perfil;
- duplicado one-to-one;
- listar;
- detalle;
- editar;
- eliminar sin historia;
- desactivar con historia.

### Servicios

- reserva;
- asignación;
- una activa;
- expiración;
- completar;
- rollback;
- estados terminales inmutables.

### Permisos

- cliente crea solicitud;
- vendedor activo atiende;
- vendedor suspendido no atiende;
- administrador consulta;
- usuario no autorizado rechazado.

---

## 7.11 Evidencia

- CRUD completo;
- filtros;
- solicitud;
- asignación;
- cambio de estado;
- rechazo no autorizado;
- desactivación protegida;
- pruebas.

## Comando de salida

```powershell
python manage.py check
python manage.py test apps.vendors
```

## Puerta de salida

`vendors` queda aprobado cuando:

- CRUD de `VendorProfile` está completo;
- solicitudes no usan edición genérica;
- existe una sola asignación activa;
- no se borran solicitudes ni asignaciones;
- pruebas y permisos pasan.

---

# 8. App `lottery`

## 8.1 Dependencias

Depende de:

- `accounts`;
- `finance`;
- `core`.

---

## 8.2 Models

### Modelos

- `LotteryProduct`;
- `DrawEvent`;
- `Ticket`;
- `DrawResult`.

### Tareas

- productos 4/5/6;
- símbolos correctos;
- eventos;
- precio y premio `*_minor`;
- cierre diez minutos antes;
- ticket único por evento y combinación;
- resultado uno a uno;
- `PROTECT`.

---

## 8.3 Migrations

```powershell
python manage.py makemigrations lottery
python manage.py sqlmigrate lottery 0001
python manage.py migrate
```

Verificar:

- configuración de productos;
- unique de ticket;
- one-to-one de resultado;
- checks monetarios;
- FKs protegidas.

---

## 8.4 Admin

### Producto

- lista;
- filtros;
- edición controlada;
- desactivación si tiene eventos.

### Evento

- filtros por estado;
- campos críticos read-only después de publicar;
- acción de cancelar;
- sin eliminación de publicados.

### Ticket y resultado

- solo lectura;
- sin delete;
- búsqueda y filtros.

---

## 8.5 Forms

### CRUD evaluable

- producto;
- evento.

### Acciones

- compra de boleto;
- cancelar evento;
- publicar resultado.

Validaciones:

- Octal 4 únicos;
- Decimal 5 únicos;
- Hexadecimal 6 únicos;
- normalización;
- cierre diez minutos antes;
- campos bloqueados después de publicar.

---

## 8.6 Services

Archivo:

```text
apps/lottery/services.py
```

Servicios:

- crear o publicar evento;
- abrir y cerrar ventas;
- comprar boleto;
- validar rol y modo;
- cancelar evento;
- publicar resultado;
- evaluar boletos;
- acreditar premio;
- reembolsar.

Regla de compra:

- cuenta activa;
- rol CLIENTE asignado;
- modo CLIENTE;
- evento abierto;
- saldo suficiente;
- combinación válida y disponible.

En modo VENDEDOR o ADMINISTRADOR no se compra.

---

## 8.7 Views CRUD y acciones

### Producto

- lista;
- detalle;
- crear;
- editar;
- eliminar seguro/desactivar.

### Evento

- lista;
- filtros;
- detalle;
- crear;
- editar borrador;
- eliminar borrador seguro;
- cancelar por POST.

### Ticket y resultado

- lista read-only;
- detalle;
- compra por POST;
- publicación por POST;
- sin CRUD genérico.

---

## 8.8 URLs

```text
/lottery/products/
/lottery/products/create/
/lottery/products/<id>/
/lottery/products/<id>/edit/
/lottery/products/<id>/delete/
/lottery/events/
/lottery/events/create/
/lottery/events/<id>/
/lottery/events/<id>/edit/
/lottery/events/<id>/cancel/
/lottery/tickets/
/lottery/tickets/<id>/
/lottery/events/<id>/buy/
/lottery/events/<id>/publish-result/
```

---

## 8.9 Templates

```text
templates/lottery/
├── product_list.html
├── product_detail.html
├── product_form.html
├── product_confirm_delete.html
├── event_list.html
├── event_detail.html
├── event_form.html
├── event_confirm_delete.html
├── ticket_list.html
├── ticket_detail.html
├── ticket_purchase_form.html
├── result_detail.html
└── result_publish_form.html
```

---

## 8.10 Tests

### Productos

- Octal correcto;
- Decimal correcto;
- Hexadecimal correcto;
- configuración inválida rechazada.

### Eventos

- orden de fechas;
- cierre diez minutos antes;
- precio positivo;
- premio no negativo;
- edición de borrador;
- bloqueo de publicado;
- cancelación.

### Tickets

- 4/5/6;
- símbolos únicos;
- normalización;
- combinación repetida;
- rol CLIENTE;
- modo CLIENTE;
- rechazo modo VENDEDOR;
- rechazo modo ADMINISTRADOR;
- saldo insuficiente;
- compra atómica.

### Resultados

- uno por evento;
- combinación válida;
- inmutable;
- sin delete;
- acreditación y reembolso.

---

## 8.11 Evidencia

- CRUD productos;
- CRUD eventos;
- validaciones;
- compra válida e inválida;
- restricciones por modo;
- cancelación;
- resultado;
- interfaz Bootstrap;
- pruebas.

## Comando de salida

```powershell
python manage.py check
python manage.py test apps.lottery
```

## Puerta de salida

`lottery` queda aprobado cuando:

- CRUD de productos y eventos funciona;
- 4/5/6 está validado;
- eventos publicados están protegidos;
- tickets y resultados no se borran;
- compra solo ocurre en modo CLIENTE;
- pruebas pasan.

---

# 9. Integración de los tres CRUD

## Objetivo

Demostrar la rúbrica con:

1. `accounts.User`;
2. `vendors.VendorProfile`;
3. `lottery.LotteryProduct` y `DrawEvent`.

## Verificación común

Cada CRUD debe incluir:

- crear;
- listar;
- buscar o filtrar;
- detalle;
- editar;
- eliminar seguro;
- permisos;
- validación;
- mensajes;
- Bootstrap;
- pruebas.

## Comando de salida

```powershell
python manage.py check
python manage.py test
```

## Puerta de salida

No avanzar a MySQL si uno de los tres CRUD falla.

---

# 10. Login, roles y modo activo

## Orden

1. crear grupos;
2. asignar permisos;
3. probar login;
4. probar logout POST;
5. selector de modo;
6. redirección a dashboard;
7. protección de rutas;
8. navegación por modo;
9. prueba de URL directa.

## Roles

- CLIENTE;
- VENDEDOR;
- ADMINISTRADOR.

## Regla crítica

Una cuenta multirrol puede comprar si:

- tiene rol CLIENTE;
- está en modo CLIENTE.

No puede comprar si está en modo:

- VENDEDOR;
- ADMINISTRADOR.

## Evidencia

- usuario cliente;
- usuario vendedor;
- usuario administrador;
- usuario multirrol;
- selector;
- ruta bloqueada;
- navegación adaptada.

## Puerta de salida

La mejora queda aprobada cuando los permisos se validan en servidor y no en JavaScript.

---

# 11. Validación completa en SQLite

## Comandos

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python manage.py test
python manage.py runserver
```

## Pruebas manuales

- registro;
- login;
- tres CRUD;
- roles;
- wallets;
- solicitudes;
- productos;
- eventos;
- tickets;
- resultados;
- eliminación protegida;
- responsive.

## Evidencia

- consola limpia;
- admin;
- CRUD;
- formularios válidos e inválidos;
- pruebas;
- responsive 360, 390, 768, 1024 y 1440 px.

## Puerta de salida

SQLite queda aprobada cuando:

- todas las migraciones están aplicadas;
- todas las pruebas pasan;
- no hay errores de consola;
- no hay datos sensibles en navegador;
- tres CRUD y mejora funcionan.

---

# 12. Migración a MySQL

## Dependencias previas

No iniciar hasta aprobar SQLite.

## Tareas

1. respaldar `db.sqlite3`;
2. exportar datos mediante Django si se requiere;
3. instalar driver MySQL;
4. crear base MySQL vacía;
5. configurar `.env`;
6. cambiar settings;
7. ejecutar migraciones desde cero;
8. crear superusuario;
9. importar datos controlados;
10. comparar conteos;
11. repetir pruebas;
12. repetir navegación y CRUD.

## Comandos previstos

```powershell
python manage.py check
python manage.py migrate
python manage.py showmigrations
python manage.py createsuperuser
python manage.py test
python manage.py runserver
```

## Pruebas

- conexión;
- migraciones;
- constraints;
- login;
- tres CRUD;
- eliminación protegida;
- roles;
- transacciones;
- conteos.

## Evidencia

- base activa MySQL;
- tablas creadas por Django;
- migraciones;
- conteos;
- CRUD;
- login;
- tests.

## Puerta de salida

MySQL queda aprobada cuando:

- las mismas migraciones funcionan;
- no se reescribieron migraciones antiguas;
- la base fue creada por Django;
- los tres CRUD pasan;
- login y roles pasan;
- no queda configuración PostgreSQL.

---

# 13. Matriz de evidencia final

| Área | Evidencia mínima |
|---|---|
| Entorno | Python, Django, venv |
| Esqueleto | Cinco apps |
| Accounts | User antes de migrate |
| SQLite | Migraciones y pruebas |
| CRUD 1 | Accounts |
| CRUD 2 | Vendors |
| CRUD 3 | Lottery |
| Bootstrap | Formularios, tablas, navbar, responsive |
| Mejora | Login, logout, roles, modo |
| Finance | Wallets y movimientos protegidos |
| Vendors | Solicitudes y asignaciones |
| Lottery | Productos 4/5/6 y eventos |
| Historial | Sin delete genérico |
| MySQL | Migraciones Django y pruebas |
| Defensa | Explicación de arquitectura y reglas |

---

# 14. Comandos de control por hito

## Después de cada cambio de modelos

```powershell
python manage.py makemigrations --check --dry-run
python manage.py check
```

## Después de cada migración

```powershell
python manage.py showmigrations
python manage.py test apps.NOMBRE_APP
```

## Antes de avanzar de app

```powershell
python manage.py check
python manage.py test
```

---

# 15. Puerta de salida general

P-07 queda aprobado cuando:

- `docs/PLAN_IMPLEMENTACION_APPS.md` está guardado;
- el orden User → SQLite → apps → CRUD → roles → MySQL está claro;
- cada app tiene models, migrations, admin, forms, views, urls, templates, tests y evidencia;
- cada etapa tiene comando y puerta de salida;
- no se ha generado código Django;
- no se ha ejecutado ninguna implementación fuera de fase.

No avanzar si:

- `User` se deja para después de `migrate`;
- MySQL se configura antes de terminar SQLite;
- se implementa todo el proyecto en un solo paso;
- falta uno de los tres CRUD;
- se permite borrar historia;
- las vistas contienen fórmulas o transiciones;
- Bootstrap no es la base real;
- se introduce PostgreSQL o arquitectura empresarial.

El siguiente paso autorizado es **P-08 — Auditoría funcional y visual del ZIP legado**.
