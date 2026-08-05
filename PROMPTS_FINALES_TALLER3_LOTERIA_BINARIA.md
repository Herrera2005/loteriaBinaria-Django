# Prompts finales — Taller #3 Lotería Binaria con Django

## Estado real de la base revisada

Estos prompts fueron preparados tras revisar el ZIP actual del proyecto. La base contiene:

- Django con las apps `accounts`, `core`, `finance`, `vendors` y `lottery`.
- SQLite como fase actual y configuración permitida únicamente para SQLite/MySQL.
- Migraciones de Lottery hasta `0009_automatic_results.py`.
- Productos oficiales y personalizados, colores, filtros, compra de boletos, resultados manuales, series editables y resultados automáticos.
- `DrawEventSeries` con límite opcional, archivo lógico, pausa, recurrencia, próximo sorteo, modo de resultado manual/automático y eventos relacionados.
- El detalle de serie ya lista los eventos generados y enlaza a su detalle.
- Falta un registro real de `last_synced_at` y un cierre visual/documental exacto de los estados pausada/completada/archivada.
- `scripts/verify.ps1` valida una base SQLite limpia, pero todavía no existe una verificación equivalente completa para MySQL.
- `README.md` y varios documentos aún describen estados antiguos alrededor de P-28 y deben actualizarse.
- El ZIP revisado contiene carpetas `__pycache__` y archivos `.pyc`; están ignorados por Git, pero deben excluirse de la entrega final.

---

# Reglas maestras que deben acompañar todos los prompts

Copia este bloque al inicio de cada prompt cuando trabajes en otro chat:

```text
RECORDATORIO OBLIGATORIO PARA ESTA RESPUESTA:

- Este es el Taller #3 “Lotería Binaria con Django”, no el proyecto empresarial ni el monorepo NestJS.
- Trabaja exclusivamente sobre el ZIP actual que adjunto en este mensaje. Antes de diagnosticar o escribir código, descomprímelo y revisa los archivos reales.
- No afirmes que un archivo, clase, función, URL, campo, migración o prueba existe sin haberlo encontrado en el ZIP actual.
- No uses recuerdos de versiones anteriores como fuente de verdad. Si el ZIP contradice el historial del chat, manda el ZIP actual.
- Orden de autoridad: enunciado del Taller #3; documentos canónicos vigentes en `docs/`; decisiones actuales del proyecto; guía docente VideoClub; `respaldo_frontend/` solo como referencia visual.
- Primera fase SQLite; segunda fase MySQL. No usar PostgreSQL.
- Mantener Bootstrap 5.3 real. El CSS propio solo complementa la identidad azul oscuro/dorada y los colores funcionales.
- No usar JSON, localStorage, sessionStorage ni datos del navegador como fuente de verdad.
- No editar `manage.py` salvo una razón extraordinaria, demostrada y explicada.
- No crear Celery, Redis, API REST, microservicios ni dependencias fuera del alcance.
- No debilitar reglas de inmutabilidad, permisos, transiciones de estado, idempotencia o trazabilidad para hacer pasar pruebas.
- Las operaciones sensibles deben permanecer en servicios transaccionales y acciones POST con CSRF.
- No generar todo el proyecto de nuevo. Conservar lo que ya funciona y modificar únicamente lo necesario.
- Antes de cambiar pruebas, determina si el fallo está en producción o si la prueba intenta saltarse una regla válida.
- Revisa modelos, formularios, servicios, vistas, URLs, templates, comandos, migraciones, pruebas y documentación relacionados antes de proponer cambios.
- Si falta información, dilo. No inventes resultados de pruebas que no hayas ejecutado.

FORMATO OBLIGATORIO DE RESPUESTA:
1. Archivos revisados realmente.
2. Diagnóstico sustentado con rutas, clases y funciones existentes.
3. Riesgos y reglas que deben conservarse.
4. Lista exacta de archivos a crear/modificar/eliminar.
5. Código completo solo de los archivos solicitados o un ZIP parche aplicado sobre la base actual.
6. Migraciones necesarias y por qué.
7. Comandos PowerShell en orden.
8. Pruebas automatizadas nuevas y de regresión.
9. Prueba manual paso a paso.
10. Resultado esperado y criterio objetivo para continuar.
11. Limitaciones: qué no se pudo ejecutar o comprobar.
```

