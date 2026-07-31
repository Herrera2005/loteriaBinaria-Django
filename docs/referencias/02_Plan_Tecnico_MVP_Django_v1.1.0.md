---
title: "Plan Técnico de Desarrollo del MVP Django"
version: "1.1.0"
project: "Lotería Binaria - MVP Django"
source_pdf: "02_Plan_Tecnico_MVP_Django_v1.1.0.pdf"
date: "2026-07-29"
---

> **Documento canónico del MVP Django.** Conversión estructural desde el PDF oficial; conserva el contenido, la numeración y las tablas en bloques de texto cuando la maquetación no permite una tabla Markdown segura.

```text
                                         LOTERIA BINARIA
```

```text
                       Plan Tecnico de Desarrollo
            Arquitectura, datos, fases, despliegue y operacion del MVP Django
Proyecto                                                        Loteria Binaria - MVP Django
```

```text
Documento                                                       PT-MVP-DJANGO
```

```text
Version                                                         1.1.0
```

```text
Estado                                                          BASELINE CORREGIDA DE CONSTRUCCIÓN
```

```text
Fecha / autor                                                   29 de julio de 2026 - Cristhian Herrera Nieto
```

Baseline de referencia exclusiva para el MVP Django. No sustituye ni modifica la arquitectura empresarial del otro proyecto
```text
                                                     Loteria Binaria.
```

## Control del documento
```text
 Campo                                                             Definicion
```

```text
                                                                   Establecer el orden de construccion, decisiones tecnicas,
```
Proposito
```text
                                                                   modelos, restricciones, pruebas, despliegue y estrategia movil.
```

```text
                                                                   Debe implementarse junto con las Reglas Maestras y la Matriz
 Autoridad                                                         de Trazabilidad. Ninguna fase se considera terminada sin su
                                                                   puerta de salida.
```

```text
                                                                   Cualquier cambio funcional debe actualizar este documento y la
 Regla de cambio                                                   matriz de trazabilidad antes de modificar modelos, migraciones o
                                                                   vistas.
```

```text
                                                                   El codigo ejecutable y PostgreSQL deben cumplir esta baseline;
 Fuente de verdad                                                  el frontend heredado es una referencia visual, no una autoridad
                                                                   funcional.
```

```text
                                                                   Proyecto academico. No procesa dinero real, tarjetas, retiros
```
Naturaleza
```text
                                                                   bancarios ni loterias reguladas.
```

```text
                                                                   DI-MVP-DJANGO v1.0.0 define arquitectura de interfaz, rutas,
```
Documento complementario
```text
                                                                   componentes, responsive y comportamiento por modo.
```

## Contenido
## 1. Punto de partida y objetivo
## 2. Arquitectura objetivo
## 3. Tecnologias y configuracion
## 4. Estructura de proyecto
## 5. Modelo de datos MVP
## 6. Servicios y transacciones
## 7. Migracion de interfaz
## 8. Fases de desarrollo
## 9. Pruebas
## 10. Despliegue
## 11. PWA / Android
## 12. Operaciones y mantenimiento
## 13. Riesgos y definicion de terminado

## 1. Punto de partida y objetivo
El ZIP actual es un frontend demostrativo completo con landing, autenticacion simulada, dashboards de
Cliente/Vendedor/Administrador, detalles de sorteo/boleto/solicitud, estilos responsive, nueve modulos JavaScript y siete
archivos JSON. Su persistencia depende de localStorage y no puede usarse como sistema multiusuario real.

```text
    Objetivo tecnico: Sustituir la simulacion por Django y PostgreSQL conservando la apariencia, sin reconstruir el proyecto
    empresarial completo.
```

```text
    Capa actual                                    Destino Django                                Observacion
```

```text
    index.html                                     templates/core/index.html                     Landing publica.
```

```text
                                                                                                 Formularios Django y sesiones. El
    pages/login.html, registro.html, elegir-                                                     selector de modo solo aparece para
                                                   templates/accounts/
    rol.html                                                                                     cuentas multirrol y explica capacidades
                                                                                                 reales.
```

```text
    pages/cliente.html                             templates/dashboards/client.html              QuerySets del usuario autenticado.
```

```text
    pages/vendedor.html                            templates/dashboards/vendor.html              Operaciones vendedor y solicitudes.
```

```text
    pages/admin.html                               templates/dashboards/admin.html               Panel visual; /admin/ sigue separado.
```

