---
title: "Reglas Maestras del MVP Django"
version: "1.1.0"
project: "Lotería Binaria - MVP Django"
source_pdf: "01_Reglas_Maestras_MVP_Django_v1.1.0.pdf"
date: "2026-07-29"
---

> **Documento canónico del MVP Django.** Conversión estructural desde el PDF oficial; conserva el contenido, la numeración y las tablas en bloques de texto cuando la maquetación no permite una tabla Markdown segura.

```text
                                         LOTERIA BINARIA
```

```text
                Reglas Maestras del MVP Django
         Baseline funcional, de seguridad y alcance para la conversion del frontend
                                        demostrativo
Proyecto                                                       Loteria Binaria - MVP Django
```

```text
Documento                                                      RM-MVP-DJANGO
```

```text
Version                                                        1.1.0
```

```text
Estado                                                         BASELINE CORREGIDA DE IMPLEMENTACIÓN
```

```text
Fecha / autor                                                  29 de julio de 2026 - Cristhian Herrera Nieto
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
                                                                   Definir sin ambiguedades el comportamiento obligatorio del MVP
```
Proposito
```text
                                                                   Django y las diferencias frente al frontend heredado.
```

```text
                                                                   Este documento manda dentro del MVP Django. Las reglas
                                                                   completas v1.4.0 siguen siendo referencia del proyecto
```
Autoridad
```text
                                                                   empresarial, pero solo se implementa el subconjunto
                                                                   expresamente seleccionado aqui.
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
## 1.   Autoridad documental y alcance
## 2.   Correcciones obligatorias al frontend heredado
## 3.   Reglas por dominio
## 4.   Funciones fuera de alcance
## 5.   Criterios de interpretacion y control de cambios
## 6.   Fuentes documentales

## 1. Autoridad documental y alcance
La finalidad es construir rapidamente una aplicacion Django funcional, persistida en PostgreSQL, desplegable y utilizable desde
navegador, PWA o contenedor movil. No es una implementacion reducida accidentalmente: es un producto academico con
alcance explicitamente limitado.

```text
    Principio central: Cuando el frontend antiguo, una nota previa o una suposicion contradigan este documento, se aplica
    esta baseline y se registra el cambio en la matriz de trazabilidad.
```

- Incluido: autenticacion real, roles, modos, PostgreSQL, wallets simuladas, movimientos, vendedores, solicitudes, sorteos
```text
       oficiales, boletos, resultados, panel maestro, despliegue y PWA.
```
- Excluido: dinero real, pasarelas, Redis, Celery, microservicios, ledger profesional completo, fondos complejos, sorteos
```text
       creados por usuarios, codigos privados, reclamos, evidencias, commit-reveal y aplicacion nativa independiente.
```
- El frontend ZIP se reutiliza como interfaz y fuente de datos demo, no como contrato de negocio.
- Toda operacion sensible debe confirmarse en el servidor y persistirse en PostgreSQL.

## 2. Correcciones obligatorias al frontend heredado
```text
    Tema                           Frontend actual                  Baseline Django                   Accion
```

```text
                                                                    PostgreSQL + sesiones             Los JSON solo alimentan
    Persistencia                   JSON + localStorage
                                                                    Django                            seed/demo.
```

```text
                                                                                                      Nunca se importan como texto
    Contrasenas                    Texto plano en usuarios.json     Hash de Django
                                                                                                      a produccion.
```

```text
    Recarga REAL                   5% de comision                   1:1 sin comision                  Aplica LOT-FIN-008.
```

```text
    VIRTUAL a REAL                 15% de comision                  10% de comision                   Aplica LOT-FIN-009.
```

```text
    Hexadecimal                    4 caracteres en datos demo       6 simbolos unicos 0-9/A-F         Aplica LOT-EVT-003.
```

```text
    Octal                          Hay configuracion de 5 digitos   4 simbolos unicos 0-7             Producto fijo del MVP.
```

```text
                                                                    Si la cuenta tiene rol CLIENTE
                                                                                                      Aplicar DEC-MVP-001;
                                   El código permite entrar como    y activa modo CLIENTE,
                                                                                                      eliminar el modo limitado
                                   CLIENTE y comprar, pero          recibe todas las funciones de
    Rol vendedor/admin                                                                                CLIENTE_FINANCIERO y
                                   textos y documentos lo           Cliente, aunque también tenga
                                                                                                      aislar permisos por
                                   contradicen.                     VENDEDOR o
                                                                                                      active_mode.
                                                                    ADMINISTRADOR.
```

```text
    Cierre                         10, 15 o 20 min configurables    10 minutos antes del sorteo       Aplica LOT-EVT-010.
```

```text
                                                                                                      Premio fijo configurado por
    Crecimiento del premio         75% visual                       No automatizado en MVP
                                                                                                      evento.
```

```text
                                                                    Un DrawResult unico e             Publicacion administrativa
    Resultado                      Simulacion local
                                                                    inmutable en PostgreSQL           auditada.
```

## 3. Reglas por dominio
Gobierno, autoridad y datos
MVP-GOV-001 - Autoridad del backend
```text
    Fuente                                                          LOT-GOV-001
```

```text
                                                                    Toda regla de identidad, permisos, saldo, tiempo, compra,
    Regla obligatoria                                               resultado y estado se decide en Django. El navegador solo envia
                                                                    comandos y presenta respuestas.
```

```text
 Fuente                                                      LOT-GOV-001
```

```text
                                                             Las vistas y servicios ignoran rol, saldo, precio, propietario,
 Aplicacion en Django                                        estado y fechas calculadas por el cliente. Se cargan desde la
                                                             sesion y PostgreSQL.
```

```text
                                                             Prueba manipulando formularios o URL: la operacion se rechaza
```
Evidencia minima
```text
                                                             o utiliza los valores del servidor.
```

MVP-GOV-002 - PostgreSQL como fuente de verdad
```text
 Fuente                                                      LOT-GOV-002
```

```text
                                                             Usuarios, wallets, movimientos, solicitudes, eventos, boletos y
 Regla obligatoria                                           resultados existen en PostgreSQL. JSON y localStorage dejan
                                                             de ser persistencia de negocio.
```

```text
                                                             Los JSON heredados se conservan solo como datos de
 Aplicacion en Django                                        referencia o entrada del seed. localStorage se limita a
                                                             preferencias visuales no sensibles.
```

```text
                                                             Cerrar navegador, borrar almacenamiento local y volver a iniciar:
```
Evidencia minima
```text
                                                             los datos confirmados permanecen.
