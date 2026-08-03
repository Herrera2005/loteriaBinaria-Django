# Siguiente trabajo autorizado

El desarrollo funcional previsto en SQLite está documentado hasta P-36E, cierre y UX/accesibilidad. El siguiente trabajo permitido es de validación y entrega:

1. ejecutar `scripts/verify.ps1` en una copia limpia;
2. regenerar y verificar `MANIFEST_SHA256.txt`;
3. crear una base MySQL 8 vacía con `utf8mb4`;
4. instalar `requirements-mysql.txt`;
5. ejecutar `scripts/verify_mysql.ps1`;
6. repetir en MySQL las pruebas críticas de concurrencia de compras, solicitudes, resultados y series;
7. generar el ZIP definitivo sin entorno, base ni secretos;
8. descomprimir el ZIP en otra carpeta y repetir auditoría, manifiesto y suite.

No corresponde crear PostgreSQL, API REST, Celery, Redis, microservicios ni nuevas funciones de negocio dentro de esta puerta.
