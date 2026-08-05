# Auditoría del ZIP legado — Taller #3 Lotería Binaria con Django

> **DOCUMENTO HISTÓRICO / DE FASE.** Auditoría inicial del ZIP legado; no describe el código Django actual. Para el estado vigente consulte `docs/INDICE_DOCUMENTACION.md`, `README.md` y `docs/MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md`.


## 1. Diagnóstico breve

Se revisaron dos paquetes disponibles:

1. `loteriaBinaria-Django.zip`: contiene únicamente documentación de planificación, referencias y scripts temporales. No contiene todavía HTML, CSS, JavaScript ni JSON del frontend.
2. `Proyecto_HerreraNietoCristhian (6).zip`: contiene el frontend legado que corresponde a la auditoría solicitada.

Por tanto, la auditoría pantalla por pantalla y regla por regla se realizó sobre el segundo paquete, que contiene:

- 10 archivos HTML;
- 3 archivos CSS;
- 9 archivos JavaScript;
- 7 archivos JSON;
- un logo;
- README y listado de estructura.

El frontend legado es navegable y visualmente útil, pero su lógica es demostrativa. Usa JSON, `fetch`, DOM y `localStorage` como fuente de verdad, por lo que no puede trasladarse directamente a Django.

Decisiones obligatorias de adaptación:

- conservar la identidad azul oscuro y dorada;
- conservar dashboards, detalles y filtros de boletos;
- sustituir la navegación estática por URLs Django;
- sustituir JSON y `localStorage` por modelos y consultas;
- sustituir validaciones críticas del navegador por forms y services;
- retirar 5 % de recarga, 15 % de conversión, 75 % de premio, cliente financiero limitado, passwords JSON, Hexadecimal de 4 y reclamo manual;
- mantener recarga simulada 1:1;
- usar conversión VIRTUAL → REAL con 10 %;
- mantener compra mayorista 0.90 REAL por 1.00 VIRTUAL;
- usar Octal 4, Decimal 5 y Hexadecimal 6, todos sin repetición;
- proteger historia mediante `PROTECT`, cancelación o desactivación.

---

# 2. Inventario real del ZIP legado

```text
Proyecto_HerreraNietoCristhian/
├── index.html
├── README.md
├── lista.txt
├── assets/
│   └── img/
│       └── logo-placeholder.png
├── css/
│   ├── animations.css
│   ├── responsive.css
│   └── styles.css
├── data/
│   ├── boletos.json
│   ├── eventos.json
│   ├── movimientos.json
│   ├── solicitudes.json
│   ├── sorteos.json
│   ├── usuarios.json
│   └── wallets.json
├── js/
│   ├── admin.js
│   ├── auth.js
│   ├── cliente.js
│   ├── main.js
│   ├── solicitudes.js
│   ├── sorteos.js
│   ├── utils.js
│   ├── vendedor.js
│   └── wallets.js
└── pages/
    ├── admin.html
    ├── boleto-detalle.html
    ├── cliente.html
    ├── elegir-rol.html
    ├── login.html
    ├── registro.html
    ├── solicitud-detalle.html
    ├── sorteo-detalle.html
    └── vendedor.html
```

---

# 3. Mapa HTML pantalla por pantalla

## 3.1 `index.html`

### Funciones visibles

- landing pública;
- presentación del proyecto;
- botones de login y registro;
- descripción de tipos de lotería;
- acceso a sorteos demo;
- explicación de roles;
- explicación antifraude;
- sección de premios;
- resumen de sesión;
- tarjetas destacadas;
- footer con contacto.

### Elementos útiles

- jerarquía visual clara;
- llamados a la acción;
- identidad azul/dorado;
- tarjetas de productos;
- explicación de roles;
- navegación pública;
- contenido responsive.

### Problemas heredados

- enlaces directos a archivos `.html`;
- sorteos destacados cargados desde JSON;
- resumen de sesión desde `localStorage`;
- explicación de premios dinámicos con regla 75 %;
- textos heredados que no coinciden con el taller.

### Destino Django

- template: `templates/core/home.html`;
- view: `core.views.home`;
- modelos consultados: `LotteryProduct`, `DrawEvent`;
- autenticación: `request.user`;
- navegación: `{% url %}`;
- destacados: queryset Django;
- no usar JavaScript para decidir sesión o roles.

---

## 3.2 `pages/login.html`

