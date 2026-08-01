# Inventario final y estado archivo por archivo

## 1. Alcance de este paquete

Este inventario corresponde a la fase actual del **Taller #3 de Lotería
Binaria con Django**. Deja completa y verificable la base SQLite, el usuario
personalizado, términos, autenticación, selector de modo, dashboards de
frontera, Bootstrap 5.3 y los scripts de comprobación.

No declara terminados los módulos de negocio `finance`, `vendors` y `lottery`.
Esos módulos permanecen deliberadamente vacíos hasta construirse uno por uno
con modelos, servicios, migraciones y pruebas reales.

## 2. Raíz y configuración

| Archivo | Función | Estado / control |
|---|---|---|
| `.env.example` | Variables de desarrollo, SQLite y ejemplo futuro MySQL | Sin secretos; demo password vacío |
| `.gitignore` | Excluye entorno, secretos, SQLite local, cache y collectstatic | Revisado |
| `requirements.txt` | Dependencias de fase SQLite | Sin driver PostgreSQL |
| `requirements-mysql.txt` | Extensión exclusiva para fase MySQL | No se instala en fase 1 |
| `manage.py` | Entrada estándar de Django | Sin lógica personalizada |
| `README.md` | Instalación, rutas, seed y puerta de salida | Correlacionado con scripts |
| `config/settings.py` | Apps, templates, static, seguridad y allowlist SQLite/MySQL | PostgreSQL bloqueado |
| `config/urls.py` | Integra admin, accounts y core | Todas las rutas usadas existen |
| `config/asgi.py` | Entrada ASGI estándar | Sin modificaciones de negocio |
| `config/wsgi.py` | Entrada WSGI estándar | Sin modificaciones de negocio |

## 3. App `accounts`

| Archivo | Función | Consumidor / prueba |
|---|---|---|
| `models.py` | `User`, `TermsVersion`, `TermsAcceptance` e inmutabilidad | forms, services, admin; pruebas de integridad |
| `roles.py` | Códigos, presentación y destino de cada modo | access, views, navbar |
| `access.py` | Roles asignados, modo activo válido y decorador de acceso | dashboards; pruebas de aislamiento |
| `forms.py` | Login, registro adulto, Bootstrap y selector de modo | views; pruebas de registro/auth |
| `services.py` | Registro atómico y revalidación legal | `RegistrationForm.save`; rollback probado por diseño |
| `views.py` | Login, logout POST, registro y selector por POST | `accounts/urls.py` |
| `urls.py` | Nombres de URL estables | templates y tests de reverse |
| `admin.py` | Usuario protegido, términos versionados, aceptaciones read-only | pruebas de permisos admin |
| `migrations/0001_initial.py` | Primera migración con usuario personalizado | No editar después de aplicada |
| `migrations/0002_*.py` | Ajuste ya existente de BigAutoField | No editar después de aplicada |
| `tests/factories.py` | Fábricas locales sin credenciales públicas | Suite accounts/core |
| `tests/test_registration.py` | Registro, edad, duplicados, CSRF, legal vigente, ARIA | 10 pruebas |
| `tests/test_auth_and_modes.py` | Login, multirrol, selector, 403, suspensión, logout | 10 pruebas |
| `tests/test_model_integrity.py` | Canonicalización e históricos inmutables, incluido QuerySet | 4 pruebas |
| `tests/test_admin.py` | Delete protegido y aceptación read-only | 3 pruebas |

## 4. App `core`

| Archivo | Función | Consumidor / prueba |
|---|---|---|
| `context_processors.py` | Navegación derivada del modo validado | `base.html`; tests de navegación |
| `views.py` | Landing y dashboards actualmente verificables | `core/urls.py` |
| `urls.py` | Home y tres paneles | reverse y navegación |
| `seed.py` | Roles y versiones legales idempotentes | dos management commands |
| `management/commands/seed_baseline.py` | Datos mínimos obligatorios | pruebas de idempotencia |
| `management/commands/seed_demo.py` | Usuarios locales opcionales con password por entorno | pruebas DEBUG/password/histórico |
| `tests/test_configuration.py` | SQLite, bloqueo PostgreSQL, rutas, static y backup | 6 pruebas |
| `tests/test_seed_commands.py` | Idempotencia y preservación histórica | 6 pruebas |
| `tests/test_views.py` | Home, permisos, navegación y privacidad admin | 9 pruebas |
| `models.py` | Frontera explícita sin modelo inventado | Deliberadamente vacío |
| `admin.py` | Frontera explícita sin registro falso | Deliberadamente vacío |

## 5. Apps reservadas

| App | Archivos actuales | Estado |
|---|---|---|
| `finance` | `apps.py`, `models.py`, `admin.py`, `migrations/__init__.py` | Frontera reservada; sin wallets/movimientos falsos |
| `vendors` | `apps.py`, `models.py`, `admin.py`, `migrations/__init__.py` | Frontera reservada; sin solicitudes falsas |
| `lottery` | `apps.py`, `models.py`, `admin.py`, `migrations/__init__.py` | Frontera reservada; sin eventos/boletos falsos |

No existen `views.py`, `urls.py`, `services.py` ni botones para funciones que
estos módulos todavía no implementan.

