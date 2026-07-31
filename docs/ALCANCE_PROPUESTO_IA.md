# Alcance propuesto — Taller #3 Lotería Binaria con Django

## Diagnóstico breve

El alcance del Taller #3 debe ser una **aplicación académica Django funcional y demostrable**, no una implementación completa de todas las operaciones financieras y de lotería descritas en el MVP canónico.

La entrega debe priorizar lo evaluable:

- desarrollo inicial con SQLite;
- migración posterior a MySQL;
- cinco aplicaciones organizadas por módulos;
- tres CRUD completos;
- interfaz basada realmente en Bootstrap 5.3;
- autenticación y roles como mejora adicional;
- pruebas, capturas y evidencia del proceso;
- conservación de registros históricos mediante desactivación o eliminación protegida.

El Manual Intercalado identifica expresamente `accounts`, `vendors` y `lottery` como los tres módulos que demuestran la rúbrica, mientras que `core` y `finance` funcionan como módulos de apoyo sin CRUD destructivo.

---

## 1. Propósito del sistema

El proyecto consiste en desarrollar una versión académica y controlada de **Lotería Binaria** utilizando Django.

El sistema permitirá administrar usuarios, vendedores, productos de lotería y eventos mediante una aplicación web organizada por módulos. También incorporará autenticación real, control básico de roles y una interfaz responsive construida con Bootstrap 5.3.

El proyecto conservará la identidad visual azul oscuro y dorada del frontend anterior, pero reemplazará su autenticación simulada, archivos JSON y almacenamiento en `localStorage` por datos administrados por Django y su base de datos.

El ZIP antiguo se conservará únicamente como referencia de:

- diseño visual;
- estructura de páginas;
- navegación;
- dashboards;
- formularios;
- detalles de boletos, sorteos y solicitudes.

No se reutilizará como fuente de verdad para usuarios, roles, saldos, boletos, solicitudes ni resultados.

Los documentos canónicos establecen que el frontend heredado es una referencia visual y de datos de demostración, mientras que las decisiones reales deben ejecutarse en Django.

---

## 2. Perfil técnico obligatorio

La implementación seguirá estas decisiones:

| Elemento | Decisión del taller |
|---|---|
| Framework backend | Django 5.2 |
| Lenguaje | Python 3.12 |
| Primera base de datos | SQLite |
| Segunda base de datos | MySQL |
| Framework visual | Bootstrap 5.3 |
| CSS complementario | Identidad azul oscuro y dorada |
| Arquitectura | Aplicación Django monolítica y modular |
| Renderizado | Templates Django |
| Autenticación | Django Authentication |
| Organización | Cinco aplicaciones |
| Persistencia sensible | Base de datos, nunca JSON o `localStorage` |
| Alcance | Académico y simulado |

PostgreSQL queda excluido de este Taller #3, aunque aparezca en los documentos originales del MVP. La secuencia específica del taller es SQLite primero y MySQL después.

---

# 3. Aplicaciones Django propuestas

## 3.1 `accounts`

Responsable de:

- usuario personalizado;
- datos personales básicos;
- estados de cuenta;
- versiones de términos;
- aceptación de términos;
- registro;
- login;
- logout;
- roles;
- modo activo;
- administración de usuarios.

Será el **primer CRUD evaluable**.

El usuario personalizado deberá existir antes de ejecutar la primera migración general. Esta condición es necesaria para evitar sustituir posteriormente el modelo de usuario predeterminado de Django.

---

## 3.2 `core`

Responsable de:

- landing pública;
- navegación común;
- dashboards;
- página inicial;
- mensajes;
- elementos compartidos;
- auditoría básica;
- utilidades transversales.

No tendrá un CRUD destructivo obligatorio. Su función principal será conectar la interfaz y mostrar información según el usuario autenticado.

---

## 3.3 `finance`

Responsable de:

- wallets simuladas;
- consulta de saldos;
- movimientos;
- visualización del historial financiero;
- futuras operaciones mediante servicios controlados.

No ofrecerá un formulario genérico para modificar saldos.

Los movimientos y balances no se administrarán como un CRUD normal. Los cambios deberán producirse mediante operaciones específicas del servidor, porque la baseline prohíbe editar directamente saldos desde formularios administrativos genéricos.

---

## 3.4 `vendors`

Responsable de:

- perfil del vendedor;
- estado del vendedor;
- consulta de solicitudes;
- relación Cliente–Vendedor;
- futuras acciones específicas sobre solicitudes.

Será el **segundo CRUD evaluable**, centrado en `VendorProfile`.

Las solicitudes no tendrán una edición genérica de su estado. Sus transiciones deberán realizarse posteriormente mediante acciones o servicios definidos.

