---
title: "Diseño Integral de Interfaz del MVP Django"
version: "1.0.0"
project: "Lotería Binaria - MVP Django"
source_pdf: "04_Diseno_Interfaz_MVP_Django_v1.0.0.pdf"
date: "2026-07-29"
---

> **Documento canónico del MVP Django.** Conversión estructural desde el PDF oficial; conserva el contenido, la numeración y las tablas en bloques de texto cuando la maquetación no permite una tabla Markdown segura.

```text
                                       LOTERÍA BINARIA
```

Diseño integral de interfaz y experiencia
Arquitectura de información, páginas, navegación, componentes y responsive
```text
                      para la implementación Django
Proyecto                                                  Lotería Binaria - MVP Django
```

```text
Documento                                                 DI-MVP-DJANGO
```

```text
Versión                                                   1.0.0
```

```text
Estado                                                    BASELINE VISUAL Y FUNCIONAL
```

```text
Fecha / autor                                             29 de julio de 2026 - Cristhian Herrera Nieto
```

```text
    Documento académico: saldos, recargas, retiros y premios simulados. No autoriza operación comercial o
                                                  regulada.
```

## Contenido
## 1. Objetivo y relación con el frontend heredado
## 2. Decisión de roles y modos
## 3. Arquitectura de información
## 4. Sistema visual
## 5. Páginas públicas
## 6. Interfaz Cliente
## 7. Interfaz Vendedor
## 8. Interfaz Administrador
## 9. Páginas de detalle y flujos
## 10. Responsive y aplicación móvil
## 11. Accesibilidad y mensajes
## 12. Integración con templates Django
## 13. Criterios de aceptación

## 1. Objetivo y relación con el frontend heredado
El ZIP contiene una base visual valiosa: landing, autenticación, selector de modo, dashboards, páginas de detalle,
paleta azul/dorada, componentes y responsive. La implementación Django debe conservar esa identidad, pero
reemplazar JSON/localStorage por datos autoritativos, corregir contradicciones y simplificar la navegación.

```text
    Método de revisión
    La URL pública proporcionada respondió 403 al acceso automatizado. La auditoría visual y estructural se realizó sobre el ZIP que
    el usuario confirmó como equivalente, revisando HTML, CSS, JavaScript, JSON, rutas y textos. Los mockups de este documento
    son propuestas conceptuales, no capturas del sitio publicado.
```

Principios de diseño
- Mostrar primero la tarea principal del modo activo y dejar funciones secundarias en navegación.
- No mostrar botones que el backend rechazará por regla permanente; sí mostrar estados y explicaciones cuando la
```text
       acción depende de saldo, tiempo o estado.
```
- Un mismo concepto utiliza el mismo nombre en todo el sistema: CLIENTE, VENDEDOR, ADMINISTRADOR; REAL,
```text
       VIRTUAL; boleto, evento y solicitud.
```
- Toda acción sensible muestra resumen, confirmación, resultado y comprobante o identificador.
- El sistema siempre señala que los saldos y operaciones son simulados.
- Diseño mobile-first, sin desbordamiento horizontal y con objetivos táctiles de al menos 44 px.

```text
       Propuesta conceptual de landing: conserva la identidad azul y dorada, prioriza sorteos visibles y etiqueta el alcance académico.
```

## 2. Decisión de roles y modos
La interfaz debe reflejar DEC-MVP-001 sin ambigüedad. El Administrador asigna roles. El usuario elige un modo
entre los roles asignados. El modo CLIENTE concede todas las funciones de Cliente, aunque la cuenta también
tenga roles adicionales.

```text
 Cuenta                             Opciones visibles                   Compra boletos                      Regla
```

```text
 Solo CLIENTE                       Entrada directa a CLIENTE           Sí                                  No se muestra selector.
```

```text
                                                                                                            En VENDEDOR atiende
 CLIENTE + VENDEDOR                 CLIENTE / VENDEDOR                  Sí, solo en CLIENTE
                                                                                                            solicitudes e inventario.
```

```text
                                                                                                            No administra un evento en el
 CLIENTE + ADMINISTRADOR            CLIENTE / ADMINISTRADOR             Sí, solo en CLIENTE
                                                                                                            que participa.
```

