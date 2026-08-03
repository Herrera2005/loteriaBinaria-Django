# Plan archivo por archivo para migrar el ZIP legado a Django

> **DOCUMENTO HISTÓRICO / DE FASE.** Plan previo a la implementación; no sustituye al inventario ni al mapa actual. Para el estado vigente consulte `docs/INDICE_DOCUMENTACION.md`, `README.md` y `docs/MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md`.


## 1. Alcance y fuente revisada

El archivo `respaldo_frontend.zip` recibido contiene documentación, evidencias y archivos de planificación, pero no contiene los HTML, CSS, JavaScript ni JSON del frontend legado.

Para este plan se revisó el respaldo visual real:

```text
Proyecto_HerreraNietoCristhian (6).zip
```

También se tomó como guía el mapa P-08:

```text
docs/MAPA_INTERFAZ.md
docs/AUDITORIA_ZIP_TALLER3.md
```

El ZIP legado se conserva sin modificaciones ni eliminación. Su función es únicamente servir como referencia visual y de flujo.

## 2. Reglas generales de migración

1. Toda página Django debe extender `templates/base.html`.
2. Toda navegación debe usar `{% url %}` o URLs calculadas por el backend.
3. Los recursos propios deben cargarse con `{% static %}`.
4. Los formularios que cambian estado usan `POST` y `{% csrf_token %}`.
5. Los filtros y búsquedas usan `GET`.
6. Los datos proceden de modelos, formularios, servicios y contexto Django.
7. Se elimina `localStorage` como fuente de verdad.
8. Se elimina `fetch()` a archivos JSON.
9. Se eliminan credenciales demo visibles y contraseñas en texto plano.
10. Se eliminan enlaces `pages/*.html`.
11. JavaScript queda limitado a comportamiento visual:
    - abrir/cerrar componentes;
    - confirmaciones visuales;
    - previews no autoritativos;
    - accesibilidad;
    - mejora progresiva.
12. Las operaciones críticas se procesan en vistas y `services.py`.
13. Se conserva el ZIP legado en `respaldo_frontend/` o fuera del árbol desplegable.
14. No se copia al sistema final ninguna regla obsoleta:
    - recarga 5 %;
    - conversión 15 %;
    - premio 75 %;
    - Hexadecimal de 4 símbolos;
    - `CLIENTE_FINANCIERO`;
    - compra permitida por variables del navegador.

---

# 3. Plan de migración HTML

| Archivo legado | Destino Django | Acción | Datos/backend necesarios |
|---|---|---|---|
| `index.html` | `templates/core/home.html` | Migrar estructura visual pública. Retirar sesión, destacados y enlaces resueltos por JS. | Productos activos, eventos destacados, `request.user`, URLs reales |
| `pages/login.html` | `templates/accounts/login.html` | Migrar formulario visual. Retirar lista de usuarios demo y contraseña `123456`. | `AuthenticationForm`, mensajes Django |
| `pages/registro.html` | `templates/accounts/register.html` | Migrar campos y layout. Validaciones pasan al formulario y servicio. | `RegistrationForm`, términos activos |
| `pages/elegir-rol.html` | `templates/accounts/choose_mode.html` | Convertir tarjetas a formulario POST. Mostrar solo grupos asignados. | `assigned_modes`, `ModeSelectionForm`, sesión Django |
| `pages/cliente.html` | `templates/dashboards/client.html` | Migrar dashboard, filtros, cards y tablas. Eliminar edición de saldos y operaciones JS. | Wallets, movimientos, boletos, eventos, solicitudes y URLs calculadas |
| `pages/vendedor.html` | `templates/dashboards/vendor.html` | Migrar dashboard y solicitudes. Eliminar compra de boletos y cálculos autoritativos JS. | Perfil vendedor, wallets, movimientos, solicitudes |
| `pages/admin.html` | `templates/dashboards/admin.html` | Migrar resumen y módulos. Retirar edición visual de usuarios/sorteos desde JS. | Conteos, eventos, solicitudes, enlaces de admin |
| `pages/sorteo-detalle.html` | `templates/lottery/event_detail.html` | Migrar detalle y formulario de compra. Corregir Hexadecimal a 6 símbolos únicos. | `DrawEvent`, `TicketPurchaseForm`, permisos backend |
| `pages/boleto-detalle.html` | `templates/lottery/ticket_detail.html` | Migrar detalle de boleto y resultado. Retirar reclamo visual/manual. | `Ticket`, `DrawResult`, estado calculado |
| `pages/solicitud-detalle.html` | `templates/vendors/request_detail.html` | Migrar detalle, historial y botones permitidos. Acciones deben ser POST. | `ConversionRequest`, asignación, formularios de acción |

