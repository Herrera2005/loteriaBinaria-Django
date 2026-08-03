# Guía de demostración SQLite — 10 a 15 minutos

## Preparación previa

1. Activar `.venv`.
2. Ejecutar `python manage.py migrate`, `seed_baseline` y `seed_demo`.
3. Ejecutar `python manage.py runserver`.
4. Tener abiertas tres sesiones o perfiles del navegador: Cliente, Vendedor y Administrador.
5. No mostrar contraseñas ni `.env` durante la exposición.

## Guion

### 0:00–1:00 — Arquitectura y alcance

- Mostrar landing.
- Explicar cinco apps Django y Bootstrap 5.3.
- Aclarar: fase actual SQLite; MySQL es la fase siguiente; PostgreSQL no aplica.

### 1:00–2:30 — Autenticación y modos

- Iniciar sesión con cuenta multirrol.
- Mostrar selector de modo.
- Cambiar mediante POST a CLIENTE y luego explicar aislamiento de permisos.

### 2:30–4:00 — CRUD evaluables

- Administrador: lista/detalle/edición de usuario.
- Mostrar perfil vendedor.
- Mostrar producto y evento de lotería.
- Señalar que desactivaciones y archivos sensibles son lógicos, no borrado destructivo.

### 4:00–5:30 — Finanzas

- En CLIENTE, mostrar wallets REAL/VIRTUAL y movimientos.
- Explicar recarga simulada 1:1 y conversión documentada.
- No editar saldos directamente.

### 5:30–7:00 — Solicitud Cliente–Vendedor

- Cliente crea solicitud y se reserva REAL.
- Vendedor abre solicitudes elegibles y toma una.
- Mostrar confirmación o historial de una solicitud completada.

### 7:00–8:30 — Compra de boleto

- Abrir evento comprable.
- Ingresar combinación válida.
- Confirmar compra y mostrar boleto.
- Explicar unicidad por evento y débito atómico VIRTUAL.

### 8:30–10:00 — Resultado manual

- Administrador abre evento permitido.
- Publicar resultado con motivo.
- Mostrar resultado público y boleto evaluado.
- Explicar resultado único, inmutable y premio idempotente.

### 10:00–12:30 — Series

- Mostrar una serie limitada y una sin límite.
- Señalar próxima generación, restantes, modo de resultado y `last_synced_at`.
- Pausar una serie y explicar que los eventos existentes no cambian.
- Mostrar archivo lógico y eventos relacionados.

### 12:30–13:30 — Resultado automático

En PowerShell:

```powershell
python manage.py process_lottery_schedules
python manage.py process_lottery_schedules
```

- Mostrar primera ejecución.
- Mostrar que la segunda no duplica eventos, resultados ni premios.

### 13:30–14:30 — Permisos y responsive

- Intentar una ruta incompatible y mostrar 403.
- Cambiar DevTools a 320 px y mostrar offcanvas, formulario y tabla responsive.

### 14:30–15:00 — Cierre técnico

Mostrar salida ya preparada de:

```text
System check identified no issues
No changes detected
Ran 458 tests
OK
```

Cerrar indicando que la puerta SQLite está lista y MySQL aún debe validarse por separado.