```text
                                    CLIENTE / VENDEDOR /                                                    Cada modo tiene navegación y
 Tres roles                                                             Sí, solo en CLIENTE
                                    ADMINISTRADOR                                                           endpoints aislados.
```

```text
                                                                                                            No aparece CLIENTE si no fue
 Solo VENDEDOR                      VENDEDOR                            No
                                                                                                            asignado.
```

```text
               Selector propuesto: cada tarjeta describe capacidades reales; no existe un “Cliente financiero” limitado y engañoso.
```

Comportamiento del selector
- Se presenta después del login solo cuando existen dos o más modos disponibles.
- Cada opción incluye nombre, funciones principales y una acción única “Entrar como…”.
- Cambiar modo se ejecuta con POST y CSRF; no se acepta un parámetro GET como autoridad.
- La barra superior muestra siempre el modo activo y permite cambiarlo desde un menú controlado.
- Al cambiar de modo se redirige al dashboard correspondiente y se registra AuditEvent.

## 3. Arquitectura de información
Mapa general
```text
    Área                                          Ruta Django sugerida                            Páginas
```

```text
                                                                                                  Landing, sorteos públicos, resultados, cómo
    Público                                       /
                                                                                                  funciona, seguridad.
```

```text
                                                                                                  Login, registro, selector de modo, perfil,
    Cuentas                                       /cuentas/
                                                                                                  términos y privacidad.
```

```text
                                                                                                  Resumen, sorteos, boleto, wallet,
    Cliente                                       /cliente/                                       conversiones, solicitudes, transferencias,
                                                                                                  historial.
```

```text
                                                                                                  Resumen, solicitudes, inventario, ventas,
    Vendedor                                      /vendedor/
                                                                                                  wallet, movimientos y perfil.
```

```text
                                                                                                  Resumen, usuarios, roles, sorteos, eventos,
    Administrador                                 /panel/                                         resultados, solicitudes, movimientos y
                                                                                                  auditoría.
```

```text
                                                                                                  Administración técnica y datos maestros;
    Django Admin                                  /admin/
                                                                                                  separada del panel visual.
```

Rutas y templates
```text
    Nombre URL                   Ruta                               Template                               Acceso
```

```text
    core:home                    /                                  core/home.html                         Público
```

```text
    accounts:login               /cuentas/ingresar/                 accounts/login.html                    Público
```

```text
    accounts:register            /cuentas/registro/                 accounts/register.html                 Público
```

```text
    accounts:choose_mode         /cuentas/modo/                     accounts/choose_mode.html              Multirrol
```

```text
    client:dashboard             /cliente/                          client/dashboard.html                  CLIENTE
```

```text
    client:draws                 /cliente/sorteos/                  client/draw_list.html                  CLIENTE
```

```text
    client:draw_detail           /cliente/sorteos/<uuid>/           client/draw_detail.html                CLIENTE
```

```text
    client:tickets               /cliente/boletos/                  client/ticket_list.html                CLIENTE
```

```text
    client:wallet                /cliente/wallet/                   client/wallet.html                     CLIENTE
```

```text
    vendor:dashboard             /vendedor/                         vendor/dashboard.html                  VENDEDOR
```

```text
    vendor:requests              /vendedor/solicitudes/             vendor/request_list.html               VENDEDOR
```

```text
    vendor:request_detail        /vendedor/solicitudes/<uuid>/      vendor/request_detail.html             VENDEDOR
```

```text
    business_admin:dashboard     /panel/                            business_admin/dashboard.html          ADMINISTRADOR
```

```text
    business_admin:events        /panel/eventos/                    business_admin/event_list.html         ADMINISTRADOR
```

```text
    business_admin:results       /panel/resultados/                 business_admin/result_list.html        ADMINISTRADOR
```

## 4. Sistema visual
```text
    Token                                     Valor de referencia                              Uso
```

```text
    Azul 950                                  #07111F                                          Fondo principal y navegación.
```

```text
    Azul 900                                  #0B1628                                          Barra superior y paneles.
```

```text
    Azul 800                                  #10233F                                          Tarjetas y superficies.
```

```text
    Dorado                                    #F5C542                                          Acción primaria, premios y foco de marca.
```

```text
    Celeste                                   #38BDF8                                          Información y módulo Vendedor.
```