```

MVP-GOV-003 - Atomicidad e idempotencia practica
```text
 Fuente                                                      LOT-GOV-003; LOT-FIN-007
```

```text
                                                             Una compra, conversion, transferencia, solicitud o reembolso no
```
Regla obligatoria
```text
                                                             puede quedar parcialmente aplicada ni duplicarse por doble clic.
```

```text
                                                             Usar transaction.atomic(), select_for_update() sobre
 Aplicacion en Django                                        wallets/solicitudes y token de formulario o identificador unico en
                                                             operaciones criticas.
```

```text
                                                             Provocar un error intermedio o enviar dos veces: existe cero o
```
Evidencia minima
```text
                                                             un unico efecto confirmado.
```

MVP-GOV-004 - Historia no destructiva
```text
 Fuente                                                      LOT-GOV-004; LOT-IAM-009
```

```text
                                                             Movimientos, boletos, resultados, aceptaciones y auditorias
```
Regla obligatoria
```text
                                                             confirmadas no se borran para corregir errores.
```

```text
                                                             Usar estados, anulacion o movimientos compensatorios. El
```
Aplicacion en Django
```text
                                                             admin no expone delete para registros historicos sensibles.
```

```text
                                                             Intentar borrar un movimiento o boleto confirmado: la accion no
```
Evidencia minima
```text
                                                             esta disponible o es rechazada.
```

MVP-GOV-005 - Hora oficial y zona horaria
```text
 Fuente                                                      LOT-GOV-005
```

```text
                                                             Aperturas, cierres, vencimientos y resultados usan la hora del
```
Regla obligatoria
```text
                                                             servidor, almacenada con zona horaria.
```

```text
                                                             USE_TZ=True; TIME_ZONE=America/Guayaquil;
 Aplicacion en Django                                        timezone.now() en backend. Nunca confiar en Date.now() para
                                                             autorizar.
```

```text
                                                             Cambiar la hora del dispositivo no altera cierre de ventas ni
```
Evidencia minima
```text
                                                             vencimiento de solicitud.
```

MVP-GOV-006 - Dinero entero
```text
 Fuente                                                      LOT-GOV-006
```

```text
                                                             Los montos se guardan en minor units enteras; se prohibe float
```
Regla obligatoria
```text
                                                             para saldos y calculos.
```

```text
                                                             BigIntegerField con sufijo _minor y funciones de formato. Por
```
Aplicacion en Django
```text
                                                             ejemplo, 10,25 se almacena como 1025.
```

```text
                                                             Pruebas de comisiones y saldos con importes pequenos
```
Evidencia minima
```text
                                                             conservan exactamente cada centesima.
```

MVP-GOV-007 - Entorno academico simulado
```text
 Fuente                                                      LOT-GOV-008
```

```text
                                                             Recargas, retiros, conversiones, premios y saldos no
```
Regla obligatoria
```text
                                                             representan dinero real ni autorizan juego comercial.
```

```text
                                                             Bandera ACADEMIC_SIMULATION=True, advertencia visible y
```
Aplicacion en Django
```text
                                                             ausencia de pasarela o datos de tarjeta.
```

```text
                                                             La interfaz y el despliegue muestran la naturaleza academica;
```
Evidencia minima
```text
                                                             no existe integracion de cobro.
```

MVP-GOV-008 - Migraciones inmutables
```text
 Fuente                                                      LOT-AUD-007
```

```text
                                                             Una migracion aplicada no se reescribe. Todo cambio posterior
```
Regla obligatoria
```text
                                                             crea una nueva migracion.
```

```text
                                                             Versionar migrations/ en Git; revisar makemigrations y probar
```
Aplicacion en Django
```text
                                                             migrate desde base vacia.
```

```text
                                                             La instalacion limpia aplica todas las migraciones en orden sin
```
Evidencia minima
```text
                                                             ediciones manuales a las antiguas.
```

Identidad, roles, modos y sesiones
MVP-IAM-001 - Usuario personalizado desde el inicio
```text
 Fuente                                                      LOT-IAM-007; decision tecnica MVP
```

```text
 Regla obligatoria                                           El proyecto define accounts.User antes del primer migrate.
```

```text
                                                             Extender AbstractUser, configurar AUTH_USER_MODEL y
```
Aplicacion en Django
```text
                                                             crear la migracion inicial de accounts antes de auth/admin.
```

```text
                                                             Una base vacia se migra sin sustituir posteriormente el modelo
```
Evidencia minima
```text
                                                             de usuario.
```

MVP-IAM-002 - Unicidad, mayoria de edad y terminos
```text
 Fuente                                                      LOT-IAM-007
```

```text
                                                             Usuario, correo y documento son unicos; el registro exige fecha
```
Regla obligatoria
```text
                                                             de nacimiento valida y aceptacion de terminos vigentes.
```

```text
                                                             UniqueConstraint/unique, validadores de formulario y
```
Aplicacion en Django
```text
                                                             TermsAcceptance versionada.
```

```text
                                                             Duplicados, menor de edad o registro sin terminos son
```
Evidencia minima
```text
                                                             rechazados con mensajes claros.
```

MVP-IAM-003 - Estados de cuenta
```text
 Fuente                                                       LOT-IAM-008; LOT-IAM-009
```

```text
                                                              Solo ACTIVO puede iniciar operaciones. SUSPENDIDO,
 Regla obligatoria                                            BLOQUEADO y DESACTIVADO conservan historial pero no
                                                              operan.
```

```text
                                                              AccountStatus TextChoices y mixin/politica comun en servicios.
```
Aplicacion en Django
```text
                                                              Desactivacion logica, no borrado fisico.
```

```text
                                                              Cada operacion de negocio falla para una cuenta no activa y no
```
Evidencia minima
```text
                                                              altera saldos.
```

MVP-IAM-004 - Roles globales y modo activo
```text
 Fuente                                                       LOT-IAM-002
```

```text
                                                              Los roles globales son CLIENTE, VENDEDOR y
 Regla obligatoria                                            ADMINISTRADOR. La sesión conserva exactamente un modo
                                                              activo compatible con un rol realmente asignado.
```

```text
                                                              Django Groups para roles; session["active_mode"] para
 Aplicacion en Django                                         CLIENTE, VENDEDOR o ADMINISTRADOR. El selector solo
                                                              muestra roles asignados y no crea privilegios.
```

```text
                                                              Un cliente puro entra directamente; una cuenta multirrol solo
 Evidencia minima                                             puede activar modos presentes en sus Groups y perfiles
                                                              habilitados.