---

# PROMPT 1 — P-36E: observabilidad y cierre de series automáticas

```text
[PEGAR AQUÍ EL BLOQUE DE REGLAS MAESTRAS]

Adjunto el ZIP actual completo del Taller #3. Implementa únicamente P-36E: observabilidad y cierre final de series automáticas.

Primero revisa, como mínimo:
- `apps/lottery/models.py`
- `apps/lottery/services.py`
- `apps/lottery/forms.py`
- `apps/lottery/views.py`
- `apps/lottery/urls.py`
- `apps/lottery/admin.py`
- `apps/lottery/management/commands/process_lottery_schedules.py`
- `templates/lottery/series_detail.html`
- `templates/lottery/series_list.html`
- `templates/lottery/series_form.html`
- `templates/lottery/event_detail.html`
- `apps/lottery/tests/test_event_series.py`
- `apps/lottery/tests/test_automatic_results.py`
- todas las migraciones de `apps/lottery/migrations/`

Estado esperado que debes confirmar en los archivos, no asumir:
- la serie ya tiene pausa, archivo lógico, límite opcional, `next_draw_at`, `remaining_occurrences`, `result_mode` y eventos relacionados;
- los eventos generados no se reescriben al editar la serie;
- el detalle ya enlaza a los eventos generados;
- falta registrar una última sincronización real independiente de `updated_at`.

Tareas:
1. Agrega a `DrawEventSeries` un campo nullable `last_synced_at` con nombre legible “última sincronización”. Usa la siguiente migración disponible después de revisar la secuencia real; no fuerces un número inventado.
2. Define con precisión qué significa sincronización: cada intento real de procesar una serie mediante el servicio de generación, aunque cree cero eventos, siempre que la serie exista. Decide y documenta si series archivadas o pausadas actualizan el campo; la decisión debe ser coherente y estar probada.
3. Actualiza el campo dentro del servicio transaccional correcto, no desde el template ni desde JavaScript.
4. Evita que el registro de sincronización rompa la idempotencia o genere carreras. Conserva `select_for_update()` y las restricciones existentes.
5. Muestra en el detalle:
   - Última sincronización o “Todavía no sincronizada”.
   - Próximo evento por generar.
   - Generaciones restantes o “Sin límite”.
   - Resultado manual/automático.
   - Estado exacto: Activa, Pausada, Completada o Archivada/Eliminada según la terminología vigente que encuentres.
6. Ajusta los mensajes para que sean claros y consistentes:
   - “Serie completada. No se generarán más sorteos.”
   - “La programación está pausada. Los eventos existentes no se modifican.”
   - “La programación fue archivada y no generará nuevos eventos.”
7. Conserva la tabla de eventos relacionados y sus enlaces. Mejora la etiqueta visual de estado sin cambiar reglas.
8. Mantén la protección: editar una serie afecta únicamente generaciones todavía no creadas. Añade o refuerza una prueba que compare los campos históricos de eventos ya generados antes y después de editar frecuencia, próxima fecha, precio, premio y anticipación.
9. Añade pruebas para `last_synced_at`:
   - empieza en `None`;
   - se completa al sincronizar;
   - cambia o no cambia en una segunda ejecución según la semántica documentada;
   - no duplica eventos;
   - no altera eventos históricos;
   - se muestra correctamente en el detalle.
10. Actualiza la documentación de P-36E y la matriz de trazabilidad vigente.

No implementes MySQL ni nuevas funciones de negocio en esta tarea.

Entrega un ZIP de parche, un diff y una guía de aplicación. Ejecuta, si el entorno lo permite:
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- pruebas específicas de series y resultados automáticos
- `python manage.py test apps.lottery -v 2`
- `python scripts/audit_project.py`

No declares “todo aprobado” si no pudiste ejecutar Django.
```

---

# PROMPT 2 — Auditoría integral sin modificar código