```text
    Verde                                     #22C55E                                          Éxito y estados completados.
```

```text
    Rojo                                      #EF4444                                          Errores y acciones destructivas.
```

```text
    Gris claro                                #F1F5F9                                          Texto y fondos de formularios claros.
```

Tipografía y jerarquía
- Fuente del sistema o Inter/Noto Sans; no depender de una fuente remota para funcionar.
- H1 de página: 32-40 px escritorio, 28-32 px móvil.
- H2 de sección: 22-28 px; texto base: 16 px; ayuda: mínimo 14 px.
- Importes usan cifras tabulares y siempre incluyen unidad REAL o VIRTUAL cuando pueda existir ambigüedad.

Componentes comunes
```text
    Componente                                                      Reglas de uso
```

```text
    Barra superior                                                  Logo, modo activo, notificaciones opcionales, perfil y cierre de
```

```text
Componente                                                    Reglas de uso
```

```text
                                                              sesión.
```

```text
Sidebar / navegación inferior                                 Solo acciones del modo; estado activo visible; no enlaces muertos.
```

```text
                                                              Etiqueta, valor, unidad, explicación breve y enlace cuando
```
Tarjeta resumen
```text
                                                              corresponde.
```

```text
Badge                                                         Estados normalizados; no depender solo del color.
```

```text
                                                              Cabecera persistente, paginación, filtros, estado vacío y scroll local
```
Tabla
```text
                                                              en móvil.
```

```text
                                                              Etiqueta visible, ayuda, error junto al campo, resumen antes de
```
Formulario
```text
                                                              confirmar y CSRF.
```

```text
                                                              Éxito, advertencia, error o información; aria-live y acción de
```
Alerta
```text
                                                              recuperación.
```

```text
                                                              Describe monto, comisión, origen/destino y efecto irreversible antes
```
Confirmación
```text
                                                              del POST.
```

## 5. Páginas públicas
```text
Página                                Contenido                                        Acción primaria
```

```text
                                      Propuesta, productos, sorteos visibles,
Landing                               pasos, roles, seguridad y naturaleza             Explorar sorteos / Crear cuenta
                                      académica.
```

```text
                                      Usuario o correo, contraseña, recuperación
Login                                 futura y acceso demo solo en entorno             Iniciar sesión
                                      académico.
```

```text
                                      Datos personales, mayoría de edad,
Registro                                                                               Crear cuenta
                                      credenciales y aceptación versionada.
```

```text
                                      Eventos publicados con filtros por producto y
Sorteos públicos                                                                       Ver detalle
                                      estado.
```

```text
                                      Resultado, premio y cifras agregadas sin
Resultados públicos                                                                    Consultar resultado
                                      datos personales.
```

```text
Términos / Privacidad                 Versión, fecha efectiva y contenido.             Volver / Aceptar durante registro
```

## 6. Interfaz Cliente

```text
                     Dashboard Cliente propuesto: prioriza saldos, sorteos disponibles, boletos activos y solicitudes.
```

```text
 Página / sección                             Qué ve                                           Qué puede hacer
```

```text
                                              Saldos, boletos activos, solicitudes,
 Resumen                                                                                       Ir a sorteos, wallet, solicitud o detalle.
                                              próximos sorteos y actividad.
```

```text
                                              Todos los eventos comprables, filtros,
 Sorteos                                                                                       Abrir detalle y comprar.
                                              precio, cierre y premio.
```

```text
                                              Producto, reglas, tiempo, precio, premio y       Ingresar selección válida y confirmar
```
Detalle de sorteo
```text
                                              disponibilidad.                                  compra.
```

```text
                                              Filtros por producto, fecha y estado;            Abrir detalle; no borrar ni devolver
```
Mis boletos
```text
                                              comprobante.                                     voluntariamente.
```

```text
                                              REAL/VIRTUAL disponible y reservado,             Recarga 1:1, conversión 10 %, retiro
```
Wallet
```text
                                              movimientos y filtros.                           simulado.
```

```text
 Solicitudes                                  Monto disponible, reserva y estados.             Crear solicitud y consultar su progreso.
```

```text
 Transferir                                   Destinatario Cliente y monto VIRTUAL.            Confirmar transferencia; nunca autoenvío.
```