## 3.1 Parciales comunes a extraer

| Elemento repetido del legado | Destino recomendado |
|---|---|
| Cabecera y navegación | `templates/base.html` |
| Mensajes | `templates/includes/_messages.html` |
| Estados vacíos | `templates/includes/_empty_state.html` |
| Paginación | `templates/includes/_pagination.html` |
| Badge de estado | `templates/includes/_status_badge.html` |
| Confirmación de acción sensible | `templates/includes/_confirm_modal.html` |
| Resumen de wallet | `templates/finance/includes/_wallet_summary.html` |
| Tabla de movimientos | `templates/finance/includes/_movement_table.html` |
| Tarjeta de evento | `templates/lottery/includes/_event_card.html` |

No se deben crear estos parciales hasta que el módulo correspondiente sea trabajado y existan los contextos reales.

---

# 4. Plan de migración CSS

| Archivo legado | Destino | Clasificación | Acción |
|---|---|---|---|
| `css/styles.css` | `static/css/app.css` | Conservar parcialmente | Extraer paleta azul/dorada, marca y detalles visuales. Reemplazar layout propio por Bootstrap |
| `css/responsive.css` | No copiar como archivo independiente | Retirar/reabsorber | Traducir solo ajustes necesarios a grid y breakpoints Bootstrap; evitar duplicar sistema responsive |
| `css/animations.css` | `static/css/app.css` o módulo posterior | Conservar solo UI | Mantener animaciones pequeñas y respetar `prefers-reduced-motion`; retirar animaciones que oculten información |

## Reglas CSS

- Bootstrap controla grid, navbar, offcanvas, cards, forms, tablas, paginación y modales.
- `app.css` solo complementa identidad, foco, contraste, objetivos táctiles y pequeños ajustes.
- No copiar clases que imiten `.row`, `.col-*`, `.btn`, `.card`, `.modal` o `.table-responsive`.
- No fijar la barra de forma que cubra contenido.
- Mantener pruebas a 360, 390, 768, 1024 y 1440 px.

---

# 5. Plan de migración de imágenes

| Recurso legado | Destino | Acción |
|---|---|---|
| `assets/img/logo-placeholder.png` | `static/img/logo-placeholder.png` | Conservar como referencia visual temporal |
| Futuro logo definitivo | `static/img/logo-loteria-binaria.png` o `.svg` | Sustituir solo cuando exista recurso aprobado |

El logo no contiene lógica y puede copiarse. El ZIP original no debe eliminarse.

---

# 6. Plan JavaScript archivo por archivo

## 6.1 `js/main.js`

**Clasificación:** conservar solo UI.

### Conservar/adaptar

- cierre y apertura segura de navegación móvil, solo si Bootstrap no lo cubre;
- enfoque y teclado;
- confirmaciones visuales;
- mejora progresiva;
- cierre opcional de mensajes.

### Retirar

- `renderizarResumenSesion`;
- `renderizarAccionesSesion`;
- lectura de usuario o rol desde `localStorage`;
- `cargarSorteosDestacados`;
- `cargarPremiosDestacados`;
- redirecciones a `pages/*.html`;
- tarjetas navegables mediante `data-url` cuando puede usarse un `<a>` real.

### Destino

```text
static/js/app.js
```

`app.js` debe ser pequeño y no contener reglas de negocio.