```

MVP-IAM-005 - Permisos completos segun modo activo
```text
                                                              DEC-MVP-001; LOT-IAM-002. Adaptación aprobada
 Fuente                                                       exclusiva para el MVP Django; sustituye LOT-IAM-004
                                                              dentro de este proyecto.
```

```text
                                                              Una cuenta con rol CLIENTE y modo activo CLIENTE puede
 Regla obligatoria                                            comprar boletos oficiales y usar todas las funciones de Cliente,
                                                              aunque también posea VENDEDOR o ADMINISTRADOR.
```

```text
                                                              La política can_purchase_official_ticket exige cuenta ACTIVA,
                                                              rol CLIENTE, active_mode=CLIENTE, evento comprable, saldo
```
Aplicacion en Django
```text
                                                              y demás reglas. En esa sesión no se permiten endpoints
                                                              VENDEDOR/ADMINISTRADOR.
```

```text
                                                              Vendedor y administrador con modo CLIENTE compran
                                                              correctamente; las mismas cuentas en modo
```
Evidencia minima
```text
                                                              VENDEDOR/ADMINISTRADOR reciben 403. No hay mezcla de
                                                              privilegios.
```

MVP-IAM-006 - Proteccion de rutas
```text
 Fuente                                                       LOT-IAM-006
```

```text
                                                              Ocultar botones no concede seguridad; toda URL y POST debe
```
Regla obligatoria
```text
                                                              validar autenticacion, modo, rol y propiedad.
```

```text
                                                              LoginRequiredMixin, UserPassesTestMixin o decoradores
```
Aplicacion en Django
```text
                                                              propios, mas verificacion dentro del servicio.
```

```text
                                                              Acceso directo a /admin-dashboard/ o boleto ajeno no expone
```
Evidencia minima
```text
                                                              datos ni ejecuta acciones.
```

MVP-IAM-007 - Autenticacion Django
```text
 Fuente                                                       LOT-GOV-001; politica de privacidad
```

```text
                                                              Las contrasenas nunca se almacenan en JSON, texto plano ni
```
Regla obligatoria
```text
                                                              localStorage.
```

```text
                                                              Django password hash, AuthenticationForm, login(), logout(),
```
Aplicacion en Django
```text
                                                              CSRF y sesiones del servidor.
```

```text
                                                              La base solo contiene hashes; logout invalida el acceso y los
```
Evidencia minima
```text
                                                              POST sin CSRF se rechazan.
```

MVP-IAM-008 - Superusuario separado del rol de negocio
```text
 Fuente                                                       LOT-IAM-005; decision tecnica MVP
```

```text
                                                              El superusuario tecnico de /admin/ no equivale automaticamente
```
Regla obligatoria
```text
                                                              al rol visual ADMINISTRADOR.
```

```text
                                                              is_superuser controla Django Admin; Group ADMINISTRADOR
```
Aplicacion en Django
```text
                                                              controla el panel de negocio.
```

```text
                                                              Una cuenta admin de negocio sin is_staff no entra al Django
```
Evidencia minima
```text
                                                              Admin; el maestro si puede gestionarlo.
```

MVP-IAM-009 - Perfil e historial propios
```text
 Fuente                                                       LOT-IAM-003; LOT-IAM-008
```

```text
                                                              Cada persona consulta su perfil, wallets, movimientos,
 Regla obligatoria                                            solicitudes y boletos permitidos, incluso si no puede iniciar
                                                              nuevas operaciones.
```

```text
                                                              QuerySets filtrados por request.user; datos sensibles
```
Aplicacion en Django
```text
                                                              minimizados.
```

```text
                                                              No se puede cambiar un identificador de URL para leer recursos
```
Evidencia minima
```text
                                                              de otra cuenta.
```

MVP-IAM-010 - Cambio de modo controlado
```text
 Fuente                                                       LOT-IAM-002
```

```text
                                                              Cambiar de modo no modifica roles ni concede permisos
                                                              permanentes. El modo CLIENTE ofrece funciones completas de
```
Regla obligatoria
```text
                                                              Cliente; VENDEDOR y ADMINISTRADOR aíslan sus propias
                                                              funciones.
```

```text
                                                              Vista POST dedicada, validación contra Groups/perfiles,
 Aplicacion en Django                                         actualización de session["active_mode"], auditoría y
                                                              regeneración de navegación.
```

```text
                                                              La cuenta solo ve modos asignados; cada endpoint rechaza un
```
Evidencia minima
```text
                                                              modo incompatible y el cambio nunca otorga un rol nuevo.
```

Wallets y operaciones financieras simuladas
MVP-FIN-001 - Wallets REAL y VIRTUAL separadas
```text
 Fuente                                                       LOT-FIN-001
```

```text
                                                              Cada usuario tiene como maximo una wallet REAL y una
```
Regla obligatoria
```text
                                                              VIRTUAL. Las unidades nunca se suman entre si.
```

```text
 Fuente                                                      LOT-FIN-001
```

```text
                                                             UniqueConstraint(user,currency), CurrencyCode TextChoices y
```
Aplicacion en Django
```text
                                                             servicios por moneda.
```

```text
                                                             No se puede usar REAL para comprar boleto ni compensar un
```
Evidencia minima
```text
                                                             saldo VIRTUAL insuficiente.
```

MVP-FIN-002 - Saldos disponibles y reservados no negativos
```text
 Fuente                                                      LOT-FIN-006; LOT-FIN-007
```

```text
 Regla obligatoria                                           available_minor y reserved_minor no pueden quedar negativos.
```

```text
 Aplicacion en Django                                        CheckConstraint y actualizaciones bajo bloqueo de fila.
```

```text
 Evidencia minima                                            Dos debitos simultaneos no producen saldo negativo.
```

MVP-FIN-003 - Recarga academica 1:1 sin comision
```text
 Fuente                                                      LOT-FIN-008
```

```text
                                                             Una recarga simulada de 100,00 acredita 100,00 REAL. No se
```
Regla obligatoria
```text
                                                             aplica el 5% del frontend antiguo.
```

```text
                                                             TopUp confirmada crea movimiento de credito REAL por el
```
Aplicacion en Django
```text
                                                             monto exacto.
```

```text
 Evidencia minima                                            Recarga de 10000 minor deja incremento exacto de 10000.
```

MVP-FIN-004 - Conversion VIRTUAL a REAL con 10%
```text
 Fuente                                                      LOT-FIN-009; LOT-FIN-013
```

```text
                                                             Se debita el bruto VIRTUAL; 90% se acredita como REAL y 10%
