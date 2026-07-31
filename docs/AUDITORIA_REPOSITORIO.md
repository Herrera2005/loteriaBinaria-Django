# Auditoría del repositorio actual — Taller #3 Lotería Binaria con Django

## 1. Diagnóstico breve

Se auditó el contenido real de `loteriaBinaria-Django.zip` sin modificarlo.

El repositorio **no contiene actualmente un proyecto Django ejecutable en la rama `main`**. La rama activa incluye documentación, referencias y scripts SQL temporales, pero no contiene:

- `manage.py`;
- paquete `config`;
- apps Django;
- `requirements.txt`;
- `.gitignore`;
- templates funcionales;
- static funcional;
- migraciones activas;
- base SQLite;
- configuración MySQL.

Sí existen ramas históricas con intentos previos:

- `feature/fase-0-baseline`;
- `feature/fase-1-esqueleto`;
- `feature/fase-2-usuario-terminos`.

Sin embargo, esas ramas no deben tomarse como base automática porque:

- `feature/fase-1-esqueleto` configura PostgreSQL como única base;
- su `.env.example` contiene una URL PostgreSQL;
- `requirements.txt` incluye `psycopg`;
- `AUTH_USER_MODEL` está comentado en esa fase;
- la rama `feature/fase-2-usuario-terminos` termina en un commit que elimina todo el proyecto;
- el commit anterior de Fase 2 sí contiene una migración y modelos, pero no pertenece al estado actual de `main`.

Conclusión:

> Se continúa desde la documentación aprobada, pero la implementación Django debe comenzar de forma limpia sobre la rama actual o sobre una rama nueva creada desde `main`.

No debe recuperarse ciegamente el esqueleto PostgreSQL anterior.

---

# 2. Alcance confirmado antes de implementar

Este repositorio corresponde al Taller #3, no al proyecto empresarial ni al monorepo NestJS.

Decisiones vigentes:

- SQLite primero;
- MySQL después;
- Bootstrap 5.3;
- cinco apps canónicas;
- CRUD evaluable en `accounts`, `vendors` y `lottery`;
- login y roles como mejora;
- historial sin delete genérico;
- usuario personalizado antes de la primera migración;
- montos `BigIntegerField` con sufijo `_minor`;
- reglas sensibles en `services.py` con `transaction.atomic`;
- sin PostgreSQL.

---

# 3. Estado Git observado

## Rama activa

```text
main
```

## Seguimiento remoto

```text
main...origin/main
```

## Estado de trabajo

```text
limpio
```

No se observaron archivos modificados o sin seguimiento dentro del ZIP.

## Ramas locales encontradas

```text
main
feature/fase-0-baseline
feature/fase-1-esqueleto
feature/fase-2-usuario-terminos
```

## Últimos commits visibles

```text
765041c md
d58819a Mds del proyecto
d3b7a30 haciendo desde 0
dc4f3e1 feat(fase-2): crear usuario personalizado y terminos
4803a59 feat(fase-1): crear esqueleto Django y configuracion
36a728c primera parte fase 1
39d6d2f docs(fase-0): congelar baseline del MVP Django
```

Hallazgo importante:

- `d3b7a30` elimina 68 archivos del intento Django anterior;
- por eso la rama `feature/fase-2-usuario-terminos` termina vacía;
- `main` fue reconstruida después únicamente con documentación.

---

# 4. Tabla de auditoría principal