---

## 6.2 `js/auth.js`

**Clasificación:** reescribir como POST Django y retirar casi todo el archivo.

### Pasar a Django

- autenticación → `LoginView`/formulario Django;
- registro → `RegistrationForm` + servicio transaccional;
- mayoría de edad → validación server-side;
- email/documento únicos → modelo/formulario;
- selección de modo → formulario POST y sesión Django;
- redirección por rol/modo → vista Django;
- mensajes → framework de messages/forms.

### Conservar solo UI

- opcionalmente mostrar/ocultar contraseña, sin almacenar valor;
- pequeños indicadores visuales de fortaleza, no autoritativos.

### Retirar

- carga de `usuarios.json`;
- comparación de contraseña;
- `guardarSesionInicial`;
- `guardarModoAcceso`;
- `obtenerUsuarioActualAuth`;
- credenciales demo;
- `localStorage`;
- `window.location.href` a HTML estáticos.

### Destino

No copiar `auth.js`. Si se necesita UI, crear después:

```text
static/js/accounts/forms-ui.js
```

---

## 6.3 `js/cliente.js`

**Clasificación:** reescribir como vistas/formularios POST Django.

### Pasar a Django

- carga de wallets, movimientos, boletos y eventos;
- compra de boleto;
- validación del modo CLIENTE;
- recarga simulada 1:1;
- conversión VIRTUAL → REAL con 10 %;
- transferencias;
- creación de solicitudes;
- filtros y paginación;
- generación de movimientos;
- permisos de compra.

### Conservar solo UI

- preview no autoritativo de conversión;
- confirmación Bootstrap antes del POST;
- filtros visuales que terminan en GET;
- actualización de etiqueta/ayuda de campos.

### Retirar

- saldos en memoria;
- escrituras a `localStorage`;
- generación de IDs;
- generación final del boleto en navegador;
- cálculo final de comisiones;
- edición directa de arrays;
- reglas 5 % y 15 %.

### Destinos

```text
templates/dashboards/client.html
templates/finance/*
templates/lottery/*
templates/vendors/*
static/js/finance/preview.js        # solo si se autoriza
static/js/lottery/ticket-ui.js      # solo UI
```

---

## 6.4 `js/vendedor.js`

**Clasificación:** reescribir como POST Django.

### Pasar a Django

- acceso por modo;
- asignación/toma de solicitudes;
- confirmación/cancelación;
- bloqueo y expiración;
- compra mayorista 0.90;
- conversión 10 %;
- movimientos y wallets;
- envío al cliente;
- permisos.

### Conservar solo UI

- contador visual calculado desde una fecha entregada por backend;
- modal de confirmación;
- preview de compra mayorista;
- filtros GET.

### Retirar

- `localStorage`;
- `cargarJSONSeguro`;
- duplicados de funciones del menú;
- simulación automática de transiciones;
- acreditación con tarjeta;
- retiro con fórmula propia;
- IDs generados en navegador;
- reglas 5 % y 15 %.

### Destinos

```text
templates/dashboards/vendor.html
templates/vendors/request_detail.html
static/js/vendors/request-timer.js  # solo visual
static/js/finance/preview.js         # solo visual
```

---

## 6.5 `js/admin.js`

**Clasificación:** reescribir como CRUD Django/admin y acciones POST.

### Pasar a Django

- usuarios, estados y roles;
- vendedores;
- productos y eventos;
- solicitudes;
- movimientos;
- estadísticas;
- creación/cancelación de eventos;
- protección de históricos.

### Conservar solo UI

- modales de confirmación;
- filtros visuales;
- pestañas Bootstrap;
- previews de formularios que no definan el valor final.

### Retirar

- eliminación visual de usuario;
- ascensos de rol desde arrays;
- configuración guardada en `localStorage`;
- creación de eventos en navegador;
- fórmula 75 %;
- generación de IDs;
- edición de históricos.

### Destinos

