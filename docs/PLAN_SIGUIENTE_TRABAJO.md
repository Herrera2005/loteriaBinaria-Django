# Orden de trabajo posterior

## Estado que debe cerrarse primero

1. Aplicar este paquete a una rama nueva.
2. Instalar dependencias SQLite.
3. Ejecutar `scripts/verify.ps1`.
4. Probar manualmente las ocho rutas.
5. Guardar evidencias.
6. Recalificar la fase.

## Después

Continuar exactamente con el siguiente bloque del manual intercalado. Cada
respuesta debe abordar un solo módulo y entregar sus modelos/forms/services o
sus views/templates/tests, no todo el sistema a la vez.

## Orden funcional obligatorio para negocio sensible

1. modelos portables y migraciones;
2. forms/validadores;
3. services con `transaction.atomic`;
4. pruebas de éxito, rechazo y rollback;
5. views/URLs;
6. templates;
7. prueba manual y responsive;
8. actualizar matriz.

No crear primero botones, saldos ni timers sin backend.