```text
    css/*, assets/img/*                            static/css, static/img                        Se conservan y ajustan rutas.
```

```text
                                                                                                 Solo comportamiento visual; operaciones
    js/*                                           static/js
                                                                                                 por POST Django.
```

```text
    data/*.json                                    seed_data/legacy y seed_demo                  No se sirven como base de datos.
```

## 2. Arquitectura objetivo
```text
      Navegador / PWA / WebView
                    | HTTPS
                    v
      Django (templates + views + forms + services)
                    | ORM / transacciones
                    v
      PostgreSQL (fuente de verdad)
```

```text
      Tareas temporales: management commands programados por el hosting
      Archivos estaticos: WhiteNoise o mecanismo del proveedor
```

- Arquitectura monolitica modular: una aplicacion Django desplegada como unidad.
- Renderizado server-side con templates; no se requiere API REST en esta version.
- Servicios de dominio separan reglas criticas de las vistas y ModelAdmin.
- PostgreSQL se usa localmente y en produccion para evitar diferencias de comportamiento.
- No Redis, no Celery, no Docker obligatorio y no microservicios.

## 3. Tecnologias y configuracion
```text
    Componente                                     Decision baseline                             Motivo
```

```text
                                                                                                 Version estable y ampliamente
    Python                                         3.12
                                                                                                 compatible; el hosting debe confirmarla.
```

```text
 Componente                                Decision baseline                            Motivo
```

```text
                                                                                        Baseline conservadora y mantenible; se
 Django                                    5.2 LTS
                                                                                        fija exactamente en requirements.
```

```text
                                                                                        Coincide con las reglas fuente y soporta
 PostgreSQL                                16 local; version compatible en hosting
                                                                                        constraints/locks.
```

```text
 Driver                                    psycopg[binary]                              Conexion PostgreSQL moderna.
```

```text
 Variables                                 django-environ + .env                        Separacion de secretos/configuracion.
```

```text
                                           Gunicorn + WhiteNoise o WSGI del
 Produccion                                                                             Despliegue simple de monolito.
                                           proveedor
```

```text
 Frontend                                  Django templates + CSS/JS heredado           Maxima reutilizacion.
```

```text
                                                                                        Sin introducir framework adicional
 Pruebas                                   Django TestCase / TransactionTestCase
                                                                                        obligatorio.
```

```text
 Movil                                     PWA; WebView opcional                        Una sola base de codigo y backend.
```

### 3.1 Entorno virtual y variables
El entorno virtual .venv contiene Python y dependencias. El archivo .env contiene configuracion privada. Ambos son necesarios
y cumplen funciones distintas.
```text
  # Windows PowerShell
  py -3.12 -m venv .venv
  .venv\Scripts\Activate.ps1
```

```text
  # Linux / WSL / hosting
  python3.12 -m venv .venv
  source .venv/bin/activate
```

```text
  python -m pip install --upgrade pip
  pip install "Django~=5.2" "psycopg[binary]" django-environ whitenoise gunicorn
  pip freeze > requirements.txt
```

### 3.2 Variables minimas
```text
  DJANGO_SETTINGS_MODULE=config.settings.local
  SECRET_KEY=change-me
  DEBUG=True
  ALLOWED_HOSTS=127.0.0.1,localhost
  DATABASE_URL=postgresql://loteria_user:password@127.0.0.1:5432/loteria_django
  ACADEMIC_SIMULATION=True
  PLATFORM_TIME_ZONE=America/Guayaquil
```

.env: Debe estar en .gitignore. .env.example conserva solamente nombres y valores ficticios.

## 4. Estructura de proyecto
```text
  loteria-binaria-django/
  |-- manage.py
```

|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- config/
```text
 |        |-- settings/base.py
 |        |-- settings/local.py
 |        |-- settings/production.py
 |        |-- urls.py
 |        |-- wsgi.py
 |        `-- asgi.py
```
|-- apps/
```text
 |        |-- accounts/
 |        |-- core/
 |        |-- finance/
 |        |-- vendors/
 |        `-- lottery/
```
|-- templates/
```text
 |        |-- base.html
 |        |-- accounts/
 |        |-- core/
 |        `-- dashboards/
```
|-- static/css/
|-- static/js/
|-- static/img/
|-- seed_data/legacy/
`-- tests/

```text
App                                        Responsabilidad                               No debe contener
```