### Funciones visibles

- formulario de usuario o correo;
- contraseña;
- mensajes de validación;
- enlace a registro;
- lista de usuarios demo;
- explicación de flujo por rol.

### Problemas heredados

- compara contraseña en texto plano contra `usuarios.json`;
- conserva sesión en `localStorage`;
- expone credenciales demo;
- redirección decidida en JavaScript.

### Destino Django

- template: `templates/accounts/login.html`;
- view: `LoginView` o vista autenticada propia;
- form: autenticación de Django;
- modelo: `accounts.User`;
- sesión: servidor Django;
- errores: mensajes de formulario;
- retirar totalmente usuarios y contraseñas demo visibles.

---

## 3.3 `pages/registro.html`

### Funciones visibles

- nombres;
- apellidos;
- documento;
- fecha de nacimiento;
- correo;
- teléfono;
- username;
- contraseña;
- confirmación;
- aceptación de términos.

### Elementos útiles

- campos coherentes con `User`;
- validación visual;
- aceptación de términos;
- buen punto de partida para Bootstrap.

### Problemas heredados

- usuario nuevo guardado solo en memoria/localStorage;
- contraseña almacenada como texto;
- validación de mayoría de edad solo en JavaScript;
- no existe transacción ni aceptación histórica real.

### Destino Django

- template: `templates/accounts/register.html`;
- form: `RegistrationForm`;
- modelos: `User`, `TermsVersion`, `TermsAcceptance`;
- contraseña: `set_password`;
- mayoría de edad: `clean_birth_date`;
- aceptación: servicio transaccional;
- datos persistidos en SQLite/MySQL.

---

## 3.4 `pages/elegir-rol.html`

### Funciones visibles

- resumen del usuario;
- tarjetas de modo Cliente, Vendedor y Administrador;
- selección de modo;
- redirección al dashboard correspondiente.

### Elementos útiles

- concepto de modo activo;
- tarjetas visuales;
- separación de contextos;
- descripción de capacidades.

### Problemas heredados

- documentación menciona `CLIENTE_FINANCIERO`;
- modo guardado en `localStorage`;
- opciones derivadas de `rolPrincipal`, no de permisos reales;
- puede existir inconsistencia entre rol real y modo activo.

### Destino Django

- template: `templates/accounts/choose_mode.html`;
- view POST: selección de modo;
- roles: Django Groups;
- modo activo: sesión del servidor;
- mostrar solo roles realmente asignados;
- retirar `CLIENTE_FINANCIERO`;
- usar CLIENTE, VENDEDOR y ADMINISTRADOR.

---

## 3.5 `pages/cliente.html`

### Funciones visibles

- resumen;
- compra de boletos;
- wallet y movimientos;
- acreditación de dinero real;
- conversión VIRTUAL → REAL;
- creación de solicitudes;
- envío de dinero;
- boletos comprados;
- filtros por tipo, antigüedad y estado;
- información del usuario.

### Elementos que deben conservarse

- dashboard por secciones;
- filtros de boletos;
- tarjetas de wallet;
- lista de movimientos;
- formulario de compra;
- estados y badges;
- detalle del usuario;
- navegación interna.

### Reglas heredadas incorrectas

- acreditación con tarjeta y comisión 5 %;
- conversión con comisión 15 %;
- cambios en `localStorage`;
- compra y descuento ejecutados en JavaScript;
- transferencias directas desde navegador;
- permisos según valores locales.

### Destino Django

- template: `templates/dashboards/client.html`;
- vistas de resumen y listados;
- forms específicos para operaciones;
- servicios en `finance/services.py`, `vendors/services.py` y `lottery/services.py`;
- movimientos y tickets desde querysets;
- filtros por parámetros GET;
- recarga simulada 1:1;
- conversión con 10 %;
- compra solo en rol CLIENTE + modo CLIENTE;
- no usar tarjetas reales.

---

## 3.6 `pages/vendedor.html`

### Funciones visibles

- resumen;
- wallet;
- movimientos;
- acreditación real;
- compra mayorista;
- conversión;
- retiro simulado;
- solicitudes de clientes;
- envío de virtual;
- información de usuario.

### Elementos que deben conservarse

- dashboard;
- tarjetas de saldo;
- listado y filtro de movimientos;
- listado de solicitudes;
- compra mayorista 0.90;
- detalle de solicitud;
- indicadores de estado.

