# Mapa de interfaz Django — Taller #3 Lotería Binaria

## 1. Objetivo

Este documento traduce las pantallas del frontend legado a la interfaz prevista del Taller #3 con Django y Bootstrap 5.3.

El ZIP se usa solo como referencia de:

- estructura visual;
- navegación;
- dashboards;
- filtros;
- formularios;
- pantallas de detalle.

La fuente de verdad será Django con SQLite primero y MySQL después.

---

# 2. Mapa general de pantallas

| Pantalla legado | Template Django | View prevista | Forms | Modelos |
|---|---|---|---|---|
| `index.html` | `core/home.html` | `home` | — | `LotteryProduct`, `DrawEvent` |
| `login.html` | `accounts/login.html` | login Django | AuthenticationForm | `User` |
| `registro.html` | `accounts/register.html` | `register` | RegistrationForm | `User`, `TermsAcceptance` |
| `elegir-rol.html` | `accounts/choose_mode.html` | `choose_mode` | ModeSelectionForm | Groups + sesión |
| `cliente.html` | `dashboards/client.html` | `client_dashboard` | filtros/acciones | Wallet, Movement, Ticket, Request |
| `vendedor.html` | `dashboards/vendor.html` | `vendor_dashboard` | filtros/acciones | VendorProfile, Wallet, Request |
| `admin.html` | `dashboards/admin.html` | `admin_dashboard` | filtros | todas mediante consultas |
| `sorteo-detalle.html` | `lottery/event_detail.html` | `event_detail` | TicketPurchaseForm | DrawEvent, Ticket |
| `boleto-detalle.html` | `lottery/ticket_detail.html` | `ticket_detail` | — | Ticket, DrawResult |
| `solicitud-detalle.html` | `vendors/request_detail.html` | `request_detail` | ActionForm | ConversionRequest, Assignment |

---

# 3. Templates base y parciales

```text
templates/
├── base.html
├── includes/
│   ├── _navbar.html
│   ├── _messages.html
│   ├── _pagination.html
│   ├── _status_badge.html
│   ├── _empty_state.html
│   └── _confirm_modal.html
├── core/
├── accounts/
├── dashboards/
├── finance/
├── vendors/
└── lottery/
```

## `base.html`

Debe contener:

- Bootstrap 5.3 CSS;
- navbar responsive;
- bloque de mensajes;
- `{% block content %}`;
- footer;
- Bootstrap bundle;
- CSS propio azul/dorado;
- bloque opcional de JavaScript de página.

No debe contener:

- usuario desde `localStorage`;
- rutas `.html`;
- datos JSON;
- lógica de roles en JavaScript.

---

# 4. Navegación pública

## Landing

### Componentes Bootstrap

- `navbar`;
- `container`;
- hero con `row`;
- cards;
- badges;
- botones;
- accordion opcional;
- footer.

### Datos

- productos activos;
- próximos eventos;
- estado de sesión.

### Destinos

- login;
- registro;
- detalle de evento;
- dashboard según sesión.

---

# 5. Interfaz de `accounts`

## Login

### Componentes

- card centrada;
- formulario Bootstrap;
- alertas;
- enlace a registro.

### Retirar

- usuarios demo;
- contraseñas visibles;
- comparación JS.

## Registro

### Componentes

- grid de campos;
- validación server-side;
- checkbox de términos;
- mensajes por campo.

## Elegir modo

### Componentes

- cards por rol;
- formulario POST;
- badge del rol;
- explicación breve.

### Reglas

- solo roles asignados;
- modo en sesión;
- CLIENTE, VENDEDOR y ADMINISTRADOR;
- retirar `CLIENTE_FINANCIERO`.

## CRUD usuarios

```text
accounts/user_list.html
accounts/user_detail.html
accounts/user_form.html
accounts/user_confirm_delete.html
```

### Elementos

- tabla responsive;
- filtros por estado;
- búsqueda;
- paginación;
- badges;
- botón desactivar;
- confirmación.

---

# 6. Dashboard Cliente

## Secciones conservadas

- resumen;
- eventos disponibles;
- wallet;
- movimientos;
- solicitudes;
- boletos;
- información del usuario.

## Secciones adaptadas

### Compra

La tarjeta del evento enlaza al detalle. La compra real ocurre mediante POST y service.

### Wallet

- mostrar REAL y VIRTUAL;
- disponible y reservado;
- movimientos paginados;
- no mostrar inputs editables de saldo.

### Recarga

- simulada 1:1;
- sin tarjeta real;
- sin 5 %.

### Conversión

- 10 %;
- preview visual opcional;
- cálculo final en servidor.

### Solicitudes

- crear solicitud;
- ver estado;
- no cambiar estados directamente.

### Boletos

Conservar filtros:

- por producto;
- por estado;
- por fecha;
- búsqueda por combinación;
- paginación.

---

# 7. Dashboard Vendedor

## Secciones conservadas

- resumen;
- wallets;
- movimientos;
- compra mayorista;
- solicitudes;
- información de usuario.

## Reglas

- compra mayorista 0.90;
- conversión 10 %;
- no compra boletos en modo VENDEDOR;
- solicitudes mediante acciones POST;
- saldo nunca editable.

