# Plan de aplicaciones Django por módulo — Taller #3 Lotería Binaria

## 1. Diagnóstico y alcance confirmado

Este documento corresponde exclusivamente al Taller #3 de Lotería Binaria con Django.

Decisiones confirmadas:

- SQLite en la primera fase y MySQL en la segunda.
- Bootstrap 5.3 como framework visual.
- Cinco apps canónicas: `accounts`, `core`, `finance`, `vendors` y `lottery`.
- CRUD evaluable en `accounts`, `vendors` y `lottery`.
- Login, roles y modo activo como mejora adicional.
- Usuario personalizado antes de la primera migración general.
- Montos enteros en campos `*_minor`; nunca `float`.
- Reglas críticas en `services.py` con `transaction.atomic`.
- Historial protegido mediante `PROTECT`, cancelación o desactivación lógica.
- Sin PostgreSQL, JSON o `localStorage` como fuente de verdad.
- No se crea una app por tabla.

## 2. Contradicciones resueltas

| Fuente o problema | Decisión del Taller #3 |
|---|---|
| Documentos canónicos originales orientados a PostgreSQL | Se adapta a SQLite → MySQL |
| ZIP basado en JSON y `localStorage` | Solo se conserva como referencia visual |
| CSS propio del frontend antiguo | Bootstrap 5.3 será la base; CSS solo complementa |
| Eliminación genérica de registros | Se reemplaza por `PROTECT`, desactivación o cancelación |
| Reglas antiguas 5 %, 15 %, 75 % y Hex de 4 | Se retiran |
| Proyecto empresarial completo | Queda fuera del alcance |

---

# 3. Resumen de las cinco apps

| App | Responsabilidad | Modelos base | Tipo de desarrollo |
|---|---|---|---|
| `accounts` | Identidad, términos, autenticación, roles y modos | `User`, `TermsVersion`, `TermsAcceptance` | CRUD evaluable + autenticación |
| `core` | Landing, dashboards, navegación y auditoría | `AuditEvent` | Páginas y consultas |
| `finance` | Wallets y movimientos simulados | `Wallet`, `Movement` | Consultas y servicios protegidos |
| `vendors` | Perfil vendedor y solicitudes Cliente–Vendedor | `VendorProfile`, `ConversionRequest`, `ConversionAssignment` | CRUD evaluable + flujo protegido |
| `lottery` | Productos, eventos, boletos y resultados | `LotteryProduct`, `DrawEvent`, `Ticket`, `DrawResult` | CRUD evaluable + registros protegidos |

Los tres CRUD completos para la rúbrica serán:

1. `accounts`
2. `vendors`
3. `lottery`

---

# 4. App `accounts`

## Responsabilidad

- usuario personalizado;
- registro, login y logout;
- cambio de contraseña;
- datos personales;
- estado de cuenta;
- versiones y aceptaciones de términos;
- grupos CLIENTE, VENDEDOR y ADMINISTRADOR;
- selección de modo activo;
- administración de usuarios.

## Modelos

### `User`

Basado en `AbstractUser`.

Campos mínimos:

- `username`;
- `email`;
- `document`;
- `phone`;
- `birth_date`;
- `status`;
- `is_active`;
- `created_at`;
- `updated_at`.

Reglas:

- `username`, `email` y `document` únicos;
- mayoría de edad validada;
- contraseñas administradas por Django;
- debe definirse antes de cualquier migración general.

### `TermsVersion`

- `kind`;
- `version`;
- `title`;
- `content`;
- `effective_at`;
- `is_active`;
- `created_at`.

Reglas:

- `kind + version` únicos;
- una versión aceptada no se modifica;
- una actualización crea una nueva versión.

### `TermsAcceptance`

- `user`;
- `terms_version`;
- `accepted_at`;
- `ip_address`.

Reglas:

- `user + terms_version` únicos;
- historial inmutable;
- nunca se elimina.

## Vistas principales

