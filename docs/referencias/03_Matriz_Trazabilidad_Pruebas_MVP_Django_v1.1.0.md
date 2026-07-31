---
title: "Matriz de Trazabilidad y Pruebas del MVP Django"
version: "1.1.0"
project: "Lotería Binaria - MVP Django"
source_pdf: "03_Matriz_Trazabilidad_Pruebas_MVP_Django_v1.1.0.pdf"
date: "2026-07-29"
---

> **Documento canónico del MVP Django.** Conversión estructural desde el PDF oficial; conserva el contenido, la numeración y las tablas en bloques de texto cuando la maquetación no permite una tabla Markdown segura.

```text
                                                                  LOTERIA BINARIA
```

```text
                                      Matriz de Trazabilidad y Pruebas
                                     Regla -> fuente -> fase -> implementacion -> control -> evidencia
Proyecto                                                                                 Loteria Binaria - MVP Django
```

```text
Documento                                                                                MT-MVP-DJANGO
```

```text
Version                                                                                  1.1.0
```

```text
Estado                                                                                   BASELINE CORREGIDA DE CONTROL
```

```text
Fecha / autor                                                                            29 de julio de 2026 - Cristhian Herrera Nieto
```

```text
                Baseline de referencia exclusiva para el MVP Django. No sustituye ni modifica la arquitectura empresarial del otro proyecto Loteria Binaria.
```

## Control del documento
```text
 Campo                                                                 Definicion
```

```text
                                                                       Evitar funciones olvidadas, reglas sin prueba, controles duplicados y desviaciones entre
```
Proposito
```text
                                                                       documentacion, migraciones, backend e interfaz.
```

```text
                                                                       Cada fila debe actualizarse durante el desarrollo. El estado inicial es PENDIENTE y solo
```
Autoridad
```text
                                                                       cambia con evidencia verificable.
```

```text
                                                                       Cualquier cambio funcional debe actualizar este documento y la matriz de trazabilidad antes
```
Regla de cambio
```text
                                                                       de modificar modelos, migraciones o vistas.
```

```text
                                                                       El codigo ejecutable y PostgreSQL deben cumplir esta baseline; el frontend heredado es una
```
Fuente de verdad
```text
                                                                       referencia visual, no una autoridad funcional.
```

```text
 Naturaleza                                                            Proyecto academico. No procesa dinero real, tarjetas, retiros bancarios ni loterias reguladas.
```

```text
                                                                       DI-MVP-DJANGO v1.0.0 define arquitectura de interfaz, rutas, componentes, responsive y
```
Documento complementario
```text
                                                                       comportamiento por modo.
```

## Contenido
## 1.   Uso y estados
## 2.   Matriz completa
## 3.   Pruebas de aceptacion por flujo
## 4.   Puertas de fase
## 5.   Registro de decisiones

## 1. Uso y estados
- Antes de implementar una funcion, localizar sus filas y confirmar regla, fuente y fase.
- Al crear un modelo/migracion, actualizar la columna de control de base de datos si cambia.
- Una regla no pasa a IMPLEMENTADA solo porque existe una pantalla; debe existir control de servidor.
- Una regla no pasa a VERIFICADA sin prueba automatizada o evidencia manual repetible.
- Toda exclusion se conserva en Reglas Maestras; no se marca como incumplimiento del MVP.
```text
    Estado                                                                                      Significado
```

```text
    PENDIENTE                                                                                   No existe implementacion aprobada.
```

```text
    EN_DESARROLLO                                                                               Hay codigo parcial; no cumple aun la evidencia.
```

```text
    IMPLEMENTADA                                                                                Existe codigo, migracion/control y revision funcional.
```

```text
    VERIFICADA                                                                                  La prueba o evidencia minima fue ejecutada correctamente.
```

```text
    BLOQUEADA                                                                                   Existe una dependencia o decision documentada pendiente.
```

```text
    NO_APLICA                                                                                   Solo cuando Reglas Maestras excluye expresamente la funcion.
```

## 2. Matriz completa
```text
                                                                                                                                          Prueba o evidencia
    Regla MVP               Fuente canonica          Fase                       Modelo / servicio             Control servidor / BD                                     Estado
                                                                                                                                          minima
```

```text
                                                                                                                                          Prueba manipulando
                                                                                                                                          formularios o URL: la
                                                                                settings, services,           transaction.atomic /
    MVP-GOV-001             LOT-GOV-001              Fases 1-13                                                                           operacion se rechaza o        PENDIENTE
                                                                                migrations                    servidor / PostgreSQL
                                                                                                                                          utiliza los valores del
                                                                                                                                          servidor.
```

```text
                                                                                                                                          Cerrar navegador, borrar
                                                                                settings, services,           transaction.atomic /        almacenamiento local y
    MVP-GOV-002             LOT-GOV-002              Fases 1-13                                                                                                         PENDIENTE
                                                                                migrations                    servidor / PostgreSQL       volver a iniciar: los datos
                                                                                                                                          confirmados permanecen.
```