```text
[PEGAR AQUÍ EL BLOQUE DE REGLAS MAESTRAS]

Adjunto el ZIP actual completo. Realiza una auditoría integral de cierre, pero en esta respuesta NO modifiques código ni generes un parche. Primero diagnostica.

Revisa todo el árbol del proyecto, incluidos:
- cinco apps Django;
- `config/`;
- migraciones;
- comandos de management;
- templates;
- static;
- scripts;
- seeds;
- documentación;
- requisitos SQLite/MySQL;
- `.env.example`, `.gitignore` y manifiesto.

Audita estas categorías:
1. Errores de sintaxis Python y templates Django.
2. Imports, métodos, clases, propiedades, URLs, templates y funciones aparentemente muertas o duplicadas.
3. Nombres de URL sin `reverse`, enlaces `{% url %}` rotos y rutas sin pruebas.
4. Formularios que exponen campos sensibles o duplican validación del modelo/servicio.
5. Acciones GET que modifican datos; POST sin CSRF; permisos ausentes.
6. Reglas de inmutabilidad y transiciones de estado de productos, eventos, boletos, resultados, movimientos y auditoría.
7. Idempotencia de seeds, compras, series, resultados, premios y comandos repetibles.
8. Consultas N+1, conteos innecesarios, ordenamientos inestables y paginación incompleta.
9. Código específico de SQLite que pueda fallar en MySQL.
10. Textos/documentos obsoletos: detecta especialmente archivos que todavía afirmen que el proyecto llega solo a P-28 o que compra/resultados no existen.
11. Residuos de entrega: `__pycache__`, `.pyc`, `.pyo`, `.bak`, base de datos, `.env`, `staticfiles`, logs o secretos.
12. Coherencia entre `README.md`, matrices, inventario, código real y pruebas.

Para cada hallazgo entrega:
- ID único;
- severidad: bloqueante, alta, media o baja;
- archivo y líneas aproximadas;
- evidencia concreta;
- impacto;
- corrección recomendada;
- pruebas que deberían protegerla;
- si es un error real, deuda técnica, texto obsoleto o falso positivo.

Incluye:
- calificación actual sobre 10 con rúbrica;
- lista priorizada de reparaciones;
- archivos que NO deben tocarse;
- puerta de salida para considerar la auditoría cerrada.

No inventes cobertura ni resultados de ejecución. Si puedes ejecutar scripts, incluye comandos y salidas reales; si no, separa claramente revisión estática de validación ejecutada.
```

---

# PROMPT 3 — Reparación controlada de los hallazgos aprobados

```text
[PEGAR AQUÍ EL BLOQUE DE REGLAS MAESTRAS]

Adjunto:
1. el ZIP actual completo;
2. el informe de auditoría integral aprobado;
3. la lista exacta de IDs de hallazgos autorizados para reparar.

Repara únicamente esos IDs. No amplíes el alcance silenciosamente.

Antes de escribir código:
- confirma que cada hallazgo todavía existe en el ZIP actual;
- identifica dependencias entre archivos;
- marca cualquier hallazgo que ya no aplique;
- conserva todos los comportamientos que tienen pruebas aprobadas.

Requisitos de implementación:
- cambios mínimos y coherentes;
- ninguna debilitación de seguridad o inmutabilidad;
- servicios transaccionales para negocio sensible;
- migración solo si el modelo realmente cambia;
- pruebas de regresión para cada hallazgo;
- actualización de documentación solo donde cambió la verdad del sistema;
- eliminación de código muerto únicamente cuando puedas demostrar que no se usa por imports, URLs, templates, admin, signals, comandos o tests.

Entrega:
- matriz ID de hallazgo → archivos cambiados → prueba que lo cubre;
- archivos completos o ZIP de parche;
- diff;
- comandos PowerShell;
- resultados reales de pruebas si puedes ejecutarlas;
- calificación antes/después con justificación.

No cierres la tarea con pruebas parciales si cambiaste componentes transversales. La puerta de salida mínima es:
- `check` OK;
- `makemigrations --check --dry-run` sin cambios pendientes;
- pruebas específicas OK;
- suite completa OK;
- auditoría estática OK.
```

---

# PROMPT 4 — Auditoría UX, accesibilidad y responsive