```text
                                              Datos, roles asignados, modo activo y            Editar campos permitidos y cambiar
```
Perfil
```text
                                              aceptaciones.                                    contraseña.
```

Compra de boleto: flujo visual
## 14. Seleccionar evento desde el listado.
## 15. Ingresar o generar una combinación que cumpla cardinalidad y símbolos únicos.
## 16. Normalizar y verificar disponibilidad en el servidor.
## 17. Mostrar resumen: evento, combinación canónica, precio VIRTUAL y saldo posterior.
## 18. Confirmar mediante POST con CSRF.
## 19. Mostrar comprobante y enlace a “Mis boletos”.

## 7. Interfaz Vendedor

```text
                       Dashboard Vendedor propuesto: inventario y solicitudes elegibles son la tarea central.
```

```text
Página / sección                           Qué ve                                          Qué puede hacer
```

```text
                                           Inventario VIRTUAL, capital REAL, ganancia
Resumen                                                                                    Ir a solicitud o compra mayorista.
                                           realizada y cola.
```

```text
                                           Solo pendientes elegibles, monto y
Solicitudes                                                                                Tomar solicitud mediante confirmación.
                                           vencimiento.
```

```text
                                           Cliente minimizado, monto, saldo,
Detalle de solicitud                                                                       Confirmar o liberar asignación.
                                           temporizador y efecto.
```

```text
Inventario                                 Lotes y costo 0,90 REAL por 1,00 VIRTUAL.       Comprar múltiplos de 1,00 VIRTUAL.
```

```text
Ventas                                     Solicitudes completadas y margen realizado.     Consultar detalle y comprobante.
```

```text
Wallet                                     Saldos y movimientos propios.                   Recarga, conversión 10 % y retiro simulado.
```

```text
                                                                                           Consultar; cambios sensibles por
Perfil                                     Datos y estado de VendorProfile.
                                                                                           administrador.
```

## 8. Interfaz Administrador

```text
                      Panel Administrador propuesto: separa operaciones rápidas, métricas y alertas de seguridad.
```

```text
Módulo                                                              Funciones
```

```text
                                                                    Métricas, alertas, eventos próximos, actividad reciente y accesos
```
Resumen
```text
                                                                    rápidos.
```

```text
                                                                    Buscar, ver perfil, activar/suspender/desactivar y asignar roles; no
```
Usuarios
```text
                                                                    borrar historia.
```

```text
Roles                                                               Asignaciones y perfiles; un cambio exige motivo y auditoría.
```

```text
                                                                    Catálogo Octal/Decimal/Hexadecimal de solo lectura salvo
```
Sorteos
```text
                                                                    activación controlada.
```

```text
                                                                    Crear borrador, programar, publicar, cerrar y cancelar antes del
```
Eventos
```text
                                                                    resultado.
```

```text
                                                                    Seleccionar evento cerrado, registrar resultado, evaluar y acreditar
```
Resultados
```text
                                                                    una vez.
```

```text
Solicitudes                                                         Consulta global e intervención limitada y auditada.
```

```text
Movimientos                                                         Consulta paginada; no editar saldos directamente.
```

```text
Auditoría                                                           Actor, modo, acción, recurso, motivo, fecha y metadata no sensible.
```

Conflicto de interés
Si un administrador posee un boleto de un evento, el sistema deshabilita y rechaza las acciones de publicar, cancelar o fijar
resultado para ese evento. Debe actuar otro administrador.

## 9. Páginas de detalle y estados
```text
Detalle                                                             Estados y acciones
```

```text
Boleto                                                              PENDIENTE_RESULTADO, NO_PREMIADO, DEVOLUCIÓN,
```

```text
    Detalle                                                      Estados y acciones
```

```text
                                                                 GANADOR; ver comprobante y premio.
```

```text
                                                                 PENDIENTE, EN_PROCESO, COMPLETADA_POR_VENDEDOR,
    Solicitud
                                                                 COMPLETADA_POR_PLATAFORMA, FALLIDA_POR_LIQUIDEZ.
```

```text
                                                                 BORRADOR, PROGRAMADO, PUBLICADO, VENTAS_ABIERTAS,
    Evento                                                       VENTAS_CERRADAS, RESULTADO_FIJADO, FINALIZADO,
                                                                 CANCELADO.
```

