# DECISION-T3-001 — SQLite en fase 1 y MySQL en fase 2

**Estado:** APROBADA PARA EL TALLER #3  
**Autoridad:** enunciado específico del Taller #3  
**Afecta:** documentos canónicos 01, 02, 03 y 05

## Decisión

El Taller #3 usa:

1. **SQLite en la primera fase**, incluyendo desarrollo inicial, migraciones,
   administración y pruebas funcionales básicas.
2. **MySQL en la segunda fase**, mediante las mismas migraciones Django y una
   migración de datos verificada.
3. **PostgreSQL queda excluido** de esta entrega, aunque aparezca en la versión
   original de algunos documentos del MVP.

Esta decisión no modifica el proyecto empresarial ni pretende sustituir su
arquitectura. Es una adaptación obligatoria y exclusiva del Taller #3.

## Consecuencias técnicas

- `DATABASE_URL` solo acepta motores SQLite o MySQL.
- `requirements.txt` corresponde a SQLite y no instala un driver externo.
- `requirements-mysql.txt` agrega `mysqlclient` únicamente para la fase 2.
- Las migraciones deben ser portables entre ambos motores.
- No se usan SQL, índices parciales, tipos ni triggers exclusivos de PostgreSQL.
- La concurrencia real debe volver a probarse en MySQL antes de aprobar los
  servicios financieros, solicitudes y compra de boletos.
- Nunca se modifica una migración ya aplicada para “hacerla compatible”; se
  crea una migración posterior si aparece una incompatibilidad real.

## Evidencia exigida

### Fase 1

```powershell
python manage.py check
python manage.py migrate
python manage.py test
python manage.py dbshell
```

Debe confirmarse `django.db.backends.sqlite3` y una cadena de migraciones limpia.

### Fase 2

```powershell
pip install -r requirements-mysql.txt
python manage.py check
python manage.py migrate
python manage.py test
```

Además, se comparan conteos SQLite/MySQL y se repiten CRUD y operaciones
sensibles sin `--fake`.