### Reglas heredadas incorrectas

- recarga con tarjeta y 5 %;
- conversión con 15 %;
- retiro genérico;
- asignaciones y saldos en navegador;
- cambios guardados en `localStorage`;
- lógica repetida entre `vendedor.js`, `wallets.js` y `solicitudes.js`.

### Destino Django

- template: `templates/dashboards/vendor.html`;
- CRUD de `VendorProfile` separado;
- solicitudes consultadas desde modelos;
- acciones POST específicas;
- compra mayorista 0.90 mediante servicio;
- conversión 10 %;
- sin compra de boletos en modo VENDEDOR;
- movimientos read-only.

---

## 3.7 `pages/admin.html`

### Funciones visibles

- resumen general;
- gestión de usuarios;
- filtros por rol y estado;
- gestión de sorteos;
- módulos Octal, Decimal y Hexadecimal;
- solicitudes;
- movimientos globales;
- estadísticas;
- activar/desactivar;
- convertir roles;
- eliminar usuario visualmente.

### Elementos que deben conservarse

- dashboard administrativo;
- filtros;
- tablas;
- módulos separados;
- resumen estadístico;
- consulta global;
- acciones protegidas;
- identidad visual.

### Reglas heredadas incorrectas

- modificación directa de roles en JavaScript;
- eliminación visual con estado `ELIMINADO`;
- configuración guardada en `localStorage`;
- premio con crecimiento 75 %;
- creación de eventos desde navegador;
- estados sin servicios;
- permisos definidos por datos locales.

### Destino Django

- template: `templates/dashboards/admin.html`;
- CRUD `accounts.User`;
- CRUD `VendorProfile`;
- CRUD `LotteryProduct` y `DrawEvent`;
- listados read-only de movimientos, tickets, resultados y auditoría;
- acciones específicas de desactivación/cancelación;
- grupos y permisos Django;
- estadísticas por ORM;
- nunca delete genérico de historia.

---

## 3.8 `pages/sorteo-detalle.html`

### Funciones visibles

- detalle del producto y evento;
- precio y premio;
- programación;
- tiempo restante;
- reglas por tipo;
- compra de boleto;
- validación de número;
- reglas de premio;
- reglas antifraude.

### Elementos que deben conservarse

- detalle rico;
- formulario de compra;
- reglas visibles;
- contador como apoyo visual;
- estados de disponibilidad;
- retorno al dashboard.

### Problemas heredados

- parámetros `id=SOR-*` o `id=EVE-*`;
- consulta de JSON;
- compra y saldo modificados en JavaScript;
- premio 75 %;
- Hexadecimal de 4 en datos;
- validación crítica solo en navegador;
- tiempo del navegador como autoridad.

### Destino Django

- template: `templates/lottery/event_detail.html`;
- URL con PK o slug;
- view: detalle de `DrawEvent`;
- form: `TicketPurchaseForm`;
- service: `purchase_ticket`;
- validación 4/5/6 y no repetición;
- cierre calculado y validado por servidor;
- precio y premio fijos en minor units;
- JavaScript solo para mejorar UX.

---

## 3.9 `pages/boleto-detalle.html`

### Funciones visibles

- información del boleto;
- estados;
- resultado;
- sorteo asociado;
- reglas de premio;
- navegación a boletos.

### Elementos que deben conservarse

- vista de detalle;
- badges de estado;
- relación con evento;
- premio obtenido;
- historial.

### Problemas heredados

- campo `reclamado`;
- premio manualmente reclamable;
- consulta desde JSON/localStorage;
- estados antiguos y demasiado textuales.

### Destino Django

- template: `templates/lottery/ticket_detail.html`;
- view read-only;
- modelo `Ticket`;
- premio acreditado automáticamente al publicar;
- retirar reclamo manual;
- no permitir editar ni eliminar.

---

## 3.10 `pages/solicitud-detalle.html`

### Funciones visibles

- detalle de solicitud;
- monto;
- cliente y vendedor;
- ganancia estimada;
- temporizador de dos minutos;
- bloqueo de botones;
- confirmar;
- cancelar;
- flujo explicado.

### Elementos que deben conservarse

- detalle;
- temporizador informativo;
- estados;
- confirmación explícita;
- explicación de 0.90;
- navegación al panel.

### Problemas heredados