```
Regla obligatoria
```text
                                                             se registra como comision. No se usa el 15% antiguo.
```

```text
                                                             Calculo entero: net=floor/algoritmo determinista; gross=net+fee.
```
Aplicacion en Django
```text
                                                             Bloqueo de ambas wallets.
```

```text
 Evidencia minima                                            500,00 VIRTUAL produce 450,00 REAL y 50,00 de comision.
```

MVP-FIN-005 - Retiro simulado sin segunda comision
```text
 Fuente                                                      LOT-FIN-010
```

```text
                                                             El retiro utiliza saldo REAL ya convertido y no cobra una
```
Regla obligatoria
```text
                                                             segunda comision de negocio.
```

```text
                                                             Withdrawal simplificado o movimiento de reserva/completado
```
Aplicacion en Django
```text
                                                             simulado, segun alcance de interfaz.
```

```text
 Evidencia minima                                            Retirar 450,00 reduce 450,00 REAL; no aparece otra tarifa.
```

MVP-FIN-006 - Transferencia VIRTUAL entre clientes
```text
 Fuente                                                      LOT-FIN-011
```

```text
                                                             Solo un CLIENTE activo puede transferir VIRTUAL a otro
```
Regla obligatoria
```text
                                                             CLIENTE activo; no se permite autoenvio ni REAL.
```

```text
                                                             Validar roles puros, recipient distinto, moneda VIRTUAL, saldo y
```
Aplicacion en Django
```text
                                                             transaction.atomic().
```

```text
                                                             Autoenvio, destinatario inactivo o saldo insuficiente se rechazan
```
Evidencia minima
```text
                                                             sin movimientos.
```

MVP-FIN-007 - Compra mayorista del vendedor
```text
 Fuente                                                      LOT-VND-001; LOT-FIN-013
```

```text
                                                             El vendedor paga 0,90 REAL por cada 1,00 VIRTUAL, en
```
Regla obligatoria
```text
                                                             incrementos completos de 1,00 VIRTUAL.
```

```text
                                                             VendorInventoryPurchase valida amount_virtual_minor % 100
```
Aplicacion en Django
```text
                                                             == 0 y costo exacto 90/100.
```

```text
                                                             Compra de 100,00 VIRTUAL debita 90,00 REAL y acredita
```
Evidencia minima
```text
                                                             100,00 VIRTUAL.
```

MVP-FIN-008 - Ganancia potencial y realizada
```text
 Fuente                                                      LOT-VND-002
```

```text
                                                             Comprar inventario crea margen potencial; la ganancia se
 Regla obligatoria                                           considera realizada al completar una solicitud y recibir REAL
                                                             1:1.
```

```text
                                                             Guardar costo y cantidad de cada compra o calcular resumen
```
Aplicacion en Django
```text
                                                             verificable desde compras y solicitudes completadas.
```

```text
                                                             Antes de vender, realized_profit=0; despues refleja la diferencia
```
Evidencia minima
```text
                                                             aplicable.
```

MVP-FIN-009 - Movimiento por cada efecto confirmado
```text
 Fuente                                                      LOT-FIN-012
```

```text
                                                             Toda recarga, conversion, transferencia, compra de boleto,
 Regla obligatoria                                           compra mayorista, solicitud, premio, reembolso o retiro crea
                                                             movimientos correlacionados.
```

```text
                                                             Movement es append-only y contiene operation_id, tipo,
```
Aplicacion en Django
```text
                                                             direccion, moneda, monto y descripcion.
```

```text
                                                             Desde una operacion se pueden localizar todos sus
```
Evidencia minima
```text
                                                             movimientos y viceversa.
```

MVP-FIN-010 - Correcciones controladas
```text
 Fuente                                                      LOT-GOV-004; LOT-AUD-003
```

```text
                                                             El administrador no escribe saldos directamente desde
 Regla obligatoria                                           formularios genericos. Una correccion exige servicio, motivo y
                                                             auditoria.
```

```text
                                                             Accion admin personalizada que crea movimiento
```
Aplicacion en Django
```text
                                                             ADJUSTMENT y AuditEvent.
```

```text
 Evidencia minima                                            No existe campo editable de saldo en el ModelAdmin normal.
```

MVP-FIN-011 - Bloqueo ante doble envio
```text
 Fuente                                                      LOT-GOV-003
```

```text
                                                             Botones y formularios financieros evitan doble confirmacion,
```
Regla obligatoria
```text
                                                             pero la defensa real esta en el backend.
```

```text
                                                             POST/Redirect/GET, identificador de operacion unico y bloqueo
```
Aplicacion en Django
```text
                                                             transaccional.
```

```text
 Evidencia minima                                            Doble clic o refresco no duplica el credito/debito.
```

MVP-FIN-012 - Prohibicion de datos de pago reales
```text
 Fuente                                                      LOT-GOV-008; politica de privacidad
```

```text
                                                             No se solicitan ni guardan numero de tarjeta, CVV, cuenta
```
Regla obligatoria
```text
                                                             bancaria ni credenciales financieras.
```

```text
                                                             Formulario de recarga solo solicita monto y confirma que es una
```
Aplicacion en Django
```text
                                                             simulacion.
```

```text
                                                             Revisar modelos, formularios y logs: no existen campos de
```
Evidencia minima
```text
                                                             tarjeta o cuenta bancaria.
```

Vendedores y solicitudes Cliente - Vendedor
MVP-VND-001 - Creacion de solicitud y reserva
```text
 Fuente                                                      LOT-VND-003
```

```text
                                                             El Cliente no convierte REAL a VIRTUAL de inmediato: crea una
```
Regla obligatoria
```text
                                                             solicitud y el monto pasa de disponible a reservado.
```

```text
                                                             Bloquear wallet REAL, validar saldo, mover available a reserved
```
Aplicacion en Django
```text
                                                             y crear ConversionRequest PENDIENTE en una transaccion.
```

```text
                                                             Saldo insuficiente no crea solicitud; solicitud valida reserva
```
Evidencia minima
```text
                                                             exactamente el monto.
```

MVP-VND-002 - Visibilidad elegible
```text
 Fuente                                                      LOT-VND-004
```

```text
                                                             Solo vendedores activos con VIRTUAL disponible suficiente ven
```
Regla obligatoria
```text
                                                             una solicitud; nunca el propio solicitante.
```

```text
                                                             QuerySet filtra profile ACTIVE, request PENDIENTE y saldo. La
 Aplicacion en Django                                        deteccion avanzada de cuentas relacionadas queda fuera del
                                                             MVP.
