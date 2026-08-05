# Guía paso a paso para cerrar P-27 y continuar

## A. Aplicar el paquete auditado

1. Guarda una copia de tu carpeta y confirma la rama:

```powershell
git branch --show-current
git status
```

2. Sustituye solo los archivos del paquete corregido.
3. No copies `.env`, `db.sqlite3`, `.venv` ni `staticfiles`.
4. Revisa el cambio:

```powershell
git diff --stat
git diff -- apps/lottery apps/vendors apps/accounts templates scripts README.md docs
```

## B. Preparar SQLite limpia

```powershell
.\.venv\Scripts\Activate.ps1
python --version
python -m pip install -r requirements.txt
Copy-Item .env.example .env -ErrorAction SilentlyContinue
```

No configures MySQL todavía.

## C. Auditoría rápida antes de Django

```powershell
python scripts/audit_project.py
python -m compileall -q -f apps config scripts manage.py
```

La auditoría debe terminar en:

```text
AUDITORÍA ESTÁTICA P-27: OK
```

## D. Verificación completa automatizada

Ejecuta:

```powershell
.\scripts\verify.ps1
```

El script usa `verification.sqlite3`, no tu base cotidiana. Debe completar:

1. auditoría estática;
2. `manage.py check`;
3. migraciones sin cambios pendientes;
4. migración desde cero;
5. baseline idempotente;
6. smoke test de `runserver`;
7. suite completa;
8. `findstatic` y `collectstatic`.

Guarda la salida completa como evidencia.

## E. Diagnóstico por módulo cuando falle algo

```powershell
python manage.py test apps.accounts -v 2
python manage.py test apps.core -v 2
python manage.py test apps.vendors -v 2
python manage.py test apps.lottery -v 2
```

Para P-27 específicamente:

```powershell
python manage.py test apps.lottery.tests.test_models -v 2
python manage.py test apps.lottery.tests.test_forms -v 2
python manage.py test apps.lottery.tests.test_crud -v 2
```

No edites una prueba solo para ocultar un fallo real. Primero determina si el
problema está en regla, vista, template o expectativa incorrecta.

## F. Prueba manual Accounts

Con modo ADMINISTRADOR:

1. abre `/accounts/users/`;
2. prueba búsqueda y paginación;
3. crea un usuario y verifica contraseña hasheada desde el flujo;
4. edita campos permitidos;
5. elimina un usuario sin historia;
6. intenta eliminar uno con aceptación de términos y confirma desactivación;
7. confirma que no puedes eliminar tu propia cuenta activa.

## G. Prueba manual Vendors

1. abre `/vendors/`;
2. crea un perfil para un usuario con rol VENDEDOR;
3. filtra por estado;
4. abre el detalle y confirma que muestra datos del perfil, no solicitudes;
5. edita el estado;
6. elimina un perfil sin historia;
7. crea/asocia historia de asignación y confirma desactivación lógica;
8. abre `/vendors/requests/` y confirma que no hay editar/eliminar solicitud.

## H. Prueba manual Lottery P-27

### Productos

1. crea Octal: `01234567`, cardinalidad `4`;
2. crea Decimal: `0123456789`, cardinalidad `5`;
3. crea Hexadecimal: `0123456789ABCDEF`, cardinalidad `6`;
4. intenta Hexadecimal con `4`: debe fallar;
5. prueba búsqueda y filtro activo/inactivo;
6. crea un evento asociado y confirma que el producto ya no puede eliminarse;
7. confirma que código, símbolos y cardinalidad quedan protegidos.

### Eventos

1. crea un evento Borrador;
2. verifica que `sales_close_at = draw_at - 10 minutos`;
3. edita nombre, producto, fechas y montos mientras siga en Borrador;
4. cambia o simula el estado Publicado;
5. vuelve a editar: producto, apertura, sorteo, precio, premio y estado deben
   permanecer bloqueados;
6. intenta manipular esos valores desde el POST: deben conservarse;
7. elimina un Borrador sin historia: permitido;
8. intenta eliminar Publicado: bloqueado;
9. intenta eliminar con Ticket: bloqueado;
10. intenta eliminar con DrawResult: bloqueado;
11. confirma que no existe acción de compra de boleto.

## I. Responsive obligatorio

En DevTools prueba cada pantalla principal en:

```text
360 px
390 px
768 px
1024 px
1440 px
```

Comprueba:

- navbar/offcanvas operable;
- logo y nombre sin solaparse;
- botones alcanzables y con tamaño táctil;
- formularios sin desbordamiento;
- tablas dentro de `table-responsive`;
- cards apiladas correctamente;
- modal de confirmación visible;
- un solo `h1`;
- sin scroll horizontal global.

Guarda al menos una captura móvil, una tablet y una escritorio por CRUD.

## J. Cerrar P-27 en Git

Cuando todo esté verde:

```powershell
git status
git add .
git status
git commit -m "Cierra P-27 CRUD Lottery y auditoria integral"
git push origin feature/taller3-fase-1-esqueleto-sqlite
```

Antes del commit verifica que no se incluyan:

```text
.env
db.sqlite3
verification.sqlite3
.venv/
__pycache__/
*.pyc
staticfiles/
```

## K. Siguiente paso: P-28

Adjunta los archivos reales de `apps/finance` y `apps/core` y solicita solo
P-28. El objetivo inmediato es:

- wallet propia read-only;
- movimientos paginados read-only;
- auditoría administrativa read-only;
- permisos de propiedad y modo;
- ninguna edición genérica de balance;
- operaciones simuladas únicamente mediante POST y servicios
  transaccionales.

Después de P-28 corresponde P-29 para navegación completa; después P-30 para
la auditoría final de los tres CRUD.