```text
                                                                                                                                          Provocar un error
                            LOT-GOV-003; LOT-                                   settings, services,           transaction.atomic /        intermedio o enviar dos
    MVP-GOV-003                                      Fases 1-13                                                                                                         PENDIENTE
                            FIN-007                                             migrations                    servidor / PostgreSQL       veces: existe cero o un
                                                                                                                                          unico efecto confirmado.
```

```text
                                                                                                                                          Intentar borrar un
                                                                                                                                          movimiento o boleto
                            LOT-GOV-004; LOT-                                   settings, services,           transaction.atomic /
    MVP-GOV-004                                      Fases 1-13                                                                           confirmado: la accion no      PENDIENTE
                            IAM-009                                             migrations                    servidor / PostgreSQL
                                                                                                                                          esta disponible o es
                                                                                                                                          rechazada.
```

```text
                                                                                                                            Prueba o evidencia
Regla MVP     Fuente canonica           Fase                        Modelo / servicio           Control servidor / BD                                      Estado
                                                                                                                            minima
```

```text
                                                                                                                            Cambiar la hora del
                                                                    settings, services,         transaction.atomic /        dispositivo no altera cierre
MVP-GOV-005   LOT-GOV-005               Fases 1-13                                                                                                         PENDIENTE
                                                                    migrations                  servidor / PostgreSQL       de ventas ni vencimiento de
                                                                                                                            solicitud.
```

```text
                                                                                                                            Pruebas de comisiones y
                                                                                                                            saldos con importes
                                                                    settings, services,         transaction.atomic /
MVP-GOV-006   LOT-GOV-006               Fases 1-13                                                                          pequenos conservan             PENDIENTE
                                                                    migrations                  servidor / PostgreSQL
                                                                                                                            exactamente cada
                                                                                                                            centesima.
```

```text
                                                                                                                            La interfaz y el despliegue
                                                                    settings, services,         transaction.atomic /        muestran la naturaleza
MVP-GOV-007   LOT-GOV-008               Fases 1-13                                                                                                         PENDIENTE
                                                                    migrations                  servidor / PostgreSQL       academica; no existe
                                                                                                                            integracion de cobro.
```

```text
                                                                                                                            La instalacion limpia aplica
                                                                    settings, services,         transaction.atomic /        todas las migraciones en
MVP-GOV-008   LOT-AUD-007               Fases 1-13                                                                                                         PENDIENTE
                                                                    migrations                  servidor / PostgreSQL       orden sin ediciones
                                                                                                                            manuales a las antiguas.
```

```text
                                                                                                                            Una base vacia se migra
              LOT-IAM-007; decision                                 accounts.User, Groups,      decoradores, politicas,
MVP-IAM-001                             Fases 2, 7, 11                                                                      sin sustituir posteriormente   PENDIENTE
              tecnica MVP                                           session                     unique constraints
                                                                                                                            el modelo de usuario.
```

```text
                                                                                                                            Duplicados, menor de edad
                                                                    accounts.User, Groups,      decoradores, politicas,     o registro sin terminos son
MVP-IAM-002   LOT-IAM-007               Fases 2, 7, 11                                                                                                     PENDIENTE
                                                                    session                     unique constraints          rechazados con mensajes
                                                                                                                            claros.
```

```text
                                                                                                                            Cada operacion de negocio
              LOT-IAM-008; LOT-                                     accounts.User, Groups,      decoradores, politicas,
MVP-IAM-003                             Fases 2, 7, 11                                                                      falla para una cuenta no       PENDIENTE
              IAM-009                                               session                     unique constraints
                                                                                                                            activa y no altera saldos.
```

```text
                                                                                                                            Cliente puro entra
                                                                    accounts.User, Groups,      decoradores, politicas,     directamente; cuenta
MVP-IAM-004   LOT-IAM-002               Fases 2, 7, 11                                                                                                     PENDIENTE
                                                                    session                     unique constraints          multirrol solo activa roles
                                                                                                                            realmente asignados.
```

```text
                                                                                                                            Vendedor+Cliente y
                                                                                                                            Administrador+Cliente
              DEC-MVP-001; LOT-                                                                                             compran en modo
                                                                    accounts.User, Groups,      decoradores, politicas,
MVP-IAM-005   IAM-002; adaptación MVP   Fases 2, 7, 11                                                                      CLIENTE; en modo               PENDIENTE
                                                                    session                     unique constraints
              de LOT-IAM-004                                                                                                VENDEDOR/ADMINISTRA
                                                                                                                            DOR reciben 403 sin
                                                                                                                            efectos.
```

```text
                                                                                                                            Acceso directo a /admin-
                                                                    accounts.User, Groups,      decoradores, politicas,     dashboard/ o boleto ajeno
MVP-IAM-006   LOT-IAM-006               Fases 2, 7, 11                                                                                                     PENDIENTE
                                                                    session                     unique constraints          no expone datos ni ejecuta
                                                                                                                            acciones.
```