```text
                                           Usuario, registro, login, modos, terminos y
accounts                                                                                 Calculos financieros o sorteos.
                                           perfiles propios.
```

```text
                                           Wallets, movimientos, recargas,
finance                                    conversiones, transferencias y retiro         HTML especifico de vendedores/sorteos.
                                           simulado.
```

```text
                                           Perfil vendedor, compra de inventario y
vendors                                                                                  Autenticacion base.
                                           solicitudes Cliente-Vendedor.
```

```text
                                           Productos, eventos, boletos, resultados,
lottery                                                                                  Credenciales o configuracion de hosting.
                                           evaluacion y cancelacion.
```

```text
                                           Landing, dashboards, auditoria y
core                                                                                     Reglas monetarias duplicadas.
                                           utilidades transversales.
```

## 5. Modelo de datos MVP
```text
Modelo                          Proposito                         Campos principales               Controles
```

```text
                                                                  AbstractUser + document,         username/email/document
accounts.User                   Cuenta principal                  phone, birth_date, status,       unicos; AUTH_USER_MODEL
                                                                  created_at                       desde inicio
```

```text
                                                                  kind, version, title, content,   unique(kind,version); no editar
accounts.TermsVersion           Version legal
                                                                  effective_at, is_active          version aceptada
```

```text
                                                                  user, terms_version,
accounts.TermsAcceptance        Aceptacion                                                         unique(user,terms_version)
                                                                  accepted_at, ip_address
```

```text
                                                                  actor, active_mode, action,
core.AuditEvent                 Auditoria                         resource_type/id, reason,        append-only; sin secretos
                                                                  metadata, created_at
```

```text
                                                                  user, currency,
                                                                                                   unique(user,currency); checks
finance.Wallet                  Wallet por moneda                 available_minor,
                                                                                                   no negativos
                                                                  reserved_minor, status
```

```text
                                                                  wallet, operation_id, type,
                                                                  direction, amount_minor,         append-only; amount>0; index
finance.Movement                Movimiento visible
                                                                  balance_after_minor,             operation_id
                                                                  description, created_at
```

```text
                                                                  user, amount_real_minor,
finance.TopUp                   Recarga simulada                  status, operation_id,            operation_id unico; monto>0
                                                                  confirmed_at
```

```text
                                                                  user, gross_virtual_minor,
finance.VirtualToRealConversi                                     fee_virtual_minor,               gross=fee+net; operation_id
                                Conversion 90/10
on                                                                net_real_minor, status,          unico
                                                                  operation_id
```

```text
                                                                  sender, recipient,
                                                                                                   sender!=recipient; operation_id
finance.VirtualTransfer         Transferencia                     amount_virtual_minor, status,
                                                                                                   unico
                                                                  operation_id
```

```text
                                                                                                   one-to-one; ACTIVE para
vendors.VendorProfile           Habilitacion vendedor             user, status, activated_at
                                                                                                   operar
```

```text
                                                                  vendor, virtual_minor,
vendors.VendorInventoryPurch                                                                       virtual_minor%100=0;
                                Compra 0,90->1,00                 real_cost_minor, status,
ase                                                                                                operation_id unico
                                                                  operation_id
```

```text
                                                                  client, amount_minor, status,
                                                                                                   monto>0; estado terminal
vendors.ConversionRequest       Solicitud REAL->VIRTUAL           expires_at, completed_at,
                                                                                                   unico
                                                                  operation_id
```

```text
vendors.ConversionAssignme                                        request, vendor, status,
                                Asignacion                                                         una ACTIVA por request
nt                                                                assigned_at, released_at
```

```text
                                                                                                   code unico; seed
                                                                  code, name, allowed_symbols,
lottery.LotteryProduct          Producto oficial                                                   OCTAL/DECIMAL/HEXADECI
                                                                  selection_count, is_active
                                                                                                   MAL
```

```text
                                                                  product, name, sales_open_at,
                                                                  sales_close_at, draw_at,         sales_close_at=draw_at-10m;
lottery.DrawEvent               Evento
                                                                  price_minor, prize_minor,        published immutable
                                                                  status, cancellation_reason
```

```text
    Modelo                              Proposito                           Campos principales                 Controles
```

```text
                                                                            user, event, normalized_key,
                                                                            price_minor,
                                                                                                               unique(event,normalized_key);
    lottery.Ticket                      Boleto                              ownership_status,
                                                                                                               no delete
                                                                            evaluation_status,
                                                                            award_minor, credited_at
```

