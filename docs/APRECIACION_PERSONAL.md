# Plantilla de apreciación crítica — Taller #3 Lotería Binaria con Django

## Datos del estudiante

* **Nombre:** Cristhian Herrera Nieto
* **Fecha:** 30 de julio de 2026
* **Curso / paralelo:** _____________________________________
* **Documento analizado:** `docs/ALCANCE_PROPUESTO_IA.md`

---

## 1. Correcto o útil

Considero que la propuesta contiene varios elementos correctos porque organiza el Taller #3 como una aplicación Django dividida en módulos y con un alcance que puede demostrarse durante una evaluación. La decisión de utilizar cinco aplicaciones canónicas —`accounts`, `core`, `finance`, `vendors` y `lottery`— ayuda a separar las responsabilidades del sistema. De esta manera, los usuarios se administran en `accounts`, los vendedores en `vendors`, los sorteos y boletos en `lottery`, las funciones generales en `core` y las operaciones monetarias de apoyo en `finance`.

También considero adecuado comenzar con SQLite. Esta base de datos viene integrada con Django, no requiere instalar un servidor adicional y permite comprobar rápidamente que los modelos, migraciones, formularios, vistas y plantillas funcionan. Usarla durante la primera fase reduce los errores de configuración y permite concentrarse en el funcionamiento de los CRUD. Una vez que el sistema básico está estable, la migración a MySQL sirve para demostrar que el proyecto puede trabajar con una base de datos administrada externamente y que la estructura desarrollada en Django no depende exclusivamente de SQLite.

El uso real de Bootstrap 5.3 también es correcto. El taller no necesita una interfaz completamente diseñada desde cero mediante CSS propio. Bootstrap permite construir formularios, tablas, tarjetas, alertas, botones, barras de navegación y diseños adaptables a dispositivos móviles. El CSS adicional debería utilizarse únicamente para complementar la identidad visual azul oscuro y dorada de Lotería Binaria, sin reemplazar el framework principal.

Los CRUD de `accounts`, `vendors` y `lottery` son apropiados para cumplir la evaluación porque representan tres módulos distintos y fáciles de demostrar. En `accounts` se pueden crear, consultar, modificar y desactivar usuarios. En `vendors` se pueden administrar perfiles o registros de vendedores. En `lottery` se pueden gestionar sorteos, eventos o boletos, dependiendo del modelo establecido en el proyecto. Esta selección permite evidenciar el uso de modelos, formularios, vistas, rutas, plantillas y operaciones de base de datos.

El login y los roles CLIENTE, VENDEDOR y ADMINISTRADOR son una mejora útil, siempre que no impidan completar primero los tres CRUD. El inicio y cierre de sesión permiten identificar al usuario, mientras que los roles ayudan a limitar las operaciones disponibles. Por ejemplo, un administrador puede gestionar registros, un vendedor puede consultar o atender las funciones relacionadas con ventas y un cliente puede visualizar sorteos o boletos. Esta mejora hace que el proyecto parezca más completo y permite explicar conceptos de autenticación, autorización y protección de rutas.

También es correcta la protección de las operaciones sensibles. No cualquier usuario debería poder crear, modificar o desactivar vendedores, sorteos o cuentas. Las vistas sensibles deben requerir autenticación y, cuando corresponda, permisos administrativos. Además, considero útil utilizar desactivación lógica en lugar de eliminar información histórica. Un vendedor, usuario o sorteo que ya tiene relaciones con otros registros no debería desaparecer completamente, porque eso podría afectar la integridad de los datos y dificultar la explicación del historial del sistema.

Las evidencias por fase también son importantes. Se deberían guardar capturas del servidor funcionando, migraciones aplicadas, registros creados, formularios validados, tablas de la base de datos, pruebas de cada CRUD, cambio de SQLite a MySQL y funcionamiento del login. Estas evidencias ayudarían a demostrar que el proyecto fue desarrollado paso a paso y no únicamente presentado como un resultado final.

En general, las partes más útiles de la propuesta son las que permiten explicar claramente la arquitectura del proyecto, la separación por aplicaciones, la secuencia de desarrollo, los tres CRUD evaluables, el uso de Bootstrap, la persistencia en dos motores de base de datos y la protección de funciones según el usuario.

