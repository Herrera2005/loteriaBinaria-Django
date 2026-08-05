# Comparación del último commit observado con el paquete corregido

> **DOCUMENTO HISTÓRICO / DE FASE.** Comparación de una etapa temprana; sus conteos y ausencias no son vigentes. Para el estado vigente consulte `docs/INDICE_DOCUMENTACION.md`, `README.md` y `docs/MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md`.


> **DOCUMENTO HISTÓRICO:** describe una fase anterior a Vendors/Lottery. Para el estado vigente P-27 consulta `AUDITORIA_P27_2026-08-01.md`, `MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md` y `GUIA_CONTINUACION_DESDE_P27.md`.


## Commit base

```text
Rama: feature/taller3-fase-1-esqueleto-sqlite
SHA: 96c1d9650ff6e67af431b4e21c46a2326a50fb9b
Mensaje: fase 2 y parte de fase 3
```

## Diferencias estructurales relevantes

| En commit observado | En paquete corregido |
|---|---|
| `config/urls.py` solo admin | incluye accounts y core |
| views de accounts/core como stubs | flujos y dashboards conectados |
| `static/app.css` | `static/css/app.css` |
| `_manages.html` | `_messages.html` |
| `index.html` y `pages/` activos | retirados del runtime; conservados dentro del ZIP |
| password demo fija | variable de entorno validada |
| sin test packages completos | 48 pruebas diseñadas en 7 archivos |
| sin puerta limpia | scripts PowerShell/Bash con SQLite temporal |
| docs con conflicto DB | decisión y correcciones trazables |

## Archivos que deben eliminarse del runtime al aplicar

```text
index.html
pages/
static/app.css
templates/includes/_manages.html
```

## Archivos que no deben eliminarse

```text
respaldo_frontend/Proyecto_HerreraNietoCristhian_legacy.zip
docs/referencias/*
apps/accounts/migrations/*
```

Las migraciones solo se sustituyen si coinciden con la cadena auditada. Si el
repositorio avanzó, se comparan y se conserva toda migración ya aplicada.

## Endurecimiento adicional del paquete

- normalización case-insensitive portable de username, email y documento;
- historial legal protegido a nivel de modelo y QuerySet;
- conteos administrativos ocultos para cuentas sin `is_staff`;
- cards de módulos pendientes fuera del render actual;
- foco/ARIA y confirmaciones visuales corregidas;
- ruta SQLite independiente del directorio desde donde se ejecute Django.