```text
    Movimiento                                                   Tipo, dirección, unidad, monto, estado, referencia y fecha.
```

Estados vacíos y errores
- Sin sorteos: explicar que no existen eventos comprables y ofrecer volver al resumen.
- Sin boletos: invitar a explorar sorteos sin fingir historial.
- Saldo insuficiente: indicar saldo, monto faltante y acceso a wallet.
- Conflicto de combinación: mantener la selección y pedir elegir otra.
- Solicitud tomada: informar que otro vendedor la obtuvo y volver al listado.
- Error inesperado: mostrar correlation_id o identificador de operación sin exponer trazas.

## 10. Responsive y aplicación móvil

```text
                            Propuesta móvil Cliente: navegación inferior para tareas frecuentes y tarjetas en una columna.
```

```text
    Ancho                                                                   Comportamiento
```

```text
    ≥ 1200 px                                                               Sidebar fijo, cuatro métricas por fila y tablas completas.
```

```text
    769-1199 px                                                             Sidebar compacto o desplegable; métricas en dos columnas.
```

```text
                                                                            Una columna, topbar compacta, navegación inferior Cliente y off-
    ≤ 768 px
                                                                            canvas para módulos extensos.
```

```text
                                                                            Botones de ancho completo, tipografía reducida moderadamente y
    ≤ 420 px
                                                                            tablas en tarjetas/scroll local.
```

- No bloquear zoom ni usar tamaños fijos que provoquen overflow.
- El menú móvil debe cerrar con botón, Escape, enlace seleccionado y clic fuera.
- La barra inferior no tapa formularios; añadir padding-bottom equivalente.
- PWA: manifest, iconos, HTTPS y service worker solo para recursos estáticos. No cachear POST ni operaciones de
```text
        saldo.
```

## 11. Accesibilidad y mensajes
- HTML semántico, un H1 por página, labels explícitos y orden de tabulación natural.
- Contraste WCAG AA; el dorado sobre fondo oscuro se reserva a textos grandes o botones con contraste
```text
        comprobado.
```
- Indicadores de foco visibles y no depender del color para estados.
- aria-live para resultados de formularios; diálogos con foco atrapado y retorno al activador.
- Errores específicos: qué ocurrió, por qué y cómo recuperarse.
- Fechas presentadas en America/Guayaquil y almacenadas en UTC.

## 12. Integración con templates Django
```text
    Archivo                                                                 Responsabilidad
```

```text
    templates/base_public.html                                              Head, header público, mensajes, bloque content y footer.
```

```text
    templates/base_dashboard.html                                           Topbar, modo, sidebar/bottom-nav, mensajes y bloques por página.
```

```text
    templates/includes/_mode_switcher.html                                  Modos permitidos calculados por backend.
```

```text
    templates/includes/_messages.html                                       Mensajes Django accesibles.
```

```text
    templates/includes/_status_badge.html                                   Estados normalizados.
```

```text
    templates/includes/_pagination.html                                     Paginación común.
```

```text
    static/css/tokens.css                                                   Variables de color, espacio, tipografía y estados.
```

```text
    static/css/components.css                                               Botones, tarjetas, formularios, tablas, alertas y modal.
```

```text
    static/css/responsive.css                                               Breakpoints y navegación móvil.
```

```text
    static/js/ui.js                                                         Menú, modales, previews; nunca autoridad de negocio.
```

## 13. Criterios de aceptación
- No existen textos que digan que el modo CLIENTE está limitado cuando el backend lo trata como Cliente completo.
- No existen referencias activas a comisiones 5 %/15 % ni crecimiento 75 %.
- Cada enlace y botón lleva a una ruta real o se elimina.
- La navegación visible coincide con active_mode y el backend vuelve a validar.
- Todas las tablas tienen filtros, paginación o estado vacío según volumen.
- Las operaciones muestran unidad REAL/VIRTUAL y resultado posterior.

- No hay overflow horizontal de página en 360, 390, 768, 1024 y 1440 px; las tablas pueden desplazarse dentro de su
```text
    contenedor.
```
- El flujo se puede completar con teclado y lector de pantalla básico.
- La interfaz indica siempre la naturaleza académica y simulada.