---

## 2. Exagerado o innecesario

Algunas partes de la propuesta podrían ser demasiado amplias para un taller académico. Lotería Binaria tiene reglas de negocio que pertenecen a un sistema empresarial más grande, pero no todas deben implementarse en esta entrega. El objetivo del Taller #3 debería ser demostrar el uso correcto de Django, modelos, base de datos, vistas, formularios, plantillas, Bootstrap y operaciones CRUD.

No considero necesario implementar completamente el sistema financiero del proyecto empresarial. Funciones como wallets reales y virtuales, comisiones, conversión de dinero, transferencias entre clientes, liquidaciones de vendedores, fondos de garantía, reparto de premios y movimientos contables aumentarían considerablemente la complejidad. En este taller, `finance` puede mantenerse como una aplicación de apoyo, con un modelo sencillo o incluso con funciones de consulta, sin desarrollar un libro contable completo.

Tampoco es obligatorio implementar todos los servicios de negocio del MVP. Las reglas de compra máxima del veinte por ciento, liberación del límite al ochenta por ciento del tiempo, generación de resultados mediante hash, revelación progresiva de números, acreditación automática de premios, reembolsos masivos y fondos de premios futuros corresponden a un producto más avanzado. Son reglas valiosas para el sistema completo, pero resultan excesivas para una entrega centrada en CRUD.

El selector de modo activo puede ser útil, pero no debería convertirse en una prioridad. En el sistema empresarial una cuenta podría entrar como cliente, vendedor o administrador según sus permisos. Para el taller bastaría con dirigir a cada usuario a un panel básico según su rol. Implementar cambios dinámicos entre modos, permisos combinados y excepciones complejas podría consumir tiempo sin aportar directamente a la rúbrica.

Las pruebas automatizadas también deben ajustarse al nivel del taller. Es conveniente tener pruebas básicas de modelos, acceso a vistas, validación de formularios y protección de rutas, pero no es necesario construir una infraestructura avanzada de integración, concurrencia, bases aisladas, pruebas de carga o escenarios financieros. Esas pruebas pertenecen más al proyecto empresarial o a una fase posterior.

El reporte CSV puede ser una ampliación útil, pero no debería ser obligatorio. Si el tiempo es limitado, primero deben terminarse y probarse los CRUD. El reporte podría agregarse únicamente si los módulos principales ya funcionan correctamente. Lo mismo ocurre con la compra completa de boletos y la publicación automática de resultados. Se puede demostrar una versión académica simplificada, pero no es necesario desarrollar todo el ciclo real de una lotería.

El ZIP antiguo tampoco debería copiarse directamente. Debe utilizarse únicamente como referencia visual para identificar pantallas, colores, tarjetas, navegación y distribución de contenido. No deberían trasladarse mecanismos basados en JSON, `localStorage`, datos simulados en el navegador ni reglas antiguas que no coincidan con el alcance actual. Django y la base de datos deben ser la fuente de verdad.

También considero innecesario implementar en esta entrega elementos como aplicación móvil, API REST completa, procesamiento en segundo plano, notificaciones, pagos reales, tarjetas, despliegue distribuido, generación criptográfica de ganadores, alta concurrencia, auditoría financiera avanzada o mecanismos empresariales contra fraude. Estas características deberían registrarse como trabajo futuro.

La principal exageración sería intentar convertir el Taller #3 en el sistema empresarial completo de Lotería Binaria. Esto aumentaría el riesgo de entregar muchas funciones incompletas. Es preferible presentar una aplicación pequeña, coherente, demostrable y correctamente probada.

---

## 3. Ajustes que realizaría

Como alcance mínimo obligatorio conservaría la estructura Django con las cinco aplicaciones canónicas, la configuración inicial con SQLite, la migración posterior a MySQL, la interfaz construida realmente con Bootstrap 5.3 y los tres CRUD evaluables en `accounts`, `vendors` y `lottery`.