```text
                                                                                                                             Prueba o evidencia
Regla MVP     Fuente canonica            Fase                        Modelo / servicio           Control servidor / BD                                       Estado
                                                                                                                             minima
```

```text
                                                                                                                             La base solo contiene
              LOT-GOV-001; politica de                               accounts.User, Groups,      decoradores, politicas,     hashes; logout invalida el
MVP-IAM-007                              Fases 2, 7, 11                                                                                                      PENDIENTE
              privacidad                                             session                     unique constraints          acceso y los POST sin
                                                                                                                             CSRF se rechazan.
```

```text
                                                                                                                             Una cuenta admin de
                                                                                                                             negocio sin is_staff no entra
              LOT-IAM-005; decision                                  accounts.User, Groups,      decoradores, politicas,
MVP-IAM-008                              Fases 2, 7, 11                                                                      al Django Admin; el             PENDIENTE
              tecnica MVP                                            session                     unique constraints
                                                                                                                             maestro si puede
                                                                                                                             gestionarlo.
```

```text
                                                                                                                             No se puede cambiar un
              LOT-IAM-003; LOT-                                      accounts.User, Groups,      decoradores, politicas,     identificador de URL para
MVP-IAM-009                              Fases 2, 7, 11                                                                                                      PENDIENTE
              IAM-008                                                session                     unique constraints          leer recursos de otra
                                                                                                                             cuenta.
```

```text
                                                                                                                             Cambiar de modo modifica
                                                                                                                             permisos de sesión sin
                                                                     accounts.User, Groups,      decoradores, politicas,
MVP-IAM-010   LOT-IAM-002                Fases 2, 7, 11                                                                      crear roles; CLIENTE            PENDIENTE
                                                                     session                     unique constraints
                                                                                                                             ofrece funciones completas
                                                                                                                             y no mezcla privilegios.
```

```text
                                                                                                                             No se puede usar REAL
                                                                     Wallet, Movement y          locks de wallet, checks y   para comprar boleto ni
MVP-FIN-001   LOT-FIN-001                Fases 4, 8, 11                                                                                                      PENDIENTE
                                                                     operaciones                 operation_id                compensar un saldo
                                                                                                                             VIRTUAL insuficiente.
```

```text
                                                                     Wallet, Movement y          locks de wallet, checks y   Dos debitos simultaneos no
MVP-FIN-002   LOT-FIN-006; LOT-FIN-007   Fases 4, 8, 11                                                                                                      PENDIENTE
                                                                     operaciones                 operation_id                producen saldo negativo.
```

```text
                                                                                                                             Recarga de 10000 minor
                                                                     Wallet, Movement y          locks de wallet, checks y
MVP-FIN-003   LOT-FIN-008                Fases 4, 8, 11                                                                      deja incremento exacto de       PENDIENTE
                                                                     operaciones                 operation_id
                                                                                                                             10000.
```

```text
                                                                                                                             500,00 VIRTUAL produce
                                                                     Wallet, Movement y          locks de wallet, checks y
MVP-FIN-004   LOT-FIN-009; LOT-FIN-013   Fases 4, 8, 11                                                                      450,00 REAL y 50,00 de          PENDIENTE
                                                                     operaciones                 operation_id
                                                                                                                             comision.
```

```text
                                                                                                                             Retirar 450,00 reduce
                                                                     Wallet, Movement y          locks de wallet, checks y
MVP-FIN-005   LOT-FIN-010                Fases 4, 8, 11                                                                      450,00 REAL; no aparece         PENDIENTE
                                                                     operaciones                 operation_id
                                                                                                                             otra tarifa.
```

```text
                                                                                                                             Autoenvio, destinatario
                                                                     Wallet, Movement y          locks de wallet, checks y   inactivo o saldo insuficiente
MVP-FIN-006   LOT-FIN-011                Fases 4, 8, 11                                                                                                      PENDIENTE
                                                                     operaciones                 operation_id                se rechazan sin
                                                                                                                             movimientos.
```

```text
                                                                                                                             Compra de 100,00
              LOT-VND-001; LOT-                                      Wallet, Movement y          locks de wallet, checks y   VIRTUAL debita 90,00
MVP-FIN-007                              Fases 4, 8, 11                                                                                                      PENDIENTE
              FIN-013                                                operaciones                 operation_id                REAL y acredita 100,00
                                                                                                                             VIRTUAL.
```

```text
                                                                                                                             Prueba o evidencia
Regla MVP     Fuente canonica            Fase                        Modelo / servicio           Control servidor / BD                                      Estado
                                                                                                                             minima
```

```text
                                                                                                                             Antes de vender,
                                                                     Wallet, Movement y          locks de wallet, checks y   realized_profit=0; despues
MVP-FIN-008   LOT-VND-002                Fases 4, 8, 11                                                                                                     PENDIENTE
                                                                     operaciones                 operation_id                refleja la diferencia
                                                                                                                             aplicable.
```

