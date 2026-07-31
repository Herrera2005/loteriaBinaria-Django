---
title: "Auditoría de Coherencia e Interfaz del MVP Django"
version: "1.0.0"
project: "Lotería Binaria - MVP Django"
source_pdf: "05_Auditoria_Coherencia_Interfaz_MVP_Django_v1.0.0.pdf"
date: "2026-07-29"
---

> **Documento canónico del MVP Django.** Conversión estructural desde el PDF oficial; conserva el contenido, la numeración y las tablas en bloques de texto cuando la maquetación no permite una tabla Markdown segura.

```text
                                         LOTERÍA BINARIA
```

Auditoría de coherencia y correcciones
```text
          Revisión del ZIP, documentos y preparación para migración a Django
Proyecto                                                   Lotería Binaria - MVP Django
```

```text
Documento                                                  AC-MVP-DJANGO
```

```text
Versión                                                    1.0.0
```

```text
Estado                                                     REVISIÓN CERRADA - IMPLEMENTACIÓN PENDIENTE
```

```text
Fecha / autor                                              29 de julio de 2026 - Cristhian Herrera Nieto
```

```text
     Documento académico: saldos, recargas, retiros y premios simulados. No autoriza operación comercial o
                                                   regulada.
```

## 1. Fuentes y alcance de la auditoría
- Proyecto_HerreraNietoCristhian (6).zip: 10 HTML, 3 CSS, 9 JavaScript, 7 JSON, logo y README.
- Reglas Maestras, Plan Técnico y Matriz de Trazabilidad v1.0.0.
- Documentación normativa adjunta: reglas, estados, flujos, permisos, diccionario, términos y privacidad.
- URL pública proporcionada: el servidor devolvió 403 al acceso automatizado; no se afirma una prueba interactiva
```text
           remota. El usuario confirmó que corresponde al mismo ZIP.
```

## 2. Fortalezas del frontend actual
- Estructura clara con index en raíz y páginas en pages/.
- Separación de CSS, JavaScript y JSON; uso de DOM, fetch y localStorage adecuado para una demo académica.
- Landing y dashboards diferenciados para Cliente, Vendedor y Administrador.
- Paleta consistente azul/dorado, tarjetas, badges, formularios y tablas.
- responsive.css dedicado con control de overflow, tablas desplazables y sidebar móvil.
- Uso frecuente de HTML semántico, aria-label, aria-live y formularios con labels.
- El código auth.js ya modela una selección de modo completa y útil.

## 3. Hallazgos de coherencia
```text
    Severidad                        Área                           Hallazgo                                Resolución aprobada
```

```text
                                                                    Código permite comprar en
                                                                    CLIENTE; página y PDFs prohíben         Adoptar DEC-MVP-001: permisos
    Crítica                          Roles/modos
                                                                    a vendedor/admin aunque elijan          completos por modo, sin mezcla.
                                                                    CLIENTE.
```

```text
                                                                    Frontend descuenta 5 %; baseline
                                                                                                            Eliminar 5 % de textos, JS, datos
    Alta                             Recarga                        Django define recarga simulada
                                                                                                            demo y seeds.
                                                                    1:1.
```

```text
                                                                    Frontend aplica 15 %; baseline          Centralizar cálculo 90/10 en
    Alta                             Conversión
                                                                    define 10 %.                            servicio Django.
```

```text
                                                                    Frontend muestra crecimiento 75         Eliminar fórmula activa; mostrar
    Alta                             Premios
                                                                    %; MVP adopta premio fijo.              premio configurado por evento.
```

```text
                                                                    Generación rápida puede repetir
                                                                                                            Validador de producto,
                                                                    símbolos; detalle no exige
    Alta                             Combinaciones                                                          normalización y UniqueConstraint
                                                                    símbolos únicos ni normaliza
                                                                                                            por evento.
                                                                    orden.
```

```text
    Alta                             Datos monetarios               JSON/JS usa float.                      BigIntegerField en minor units.
```

```text
                                                                    Contraseñas en texto y                  Django auth, sesiones, CSRF y
    Alta                             Seguridad
                                                                    localStorage como autoridad.            PostgreSQL.
```

```text
                                                                    INACTIVO/ADMIN/PROXIMO
                                                                                                            Crear mapeo único y no importar
    Media                            Estados                        difieren de nombres seleccionados
                                                                                                            estados literales sin normalización.
                                                                    para Django.
```

```text
                                                                    “Eliminar visualmente” contradice       Desactivar/anonimizar; nunca
    Media                            Administración
                                                                    conservación histórica.                 borrar operaciones.
```

```text
                                                                                                            seed_demo calcula fechas
                                                                    Eventos con fechas fijas pueden
    Media                            Fechas demo                                                            relativas o comando
                                                                    quedar vencidos.
                                                                                                            refresh_demo_events.
```

```text
                                                                    Lógica financiera y de compra
                                                                                                            Mover reglas a servicios Django;
    Media                            JavaScript                     repetida entre cliente.js,
                                                                                                            JS solo UI.
                                                                    vendedor.js, wallets.js y sorteos.js.
```

```text
                                                                    Enlaces “detalle demo” y textos
                                                                                                            Rutas con IDs reales y eliminación
    Baja                             Navegación                     históricos pueden convertirse en
                                                                                                            de enlaces de demostración.
                                                                    funciones muertas.
```

