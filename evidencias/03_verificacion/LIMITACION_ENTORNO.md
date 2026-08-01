# Limitación del entorno de generación

## Comprobaciones ejecutadas

- `python scripts/audit_project.py`: **OK**.
- `python -m compileall -q apps config scripts manage.py`: **OK**.
- `node --check static/js/app.js`: **OK**.
- revisión AST básica de imports no utilizados: **OK**.
- inventario y hash del ZIP legado: **OK**.
- copia exacta del logo legado: **OK**.

## Comprobaciones no ejecutadas aquí

El entorno de generación no tenía Django instalado. El índice de paquetes
disponible en el contenedor no ofreció `Django==5.2.16`, por lo que la
instalación no pudo completarse. Por honestidad, no se afirma que se hayan
ejecutado:

- `python manage.py check`;
- `python manage.py makemigrations --check --dry-run`;
- `python manage.py migrate`;
- las 48 pruebas Django;
- `findstatic`;
- `collectstatic`.

## Cómo cerrar la limitación

En Windows, desde la raíz y con el entorno activado:

```powershell
pip install -r requirements.txt
.\scripts\verify.ps1
```

Guardar la salida completa en:

```text
evidencias/03_verificacion/verificacion_django_local.txt
```

La fase no debe marcarse VERIFICADA hasta que ese archivo muestre todos los
comandos verdes.