```text
                                                                            event, winning_key,
    lottery.DrawResult                  Resultado                           published_by, reason,              one-to-one event; immutable
                                                                            published_at
```

### 5.1 Decisiones de modelado
- BigAutoField para User y UUIDField para operaciones y agregados expuestos, segun simplicidad de implementacion.
- TextChoices para estados y monedas. Los valores del navegador nunca se aplican sin validar la transicion.
- BigIntegerField para todo monto. Las funciones de presentacion convierten a formato decimal.
- Movimiento visible simplificado, no ledger de doble entrada. Aun asi, es append-only y correlacionado.
- No se crean las 101 tablas del diccionario completo. Cada modelo incluido responde a una funcion visible del MVP.
- Los modelos fuera de alcance se mantienen en los documentos fuente, no como tablas vacias.

### 5.2 Orden de migraciones
## 14. Crear proyecto y apps sin ejecutar migrate.
## 15. Definir accounts.User y AUTH_USER_MODEL.
## 16. Generar accounts/0001_initial.py.
## 17. Configurar PostgreSQL y ejecutar migrate por primera vez.
## 18. Agregar TermsVersion/Acceptance y AuditEvent.
## 19. Agregar Wallet/Movement y operaciones financieras.
## 20. Agregar VendorProfile/Request/Assignment.
## 21. Agregar LotteryProduct/Event/Ticket/Result.
## 22. Crear constraints e indices en migraciones explicitas.
## 23. Probar migracion limpia desde una base nueva antes de desplegar.

## 6. Servicios y transacciones
```text
    Servicio                                         Responsabilidad                                Control principal
```

```text
                                                     Valida unicidad, edad, terminos; crea
    accounts.services.register_user                                                                 atomic
                                                     usuario y wallets.
```

```text
                                                     Valida rol asignado, cambia                    POST + Groups/perfil + auditoría; modo
    accounts.services.change_active_mode             session["active_mode"] y regenera              CLIENTE concede funciones completas
                                                     navegación sin conceder roles.                 de Cliente.
```

```text
    finance.services.confirm_topup                   Acredita REAL 1:1 y crea movimiento.           lock wallet + operation_id
```

```text
                                                     Debita VIRTUAL, acredita REAL, registra
    finance.services.convert_virtual_to_real                                                        locks dos wallets + atomic
                                                     fee.
```

```text
    finance.services.transfer_virtual                Mueve VIRTUAL entre clientes.                  locks ordenados de wallets + atomic
```

```text
    vendors.services.purchase_inventory              Aplica 0,90/1,00 y registra compra.            locks wallets + atomic
```

```text
    vendors.services.create_request                  Reserva REAL y crea vencimiento.               lock wallet + atomic
```

```text
    vendors.services.assign_request                  Primer vendedor toma la solicitud.             lock request + unique activa
```

```text
    vendors.services.complete_request                Intercambia REAL/VIRTUAL y finaliza.           locks request/asignacion/wallets + atomic
```

```text
    vendors.services.process_expired_reques
                                                     Fallback o libera reserva.                     command idempotente
    ts
```

```text
    Servicio                                     Responsabilidad                                  Control principal
```

```text
    lottery.services.purchase_ticket             Valida y compra boleto.                          lock wallet/event + unique ticket
```

```text
    lottery.services.cancel_event                Reembolsa boletos y cancela.                     lock event/tickets/wallets + atomic
```

```text
    lottery.services.publish_result              Fija resultado, evalua y acredita.               one-to-one result + locks + atomic
```

```text
    Regla de implementacion: Las vistas deben ser delgadas: validan formulario, llaman al servicio, muestran mensaje y
    redirigen. No deben repetir formulas o transiciones.
```

### 6.1 Orden de bloqueos
- Bloquear filas siempre en un orden determinista para reducir deadlocks: usuario/wallet por ID ascendente, luego agregado
```text
       de negocio.
```
- Releer saldo y estado despues de adquirir el lock.
- No enviar correo, renderizar templates ni llamar servicios externos dentro de una transaccion.
- Capturar IntegrityError de la unicidad de boleto/asignacion y devolver un mensaje de dominio.