## 4. Análisis específico de la regla de roles
La observación del usuario es correcta: ofrecer “Entrar como Cliente” y después impedir las acciones principales
de Cliente hace que el selector sea engañoso. Además, el ZIP ya contiene una implementación parcial que
autoriza la compra según modo CLIENTE, por lo que la primera versión de los PDFs se apartó de la interfaz real.
```text
    Resolución
    Los roles se asignan administrativamente. El usuario solo selecciona entre roles asignados. En modo CLIENTE obtiene funciones
    completas de Cliente; en VENDEDOR o ADMINISTRADOR no compra boletos. Las autorizaciones se aíslan por solicitud y se registran en
    auditoría.
```

```text
    Escenario                                                            Resultado corregido
```

```text
    Cliente puro                                                         Entra directamente a Cliente y compra.
```

```text
    Vendedor+Cliente en CLIENTE                                          Compra, gestiona wallet, crea solicitudes y ve boletos.
```

```text
    Vendedor+Cliente en VENDEDOR                                         Atiende solicitudes e inventario; comprar devuelve 403.
```

```text
    Administrador+Cliente en CLIENTE                                     Compra como Cliente.
```

```text
    Administrador+Cliente en ADMINISTRADOR                               Administra; comprar devuelve 403.
```

```text
    Administrador participante                                           No administra el mismo evento en el que posee boleto.
```

## 5. Calificación inicial
```text
    Dimensión                                     Nota /10                                        Motivo
```

```text
    Diseño visual                                 8,4                                             Identidad consistente y componentes amplios.
```

```text
                                                                                                  Cobertura completa, pero navegación y textos
    Arquitectura de información                   7,8
                                                                                                  mezclan demo y reglas.
```

```text
                                                                                                  CSS dedicado y controles de overflow; prueba
    Responsive estático                           8,2
                                                                                                  remota no disponible por 403.
```

```text
                                                                                                  Buena base semántica; faltan verificación de
    Accesibilidad                                 7,4
                                                                                                  contraste, foco y diálogos.
```

```text
                                                                                                  Contradicción directa entre selector, textos,
    Coherencia de roles                           4,0
                                                                                                  JSON y PDFs.
```

```text
    Coherencia financiera                         4,5                                             5 %, 15 %, 75 % y premio fijo coexistían.
```

```text
                                                                                                  Faltan unicidad de símbolos, normalización y
    Reglas de lotería                             5,5
                                                                                                  exclusión concurrente.
```

```text
                                                                                                  Buen frontend de referencia, aún no es una
    Preparación Django                            5,8
                                                                                                  baseline backend coherente.
```

```text
    Nota global inicial: 6,1/10
    La nota evalúa el conjunto como especificación para Django, no como entrega frontend del parcial. Como frontend académico visual, su
    valoración es mayor.
```

## 6. Correcciones documentales aplicadas
- Reglas Maestras actualizadas a v1.1.0 con DEC-MVP-001.
- Plan Técnico actualizado a v1.1.0 con fases y puertas de salida del diseño.
- Matriz actualizada a v1.1.0 con regresiones de cuentas multirrol y conflicto administrativo.
- Creado DI-MVP-DJANGO v1.0.0 con páginas, rutas, componentes y responsive.
- Eliminado CLIENTE_FINANCIERO como concepto del MVP.
- Conservadas recarga 1:1, conversión 10 %, compra mayorista 0,90/1,00 y premio fijo por evento.
- Definidas reglas de símbolos únicos, normalización y combinación única por evento.

## 7. Calificación posterior
```text
    Dimensión                                     Nota /10                                       Resultado
```

```text
                                                                                                 Mantiene marca y mejora jerarquía, navegación
    Diseño visual propuesto                       9,2
                                                                                                 y móvil.
```

```text
                                                                                                 Mapa de rutas y responsabilidades por página
    Arquitectura de información                   9,4
                                                                                                 definido.
```

```text
                                                                                                 Comportamientos por breakpoint y navegación
    Responsive especificado                       9,1
                                                                                                 móvil documentados.
```

```text
                                                                                                 Criterios AA, foco, mensajes y formularios
    Accesibilidad especificada                    9,0
                                                                                                 definidos.
```

```text
                                                                                                 Modo activo significativo, roles asignados y
    Coherencia de roles                           9,7
                                                                                                 conflictos explícitos.
```

```text
    Coherencia financiera                         9,6                                            Una tarifa por flujo y cálculo en minor units.
```

```text
                                                                                                 Validador, normalización, unicidad y
    Reglas de lotería                             9,3
                                                                                                 transacciones establecidos.
```

```text
                                                                                                 Modelos, servicios, templates, fases y pruebas
    Preparación Django                            9,5
                                                                                                 conectados.
```

```text
    Nota global posterior: 9,4/10
    No se asigna 10/10 porque todavía faltan implementación, migraciones, pruebas automatizadas y verificación responsive en la aplicación
    Django desplegada.
```

## 8. Riesgos que permanecen
- El hosting elegido puede limitar PostgreSQL, tareas programadas o tamaño de archivos estáticos; se verificará
```text
       antes del despliegue.
```
- La compra concurrente y la asignación de solicitudes necesitan pruebas PostgreSQL reales.
- La PWA no debe permitir operaciones offline ni cachear respuestas privadas.
- Los mockups son referencia; el resultado debe verificarse en 360, 390, 768, 1024 y 1440 px.
- Antes de operar públicamente con dinero o premios reales se requiere revisión legal y una arquitectura distinta.

## 9. Veredicto
El proyecto se puede migrar a Django sin convertirlo en el sistema empresarial completo. La base visual es
reutilizable y el alcance es razonable, siempre que las reglas corregidas se implementen en servicios Django y
PostgreSQL, no como condiciones dispersas en JavaScript. Los cinco documentos entregados forman la nueva
baseline de trabajo.
