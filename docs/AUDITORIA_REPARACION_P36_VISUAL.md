# Auditoría y reparación P-36 — catálogo visual y detalle de sorteos

Fecha de revisión: 2 de agosto de 2026.

## Alcance revisado

Se auditó el proyecto completo entregado, con énfasis en:

- catálogo de sorteos del Cliente;
- panel principal del Cliente;
- detalle y compra de un sorteo;
- color identificador de productos;
- sincronización de estados visibles;
- pruebas de regresión;
- auditoría estática y residuos de entrega.

No se modificaron las reglas financieras, los servicios de compra, la publicación de resultados ni las migraciones existentes.

## Calificación antes de la reparación: 5,8/10

La lógica principal seguía presente, pero el sistema tenía un fallo crítico de presentación:

1. `client_event_detail.html` contenía un tag Django dividido entre dos líneas:

   ```django
   {% if not
       has_enough_virtual %}
   ```

   Django no lo interpretaba como un bloque completo. El `{% endif %}` posterior cerraba el bloque exterior y el siguiente `{% elif is_upcoming %}` quedaba fuera de contexto. Esto provocaba `TemplateSyntaxError` al abrir un sorteo.

2. La comparación de cancelación tenía un espacio dentro del valor:

   ```django
   event.status == " CANCELLED"
   ```

   Por ello, un evento cancelado no recibía correctamente la alerta de peligro.

3. `LotteryProductForm` tenía dos métodos `clean_accent_color`. El segundo reemplazaba silenciosamente al primero, dejando código muerto y una conducta menos clara.

4. El widget de color se reconstruía varias veces y `self.fields["code"].required = False` estaba duplicado.

5. El estilo visual dependía demasiado del CSS personalizado y de la copia en caché del navegador. Las tarjetas podían verse sin borde de estado aunque Bootstrap siguiera cargado.

6. El dashboard no sincronizaba estados antes de consultar y no incluía de forma uniforme eventos `SCHEDULED` próximos.

7. La auditoría estática previa no detectaba tags Django partidos después del nombre de la instrucción.

8. El ZIP contenía numerosos `__pycache__`, archivos `.pyc` y dos respaldos `.bak`, por lo que su propia auditoría estática fallaba.

## Reparaciones aplicadas

### Plantillas

- Se reconstruyó `templates/lottery/client_event_detail.html` sin tags multilínea.
- Se corrigió la comparación exacta con `CANCELLED`.
- Se conservaron compra, consulta parcial, sugerencias, saldo y mensajes existentes.
- Se añadieron bordes Bootstrap robustos:
  - verde para ventas abiertas;
  - celeste para próximos;
  - gris para estados neutrales.
- Se mantuvo el color del producto en el marcador y los símbolos.
- Se actualizaron el catálogo y el dashboard para usar la misma presentación.

### Vista del dashboard

`_visible_event_rows()` ahora:

- sincroniza estados antes de consultar;
- incluye `SCHEDULED`, `PUBLISHED` y `SALES_OPEN`;
- coloca primero los eventos con ventas abiertas;
- expone `is_open_now` e `is_upcoming` al template;
- conserva orden estable por cierre, sorteo e identificador.

### Formulario de producto

- Se creó `ColorInput` con `input_type = "color"`.
- Se dejó una sola implementación de `clean_accent_color`.
- Si un formulario antiguo no envía el color, conserva el valor actual o usa `#FD7E14`.
- Se eliminaron configuraciones y asignaciones duplicadas.

### CSS y caché

- Se conservó el borde superior por color de producto para tarjetas sin estado visual.
- Las tarjetas abiertas y próximas usan borde completo de estado.
- Se eliminaron selectores de insignias que ya no tenían uso.
- `base.html` incorpora una versión de CSS en la URL para evitar que el navegador reutilice la copia anterior.

### Auditoría preventiva

`scripts/audit_project.py` ahora detecta:

- tags Django partidos en cualquier posición;
- bloques `if`, `for`, `block` y `with` mal cerrados;
- ramas `elif`, `else` o `empty` fuera de contexto;
- métodos o clases duplicados dentro del mismo ámbito Python.

### Pruebas agregadas

Se añadieron regresiones para comprobar:

- detalle abierto renderizable;
- detalle próximo renderizable sin `TemplateSyntaxError`;
- clases visuales verde y celeste;
- símbolos visibles;
- dashboard con abiertos antes que próximos;
- conservación del color existente en formularios antiguos.

## Calificación después de la reparación: 9,2/10 provisional

Resultado estático verificado en la copia reparada:

```text
AUDITORÍA ESTÁTICA P-28: OK
Python parseable y sin bytecode versionado
Templates y bloques Django verificados
SQLite/MySQL conservados; PostgreSQL excluido
396 pruebas automatizadas diseñadas
```

La calificación queda como provisional porque la suite Django completa debe ejecutarse en el `.venv` del proyecto, donde está instalada la versión requerida de Django.

## Comprobación local obligatoria

Desde la raíz del proyecto:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.lottery.tests.test_client_catalog -v 2
python manage.py test apps.lottery.tests.test_filters_and_colors -v 2
python manage.py test apps.lottery -v 2
python manage.py test -v 2
python scripts/audit_project.py
```

Después de iniciar el servidor, usar `Ctrl + F5` una vez para forzar la carga del CSS reparado.

## Puerta de salida

La reparación se considera aprobada cuando:

- el detalle de un sorteo devuelve HTTP 200;
- los abiertos muestran borde verde;
- los próximos muestran borde celeste;
- los símbolos se ven con el color del producto;
- no aparece `TemplateSyntaxError`;
- no hay `FAIL` ni `ERROR` en la suite;
- la auditoría estática termina en `OK`.