Primero desarrollaría `accounts`, porque los usuarios sirven como base para relacionar vendedores, permisos y otras operaciones. Este CRUD debería permitir listar, crear, consultar, modificar y desactivar cuentas. La eliminación física debería evitarse cuando el usuario tenga relaciones históricas. También se deberían validar campos obligatorios y evitar registros duplicados, especialmente en correo, nombre de usuario o documento si esos campos existen en el modelo actual.

Después desarrollaría `vendors`, porque normalmente un vendedor estará relacionado con una cuenta. Este módulo debería incluir un CRUD claro y sencillo para registrar vendedores, consultar sus datos, modificar información permitida y cambiar su estado. No intentaría implementar todavía comisiones, compra de saldo virtual, atención de solicitudes o liquidaciones.

En tercer lugar desarrollaría `lottery`, porque es el módulo funcional que representa mejor la temática del proyecto. El CRUD podría centrarse en la administración de sorteos o eventos: crear, listar, visualizar detalles, modificar únicamente los datos permitidos y desactivar o cancelar. En caso de que el enunciado requiera boletos, estos podrían incluirse de forma simplificada, sin desarrollar todavía todos los límites, premios y operaciones financieras del sistema completo.

`core` debería contener elementos compartidos, como la página principal, utilidades, plantillas base, navegación, páginas de error y funciones generales. No lo convertiría en otro CRUD obligatorio. `finance` se mantendría como apoyo y podría contener un modelo sencillo de movimiento simulado o solamente una estructura preparada para una fase futura. No implementaría dinero real ni integración con servicios externos.

El login, logout, roles y protección de rutas se desarrollarían después de tener los CRUD básicos funcionando. Serían una mejora adicional importante, pero no deberían retrasar el cumplimiento mínimo. Se podría utilizar el sistema de autenticación de Django y grupos o campos de rol sencillos. Las rutas administrativas requerirían autenticación y comprobación del rol correspondiente.

En la interfaz conservaría del ZIP las ideas visuales útiles: página de inicio, formulario de inicio de sesión, paneles por rol, tarjetas de sorteos, tablas de administración, formularios y pantallas de detalle. Sin embargo, reemplazaría la lógica basada en el navegador por vistas, formularios y consultas reales de Django. La apariencia azul oscuro y dorada se conservaría mediante un archivo CSS complementario, mientras que la estructura principal se construiría con Bootstrap 5.3.

Eliminaría o corregiría reglas antiguas que no correspondan al taller. No utilizaría PostgreSQL, ya que la secuencia solicitada es SQLite en la primera fase y MySQL en la segunda. Tampoco utilizaría JSON ni `localStorage` como almacenamiento. Evitaría crear rutas o modelos que no hayan sido confirmados en los archivos actuales del proyecto.

Las evidencias indispensables serían las siguientes: estructura de las cinco apps, ejecución del servidor, migraciones en SQLite, funcionamiento de los tres CRUD, validaciones de formularios, interfaz Bootstrap, login y roles si se implementan, protección de rutas, configuración de MySQL, migraciones aplicadas en MySQL, registros visibles en la base de datos y pruebas finales de navegación.

Para terminar el proyecto a tiempo, trabajaría por fases pequeñas. No avanzaría al siguiente módulo hasta que el anterior pueda crearse, consultarse, editarse y desactivarse correctamente. También probaría cada ruta inmediatamente después de implementarla, mantendría un registro de errores y conservaría capturas del proceso. Las ampliaciones se realizarían únicamente después de cumplir completamente la rúbrica.

---

# Tabla de análisis crítico