- registro;
- login;
- logout por POST;
- cambio de contraseña;
- selector de modo;
- cambio de modo por POST;
- lista administrativa de usuarios;
- detalle;
- creación;
- edición;
- desactivación o eliminación protegida;
- lista y detalle de términos.

## Templates

```text
templates/accounts/
├── login.html
├── register.html
├── password_change.html
├── choose_mode.html
├── user_list.html
├── user_detail.html
├── user_form.html
├── user_confirm_delete.html
├── terms_list.html
├── terms_detail.html
└── terms_form.html
```

## Dependencias permitidas

- Django Auth;
- Django Groups;
- sesiones;
- `core` para auditoría;
- `settings.AUTH_USER_MODEL` como referencia desde otras apps.

## No debe contener

- cálculos financieros;
- cambios directos de saldo;
- productos o eventos;
- compra de boletos;
- solicitudes Cliente–Vendedor;
- contraseñas visibles;
- roles en `localStorage`.

## CRUD evaluable

| Operación | Implementación |
|---|---|
| Crear | Usuario con contraseña segura |
| Listar | Búsqueda y paginación |
| Ver | Detalle |
| Editar | Campos permitidos |
| Eliminar | Borrar solo sin historia; si existe, desactivar |

## Eliminación protegida

Si el usuario tiene wallets, movimientos, perfil vendedor, solicitudes, boletos, resultados, aceptaciones o auditoría:

```text
status = DISABLED
is_active = False
```

No se elimina físicamente.

---

# 5. App `core`

## Responsabilidad

- landing;
- navegación común;
- dashboards;
- mensajes;
- páginas de error;
- utilidades transversales;
- redirección posterior al login;
- auditoría.

## Modelo

### `AuditEvent`

Campos conceptuales:

- actor;
- modo activo;
- acción;
- tipo e identificador del recurso;
- motivo;
- metadata no sensible;
- fecha.

Reglas:

- append-only;
- sin secretos;
- sin edición;
- sin eliminación.

## Vistas principales

- página principal;
- dashboard Cliente;
- dashboard Vendedor;
- dashboard Administrador;
- acceso denegado;
- auditoría administrativa;
- páginas 404 y 500.

## Templates

```text
templates/core/
├── home.html
├── access_denied.html
├── audit_list.html
└── audit_detail.html

templates/dashboards/
├── client.html
├── vendor.html
└── admin.html

templates/includes/
├── _messages.html
├── _navbar.html
└── _pagination.html
```

## Dependencias permitidas

Puede consultar:

- `accounts`;
- `finance`;
- `vendors`;
- `lottery`.

Solo para construir dashboards, navegación y resúmenes.

## No debe contener

- reglas monetarias;
- transiciones de solicitudes;
- compra de boletos;
- publicación de resultados;
- modelos duplicados de otras apps;
- CRUD destructivo de auditoría.

## Eliminación protegida

`AuditEvent` nunca se elimina.

`core` no demuestra un CRUD completo para la rúbrica.

---

# 6. App `finance`

## Responsabilidad

- wallets REAL y VIRTUAL;
- saldo disponible y reservado;
- movimientos;
- recarga REAL simulada 1:1;
- conversión VIRTUAL → REAL con 10 %;
- compra mayorista a 0.90 REAL por 1.00 VIRTUAL;
- futuras operaciones financieras autorizadas.

## Modelos

### `Wallet`

- usuario;
- moneda;
- `available_minor`;
- `reserved_minor`;
- estado;
- fechas.

Reglas:

- `user + currency` únicos;
- saldos no negativos;
- REAL y VIRTUAL separados;
- nunca `float`.

### `Movement`

- wallet;
- `operation_id`;
- tipo;
- dirección;
- `amount_minor`;
- `balance_after_minor`;
- descripción;
- fecha.

Reglas:

- `amount_minor > 0`;
- append-only;
- no se edita;
- no se elimina;
- una corrección usa movimiento compensatorio.

## Vistas principales

- wallet propia;
- movimientos paginados;
- detalle de movimiento;
- consulta administrativa;
- formularios específicos de operación solo después de aprobar servicios.

