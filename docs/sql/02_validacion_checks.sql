-- =============================================================
-- 02_validacion_checks.sql
-- Consultas de verificación del modelo ER temporal.
--
-- Ejecutar después de:
--   00_validacion_ddl.sql
--   01_validacion_inserts.sql
--
-- Una consulta de error debe devolver 0 filas o total_errores = 0.
-- =============================================================

USE loteria_taller3_validacion;

-- =============================================================
-- 1. Identidad de la base y versión
-- =============================================================

SELECT
    DATABASE() AS base_activa,
    VERSION() AS version_mysql,
    @@character_set_database AS charset_base,
    @@collation_database AS collation_base;

-- =============================================================
-- 2. Inventario de tablas
-- Resultado esperado: 13 tablas del ER.
-- =============================================================

SELECT
    table_name
FROM information_schema.tables
WHERE table_schema = 'loteria_taller3_validacion'
ORDER BY table_name;

SELECT COUNT(*) AS total_tablas
FROM information_schema.tables
WHERE table_schema = 'loteria_taller3_validacion';

-- =============================================================
-- 3. Conteos por tabla
-- Esperados:
-- 10 en casi todas;
-- 20 wallets;
-- 20 movements;
-- 3 productos canónicos.
-- =============================================================

SELECT 'accounts_user' AS tabla, COUNT(*) AS total FROM accounts_user
UNION ALL
SELECT 'accounts_terms_version', COUNT(*) FROM accounts_terms_version
UNION ALL
SELECT 'accounts_terms_acceptance', COUNT(*) FROM accounts_terms_acceptance
UNION ALL
SELECT 'core_audit_event', COUNT(*) FROM core_audit_event
UNION ALL
SELECT 'finance_wallet', COUNT(*) FROM finance_wallet
UNION ALL
SELECT 'finance_movement', COUNT(*) FROM finance_movement
UNION ALL
SELECT 'vendors_vendor_profile', COUNT(*) FROM vendors_vendor_profile
UNION ALL
SELECT 'vendors_conversion_request', COUNT(*) FROM vendors_conversion_request
UNION ALL
SELECT 'vendors_conversion_assignment', COUNT(*) FROM vendors_conversion_assignment
UNION ALL
SELECT 'lottery_product', COUNT(*) FROM lottery_product
UNION ALL
SELECT 'lottery_draw_event', COUNT(*) FROM lottery_draw_event
UNION ALL
SELECT 'lottery_ticket', COUNT(*) FROM lottery_ticket
UNION ALL
SELECT 'lottery_draw_result', COUNT(*) FROM lottery_draw_result;

-- =============================================================
-- 4. Duplicados en campos únicos
-- Todas deben devolver 0 filas.
-- =============================================================

SELECT username, COUNT(*) AS repeticiones
FROM accounts_user
GROUP BY username
HAVING COUNT(*) > 1;

SELECT email, COUNT(*) AS repeticiones
FROM accounts_user
GROUP BY email
HAVING COUNT(*) > 1;

SELECT document, COUNT(*) AS repeticiones
FROM accounts_user
GROUP BY document
HAVING COUNT(*) > 1;

SELECT kind, version, COUNT(*) AS repeticiones
FROM accounts_terms_version
GROUP BY kind, version
HAVING COUNT(*) > 1;

SELECT user_id, terms_version_id, COUNT(*) AS repeticiones
FROM accounts_terms_acceptance
GROUP BY user_id, terms_version_id
HAVING COUNT(*) > 1;

SELECT user_id, currency, COUNT(*) AS repeticiones
FROM finance_wallet
GROUP BY user_id, currency
HAVING COUNT(*) > 1;

SELECT user_id, COUNT(*) AS perfiles
FROM vendors_vendor_profile
GROUP BY user_id
HAVING COUNT(*) > 1;

SELECT operation_id, COUNT(*) AS repeticiones
FROM vendors_conversion_request
GROUP BY operation_id
HAVING COUNT(*) > 1;

SELECT code, COUNT(*) AS repeticiones
FROM lottery_product
GROUP BY code
HAVING COUNT(*) > 1;