## 6. Templates

| Archivo | Función | Estado |
|---|---|---|
| `templates/base.html` | Bootstrap 5.3, navbar/offcanvas, logo, usuario, modo, footer | Base única y responsive |
| `templates/includes/_messages.html` | Messages Django con `aria-live` | Activo |
| `templates/includes/_confirm_modal.html` | Confirmación accesible de POST sensible | Activo vía `app.js` |
| `templates/core/home.html` | Landing y reglas Octal/Decimal/Hexadecimal | Sin datos falsos |
| `templates/accounts/login.html` | AuthenticationForm server-side | Sin credenciales demo |
| `templates/accounts/register.html` | Registro, errores y contenido legal vigente | CSRF y labels |
| `templates/accounts/choose_mode.html` | Tarjetas solo para roles asignados | POST validado |
| `templates/dashboards/client.html` | Frontera CLIENTE | Estado pendiente; no simula negocio |
| `templates/dashboards/vendor.html` | Frontera VENDEDOR | Sin compra de boletos ni acción falsa |
| `templates/dashboards/admin.html` | Módulos admin realmente disponibles | Conteos solo para staff |
| `templates/403.html` | Error de autorización | Un `h1` |
| `templates/404.html` | Ruta inexistente | Un `h1` |

## 7. Static

| Archivo | Función | Estado |
|---|---|---|
| `static/css/app.css` | Identidad azul/dorada, foco, 44 px, overflow | Complementa Bootstrap; no lo reemplaza |
| `static/js/app.js` | Modal de confirmación y foco al primer error | Solo UI; sin negocio ni almacenamiento |
| `static/img/logo-placeholder.png` | Copia exacta del logo del ZIP visual | Sin lógica |

## 8. Scripts y evidencia

| Archivo | Función | Estado |
|---|---|---|
| `scripts/audit_project.py` | Estructura, sintaxis, H1, CSRF, residuos y configuración | Ejecutado: OK |
| `scripts/verify.ps1` | SQLite temporal, check, migraciones, 48 tests, static | Requiere dependencias locales |
| `scripts/verify.sh` | Equivalente POSIX | Requiere dependencias locales |
| `evidencias/03_verificacion/auditoria_estatica.txt` | Salida del auditor | Generada |
| `evidencias/03_verificacion/compileall.txt` | Parseo/compilación Python | Generada |
| `evidencias/03_verificacion/javascript_sintaxis.txt` | `node --check` | Generada |
| `evidencias/03_verificacion/imports_ast.txt` | Imports posiblemente muertos | Sin hallazgos |
| `evidencias/03_verificacion/inventario_pruebas.txt` | Conteo por archivo | Total 48 |
| `evidencias/03_verificacion/LIMITACION_ENTORNO.md` | Límites honestos de la verificación | Vigente |

## 9. Documentación de control

| Archivo | Propósito |
|---|---|
| `DECISION_T3_001_SQLITE_MYSQL.md` | Resuelve el conflicto PostgreSQL vs Taller #3 |
| `CORRECCIONES_DOCUMENTACION_TALLER3.md` | Indica líneas/secciones a versionar y corregir |
| `INFORME_AUDITORIA_INTEGRAL.md` | Hallazgos, arreglos, nota y puerta de salida |
| `COMPARACION_GITHUB_COMMIT.md` | Diferencias contra el último commit observado |
| `MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md` | Regla → archivo → evidencia → estado |
| `MATRIZ_FUNCIONES_USO_PRUEBA.md` | Símbolo → consumidor → prueba |
| `ARCHIVOS_Y_RESPONSABILIDADES.md` | Resumen técnico por capa |
| `PLAN_MIGRACION_ZIP_TEMPLATES_STATIC.md` | Decisión archivo por archivo del frontend legado |
| `AUDITORIA_ZIP_TALLER3.md` | Inventario y problemas del ZIP visual |
| `MAPA_INTERFAZ.md` | Pantallas y destino Django |
| `PRUEBAS_RESPONSIVE.md` | Matriz 360/390/768/1024/1440 |
| `GUIA_APLICACION_CAMBIOS.md` | Cómo integrar el paquete sin perder trabajo |
| `PLAN_SIGUIENTE_TRABAJO.md` | Orden de desarrollo posterior |
| `docs/referencias/*` | Fuentes canónicas y docentes preservadas |

## 10. Respaldo y seed legado

| Archivo | Decisión |
|---|---|
| `respaldo_frontend/Proyecto_HerreraNietoCristhian_legacy.zip` | Preservado, no se ejecuta ni despliega |
| `respaldo_frontend/README.md` | Explica su carácter visual |
| `seed_data/legacy/README.md` | Documenta por qué los JSON no se importan |

## 11. Ausencias deliberadas

No faltan por accidente; se excluyen hasta su módulo:

- modelos financieros;
- servicios de recarga/conversión/transferencia;
- perfiles y solicitudes de vendedor;
- productos, eventos, boletos y resultados;
- CRUD accounts propio fuera de Django admin;
- MySQL activo;
- API REST, Celery, Redis, microservicios o pagos reales.

Agregar cualquiera de esas piezas exige una tarea separada, migración nueva,
pruebas y actualización de la matriz de trazabilidad.