- temporizador controlado por navegador;
- confirmación/cancelación en `localStorage`;
- saldo y asignación modificados en JavaScript;
- lógica duplicada entre módulos;
- expiración simulada.

### Destino Django

- template: `templates/vendors/request_detail.html`;
- view read-only;
- acciones POST;
- service con `transaction.atomic`;
- expiración calculada en servidor;
- temporizador JavaScript solo visual;
- asignación y saldo desde base de datos.

---

# 4. Auditoría CSS

## `css/styles.css`

### Conservar

- paleta azul oscuro y dorado;
- variables visuales;
- tarjetas;
- botones;
- badges;
- alertas;
- tablas;
- sidebar;
- footer;
- jerarquía tipográfica.

### Adaptar

- convertir estilos en complemento de Bootstrap;
- usar variables CSS solo para identidad;
- evitar duplicar `.container`, grid, formularios y botones de Bootstrap;
- mapear clases antiguas a utilidades Bootstrap.

## `css/responsive.css`

### Conservar

- intención mobile-first;
- tratamiento de sidebar;
- menú móvil;
- tablas contenidas;
- ajustes a 360 px.

### Adaptar

- sustituir gran parte por grid Bootstrap, `offcanvas`, `navbar-expand-*`, `table-responsive`;
- conservar solo correcciones específicas.

## `css/animations.css`

### Conservar de forma limitada

- transiciones suaves;
- entrada de tarjetas;
- estados de botones.

### Retirar o reducir

- animaciones que dificulten pruebas;
- efectos duplicados por Bootstrap;
- animaciones que ignoren `prefers-reduced-motion`.

---

# 5. Auditoría JavaScript

| Archivo | Función actual | Decisión |
|---|---|---|
| `utils.js` | fetch JSON, sesión, rutas, render helpers | RETIRAR autoridad; conservar ideas de formato |
| `main.js` | menú, sesión, destacados | ADAPTAR para menú/UX; sesión pasa a Django |
| `auth.js` | login, registro, modos | RETIRAR lógica; reemplazar por Auth/forms |
| `cliente.js` | dashboard y operaciones | ADAPTAR vistas; retirar operaciones locales |
| `vendedor.js` | dashboard, compras, solicitudes | ADAPTAR UI; reglas a services |
| `admin.js` | usuarios, sorteos, estadísticas | ADAPTAR UI; CRUD Django |
| `sorteos.js` | detalle, validación, compra | ADAPTAR validación UX; servidor manda |
| `solicitudes.js` | estados, timers, asignaciones | ADAPTAR timer visual; reglas a services |
| `wallets.js` | saldos, movimientos, fórmulas | RETIRAR autoridad; servicios Django |

## Hallazgos técnicos

- `vendedor.js` declara dos veces `cerrarMenuMovilAppSeguro`.
- `vendedor.js` declara dos veces `actualizarTituloMenuMovilAppSeguro`.
- existe solapamiento funcional entre `cliente.js` y `wallets.js`;
- existe solapamiento funcional entre `vendedor.js`, `wallets.js` y `solicitudes.js`;
- varias funciones escriben directamente colecciones completas en `localStorage`;
- las vistas se renderizan con cadenas HTML construidas en JavaScript;
- permisos, saldos y roles se leen desde el navegador;
- la lógica del servidor está simulada en múltiples archivos.

Conclusión: no conviene migrar estos JavaScript línea por línea. Deben conservarse únicamente interacciones de presentación.

---

# 6. Auditoría JSON

## `usuarios.json`

### Hallazgos

- 6 usuarios;
- contraseñas `123456` en texto plano;
- roles y permisos directos;
- estado;
- banderas como `puedeComprarBoletos`.

### Decisión

RETIRAR como fuente de verdad.

Mapeo:

- `User`;
- Django Groups;
- `VendorProfile`;
- contraseña hash;
- permisos del servidor.

---

## `sorteos.json`

### Hallazgos

- Octal 4;
- Decimal 5;
- Hexadecimal 4;
- porcentaje de acumulación 75;
- distintos minutos de cierre.

### Decisión

ADAPTAR.

Conservar:

- nombres;
- descripciones;
- identidad por producto.

Retirar/corregir:

- Hex 4 → Hex 6;
- 75 %;
- cierres distintos → 10 minutos;
- montos float → minor units.

Mapeo:

- `LotteryProduct`;
- `DrawEvent`.

---

## `eventos.json`

### Hallazgos

- 5 eventos;
- premio actual;
- ventas y boletos;
- estado;
- número ganador incluido.

### Decisión

ADAPTAR.

Mapeo:

- `DrawEvent`;
- `DrawResult`;
- agregados calculados por ORM.

No guardar `numeroGanador` directamente en evento.

---

## `boletos.json`

### Hallazgos

- 7 boletos;
- precio float;
- Hex de 4;
- campo `reclamado`;
- resultado y premio.

### Decisión

ADAPTAR.

Mapeo:

- `Ticket`;
- `DrawResult`;
- `price_minor`;
- `award_minor`.

Retirar reclamo manual.

---

## `wallets.json`

### Hallazgos

- una estructura por usuario con saldos REAL y VIRTUAL juntos;
- valores float;
- reservas;
- ganancias.

### Decisión

ADAPTAR.

Mapeo:

- dos `Wallet` por usuario;
- moneda REAL y VIRTUAL;
- `available_minor`;
- `reserved_minor`.

No copiar saldos de demostración como autoridad.

---

## `movimientos.json`

### Hallazgos

- 10 movimientos;
- 5 % de recarga;
- 15 % de conversión;
- montos float;
- referencias.

### Decisión

ADAPTAR estructura, retirar fórmulas antiguas.

Mapeo:

- `Movement`;
- `operation_id`;
- `amount_minor`;
- crédito/débito;
- descripción;
- referencia lógica en auditoría/servicio.

---

## `solicitudes.json`

### Hallazgos

- un objeto, no una lista;
- estado;
- expiración;
- bloqueo;
- reserva;
- vendedor opcional.

### Decisión

ADAPTAR.

Mapeo:

- `ConversionRequest`;
- `ConversionAssignment`;
- servicios de reserva/asignación/expiración.

---

# 7. Tabla CONSERVAR / ADAPTAR / RETIRAR

| Elemento | Decisión | Motivo |
|---|---|---|
| Identidad azul oscuro/dorado | CONSERVAR | Identidad visual del proyecto |
| Landing y CTA | CONSERVAR | Flujo público útil |
| Dashboards por rol | CONSERVAR | Buena separación visual |
| Tarjetas, badges y alertas | CONSERVAR | Útiles con Bootstrap |
| Filtros de boletos | CONSERVAR | Mejora funcional evaluable |
| Detalles de sorteo, boleto y solicitud | CONSERVAR | Flujos claros |
| Sidebar y menú móvil | ADAPTAR | Usar Bootstrap navbar/offcanvas |
| Tablas administrativas | ADAPTAR | `table-responsive` y ORM |
| Formularios | ADAPTAR | Django Forms + Bootstrap |
| Temporizadores | ADAPTAR | Solo presentación; servidor manda |
| Modo activo | ADAPTAR | Sesión Django |
| Roles | ADAPTAR | Django Groups |
| Wallet visual | ADAPTAR | Dos wallets por moneda |
| Compra mayorista 0.90 | CONSERVAR | Regla vigente |
| Recarga 5 % | RETIRAR | Regla obsoleta; ahora 1:1 |
| Conversión 15 % | RETIRAR | Regla obsoleta; ahora 10 % |
| Premio 75 % | RETIRAR | Premio fijo del taller |
| `CLIENTE_FINANCIERO` | RETIRAR | Solo CLIENTE/VENDEDOR/ADMIN |
| `localStorage` autoritativo | RETIRAR | Django y BD son fuente de verdad |
| passwords en JSON | RETIRAR | Inseguro |
| Hexadecimal de 4 | RETIRAR | Debe ser 6 |
| reclamo manual | RETIRAR | Acreditación automática |
| eliminación visual de usuarios | RETIRAR | Desactivación protegida |
| tarjetas/pagos reales | RETIRAR | Fuera de alcance |
| rutas `.html` | RETIRAR | Usar URL dispatcher |
| render HTML desde JS | RETIRAR | Templates Django |
| datos JSON como catálogo vivo | RETIRAR | Modelos y fixtures controlados |

---

# 8. Reglas heredadas y decisión final