| Elemento solicitado | Estado en `main` | Evidencia real | Clasificación | Decisión |
|---|---|---|---|---|
| `manage.py` | No existe | No aparece en el árbol de `main` | FALTA | Crear en la fase de esqueleto |
| `config/settings.py` | No existe | No hay carpeta `config` | FALTA | Crear configuración portable |
| `config/settings/` dividido | No existe | Solo aparece en ramas antiguas | FALTA | Puede crearse después según plan |
| `config/urls.py` | No existe | No hay paquete `config` | FALTA | Crear con admin inicialmente |
| Apps Django | No existen | No existe carpeta `apps` en `main` | FALTA | Crear cinco apps |
| `AUTH_USER_MODEL` | No existe | No hay settings | FALTA CRÍTICA | Definir antes de migrar |
| Migraciones activas | No existen | No hay carpetas `migrations` en `main` | FALTA | Generar después de `User` |
| Templates Django | No existen | No hay carpeta `templates` en `main` | FALTA | Crear estructura base |
| Static Django | No existe | No hay carpeta `static` en `main` | FALTA | Crear estructura Bootstrap/CSS |
| `requirements.txt` | No existe | No está rastreado en `main` | FALTA | Crear limpio, sin psycopg |
| `.gitignore` | No existe | No está rastreado en `main` | FALTA | Crear antes de venv y `.env` |
| `.env.example` | No existe | No está en `main` | FALTA | Crear para SQLite/MySQL |
| `db.sqlite3` | No existe | No se encontró archivo SQLite | CORRECTO PARA PRE-MIGRACIÓN | Crear solo después de `User` |
| Base MySQL final | No existe | Solo hay scripts temporales | CORRECTO | Configurar en segunda fase |
| Scripts SQL temporales | Existen | `docs/sql/00`, `01`, `02` | EXISTE | Solo evidencia ER, no base final |
| Documentación del alcance | Existe | Archivos en `docs/` | EXISTE | Conservar |
| Modelo ER | Existe | `docs/MODELO_ER.md` | EXISTE | Conservar |
| Plan de apps | Existe | `docs/PLAN_APPS.md` | EXISTE | Conservar |
| Plan de implementación | Existe | `docs/PLAN_IMPLEMENTACION_APPS.md` | EXISTE | Conservar |
| Modelo consolidado de referencia | Existe | `docs/modelo_consolidado_referencia.py` | EXISTE, NO EJECUTABLE | Usar solo como referencia |
| Evidencias | Carpeta vacía | `evidencias/` sin archivos | INCOMPLETO | Poblar por fase |
| Respaldo frontend | Carpeta vacía | `respaldo_frontend/` sin archivos | INCOMPLETO | Agregar ZIP/archivos solo si se autoriza |
| Bootstrap 5.3 | No implementado | No hay templates/static | FALTA | Integrar en fase de interfaz |
| CRUD `accounts` | No existe | Sin app ni código | FALTA | Implementar primero |
| CRUD `vendors` | No existe | Sin app ni código | FALTA | Implementar después |
| CRUD `lottery` | No existe | Sin app ni código | FALTA | Implementar después |
| Login/roles | No existe | Sin Auth personalizado activo | FALTA | Mejora posterior al CRUD base |

---

# 5. Revisión específica de `manage.py`

## Estado actual

```text
NO EXISTE EN main
```

## Hallazgo en rama histórica

En `feature/fase-1-esqueleto` sí existió un `manage.py` que establecía:

```text
DJANGO_SETTINGS_MODULE=config.settings.local
```

Ese archivo era técnicamente razonable, pero pertenece a una rama antigua configurada para PostgreSQL.

## Decisión

No editar ni recuperar `manage.py` aisladamente.

Cuando se cree el proyecto Django, debe usarse el `manage.py` generado por:

```text
django-admin startproject config .
```

Solo se modificaría con una razón extraordinaria. En principio no se modifica.

---

# 6. Revisión específica de settings

## Estado actual

```text
NO EXISTE config/settings.py NI config/settings/
```

## Hallazgos de la rama histórica

La rama `feature/fase-1-esqueleto` contenía:

```text
config/settings/base.py
config/settings/local.py
config/settings/production.py
```

Aspectos aprovechables conceptualmente:

- `BASE_DIR`;
- templates globales;
- static global;
- cinco apps;
- zona horaria;
- `BigAutoField`;
- variables de entorno.

Aspectos que contradicen el taller:

```text
# PostgreSQL es la única base de datos del MVP.
DATABASES = {
    "default": env.db("DATABASE_URL"),
}
```

