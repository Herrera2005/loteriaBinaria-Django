# Plan siguiente desde P-27

## Primero: cerrar P-27

1. Mantener la rama actual y crear un respaldo antes de sustituir archivos.
2. Instalar dependencias de `requirements.txt` en el entorno virtual.
3. Ejecutar `scripts/verify.ps1` sobre SQLite limpia.
4. Corregir cualquier fallo real sin saltar pruebas ni usar `--fake`.
5. Probar manualmente Accounts, Vendors y Lottery.
6. Verificar responsive en 360, 390, 768, 1024 y 1440 px.
7. Guardar capturas y salida de consola.
8. Hacer commit de cierre P-27.

## Después: P-28, no P-29 todavía

Implementar únicamente consultas seguras de Finance/Core:

1. revisar modelos reales de `finance` y `core`;
2. wallet propia y movimientos paginados en solo lectura;
3. auditoría administrativa en solo lectura;
4. ninguna edición directa de balance;
5. recargas/conversiones simuladas solo por POST y servicio transaccional;
6. pruebas de propiedad y permisos;
7. ejecutar `python manage.py test apps.finance apps.core`.

## Orden obligatorio para reglas sensibles

1. modelos portables y migraciones;
2. formularios/validadores;
3. servicios con `transaction.atomic`;
4. pruebas de éxito, rechazo y rollback;
5. vistas y URLs;
6. templates Bootstrap;
7. prueba manual y responsive;
8. actualización de matriz.

No crear botones, saldos, timers ni compra de boletos sin backend persistente.
