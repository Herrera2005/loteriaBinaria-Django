# Índice y autoridad de documentación

## 1. Orden de autoridad del Taller #3

1. Enunciado del Taller #3.
2. Decisiones vigentes específicas del taller en `docs/`.
3. Código, migraciones y pruebas ejecutables del ZIP actual.
4. Guía docente y manual intercalado.
5. Documentos originales de `docs/referencias/`, interpretados mediante las decisiones del Taller #3.
6. Frontend legado, únicamente como referencia visual.

Cuando un documento histórico contradiga el código actual o una decisión vigente, manda el estado ejecutable actual y debe registrarse la discrepancia.

## 2. Documentos vigentes y canónicos operativos

| Documento | Función |
|---|---|
| `README.md` | entrada principal, instalación, alcance, comandos y estado actual |
| `docs/INDICE_DOCUMENTACION.md` | clasificación y autoridad documental |
| `docs/DECISION_T3_001_SQLITE_MYSQL.md` | SQLite fase 1, MySQL fase 2 y exclusión de PostgreSQL |
| `docs/DECISION_P32B_CUENTAS_ROLES_PERFILES.md` | relación vigente entre cuenta, Groups, modo y perfil vendedor |
| `docs/MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md` | requisito → implementación → interfaz → prueba → evidencia |
| `docs/INVENTARIO_FINAL.md` | inventario técnico del árbol actual |
| `docs/ARCHIVOS_Y_RESPONSABILIDADES.md` | responsabilidad de módulos y archivos clave |
| `docs/MAPA_INTERFAZ.md` | arquitectura de información y navegación |
| `docs/MATRIZ_CRUD.md` | CRUD evaluables y controles |
| `docs/PRUEBAS_RESPONSIVE.md` | matriz UX/accesibilidad por ancho |
| `docs/REPARACION_HALLAZGOS_CIERRE.md` | reparaciones de auditoría autorizadas |
| `docs/RESULTADO_AUDITORIA_FINAL.md` | evidencia ejecutada y límites conocidos |
| `docs/PLAN_SIGUIENTE_TRABAJO.md` | única continuación autorizada: validación MySQL y entrega |
| `docs/ACTUALIZACION_DOCUMENTAL_P36E.md` | resumen de actualización documental y evidencia ejecutada |
| `docs/REPORTE_FINAL_SQLITE.md` | resultado ejecutado de la puerta SQLite limpia |
| `docs/CIERRE_SQLITE_EVIDENCIA_REQUISITO.md` | evidencia automatizada/manual vinculada con requisitos del taller |
| `docs/CIERRE_SQLITE_CHECKLIST_CAPTURAS.md` | lista de capturas reales que debe producir el estudiante |
| `docs/CIERRE_SQLITE_COMANDOS_EVIDENCIA.md` | comandos PowerShell para generar las evidencias |
| `docs/DEMOSTRACION_SQLITE_10_15_MIN.md` | guion de exposición funcional de 10–15 minutos |

## 3. Evidencia vigente de implementación

Estos documentos describen bloques ya implementados y sirven como evidencia, pero no definen por sí solos el estado global:

- `AUDITORIA_REPARACION_P36_VISUAL.md`
- `IMPLEMENTACION_P33R_REORGANIZACION_FINANCE.md`
- `IMPLEMENTACION_P33_FINANZAS_CLIENTE.md`
- `IMPLEMENTACION_P34A_SOLICITUD_REAL_VIRTUAL.md`
- `VERIFICACION_RUNSERVER.md`

Las frases de alcance parcial dentro de esos documentos deben leerse en la fecha/fase indicada, no como limitaciones actuales.

## 4. Documentos históricos o de planificación

Se conservan para trazabilidad y no describen el estado ejecutable vigente:

- `AUDITORIA_ZIP_TALLER3.md`
- `COMPARACION_GITHUB_COMMIT.md`
- `CORRECCIONES_DOCUMENTACION_TALLER3.md`
- `GUIA_APLICACION_CAMBIOS.md`
- `PLAN_MIGRACION_ZIP_TEMPLATES_STATIC.md`
- todo `docs/historico/p27_p28/`

## 5. Referencias originales

`docs/referencias/` contiene los cinco documentos originales del MVP y la guía docente. Se conservan sin reescribir su contenido. Sus menciones a PostgreSQL no aplican operativamente al Taller #3; la decisión `DECISION_T3_001_SQLITE_MYSQL.md` establece SQLite → MySQL.

## 6. Regla de actualización

Cuando cambie código productivo se debe actualizar, como mínimo:

1. README si cambia alcance, instalación o comandos;
2. matriz de trazabilidad;
3. inventario y responsabilidades si cambian archivos;
4. pruebas/evidencia correspondiente;
5. manifiesto SHA-256 al cerrar la entrega.

Los conteos de pruebas solo pueden publicarse a partir de una ejecución real y deben incluir fecha, comando y resultado.