| Elemento de la propuesta                    | Correcto o útil                                                             | Exagerado o innecesario                                        | Ajuste que realizaría                                                             | Justificación                                                             |
| ------------------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| SQLite en la primera fase                   | Sí. Permite comenzar rápidamente y comprobar modelos, formularios y vistas. | No resulta exagerado.                                          | Mantenerlo como base inicial del desarrollo.                                      | Reduce errores de configuración y permite concentrarse en Django.         |
| Migración posterior a MySQL                 | Sí. Demuestra el uso de un motor externo.                                   | Podría complicarse si se intenta demasiado pronto.             | Realizarla después de validar todos los CRUD en SQLite.                           | Evita confundir errores del código con errores de conexión.               |
| Uso de Bootstrap 5.3                        | Sí. Facilita una interfaz consistente y adaptable.                          | Sería innecesario reemplazarlo con demasiado CSS propio.       | Usar componentes reales de Bootstrap y CSS solo para colores y detalles.          | Cumple el requisito visual y reduce el tiempo de diseño.                  |
| Cinco apps canónicas                        | Sí. Organizan el proyecto por responsabilidades.                            | Podría ser excesivo desarrollar CRUD completos en las cinco.   | Mantener las cinco, pero priorizar solo tres CRUD.                                | Conserva una arquitectura ordenada sin ampliar demasiado el alcance.      |
| CRUD de `accounts`                          | Sí. Demuestra administración de usuarios.                                   | Un sistema de identidad empresarial sería excesivo.            | Crear, listar, consultar, editar y desactivar cuentas.                            | Es la base para roles, vendedores y autenticación.                        |
| CRUD de `vendors`                           | Sí. Representa un segundo módulo independiente.                             | Comisiones y liquidaciones no son necesarias.                  | Gestionar perfil, estado y relación con una cuenta.                               | Cumple la rúbrica sin implementar operaciones financieras complejas.      |
| CRUD de `lottery`                           | Sí. Es el módulo principal de la temática.                                  | Todo el motor real de sorteos sería excesivo.                  | Gestionar sorteos o eventos mediante un CRUD simplificado.                        | Permite demostrar la lógica principal del proyecto.                       |
| Login y logout reales                       | Sí. Mejoran la seguridad y la presentación.                                 | No deben impedir completar los CRUD.                           | Implementarlos después de los módulos obligatorios.                               | Son una mejora adicional claramente demostrable.                          |
| Roles CLIENTE, VENDEDOR y ADMINISTRADOR     | Sí. Permiten restringir acciones.                                           | Los permisos combinados muy complejos serían innecesarios.     | Utilizar roles simples o grupos de Django.                                        | Permite explicar autorización sin construir un sistema empresarial.       |
| Selector de modo activo                     | Puede ser útil para cuentas con varios permisos.                            | Es demasiado complejo para el alcance mínimo.                  | Sustituirlo por redirección a un panel según el rol o dejarlo como mejora futura. | Reduce lógica y posibles errores de permisos.                             |
| Protección de rutas                         | Sí. Es necesaria para operaciones sensibles.                                | No es exagerada.                                               | Aplicar autenticación y comprobación de rol en crear, editar y desactivar.        | Evita que usuarios no autorizados manipulen datos.                        |
| Desactivación en lugar de borrado histórico | Sí. Conserva relaciones y trazabilidad.                                     | No resulta exagerado si se aplica de forma sencilla.           | Añadir estados activos o inactivos donde sea necesario.                           | Evita pérdida de información relacionada.                                 |
| Uso del ZIP solo como referencia visual     | Sí. Ayuda a conservar la identidad del proyecto.                            | Copiar toda su lógica sería incorrecto.                        | Reutilizar ideas visuales, no JSON ni `localStorage`.                             | Django y la base de datos deben ser la fuente de verdad.                  |
| Evidencias y capturas por fase              | Sí. Demuestran el proceso de desarrollo.                                    | Demasiadas capturas repetidas podrían ser innecesarias.        | Guardar evidencias de cada hito importante.                                       | Facilitan la evaluación y defensa del proyecto.                           |
| Pruebas automatizadas                       | Son útiles para modelos, formularios y permisos.                            | Una infraestructura avanzada sería excesiva.                   | Crear pruebas básicas de los tres CRUD y rutas protegidas.                        | Aporta confiabilidad sin sobrecargar el taller.                           |
| Reporte CSV                                 | Es una mejora útil para demostrar exportación.                              | No es necesario para aprobar.                                  | Implementarlo solo si los CRUD ya están completos.                                | No aporta tanto como las funciones principales de la rúbrica.             |
| Operaciones financieras simuladas           | Pueden servir para mostrar la idea del sistema.                             | Un libro contable completo es excesivo.                        | Mantener `finance` como apoyo o demostración simple.                              | El objetivo del taller no es construir un sistema financiero real.        |
| Compra de boletos                           | Es coherente con la temática.                                               | Todo el proceso de saldo, límites y comisiones sería excesivo. | Implementar una versión básica o dejarla como consulta futura.                    | El CRUD de sorteos puede demostrar el módulo sin todo el flujo de compra. |
| Publicación de resultados                   | Puede complementar el módulo de lotería.                                    | Hash, revelación progresiva y pagos automáticos son excesivos. | Permitir registrar un resultado manual si existe tiempo.                          | Conserva una demostración sencilla de cierre del sorteo.                  |
| Funciones futuras o fuera de alcance        | Es útil documentarlas.                                                      | Implementarlas ahora ampliaría demasiado el taller.            | Registrarlas en una sección de trabajo futuro.                                    | Permite demostrar visión del sistema sin comprometer la entrega.          |