Y en `.env.example`:

```text
DATABASE_URL=postgresql://...
```

También incluía:

```text
psycopg
psycopg-binary
```

## Decisión

No reutilizar ese settings sin corregirlo completamente.

La nueva primera configuración debe usar SQLite. MySQL se agregará solo en la segunda fase.

---

# 7. Revisión de `urls.py`

## Estado actual

```text
NO EXISTE
```

## Estado histórico

La rama previa solo tenía:

```text
admin/
```

No existían includes para:

- `accounts`;
- `core`;
- `finance`;
- `vendors`;
- `lottery`.

## Decisión

El primer `config/urls.py` podrá contener solo admin mientras se crea el esqueleto, pero después deberá incluir las apps por fases.

No deben inventarse rutas CRUD antes de revisar los archivos reales de cada fase.

---

# 8. Revisión de apps

## Estado actual en `main`

```text
NO EXISTE apps/
```

## Estado histórico

En `feature/fase-1-esqueleto` existieron las cinco apps:

```text
apps/accounts
apps/core
apps/finance
apps/vendors
apps/lottery
```

Pero sus `models.py`, `views.py`, `admin.py` y tests eran mayormente archivos vacíos generados por `startapp`.

## Decisión

Crear las cinco apps desde cero en una rama nueva.

No recuperar archivos vacíos solo para aparentar avance.

---

# 9. Revisión de `AUTH_USER_MODEL`

## Estado actual

```text
NO DEFINIDO
```

## Estado histórico de Fase 1

Estaba comentado:

```text
# AUTH_USER_MODEL = "accounts.User"
```

## Estado histórico del commit anterior de Fase 2

En `dc4f3e1` sí estaba activo:

```text
AUTH_USER_MODEL = "accounts.User"
```

También existía:

```text
apps/accounts/migrations/0001_initial.py
```

## Riesgo

Recuperar solo la migración sin recuperar exactamente sus modelos, settings y dependencias produciría inconsistencias.

## Decisión

En la implementación nueva:

1. crear `accounts.User`;
2. configurar `AUTH_USER_MODEL`;
3. ejecutar `makemigrations accounts`;
4. revisar la migración;
5. ejecutar el primer `migrate`.

No ejecutar `migrate` antes.

---

# 10. Revisión de migraciones

## Migraciones activas en `main`

```text
NINGUNA
```

Por tanto, actualmente no hay migraciones aplicadas ni archivos que deban conservarse como historial activo.

## Migración histórica encontrada

Solo en el commit `dc4f3e1`:

```text
apps/accounts/migrations/0001_initial.py
```

Esa migración fue eliminada después por `d3b7a30`.

## Migraciones que no deben editarse

### En el estado actual

No existe ninguna migración activa.

### Si se decide restaurar el commit histórico

No debe editarse manualmente:

```text
apps/accounts/migrations/0001_initial.py
```

En ese caso debe restaurarse el conjunto coherente completo:

- modelo;
- settings;
- migración;
- forms;
- validators;
- services;
- tests.

Sin embargo, **no se recomienda restaurarlo directamente**, porque fue creado bajo configuración PostgreSQL y antes de redefinir el perfil SQLite → MySQL del Taller #3.

## Regla futura

Una vez generada y aplicada una migración nueva:

- no reescribirla;
- no cambiar su contenido para adaptarla a MySQL;
- crear migraciones posteriores;
- probar la cadena desde base vacía.

---

# 11. Revisión de templates

## Estado actual

```text
NO EXISTEN
```

La carpeta `templates/` solo existió en ramas antiguas mediante `.gitkeep`.

No existen:

- `base.html`;
- navbar;
- login;
- CRUD;
- dashboards;
- templates Bootstrap.

## Decisión

La interfaz debe comenzar después del esqueleto y usuario personalizado.

Bootstrap 5.3 debe ser real, no una copia completa del CSS legado.

---

# 12. Revisión de static

## Estado actual

```text
NO EXISTE
```