```text
                                                                                                                             Desde una operacion se
                                                                     Wallet, Movement y          locks de wallet, checks y
MVP-FIN-009   LOT-FIN-012                Fases 4, 8, 11                                                                      pueden localizar todos sus     PENDIENTE
                                                                     operaciones                 operation_id
                                                                                                                             movimientos y viceversa.
```

```text
                                                                                                                             No existe campo editable
              LOT-GOV-004; LOT-                                      Wallet, Movement y          locks de wallet, checks y
MVP-FIN-010                              Fases 4, 8, 11                                                                      de saldo en el ModelAdmin      PENDIENTE
              AUD-003                                                operaciones                 operation_id
                                                                                                                             normal.
```

```text
                                                                     Wallet, Movement y          locks de wallet, checks y   Doble clic o refresco no
MVP-FIN-011   LOT-GOV-003                Fases 4, 8, 11                                                                                                     PENDIENTE
                                                                     operaciones                 operation_id                duplica el credito/debito.
```

```text
                                                                                                                             Revisar modelos,
              LOT-GOV-008; politica de                               Wallet, Movement y          locks de wallet, checks y   formularios y logs: no
MVP-FIN-012                              Fases 4, 8, 11                                                                                                     PENDIENTE
              privacidad                                             operaciones                 operation_id                existen campos de tarjeta o
                                                                                                                             cuenta bancaria.
```

```text
                                                                                                                             Saldo insuficiente no crea
                                                                     ConversionRequest/          locks, estados y comando    solicitud; solicitud valida
MVP-VND-001   LOT-VND-003                Fases 4, 9, 11                                                                                                     PENDIENTE
                                                                     Assignment                  de expiracion               reserva exactamente el
                                                                                                                             monto.
```

```text
                                                                                                                             Vendedor insolvente o
                                                                     ConversionRequest/          locks, estados y comando
MVP-VND-002   LOT-VND-004                Fases 4, 9, 11                                                                      mismo usuario no recibe la     PENDIENTE
                                                                     Assignment                  de expiracion
                                                                                                                             solicitud.
```

```text
                                                                                                                             Dos vendedores
                                                                     ConversionRequest/          locks, estados y comando
MVP-VND-003   LOT-VND-005                Fases 4, 9, 11                                                                      concurrentes: solo uno         PENDIENTE
                                                                     Assignment                  de expiracion
                                                                                                                             recibe asignacion.
```

```text
                                                                                                                             Tomarla a los 4:50 deja
                                                                     ConversionRequest/          locks, estados y comando
MVP-VND-004   LOT-VND-006                Fases 4, 9, 11                                                                      aproximadamente 10             PENDIENTE
                                                                     Assignment                  de expiracion
                                                                                                                             segundos.
```

```text
                                                                                                                             Otro vendedor puede
                                                                     ConversionRequest/          locks, estados y comando
MVP-VND-005   LOT-VND-008                Fases 4, 9, 11                                                                      tomarla y la reserva           PENDIENTE
                                                                     Assignment                  de expiracion
                                                                                                                             permanece.
```

```text
                                                                     ConversionRequest/          locks, estados y comando    Un fallo despues del primer
MVP-VND-006   LOT-VND-007                Fases 4, 9, 11                                                                                                     PENDIENTE
                                                                     Assignment                  de expiracion               calculo revierte todo.
```

```text
                                                                                                                             Confirmacion y proceso de
                                                                     ConversionRequest/          locks, estados y comando
MVP-VND-007   LOT-VND-010                Fases 4, 9, 11                                                                      vencimiento concurrentes       PENDIENTE
                                                                     Assignment                  de expiracion
                                                                                                                             no duplican efectos.
```

```text
              LOT-VND-009; adaptacion                                ConversionRequest/          locks, estados y comando    Ejecutarlo dos veces deja el
MVP-VND-008                              Fases 4, 9, 11                                                                                                     PENDIENTE
              MVP                                                    Assignment                  de expiracion               mismo resultado.
```

```text
                                                                                                                                 Prueba o evidencia
Regla MVP     Fuente canonica              Fase                        Modelo / servicio            Control servidor / BD                                         Estado
                                                                                                                                 minima
```

```text
                                                                                                                                 No queda REAL reservado
              LOT-VND-009; LOT-                                        ConversionRequest/           locks, estados y comando
MVP-VND-009                                Fases 4, 9, 11                                                                        indefinidamente ni saldo         PENDIENTE
              VND-010                                                  Assignment                   de expiracion
                                                                                                                                 negativo en plataforma.
```

```text
                                                                                                                                 El detalle muestra la
              LOT-AUD-001; estados                                     ConversionRequest/           locks, estados y comando
MVP-VND-010                                Fases 4, 9, 11                                                                        secuencia completa sin           PENDIENTE
              v1.1.0                                                   Assignment                   de expiracion
                                                                                                                                 reescribir eventos previos.
```