```text
templates/dashboards/admin.html
templates/accounts/user_*.html
templates/vendors/vendorprofile_*.html
templates/lottery/event_*.html
Django admin
```

No copiar `admin.js` completo.

---

## 6.6 `js/solicitudes.js`

**Clasificación:** reescribir como services Django y POST.

### Pasar a Django

- creación;
- asignación;
- bloqueo;
- transición de estados;
- confirmación;
- cancelación;
- expiración;
- reserva/liberación de saldo;
- auditoría;
- concurrencia.

### Conservar solo UI

- contador visual hasta `expires_at`;
- activar/desactivar visualmente botones según contexto ya calculado;
- modal de confirmación.

### Retirar

- temporizador como autoridad;
- completar solicitud por sistema en navegador;
- edición de arrays;
- cambios de saldo desde JS;
- almacenamiento local.

### Destino opcional

```text
static/js/vendors/request-timer.js
```

El servidor debe volver a validar el estado al recibir el POST.

---

## 6.7 `js/sorteos.js`

**Clasificación:** reescribir como vistas/forms/services Django.

### Pasar a Django

- detalle de evento;
- consulta de boleto;
- validación de combinación;
- compra;
- disponibilidad;
- saldo;
- unicidad;
- resultado;
- movimientos.

### Conservar solo UI

- contador visual de cierre;
- normalización visual a mayúsculas;
- ayuda de símbolos permitidos;
- modal de confirmación.

### Retirar

- resolver eventos desde JSON;
- generar boleto;
- descontar saldo;
- guardar boleto en `localStorage`;
- determinar permisos;
- generar IDs;
- cálculo autoritativo del tiempo;
- validación final exclusivamente JS.

### Destino opcional

```text
static/js/lottery/event-ui.js
```

Reglas definitivas:

- OCTAL: 4 símbolos únicos, 0–7;
- DECIMAL: 5 símbolos únicos, 0–9;
- HEXADECIMAL: 6 símbolos únicos, 0–9/A–F.

---

## 6.8 `js/wallets.js`

**Clasificación:** retirar como fuente de verdad y reescribir en services Django.

### Pasar a Django

- saldos disponibles/reservados;
- movimientos;
- débitos/créditos;
- comisiones;
- reservas;
- liberaciones;
- transferencias.

### Conservar solo UI

- formateo visual de moneda puede hacerse preferentemente mediante filtros/templates de Django;
- preview opcional no autoritativo.

### Retirar

- mutación de wallets en navegador;
- persistencia;
- reglas financieras en JS.

### Destino

No copiar el archivo. La lógica final vive en:

```text
apps/finance/services.py
```

Un módulo JS de preview solo se crea cuando exista el formulario real.

---

## 6.9 `js/utils.js`

**Clasificación:** retirar casi completo; conservar utilidades estrictamente visuales.

### Retirar

- rutas basadas en `/pages/`;
- carga JSON;
- sesión;
- roles;
- redirecciones;
- acceso a datos del negocio;
- generación de IDs;
- formateo usado para cálculos.

### Conservar en `static/js/app.js`

- confirmación accesible;
- enfoque;
- utilidades de UI sin datos sensibles;
- inicialización opcional de tooltips.

---

# 7. Clasificación de JSON

Los JSON no se cargarán en producción ni desde el navegador.

| Archivo | Decisión | Razón |
|---|---|---|
| `data/usuarios.json` | Descartar | Contiene passwords en texto plano, roles y permisos obsoletos |
| `data/wallets.json` | Descartar como seed | Saldos arbitrarios y estructura legado; crear wallets con services/seed controlado |
| `data/movimientos.json` | Descartar | Contiene 5 %, 15 %, tarjeta y movimientos incompatibles |
| `data/sorteos.json` | Adaptar manualmente a seed controlado | Solo rescatar nombres/tipos visuales; corregir Hexadecimal y retirar 75 % |
| `data/eventos.json` | Descartar o usar solo como referencia de escenarios | Fechas y premios demo no deben convertirse automáticamente |
| `data/boletos.json` | Descartar | Boletos históricos ficticios, montos float y reglas antiguas |
| `data/solicitudes.json` | Descartar o referencia de estados | No importar saldos reservados/transiciones simuladas |