```

```text
 Evidencia minima                                            Vendedor insolvente o mismo usuario no recibe la solicitud.
```

MVP-VND-003 - Asignacion atomica
```text
 Fuente                                                      LOT-VND-005
```

```text
                                                             La primera asignacion valida gana; una solicitud solo tiene una
```
Regla obligatoria
```text
                                                             asignacion ACTIVA.
```

```text
                                                             select_for_update sobre request y UniqueConstraint condicional
```
Aplicacion en Django
```text
                                                             para asignacion activa cuando sea viable.
```

```text
 Evidencia minima                                            Dos vendedores concurrentes: solo uno recibe asignacion.
```

MVP-VND-004 - Plazo total de cinco minutos
```text
 Fuente                                                      LOT-VND-006
```

```text
                                                             expires_at se calcula al crear la solicitud y no se extiende al
```
Regla obligatoria
```text
                                                             tomarla.
```

```text
                                                             expires_at=created_at+5 minutos; todas las acciones usan
```
Aplicacion en Django
```text
                                                             timezone.now().
```

```text
 Evidencia minima                                            Tomarla a los 4:50 deja aproximadamente 10 segundos.
```

MVP-VND-005 - Cancelacion de asignacion
```text
 Fuente                                                        LOT-VND-008
```

```text
                                                               Si el vendedor cancela antes del vencimiento, la solicitud vuelve
```
Regla obligatoria
```text
                                                               a PENDIENTE y el REAL del cliente sigue reservado.
```

```text
                                                               Asignacion LIBERADA; request EN_PROCESO->PENDIENTE;
```
Aplicacion en Django
```text
                                                               no mover wallets.
```

```text
 Evidencia minima                                              Otro vendedor puede tomarla y la reserva permanece.
```

MVP-VND-006 - Confirmacion por vendedor
```text
 Fuente                                                        LOT-VND-007
```

```text
                                                               La confirmacion intercambia de forma atomica: VIRTUAL
```
Regla obligatoria
```text
                                                               vendedor->cliente y REAL reservado cliente->vendedor.
```

```text
                                                               Bloquear request, assignment y cuatro wallets; validar saldo;
 Aplicacion en Django                                          actualizar todos los saldos, movimientos y estado en
                                                               transaction.atomic().
```

```text
 Evidencia minima                                              Un fallo despues del primer calculo revierte todo.
```

MVP-VND-007 - Finalizacion unica
```text
 Fuente                                                        LOT-VND-010
```

```text
                                                               Una solicitud solo puede terminar una vez: por vendedor,
```
Regla obligatoria
```text
                                                               plataforma o fallo de liquidez.
```

```text
                                                               Estados terminales y control transaccional; completed_at y
```
Aplicacion en Django
```text
                                                               operation_id unicos.
```

```text
                                                               Confirmacion y proceso de vencimiento concurrentes no
```
Evidencia minima
```text
                                                               duplican efectos.
```

MVP-VND-008 - Procesamiento de vencidas sin Celery
```text
 Fuente                                                        LOT-VND-009; adaptacion MVP
```

```text
                                                               Un comando Django procesa solicitudes vencidas. En
 Regla obligatoria                                             produccion puede ejecutarse mediante el programador del
                                                               hosting.
```

```text
                                                               Management command process_expired_requests con
```
Aplicacion en Django
```text
                                                               transacciones e idempotencia.
```

```text
 Evidencia minima                                              Ejecutarlo dos veces deja el mismo resultado.
```

MVP-VND-009 - Fallback o liberacion
```text
 Fuente                                                        LOT-VND-009; LOT-VND-010
```

```text
                                                               Si la wallet general tiene VIRTUAL, completa la conversion; si
 Regla obligatoria                                             no, libera el REAL del cliente y marca
                                                               FALLIDA_POR_LIQUIDEZ.
```

```text
                                                               Wallet tecnica de plataforma creada por seed; servicio de
```
Aplicacion en Django
```text
                                                               expiracion bloquea request y wallets.
```

```text
                                                               No queda REAL reservado indefinidamente ni saldo negativo en
```
Evidencia minima
```text
                                                               plataforma.
```

MVP-VND-010 - Historial de la solicitud
```text
 Fuente                                                       LOT-AUD-001; estados v1.1.0
```

```text
                                                              Cada creacion, asignacion, liberacion, confirmacion o
```
Regla obligatoria
```text
                                                              vencimiento queda trazable.
```

```text
                                                              AuditEvent y/o ConversionRequestEvent simplificado con actor,
```
Aplicacion en Django
```text
                                                              estado anterior/nuevo, motivo y fecha.
```

```text
                                                              El detalle muestra la secuencia completa sin reescribir eventos
```
Evidencia minima
```text
                                                              previos.
```

Loteria oficial, boletos y resultados
MVP-EVT-001 - Productos y cardinalidad fijos
```text
 Fuente                                                       LOT-EVT-002; LOT-EVT-003
```

```text
                                                              OCTAL usa 0-7 y 4 simbolos distintos; DECIMAL usa 0-9 y 5
```
Regla obligatoria
```text
                                                              distintos; HEXADECIMAL usa 0-9/A-F y 6 distintos.
```

```text
                                                              LotteryProduct se crea por seed y el validador del servidor aplica
```
Aplicacion en Django
```text
                                                              universo, longitud, mayusculas y no repeticion.
```

```text
                                                              Se rechazan entradas cortas, largas, repetidas o fuera de
```
Evidencia minima
```text
                                                              universo.
```

MVP-EVT-002 - Normalizacion canonica
```text
 Fuente                                                       LOT-EVT-004
```

```text
                                                              El orden no diferencia combinaciones; antes de comparar se
```
Regla obligatoria
```text
                                                              ordenan los simbolos con una regla estable.
```

```text
                                                              normalize_selection() compartida por formularios, servicios y
```
Aplicacion en Django
```text
                                                              seed.
```

```text
 Evidencia minima                                             7-4-2-0 y 0-2-4-7 producen la misma normalized_key.
```

MVP-EVT-003 - Unicidad por evento
```text
 Fuente                                                       LOT-EVT-001
```

```text
                                                              Una normalized_key solo puede venderse una vez dentro del
```
Regla obligatoria
```text
                                                              mismo evento.
```

```text
                                                              UniqueConstraint(event, normalized_key) en Ticket y captura de
```
Aplicacion en Django
```text
                                                              IntegrityError.
```

```text
 Evidencia minima                                             Dos compras concurrentes: solo una confirma.