```text
[PEGAR AQUÍ EL BLOQUE DE REGLAS MAESTRAS]

Adjunto el ZIP actual completo. Audita y mejora únicamente la UX, accesibilidad y respuesta visual, sin cambiar reglas de negocio.

Revisa todas las pantallas de:
- autenticación y selección de modo;
- dashboards Cliente/Vendedor/Administrador;
- cuentas;
- vendedores y solicitudes;
- finanzas;
- productos, eventos, compra de boletos, resultados y series;
- errores 403/404;
- navegación base, offcanvas, mensajes y modal de confirmación.

Valida como mínimo estos anchos:
- 320 px;
- 375 px;
- 768 px;
- 1024 px;
- 1440 px.

Comprueba:
1. Bootstrap 5.3 usado realmente.
2. Sin scroll horizontal accidental.
3. Formularios, tablas y botones utilizables con teclado.
4. `label`, `fieldset`, `legend`, `aria-*`, foco visible y mensajes asociados.
5. Colores con significado acompañados de texto; no depender solo de verde/celeste/color del producto.
6. Contraste razonable en identidad azul/dorada.
7. Tablas convertidas o desplazables de forma usable en móvil.
8. Botones peligrosos diferenciados y confirmados.
9. Estados vacíos, errores y mensajes coherentes.
10. Fechas, montos y estados legibles.
11. Tarjetas de sorteos abiertas/próximas uniformes.
12. Series activas, pausadas, completadas y archivadas diferenciables.
13. Ningún texto de fases antiguas como “todavía no se compra”.
14. Ningún enlace visible para un modo sin permiso.

Primero entrega diagnóstico y capturas/representaciones de lo encontrado. Después aplica solo mejoras justificadas.

No cambies modelos, servicios financieros, estados ni permisos para resolver problemas visuales.

Añade pruebas de templates/responses donde sea razonable y actualiza `docs/PRUEBAS_RESPONSIVE.md` con una matriz real de pantalla × ancho × resultado.
```

---

# PROMPT 5 — Auditoría de seguridad, permisos y reglas de negocio

```text
[PEGAR AQUÍ EL BLOQUE DE REGLAS MAESTRAS]

Adjunto el ZIP actual completo. Haz una auditoría de seguridad y permisos de extremo a extremo, y corrige únicamente fallos demostrados.

Debes construir una matriz de acciones por rol y modo:
- anónimo;
- CLIENTE;
- VENDEDOR;
- ADMINISTRADOR;
- usuario multirrol en cada modo activo;
- staff/superuser cuando corresponda.

Revisa:
1. Login, logout POST, registro, términos y cambio de modo.
2. CRUD de usuarios, vendedores, productos y eventos.
3. Propiedad de wallet, movimientos, boletos y solicitudes.
4. Conflicto de interés: Administrador que participó en un evento puede verlo en historial, marcado como participante, pero no administrarlo.
5. Vendedor no compra boletos.
6. Cliente no accede a administración.
7. Operaciones sensibles solo POST con CSRF.
8. Estados de evento solo por servicios/acciones permitidas.
9. Productos/eventos/resultados/tickets/movimientos/auditoría protegidos contra modificación o borrado indebido.
10. Compra y premios idempotentes.
11. Series pausadas, completadas o archivadas no generan.
12. Resultados manuales y automáticos no se duplican.
13. Errores 403/404 sin filtrar información sensible.
14. Parámetros GET manipulados, IDs ajenos y acceso directo por URL.
15. Ausencia de secretos o credenciales versionadas.

Crea pruebas negativas para cada permiso importante. No cambies una prueba para que pase sin demostrar primero cuál es la regla canónica.

Entrega una matriz regla → vista/servicio → prueba → resultado y una calificación antes/después.
```

---

# PROMPT 6 — Seeds finales y datos de demostración coherentes

