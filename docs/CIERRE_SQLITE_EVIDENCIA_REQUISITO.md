# Matriz evidencia → requisito del Taller #3

| Requisito o flujo | Evidencia automatizada | Evidencia manual sugerida | Resultado actual |
|---|---|---|---|
| Entorno y dependencias | Python, Django y `pip check` en `verify.ps1` | `01_entorno_python_django.png` | Ejecutado en auditoría aislada; captura local pendiente |
| `manage.py check` | `System check identified no issues` | `02_check_migraciones_pendientes.png` | OK ejecutado |
| Sin migraciones pendientes | `No changes detected` | `02_check_migraciones_pendientes.png` | OK ejecutado |
| Migración SQLite limpia | `migrate` hasta `lottery.0011` | `03_migracion_limpia_0011.png` | OK ejecutado |
| Seeds idempotentes | seed baseline/demo dos veces | `04_seeds_primera_segunda_ejecucion.png` | OK ejecutado |
| Runserver | `scripts/smoke_runserver.py` HTTP 200 | `05_smoke_runserver_http200.png` | OK ejecutado tras usar puerto libre |
| Suite completa | `python manage.py test` | `06_suite_458_ok.png` | 458 pruebas, OK |
| Static | `findstatic` y `collectstatic` | `07_static_find_collect.png` | 3 recursos encontrados; 130 copiados |
| CRUD accounts | `accounts.tests.test_views` | `13_crud_accounts_lista_detalle_edicion.png` | Automatizado OK; captura pendiente |
| CRUD vendors | `vendors.tests.test_views` | `14_crud_vendors_lista_detalle_edicion.png` | Automatizado OK; captura pendiente |
| CRUD lottery | `lottery.tests.test_crud` | `15_crud_lottery_productos_eventos.png` | Automatizado OK; captura pendiente |
| Login/logout/modos | `test_auth`, `test_auth_and_modes` | `08_login.png`, `09_selector_modo.png` | Automatizado OK |
| Wallets/movimientos | finance models, operations y views | `16_wallets_movimientos.png` | Automatizado OK |
| Solicitud Cliente–Vendedor | client requests, assignment, settlement, closure | `17`–`19` | Automatizado OK |
| Compra de boleto | `test_ticket_purchase` | `20_compra_boleto.png`, `21_boleto_comprobante.png` | Automatizado OK |
| Resultado manual | `test_result_publication` | `22_resultado_manual.png` | Automatizado OK |
| Serie limitada/sin límite | `test_event_series` | `23`, `24` | Automatizado OK |
| Pausa/edición futura/archivo | `test_event_series`, `test_closure_repairs` | `25`–`27` | Automatizado OK |
| Resultado automático | `test_automatic_results` | `28`, `29` | Automatizado OK |
| Idempotencia comandos | comandos ejecutados dos veces y pruebas de servicios | salida de consola | OK en escenario limpio |
| Responsive/accesibilidad | `test_ux_accessibility` | `31`–`35` | Automatizado OK; inspección visual pendiente |
| Permisos | matrices de permisos y tests por app | `30_permisos_403.png` | Automatizado OK |
| Auditoría/manifiesto | `manifest_project.py`, `audit_project.py` | `36_auditoria_manifiesto_ok.png` | Requiere regeneración después de estos documentos |
| MySQL fase 2 | No corresponde al cierre SQLite | ninguna todavía | Pendiente y fuera de esta fase |