SELECT operation_id, COUNT(*) AS repeticiones
FROM lottery_ticket
GROUP BY operation_id
HAVING COUNT(*) > 1;

SELECT event_id, normalized_key, COUNT(*) AS repeticiones
FROM lottery_ticket
GROUP BY event_id, normalized_key
HAVING COUNT(*) > 1;

SELECT event_id, COUNT(*) AS resultados
FROM lottery_draw_result
GROUP BY event_id
HAVING COUNT(*) > 1;

-- =============================================================
-- 5. Integridad referencial
-- Cada total_errores debe ser 0.
-- =============================================================

SELECT COUNT(*) AS total_errores
FROM accounts_terms_acceptance ta
LEFT JOIN accounts_user u ON u.id = ta.user_id
WHERE u.id IS NULL;

SELECT COUNT(*) AS total_errores
FROM accounts_terms_acceptance ta
LEFT JOIN accounts_terms_version tv ON tv.id = ta.terms_version_id
WHERE tv.id IS NULL;

SELECT COUNT(*) AS total_errores
FROM core_audit_event a
LEFT JOIN accounts_user u ON u.id = a.actor_id
WHERE a.actor_id IS NOT NULL
  AND u.id IS NULL;

SELECT COUNT(*) AS total_errores
FROM finance_wallet w
LEFT JOIN accounts_user u ON u.id = w.user_id
WHERE u.id IS NULL;

SELECT COUNT(*) AS total_errores
FROM finance_movement m
LEFT JOIN finance_wallet w ON w.id = m.wallet_id
WHERE w.id IS NULL;

SELECT COUNT(*) AS total_errores
FROM vendors_vendor_profile vp
LEFT JOIN accounts_user u ON u.id = vp.user_id
WHERE u.id IS NULL;

SELECT COUNT(*) AS total_errores
FROM vendors_conversion_request cr
LEFT JOIN accounts_user u ON u.id = cr.client_id
WHERE u.id IS NULL;

SELECT COUNT(*) AS total_errores
FROM vendors_conversion_assignment ca
LEFT JOIN vendors_conversion_request cr ON cr.id = ca.request_id
LEFT JOIN vendors_vendor_profile vp ON vp.id = ca.vendor_id
WHERE cr.id IS NULL OR vp.id IS NULL;

SELECT COUNT(*) AS total_errores
FROM lottery_draw_event de
LEFT JOIN lottery_product lp ON lp.id = de.product_id
WHERE lp.id IS NULL;

SELECT COUNT(*) AS total_errores
FROM lottery_ticket t
LEFT JOIN accounts_user u ON u.id = t.user_id
LEFT JOIN lottery_draw_event de ON de.id = t.event_id
WHERE u.id IS NULL OR de.id IS NULL;

SELECT COUNT(*) AS total_errores
FROM lottery_draw_result dr
LEFT JOIN lottery_draw_event de ON de.id = dr.event_id
LEFT JOIN accounts_user u ON u.id = dr.published_by_id
WHERE de.id IS NULL OR u.id IS NULL;

-- =============================================================
-- 6. Valores monetarios y estados
-- Todas deben devolver 0 filas.
-- =============================================================

SELECT *
FROM finance_wallet
WHERE available_minor < 0
   OR reserved_minor < 0;

SELECT *
FROM finance_movement
WHERE amount_minor <= 0
   OR balance_after_minor < 0;

SELECT *
FROM vendors_conversion_request
WHERE amount_minor <= 0;

SELECT *
FROM lottery_draw_event
WHERE price_minor <= 0
   OR prize_minor < 0;

SELECT *
FROM lottery_ticket
WHERE price_minor <= 0
   OR award_minor < 0;

-- =============================================================
-- 7. Configuración canónica de productos
-- Resultado esperado: tres filas correctas y 0 errores.
-- =============================================================

SELECT
    code,
    allowed_symbols,
    selection_count,
    is_active
FROM lottery_product
ORDER BY id;