```

MVP-EVT-004 - Estados simplificados del evento
```text
 Fuente                                                       Estados v1.1.0; adaptacion MVP
```

```text
                                                              Estados: BORRADOR, PROGRAMADO, PUBLICADO,
 Regla obligatoria                                            VENTAS_ABIERTAS, VENTAS_CERRADAS,
                                                              RESULTADO_FIJADO, FINALIZADO y CANCELADO.
```

```text
                                                              TextChoices y servicio de transicion; no se acepta un estado
```
Aplicacion en Django
```text
                                                              enviado como autoridad por el navegador.
```

```text
 Evidencia minima                                             Las transiciones no permitidas son rechazadas.
```

MVP-EVT-005 - Cierre diez minutos antes
```text
 Fuente                                                      LOT-EVT-010
```

```text
 Regla obligatoria                                           Las ventas cierran exactamente diez minutos antes de draw_at.
```

```text
                                                             sales_close_at se calcula o valida como draw_at-10 min y el
```
Aplicacion en Django
```text
                                                             servicio compara con hora oficial.
```

```text
                                                             Compra un segundo antes puede continuar; un segundo
```
Evidencia minima
```text
                                                             despues falla.
```

MVP-EVT-006 - Compra solo para Cliente elegible
```text
                                                             DEC-MVP-001; LOT-IAM-003; adaptación MVP de LOT-
```
Fuente
```text
                                                             IAM-004
```

```text
                                                             Puede comprar una cuenta ACTIVA con rol CLIENTE y modo
 Regla obligatoria                                           activo CLIENTE. Tener además VENDEDOR o
                                                             ADMINISTRADOR no reduce los permisos del modo CLIENTE.
```

```text
                                                             Política central can_purchase_official_ticket(user, active_mode,
```
Aplicacion en Django
```text
                                                             event) usada por vistas, servicio y pruebas.
```

```text
                                                             Cliente puro, vendedor+cliente y administrador+cliente compran
 Evidencia minima                                            en modo CLIENTE; todos son rechazados en modos
                                                             incompatibles o con cuenta suspendida.
```

MVP-EVT-007 - Compra atomica
```text
 Fuente                                                      LOT-EVT-016
```

```text
                                                             Validar usuario, evento, hora, saldo, seleccion y unicidad;
 Regla obligatoria                                           debitar VIRTUAL, crear Ticket y Movement en una unica
                                                             transaccion.
```

```text
                                                             select_for_update en wallet/event; transaction.atomic; constraint
```
Aplicacion en Django
```text
                                                             de unicidad.
```

```text
 Evidencia minima                                            Fallo al crear Ticket revierte el debito.
```

MVP-EVT-008 - Evento publicado inmutable
```text
 Fuente                                                      LOT-EVT-007
```

```text
                                                             Precio, producto, fechas y premio de un evento publicado no se
```
Regla obligatoria
```text
                                                             editan mediante formularios normales.
```

```text
                                                             Model.clean()/servicio y ModelAdmin readonly_fields segun
```
Aplicacion en Django
```text
                                                             estado.
```

```text
                                                             Intentar cambiar precio o draw_at despues de publicar se
```
Evidencia minima
```text
                                                             rechaza.
```

MVP-EVT-009 - Cancelacion antes del resultado
```text
 Fuente                                                      LOT-EVT-018; LOT-EVT-019
```

```text
                                                             Un evento previo a RESULTADO_FIJADO puede cancelarse
```
Regla obligatoria
```text
                                                             con motivo y reembolso integro de cada boleto no reembolsado.
```

```text
                                                             Servicio cancel_event bloquea evento, tickets y wallets; marca
```
Aplicacion en Django
```text
                                                             tickets REEMBOLSADO y acredita precio una vez.
```

```text
 Evidencia minima                                            Repetir cancelacion no duplica reembolsos.
```

MVP-EVT-010 - Resultado unico e inmutable
```text
 Fuente                                                       LOT-PRZ-014
```

```text
                                                              Cada evento tiene como maximo un DrawResult. Una vez fijado,
```
Regla obligatoria
```text
                                                              no se edita ni regenera.
```

```text
                                                              OneToOneField(event), restriccion unica y admin action con
```
Aplicacion en Django
```text
                                                              confirmacion/motivo.
```

```text
                                                              Dos intentos de publicar resultado conservan el primero y
```
Evidencia minima
```text
                                                              rechazan el segundo.
```

MVP-EVT-011 - Evaluacion basica
```text
 Fuente                                                       LOT-PRZ-001; LOT-PRZ-002
```

```text
                                                              Coincidencia exacta obtiene premio mayor; coincidencia en
```
Regla obligatoria
```text
                                                              todos menos un simbolo obtiene devolucion del precio.
```

```text
                                                              Servicio evaluate_tickets usa conjuntos normalizados y actualiza
```
Aplicacion en Django
```text
                                                              evaluation_status/award_minor.
```

```text
                                                              Casos distancia 0, 1 y 2 producen mayor, devolucion y no
```
Evidencia minima
```text
                                                              premiado.
```

MVP-EVT-012 - Credito de premios exactamente una vez
```text
 Fuente                                                       LOT-PRZ-016
```

```text
                                                              Cada premio o devolucion se acredita una sola vez en
```
Regla obligatoria
```text
                                                              VIRTUAL.
```

```text
                                                              Ticket.credited_at/award_operation_id y transaccion con lock;
```
Aplicacion en Django
```text
                                                              reintento devuelve estado existente.
```

```text
 Evidencia minima                                             Reprocesar resultado no duplica saldo.
```

MVP-EVT-013 - Resultado publico sin datos personales
```text
 Fuente                                                       LOT-PRZ-018; politica de privacidad
```

```text
                                                              La pagina publica muestra evento, combinacion ganadora y
```
Regla obligatoria
```text
                                                              cifras agregadas, nunca identidad, documento, correo o wallet.
```

```text
 Aplicacion en Django                                         DTO/contexto con allowlist de campos publicos.
```

```text
                                                              Inspeccion de HTML/JSON no encuentra datos personales de
```
Evidencia minima
```text
                                                              ganadores.
```

MVP-EVT-014 - Sin reservas ni carrito en esta version
```text
 Fuente                                                       LOT-EVT-011; decision de alcance MVP
```

```text
                                                              El MVP realiza compra directa. Reservas de cinco minutos,
 Regla obligatoria                                            carrito y limite de 20% quedan documentados como ampliacion
                                                              futura.
```

```text
                                                              No crear modelos de carrito/reserva; la unicidad se resuelve al