La rama histórica tenía solo:

```text
static/css/.gitkeep
static/img/.gitkeep
static/js/.gitkeep
```

No hay:

- Bootstrap local;
- CSS azul/dorado;
- logo;
- JavaScript;
- assets.

## Decisión

Crear la estructura en la fase correspondiente.

El JavaScript futuro será únicamente de presentación. No será fuente de verdad.

---

# 13. Revisión de requirements

## Estado actual

```text
NO EXISTE requirements.txt EN main
```

## Estado histórico

El archivo antiguo estaba codificado en UTF-16 y contenía:

```text
Django==5.2.16
django-environ
gunicorn
psycopg
psycopg-binary
whitenoise
```

## Problemas

- `psycopg` contradice el Taller #3;
- `psycopg-binary` contradice el Taller #3;
- la codificación UTF-16 puede causar problemas con `pip`;
- MySQL aún no debe configurarse en la primera fase;
- `gunicorn` y `whitenoise` no son necesarios para iniciar SQLite.

## Decisión

Crear un `requirements.txt` nuevo en UTF-8 cuando corresponda.

Primera fase: Django y dependencias mínimas.

Segunda fase: agregar el driver MySQL aprobado.

---

# 14. Revisión de `.gitignore`

## Estado actual

```text
NO EXISTE EN main
```

## Estado histórico aprovechable

La versión anterior ignoraba:

```text
.venv/
.env
__pycache__/
*.py[cod]
staticfiles/
media/
db.sqlite3
*.sqlite3
.vscode/
.idea/
```

## Decisión

Crear `.gitignore` antes de instalar o generar archivos locales.

Debe ignorar `db.sqlite3` porque es una base local de desarrollo, salvo que el enunciado exija expresamente entregarla.

---

# 15. Revisión de bases existentes

## SQLite

No se encontró:

```text
db.sqlite3
*.sqlite3
*.db
```

## MySQL

No se puede confirmar una base MySQL externa desde el ZIP.

## SQL temporal

Existen:

```text
docs/sql/00_validacion_ddl.sql
docs/sql/01_validacion_inserts.sql
docs/sql/02_validacion_checks.sql
```

Estos scripts:

- validan el ER;
- no son migraciones Django;
- no deben usarse para crear la base final;
- la base temporal debe eliminarse después de validarla.

## PostgreSQL

No existe una base PostgreSQL dentro del ZIP, pero la rama histórica sí contiene configuración PostgreSQL. Esa configuración contradice el taller actual.

---

# 16. ¿Se parte de cero o se continúa?

## Respuesta

Se adopta una decisión intermedia precisa:

> Se continúa con la documentación, el ER, el plan de apps y las decisiones ya aprobadas; pero la implementación Django se inicia desde un esqueleto limpio.

No se parte de cero conceptualmente porque ya existen:

- alcance;
- apreciación;
- ER;
- scripts temporales;
- plan de apps;
- plan de implementación;
- modelo consolidado de referencia;
- referencias canónicas.

Sí se parte de cero técnicamente en `main` porque no existe un proyecto Django ejecutable.

---

# 17. Tabla final: existe / incompleto / falta / contradice

| Elemento | Estado |
|---|---|
| Documentación base | EXISTE |
| Modelo ER | EXISTE |
| Scripts SQL temporales | EXISTE |
| Plan de apps | EXISTE |
| Plan de implementación | EXISTE |
| Auditoría del ZIP | FALTA EN EL ZIP ACTUAL DE `main` |
| `manage.py` | FALTA |
| Proyecto `config` | FALTA |
| Settings SQLite | FALTA |
| Settings MySQL | FALTA, CORRECTO POR AHORA |
| Apps | FALTAN |
| `User` personalizado | FALTA |
| `AUTH_USER_MODEL` | FALTA CRÍTICA |
| Migraciones activas | FALTAN |
| Templates | FALTAN |
| Bootstrap | FALTA |
| Static | FALTA |
| Requirements actual | FALTA |
| `.gitignore` | FALTA |
| `.env.example` | FALTA |
| Base SQLite | FALTA, CORRECTO ANTES DE MIGRAR |
| CRUD `accounts` | FALTA |
| CRUD `vendors` | FALTA |
| CRUD `lottery` | FALTA |
| Login/roles | FALTA |
| Configuración PostgreSQL histórica | CONTRADICE |
| `psycopg` histórico | CONTRADICE |
| Rama Fase 2 vacía por borrado | INCOMPLETO / NO UTILIZABLE |
| Carpetas `evidencias` y `respaldo_frontend` | INCOMPLETAS |

