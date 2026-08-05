# Reporte final de cierre SQLite

Fecha de validación: 2 de agosto de 2026.

## 1. Alcance

Se validó la fase SQLite del Taller #3 sobre una base temporal limpia, sin usar ni modificar la base `db.sqlite3` incluida en el ZIP de origen. No se ejecutó MySQL.

## 2. Revisión de `scripts/verify.ps1`

El script ya cubría manifiesto, auditoría, `check`, migraciones, seeds, comandos temporales, smoke, suite, static y `check --deploy`. Se amplió para:

- mostrar Python, Django, django-environ y `pip check`;
- usar un puerto de smoke configurable y menos propenso a colisiones;
- ejecutar una batería funcional explícita de los flujos agregados después de P-28;
- conservar después la suite completa como puerta obligatoria.

También se actualizó `verify.sh` con la misma cobertura.

## 3. Resultados ejecutados

| Validación | Comando | Resultado real |
|---|---|---|
| Python | `python --version` | Python 3.13.5 en el contenedor de auditoría |
| Django | import desde dependencias incluidas | Django 5.2.16 |
| django-environ | import | 0.14.0 |
| Check | `python manage.py check` | 0 problemas |
| Migraciones pendientes | `makemigrations --check --dry-run` | `No changes detected` |
| Migración limpia | `migrate --noinput` | todas aplicadas hasta `lottery.0011` |
| Baseline | dos ejecuciones | 3 roles y 2 versiones legales en ambas |
| Demo | dos ejecuciones | completado sin imprimir credenciales |
| Backfill | dos ejecuciones | 0 wallets nuevas después del seed |
| Solicitudes vencidas | dos ejecuciones | 0 pendientes en escenario limpio |
| Estados de eventos | dos ejecuciones | 0 cambios en escenario limpio |
| Schedules | dos ejecuciones | 0 duplicaciones en escenario limpio |
| Smoke | `SMOKE_PORT=8876` | HTTP 200 |
| Pruebas funcionales explícitas | módulos posteriores a P-28 | 218 pruebas, OK |
| Suite completa | `python manage.py test` | 458 pruebas, OK |
| Static | `findstatic` | CSS, JS y logo encontrados |
| Collectstatic | `collectstatic --clear` | 130 archivos copiados |

La suite completa se aceleró con un settings externo que sustituyó únicamente el hasher de contraseña. Ese archivo no forma parte del proyecto. Las reglas, vistas, modelos, servicios y base de datos probados fueron los del ZIP.

## 4. Flujos cubiertos por pruebas

- CRUD accounts, vendors y lottery.
- Login, logout, cambio de modo y aislamiento de permisos.
- Wallets, movimientos y operaciones financieras.
- Solicitudes Cliente–Vendedor y estados terminales.
- Compra de boleto, unicidad y rollback.
- Resultado manual, evaluación y acreditación.
- Series limitadas y sin límite.
- Pausa, reactivación, edición futura, archivo lógico y observabilidad.
- Resultado automático y repetición del comando.
- UX, accesibilidad, responsive y 403/404.

## 5. Evidencia manual pendiente

Las capturas visuales y la demostración interactiva deben producirse en el equipo del usuario. Se detallan en:

- `docs/CIERRE_SQLITE_CHECKLIST_CAPTURAS.md`;
- `docs/CIERRE_SQLITE_COMANDOS_EVIDENCIA.md`;
- `docs/DEMOSTRACION_SQLITE_10_15_MIN.md`.

No se fabricaron imágenes ni salidas.

## 6. Incidencias del ZIP recibido

- El ZIP recibido incluía `.venv`, `.env` y `db.sqlite3`; esos elementos no deben formar parte del ZIP final de entrega.
- El manifiesto esperaba la carpeta `docs/`, pero el ZIP no la contenía. Se restauró la documentación vigente coherente con el manifiesto y se añadieron los documentos de cierre SQLite.
- El primer smoke encontró el puerto 8765 ocupado por otro proceso de auditoría. Al liberar el puerto o usar 8876, respondió HTTP 200. No fue un fallo de la aplicación.

## 7. Veredicto

**Cierre técnico SQLite: aprobado en validación automatizada.**

Condiciones pendientes antes de presentar:

1. producir las capturas reales en Windows;
2. ejecutar `scripts/verify.ps1` en el equipo oficial y guardar su transcripción;
3. regenerar manifiesto después de cualquier cambio final;
4. crear el ZIP sin entorno, base local, `.env`, bytecode ni `staticfiles`;
5. auditar el ZIP final en modo paquete.

MySQL permanece pendiente y no se declara aprobado.