```
Aplicacion en Django
```text
                                                              confirmar la compra.
```

```text
                                                              La interfaz no promete reserva temporal ni muestra funciones
```
Evidencia minima
```text
                                                              inexistentes.
```

MVP-EVT-015 - Premio fijo por evento
```text
 Fuente                                                      LOT-PRZ-003 a LOT-PRZ-011; decision de alcance MVP
```

```text
                                                             El administrador define prize_virtual_minor. Fondos, crecimiento
 Regla obligatoria                                           90%, acumulados y redondeo a cuartos no se automatizan en el
                                                             MVP.
```

```text
                                                             Eliminar textos antiguos de crecimiento 75% o marcarlos como
```
Aplicacion en Django
```text
                                                             funcionalidad futura.
```

```text
                                                             El premio mostrado coincide con el almacenado y no existe
```
Evidencia minima
```text
                                                             reparto financiero simulado oculto.
```

Administracion, auditoria, privacidad y despliegue
MVP-ADM-001 - Administracion con permisos
```text
 Fuente                                                      LOT-IAM-005
```

```text
                                                             El panel de negocio requiere rol y modo ADMINISTRADOR;
                                                             /admin/ requiere is_staff. Un administrador que tenga boleto en
```
Regla obligatoria
```text
                                                             un evento no puede publicar, cancelar ni fijar el resultado de ese
                                                             mismo evento.
```

```text
                                                             Mixins, Groups/permissions, acciones específicas y policy
```
Aplicacion en Django
```text
                                                             can_administer_event que verifica conflicto de participación.
```

```text
                                                             Cliente/vendedor reciben 403; administrador participante recibe
```
Evidencia minima
```text
                                                             conflicto 409/403 y otro administrador debe operar el evento.
```

MVP-ADM-002 - Motivo obligatorio
```text
 Fuente                                                      LOT-AUD-003
```

```text
                                                             Cambios de estado/rol, cancelacion, correccion de saldo y
```
Regla obligatoria
```text
                                                             publicacion de resultado requieren motivo.
```

```text
 Aplicacion en Django                                        Formularios de accion con reason no vacio y AuditEvent.
```

```text
 Evidencia minima                                            Accion sin motivo es rechazada.
```

MVP-ADM-003 - Auditoria minima
```text
 Fuente                                                      LOT-AUD-001; LOT-AUD-002
```

```text
                                                             Registrar actor, modo, accion, recurso, motivo, fecha, IP
```
Regla obligatoria
```text
                                                             aproximada cuando sea pertinente y metadata no sensible.
```

```text
                                                             Modelo AuditEvent append-only; nunca guardar contrasenas,
```
Aplicacion en Django
```text
                                                             tokens o secretos.
```

```text
                                                             Cada accion critica se localiza por actor/recurso y los logs no
```
Evidencia minima
```text
                                                             contienen secretos.
```

MVP-ADM-004 - Seed idempotente
```text
 Fuente                                                      LOT-GOV-003; practica de despliegue
```

```text
                                                             seed_demo puede ejecutarse varias veces sin duplicar
```
Regla obligatoria
```text
                                                             productos, roles, wallets tecnicas o usuarios demo.
```

```text
                                                             update_or_create por claves naturales; contrasenas demo solo
```
Aplicacion en Django
```text
                                                             en DEBUG y mediante set_password.
```

```text
 Evidencia minima                                            Dos ejecuciones mantienen los mismos registros esperados.
```

MVP-PRV-001 - Minimizacion de datos
```text
 Fuente                                                      Politica de privacidad v1.1.0
```

```text
                                                             Guardar solo identificacion y contacto necesarios para la
```
Regla obligatoria
```text
                                                             demostracion. No exponerlos en listados publicos.
```

```text
                                                             Separar contextos publicos/privados, permisos por propietario y
```
Aplicacion en Django
```text
                                                             campos limitados en templates.
```

```text
                                                             Revision de paginas publicas confirma ausencia de documento,
```
Evidencia minima
```text
                                                             telefono y correo.
```

MVP-PRV-002 - Terminos y privacidad versionados
```text
 Fuente                                                      LOT-IAM-007; Terms v1.1.0; Privacy v1.1.0
```

```text
                                                             Cada registro acepta una version concreta de terminos y
```
Regla obligatoria
```text
                                                             privacidad; la aceptacion es historica.
```

```text
                                                             TermsVersion y TermsAcceptance con version, fecha, usuario e
```
Aplicacion en Django
```text
                                                             IP opcional.
```

```text
                                                             Actualizar la version no altera aceptaciones anteriores y puede
```
Evidencia minima
```text
                                                             exigir nueva aceptacion.
```

MVP-SEC-001 - Secretos fuera del repositorio
```text
 Fuente                                                      Politica de privacidad; buenas practicas Django
```

```text
                                                             SECRET_KEY, DATABASE_URL y credenciales se cargan
```
Regla obligatoria
```text
                                                             desde .env y variables del hosting.
```

```text
                                                             .env en .gitignore; .env.example sin secretos; settings
```
Aplicacion en Django
```text
                                                             separados.
```

```text
 Evidencia minima                                            Busqueda en Git no encuentra claves reales.
```

MVP-SEC-002 - Configuracion de produccion
```text
 Fuente                                                      LOT-GOV-001; practica de despliegue
```

```text
                                                             En produccion: DEBUG=False, ALLOWED_HOSTS definido,
 Regla obligatoria                                           cookies seguras bajo HTTPS, CSRF confiable y static
                                                             recopilado.
```

```text
                                                             settings/production.py, WhiteNoise/Gunicorn o configuracion
```
Aplicacion en Django
```text
                                                             equivalente del proveedor.
```

```text
                                                             django check --deploy sin hallazgos criticos y sitio accesible por
```
Evidencia minima
```text
                                                             HTTPS.
```

MVP-DEP-001 - Despliegue reproducible
```text
 Fuente                                                      LOT-AUD-007; practica operativa
```

```text
                                                             El servidor se reconstruye desde Git, requirements, variables,
 Regla obligatoria                                           migraciones y seed; no depende de cambios manuales
                                                             invisibles.
```

```text
                                                             README/runbook con install, migrate, collectstatic,
```
Aplicacion en Django
```text
                                                             createsuperuser y seed.
```

```text
 Evidencia minima                                            Instalacion en base vacia produce una aplicacion funcional.
```

MVP-MOB-001 - PWA como primera aplicacion movil
```text
    Fuente                                                         Decision de alcance MVP