## Templates

```text
templates/finance/
├── wallet_detail.html
├── movement_list.html
├── movement_detail.html
├── topup_form.html
├── conversion_form.html
└── operation_result.html
```

## Dependencias permitidas

- `accounts.User`;
- `core.AuditEvent`;
- servicios propios.

`vendors` y `lottery` podrán invocar servicios financieros públicos, pero nunca modificar wallets directamente.

## No debe contener

- autenticación base;
- HTML específico de vendedores;
- reglas de combinaciones;
- publicación de resultados;
- edición genérica de saldos;
- borrado de movimientos;
- pagos reales o tarjetas.

## Servicios

Las reglas críticas vivirán en:

```text
apps/finance/services.py
```

Con:

- `transaction.atomic`;
- montos enteros;
- validaciones del servidor;
- movimientos correlacionados;
- rollback ante error.

## Eliminación protegida

- una wallet con movimientos no se borra;
- puede pasar a `BLOCKED` o `CLOSED`;
- `Movement` nunca se elimina.

`finance` no demuestra CRUD completo para la rúbrica.

---

# 7. App `vendors`

## Responsabilidad

- perfil vendedor;
- estado del vendedor;
- solicitudes Cliente–Vendedor;
- asignaciones;
- expiraciones;
- finalizaciones;
- futuras acciones autorizadas.

## Modelos

### `VendorProfile`

- relación uno a uno con `User`;
- estado;
- fecha de activación;
- fechas.

Estados:

- `PENDING`;
- `ACTIVE`;
- `SUSPENDED`;
- `DISABLED`.

### `ConversionRequest`

- cliente;
- `operation_id`;
- `amount_minor`;
- estado;
- expiración;
- finalización;
- fechas.

Estados:

- `PENDING`;
- `IN_PROGRESS`;
- `COMPLETED_BY_VENDOR`;
- `COMPLETED_BY_PLATFORM`;
- `CANCELLED`;
- `EXPIRED`;
- `FAILED_LIQUIDITY`.

### `ConversionAssignment`

- solicitud;
- vendedor;
- estado;
- fecha de asignación;
- liberación;
- finalización.

Reglas:

- conserva el historial;
- solo una asignación activa por solicitud;
- la regla activa se controla en servicio para mantener portabilidad SQLite/MySQL.

## Vistas principales

### CRUD `VendorProfile`

- lista con filtros;
- detalle;
- creación;
- edición;
- eliminación o desactivación protegida.

### Solicitudes

- lista administrativa read-only;
- lista elegible para vendedor;
- detalle;
- acciones POST específicas para asignar, liberar, completar, cancelar o expirar.

No habrá `UpdateView` genérico para transiciones.

## Templates

```text
templates/vendors/
├── vendorprofile_list.html
├── vendorprofile_detail.html
├── vendorprofile_form.html
├── vendorprofile_confirm_delete.html
├── request_list.html
├── request_detail.html
├── request_confirm_action.html
└── assignment_detail.html
```

## Dependencias permitidas

- `accounts.User`;
- `finance` mediante servicios;
- `core.AuditEvent`.

## No debe contener

- autenticación base;
- definición del usuario;
- productos o resultados;
- compra de boletos;
- cambios directos de wallet;
- estados editables mediante formularios genéricos;
- fórmulas duplicadas de `finance`.

## CRUD evaluable

| Operación | Implementación |
|---|---|
| Crear | Perfil para usuario válido |
| Listar | Filtros y paginación |
| Ver | Detalle |
| Editar | Campos permitidos |
| Eliminar | Borrar sin historia; en otro caso, desactivar |

## Eliminación protegida

Si el perfil tiene solicitudes, asignaciones, compras, movimientos o auditoría:

```text
status = DISABLED
```

`ConversionRequest` y `ConversionAssignment` nunca se borran.

---

# 8. App `lottery`

## Responsabilidad