SELECT COUNT(*) AS total_errores
FROM lottery_product
WHERE NOT (
    (code = 'OCTAL'
        AND allowed_symbols = '01234567'
        AND selection_count = 4)
    OR
    (code = 'DECIMAL'
        AND allowed_symbols = '0123456789'
        AND selection_count = 5)
    OR
    (code = 'HEXADECIMAL'
        AND allowed_symbols = '0123456789ABCDEF'
        AND selection_count = 6)
);

-- =============================================================
-- 8. Cierre exactamente 10 minutos antes
-- total_errores esperado: 0.
-- =============================================================

SELECT
    id,
    name,
    sales_close_at,
    draw_at,
    TIMESTAMPDIFF(MINUTE, sales_close_at, draw_at) AS minutos_antes
FROM lottery_draw_event
ORDER BY id;

SELECT COUNT(*) AS total_errores
FROM lottery_draw_event
WHERE sales_close_at <> DATE_SUB(draw_at, INTERVAL 10 MINUTE);

-- =============================================================
-- 9. Validación de claves de tickets y resultados por producto
-- Las consultas de errores deben devolver 0 filas.
-- =============================================================

-- Longitud exacta
SELECT
    t.id,
    p.code,
    t.normalized_key,
    CHAR_LENGTH(t.normalized_key) AS longitud,
    p.selection_count
FROM lottery_ticket t
JOIN lottery_draw_event e ON e.id = t.event_id
JOIN lottery_product p ON p.id = e.product_id
WHERE CHAR_LENGTH(t.normalized_key) <> p.selection_count;

SELECT
    r.id,
    p.code,
    r.winning_key,
    CHAR_LENGTH(r.winning_key) AS longitud,
    p.selection_count
FROM lottery_draw_result r
JOIN lottery_draw_event e ON e.id = r.event_id
JOIN lottery_product p ON p.id = e.product_id
WHERE CHAR_LENGTH(r.winning_key) <> p.selection_count;

-- Universo permitido
SELECT t.id, p.code, t.normalized_key
FROM lottery_ticket t
JOIN lottery_draw_event e ON e.id = t.event_id
JOIN lottery_product p ON p.id = e.product_id
WHERE
    (p.code = 'OCTAL' AND t.normalized_key NOT REGEXP '^[0-7]{4}$')
    OR
    (p.code = 'DECIMAL' AND t.normalized_key NOT REGEXP '^[0-9]{5}$')
    OR
    (p.code = 'HEXADECIMAL' AND t.normalized_key NOT REGEXP '^[0-9A-F]{6}$');

SELECT r.id, p.code, r.winning_key
FROM lottery_draw_result r
JOIN lottery_draw_event e ON e.id = r.event_id
JOIN lottery_product p ON p.id = e.product_id
WHERE
    (p.code = 'OCTAL' AND r.winning_key NOT REGEXP '^[0-7]{4}$')
    OR
    (p.code = 'DECIMAL' AND r.winning_key NOT REGEXP '^[0-9]{5}$')
    OR
    (p.code = 'HEXADECIMAL' AND r.winning_key NOT REGEXP '^[0-9A-F]{6}$');

-- Símbolos repetidos: cada consulta debe devolver 0 filas.
-- Se verifica comparando longitud total con cantidad de caracteres
-- distintos obtenidos mediante una tabla derivada de posiciones.
WITH RECURSIVE positions AS (
    SELECT 1 AS pos
    UNION ALL
    SELECT pos + 1
    FROM positions
    WHERE pos < 16
)
SELECT
    t.id,
    t.normalized_key
FROM lottery_ticket t
JOIN positions p
    ON p.pos <= CHAR_LENGTH(t.normalized_key)
GROUP BY t.id, t.normalized_key
HAVING COUNT(DISTINCT SUBSTRING(t.normalized_key, p.pos, 1))
       <> CHAR_LENGTH(t.normalized_key);

WITH RECURSIVE positions AS (
    SELECT 1 AS pos
    UNION ALL
    SELECT pos + 1
    FROM positions
    WHERE pos < 16
)
SELECT
    r.id,
    r.winning_key