---

# 18. Comandos de diagnóstico para ejecutar localmente

Ejecutar desde la raíz del repositorio.

## Git

```powershell
git status
git branch -a
git log --oneline --decorate --graph --all -20
git ls-tree -r --name-only main
```

## Archivos raíz

```powershell
Get-ChildItem -Force
Get-ChildItem -Recurse -File | Select-Object FullName
```

## Archivos críticos

```powershell
Test-Path manage.py
Test-Path config
Test-Path apps
Test-Path requirements.txt
Test-Path .gitignore
Test-Path db.sqlite3
```

## Buscar configuración contradictoria

```powershell
git grep -n -i "postgres\|psycopg\|DATABASE_URL" -- .
git grep -n "AUTH_USER_MODEL" -- .
git grep -n -i "localStorage\|usuarios.json\|password" -- .
```

## Revisar ramas históricas sin cambiarlas

```powershell
git ls-tree -r --name-only feature/fase-1-esqueleto
git show feature/fase-1-esqueleto:config/settings/base.py
git show feature/fase-1-esqueleto:.env.example
git show dc4f3e1:apps/accounts/models.py
git show dc4f3e1:apps/accounts/migrations/0001_initial.py
```

## Bases locales

```powershell
Get-ChildItem -Recurse -File -Include *.sqlite3,*.db,.env
```

No ejecutar todavía:

```powershell
python manage.py migrate
python manage.py makemigrations
```

No pueden ejecutarse porque `manage.py` no existe en `main`.

---

# 19. Pruebas de auditoría

- [x] Se revisó la rama activa.
- [x] Se revisó el estado Git.
- [x] Se revisaron ramas históricas.
- [x] Se comprobó que `manage.py` no existe en `main`.
- [x] Se comprobó que `config` no existe en `main`.
- [x] Se comprobó que `apps` no existe en `main`.
- [x] Se comprobó que `AUTH_USER_MODEL` no está activo.
- [x] Se comprobó que no existen migraciones activas.
- [x] Se comprobó que no existe SQLite.
- [x] Se identificó configuración PostgreSQL histórica.
- [x] Se identificó el commit que eliminó el proyecto previo.
- [x] No se modificó el repositorio.

---

# 20. Siguiente paso único

El único siguiente paso recomendado es:

> Crear una nueva rama desde `main` para la Fase 1 y preparar únicamente el entorno y el esqueleto Django con SQLite, sin ejecutar `migrate`.

Nombre sugerido:

```text
feature/taller3-fase-1-esqueleto-sqlite
```

No se debe recuperar directamente `feature/fase-1-esqueleto`, porque contiene decisiones PostgreSQL incompatibles.

---

# 21. Puerta de salida

La auditoría queda aprobada cuando:

- `docs/AUDITORIA_REPOSITORIO.md` está guardado;
- el usuario confirma que trabajará desde `main`;
- se confirma que las ramas antiguas serán solo referencia;
- no se ha ejecutado `migrate`;
- no se ha creado todavía código fuera de la Fase 1;
- el siguiente trabajo se limita al esqueleto SQLite.

No avanzar si se pretende:

- continuar directamente desde la rama Fase 2 vacía;
- reutilizar settings PostgreSQL;
- instalar `psycopg`;
- ejecutar migraciones antes de `accounts.User`;
- mezclar esta entrega con el proyecto empresarial.
