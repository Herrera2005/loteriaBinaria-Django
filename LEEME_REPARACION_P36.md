# Reparación P-36 lista para aplicar

Este paquete corrige el error al abrir sorteos y restaura la diferenciación visual por estado.

## Aplicación recomendada

1. Guarda un commit del estado actual.
2. Copia el contenido del paquete sobre la raíz del proyecto.
3. No elimines tu `db.sqlite3` ni tu `.env` local.
4. Ejecuta:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.lottery.tests.test_client_catalog -v 2
python manage.py test apps.lottery.tests.test_filters_and_colors -v 2
python manage.py test apps.lottery -v 2
python manage.py test -v 2
python scripts/audit_project.py
```

5. Reinicia el servidor y pulsa `Ctrl + F5` en el navegador.

## Resultado visual

- ventas abiertas: borde verde;
- próximos: borde celeste;
- estados restantes: borde gris;
- símbolos: contorno con el color del producto.

No se agregó ninguna migración y no se modificó la base de datos.
