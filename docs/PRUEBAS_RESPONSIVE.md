# Pruebas responsive, UX y accesibilidad — cierre visual

## 1. Alcance real

Se revisaron las pantallas de autenticación y selección de modo; dashboards Cliente, Vendedor y Administrador; cuentas; vendedores y solicitudes; finanzas; productos, eventos, compra de boletos, resultados y series; páginas 403/404; navegación base, offcanvas, mensajes y modal de confirmación.

No se modificaron modelos, servicios financieros, reglas, estados, permisos ni migraciones.

## 2. Evidencia utilizada

- Django 5.2.16 cargando las respuestas públicas y autenticadas.
- Compilación de templates mediante Django.
- Inspección de los 63 templates, `static/css/app.css` y `static/js/app.js`.
- Respuestas renderizadas para Home, Login, Registro, los tres dashboards, catálogo Cliente, listado de series, solicitudes Vendedor y error 403.
- Pruebas automatizadas de Bootstrap, skip link, offcanvas, mensajes, modal, filtros, tablas, estados textuales y páginas de error.
- Reglas CSS verificadas para 320, 375, 768, 1024 y 1440 px.

El Chromium headless del entorno no pudo acceder al servidor ni finalizar capturas desde `file://`; la evidencia visual automatizada se entrega como representación estructural basada en HTML real renderizado y reglas CSS. Las capturas manuales finales siguen siendo obligatorias antes de la entrega docente.

## 3. Diagnóstico previo confirmado

| ID | Hallazgo | Evidencia previa | Mejora aplicada |
|---|---|---|---|
| UX-01 | Foco desigual entre enlaces, botones y controles | Bootstrap cubría parte del foco, pero no existía una regla transversal de alto contraste | Foco `:focus-visible` dorado, con offset y halo oscuro |
| UX-02 | Objetivos táctiles pequeños en botones compactos y cierre | Algunos `.btn-sm`, `.btn-close` y paginadores quedaban por debajo de 44 px | Altura mínima de 40–44 px según control |
| UX-03 | Tablas desplazables sin nombre o ayuda estática | `.table-responsive` dependía del scroll visual; no todas tenían nombre | `data-table-label`, región enfocada, `aria-label`, instrucción e indicador de foco |
| UX-04 | Filtros sin landmark uniforme | Algunos formularios tenían labels, pero no `role="search"` coherente | Landmark de búsqueda con nombre “Filtrar resultados” |
| UX-05 | Sorteos abiertos/próximos dependían demasiado de verde/celeste | Había texto, pero la identidad visual se apoyaba en `text-bg-success/info` | Badge con texto, símbolo, borde y fondo propio de alto contraste |
| UX-06 | Modal destructivo no priorizaba la salida segura | El foco inicial no estaba definido y el botón de confirmación era siempre primario | Foco inicial en “Cancelar”; acción destructiva cambia a rojo y texto explícito |
| UX-07 | 403/404 tenían una sola vía de recuperación | Solo se mostraba volver al inicio | “Volver atrás” más “Ir al inicio seguro” |
| UX-08 | Formularios móviles podían provocar zoom en iOS | Controles podían heredar fuente inferior a 16 px | Controles a `1rem` en móvil |
| UX-09 | Tarjeta de sorteo podía comprimir título y badge a 320 px | Cabecera horizontal rígida | Cabecera apilada bajo 576 px |
| UX-10 | Mensaje público sugería una fase incompleta | Home decía que finanzas “todavía no” estaban habilitadas | Texto actualizado: operaciones solo dentro de sesión autorizada |

## 4. Matriz pantalla × ancho × resultado

Leyenda:

- **OK**: la estructura, clases Bootstrap y CSS propio cubren el ancho.
- **OK-scroll**: la tabla conserva desplazamiento interno, nombre accesible y foco.
- **OK-offcanvas**: navegación lateral convertida en offcanvas.
- **Manual**: debe capturarse en navegador real para evidencia final.