```text
[PEGAR AQUÍ EL BLOQUE DE REGLAS MAESTRAS]

Adjunto el ZIP actual completo. Revisa y completa los seeds para demostración final, sin importar JSON legado ni guardar contraseñas en el repositorio.

Primero revisa:
- `apps/core/seed.py`;
- `seed_baseline`;
- `seed_demo`;
- pruebas de seeds;
- señales de wallets;
- modelos actuales de accounts, vendors, finance y lottery;
- reglas de productos, eventos, series, tickets y resultados.

Estado actual que debes verificar:
- `seed_baseline` crea roles y versiones legales;
- `seed_demo` crea usuarios demo usando `DJANGO_DEMO_PASSWORD` y exige `DEBUG=True`;
- no debe imprimir credenciales;
- debe ser idempotente.

Diseña una demo mínima pero completa, solo si es compatible con el alcance:
- usuarios Cliente, Vendedor, multirrol y Administrador;
- roles y términos aceptados;
- wallets existentes;
- perfil vendedor válido;
- productos oficiales;
- al menos un producto personalizado;
- eventos en estados útiles para mostrar el sistema;
- una serie manual y una automática;
- opcionalmente boletos/movimientos solo mediante servicios oficiales, nunca insertando saldos o historia sensible de forma incoherente.

Requisitos:
1. Separar baseline obligatorio de demo opcional.
2. Idempotencia comprobada al ejecutar dos veces.
3. No mutar historia aceptada o movimientos existentes.
4. No reutilizar datos del `respaldo_frontend`.
5. No usar fechas absolutas que caduquen; calcular fechas relativas con timezone.
6. No crear un resultado automático vencido que cambie de forma imprevisible durante las pruebas.
7. Documentar exactamente qué crea cada comando.
8. Añadir pruebas de conteos, relaciones, idempotencia y seguridad.

Entrega comandos para limpiar únicamente datos demo si ya existe una estrategia segura. No agregues un borrado masivo sin protección explícita.
```

---

# PROMPT 7 — Actualización documental y matriz de trazabilidad