FROM lottery_draw_result r
JOIN positions p
    ON p.pos <= CHAR_LENGTH(r.winning_key)
GROUP BY r.id, r.winning_key
HAVING COUNT(DISTINCT SUBSTRING(r.winning_key, p.pos, 1))
       <> CHAR_LENGTH(r.winning_key);

-- =============================================================
-- 10. Asignación activa única por solicitud
-- Esta regla se controlará en services.py; la carga debe cumplirla.
-- Resultado esperado: 0 filas.
-- =============================================================

SELECT request_id, COUNT(*) AS asignaciones_activas
FROM vendors_conversion_assignment
WHERE status = 'ACTIVE'
GROUP BY request_id
HAVING COUNT(*) > 1;

-- =============================================================
-- 11. Coherencia básica solicitud/asignación
-- Consultas de hallazgos esperados: 0 filas.
-- =============================================================

SELECT cr.id, cr.status
FROM vendors_conversion_request cr
WHERE cr.status = 'IN_PROGRESS'
  AND NOT EXISTS (
      SELECT 1
      FROM vendors_conversion_assignment ca
      WHERE ca.request_id = cr.id
        AND ca.status = 'ACTIVE'
  );

SELECT cr.id, cr.status
FROM vendors_conversion_request cr
WHERE cr.status = 'COMPLETED_BY_VENDOR'
  AND NOT EXISTS (
      SELECT 1
      FROM vendors_conversion_assignment ca
      WHERE ca.request_id = cr.id
        AND ca.status = 'COMPLETED'
  );

-- =============================================================
-- 12. Cálculos económicos de referencia
-- No modifican datos; solo validan fórmulas del taller.
-- =============================================================

-- Recarga 1:1
SELECT
    10000 AS recarga_real_minor,
    10000 AS credito_real_minor,
    CASE WHEN 10000 = 10000 THEN 'OK' ELSE 'ERROR' END AS validacion;

-- Conversión VIRTUAL -> REAL con 10 %
SELECT
    50000 AS gross_virtual_minor,
    5000 AS fee_virtual_minor,
    45000 AS net_real_minor,
    CASE
        WHEN 50000 = 5000 + 45000
         AND 5000 = 50000 * 10 DIV 100
        THEN 'OK'
        ELSE 'ERROR'
    END AS validacion;

-- Compra mayorista 0.90 REAL por 1.00 VIRTUAL
SELECT
    10000 AS virtual_minor,
    9000 AS real_cost_minor,
    CASE
        WHEN 9000 = 10000 * 90 DIV 100
        THEN 'OK'
        ELSE 'ERROR'
    END AS validacion;

-- =============================================================
-- 13. Historia protegida: demostración de RESTRICT
-- NO ejecutar durante una presentación sin saber que fallará.
-- Estas sentencias están comentadas a propósito.
-- =============================================================

-- Debe fallar porque el usuario tiene wallets, tickets u otra historia:
-- DELETE FROM accounts_user WHERE id = 1;

-- Debe fallar porque la wallet tiene movimientos:
-- DELETE FROM finance_wallet WHERE id = 1;

-- Debe fallar porque el evento tiene tickets y resultado:
-- DELETE FROM lottery_draw_event WHERE id = 1;

-- Debe fallar porque el producto tiene eventos:
-- DELETE FROM lottery_product WHERE id = 1;

-- =============================================================
-- 14. Eventos cancelados con resultado
-- Resultado esperado: 0 filas.
-- La implementación Django también deberá impedir esta combinación
-- mediante el servicio de publicación de resultados.
-- =============================================================

SELECT
    e.id,
    e.name,
    e.status,
    r.id AS result_id,
    r.winning_key
FROM lottery_draw_event e
JOIN lottery_draw_result r ON r.event_id = e.id
WHERE e.status = 'CANCELLED';

-- =============================================================
-- 15. Eliminación de la base temporal
-- Ejecutar SOLO después de guardar capturas y validar todo.
-- =============================================================

-- DROP DATABASE IF EXISTS loteria_taller3_validacion;
