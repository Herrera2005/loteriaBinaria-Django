# Verificación reproducible de `runserver`

## Objetivo

Comprobar que el proyecto inicia con SQLite y que la landing pública responde con HTTP 200 y contiene los elementos principales del Taller #3.

## Inicio normal en Windows

```powershell
.\.venv\Scripts\Activate.ps1
.\scripts\run_local.ps1
```

La página esperada es:

```text
http://127.0.0.1:8000/
```

Debe mostrar:

- logo y nombre Lotería Binaria;
- aviso de simulación académica;
- explicación Octal, Decimal y Hexadecimal;
- botones de login y registro para usuarios anónimos;
- Bootstrap 5.3 y la identidad azul/dorada.

## Smoke test automatizado

Con las migraciones ya aplicadas:

```powershell
python scripts/smoke_runserver.py
```

El script:

1. comprueba que el puerto 8765 está libre;
2. inicia `runserver --noreload` de manera temporal;
3. consulta `http://127.0.0.1:8765/`;
4. exige HTTP 200 y los textos principales;
5. detiene el servidor incluso si ocurre un error.

Salida esperada:

```text
SMOKE RUNSERVER: OK - http://127.0.0.1:8765/ respondió HTTP 200.
```

## Verificación completa

```powershell
.\scripts\verify.ps1
```

La verificación usa `verification.sqlite3`, ejecuta migraciones, seed baseline, smoke de `runserver`, tests y comprobación de static. Después elimina la base temporal y `staticfiles`, sin tocar `db.sqlite3`.