---

# Resumen personal

## Aspectos que conservaría

Conservaría la estructura de cinco aplicaciones porque separa adecuadamente las responsabilidades del sistema. También mantendría los tres CRUD de `accounts`, `vendors` y `lottery`, debido a que permiten demostrar claramente los conocimientos principales evaluados en Django.

Mantendría la secuencia SQLite y posteriormente MySQL. SQLite facilitaría la construcción inicial y MySQL permitiría comprobar que la aplicación funciona con una base de datos externa. También conservaría Bootstrap 5.3 como base principal de la interfaz, complementándolo con la identidad azul oscuro y dorada.

Además, conservaría el login, logout, los roles y la protección de rutas como mejoras adicionales. Estas funciones harían que el proyecto sea más coherente y permitirían demostrar que las operaciones sensibles no están disponibles para cualquier usuario.

## Aspectos que eliminaría o pospondría

Pospondría las operaciones financieras completas, las wallets, las conversiones de dinero, las comisiones, los fondos de garantía, las transferencias y las liquidaciones de vendedores. Estas funciones pertenecen a una aplicación más grande y no son necesarias para demostrar los objetivos principales del taller.

También dejaría para una fase futura el selector avanzado de modos, el motor automático de sorteos, la publicación criptográfica de resultados, las compras con límites complejos, los reembolsos automáticos, los reportes avanzados y las pruebas de concurrencia.

No trasladaría desde el ZIP ningún almacenamiento mediante JSON o `localStorage`. Tampoco copiaría funciones antiguas que no estén respaldadas por los requisitos actuales del Taller #3.

## Alcance final que propondría para el taller

El alcance final sería una aplicación Django organizada en las cinco apps canónicas: `accounts`, `core`, `finance`, `vendors` y `lottery`. Durante la primera fase funcionaría con SQLite y, después de validar los módulos principales, se configuraría MySQL y se repetirían las migraciones y pruebas.

La aplicación tendría tres CRUD completos y evaluables. `accounts` administraría usuarios; `vendors`, vendedores; y `lottery`, sorteos o eventos. Las eliminaciones sensibles se reemplazarían por desactivaciones o cambios de estado para conservar el historial.

La interfaz utilizaría Bootstrap 5.3 de manera real, con navegación adaptable, tablas, formularios, tarjetas, mensajes de validación y páginas de detalle. El CSS propio se limitaría a la identidad visual azul oscuro y dorada.

Como mejora adicional, incluiría login, logout, roles básicos y protección de rutas. `core` serviría para elementos compartidos y `finance` quedaría como módulo de apoyo, sin desarrollar todavía operaciones económicas complejas.

El proyecto se entregaría con evidencia del proceso: capturas de las fases, migraciones, pruebas de CRUD, validaciones, funcionamiento en SQLite, migración a MySQL, autenticación y protección de operaciones sensibles.

---

# Verificación antes de entregar

* [x] La apreciación está escrita con palabras propias.
* [x] Se identificaron aspectos correctos o útiles.
* [x] Se identificaron aspectos exagerados o innecesarios.
* [x] Se propusieron ajustes concretos.
* [x] Se explicó por qué se priorizan tres CRUD.
* [x] Se explicó por qué se usa Bootstrap 5.3.
* [x] Se explicó la secuencia SQLite → MySQL.
* [x] Se mencionó login y roles como mejora adicional.
* [x] Se diferenciaron funciones obligatorias y ampliaciones futuras.
* [x] Se agregó nombre y fecha.