## 7. Migracion de la interfaz
## 24. Crear base.html con header, navegacion, mensajes y footer.
## 25. Reemplazar rutas relativas por {% url %} y recursos por {% static %}.
## 26. Convertir formularios HTML en Django Forms con CSRF.
## 27. Reemplazar fetch a JSON por contextos de vistas o endpoints POST puntuales.
## 28. Eliminar persistencia de saldos, boletos, solicitudes y roles en localStorage.
## 29. Mantener JavaScript para menu movil, filtros visuales, confirmaciones y temporizadores informativos.
## 30. Corregir textos de 5 %/15 %, 75 %, cardinalidades, estados y política de roles/modos heredada.
## 31. Validar responsive en escritorio, tablet y movil antes del despliegue.
```text
    Clave localStorage heredada                  Destino                                          Accion
```

```text
    usuario actual / rol / modo                  request.user + session active_mode               Eliminar autoridad local.
```

```text
    wallets                                      finance.Wallet                                   No escribir desde JS.
```

```text
    movimientos                                  finance.Movement                                 Consultar paginado.
```

```text
    boletos                                      lottery.Ticket                                   Crear solo por servicio.
```

```text
    solicitudes                                  vendors.ConversionRequest                        Cambiar solo por POST autorizado.
```

```text
    sorteos/eventos                              lottery models                                   Gestionar desde admin/panel.
```

## 8. Fases de desarrollo
```text
    Fase                               Nombre                              Trabajo                           Puerta de salida
```

```text
                                                                           Congelar cinco documentos,
                                                                                                             Reglas, plan, matriz, diseño de
                                                                           respaldar el ZIP, registrar
    Fase 0                             Baseline y respaldo                                                   interfaz y auditoría aprobados;
                                                                           contradicciones y aprobar
                                                                                                             copia intacta del frontend.
                                                                           DEC-MVP-001.
```

```text
                                                                           Crear .venv, instalar
                                                                           dependencias, iniciar
                                                                                                             manage.py check correcto; no
    Fase 1                             Entorno y esqueleto                 proyecto/config/apps, .env.exa
                                                                                                             se ejecuta migrate todavia.
                                                                           mple, settings y chequeo
                                                                           inicial.
```

```text
Fase      Nombre                             Trabajo                            Puerta de salida
```

```text
                                             Crear accounts.User, estados,
                                                                                Primera migracion de accounts
                                             terminos, aceptaciones,
Fase 2    Usuario personalizado                                                 lista antes de la migracion
                                             AUTH_USER_MODEL y
                                                                                general.
                                             admin basico.
```

```text
                                             Crear BD/usuario, configurar
                                             DATABASE_URL, aplicar              /admin/ accesible y tablas en
Fase 3    PostgreSQL y migracion inicial
                                             migraciones, crear                 PostgreSQL.
                                             superusuario.
```

```text
                                             Implementar core/audit,
                                             finance, vendors y lottery por     Migrations reproducibles y
Fase 4    Modelos y restricciones
                                             bloques con constraints e          modelo validado.
                                             indices.
```

```text
                                             Crear grupos, productos,
                                             wallets tecnicas,                  seed_demo idempotente y
Fase 5    Seeds y administracion
                                             usuarios/eventos demo y            panel maestro usable.
                                             ModelAdmin seguros.
```

```text
                                             Mover HTML a templates y
                                                                                Landing, selector y
                                             recursos a static; crear bases
                                                                                dashboards coinciden con el
                                             públicas/dashboard,
Fase 6    Importacion de interfaz                                               mapa de interfaz y no
                                             componentes, rutas del diseño
                                                                                contienen textos ni botones
                                             DI-MVP-DJANGO y
                                                                                contradictorios.
                                             responsive móvil.
```

```text
                                             Registro, login/logout, selector   Cliente puro entra directo;
                                             multirrol, active_mode,            multirrol obtiene funciones
Fase 7    Autenticacion y permisos           protección de rutas,               completas del modo elegido;
                                             aislamiento de modos y             pruebas de aislamiento
                                             conflictos por evento.             aprobadas.
```

```text
                                             Recarga 1:1, conversion 10%,
                                                                                Operaciones atomicas y
Fase 8    Wallets y finanzas                 transferencia, retiro simulado y
                                                                                movimientos persistidos.
                                             compra mayorista.
```

```text
                                             Reserva REAL, listado
                                             elegible, asignacion,              Flujo Cliente-Vendedor
Fase 9    Solicitudes
                                             confirmacion/cancelacion,          completo.
                                             expiracion y fallback.
```