| Regla del ZIP | Estado | Regla del Taller #3 |
|---|---|---|
| Recarga con comisión 5 % | RETIRAR | Recarga REAL simulada 1:1 |
| VIRTUAL → REAL con 15 % | RETIRAR | Comisión 10 % |
| Compra mayorista 0.90 | CONSERVAR | 0.90 REAL por 1.00 VIRTUAL |
| Premio crece con 75 % | RETIRAR | Premio fijo |
| Octal 4 | CONSERVAR | 4 únicos, 0–7 |
| Decimal 5 | CONSERVAR | 5 únicos, 0–9 |
| Hexadecimal 4 | RETIRAR | 6 únicos, 0–9/A–F |
| Reclamo manual | RETIRAR | Acreditación automática |
| Vendedor en modo vendedor no compra | CONSERVAR | Sigue vigente |
| Admin en modo admin no compra | CONSERVAR | Sigue vigente |
| Multirrol en modo cliente compra | ADAPTAR | Solo si tiene rol CLIENTE |
| Sesión en `localStorage` | RETIRAR | Sesión Django |
| Password en JSON | RETIRAR | Hash Django |
| Delete visual | RETIRAR | Desactivar/cancelar/PROTECT |
| Temporizador navegador | ADAPTAR | Servidor determina expiración |

---

# 9. Enlaces y funciones muertas o problemáticas

## Enlaces

- no se encontraron enlaces locales a archivos inexistentes entre las páginas principales;
- todos los HTML referenciados existen;
- `cliente.html` enlaza a `sorteo-detalle.html` sin ID, pero el script elige el primer evento próximo; es un fallback implícito y debe retirarse en Django;
- enlaces con `?id=SOR-*`, `?id=EVE-*`, `?id=BOL-*` y `?id=SOL-*` deben reemplazarse por rutas Django;
- `mailto:` y WhatsApp son externos y opcionales;
- el favicon declara en algunas páginas `image/svg+xml`, pero el archivo real es PNG;
- `lista.txt` menciona `logo-placeholder.svg`, pero el archivo real es `logo-placeholder.png`.

## Funciones duplicadas o solapadas

- funciones de menú seguro duplicadas en `vendedor.js`;
- operaciones de wallet duplicadas entre `wallets.js`, `cliente.js` y `vendedor.js`;
- manejo de solicitudes duplicado entre `solicitudes.js` y `vendedor.js`;
- compra de boletos aparece tanto en `cliente.js` como en `sorteos.js`;
- renderizado de sesión aparece en `main.js`, `auth.js` y `utils.js`;
- múltiples funciones generan IDs en navegador;
- múltiples funciones redondean montos con números flotantes.

## Funciones a retirar completamente

- guardado de colecciones en `localStorage`;
- lectura de usuario y roles desde navegador;
- comparación de password;
- generación de movimientos financieros en navegador;
- modificación de saldos;
- transiciones de solicitudes;
- eliminación visual;
- actualización de configuración de sorteo;
- acreditación manual de premio.

---

# 10. Pruebas documentales de la auditoría

- [ ] Se inventariaron 10 HTML.
- [ ] Se inventariaron 3 CSS.
- [ ] Se inventariaron 9 JS.
- [ ] Se inventariaron 7 JSON.
- [ ] Cada pantalla tiene destino Django.
- [ ] Se retiró 5 %.
- [ ] Se retiró 15 %.
- [ ] Se retiró 75 %.
- [ ] Se retiró cliente financiero limitado.
- [ ] Se retiró `localStorage` como autoridad.
- [ ] Se retiraron passwords JSON.
- [ ] Se corrigió Hex 4 → 6.
- [ ] Se retiró reclamo manual.
- [ ] Se conservaron filtros de boletos.
- [ ] Se conservaron dashboards.
- [ ] Se conservaron detalles.
- [ ] Se identificaron duplicaciones JS.
- [ ] Se identificaron inconsistencias de logo.
- [ ] No se generó código Django.

---

# 11. Puerta de salida

P-08 queda aprobado cuando:

- esta auditoría está guardada;
- el mapa de interfaz está guardado;
- se confirma que el ZIP no será copiado directamente;
- cada pantalla tiene un destino Django;
- las reglas obsoletas están marcadas para retiro;
- Bootstrap 5.3 sustituirá la mayor parte del layout propio;
- no se reutilizarán JSON, passwords ni `localStorage`;
- no se ha generado código.

El siguiente paso es revisar el repositorio real antes de crear el proyecto o modificar archivos.
