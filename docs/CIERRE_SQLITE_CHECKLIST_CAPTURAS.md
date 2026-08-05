# Checklist de capturas — cierre demostrable SQLite

Fecha de preparación: 2 de agosto de 2026.

Las capturas deben producirse en el equipo Windows del estudiante. Este documento no contiene capturas fabricadas.

## Convención

Guardar en `evidencias/04_cierre_sqlite/` usando PNG. No incluir contraseñas, `.env`, hashes, documentos personales completos ni saldos que no sean de demo.

| Nº | Nombre sugerido | Pantalla o consola | Qué debe verse | Estado |
|---:|---|---|---|---|
| 01 | `01_entorno_python_django.png` | PowerShell | `python --version`, Django 5.2.16 y `pip check` sin errores | Pendiente de captura |
| 02 | `02_check_migraciones_pendientes.png` | PowerShell | `check` sin problemas y `No changes detected` | Pendiente de captura |
| 03 | `03_migracion_limpia_0011.png` | PowerShell | migración limpia hasta `lottery.0011_portable_series_sequence_unique` | Pendiente de captura |
| 04 | `04_seeds_primera_segunda_ejecucion.png` | PowerShell | baseline/demo ejecutados dos veces sin duplicaciones | Pendiente de captura |
| 05 | `05_smoke_runserver_http200.png` | PowerShell + navegador | smoke HTTP 200 y landing abierta | Pendiente de captura |
| 06 | `06_suite_458_ok.png` | PowerShell | `Ran 458 tests` y `OK` | Pendiente de captura |
| 07 | `07_static_find_collect.png` | PowerShell | tres static encontrados y `130 static files copied` | Pendiente de captura |
| 08 | `08_login.png` | Navegador | formulario de ingreso, CSRF y aviso académico | Pendiente de captura |
| 09 | `09_selector_modo.png` | Navegador | modos permitidos para una cuenta multirrol | Pendiente de captura |
| 10 | `10_dashboard_cliente.png` | Navegador | saldo, sorteos, boletos y solicitudes | Pendiente de captura |
| 11 | `11_dashboard_vendedor.png` | Navegador | inventario, solicitudes y actividad | Pendiente de captura |
| 12 | `12_dashboard_administrador.png` | Navegador | accesos CRUD, eventos, series y auditoría | Pendiente de captura |
| 13 | `13_crud_accounts_lista_detalle_edicion.png` | Navegador | lista de usuarios y formulario permitido | Pendiente de captura |
| 14 | `14_crud_vendors_lista_detalle_edicion.png` | Navegador | perfiles vendedores y desactivación lógica | Pendiente de captura |
| 15 | `15_crud_lottery_productos_eventos.png` | Navegador | productos y eventos persistidos | Pendiente de captura |
| 16 | `16_wallets_movimientos.png` | Navegador | REAL/VIRTUAL y movimientos correlacionados | Pendiente de captura |
| 17 | `17_solicitud_cliente.png` | Navegador | solicitud creada, monto reservado y estado | Pendiente de captura |
| 18 | `18_asignacion_vendedor.png` | Navegador | solicitud elegible/asignada al vendedor | Pendiente de captura |
| 19 | `19_solicitud_completada.png` | Navegador | estado terminal y movimientos resultantes | Pendiente de captura |
| 20 | `20_compra_boleto.png` | Navegador | evento, combinación canónica y confirmación | Pendiente de captura |
| 21 | `21_boleto_comprobante.png` | Navegador | boleto persistido y precio guardado | Pendiente de captura |
| 22 | `22_resultado_manual.png` | Navegador | resultado único, motivo y estado final | Pendiente de captura |
| 23 | `23_serie_limitada.png` | Navegador | límite, restantes, próximo evento y sincronización | Pendiente de captura |
| 24 | `24_serie_sin_limite.png` | Navegador | texto `Sin límite` y eventos relacionados | Pendiente de captura |
| 25 | `25_serie_pausada.png` | Navegador | estado pausado y mensaje de no modificación histórica | Pendiente de captura |
| 26 | `26_serie_editada_evento_historico.png` | Navegador | parámetros nuevos y evento anterior sin cambios | Pendiente de captura |
| 27 | `27_serie_archivada.png` | Navegador | archivo lógico y eventos históricos visibles | Pendiente de captura |
| 28 | `28_resultado_automatico_comando.png` | PowerShell + navegador | comando procesa un resultado automático | Pendiente de captura |
| 29 | `29_resultado_automatico_segunda_ejecucion.png` | PowerShell | segunda ejecución sin resultado/premio duplicado | Pendiente de captura |
| 30 | `30_permisos_403.png` | Navegador | modo incompatible recibe 403 con recuperación segura | Pendiente de captura |
| 31 | `31_responsive_320.png` | DevTools | pantalla clave a 320 px sin scroll horizontal de página | Pendiente de captura |
| 32 | `32_responsive_375.png` | DevTools | pantalla clave a 375 px | Pendiente de captura |
| 33 | `33_responsive_768.png` | DevTools | pantalla clave a 768 px | Pendiente de captura |
| 34 | `34_responsive_1024.png` | DevTools | pantalla clave a 1024 px | Pendiente de captura |
| 35 | `35_responsive_1440.png` | DevTools | pantalla clave a 1440 px | Pendiente de captura |
| 36 | `36_auditoria_manifiesto_ok.png` | PowerShell | manifiesto y auditoría estática en OK | Pendiente de captura |

## Criterios de calidad de la evidencia

- Mostrar comando completo y salida final, sin recortar el mensaje de éxito o error.
- No editar imágenes para alterar resultados.
- En capturas de navegador, mostrar la URL y el modo activo cuando sea pertinente.
- Para demostrar idempotencia, capturar primera y segunda ejecución o una salida conjunta legible.
- Para edición futura de series, conservar una captura previa del evento histórico y otra posterior.