```text
                                                                                                                                 Se rechazan entradas
              LOT-EVT-002; LOT-                                        LotteryProduct, DrawEvent,   validadores, constraints y
MVP-EVT-001                                Fases 4, 10, 11                                                                       cortas, largas, repetidas o      PENDIENTE
              EVT-003                                                  Ticket, DrawResult           servicios de evento
                                                                                                                                 fuera de universo.
```

```text
                                                                       LotteryProduct, DrawEvent,   validadores, constraints y   7-4-2-0 y 0-2-4-7 producen
MVP-EVT-002   LOT-EVT-004                  Fases 4, 10, 11                                                                                                        PENDIENTE
                                                                       Ticket, DrawResult           servicios de evento          la misma normalized_key.
```

```text
                                                                       LotteryProduct, DrawEvent,   validadores, constraints y   Dos compras concurrentes:
MVP-EVT-003   LOT-EVT-001                  Fases 4, 10, 11                                                                                                        PENDIENTE
                                                                       Ticket, DrawResult           servicios de evento          solo una confirma.
```

```text
              Estados v1.1.0; adaptacion                               LotteryProduct, DrawEvent,   validadores, constraints y   Las transiciones no
MVP-EVT-004                                Fases 4, 10, 11                                                                                                        PENDIENTE
              MVP                                                      Ticket, DrawResult           servicios de evento          permitidas son rechazadas.
```

```text
                                                                                                                                 Compra un segundo antes
                                                                       LotteryProduct, DrawEvent,   validadores, constraints y
MVP-EVT-005   LOT-EVT-010                  Fases 4, 10, 11                                                                       puede continuar; un              PENDIENTE
                                                                       Ticket, DrawResult           servicios de evento
                                                                                                                                 segundo despues falla.
```

```text
                                                                                                                                 Cliente puro y multirrol en
                                                                                                                                 modo CLIENTE compran;
              DEC-MVP-001; LOT-
                                                                       LotteryProduct, DrawEvent,   validadores, constraints y   cuenta suspendida, modo
MVP-EVT-006   IAM-003; adaptación MVP      Fases 4, 10, 11                                                                                                        PENDIENTE
                                                                       Ticket, DrawResult           servicios de evento          VENDEDOR/ADMINISTRA
              de LOT-IAM-004
                                                                                                                                 DOR o cierre reciben
                                                                                                                                 rechazo.
```

```text
                                                                       LotteryProduct, DrawEvent,   validadores, constraints y   Fallo al crear Ticket revierte
MVP-EVT-007   LOT-EVT-016                  Fases 4, 10, 11                                                                                                        PENDIENTE
                                                                       Ticket, DrawResult           servicios de evento          el debito.
```

```text
                                                                                                                                 Intentar cambiar precio o
                                                                       LotteryProduct, DrawEvent,   validadores, constraints y
MVP-EVT-008   LOT-EVT-007                  Fases 4, 10, 11                                                                       draw_at despues de               PENDIENTE
                                                                       Ticket, DrawResult           servicios de evento
                                                                                                                                 publicar se rechaza.
```

```text
              LOT-EVT-018; LOT-                                        LotteryProduct, DrawEvent,   validadores, constraints y   Repetir cancelacion no
MVP-EVT-009                                Fases 4, 10, 11                                                                                                        PENDIENTE
              EVT-019                                                  Ticket, DrawResult           servicios de evento          duplica reembolsos.
```

```text
                                                                                                                                 Dos intentos de publicar
                                                                       LotteryProduct, DrawEvent,   validadores, constraints y   resultado conservan el
MVP-EVT-010   LOT-PRZ-014                  Fases 4, 10, 11                                                                                                        PENDIENTE
                                                                       Ticket, DrawResult           servicios de evento          primero y rechazan el
                                                                                                                                 segundo.
```

```text
                                                                                                                                 Casos distancia 0, 1 y 2
              LOT-PRZ-001; LOT-                                        LotteryProduct, DrawEvent,   validadores, constraints y
MVP-EVT-011                                Fases 4, 10, 11                                                                       producen mayor,                  PENDIENTE
              PRZ-002                                                  Ticket, DrawResult           servicios de evento
                                                                                                                                 devolucion y no premiado.
```

```text
                                                                                                                                    Prueba o evidencia
Regla MVP     Fuente canonica                 Fase                        Modelo / servicio            Control servidor / BD                                       Estado
                                                                                                                                    minima
```

```text
                                                                          LotteryProduct, DrawEvent,   validadores, constraints y   Reprocesar resultado no
MVP-EVT-012   LOT-PRZ-016                     Fases 4, 10, 11                                                                                                      PENDIENTE
                                                                          Ticket, DrawResult           servicios de evento          duplica saldo.
```