## CRUD vendedor

Separado del dashboard:

```text
vendors/vendorprofile_list.html
vendors/vendorprofile_detail.html
vendors/vendorprofile_form.html
vendors/vendorprofile_confirm_delete.html
```

---

# 8. Dashboard Administrador

## Secciones conservadas

- resumen;
- usuarios;
- vendedores;
- productos;
- eventos;
- solicitudes;
- movimientos;
- estadísticas.

## Adaptación

Cada sección debe usar vistas Django o enlaces a CRUD reales. No debe renderizar tablas completas desde JavaScript.

### Usuarios

- CRUD protegido;
- desactivación;
- roles mediante permisos/grupos.

### Productos

- Octal, Decimal y Hexadecimal;
- configuración 4/5/6;
- desactivación si tienen eventos.

### Eventos

- CRUD;
- filtros;
- cancelación;
- bloqueo de campos publicados.

### Históricos

Solo lectura:

- movimientos;
- tickets;
- resultados;
- aceptaciones;
- auditoría.

---

# 9. Detalle de evento

## Template

```text
templates/lottery/event_detail.html
```

## Componentes

- encabezado;
- badge de estado;
- producto;
- precio;
- premio;
- apertura/cierre/sorteo;
- reglas 4/5/6;
- formulario de compra;
- mensajes;
- boletos vendidos agregados si aplica.

## JavaScript permitido

- contador visual;
- preview de combinación;
- convertir letras a mayúscula;
- mejorar UX.

## JavaScript no permitido

- decidir cierre real;
- descontar saldo;
- crear ticket;
- validar permisos finales;
- guardar compra.

---

# 10. Detalle de boleto

## Template

```text
templates/lottery/ticket_detail.html
```

## Componentes

- ID;
- combinación;
- evento;
- precio;
- estado de propiedad;
- estado de evaluación;
- premio;
- fecha;
- enlace al evento.

## Regla

No existe botón “reclamar”. El premio o reembolso se acredita mediante servicio.

---

# 11. Detalle de solicitud

## Template

```text
templates/vendors/request_detail.html
```

## Componentes

- cliente;
- monto;
- estado;
- expiración;
- vendedor asignado;
- historial;
- temporizador visual;
- botones según permiso y estado.

## Acciones

- asignar;
- liberar;
- completar;
- cancelar;
- expirar.

Todas por POST y service.

---

# 12. Bootstrap 5.3 aplicado de forma real

| Necesidad | Componente Bootstrap |
|---|---|
| Navegación | `navbar`, `offcanvas` |
| Layout | `container`, `row`, `col-*` |
| Dashboards | `nav-pills`, cards |
| Formularios | `form-control`, `form-select`, validation |
| Tablas | `table`, `table-striped`, `table-responsive` |
| Estados | `badge`, `alert` |
| Confirmaciones | modal |
| Paginación | `pagination` |
| Vacíos | card/alert |
| Responsive | breakpoints Bootstrap |

CSS propio:

- colores azul y dorado;
- logo;
- sombras;
- ajustes de marca;
- pequeños arreglos responsive.

---

# 13. Rutas previstas

```text
/
accounts/login/
accounts/logout/
accounts/register/
accounts/mode/
accounts/users/
accounts/users/<pk>/
vendors/
vendors/<pk>/
vendors/requests/
vendors/requests/<pk>/
lottery/products/
lottery/events/
lottery/events/<pk>/
lottery/events/<pk>/buy/
lottery/tickets/
lottery/tickets/<pk>/
finance/wallets/
finance/movements/
dashboard/client/
dashboard/vendor/
dashboard/admin/
```

Usar siempre `{% url %}`.

---

# 14. Mapeo de filtros heredados

| Filtro legado | Implementación Django |
|---|---|
| Boleto por tipo | GET + queryset por producto |
| Boleto por estado | GET + choices |
| Boleto por fecha | rango GET |
| Usuario por rol | Groups |
| Usuario por estado | filtro del modelo |
| Solicitud por estado | queryset |
| Movimiento por tipo | queryset |
| Evento por producto | queryset |
| Evento por estado | queryset |

Los filtros no deben leer arrays del navegador.

---

# 15. Estados vacíos y errores

Cada listado debe incluir:

- mensaje sin resultados;
- botón para limpiar filtros;
- enlace de regreso;
- error 403;
- error 404;
- formulario con errores;
- mensaje de operación exitosa;
- mensaje de eliminación bloqueada.

---

# 16. Responsive que debe conservarse

Probar:

- 360 px;
- 390 px;
- 768 px;
- 1024 px;
- 1440 px.

Verificar:

- navbar;
- offcanvas;
- formularios;
- tablas;
- botones;
- cards;
- filtros;
- detalles;
- ausencia de scroll horizontal global.

---

# 17. Puerta de salida

El mapa queda aprobado cuando:

- las 10 pantallas tienen destino;
- Bootstrap sustituye el layout principal;
- filtros de boletos se conservan;
- dashboards se conservan;
- detalles se conservan;
- ninguna pantalla depende de JSON o `localStorage`;
- login y roles se resuelven en servidor;
- las operaciones sensibles son POST + service;
- no se generó código.
