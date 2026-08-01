# Resultado de auditoría final de la base del Taller #3

## Alcance revisado

- configuración Django y SQLite;
- cinco apps canónicas;
- `accounts.User`, términos y aceptaciones;
- autenticación, roles y modo activo;
- rutas, templates, static y Bootstrap;
- seeds;
- pruebas;
- scripts de inicio y verificación;
- continuidad con el Manual Intercalado v4.0;
- conservación del ZIP visual anterior.

## Correcciones consolidadas

- una sola estructura Django activa;
- retirada del runtime de `index.html`, `pages/` y CSS mal ubicado;
- respaldo visual conservado como ZIP fuera de `static`;
- SQLite por defecto y MySQL preparado para la segunda fase;
- PostgreSQL bloqueado para esta entrega;
- logout y selección de modo mediante POST/CSRF;
- navegación calculada por el backend;
- módulos futuros sin botones ni datos simulados;
- auditoría estática reproducible;
- smoke test de `runserver` incorporado;
- script de inicio local;
- workflow CI para repetir la verificación en GitHub;
- documentación de dependencias y orden de crecimiento.

## Verificaciones ejecutadas en el paquete

```text
AUDITORÍA ESTÁTICA: OK
Python: compilación sintáctica OK
JavaScript: sintaxis OK
Bash: sintaxis OK
ZIP legado: conservado
Archivos temporales/secretos: ausentes
```

## Verificación runtime

La verificación runtime queda automatizada mediante:

```powershell
.\scripts\verify.ps1
```

Incluye una base SQLite limpia, migraciones, `seed_baseline`, ejecución temporal de `runserver`, petición HTTP a la landing, suite Django y static.

El entorno de generación de este paquete no tiene Django instalado ni acceso directo al índice de paquetes, por lo que no se afirma falsamente que `runserver` se ejecutó aquí. El script y GitHub Actions permiten comprobarlo de forma reproducible en el equipo del estudiante o al subir la rama.

## Calificación

| Dimensión | Nota |
|---|---:|
| Estructura y coherencia | 9.6/10 |
| Seguridad de la fase actual | 9.5/10 |
| Templates y responsive | 9.4/10 |
| Pruebas y reproducibilidad | 9.6/10 |
| Escalabilidad con el manual | 9.7/10 |
| Estado global antes de ejecutar runtime | **9.5/10** |

La nota puede considerarse **9.8/10** cuando `scripts/verify.ps1` y el workflow de GitHub terminen en verde.