```text
                                                                                Cliente puro y cuentas multirrol
                                             Productos, eventos, compra,
                                                                                en modo CLIENTE compran;
                                             unicidad, normalización,
                                                                                modos
Fase 10   Loteria y resultados               cancelación, resultado,
                                                                                VENDEDOR/ADMINISTRADO
                                             evaluación, créditos y conflicto
                                                                                R no compran; resultado
                                             del administrador participante.
                                                                                auditado.
```

```text
                                             Tests unitarios/integracion,
                                             accesos, concurrencia critica,     Suite minima verde y django
```
Fase 11   Pruebas y seguridad
```text
                                             validacion de despliegue y         check --deploy revisado.
                                             privacidad.
```

```text
                                             Subir Git, configurar
                                             hosting/PostgreSQL, variables,     URL publica funcional y
```
Fase 12   Despliegue
```text
                                             migrate, collectstatic,            reproducible.
                                             superusuario, seed y HTTPS.
```

```text
                                             Manifest, service worker
                                             seguro, instalacion PWA y, si      Aplicacion instalable
```
Fase 13   PWA / Android
```text
                                             se exige, contenedor               conectada al mismo backend.
                                             WebView.
```

Fase 0 - Baseline y respaldo
Congelar estos documentos, respaldar el ZIP, crear rama/carpeta Django y registrar contradicciones heredadas.

Puerta de salida: Cinco PDFs, copia intacta del frontend, auditoría y alcance aprobado.

Fase 1 - Entorno y esqueleto
Crear .venv, instalar dependencias, iniciar proyecto/config/apps, .env.example, settings y chequeo inicial.

Puerta de salida: manage.py check correcto; no se ejecuta migrate todavia.

```text
  django-admin startproject config .
  python manage.py startapp accounts apps/accounts
  python manage.py startapp core apps/core
  python manage.py startapp finance apps/finance
  python manage.py startapp vendors apps/vendors
  python manage.py startapp lottery apps/lottery
  python manage.py check
```

Fase 2 - Usuario personalizado
Crear accounts.User, estados, terminos, aceptaciones, AUTH_USER_MODEL y admin basico.

Puerta de salida: Primera migracion de accounts lista antes de la migracion general.

Fase 3 - PostgreSQL y migracion inicial
Crear BD/usuario, configurar DATABASE_URL, aplicar migraciones, crear superusuario.

Puerta de salida: /admin/ accesible y tablas en PostgreSQL.

```text
  python manage.py makemigrations accounts
  python manage.py migrate
  python manage.py createsuperuser
  python manage.py check
```

Fase 4 - Modelos y restricciones
Implementar core/audit, finance, vendors y lottery por bloques con constraints e indices.

Puerta de salida: Migrations reproducibles y modelo validado.

Fase 5 - Seeds y administracion
Crear grupos, productos, wallets tecnicas, usuarios/eventos demo y ModelAdmin seguros.

Puerta de salida: seed_demo idempotente y panel maestro usable.

```text
  python manage.py seed_demo
  python manage.py seed_demo          # segunda ejecucion: sin duplicados
```

Fase 6 - Importacion de interfaz
Mover HTML a templates y CSS/JS/img a static; base.html, urls y correccion responsive.

Puerta de salida: Landing y dashboards renderizan con Django sin JSON/localStorage autoritativo.

Fase 7 - Autenticacion y permisos
Registro, login/logout, selector de modo, proteccion de rutas y perfil.

Puerta de salida: Matriz basica de roles aprobada.

Fase 8 - Wallets y finanzas
Recarga 1:1, conversion 10%, transferencia, retiro simulado y compra mayorista.

Puerta de salida: Operaciones atomicas y movimientos persistidos.

Fase 9 - Solicitudes
Reserva REAL, listado elegible, asignacion, confirmacion/cancelacion, expiracion y fallback.

Puerta de salida: Flujo Cliente-Vendedor completo.

Fase 10 - Loteria y resultados
Productos, eventos, compra, unicidad, cancelacion, resultado, evaluacion y creditos.

Puerta de salida: Cliente elegible compra y consulta un boleto persistente.

Fase 11 - Pruebas y seguridad
Tests unitarios/integracion, accesos, concurrencia critica, validacion de despliegue y privacidad.

Puerta de salida: Suite minima verde y django check --deploy revisado.

```text
  python manage.py test
  python manage.py check
  python manage.py check --deploy --settings=config.settings.production
```