---

## 3.5 `lottery`

Responsable de:

- productos Octal, Decimal y Hexadecimal;
- eventos;
- boletos;
- resultados;
- reglas de símbolos;
- fechas de apertura y cierre;
- premio fijo;
- consulta pública y administrativa.

Será el **tercer CRUD evaluable**, centrado en:

- productos;
- eventos.

Los boletos y resultados serán registros protegidos y no se eliminarán mediante un CRUD genérico.

---

# 4. Desarrollo mínimo aceptable para aprobar

## 4.1 Configuración inicial

El proyecto mínimo deberá demostrar:

- entorno virtual activo;
- Django instalado dentro del entorno;
- proyecto `config`;
- carpeta `apps`;
- cinco aplicaciones registradas;
- templates globales;
- archivos estáticos;
- configuración de zona horaria;
- SQLite activa;
- archivo `.env`;
- `.env` excluido del repositorio;
- `requirements.txt`;
- ejecución correcta de `python manage.py check`.

No se deberá ejecutar la primera migración general antes de definir `accounts.User`.

---

## 4.2 Usuario personalizado

Debe existir un usuario basado en el sistema de autenticación de Django con, como mínimo:

- nombre de usuario;
- correo;
- documento;
- teléfono;
- fecha de nacimiento;
- estado;
- fechas de creación y actualización.

También se incluirán los modelos mínimos de términos y aceptación.

La evidencia deberá demostrar que:

- `AUTH_USER_MODEL` corresponde al usuario personalizado;
- las contraseñas se almacenan mediante hash;
- correo y documento no se duplican;
- una fecha de nacimiento inválida es rechazada;
- una cuenta puede desactivarse sin eliminar su historia.

---

## 4.3 Primer CRUD: Accounts

Debe incluir:

| Operación | Evidencia mínima |
|---|---|
| Crear | Registrar un usuario válido |
| Listar | Tabla con búsqueda y paginación |
| Ver | Página de detalle |
| Editar | Modificar campos permitidos |
| Eliminar | Eliminación protegida o desactivación |

Debe estar protegido para que solamente un usuario autorizado pueda acceder.

Un usuario común no deberá entrar al CRUD administrativo manipulando directamente la URL.

---

## 4.4 Segundo CRUD: Vendors

Debe incluir:

| Operación | Evidencia mínima |
|---|---|
| Crear | Crear un perfil vendedor |
| Listar | Lista con filtro por estado |
| Ver | Detalle del perfil |
| Editar | Modificar campos permitidos |
| Eliminar | Eliminar si no tiene historia o desactivar si la tiene |

Debe impedir que un mismo usuario tenga más de un perfil vendedor.

Las solicitudes Cliente–Vendedor podrán mostrarse en modo consulta, pero no deberán permitir modificar estados terminales mediante un `UpdateView` genérico.

---

## 4.5 Tercer CRUD: Lottery

Debe incluir CRUD de productos y eventos.

### Productos

Como mínimo:

| Producto | Símbolos | Cantidad |
|---|---|---:|
| Octal | 0–7 | 4 únicos |
| Decimal | 0–9 | 5 únicos |
| Hexadecimal | 0–9 y A–F | 6 únicos |

### Eventos

Cada evento deberá mostrar al menos:

- producto;
- nombre;
- fecha de apertura;
- fecha del sorteo;
- fecha de cierre;
- precio;
- premio fijo;
- estado.

El cierre deberá corresponder a diez minutos antes del sorteo.

El CRUD debe respetar estas reglas:

- un evento en borrador puede editarse;
- un evento publicado no puede modificar libremente producto, precio, premio ni fechas;
- un producto con eventos asociados no se elimina;
- un evento con boletos o resultado no se elimina físicamente;
- los resultados no se editan ni eliminan mediante un CRUD genérico.

---

## 4.6 Interfaz Bootstrap 5.3

La interfaz mínima deberá usar componentes reales de Bootstrap:

- `navbar`;
- sistema de cuadrícula;
- tarjetas;
- formularios;
- alertas;
- badges;
- tablas responsive;
- paginación;
- botones;
- menú colapsable u `offcanvas`;
- modal únicamente cuando sea necesario.

El CSS propio solamente complementará:

- colores;
- tipografía;
- espaciado;
- identidad de marca;
- pequeños ajustes responsive.

No se deberá reconstruir manualmente en CSS un framework paralelo.

---

## 4.7 Responsive mínimo

Se deberán comprobar, como mínimo, estos anchos:

```text
360 px
390 px
768 px
1024 px
1440 px
```

Se deberá verificar:

- ausencia de scroll horizontal global;
- menú accesible;
- botones utilizables;
- tablas contenidas;
- formularios legibles;
- tarjetas sin texto cortado;
- mensajes visibles;
- objetivos táctiles adecuados;
- un único encabezado principal por página.

---

## 4.8 Migración SQLite → MySQL

La primera versión funcional deberá ejecutarse completamente sobre SQLite.

Después se realizará la migración a MySQL mediante este proceso general:

1. completar y probar las migraciones en SQLite;
2. exportar los datos necesarios;
3. crear una base MySQL vacía;
4. configurar las credenciales mediante `.env`;
5. ejecutar las mismas migraciones en MySQL;
6. importar los datos;
7. comparar conteos;
8. repetir los tres CRUD;
9. repetir login y roles;
10. guardar capturas y evidencia.

No se crearán manualmente las tablas definitivas con un script SQL externo. El esquema final será creado por Django mediante sus migraciones.

Tampoco se deberán reescribir migraciones ya aplicadas para adaptarlas a MySQL.

---

# 5. Funciones base obligatorias

## 5.1 Gestión de usuarios

- crear usuarios;
- listar;
- buscar;
- consultar detalle;
- editar;
- desactivar o eliminar de forma segura;
- validar duplicados;
- administrar términos.

## 5.2 Gestión de vendedores

- crear perfiles;
- listar;
- filtrar;
- consultar;
- editar;
- desactivar;
- consultar solicitudes asociadas.

## 5.3 Gestión de lotería

- administrar productos;
- administrar eventos;
- respetar reglas Octal, Decimal y Hexadecimal;
- aplicar cierre diez minutos antes;
- proteger eventos publicados;
- consultar boletos y resultados sin edición destructiva.

## 5.4 Navegación

- landing;
- login;
- registro;
- panel según contexto;
- navegación común;
- mensajes de éxito y error;
- páginas de estado vacío;
- manejo básico de errores.

## 5.5 Administración Django

- superusuario;
- modelos registrados;
- filtros;
- búsquedas;
- campos de solo lectura cuando corresponda;
- ausencia de eliminación para registros históricos.

---

# 6. Mejora adicional real

La mejora adicional principal será:

## Autenticación real y control de roles

Se implementará:

- registro seguro;
- login;
- logout mediante POST;
- contraseñas con hash;
- grupos de Django;
- roles CLIENTE, VENDEDOR y ADMINISTRADOR;
- rutas protegidas;
- navegación según permisos;
- rechazo de acceso directo no autorizado;
- modo activo almacenado en la sesión del servidor cuando una cuenta tenga más de un rol.

La mejora es funcional y no solamente estética.

### Comportamiento esperado

- Un cliente puro entra al área Cliente.
- Un usuario multirrol selecciona únicamente entre roles asignados.
- El modo CLIENTE permite las funciones de Cliente si ese rol está asignado.
- El modo VENDEDOR no permite comprar boletos.
- El modo ADMINISTRADOR no permite comprar boletos.
- Cambiar el modo no crea un rol nuevo.
- El modo no se decide mediante JavaScript, query string o `localStorage`.
- Las rutas verifican permisos en el servidor.

---

# 7. Evidencia obligatoria

## 7.1 Evidencia de análisis

- propuesta generada con IA;
- apreciación personal;
- modelo entidad–relación;
- validación SQL temporal;
- lista de aplicaciones;
- plan de implementación;
- auditoría del ZIP.

## 7.2 Evidencia de entorno

- versión de Python;
- entorno virtual activo;
- versión de Django;
- árbol del proyecto;
- `manage.py check`;
- configuración SQLite.

## 7.3 Evidencia de modelos y migraciones

- `makemigrations`;
- revisión de migraciones;
- `sqlmigrate`;
- `migrate`;
- `showmigrations`;
- acceso al admin;
- usuario personalizado confirmado.

## 7.4 Evidencia de los tres CRUD

Para cada app:

- lista;
- formulario de creación;
- detalle;
- formulario de edición;
- confirmación de eliminación o desactivación;
- caso válido;
- caso inválido;
- prueba de permisos;
- prueba automatizada;
- captura de Bootstrap.

## 7.5 Evidencia de autenticación

- registro;
- login;
- logout;
- contraseña protegida;
- roles;
- selector de modo;
- ruta rechazada;
- navegación adaptada.

## 7.6 Evidencia de MySQL

- servidor MySQL;
- base seleccionada;
- migraciones;
- tablas creadas por Django;
- conteos antes y después;
- CRUD funcionando;
- login funcionando;
- pruebas ejecutadas.

---

# 8. Ampliaciones futuras opcionales

Estas funciones pueden realizarse únicamente después de completar todo el mínimo evaluable:

- exportación CSV;
- recarga REAL simulada 1:1;
- conversión VIRTUAL a REAL con comisión del 10%;
- compra mayorista del vendedor a razón de 0,90 REAL por 1,00 VIRTUAL;
- creación de solicitudes con reserva de saldo;
- asignación de solicitudes;
- compra de boletos;
- evaluación de boletos;
- publicación controlada de resultados;
- reembolso por cancelación;
- auditoría ampliada;
- dashboard con métricas;
- PWA;
- despliegue remoto.

Cada ampliación deberá desarrollarse una por una y mediante servicios de dominio, no agregando cálculos directamente en las vistas.

---

# 9. Funciones fuera de alcance por tiempo

Para proteger la entrega, deben quedar fuera:

- pagos reales;
- tarjetas;
- CVV;
- cuentas bancarias;
- retiros bancarios reales;
- pasarelas de pago;
- cumplimiento regulatorio de loterías;
- dinero o premios reales;
- API REST obligatoria;
- aplicación móvil nativa;
- microservicios;
- Redis;
- Celery;
- WebSockets;
- concurrencia avanzada en SQLite;
- infraestructura Docker obligatoria;
- ledger profesional de doble entrada;
- fondos financieros complejos;
- sorteos privados creados por usuarios;
- códigos de invitación;
- reclamos;
- expulsiones;
- evidencia documental;
- commit–reveal;
- sistema empresarial completo;
- migración a PostgreSQL;
- funciones heredadas que dependan de JSON o `localStorage`.

---

# 10. Diferencia entre mínimo evaluable y proyecto futuro

| Área | Mínimo evaluable | Ampliación futura |
|---|---|---|
| Base de datos | SQLite y luego MySQL | Hosting remoto |
| Apps | Cinco registradas | Más módulos |
| CRUD | Accounts, Vendors, Lottery | CRUD adicionales |
| Interfaz | Bootstrap 5.3 responsive | PWA o app móvil |
| Seguridad | Login, roles, rutas, CSRF | Auditoría avanzada |
| Finanzas | Consulta segura | Operaciones completas |
| Vendedores | Perfil y solicitudes read-only | Asignación y confirmación |
| Lotería | Productos y eventos | Compra, premios y resultados |
| Reportes | No imprescindible | CSV y métricas |
| Concurrencia | Validación básica | Pruebas avanzadas en MySQL |

---

# 11. Criterio de terminado del mínimo

El Taller #3 puede considerarse completo cuando se demuestre que:

- las cinco apps existen y están correctamente registradas;
- el usuario personalizado se creó antes de la primera migración;
- la versión SQLite funciona;
- la versión MySQL funciona;
- existen tres CRUD completos;
- todos los CRUD usan Bootstrap 5.3;
- login y roles funcionan;
- las rutas están protegidas;
- no existen contraseñas en texto;
- no se administran saldos mediante un formulario genérico;
- no se borran boletos, movimientos, resultados ni auditoría;
- no quedan enlaces a `pages/*.html`;
- no queda `localStorage` como autoridad de negocio;
- no aparecen porcentajes obsoletos del ZIP;
- las pruebas automatizadas pasan;
- `python manage.py check` no reporta errores;
- las capturas y evidencias están organizadas;
- el estudiante puede explicar la estructura y las decisiones tomadas.

---

# Comandos de esta tarea

En P-01 no se ejecutan comandos Django ni migraciones.

Solo se debe crear la carpeta documental si todavía no existe:

```powershell
New-Item -ItemType Directory -Force docs
```

Después, crear:

```text
docs/ALCANCE_PROPUESTO_IA.md
```

y guardar allí el contenido anterior.

No ejecutar todavía:

```powershell
django-admin startproject
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

---

# Pruebas documentales de P-01

Antes de continuar, revisar manualmente:

- [ ] El alcance menciona SQLite primero.
- [ ] El alcance menciona MySQL después.
- [ ] No aparece PostgreSQL como base de esta entrega.
- [ ] Existen cinco apps.
- [ ] Se identifican tres CRUD evaluables.
- [ ] Bootstrap 5.3 es obligatorio.
- [ ] Login y roles aparecen como mejora real.
- [ ] Se distingue mínimo de ampliaciones.
- [ ] Se excluyen pagos reales.
- [ ] Se excluye el proyecto empresarial completo.
- [ ] Se solicita evidencia.
- [ ] No se generó código Django.

# Puerta de salida

P-01 queda aprobado cuando:

```text
docs/ALCANCE_PROPUESTO_IA.md
```

esté guardado, el estudiante haya marcado qué partes considera útiles, exageradas o innecesarias, y el alcance no incluya funciones empresariales fuera del taller.

El siguiente paso autorizado por el manual es **P-02 — Guía para apreciación personal**.
