# Matriz de trazabilidad vigente — P-36E, cierre y UX

**Estado:** vigente  
**Base verificada:** SQLite  
**Pruebas ejecutadas:** 458, OK  
**MySQL:** preparado, pendiente de ejecución en servidor real

| Requisito/flujo | Modelo principal | Servicio/política | Vista/URL | Template | Prueba principal | Evidencia vigente |
|---|---|---|---|---|---|---|
| Registro adulto y términos | `accounts.User`, `TermsVersion`, `TermsAcceptance` | `register_client()` | `accounts:register` | `accounts/register.html` | `test_registration.py`, `test_services.py` | usuario, wallets y aceptaciones creados atómicamente |
| Login/logout/cambio de contraseña | `accounts.User` | Django auth | `accounts:login`, `logout`, `password_change` | `accounts/login.html`, password templates | `test_auth.py`, `test_auth_and_modes.py` | sesión del servidor y logout POST |
| Roles y modo activo | Groups + sesión | `accounts.access`, políticas | `accounts:choose_mode`, dashboards | `choose_mode.html`, `dashboards/*` | `test_permissions.py`, `test_auth_and_modes.py` | no se activa un rol no asignado |
| Perfil propio y CRUD de usuarios | `accounts.User` | `delete_or_deactivate_user()` | `accounts:profile`, `user_*` | `accounts/profile_*`, `user_*` | `test_views.py`, `test_admin.py` | desactivación lógica cuando existe historia |
| Auditoría | `core.AuditEvent` | manager append-only | `core:audit_list`, `audit_detail` | `core/audit_*` | `core/test_models.py`, `test_closure_repairs.py` | `update/delete` masivos rechazados |
| Wallets y movimientos | `finance.Wallet`, `Movement` | `ensure_user_wallets()` | `finance:wallet_detail`, `movement_list` | `wallet_detail.html` | `finance/test_models.py`, `test_views.py` | saldos separados e histórico inmutable |
| Recarga y retiro cliente | `TopUp`, `Withdrawal` | `confirm_topup()`, `confirm_withdrawal()` | `finance:real_operations` | `real_operations.html` | `test_operations.py`, `test_views.py` | `operation_id`, locks y movimientos |
| Conversión VIRTUAL→REAL | `VirtualToRealConversion` | `convert_virtual_to_real()` | `finance:wallet_conversion` | `wallet_conversion.html` | `test_operations.py` | comisión del taller e idempotencia |
| Transferencia VIRTUAL | `VirtualTransfer` | `transfer_virtual()` | `finance:virtual_transfer` | `transfer_form.html` | `test_operations.py` | no autoenvío y wallets bloqueadas |
| Operaciones vendedor | `VendorInventoryPurchase` | servicios `confirm_vendor_*`, `purchase_vendor_inventory()` | rutas `finance:vendor_*` | templates `vendor_*` | `test_vendor_finance.py` | inventario 0,90→1,00 y modo VENDEDOR |
| Perfil vendedor | `vendors.VendorProfile` | `remove_or_deactivate_vendor_profile()` | `vendors:vendorprofile_*` | `vendorprofile_*` | `vendors/test_models.py`, `test_views.py` | archivo/desactivación con historia |
| Solicitud Cliente–Vendedor | `ConversionRequest`, `ConversionAssignment` | create/assign/complete/release/cancel/expire | `vendors:client_conversionrequest_*`, `conversionrequest_list` | `client_conversionrequest_*`, listados | `test_client_requests.py`, `test_vendor_assignment.py`, `test_vendor_settlement.py`, `test_request_closure.py` | reserva, asignación única, liquidación y expiración |
| Productos de lotería | `LotteryProduct` | `delete_lottery_product()` y validadores | `lottery:product_*` | `product_*` | `test_custom_products.py`, `test_crud.py`, `test_forms.py` | oficiales/personalizados y borrado controlado |
| Eventos manuales | `DrawEvent`, `DrawEventStatusTransition` | `transition_draw_event()`, `sync_lottery_event_states()` | `lottery:event_*`, `event_transition` | `event_*`, `event_transition_form.html` | `test_event_workflow.py`, `test_closure_repairs.py` | POST, transiciones válidas e historial inmutable |
| Catálogo y compra de boleto | `DrawEvent`, `Ticket`, `Wallet` | `purchase_ticket()` + política de modo | `lottery:client_event_*` | `client_event_list.html`, `client_event_detail.html` | `test_client_catalog.py`, `test_ticket_purchase.py`, `test_combination_availability.py` | compra atómica, combinación única y GET sin escrituras |
| Mis boletos | `Ticket` | queryset por propietario | `lottery:client_ticket_*` | `client_ticket_*` | `test_ticket_purchase.py`, `test_permissions.py` | aislamiento por usuario |
| Cancelación y reembolso | `DrawEvent`, `Ticket`, `Movement` | `transition_draw_event()`, `refund_cancelled_event_tickets()` | `lottery:event_transition` | `event_transition_form.html` | `test_event_workflow.py`, `test_result_publication.py` | reembolso una sola vez |
| Resultado manual | `DrawResult`, `Ticket` | `publish_draw_result()`, `settle_draw_result()` | `lottery:result_publish`, `public_result_detail` | `result_publish_form.html`, `public_result_detail.html` | `test_result_publication.py` | resultado único, inmutable y premios idempotentes |
| Resultado automático | `DrawEvent.result_mode`, `DrawResult` | `process_due_automatic_results()` | comando `process_lottery_schedules` | detalle/listados de evento | `test_automatic_results.py` | generación solo para eventos vencidos elegibles |
| Series de eventos | `DrawEventSeries`, `DrawEvent` | `generate_series_events()`, `process_active_event_series()` | `lottery:series_*` | `series_list/detail/form/archive` | `test_event_series.py`, `test_closure_repairs.py`, `test_unified_creation.py` | límite opcional, pausa, archivo y eventos históricos intactos |
| Observabilidad de series | `DrawEventSeries.last_synced_at` | sello externo + transacción de generación | detalle de serie y comando | `series_detail.html` | `test_event_series.py`, `test_closure_repairs.py` | registra intento real sin duplicar eventos |
| Unicidad portable de serie | `DrawEvent.series`, `series_sequence` | constraint de modelo | generación por servicio | no aplica | `test_closure_repairs.py` | migración `0011`, portable SQLite/MySQL |
| UX y accesibilidad | respuestas/templates | JS progresivo sin autoridad | todas las pantallas | `base.html`, includes y templates de apps | `core/test_ux_accessibility.py` | 320/375/768/1024/1440 documentados |
| Entrega reproducible | no aplica | scripts de verificación | no aplica | no aplica | auditoría/manifiesto | ZIP sin entorno, base, secretos o bytecode |

## Estado por motor

- **SQLite:** `check` OK, migraciones sin cambios pendientes y 458 pruebas OK.
- **MySQL:** settings, requisitos, migración portable y scripts preparados. Falta ejecutar la puerta en un servidor real.
- **PostgreSQL:** fuera de alcance del Taller #3.