```text
                                                                                                                                    Inspeccion de HTML/JSON
              LOT-PRZ-018; politica de                                    LotteryProduct, DrawEvent,   validadores, constraints y
MVP-EVT-013                                   Fases 4, 10, 11                                                                       no encuentra datos             PENDIENTE
              privacidad                                                  Ticket, DrawResult           servicios de evento
                                                                                                                                    personales de ganadores.
```

```text
                                                                                                                                    La interfaz no promete
              LOT-EVT-011; decision de                                    LotteryProduct, DrawEvent,   validadores, constraints y
MVP-EVT-014                                   Fases 4, 10, 11                                                                       reserva temporal ni muestra    PENDIENTE
              alcance MVP                                                 Ticket, DrawResult           servicios de evento
                                                                                                                                    funciones inexistentes.
```

```text
                                                                                                                                    El premio mostrado
              LOT-PRZ-003 a LOT-
                                                                          LotteryProduct, DrawEvent,   validadores, constraints y   coincide con el almacenado
MVP-EVT-015   PRZ-011; decision de            Fases 4, 10, 11                                                                                                      PENDIENTE
                                                                          Ticket, DrawResult           servicios de evento          y no existe reparto
              alcance MVP
                                                                                                                                    financiero simulado oculto.
```

```text
                                                                                                                                    Cliente y vendedor reciben
                                                                                                       permisos, motivo y append-
MVP-ADM-001   LOT-IAM-005                     Fases 5, 7, 11              AuditEvent, Admin y panel                                 403 en rutas                   PENDIENTE
                                                                                                       only
                                                                                                                                    administrativas.
```

```text
                                                                                                       permisos, motivo y append-   Accion sin motivo es
MVP-ADM-002   LOT-AUD-003                     Fases 5, 7, 11              AuditEvent, Admin y panel                                                                PENDIENTE
                                                                                                       only                         rechazada.
```

```text
                                                                                                                                    Cada accion critica se
              LOT-AUD-001; LOT-                                                                        permisos, motivo y append-   localiza por actor/recurso y
MVP-ADM-003                                   Fases 5, 7, 11              AuditEvent, Admin y panel                                                                PENDIENTE
              AUD-002                                                                                  only                         los logs no contienen
                                                                                                                                    secretos.
```

```text
                                                                                                                                    Dos ejecuciones mantienen
              LOT-GOV-003; practica de                                                                 permisos, motivo y append-
MVP-ADM-004                                   Fases 5, 7, 11              AuditEvent, Admin y panel                                 los mismos registros           PENDIENTE
              despliegue                                                                               only
                                                                                                                                    esperados.
```

```text
                                                                                                                                    Revision de paginas
                                                                          Terms, templates y           allowlist y aceptacion       publicas confirma ausencia
MVP-PRV-001   Politica de privacidad v1.1.0   Fases 2, 6, 11                                                                                                       PENDIENTE
                                                                          privacidad                   versionada                   de documento, telefono y
                                                                                                                                    correo.
```

```text
                                                                                                                                    Actualizar la version no
              LOT-IAM-007; Terms                                          Terms, templates y           allowlist y aceptacion       altera aceptaciones
MVP-PRV-002                                   Fases 2, 6, 11                                                                                                       PENDIENTE
              v1.1.0; Privacy v1.1.0                                      privacidad                   versionada                   anteriores y puede exigir
                                                                                                                                    nueva aceptacion.
```

```text
              Politica de privacidad;                                                                  env, CSRF, HTTPS y check     Busqueda en Git no
MVP-SEC-001                                   Fases 1, 11, 12             settings local/production                                                                PENDIENTE
              buenas practicas Django                                                                  --deploy                     encuentra claves reales.
```

```text
                                                                                                                                    django check --deploy sin
              LOT-GOV-001; practica de                                                                 env, CSRF, HTTPS y check
MVP-SEC-002                                   Fases 1, 11, 12             settings local/production                                 hallazgos criticos y sitio     PENDIENTE
              despliegue                                                                               --deploy
                                                                                                                                    accesible por HTTPS.
```

```text
                                                                                                                                     Prueba o evidencia
Regla MVP          Fuente canonica           Fase                        Modelo / servicio           Control servidor / BD                                         Estado
                                                                                                                                     minima
```

```text
                                                                                                                                     Instalacion en base vacia
                   LOT-AUD-007; practica                                                             migrate/collectstatic/health
MVP-DEP-001                                  Fase 12                     runbook y hosting                                           produce una aplicacion        PENDIENTE
                   operativa                                                                         check
                                                                                                                                     funcional.
```

```text
                                                                                                                                     Instalacion en Android abre
                                                                                                     manifest/service worker sin     la URL publica y las
MVP-MOB-001        Decision de alcance MVP   Fase 13                     PWA y frontend responsive                                                                 PENDIENTE
                                                                                                     writes offline                  operaciones siempre
                                                                                                                                     consultan el servidor.
```

