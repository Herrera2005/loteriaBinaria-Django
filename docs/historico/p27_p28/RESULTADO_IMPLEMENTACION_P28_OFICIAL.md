# Resultado de implementación P-28 oficial

## Alcance cerrado

Se implementó únicamente el bloque visual y read-only solicitado:

- wallet propia;
- movimientos propios filtrables y paginados;
- auditoría administrativa list/detail;
- home con productos activos reales;
- dashboards Cliente, Vendedor y Administrador con datos del backend;
- pruebas de propiedad, permisos, paginación y métodos HTTP.

No se implementaron recargas, conversiones, compra mayorista, transferencia,
retiro ni compra de boletos.

## Decisiones de seguridad

- Las rutas de Finance no reciben un `user_id` ni un `wallet_id` para decidir
  propiedad. Siempre filtran por `request.user`.
- Agregar parámetros GET como `?user=<otro>` no cambia el propietario consultado.
- No existe ruta `/finance/wallets/<pk>/`; por tanto, cambiar un PK no expone
  wallets ajenas.
- Las vistas de auditoría requieren rol y modo activo ADMINISTRADOR.
- Cliente y Vendedor reciben 403 en auditoría.
- Todos los endpoints de P-28 son GET read-only; POST devuelve 405.
- Ninguna vista llama `ensure_user_wallets` ni crea datos durante GET.
- No se añadió `CreateView`, `UpdateView` ni `DeleteView` para Wallet, Movement
  o AuditEvent.

## Rutas

```text
/finance/wallets/
/finance/movements/
/audit/
/audit/<pk>/
```

## Interfaz

- Bootstrap 5.3 real.
- Base común con logo, aviso académico, usuario y modo activo.
- Cards de saldo inspiradas en el frontend legado.
- Tablas responsive, filtros, badges, estados vacíos y paginación.
- No se copiaron localStorage, JSON de negocio ni reglas antiguas.

## Observación importante sobre pruebas

El paquete P-28A no tenía `apps/finance/tests/__init__.py`. Por ello Django
reportaba 175 pruebas mientras el auditor estático detectaba 195 funciones de
prueba. P-28 agrega ese archivo para que las pruebas de Finance sean realmente
descubiertas, además de las pruebas nuevas de vistas.
