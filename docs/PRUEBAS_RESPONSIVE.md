# Pruebas responsive y accesibilidad — Taller #3 Lotería Binaria

## Alcance auditado

Archivos revisados:

- `templates/base.html`
- `templates/includes/_messages.html`
- `templates/core/home.html`
- `templates/accounts/login.html`
- `templates/accounts/register.html`
- `templates/accounts/choose_mode.html`
- `templates/dashboards/client.html`
- `templates/dashboards/vendor.html`
- `templates/dashboards/admin.html`
- `static/css/app.css`

La revisión realizada fue estática sobre el HTML Django y CSS entregados. La comprobación visual final debe ejecutarse cuando existan las vistas, formularios y contextos reales.

## Diagnóstico y cambios aplicados

1. La barra usaba `navbar-expand-lg`; en 1024 px podía quedar demasiado ajustada con usuario, modo y acciones. Se cambió a `navbar-expand-xl`, por lo que 360, 390, 768 y 1024 px usan `offcanvas`, mientras 1440 px usa navegación expandida.
2. Se agregó una clase propia al `offcanvas` para mantener el azul profundo sin depender de `text-bg-dark`.
3. Se fijaron objetivos táctiles mínimos de 44 px para botones, toggler, campos, enlaces de navegación y paginación.
4. Se reforzó el foco visible con dorado y contraste sobre botones, controles, navegación, paginación, listas y tarjetas enlazadas.
5. Se añadió control de desbordamiento para textos largos, nombres de usuario, cards, alerts y elementos interactivos.
6. Las tablas dentro de `.table-responsive` conservan un ancho mínimo y desplazan horizontalmente sin ensanchar toda la página.
7. Se ajustaron títulos `display-*`, padding de cards y aviso académico para 360/390 px.
8. La barra no es `fixed` ni `sticky`, por lo que no tapa el contenido. El enlace “Saltar al contenido” mantiene acceso por teclado.
9. Cada página revisada contiene un solo `h1`; `base.html` no introduce otro.
10. Los mensajes mantienen `aria-live="polite"` y los errores usan `role="alert"`.

## Matriz de prueba manual

| Vista | 360 px | 390 px | 768 px | 1024 px | 1440 px |
|---|---|---|---|---|---|
| Base/navbar | Offcanvas abre/cierra; marca y toggler no chocan | Igual; sin scroll horizontal | Offcanvas; usuario y botones apilados | Offcanvas para evitar saturación | Navbar expandida; enlaces y usuario alineados |
| Home | H1 envuelve sin recorte; CTA apiladas; cards a una columna | Igual | Cards a 2 columnas donde aplique | Hero en 2 columnas; productos responsivos | Hero amplio; 3 cards por fila |
| Login | Card ocupa ancho útil; inputs y botón ≥44 px | Igual | Card centrada | Card centrada | Card centrada y con ancho limitado |
| Registro | Campos en una columna; errores visibles | Igual | Campos en 2 columnas | Formulario centrado | Formulario centrado y legible |
| Elegir modo | Una card por fila; botón completo | Igual | 2 columnas | 2 columnas, offcanvas activo | Hasta 3 columnas |
| Cliente | KPIs apilados; tablas con scroll interno | Igual | KPIs 2 columnas; filtros 2 columnas | Offcanvas; filtros sin choque | KPIs 4 columnas; tabla completa |
| Vendedor | KPIs y solicitudes apilados; tabla desplazable | Igual | 2 columnas | Offcanvas; tablas internas | 4 KPIs; panel amplio |
| Administrador | Cards y tablas sin desbordar | Igual | 2 columnas | Offcanvas; acciones legibles | 3 módulos/4 KPIs según grid |

## Casos funcionales por ancho

### 360 y 390 px

- No debe existir scroll horizontal en `body`.
- El scroll horizontal solo puede aparecer dentro de `.table-responsive`.
- Marca, nombre y toggler deben caber en una línea o envolver sin superponerse.
- El `offcanvas` debe abrir, cerrar y devolver el foco al toggler.
- Botones y controles deben medir al menos 44 px de alto.
- Los botones dobles deben apilarse.
- Los mensajes largos deben envolver.
- El aviso académico no debe quedar recortado.

### 768 px

- Navbar aún debe usar `offcanvas`.
- Formularios de registro y filtros pueden usar dos columnas.
- Cards deben quedar alineadas sin alturas forzadas incorrectas.
- Tablas deben conservar scroll interno cuando sea necesario.

### 1024 px

- Navbar debe seguir en `offcanvas`; no debe comprimir enlaces, usuario y modo.
- Hero y dashboards deben aprovechar el grid sin desbordarse.
- Tablas grandes deben seguir dentro de su contenedor.
- No debe haber contenido cubierto por la cabecera.

### 1440 px

- Navbar debe mostrarse expandida.
- El usuario, modo y acciones deben permanecer alineados.
- Cards deben usar el ancho del contenedor sin líneas excesivamente largas.
- Footer debe quedar al final aun con poco contenido.

## Accesibilidad

Marcar cada caso:

- [ ] Existe un solo `h1` por página.
- [ ] Todos los inputs reales tienen `label` asociado.
- [ ] El foco se distingue en navbar, botones, formularios, cards y paginación.
- [ ] El enlace “Saltar al contenido” aparece al recibir foco.
- [ ] Los errores generales usan `role="alert"`.
- [ ] Los mensajes informativos se anuncian con `aria-live`.
- [ ] La combinación azul/dorado conserva contraste legible.
- [ ] No se comunica un estado únicamente mediante color.
- [ ] El `offcanvas` puede utilizarse con teclado y cerrarse con Escape.
- [ ] No aparecen credenciales, secretos ni datos personales reales.

## Contextos que deben probarse

- Usuario anónimo.
- Usuario autenticado con un solo rol.
- Usuario con CLIENTE y VENDEDOR.
- Usuario con los tres roles.
- Modo CLIENTE activo.
- Modo VENDEDOR activo sin acciones de compra.
- Modo ADMINISTRADOR activo sin acciones de compra.
- Listas vacías.
- Listas con muchos registros.
- Texto largo en nombre de usuario, evento y mensajes.
- Formulario con errores de campo y error general.

## Comandos de verificación

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py findstatic css/app.css
```

Buscar fuentes de verdad indebidas:

```powershell
Select-String `
    -Path templates\*.html,templates\**\*.html,static\css\app.css `
    -Pattern "localStorage|sessionStorage|usuarios\.json|fetch\(|5%|15%|75%|CLIENTE_FINANCIERO"
```

No debe haber coincidencias.

## Evidencias sugeridas

Guardar en `evidencias/04_responsive/`:

- `home_360.png`, `home_390.png`, `home_768.png`, `home_1024.png`, `home_1440.png`
- `login_360_error.png`
- `register_390_errors.png`
- `choose_mode_768.png`
- `client_360_table_scroll.png`
- `client_1440.png`
- `vendor_1024.png`
- `admin_1440.png`
- `keyboard_focus.png`
- `offcanvas_open.png`

## Puerta de salida

La auditoría queda aprobada cuando:

- no hay scroll horizontal global en los cinco anchos;
- el `offcanvas` se usa hasta 1199.98 px y la navbar se expande desde 1200 px;
- ningún control táctil principal mide menos de 44 px;
- todas las tablas anchas usan scroll interno;
- cada página tiene un solo `h1`;
- labels, foco y mensajes son perceptibles;
- la cabecera no tapa contenido;
- no existen enlaces o acciones no proporcionados por Django;
- `python manage.py check` pasa;
- no se generan migraciones.
