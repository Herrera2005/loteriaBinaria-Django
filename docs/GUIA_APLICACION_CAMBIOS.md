# Guía para aplicar el paquete corregido a la rama GitHub

> **DOCUMENTO HISTÓRICO / DE FASE.** Guía de una entrega intermedia; no es la guía de instalación actual. Para el estado vigente consulte `docs/INDICE_DOCUMENTACION.md`, `README.md` y `docs/MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md`.


> **DOCUMENTO HISTÓRICO:** describe una fase anterior a Vendors/Lottery. Para el estado vigente P-27 consulta `AUDITORIA_P27_2026-08-01.md`, `MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md` y `GUIA_CONTINUACION_DESDE_P27.md`.


## 1. Antes de copiar

Desde el repositorio local:

```powershell
git switch feature/taller3-fase-1-esqueleto-sqlite
git pull --ff-only
git status --short
git rev-parse HEAD
```

El commit auditado fue:

```text
96c1d9650ff6e67af431b4e21c46a2326a50fb9b
```

Si `HEAD` es distinto, revisar el diff antes de reemplazar archivos.

Crear una rama de seguridad:

```powershell
git switch -c fix/taller3-integracion-verificable
```

No borrar `respaldo_frontend/`.

## 2. Copia controlada

Descomprimir el ZIP corregido fuera del repositorio, por ejemplo:

```text
D:\temp\loteriaBinaria-Django-auditado\
```

Copiar su contenido a la raíz del repositorio. El paquete no contiene `.git`.

Antes de aceptar cambios de migraciones:

```powershell
git diff -- apps/accounts/migrations
```

Las migraciones incluidas corresponden a la cadena observada. Si la rama ya
tiene migraciones adicionales aplicadas, no borrarlas, editarlas ni
renumerarlas.

## 3. Retirar runtime estático duplicado

El ZIP visual queda respaldado. Estas rutas antiguas no deben seguir activas
en la raíz Django:

```powershell
Remove-Item index.html -Force -ErrorAction SilentlyContinue
Remove-Item pages -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item static\app.css -Force -ErrorAction SilentlyContinue
Remove-Item templates\includes\_manages.html -Force -ErrorAction SilentlyContinue
```

No ejecutar esos comandos sobre el contenido interno del ZIP legado.

## 4. Entorno SQLite

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

No agregar `mysqlclient` hasta que SQLite esté completamente verde.

## 5. Puerta automática

```powershell
.\scripts\verify.ps1
```

El script usa `verification.sqlite3`, no `db.sqlite3`, y limpia la base y
`staticfiles/` al terminar.

## 6. Arranque local

```powershell
python manage.py migrate
python manage.py seed_baseline
python manage.py createsuperuser
python manage.py runserver
```

## 7. Pruebas manuales mínimas

1. Abrir `/` como usuario anónimo.
2. Registrar un adulto.
3. Intentar menor, username, email y documento duplicados variando mayúsculas.
4. Iniciar sesión escribiendo el username con mayúsculas y espacios.
5. Probar una cuenta de un rol y otra multirrol.
6. Cambiar de modo únicamente mediante POST.
7. Manipular la URL hacia otro dashboard y confirmar 403.
8. Confirmar que VENDEDOR/ADMINISTRADOR no muestran compra de boletos.
9. Confirmar que no hay tarjetas de módulos pendientes que simulen acciones.
10. Probar logout por POST.
11. Probar 360, 390, 768, 1024 y 1440 px.

## 8. Revisar antes del commit

```powershell
git status --short
git diff --check
git grep -n -I -E "localStorage|sessionStorage|fetch\(|usuarios\.json|pages/.*\.html|CLIENTE_FINANCIERO"
git grep -n -I -E "5%|15%|75%|123456"
```

Las menciones dentro de `docs/` o del ZIP pueden ser históricas. No deben
aparecer en código runtime.

## 9. Commit sugerido

```powershell
git add .
git commit -m "fix(taller3): integrar accounts, templates y pruebas SQLite"
git push -u origin fix/taller3-integracion-verificable
```

## 10. No continuar si

- falla una migración;
- `makemigrations --check` detecta cambios;
- una de las 48 pruebas falla;
- aparece PostgreSQL en settings o requirements runtime;
- el selector acepta un rol no asignado;
- una ruta de otro modo no devuelve 403;
- una aceptación legal puede editarse o eliminarse;
- hay acciones visuales sin backend;
- el ZIP visual fue eliminado.