```text
[PEGAR AQUÍ EL BLOQUE DE REGLAS MAESTRAS]

Adjunto el ZIP actual completo. Actualiza la documentación para que refleje el código real actual y elimine contradicciones históricas.

Antes de editar, compara:
- `README.md`;
- todos los `docs/*.md`;
- `docs/referencias/`;
- migraciones reales;
- URLs;
- modelos;
- comandos;
- pruebas;
- scripts de verificación.

Problemas que debes verificar:
- el README todavía puede afirmar que el proyecto llega a P-28;
- puede decir que compra, conversiones o resultados no existen aunque el código actual sí los implemente;
- matrices duplicadas con sufijo `(1)` pueden contener versiones divergentes;
- documentos P-36 pueden faltar del ZIP actual;
- el número de pruebas puede estar desactualizado.

Tareas:
1. Define qué documentos son canónicos y cuáles quedan históricos.
2. No borres historia útil; mueve o marca como histórico/deprecado cuando corresponda.
3. Actualiza el README con estado actual, rutas, comandos, migraciones y alcance real.
4. Actualiza matriz de trazabilidad: requisito → modelo → servicio → vista → template → prueba → evidencia.
5. Actualiza inventario de archivos y responsabilidades.
6. Documenta series manuales/automáticas, límites, archivo lógico, resultados automáticos e idempotencia.
7. Documenta claramente SQLite fase 1 y MySQL fase 2; no PostgreSQL.
8. No inventes cantidades de pruebas: obtén el número de una ejecución real o indica “pendiente de ejecución”.
9. Elimina textos obsoletos de interfaz/documentación sin cambiar reglas.
10. Entrega un índice de documentación final.

No modifiques lógica productiva en esta tarea, salvo que encuentres un enlace documental roto que requiera una corrección mínima y explícita.
```

---

# PROMPT 8 — Preparación y evidencias de la fase SQLite

```text
[PEGAR AQUÍ EL BLOQUE DE REGLAS MAESTRAS]

Adjunto el ZIP actual completo. Prepara el cierre demostrable de la fase SQLite antes de tocar MySQL.

Usa una base SQLite limpia y ejecuta el flujo real del proyecto. Revisa primero `scripts/verify.ps1` y decide si debe ampliarse para incluir las funciones agregadas después de P-28.

Debes verificar y documentar:
1. entorno y dependencias;
2. `check`;
3. ausencia de migraciones pendientes;
4. migración limpia desde cero hasta la última migración real;
5. seeds baseline y demo idempotentes;
6. smoke test de runserver;
7. suite completa;
8. static encontrados y collectstatic;
9. CRUD de accounts, vendors y lottery;
10. login/logout y modos;
11. wallets y movimientos;
12. solicitudes Cliente–Vendedor;
13. compra de boleto;
14. resultado manual;
15. serie limitada e ilimitada;
16. pausa, edición futura y archivo lógico;
17. resultado automático e idempotencia del comando;
18. responsive y permisos.

Crea:
- checklist de capturas con nombre de archivo sugerido;
- comandos exactos para producir cada evidencia;
- tabla evidencia → requisito del taller;
- guía de demostración de 10–15 minutos;
- reporte final de SQLite.

No fabriques capturas ni salidas. Marca como “pendiente” cualquier evidencia que deba producir el usuario en su equipo.
```

---

# PROMPT 9 — Auditoría previa de compatibilidad MySQL, sin migrar todavía

```text
[PEGAR AQUÍ EL BLOQUE DE REGLAS MAESTRAS]

Adjunto el ZIP actual completo. Realiza una auditoría previa de compatibilidad SQLite → MySQL, pero todavía NO cambies `.env`, no crees la base y no migres datos.

Revisa:
- `config/settings.py`;
- `.env.example`;
- `requirements.txt` y `requirements-mysql.txt`;
- todos los modelos y migraciones;
- constraints, índices, `UniqueConstraint`, `CheckConstraint` y `select_for_update`;
- consultas ORM;
- tests con supuestos SQLite;
- scripts de verificación;
- seeds;
- campos de fecha, texto, booleanos y enteros;
- nombres potencialmente reservados;
- collations/case sensitivity;
- charset `utf8mb4` y modo estricto.

Debes responder:
1. Qué ya está preparado para MySQL.
2. Qué puede fallar y por qué.
3. Si `mysqlclient` es suficiente en el entorno Windows actual.
4. Qué migraciones deben probarse en una base MySQL vacía.
5. Qué pruebas dependen de comportamiento SQLite.
6. Cómo manejar unicidad case-insensitive de email/username/documento si aplica.
7. Cómo respaldar SQLite antes del cambio.
8. Si el taller exige conservar datos o solo demostrar el mismo esquema en MySQL; busca la autoridad documental, no lo supongas.
9. Plan de rollback.
10. Puerta de salida antes de ejecutar la migración.

Entrega únicamente informe y plan. No generes código hasta que se apruebe la auditoría.
```

---

# PROMPT 10 — Ejecución de la fase MySQL

```text
[PEGAR AQUÍ EL BLOQUE DE REGLAS MAESTRAS]

Adjunto:
- ZIP actual aprobado en SQLite;
- informe de compatibilidad MySQL aprobado;
- salida verde de la verificación SQLite;
- datos del entorno MySQL local, sin compartir contraseñas en el chat si no es necesario.

Implementa y guía la segunda fase MySQL sin eliminar la compatibilidad SQLite.

Requisitos:
1. Mantén `DATABASE_URL` como selección de motor por entorno.
2. SQLite debe seguir siendo utilizable para fase 1 y pruebas locales cuando se configure.
3. Usa MySQL 8 y `utf8mb4`; no PostgreSQL.
4. No escribas credenciales en archivos versionados.
5. Actualiza `.env.example` solo con ejemplos sin secretos.
6. Instala dependencias desde `requirements-mysql.txt`.
7. Da comandos SQL exactos para crear base y usuario con privilegios mínimos, usando placeholders claros.
8. Ejecuta las migraciones desde cero en una base MySQL vacía; no uses `--fake`.
9. Ejecuta seeds y backfills idempotentes.
10. Ejecuta suite completa sobre MySQL.
11. Crea o adapta un script de verificación MySQL equivalente a `scripts/verify.ps1`, sin destruir una base real por accidente. Debe exigir un nombre de base de verificación claramente separado.
12. Prueba transacciones, bloqueos, idempotencia, unicidad y constraints importantes.
13. Define rollback a SQLite mediante `.env` sin perder el respaldo.
14. Documenta salidas esperadas y cómo confirmar qué motor está activo sin imprimir contraseñas.

Si la autoridad documental exige mover datos existentes, realiza primero una estrategia portable y probada. Si no lo exige, usa una base MySQL limpia y seeds controlados. No mezcles ambas estrategias sin explicar la decisión.

Entrega archivos completos, comandos PowerShell/SQL, pruebas, evidencia esperada y criterio de aprobación.
```

---

# PROMPT 11 — Comparación SQLite vs MySQL y regresión cruzada

```text
[PEGAR AQUÍ EL BLOQUE DE REGLAS MAESTRAS]

Adjunto el proyecto ya ejecutable en SQLite y MySQL. Realiza una regresión cruzada y demuestra que las reglas se comportan igual en ambos motores.

Crea una matriz de pruebas para:
- migraciones limpias;
- seeds;
- unicidad de usuarios/productos/combinaciones;
- constraints de series;
- transiciones de eventos;
- compra e idempotencia;
- movimientos append-only;
- resultado único e inmutable;
- premios únicos;
- archivo lógico de series;
- generación concurrente o repetida;
- filtros y ordenamientos;
- fechas con `America/Guayaquil` y `USE_TZ=True`.

Ejecuta la misma suite con dos `DATABASE_URL` distintas y registra:
- motor;
- versión;
- cantidad de pruebas;
- fallos;
- diferencias encontradas.

No ocultes fallos con condiciones específicas del motor salvo que exista una razón documentada. Corrige la causa común cuando sea posible.

Entrega un reporte comparativo y una puerta de salida objetiva para declarar terminada la fase MySQL.
```

---

# PROMPT 12 — Limpieza, empaquetado y entrega final

```text
[PEGAR AQUÍ EL BLOQUE DE REGLAS MAESTRAS]

Adjunto el proyecto final y las evidencias aprobadas. Prepara la entrega final sin modificar reglas de negocio.

Audita y limpia:
- `__pycache__`;
- `.pyc`, `.pyo`, `.bak`;
- `.env`;
- `db.sqlite3` si la entrega no la requiere;
- `verification.sqlite3`;
- `staticfiles/`;
- logs;
- cobertura;
- archivos temporales;
- credenciales o secretos;
- ZIPs anidados innecesarios;
- duplicados documentales no canónicos.

Conserva:
- migraciones completas;
- `.env.example` sin secretos;
- requisitos SQLite/MySQL;
- static fuente;
- templates;
- scripts de verificación;
- documentación canónica;
- respaldo frontend solo si la entrega lo exige o está documentado.

Tareas:
1. Ejecuta auditoría estática final.
2. Ejecuta verificación SQLite limpia.
3. Ejecuta verificación MySQL limpia.
4. Ejecuta suite completa.
5. Verifica `makemigrations --check --dry-run`.
6. Verifica `findstatic` y `collectstatic`.
7. Genera inventario y manifiesto SHA-256 actualizados.
8. Crea un ZIP final con una sola raíz clara.
9. Abre el ZIP generado y verifica sus contenidos y hashes.
10. Entrega instrucciones de instalación desde cero para SQLite y MySQL.
11. Entrega guion de demostración y checklist de evidencias.
12. Califica el proyecto con rúbrica antes/después y explica cualquier pendiente real.

Nunca afirmes que el ZIP está limpio sin inspeccionarlo después de crearlo.
```

---

# Orden recomendado de uso

1. Prompt 1 — cierre de series y `last_synced_at`.
2. Prompt 2 — auditoría integral sin cambios.
3. Prompt 3 — reparación de hallazgos aprobados.
4. Prompt 4 — UX/accesibilidad/responsive.
5. Prompt 5 — seguridad y permisos.
6. Prompt 6 — seeds de demostración.
7. Prompt 7 — documentación y trazabilidad.
8. Prompt 8 — evidencias y cierre SQLite.
9. Prompt 9 — auditoría previa MySQL.
10. Prompt 10 — implementación MySQL.
11. Prompt 11 — regresión cruzada.
12. Prompt 12 — entrega final.

No se debe iniciar MySQL hasta que SQLite tenga suite completa y auditoría en verde.