- productos Octal, Decimal y Hexadecimal;
- eventos;
- fechas;
- precio;
- premio fijo;
- boletos;
- combinaciones;
- resultados;
- cancelaciones;
- futura compra de boletos mediante servicio.

## Modelos

### `LotteryProduct`

| Código | Símbolos | Cantidad |
|---|---|---:|
| `OCTAL` | `0-7` | 4 únicos |
| `DECIMAL` | `0-9` | 5 únicos |
| `HEXADECIMAL` | `0-9A-F` | 6 únicos |

### `DrawEvent`

- producto;
- nombre;
- apertura;
- cierre;
- sorteo;
- `price_minor`;
- `prize_minor`;
- estado;
- motivo de cancelación;
- fechas.

Reglas:

- cierre exactamente diez minutos antes;
- precio positivo;
- premio no negativo;
- campos críticos bloqueados después de publicar.

### `Ticket`

- usuario;
- evento;
- `operation_id`;
- combinación normalizada;
- precio;
- estados;
- premio;
- fecha.

Reglas:

- combinación única por evento;
- compra solo mediante servicio;
- sin eliminación.

### `DrawResult`

- evento;
- combinación ganadora;
- administrador;
- motivo;
- fecha.

Reglas:

- un resultado por evento;
- inmutable;
- sin eliminación.

## Vistas principales

### CRUD de productos

- lista;
- detalle;
- crear;
- editar;
- eliminar o desactivar protegido.

### CRUD de eventos

- lista y filtros;
- detalle;
- crear;
- editar mientras sea permitido;
- eliminar solo borradores seguros;
- cancelar mediante acción protegida.

### Boletos y resultados

- listas read-only;
- detalles;
- compra por POST y servicio;
- publicación mediante acción específica;
- sin CRUD genérico.

## Templates

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

## Dependencias permitidas

- `accounts.User`;
- `finance` mediante servicios;
- `core.AuditEvent`.

## No debe contener

- autenticación base;
- credenciales;
- configuración de hosting;
- cálculos financieros duplicados;
- edición directa de wallets;
- JSON o `localStorage` como fuente de verdad;
- Hexadecimal de 4 símbolos;
- crecimiento de premio del 75 %;
- borrado de tickets o resultados.

## CRUD evaluable

El tercer CRUD se demostrará con `LotteryProduct` y `DrawEvent`.

| Operación | Producto | Evento |
|---|---|---|
| Crear | Sí | Sí |
| Listar | Sí | Sí |
| Ver | Sí | Sí |
| Editar | Sí, con reglas | Solo mientras sea permitido |
| Eliminar | Desactivar si tiene eventos | Solo borrador sin historia |

## Eliminación protegida

### Producto

- sin eventos: puede eliminarse;
- con eventos: se desactiva.

### Evento

Solo se elimina físicamente si:

- está en `DRAFT`;
- no tiene tickets;
- no tiene resultado;
- no tiene movimientos relacionados.

En otro caso se cancela.

### Ticket y resultado

Nunca se eliminan.

---

# 9. Matriz de dependencias permitidas

| App | Puede depender de | Uso permitido |
|---|---|---|
| `accounts` | Django Auth y `core` mínimo | Identidad y auditoría |
| `core` | Todas mediante consultas | Dashboards y navegación |
| `finance` | `accounts`, `core` | Wallets y auditoría |
| `vendors` | `accounts`, `finance`, `core` | Perfil, solicitudes y operaciones |
| `lottery` | `accounts`, `finance`, `core` | Propiedad, cobros, premios y auditoría |

Reglas para evitar acoplamiento:

- usar `settings.AUTH_USER_MODEL`;
- evitar imports circulares;
- no importar views entre apps;
- no duplicar servicios;
- no modificar directamente modelos de otra app;
- usar namespaces de URLs;
- mantener templates dentro de su módulo.

---

# 10. Matriz de los tres CRUD

