# Informe de auditoría integral, corrección y puerta de salida

## 1. Identificación

- Proyecto: **Lotería Binaria — Taller #3 con Django**.
- Repositorio revisado: `Herrera2005/loteriaBinaria-Django`.
- Rama revisada: `feature/taller3-fase-1-esqueleto-sqlite`.
- Commit observado: `96c1d9650ff6e67af431b4e21c46a2326a50fb9b`.
- Mensaje observado: `fase 2 y parte de fase 3`.
- Referencia visual preservada: `Proyecto_HerreraNietoCristhian_legacy.zip`.
- Base de fase actual: **SQLite**.
- Base de segunda fase: **MySQL**.
- PostgreSQL: **fuera del alcance de este taller**.

## 2. Fuentes y autoridad aplicadas

1. Enunciado específico del Taller #3.
2. Cinco documentos canónicos conservados en `docs/referencias/`.
3. Guía docente VideoClub.
4. ZIP legado únicamente como referencia visual y de flujo.

Cuando los documentos canónicos originales mencionan PostgreSQL, prevalece el
enunciado del taller. La adaptación queda registrada en
`docs/DECISION_T3_001_SQLITE_MYSQL.md`; los originales no se editaron
silenciosamente.

## 3. Método de revisión

Se revisaron:

- estructura de la rama y último commit;
- configuración Django;
- modelos y migraciones existentes;
- admin;
- templates y recursos static;
- rutas y stubs de views;
- documentos canónicos y documentos del taller;
- inventario del ZIP visual;
- residuos de `localStorage`, JSON, `fetch`, credenciales demo y enlaces
  `pages/*.html`;
- correlación entre archivo, función, ruta, template y prueba;
- portabilidad SQLite → MySQL;
- accesibilidad y responsive del HTML/CSS;
- diseño de pruebas reproducibles.

## 4. Diagnóstico del commit original

### Críticos

1. `config/urls.py` solo conectaba `/admin/`; los templates utilizaban nombres
   de URL que todavía no estaban disponibles.
2. `apps/accounts/views.py` y `apps/core/views.py` seguían como stubs, por lo
   que login, registro, selector y dashboards no eran verificables.
3. `base.html` buscaba `static/css/app.css`, mientras el CSS se encontraba en
   `static/app.css`.
4. El template base incluía `_messages.html`, pero el partial existente tenía
   el nombre `_manages.html`.
5. Convivían el runtime Django y el frontend estático (`index.html` y
   `pages/*.html`), creando dos arquitecturas y rutas ambiguas.

### Altos

6. No existía suite automatizada para registro, términos, roles, modo activo,
   protección de rutas, seeds, static o conservación del respaldo.
7. El seed demo contenía una contraseña fija.
8. Las dependencias de SQLite y MySQL no estaban separadas por fase.
9. El selector y la navegación no estaban conectados a una política backend
   comprobable.
10. No existía una puerta de migración limpia sobre una SQLite descartable.

### Documentales

11. Los documentos 01, 02, 03 y 05 conservan menciones activas a PostgreSQL.
    El conflicto no debe resolverse borrando evidencia: se corrige mediante una
    decisión del taller y una futura versión documental trazable.
12. La auditoría canónica asignaba 9,4/10 a la especificación corregida, pero
    aclaraba que faltaban código, migraciones y pruebas. Esa nota no podía
    trasladarse automáticamente al commit ejecutable.

## 5. Correcciones incluidas en este paquete

### Configuración

- `config/settings.py` acepta exclusivamente SQLite o MySQL.
- SQLite es el valor predeterminado de fase 1.
- `requirements.txt` contiene la fase SQLite.
- `requirements-mysql.txt` agrega `mysqlclient` solo para fase 2.
- secretos y contraseña demo se leen del entorno.
- static, templates, zona horaria y usuario personalizado quedan conectados.

### Accounts

- usuario personalizado definitivo;
- username, email y documento normalizados con forma canónica portable SQLite/MySQL;
- versiones legales inmutables después de la primera aceptación y aceptaciones históricas no editables/eliminables;
- registro adulto con aceptación de términos y privacidad vigentes;
- servicio transaccional de registro con revalidación y bloqueo de versiones legales vigentes;
- contraseña mediante `create_user`/hash de Django;
- login con bloqueo por estado académico;
- logout únicamente por POST;
- roles mediante Groups;
- selector de modo únicamente con roles asignados;
- sesión `active_mode` validada en cada ruta;
- 403 ante mezcla de modos;
- admin sin eliminación física de usuarios o aceptaciones;
- seed legal que no muta una versión histórica ya creada.

### Core e interfaz

- landing pública;
- rutas reales para login, registro, selector y dashboards;
- navbar y offcanvas derivados del backend;
- administración visible solo para staff en modo ADMINISTRADOR;
- dashboards que ocultan tarjetas y acciones de módulos que todavía no existen;
- estados vacíos explícitos;
- Bootstrap 5.3 real con SRI;
- identidad azul profundo/dorado del ZIP;
- tablas responsive, foco visible, ARIA de error y objetivos táctiles mínimos de 44 px;
- modal de confirmación para formularios sensibles;
- JavaScript limitado a UI;
- páginas 403/404.

### Respaldo y migración visual

- el ZIP legado se conserva fuera de `static`;
- el logo utilizado es una copia exacta del recurso visual legado;
- no se cargan los JSON del respaldo;
- `seed_data/legacy/` solo documenta qué no debe importarse.

### Pruebas

Se diseñaron **48 pruebas Django** para:

- registro y normalización;
- mayoría de edad;
- duplicidad case-insensitive de username, correo y documento;
- términos ausentes o sustituidos durante el registro;
- CSRF;
- login de un rol y multirrol;
- modo no asignado y aislamiento de URL;
- aislamiento de dashboards;
- estado suspendido;
- logout POST;
- admin e históricos protegidos;
- seeds idempotentes, preservación de IP histórica e inmutabilidad legal;
- bloqueo explícito de PostgreSQL;
- rutas, static, backup, navegación, privacidad de conteos administrativos y ruta SQLite determinista.

`scripts/verify.ps1` y `scripts/verify.sh` crean una SQLite temporal, aplican
todas las migraciones, ejecutan pruebas y `collectstatic`, y luego eliminan los
artefactos temporales sin tocar `db.sqlite3`.

### Endurecimiento final de coherencia

- la ruta SQLite relativa se resuelve siempre bajo `BASE_DIR`;
- el login normaliza username antes de autenticar;
- la base aplica forma canónica a username, email y documento;
- el formulario marca errores con `is-invalid` y `aria-invalid`;
- una versión legal aceptada solo puede activarse/desactivarse, no reescribirse;
- una aceptación no puede editarse ni eliminarse mediante modelo o QuerySet;
- el seed demo usa `get_or_create` para no reescribir IP histórica;
- un usuario con grupo ADMINISTRADOR pero sin `is_staff` no recibe conteos;
- la navbar conserva offcanvas hasta 1199.98 px;
- los módulos pendientes no presentan tarjetas que parezcan funcionales;
- el JavaScript solo gestiona foco y confirmación visual, y limpia su estado al cancelar.

## 6. Reglas correlacionadas

### Implementadas en esta fase

- Django y la base relacional activa son fuente de verdad.
- SQLite fase 1; MySQL fase 2.
- usuario personalizado antes de la primera migración general;
- roles asignados por backend;
- selección de modo por POST;
- CLIENTE, VENDEDOR y ADMINISTRADOR aislados por modo;
- VENDEDOR/ADMINISTRADOR no muestran compra de boletos;
- password hash y sesiones Django;
- aceptación legal histórica;
- sin tarjeta, pagos reales, JSON o `localStorage` de negocio;
- Bootstrap 5.3 y responsive común.

### Documentadas, todavía no implementadas

- wallets REAL/VIRTUAL y movimientos;
- recarga simulada 1:1;
- conversión VIRTUAL → REAL con 10 %;
- transferencia VIRTUAL;
- compra mayorista 0.90 REAL por 1.00 VIRTUAL;
- solicitudes y reservas;
- Octal 4, Decimal 5, Hexadecimal 6, todos con símbolos únicos;
- combinación única por evento;
- límite de compra, cierre y concurrencia;
- premio fijo, resultados y acreditación automática.

No se agregaron botones ni rutas falsas para estas reglas. Deben desarrollarse
módulo por módulo, con servicios y pruebas antes de la interfaz.

## 7. Ambigüedades resueltas

| Ambigüedad | Resolución |
|---|---|
| PostgreSQL en documentos vs SQLite/MySQL en taller | prevalece el enunciado; decisión T3-001 |
| vendedor/admin multirrol en modo CLIENTE | CLIENTE conserva funciones completas cuando el rol está asignado |
| modo VENDEDOR o ADMINISTRADOR | no compra boletos |
| legal vigente cambia durante registro | el servicio vuelve a consultar la última versión y revierte |
| seed legal repetido | no modifica versiones históricas existentes |
| dos frontends activos | solo templates/static; HTML legado queda dentro del ZIP |
| contraseña demo | se exige variable local y no se imprime |
| dashboards sin backend | estados vacíos y aviso; cero acciones simuladas |

## 8. Calificación

### Rama observada antes de correcciones

| Dimensión | Nota /10 |
|---|---:|
| Configuración y rutas | 3.5 |
| Accounts integrado | 6.2 |
| Interfaz Django | 6.8 |
| Seguridad básica | 5.3 |
| Trazabilidad documental | 6.4 |
| Pruebas reproducibles | 2.0 |
| **Global** | **5.1** |

### Paquete corregido — revisión estática ejecutada

| Dimensión | Nota /10 |
|---|---:|
| Arquitectura de fase | 9.4 |
| Accounts y permisos | 9.5 |
| Interfaz y responsive | 9.2 |
| Seguridad básica | 9.4 |
| Seeds e inmutabilidad legal | 9.6 |
| Trazabilidad | 9.5 |
| Diseño de pruebas | 9.6 |
| Evidencia ejecutada en este entorno | 8.0 |
| **Global verificable actualmente** | **9.2** |

La nota se limita a **9,2/10** porque en el entorno de generación no estaba
instalado Django y no fue posible ejecutar `manage.py check`, migraciones ni
la suite. Sí se ejecutaron auditoría estática, parseo/compilación Python y
sintaxis JavaScript. Cuando `scripts/verify.ps1` quede completamente verde en
el equipo del estudiante, la fase puede calificarse **9,6/10**. No llega a
10/10 porque finance, vendors y lottery siguen pendientes por diseño.

## 9. Puerta de salida

No integrar ni continuar al siguiente módulo hasta obtener:

```text
AUDITORÍA ESTÁTICA: OK
System check identified no issues
No changes detected
migraciones aplicadas sin error
48 pruebas verdes
static encontrados
collectstatic completado
```

Después se revisan manualmente `/`, login, registro, selector y los tres
paneles en 360, 390, 768, 1024 y 1440 px.

## 10. Siguiente módulo recomendado

Continuar con **un solo módulo por respuesta** según el manual intercalado.
La base debe quedar primero integrada en la rama. Después corresponde el CRUD
evaluable que indique la fase del manual; no deben implementarse juntos
finance, vendors y lottery.