Fase 12 - Despliegue
Subir Git, configurar hosting/PostgreSQL, variables, migrate, collectstatic, superusuario, seed y HTTPS.

Puerta de salida: URL publica funcional y reproducible.

```text
  pip install -r requirements.txt
  python manage.py migrate --settings=config.settings.production
  python manage.py collectstatic --noinput --settings=config.settings.production
  python manage.py seed_demo --settings=config.settings.production
```

Fase 13 - PWA / Android
Manifest, service worker seguro, instalacion PWA y, si se exige, contenedor WebView.

```text
    Puerta de salida: Aplicacion instalable conectada al mismo backend.
```

## 9. Estrategia de pruebas
```text
    Nivel                                    Cobertura                                     Herramienta
```

```text
                                             Normalizacion, universos, comision 90/10,
    Unitarias                                                                              Funciones puras.
                                             costo 0,90, estados permitidos.
```

```text
                                             Constraints de saldo, wallet unica, boleto
    Modelos                                                                                TestCase + IntegrityError.
                                             unico y resultado unico.
```

```text
                                             Cada flujo exitoso y cada rollback por
    Servicios                                                                              TestCase/TransactionTestCase.
                                             error.
```

```text
                                             Acceso por rol, modo, estado y
    Permisos                                                                               Client Django.
                                             propietario.
```

```text
                                                                                           TransactionTestCase con conexiones
    Concurrencia critica                     Doble compra y doble asignacion.
                                                                                           separadas cuando el entorno lo permita.
```

```text
    Interfaz                                 Rutas, mensajes, CSRF y responsive.           Client + revision manual.
```

```text
                                             Migracion limpia, static, HTTPS y check --
    Despliegue                                                                             Entorno de staging/hosting.
                                             deploy.
```

## 10. Despliegue
- El proveedor final puede ser PythonAnywhere o Alwaysdata; la eleccion se hace en Fase 12 verificando soporte vigente de
```text
       Python, PostgreSQL, tareas programadas, dominio y HTTPS.
```
- No mantener dos despliegues productivos simultaneos. Elegir uno como fuente oficial y usar el otro solo como respaldo si
```text
       se documenta.
```
- Variables de produccion se configuran en el panel del proveedor o archivo no versionado.
- La base de produccion no se llena copiando SQLite; se aplican migraciones y seed controlado.
- Crear el superusuario de produccion de forma interactiva o mediante variables temporales, nunca con password fijo en Git.
- Configurar backup/export periodico de PostgreSQL y probar restauracion.
```text
    Chequeo de lanzamiento                                          Criterio
```

```text
                                                                    DEBUG=False, SECRET_KEY unica, ALLOWED_HOSTS y
    Configuracion
                                                                    CSRF_TRUSTED_ORIGINS correctos.
```

```text
                                                                    Migrations aplicadas y usuario DB con privilegios minimos
    Base
                                                                    necesarios.
```

```text
    Static                                                          collectstatic correcto; CSS, JS, logo y manifest cargan.
```

```text
    Cuentas                                                         Superusuario maestro y usuarios demo controlados.
```

```text
                                                                    HTTPS, cookies seguras, CSRF, formularios POST y no
    Seguridad
                                                                    secretos en repositorio.
```

```text
                                                                    Login, recarga, conversion, solicitud, compra, resultado y logout
    Funcional
                                                                    probados.
```

```text
    Movil                                                           Responsive y PWA instalable desde Android.
```

## 11. PWA y Android
- Crear manifest.webmanifest con nombre, short_name, iconos, start_url y display=standalone.
- Service worker cachea shell estatico y paginas publicas; no cachea respuestas autenticadas sensibles ni POST.
- Las operaciones requieren conexion. Si no hay red, mostrar estado offline y no simular confirmacion.
- Probar instalacion, login, navegacion atras, cierre de sesion y renovacion de contenido.
- Si se exige APK, usar un contenedor WebView del dominio HTTPS y mantener una unica fuente de datos.

## 12. Operaciones y mantenimiento
```text
    Tarea                                       Comando / mecanismo                           Frecuencia o disparador
```

```text
                                                python manage.py                              Programado por hosting; tambien manual
    Procesar solicitudes vencidas
                                                process_expired_requests                      para demo.
```

```text
    Crear datos demo                            python manage.py seed_demo                    Instalacion y reinicio controlado.
```

