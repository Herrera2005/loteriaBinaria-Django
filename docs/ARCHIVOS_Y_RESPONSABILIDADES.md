# Archivos y responsabilidades de la fase corregida

## Configuración

- `config/settings.py`: entorno, SQLite/MySQL, templates, static y seguridad.
- `config/urls.py`: admin, accounts y core.
- `requirements.txt`: dependencias de fase SQLite.
- `requirements-mysql.txt`: extensión exclusiva de fase MySQL.

## Accounts

- `models.py`: usuario, versiones legales y aceptaciones.
- `forms.py`: login, registro adulto y selector de modo.
- `services.py`: creación transaccional del cliente.
- `access.py`: autorización por rol asignado y modo activo.
- `views.py`: login, logout POST, registro y cambio de modo.
- `admin.py`: administración protegida y sin delete de usuarios/históricos.

## Core

- `views.py`: home y dashboards verificables.
- `context_processors.py`: navbar derivada del backend.
- `seed.py`: roles y términos idempotentes.
- `management/commands/`: comandos reproducibles.

## Interfaz

- `templates/base.html`: Bootstrap, cabecera, usuario, modo, mensajes y modal.
- `templates/accounts/*`: autenticación y modo.
- `templates/dashboards/*`: estados reales sin acciones no implementadas.
- `static/css/app.css`: identidad azul/dorada y accesibilidad complementaria.
- `static/js/app.js`: solo confirmación visual y foco.
- `static/img/logo-placeholder.png`: referencia visual del ZIP.

## Pruebas

- `apps/accounts/tests/`: registro, autenticación, modos y admin protegido.
- `apps/core/tests/`: rutas, navegación, seeds, settings y static.
- `scripts/audit_project.py`: residuos legado y estructura.
- `scripts/verify.ps1` / `verify.sh`: puerta de salida reproducible.