```text
                                                                                                                                     Una operacion realizada en
                                                                                                     manifest/service worker sin
MVP-MOB-002        LOT-GOV-002               Fase 13                     PWA y frontend responsive                                   web aparece al iniciar        PENDIENTE
                                                                                                     writes offline
                                                                                                                                     sesion desde movil.
```

```text
                                                                                                                                     Administrador con boleto no
                                                                                                                                     puede
                                                                         DrawEvent, Ticket,          policy
MVP-IAM-011        DEC-MVP-001               Fases 7, 10, 11                                                                         publicar/cancelar/fijar       PENDIENTE
                                                                         AuditEvent                  can_administer_event
                                                                                                                                     resultado del mismo
                                                                                                                                     evento; otro admin sí.
```

```text
                                                                                                                                     No hay acciones muertas,
                                                                         templates, static,          tests de plantilla y            textos contradictorios ni
MVP-UI-001         DI-MVP-DJANGO v1.0.0      Fases 6, 7, 11                                                                                                        PENDIENTE
                                                                         navegación                  responsive                      navegación a módulos no
                                                                                                                                     autorizados.
```

## 3. Pruebas de aceptacion por flujo
```text
Flujo                                                  Escenario                                                            Resultado esperado
```

```text
                                                       Crear cliente adulto con terminos; intentar                          Solo el primero valido se crea; se generan wallets y
```
Registro
```text
                                                       usuario/correo/documento duplicado y menor de edad.                  aceptaciones.
```

```text
                                                                                                                            Solo se muestran roles asignados; modo CLIENTE tiene
                                                       Entrar como Cliente puro, Vendedor+Cliente y
Login/modo                                                                                                                  funciones completas; otros modos aíslan acciones y no
                                                       Administrador+Cliente; cambiar modos y manipular URL.
                                                                                                                            escalan privilegios.
```

```text
Recarga                                                Acreditar 100,00 REAL y repetir el POST.                             Incremento 100,00 una sola vez; sin comision.
```

```text
                                                                                                                            Debito 500,00, credito 450,00 REAL y fee 50,00;
Conversion                                             Convertir 500,00 VIRTUAL.
                                                                                                                            movimientos correlacionados.
```

```text
                                                       Enviar VIRTUAL a otro cliente; probar autoenvio, inactivo y
Transferencia                                                                                                               Solo la transferencia valida confirma.
                                                       saldo insuficiente.
```

```text
                                                       Vendedor compra 100,00 VIRTUAL; probar 0,50 VIRTUAL y
Compra mayorista                                                                                                            90,00 REAL->100,00 VIRTUAL; orden invalida rechazada.
                                                       saldo insuficiente.
```

```text
Flujo                                           Escenario                                                         Resultado esperado
```

```text
                                                                                                                  La valida reserva 100,00 y crea PENDIENTE; la otra no
Crear solicitud                                 Cliente solicita 100,00 REAL con y sin saldo.
                                                                                                                  altera nada.
```

```text
Asignar solicitud                               Dos vendedores intentan tomar la misma.                           Solo uno queda ACTIVA/EN_PROCESO.
```

```text
                                                                                                                  Rollback completo; en exito, intercambio REAL/VIRTUAL y
Confirmar solicitud                             Forzar error entre movimientos.
                                                                                                                  estado terminal.
```

```text
                                                Ejecutar command dos veces con wallet general suficiente e
Vencimiento                                                                                                       Finalizacion unica; fallback o liberacion sin reserva colgada.
                                                insuficiente.
```

```text
Validar boleto                                  Probar Octal/Decimal/Hex valido e invalido; permutaciones.        Longitud/universo/unicidad correctos y clave canonica.
```

```text
                                                Dos cuentas compran la misma combinación; probar multirrol        Solo una combinación se vende; multirrol en CLIENTE
Comprar boleto                                  en CLIENTE, los mismos usuarios en                                puede comprar; modos incompatibles, cierre y saldo
                                                VENDEDOR/ADMINISTRADOR y cierre.                                  insuficiente se rechazan.
```

```text
Cancelar evento                                 Cancelar antes del resultado y repetir.                           Reembolso total una vez; evento CANCELADO.
```

```text
Publicar resultado                              Publicar resultado, repetir y reprocesar premios.                 Un resultado, evaluacion correcta y premios no duplicados.
```

```text
Privacidad publica                              Abrir landing/evento/resultado sin sesion.                        No aparecen documento, correo, telefono ni wallet.
```

```text
                                                Instalar desde cero, migrate, collectstatic, seed, check --
Despliegue                                                                                                        URL HTTPS operativa con DEBUG=False.
                                                deploy.
```

```text
                                                                                                                  Shell abre; operaciones offline no se confirman; datos se
PWA                                             Instalar en Android, usar online/offline y volver a conectar.
                                                                                                                  sincronizan desde servidor.
```

```text
                                                Administrador compra en modo CLIENTE y luego intenta              La administración del evento se rechaza y queda auditada;
```
Conflicto administrador-evento
```text
                                                publicar/cancelar/registrar resultado del mismo evento.           otro administrador sin boleto puede continuar.
```