| Pantalla o familia | 320 px | 375 px | 768 px | 1024 px | 1440 px |
|---|---|---|---|---|---|
| Home pública | OK, CTA apiladas | OK | OK, grid intermedio | OK | OK, dos columnas |
| Login | OK, una columna | OK | OK, card centrada | OK | OK, ancho limitado |
| Registro | OK, una columna | OK | OK, dos columnas | OK | OK |
| Selección de modo | OK, cards apiladas | OK | OK, 2 columnas | OK-offcanvas | OK, hasta 3 columnas |
| Dashboard Cliente | OK-offcanvas; tarjetas apiladas; OK-scroll | Igual | OK-offcanvas; 2 columnas | OK-offcanvas | OK, sidebar y KPIs amplios |
| Dashboard Vendedor | OK-offcanvas; OK-scroll | Igual | OK-offcanvas | OK-offcanvas | OK |
| Dashboard Administrador | OK-offcanvas; OK-scroll | Igual | OK-offcanvas | OK-offcanvas | OK |
| Lista/edición de cuentas | OK-scroll; acciones apiladas | OK-scroll | OK-scroll | OK | OK |
| Perfil y contraseña | OK | OK | OK | OK | OK |
| Vendedores | OK-scroll | OK-scroll | OK-scroll | OK | OK |
| Solicitudes Cliente | OK-scroll | OK-scroll | OK | OK | OK |
| Solicitudes Vendedor/Admin | OK-scroll | OK-scroll | OK | OK | OK |
| Wallet y movimientos | OK-scroll | OK-scroll | OK | OK | OK |
| Recarga/conversión/retiro | OK, formularios apilados | OK | OK | OK | OK |
| Transferencia VIRTUAL | OK | OK | OK | OK | OK |
| Inventario Vendedor | OK-scroll | OK-scroll | OK | OK | OK |
| Productos | OK-scroll | OK-scroll | OK | OK | OK |
| Formulario de producto | OK | OK | OK | OK | OK |
| Catálogo Cliente | OK, tarjeta y badge apilados | OK | OK, 2 columnas | OK | OK, 3 columnas |
| Detalle/compra de boleto | OK, fieldset legible | OK | OK | OK | OK |
| Boletos Cliente | OK-scroll | OK-scroll | OK | OK | OK |
| Eventos Administrador | OK-scroll | OK-scroll | OK | OK | OK |
| Creación Evento/Serie | OK, selector apilado | OK | OK | OK | OK |
| Detalle de evento | OK, acciones completas | OK | OK | OK | OK |
| Publicar/consultar resultado | OK | OK | OK | OK | OK |
| Series automáticas | OK-scroll; estados textuales | OK-scroll | OK | OK | OK |
| Detalle de serie | OK-scroll; definición apilada | OK-scroll | OK | OK | OK |
| 403 y 404 | OK, botones completos | OK | OK | OK | OK |
| Offcanvas | OK, ancho máximo 90vw | OK | OK | OK | No aplica: sidebar fija |
| Mensajes | OK, texto y cierre táctil | OK | OK | OK | OK |
| Modal de confirmación | OK, botones apilables | OK | OK | OK | OK |

Resultado estructural: **todas las familias quedan cubiertas en los cinco anchos**. Resultado visual final: **Manual** hasta obtener capturas reales en Chrome/Firefox/Edge del equipo de entrega.

## 5. Comprobaciones de accesibilidad

- Bootstrap 5.3.8 se carga realmente en CSS y bundle JS.
- Existe skip link hacia `#main-content`.
- Offcanvas tiene nombre accesible, cierre con Escape proporcionado por Bootstrap y devolución de foco al toggler.
- Mensajes usan `aria-live`, `role="alert"` para error y prefijos textuales.
- Modal usa `role="dialog"`, `aria-modal`, título y descripción; el foco inicial queda en Cancelar.
- Formularios conservan labels explícitos; grupos de selección críticos usan fieldset/legend.
- Filtros principales se exponen como landmark de búsqueda.
- Tablas se exponen como regiones con nombre, ayuda y foco visible.
- Estados no dependen solo del color: incluyen texto y símbolos.
- `prefers-reduced-motion` desactiva animaciones/transiciones no esenciales.
- Objetivos táctiles principales alcanzan al menos 40–44 px.
- No se encontró texto visible que afirme que la compra o los resultados no existen.
- La navegación sigue procediendo de `nav_items` del backend; no se añadieron enlaces por fuera de los permisos.

## 6. Capturas manuales obligatorias

Crear `evidencias/04_responsive/` y guardar, como mínimo:

- `home_320.png`, `home_375.png`, `home_768.png`, `home_1024.png`, `home_1440.png`
- `login_320.png`, `registro_375.png`, `elegir_modo_768.png`
- `cliente_320.png`, `cliente_1440.png`
- `vendedor_375.png`, `vendedor_1024.png`
- `administrador_768.png`, `administrador_1440.png`
- `catalogo_sorteos_320.png`, `compra_boleto_375.png`
- `series_320.png`, `serie_detalle_1024.png`
- `tabla_scroll_320.png`
- `offcanvas_abierto_320.png`
- `modal_destructivo_375.png`
- `error_403_320.png`, `error_404_375.png`

En DevTools, para cada ancho:

1. fijar exactamente el ancho solicitado;
2. comprobar que `document.documentElement.scrollWidth === window.innerWidth` salvo el scroll interno de `.table-responsive`;
3. recorrer con Tab y Shift+Tab;
4. abrir/cerrar offcanvas y modal con teclado;
5. aumentar zoom a 200 %;
6. verificar que ninguna acción de otro modo aparezca en navegación.

## 7. Puerta de salida visual

La mejora se considera cerrada cuando:

- `python manage.py check` termina en OK;
- `python manage.py makemigrations --check --dry-run` no detecta cambios;
- `python manage.py test apps.core.tests.test_ux_accessibility -v 2` termina en OK;
- la suite completa termina en OK;
- `node --check static/js/app.js` termina en OK;
- las capturas manuales de los cinco anchos confirman ausencia de scroll horizontal de página;
- contraste, foco y navegación por teclado son aceptables;
- el manifiesto se regenera después de la última modificación.
