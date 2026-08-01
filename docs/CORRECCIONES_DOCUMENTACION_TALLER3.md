# Correcciones documentales necesarias para el Taller #3

> **DOCUMENTO HISTÓRICO:** describe una fase anterior a Vendors/Lottery. Para el estado vigente P-27 consulta `AUDITORIA_P27_2026-08-01.md`, `MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md` y `GUIA_CONTINUACION_DESDE_P27.md`.


## Regla de edición

Los cinco documentos originales se conservan en `docs/referencias/` como
evidencia. No deben editarse silenciosamente ni reemplazarse por una versión
no trazable. Para la entrega del Taller #3 se aplica
`DECISION_T3_001_SQLITE_MYSQL.md`; en una futura revisión documental deben
publicarse nuevas versiones, por ejemplo `v1.2.0-T3`.

## 1. Reglas Maestras v1.1.0

Corregir las referencias activas a PostgreSQL en las líneas aproximadas
73, 103, 112, 121, 129, 183, 206, 217–224, 1834 y 1934.

Sustituciones conceptuales:

- “Django y PostgreSQL” → “Django y la base activa de la fase
  (SQLite en fase 1; MySQL en fase 2)”.
- “persistida en PostgreSQL” → “persistida inicialmente en SQLite y migrada
  después a MySQL”.
- `MVP-GOV-002 - PostgreSQL como fuente de verdad` →
  `MVP-GOV-002 - Django y la base relacional activa como fuente de verdad`.
- `DATABASE_URL` se conserva, pero solo con esquemas `sqlite:///` y `mysql://`.

No modificar las filas históricas que comparan “Hexadecimal de 4”,
`CLIENTE_FINANCIERO` u otras reglas heredadas: son hallazgos de auditoría y
deben mantenerse etiquetados como retirados.

## 2. Plan Técnico v1.1.0

Corregir las secciones/líneas aproximadas 68, 110, 164–206, 250, 260, 483,
652–654, 738, 781–784, 845, 911, 920 y 1056.

Cambios concretos:

- Arquitectura de datos: SQLite → MySQL, no PostgreSQL.
- Instalación inicial:

  ```powershell
  pip install -r requirements.txt
  ```

- Instalación de segunda fase:

  ```powershell
  pip install -r requirements-mysql.txt
  ```

- Reemplazar `psycopg[binary]` por `mysqlclient` únicamente en la fase MySQL.
- Reemplazar el ejemplo PostgreSQL por:

  ```env
  DATABASE_URL=sqlite:///db.sqlite3
  # Fase 2:
  # DATABASE_URL=mysql://usuario:clave@127.0.0.1:3306/loteria_taller3
  ```

- La puerta de salida inicial debe exigir `/admin/`, SQLite y pruebas verdes.
- La puerta de salida de la segunda fase debe exigir MySQL, importación y
  conteos equivalentes.

La sección que menciona corregir 5 %, 15 % y 75 % es histórica y correcta:
describe residuos a retirar, no reglas activas.

## 3. Matriz de Trazabilidad v1.1.0

Corregir la fuente de verdad de la línea aproximada 71 y todas las columnas
“servidor / PostgreSQL” de las líneas aproximadas 143–210.

Reemplazar por:

```text
servidor / base activa de la fase (SQLite o MySQL)
```

En la puerta de fase cercana a la línea 855, sustituir:

```text
PostgreSQL y migración inicial
```

por dos puertas independientes:

1. SQLite y migración inicial.
2. Migración verificada a MySQL.

Las pruebas de exclusión concurrente no deben marcarse VERIFICADAS solo con
SQLite; quedan pendientes hasta repetirse en MySQL.

## 4. Diseño de Interfaz v1.0.0

No requiere cambio de base de datos. La mención a 5 %/15 %/75 % en la línea
aproximada 713 es una prohibición correcta.

Debe conservarse:

- Bootstrap 5.3;
- azul profundo/dorado;
- selector que muestra solo roles asignados;
- modo CLIENTE completo;
- modos VENDEDOR/ADMINISTRADOR sin compra;
- responsive 360, 390, 768, 1024 y 1440 px.

## 5. Auditoría de Coherencia v1.0.0

Conservar las comparaciones históricas de 5 %, 15 %, 75 % y
`CLIENTE_FINANCIERO` porque documentan problemas ya retirados.

Corregir las referencias activas a PostgreSQL en las líneas aproximadas 110,
312, 316 y 324:

- fuente de verdad → base relacional activa de la fase;
- riesgo de hosting → soporte MySQL;
- pruebas de concurrencia → MySQL real;
- veredicto → servicios Django y base activa, no JavaScript.

## Reglas vigentes que sí están correlacionadas

- Recarga académica REAL 1:1.
- Conversión VIRTUAL → REAL con 10 %.
- Compra mayorista 0.90 REAL por 1.00 VIRTUAL.
- Premio fijo por evento.
- Octal: 4 únicos; Decimal: 5 únicos; Hexadecimal: 6 únicos.
- Cliente multirrol conserva funciones completas en modo CLIENTE.
- VENDEDOR y ADMINISTRADOR no compran en esos modos.
- El servidor y la base son autoridad; el navegador solo presenta UI.