## 4. Puertas de fase
```text
Fase                             Nombre                                           Puerta de salida verificable                    Estado
```

```text
                                                                                  Tres PDFs, copia intacta del frontend y
Fase 0                           Baseline y respaldo                                                                              PENDIENTE
                                                                                  alcance aprobado.
```

```text
                                                                                  manage.py check correcto; no se ejecuta
Fase 1                           Entorno y esqueleto                                                                              PENDIENTE
                                                                                  migrate todavia.
```

```text
                                                                                  Primera migracion de accounts lista antes de
Fase 2                           Usuario personalizado                                                                            PENDIENTE
                                                                                  la migracion general.
```

```text
 Fase                                          Nombre                                             Puerta de salida verificable                     Estado
```

```text
 Fase 3                                        PostgreSQL y migracion inicial                     /admin/ accesible y tablas en PostgreSQL.        PENDIENTE
```

```text
 Fase 4                                        Modelos y restricciones                            Migrations reproducibles y modelo validado.      PENDIENTE
```

```text
                                                                                                  seed_demo idempotente y panel maestro
 Fase 5                                        Seeds y administracion                                                                              PENDIENTE
                                                                                                  usable.
```

```text
                                                                                                  Landing y dashboards renderizan con
 Fase 6                                        Importacion de interfaz                                                                             PENDIENTE
                                                                                                  Django sin JSON/localStorage autoritativo.
```

```text
                                                                                                  Roles asignados, selector coherente,
 Fase 7                                        Autenticacion y permisos                           permisos completos por modo y aislamiento        PENDIENTE
                                                                                                  verificados.
```

```text
                                                                                                  Operaciones atomicas y movimientos
 Fase 8                                        Wallets y finanzas                                                                                  PENDIENTE
                                                                                                  persistidos.
```

```text
 Fase 9                                        Solicitudes                                        Flujo Cliente-Vendedor completo.                 PENDIENTE
```

```text
                                                                                                  Compra válida para modo CLIENTE,
 Fase 10                                       Loteria y resultados                               unicidad, resultado y conflicto administrativo   PENDIENTE
                                                                                                  verificados.
```

```text
                                                                                                  Suite minima verde y django check --deploy
 Fase 11                                       Pruebas y seguridad                                                                                 PENDIENTE
                                                                                                  revisado.
```

```text
 Fase 12                                       Despliegue                                         URL publica funcional y reproducible.            PENDIENTE
```

```text
                                                                                                  Aplicacion instalable conectada al mismo
 Fase 13                                       PWA / Android                                                                                       PENDIENTE
                                                                                                  backend.
```

## 5. Registro de decisiones
Esta tabla se completa cuando una necesidad no pueda resolverse usando los tres documentos. No se modifica codigo primero y se documenta despues.

```text
 ID                          Fecha                             Pregunta / conflicto               Decision                         Documentos afectados           Estado
```

```text
                                                                                                  Adoptar los tres documentos
 DEC-MVP-001                 29 de julio de 2026               Baseline inicial del MVP Django.   generados y mantener separado    Los tres PDFs                  REGISTRADA
                                                                                                  el proyecto empresarial.
```

## 6. Checklist de revision antes de cada entrega
- Las migraciones nuevas estan versionadas y una base vacia migra correctamente.
- No hay saldos, roles, estados o precios decididos por JavaScript/localStorage.
- Las formulas usan minor units y las tarifas coinciden con Reglas Maestras.
- Cada POST sensible usa CSRF, autenticacion y politica de autorizacion.
- Los servicios criticos usan transaccion y bloqueo cuando corresponde.
- No se exponen datos personales en paginas publicas.
- Las pantallas no prometen funciones declaradas fuera de alcance.
- Los tests de las filas modificadas se ejecutaron y su estado fue actualizado.
- README, .env.example y runbook siguen siendo reproducibles.
- El despliegue mantiene ACADEMIC_SIMULATION visible y no contiene datos de pago reales.

## 6. Casos de regresión obligatorios por la corrección v1.1.0
Los siguientes casos impiden que la contradicción vuelva a aparecer durante la migración del frontend a Django.
- Cuenta solo CLIENTE: no ve selector y entra directamente al panel Cliente.
- Cuenta CLIENTE+VENDEDOR: ve Cliente y Vendedor; compra en CLIENTE y recibe 403 en VENDEDOR.
- Cuenta CLIENTE+ADMINISTRADOR: ve Cliente y Administrador; compra en CLIENTE y administra únicamente en ADMINISTRADOR.
- Cuenta con los tres roles: cada modo presenta navegación y endpoints diferentes; no mezcla permisos.
- Modificar active_mode desde el navegador a un rol no asignado no concede acceso.
- Administrador participante no administra el mismo evento.
- Vendedor no atiende una solicitud propia aunque cambie de modo entre la creación y la asignación.