## 7.1 `seed_data/legacy` opcional

Solo para trazabilidad y nunca para carga automática:

```text
seed_data/legacy/
├── README.md
├── sorteos_legacy_reference.json
└── NOT_IMPORTABLE.txt
```

Reglas:

- no incluir `usuarios.json`;
- no incluir contraseñas;
- no instalar fixtures automáticas;
- no referenciar estos archivos desde templates o JavaScript;
- indicar claramente que no son fuente de verdad.

El seed real debe ser un management command idempotente con `update_or_create`.

---

# 8. Plan de `static/js`

Estructura mínima prevista:

```text
static/js/
├── app.js
├── lottery/
│   └── event-ui.js          # solo cuando exista detalle/compra real
├── vendors/
│   └── request-timer.js     # solo cuando exista solicitud real
└── finance/
    └── preview.js           # solo cuando existan formularios reales
```

En el primer módulo de migración se crea únicamente:

```text
static/js/app.js
```

Contenido permitido:

- confirmación para formularios marcados por el backend;
- enfoque al primer campo inválido;
- inicialización opcional de tooltips;
- cierre del offcanvas después de navegar;
- ninguna lectura o escritura de roles, saldos, boletos o resultados.

---

# 9. Orden de implementación por módulos

## Módulo 1 — Recursos comunes

Archivos:

```text
static/js/app.js
static/img/logo-placeholder.png
templates/base.html
```

Objetivo:

- copiar logo temporal;
- cargar `app.js`;
- implementar únicamente UI común;
- no cambiar negocio.

## Módulo 2 — Público y accounts

Archivos:

```text
templates/core/home.html
templates/accounts/login.html
templates/accounts/register.html
templates/accounts/choose_mode.html
```

Objetivo:

- eliminar enlaces estáticos;
- forms Django;
- selector POST;
- sin credenciales.

## Módulo 3 — Dashboard cliente

Archivos:

```text
templates/dashboards/client.html
```

Y después, solo si existen vistas/forms:

```text
static/js/finance/preview.js
```

## Módulo 4 — Dashboard vendedor y solicitudes

Archivos:

```text
templates/dashboards/vendor.html
templates/vendors/request_detail.html
static/js/vendors/request-timer.js
```

## Módulo 5 — Dashboard administrador

Archivos:

```text
templates/dashboards/admin.html
```

CRUD y admin se trabajan en tareas separadas.

## Módulo 6 — Lotería

Archivos:

```text
templates/lottery/event_detail.html
templates/lottery/ticket_detail.html
static/js/lottery/event-ui.js
```

---

# 10. Validaciones globales

## Buscar restos prohibidos

```powershell
Get-ChildItem templates,static -Recurse -File |
    Select-String -Pattern `
        "localStorage|sessionStorage|fetch\(|data/.*\.json|pages/.*\.html|123456|5%|15%|75%|CLIENTE_FINANCIERO"
```

Resultado esperado: ninguna coincidencia de lógica legado.

## Verificar recursos

```powershell
python manage.py findstatic css/app.css
python manage.py findstatic js/app.js
python manage.py findstatic img/logo-placeholder.png
```

## Django

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
```

Los cambios de templates/static no deben generar migraciones.

---

# 11. Criterio para iniciar el primer módulo

El plan queda aprobado cuando:

- el ZIP legado permanece intacto;
- cada HTML tiene destino Django;
- cada JS está clasificado;
- cada JSON tiene decisión explícita;
- no se propone importar passwords;
- no se propone cargar JSON desde navegador;
- no se usa `localStorage`;
- el trabajo continuará un módulo por respuesta.

El primer módulo a implementar será **Recursos comunes**:

```text
static/js/app.js
static/img/logo-placeholder.png
templates/base.html
```

No se deben generar todavía módulos de lotería, finance, vendors o CRUD.
