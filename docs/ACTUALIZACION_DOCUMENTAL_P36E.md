# Actualización documental contra el código real

## Alcance

Esta actualización comparó README, todos los Markdown de `docs/`, referencias originales, modelos, migraciones, URLs, comandos, tests y scripts de verificación del ZIP actual.

No se modificó lógica productiva, modelos, servicios, vistas, URLs, templates ni migraciones.

## Cambios documentales

- se creó `INDICE_DOCUMENTACION.md` con autoridad y clasificación;
- se añadió `docs/referencias/README.md` para explicar la adaptación SQLite→MySQL;
- se reescribió el README con el alcance P-36E real;
- se amplió la matriz a requisito→modelo→servicio→vista→template→prueba→evidencia;
- se actualizaron inventario y responsabilidades;
- se documentaron series, límites, archivo lógico, resultados automáticos e idempotencia;
- se actualizaron cifras vigentes a 458 pruebas ejecutadas;
- los documentos de fases anteriores fueron marcados como históricos sin eliminar su contenido;
- se regeneró el manifiesto SHA-256.

## Evidencia ejecutada

```text
manage.py check: OK
makemigrations --check --dry-run: No changes detected
Found 458 test(s).
Ran 458 tests
OK
MANIFIESTO SHA-256: OK
AUDITORÍA ESTÁTICA DE CIERRE: OK
```

## Limitación

La actualización no ejecutó MySQL. La fase 2 continúa pendiente de una ejecución real mediante los scripts dedicados.