| App | Entidad evaluable | Crear | Listar | Detalle | Editar | Eliminar seguro |
|---|---|---:|---:|---:|---:|---:|
| `accounts` | `User` | Sí | Sí | Sí | Sí | Sí |
| `vendors` | `VendorProfile` | Sí | Sí | Sí | Sí | Sí |
| `lottery` | `LotteryProduct` / `DrawEvent` | Sí | Sí | Sí | Sí | Sí |

La operación “D” puede cumplirse mediante:

- eliminación física si no hay historia;
- desactivación;
- cancelación;
- bloqueo por `PROTECT`;
- mensaje claro al usuario.

---

# 11. Registros sin delete genérico

No se creará `DeleteView` genérico para:

- `TermsAcceptance`;
- `AuditEvent`;
- `Movement`;
- `ConversionRequest`;
- `ConversionAssignment`;
- `Ticket`;
- `DrawResult`.

Tampoco se borrarán libremente:

- usuarios con historia;
- wallets con movimientos;
- perfiles con solicitudes;
- productos con eventos;
- eventos publicados o con boletos.

---

# 12. Orden de implementación

1. `accounts.User`.
2. Configurar `AUTH_USER_MODEL`.
3. `TermsVersion` y `TermsAcceptance`.
4. Primera migración de `accounts`.
5. Migración general SQLite.
6. `core.AuditEvent`.
7. `finance.Wallet` y `Movement`.
8. `vendors.VendorProfile`.
9. `ConversionRequest` y `ConversionAssignment`.
10. `LotteryProduct` y `DrawEvent`.
11. `Ticket` y `DrawResult`.
12. CRUD `accounts`.
13. CRUD `vendors`.
14. CRUD `lottery`.
15. Login, grupos y modo activo.
16. Servicios mínimos.
17. Pruebas completas en SQLite.
18. Migración a MySQL.
19. Repetición de CRUD, login y pruebas.

---

# 13. Estructura prevista por app

```text
apps/<app>/
├── models.py
├── forms.py
├── views.py
├── urls.py
├── admin.py
├── services.py
└── tests/
```

En `accounts` podrán añadirse:

```text
policies.py
decorators.py
context_processors.py
```

Esta es una planificación; los archivos no deben crearse todos todavía.

---

# 14. Comandos de esta fase

P-05 es documental.

Crear la carpeta si no existe:

```powershell
New-Item -ItemType Directory -Force docs
```

Archivo esperado:

```text
docs/PLAN_APPS.md
```

No ejecutar todavía:

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

---

# 15. Pruebas documentales

- [ ] Existen exactamente cinco apps.
- [ ] No se propone una app por tabla.
- [ ] `accounts` administra identidad y autenticación.
- [ ] `core` administra landing, dashboards y auditoría.
- [ ] `finance` administra wallets y movimientos.
- [ ] `vendors` administra perfiles y solicitudes.
- [ ] `lottery` administra productos, eventos, boletos y resultados.
- [ ] Se identifican los tres CRUD evaluables.
- [ ] `User` se implementa antes de migrar.
- [ ] No se usan montos `float`.
- [ ] Las reglas críticas se reservan para servicios.
- [ ] No hay delete genérico de historia.
- [ ] No se duplican reglas monetarias en views.
- [ ] No se usa JSON ni `localStorage` como fuente de verdad.
- [ ] El plan es portable SQLite/MySQL.

---

# 16. Puerta de salida

P-05 queda aprobado cuando:

- `docs/PLAN_APPS.md` está guardado;
- se aprueban las cinco responsabilidades;
- los CRUD evaluables son `accounts`, `vendors` y `lottery`;
- `core` y `finance` no tienen CRUD destructivo;
- las dependencias no producen imports circulares;
- la eliminación protegida está definida;
- no se han creado modelos ni migraciones.

No avanzar si:

- se propone una app por tabla;
- se mezcla finanzas dentro de views de `lottery`;
- se define el usuario después de migrar;
- se permite borrar movimientos, tickets, resultados, aceptaciones o auditoría;
- se usa PostgreSQL;
- se intenta implementar todas las apps a la vez.

El siguiente paso autorizado es **P-06 — Models.py consolidado de referencia**.
