# Escalabilidad conforme al Manual Intercalado v4.0

## Estado actual consolidado

La base entregada cubre las puertas previas y visuales necesarias para continuar sin rehacer arquitectura:

- proyecto `config` y cinco apps canónicas;
- SQLite como base de la primera fase;
- `accounts.User` personalizado antes de la primera migración;
- términos y aceptaciones históricas;
- administración y seeds idempotentes de `accounts/core`;
- autenticación, logout por POST y selector de modo en sesión Django;
- `base.html`, Bootstrap 5.3, templates públicos y dashboards;
- frontend legado aislado en un ZIP de respaldo;
- auditoría responsive y pruebas automatizadas.

## Correspondencia con el manual

| Bloque del manual | Estado | Evidencia principal |
|---|---|---|
| P-13 Settings, templates, static y SQLite | Completo | `config/settings.py`, `.env.example`, `templates/`, `static/` |
| P-14 Usuario personalizado | Completo | `apps/accounts/models.py`, migraciones y `AUTH_USER_MODEL` |
| P-15 Migración SQLite y admin | Preparado y verificable localmente | `scripts/run_local.*`, `scripts/verify.*` |
| P-16 Admin seguro y seed | Completo para `accounts/core` | `apps/accounts/admin.py`, `seed_baseline`, `seed_demo` |
| P-17 Base Bootstrap | Completo | `templates/base.html`, `static/css/app.css` |
| P-18 Público, login y registro | Completo | templates y forms de `accounts` |
| P-19 Selector y dashboards | Completo para los módulos existentes | sesión Django y decoradores backend |
| P-20 Responsive/accesibilidad | Preparado | `docs/PRUEBAS_RESPONSIVE.md` |
| P-21 Migración frontend | Completo en alcance actual | `docs/PLAN_MIGRACION_ZIP_TEMPLATES_STATIC.md` |

## Fronteras para las siguientes fases

Las apps `finance`, `vendors` y `lottery` existen, pero no simulan funcionalidades inexistentes. Esta decisión evita dependencias circulares y permite implementar cada módulo en el orden del manual.

### `finance`

Responsabilidad futura:

- `Wallet` REAL/VIRTUAL;
- montos en `BigIntegerField` con sufijo `_minor`;
- movimientos históricos protegidos;
- reservas y liberaciones;
- servicios atómicos para recarga 1:1 y conversión con 10 %.

No debe conocer HTML ni leer valores de JavaScript.

### `vendors`

Responsabilidad futura:

- perfil del vendedor;
- solicitudes Cliente-Vendedor;
- asignación, aceptación, confirmación, cancelación y expiración;
- compra mayorista 0.90 REAL por 1.00 VIRTUAL mediante servicio;
- CRUD evaluable del perfil o entidad definida por el plan aprobado.

Dependerá de `accounts` y `finance`, pero `finance` no debe depender de `vendors`.

### `lottery`

Responsabilidad futura:

- productos Octal, Decimal y Hexadecimal;
- eventos no editables después de publicados;
- boletos, resultados y acreditación;
- reglas 4/5/6 símbolos únicos;
- límite de compra del cliente y liberación temporal;
- CRUD evaluable de productos/eventos según el plan aprobado.

Dependerá de `accounts` y `finance`. Las fórmulas y transiciones vivirán en `services.py`.

## Orden de crecimiento obligatorio

1. Cerrar la puerta SQLite actual con `scripts/verify.ps1`.
2. Implementar modelos y migraciones de un solo módulo.
3. Registrar admin y seed mínimo del mismo módulo.
4. Crear services con `transaction.atomic`.
5. Crear forms y vistas protegidas.
6. Conectar templates existentes sin inventar tarjetas ni enlaces.
7. Añadir pruebas del módulo.
8. Repetir para el siguiente módulo.
9. Solo después de tener SQLite completamente verde, migrar a MySQL.

## Reglas de dependencia

```text
accounts  <- finance <- vendors
    \          \
     \----------> lottery
core coordina navegación y páginas, pero no contiene reglas financieras.
```

- `accounts` no importa modelos de `finance`, `vendors` o `lottery`.
- `finance` puede referenciar `AUTH_USER_MODEL`, pero no vistas ni templates.
- `vendors` y `lottery` llaman servicios de `finance`; no editan saldos directamente.
- las vistas no duplican fórmulas;
- JavaScript no decide permisos, saldos, estados ni resultados.

## Puerta antes de MySQL

No cambiar `DATABASE_URL` a MySQL hasta aprobar:

```powershell
.\scripts\verify.ps1
```

Después, instalar `requirements-mysql.txt`, crear una base vacía y repetir migraciones, seeds, tests y conteos. No usar `--fake` para ocultar incompatibilidades.