```text
                                                                                              Cada despliegue con migraciones
    Aplicar cambios de esquema                  python manage.py migrate
                                                                                              nuevas.
```

```text
    Recolectar estaticos                        python manage.py collectstatic --noinput      Cada despliegue que cambie frontend.
```

```text
    Chequeo general                             python manage.py check                        Antes de commit/despliegue.
```

```text
    Chequeo produccion                          python manage.py check --deploy               Antes de lanzar.
```

```text
    Backup                                      pg_dump o herramienta del proveedor           Politica definida en Fase 12.
```

## 13. Riesgos y mitigaciones
```text
    Riesgo                                      Impacto                                       Mitigacion
```

```text
    Intentar implementar las reglas
                                                Aumento drastico de alcance.                  Aplicar exclusiones y matriz MVP.
    empresariales completas
```

```text
                                                                                              Crear User custom antes del primer
    Migrar primero con User predeterminado      Cambio costoso de autenticacion.
                                                                                              migrate.
```

```text
    Conservar logica financiera en JavaScript   Fraude y estados divergentes.                 Servicios Django autoritativos.
```

```text
    Usar float                                  Errores de centesimas.                        BigIntegerField y pruebas.
```

```text
    Doble clic/concurrencia                     Duplicacion de efectos.                       Atomicidad, locks y constraints.
```

```text
                                                                                              Nueva migracion y CI/manual clean
    Editar migraciones aplicadas                Entornos incompatibles.
                                                                                              migrate.
```

```text
                                                                                              No cachear autenticado/POST; Cache-
    PWA cachea datos privados                   Fuga o estado obsoleto.
                                                                                              Control.
```

```text
                                                                                              Verificar provider en Fase 12 y mantener
    Hosting no soporta requisito                Bloqueo de lanzamiento.
                                                                                              configuracion portable.
```

## 14. Definicion de terminado del MVP
- Una instalacion limpia crea el proyecto desde requirements, .env, migrate y seed_demo.
- Existe superusuario maestro y panel visual de administrador.
- Registro, login, logout, roles, modos y restricciones funcionan en servidor.
- Wallets, movimientos, conversiones, transferencias, inventario y solicitudes persisten en PostgreSQL.

- Una cuenta con rol CLIENTE compra en modo CLIENTE, incluso si también posee VENDEDOR o ADMINISTRADOR; en
```text
    otros modos la compra se rechaza.
```
- Evento puede cerrarse, cancelarse con reembolso y recibir un resultado unico con premios no duplicados.
- El frontend es responsive, no depende de JSON/localStorage para negocio y se instala como PWA.
- El sitio esta publicado por HTTPS, con DEBUG=False, variables seguras y pruebas minimas verdes.
- La interfaz declara claramente que es una simulacion academica.

## 14. Integración obligatoria con el diseño de interfaz
El documento DI-MVP-DJANGO define rutas, páginas, navegación y componentes. No se considera terminada la Fase 6
cuando solo se copian los HTML: cada vista debe respetar permisos, estados vacíos, mensajes de error, CSRF, responsive y
el modo activo.
Se utilizarán plantillas base separadas para páginas públicas y paneles autenticados. Los datos se obtienen mediante
QuerySets y servicios; JavaScript queda limitado a interacción visual, filtros y mejoras progresivas.
- base_public.html: landing, login, registro y páginas legales.
- base_dashboard.html: barra superior, selector de modo, navegación por rol, mensajes y perfil.
- includes/: tarjetas, badges, tablas, paginación, formularios, estados vacíos y diálogos de confirmación.
- Cada acción sensible usa POST, CSRF, validación de active_mode, servicio atómico y patrón Post/Redirect/Get.
- En móvil se usa navegación inferior para Cliente y menú lateral desplegable para módulos extensos de
```text
    Vendedor/Administrador.
```

## 15. Decisión técnica de roles y conflictos
DEC-MVP-001 sustituye dentro del MVP Django la prohibición global basada en poseer roles adicionales. La autorización se
evalúa por cuenta activa, rol asignado, modo activo, recurso y estado.
- El usuario no puede elegir un rol no asignado.
- El modo CLIENTE concede compra de boletos y demás funciones completas de Cliente.
- El modo VENDEDOR no permite compra de boletos.
- El modo ADMINISTRADOR no permite compra de boletos.
- Un administrador con boleto en un evento no puede administrarlo.
- Un vendedor nunca puede atender solicitudes creadas por esa misma cuenta.