```

```text
                                                                   La web responsive se instala como PWA; un APK WebView es
    Regla obligatoria
                                                                   opcional despues del despliegue.
```

```text
                                                                   manifest.webmanifest, iconos, service worker y HTTPS. No
    Aplicacion en Django
                                                                   cachear POST ni permitir operaciones financieras offline.
```

```text
                                                                   Instalacion en Android abre la URL publica y las operaciones
    Evidencia minima
                                                                   siempre consultan el servidor.
```

MVP-MOB-002 - Una sola fuente para web y movil
```text
    Fuente                                                         LOT-GOV-002
```

```text
                                                                   Navegador, PWA y eventual WebView usan el mismo Django y
    Regla obligatoria
                                                                   PostgreSQL.
```

```text
    Aplicacion en Django                                           No duplicar usuarios ni datos en una base movil separada.
```

```text
                                                                   Una operacion realizada en web aparece al iniciar sesion desde
    Evidencia minima
                                                                   movil.
```

## 4. Funciones fuera de alcance
- Carrito y reservas temporales de combinaciones; compra directa con control de concurrencia.
- Limite del 20% durante el 80% inicial de preventa.
- Libro contable profesional de doble entrada y reconstruccion de proyecciones.
- Fondos de garantia, acumulados 50/25/15/10 y crecimiento automatico del premio.
- Commitment criptografico, semilla secreta, snapshot_hash e informe verificable por hash.
- Sorteos creados por usuarios, codigos privados, invitaciones, escrow, expulsiones y reclamos.
- Integracion de pagos, bancos, tarjetas, retiros reales o verificacion automatica de identidad.
- Redis, WebSocket, Celery/BullMQ y microservicios. Los vencimientos se resuelven con management commands
```text
       programables.
```
- Aplicacion movil nativa con API independiente. Se usa PWA y, opcionalmente, WebView de la misma web.
```text
    Regla de alcance: Una funcion excluida no debe aparecer como operativa en la interfaz. Puede mostrarse solo como futura,
    claramente etiquetada y sin botones que simulen persistencia.
```

## 5. Interpretacion y control de cambios
## 7. No inventar reglas ante una duda: buscar primero en este documento, el plan tecnico y la matriz.
## 8. Si una necesidad no esta definida, registrarla como decision pendiente antes de codificar.
## 9. Toda modificacion de tarifa, rol, estado, modelo o flujo debe actualizar los tres PDFs y generar una nueva version.
## 10. No editar una migracion ya aplicada; crear una nueva migracion y documentar el impacto.
## 11. No usar el frontend como prueba de que una regla es correcta: el backend y las pruebas son la evidencia.
## 12. No mezclar este MVP con el monorepo empresarial de NestJS/Prisma salvo una decision posterior expresa.

## 6. Fuentes documentales
```text
    Fuente                                   Version                                      Uso en esta baseline
```

```text
                                                                                          Reglas canonicas completas; se
    REGLAS-NEGOCIO.md                        v1.4.0
                                                                                          selecciono un subconjunto para el MVP.
```

```text
                                                                                          Estados canonicos; se simplificaron sin
    ESTADOS-Y-TRANSICIONES.md                v1.1.0
                                                                                          contradecir los flujos incluidos.
```

```text
Fuente                                         Version                                      Uso en esta baseline
```

```text
                                                                                            Tarifas, minor units y efectos economicos
FLUJOS-FINANCIEROS.md                          v1.1.0
                                                                                            simulados.
```

```text
                                                                                            Referencia histórica. El deny override de
                                                                                            LOT-IAM-004 queda sustituido en este
MATRIZ-DE-PERMISOS.md                          v1.1.0
                                                                                            MVP por DEC-MVP-001 para conservar
                                                                                            una selección de modo coherente.
```

```text
                                                                                            Referencia de integridad; no se copian
DICCIONARIO-DE-DATOS.md                        v1.1.0
                                                                                            sus 101 tablas.
```

```text
                                                                                            Escenarios canonicos usados para
MATRIZ-REGLA-PRUEBA.md / CSV                   v1.1.0
                                                                                            seleccionar pruebas del MVP.
```

```text
                                                                                            Terminos academicos y conductas
TERMS-v1.1.0.md                                v1.1.0
                                                                                            prohibidas.
```

```text
                                                                                            Minimizacion, proteccion y naturaleza
PRIVACY-v1.1.0.md                              v1.1.0
                                                                                            academica.
```

```text
                                                                                            Pantallas, CSS, JS y datos que seran
Proyecto_HerreraNietoCristhian (6).zip         Frontend demo
                                                                                            migrados a templates y seed.
```

## 7. Decisión DEC-MVP-001 - Roles y modos coherentes
Esta decisión corrige la contradicción detectada entre la interfaz existente y la primera versión de las Reglas Maestras. Es
exclusiva del MVP Django y no modifica la baseline empresarial del otro proyecto.
La asignación de roles pertenece al Administrador. La selección de modo pertenece al usuario autenticado y solo puede elegir
entre roles ya asignados. El modo activo determina todas las autorizaciones de la solicitud actual.
- CLIENTE: compra boletos, gestiona wallets, crea solicitudes, transfiere VIRTUAL y consulta historial.
- VENDEDOR: compra inventario, atiende solicitudes y consulta ventas; no compra boletos mientras ese modo esté activo.
- ADMINISTRADOR: administra usuarios, eventos, resultados y auditoría; no compra boletos mientras ese modo esté
```text
    activo.
```
- Una cuenta multirrol que cambia a CLIENTE obtiene funciones completas de Cliente. La presencia de otros roles no
```text
    constituye una denegación automática.
```
- No se permite mezclar permisos en una misma operación. Para usar otra capacidad debe cambiar de modo mediante
```text
    POST validado.
```
- El vendedor nunca atiende una solicitud propia. El administrador que participa en un evento no administra ese mismo
```text
    evento.
```

## 8. Registro de revisión v1.1.0
Revisión inicial de coherencia: 6,1/10 para uso como baseline Django. La interfaz era visualmente completa, pero existían
contradicciones entre reglas, textos y JavaScript.
Revisión posterior a correcciones documentales: 9,4/10. La nota no representa implementación terminada; faltan código
Django, migraciones y pruebas para alcanzar verificación total.
- Corregida la política de roles y modo activo.
- Eliminado CLIENTE_FINANCIERO como modo ambiguo.
- Mantenidas recarga 1:1, conversión 10 % y premio fijo del MVP.
- Añadida separación de funciones por evento para administradores participantes.
- Vinculado el documento de diseño de interfaz DI-MVP-DJANGO.
