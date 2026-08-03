# Matriz archivo → función → consumidor → prueba

## Accounts

| Archivo / símbolo | Responsabilidad | Consumidor | Prueba asociada |
|---|---|---|---|
| `models.User` | identidad y estado | auth, admin, services | registro, login, admin |
| `models.TermsVersion` | versión legal | form, service, seed, admin | registro/seed/admin |
| `models.TermsAcceptance` | histórico protegido | service, seed demo, admin | registro/seed/admin |
| `forms.TallerAuthenticationForm` | login y estado | `AccountLoginView` | auth/modes |
| `forms.RegistrationForm` | validación registro | `register` | registration |
| `forms.ModeSelectionForm` | rol asignado | `choose_mode` | auth/modes |
| `services.age_cutoff` | mayoría de edad | form y service | minor rejected |
| `services.current_terms_version` | legal vigente | form y service | missing/superseded |
| `services.register_client` | alta atómica | `RegistrationForm.save` | registration |
| `access.assigned_mode_codes` | roles canónicos | login, selector, sesión | auth/modes |
| `access.get_valid_active_mode` | limpiar modo inválido | navbar, home, decorador | unassigned session |
| `access.active_mode_required` | aislamiento de ruta | tres dashboards | wrong dashboard 403 |
| `views.AccountLoginView` | iniciar sesión | URL login | single/multirole/status |
| `views.AccountLogoutView` | logout POST | URL logout | GET 405/POST redirect |
| `views.register` | flujo registro | URL register | registration/CSRF |
| `views.choose_mode` | cambio por POST | URL mode | selector/mode/status |

## Core

| Archivo / símbolo | Responsabilidad | Consumidor | Prueba asociada |
|---|---|---|---|
| `context_processors.navigation` | navbar backend | `base.html` | navegación por modo |
| `views.home` | landing pública | URL `/` | home public |
| `views.client_dashboard` | shell CLIENTE | URL client | auth/navigation |
| `views.vendor_dashboard` | shell VENDEDOR | URL vendor | no ticket purchase |
| `views.admin_dashboard` | shell ADMIN | URL admin dashboard | staff/non-staff modules |
| `seed.ensure_role_groups` | roles idempotentes | dos commands | seed tests |
| `seed.ensure_legal_versions` | baseline legal inmutable | dos commands | seed tests |
| `seed_baseline` | datos mínimos | instalación | idempotence/history |
| `seed_demo` | cuentas locales seguras | desarrollo opcional | password/debug/idempotence |

## Interfaz y scripts

| Archivo | Uso real | Validación |
|---|---|---|
| `templates/base.html` | layout, navbar, messages, modal | auditor + views |
| `_messages.html` | Django messages/aria-live | auditor/render |
| `_confirm_modal.html` | confirmación UI | `app.js` |
| `static/js/app.js` | confirmación/foco solamente | `node --check` |
| `static/css/app.css` | identidad/accesibilidad | findstatic/manual |
| `scripts/audit_project.py` | residuos y estructura | ejecución directa |
| `scripts/verify.*` | puerta limpia reproducible | ejecución local |

## Módulos reservados

`finance`, `vendors` y `lottery` solo contienen `AppConfig`, `models.py` y
`admin.py` explícitamente vacíos. No tienen rutas, vistas, servicios, botones
o datos falsos. Su presencia reserva la arquitectura canónica sin afirmar que
el negocio ya existe.
