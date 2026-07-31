-- =============================================================
-- 01_validacion_inserts.sql
-- Datos TEMPORALES y académicos para validar el modelo ER.
--
-- Ejecutar después de:
--   docs/sql/00_validacion_ddl.sql
--
-- No contiene contraseñas, tarjetas, cuentas bancarias ni secretos.
-- La base se eliminará después de la validación.
-- =============================================================

USE loteria_taller3_validacion;

START TRANSACTION;

-- =============================================================
-- accounts_user: 10 registros
-- =============================================================

INSERT INTO accounts_user
    (id, username, email, document, phone, birth_date, status, is_active,
     created_at, updated_at)
VALUES
    (1, 'cliente01', 'cliente01@example.test', '0900000001', '0990000001',
     '1998-01-15', 'ACTIVE', TRUE, '2026-07-30 08:00:00', '2026-07-30 08:00:00'),
    (2, 'cliente02', 'cliente02@example.test', '0900000002', '0990000002',
     '1997-02-16', 'ACTIVE', TRUE, '2026-07-30 08:01:00', '2026-07-30 08:01:00'),
    (3, 'cliente03', 'cliente03@example.test', '0900000003', '0990000003',
     '1996-03-17', 'ACTIVE', TRUE, '2026-07-30 08:02:00', '2026-07-30 08:02:00'),
    (4, 'vendedor01', 'vendedor01@example.test', '0900000004', '0990000004',
     '1995-04-18', 'ACTIVE', TRUE, '2026-07-30 08:03:00', '2026-07-30 08:03:00'),
    (5, 'vendedor02', 'vendedor02@example.test', '0900000005', '0990000005',
     '1994-05-19', 'ACTIVE', TRUE, '2026-07-30 08:04:00', '2026-07-30 08:04:00'),
    (6, 'vendedor03', 'vendedor03@example.test', '0900000006', '0990000006',
     '1993-06-20', 'SUSPENDED', TRUE, '2026-07-30 08:05:00', '2026-07-30 08:05:00'),
    (7, 'admin01', 'admin01@example.test', '0900000007', '0990000007',
     '1992-07-21', 'ACTIVE', TRUE, '2026-07-30 08:06:00', '2026-07-30 08:06:00'),
    (8, 'admin02', 'admin02@example.test', '0900000008', '0990000008',
     '1991-08-22', 'ACTIVE', TRUE, '2026-07-30 08:07:00', '2026-07-30 08:07:00'),
    (9, 'usuario09', 'usuario09@example.test', '0900000009', NULL,
     '1990-09-23', 'BLOCKED', TRUE, '2026-07-30 08:08:00', '2026-07-30 08:08:00'),
    (10, 'usuario10', 'usuario10@example.test', '0900000010', NULL,
     '1989-10-24', 'DISABLED', FALSE, '2026-07-30 08:09:00', '2026-07-30 08:09:00');

-- =============================================================
-- accounts_terms_version: 10 registros
-- =============================================================

INSERT INTO accounts_terms_version
    (id, kind, version, title, content, effective_at, is_active, created_at)
VALUES
    (1, 'TERMS', '1.0', 'Términos 1.0',
     'Condiciones académicas iniciales del sistema.',
     '2026-01-01 00:00:00', FALSE, '2026-01-01 00:00:00'),
    (2, 'PRIVACY', '1.0', 'Privacidad 1.0',
     'Política inicial de privacidad académica.',
     '2026-01-01 00:00:00', FALSE, '2026-01-01 00:00:00'),
    (3, 'TERMS', '1.1', 'Términos 1.1',
     'Actualización de condiciones académicas.',
     '2026-02-01 00:00:00', FALSE, '2026-02-01 00:00:00'),
    (4, 'PRIVACY', '1.1', 'Privacidad 1.1',
     'Actualización de privacidad y minimización de datos.',
     '2026-02-01 00:00:00', FALSE, '2026-02-01 00:00:00'),
    (5, 'TERMS', '1.2', 'Términos 1.2',
     'Ajustes sobre autenticación y roles.',
     '2026-03-01 00:00:00', FALSE, '2026-03-01 00:00:00'),
    (6, 'PRIVACY', '1.2', 'Privacidad 1.2',
     'Ajustes sobre datos visibles y auditoría.',
     '2026-03-01 00:00:00', FALSE, '2026-03-01 00:00:00'),
    (7, 'TERMS', '1.3', 'Términos 1.3',
     'Ajustes sobre operaciones simuladas.',
     '2026-04-01 00:00:00', FALSE, '2026-04-01 00:00:00'),
    (8, 'PRIVACY', '1.3', 'Privacidad 1.3',
     'Ajustes sobre conservación histórica.',
     '2026-04-01 00:00:00', FALSE, '2026-04-01 00:00:00'),
    (9, 'TERMS', '1.4', 'Términos 1.4 vigentes',
     'Términos vigentes para la demostración del taller.',
     '2026-07-01 00:00:00', TRUE, '2026-07-01 00:00:00'),
    (10, 'PRIVACY', '1.4', 'Privacidad 1.4 vigente',
     'Política vigente para la demostración del taller.',
     '2026-07-01 00:00:00', TRUE, '2026-07-01 00:00:00');

-- =============================================================
-- accounts_terms_acceptance: 10 registros
-- =============================================================

INSERT INTO accounts_terms_acceptance
    (id, user_id, terms_version_id, accepted_at, ip_address)
VALUES
    (1, 1, 9, '2026-07-30 08:10:00', '192.0.2.1'),
    (2, 2, 9, '2026-07-30 08:11:00', '192.0.2.2'),
    (3, 3, 9, '2026-07-30 08:12:00', '192.0.2.3'),
    (4, 4, 9, '2026-07-30 08:13:00', '192.0.2.4'),
    (5, 5, 9, '2026-07-30 08:14:00', '192.0.2.5'),
    (6, 6, 9, '2026-07-30 08:15:00', '192.0.2.6'),
    (7, 7, 10, '2026-07-30 08:16:00', '2001:db8::7'),
    (8, 8, 10, '2026-07-30 08:17:00', '2001:db8::8'),
    (9, 9, 10, '2026-07-30 08:18:00', '2001:db8::9'),
    (10, 10, 10, '2026-07-30 08:19:00', NULL);

-- =============================================================
-- core_audit_event: 10 registros
-- =============================================================

INSERT INTO core_audit_event
    (id, actor_id, active_mode, action, resource_type, resource_id,
     reason, metadata, created_at)
VALUES
    (1, 7, 'ADMINISTRADOR', 'CREATE_USER', 'User', '1',
     'Creación académica de usuario', '{"source":"validation"}',
     '2026-07-30 08:20:00'),
    (2, 7, 'ADMINISTRADOR', 'CREATE_USER', 'User', '2',
     'Creación académica de usuario', '{"source":"validation"}',
     '2026-07-30 08:21:00'),
    (3, 7, 'ADMINISTRADOR', 'ACTIVATE_VENDOR', 'VendorProfile', '1',
     'Activación de vendedor demo', '{"status":"ACTIVE"}',
     '2026-07-30 08:22:00'),
    (4, 8, 'ADMINISTRADOR', 'CREATE_PRODUCT', 'LotteryProduct', '1',
     'Producto oficial Octal', '{"code":"OCTAL"}',
     '2026-07-30 08:23:00'),
    (5, 8, 'ADMINISTRADOR', 'CREATE_PRODUCT', 'LotteryProduct', '2',
     'Producto oficial Decimal', '{"code":"DECIMAL"}',
     '2026-07-30 08:24:00'),
    (6, 8, 'ADMINISTRADOR', 'CREATE_PRODUCT', 'LotteryProduct', '3',
     'Producto oficial Hexadecimal', '{"code":"HEXADECIMAL"}',
     '2026-07-30 08:25:00'),
    (7, 1, 'CLIENTE', 'CREATE_REQUEST', 'ConversionRequest', '1',
     'Solicitud simulada', '{"amount_minor":10000}',
     '2026-07-30 08:26:00'),
    (8, 4, 'VENDEDOR', 'ASSIGN_REQUEST', 'ConversionAssignment', '1',
     'Asignación simulada', '{"request_id":1}',
     '2026-07-30 08:27:00'),
    (9, 1, 'CLIENTE', 'BUY_TICKET', 'Ticket', '1',
     'Compra simulada', '{"event_id":1}',
     '2026-07-30 08:28:00'),
    (10, 7, 'ADMINISTRADOR', 'PUBLISH_RESULT', 'DrawResult', '1',
     'Publicación académica', '{"event_id":1}',
     '2026-07-30 08:29:00');

-- =============================================================
-- finance_wallet: 20 registros, dos por usuario
-- =============================================================

INSERT INTO finance_wallet
    (id, user_id, currency, available_minor, reserved_minor, status,
     created_at, updated_at)
VALUES
    (1, 1, 'REAL', 50000, 10000, 'ACTIVE', '2026-07-30 08:30:00', '2026-07-30 08:30:00'),
    (2, 1, 'VIRTUAL', 30000, 0, 'ACTIVE', '2026-07-30 08:30:00', '2026-07-30 08:30:00'),
    (3, 2, 'REAL', 40000, 8000, 'ACTIVE', '2026-07-30 08:31:00', '2026-07-30 08:31:00'),
    (4, 2, 'VIRTUAL', 25000, 0, 'ACTIVE', '2026-07-30 08:31:00', '2026-07-30 08:31:00'),
    (5, 3, 'REAL', 35000, 5000, 'ACTIVE', '2026-07-30 08:32:00', '2026-07-30 08:32:00'),
    (6, 3, 'VIRTUAL', 22000, 0, 'ACTIVE', '2026-07-30 08:32:00', '2026-07-30 08:32:00'),
    (7, 4, 'REAL', 90000, 0, 'ACTIVE', '2026-07-30 08:33:00', '2026-07-30 08:33:00'),
    (8, 4, 'VIRTUAL', 120000, 0, 'ACTIVE', '2026-07-30 08:33:00', '2026-07-30 08:33:00'),
    (9, 5, 'REAL', 80000, 0, 'ACTIVE', '2026-07-30 08:34:00', '2026-07-30 08:34:00'),
    (10, 5, 'VIRTUAL', 100000, 0, 'ACTIVE', '2026-07-30 08:34:00', '2026-07-30 08:34:00'),
    (11, 6, 'REAL', 20000, 0, 'BLOCKED', '2026-07-30 08:35:00', '2026-07-30 08:35:00'),
    (12, 6, 'VIRTUAL', 50000, 0, 'BLOCKED', '2026-07-30 08:35:00', '2026-07-30 08:35:00'),
    (13, 7, 'REAL', 10000, 0, 'ACTIVE', '2026-07-30 08:36:00', '2026-07-30 08:36:00'),
    (14, 7, 'VIRTUAL', 10000, 0, 'ACTIVE', '2026-07-30 08:36:00', '2026-07-30 08:36:00'),
    (15, 8, 'REAL', 15000, 0, 'ACTIVE', '2026-07-30 08:37:00', '2026-07-30 08:37:00'),
    (16, 8, 'VIRTUAL', 15000, 0, 'ACTIVE', '2026-07-30 08:37:00', '2026-07-30 08:37:00'),
    (17, 9, 'REAL', 0, 0, 'BLOCKED', '2026-07-30 08:38:00', '2026-07-30 08:38:00'),
    (18, 9, 'VIRTUAL', 0, 0, 'BLOCKED', '2026-07-30 08:38:00', '2026-07-30 08:38:00'),
    (19, 10, 'REAL', 0, 0, 'CLOSED', '2026-07-30 08:39:00', '2026-07-30 08:39:00'),
    (20, 10, 'VIRTUAL', 0, 0, 'CLOSED', '2026-07-30 08:39:00', '2026-07-30 08:39:00');

-- =============================================================
-- finance_movement: 20 registros
-- =============================================================

INSERT INTO finance_movement
    (id, wallet_id, operation_id, type, direction, amount_minor,
     balance_after_minor, description, created_at)
VALUES
    (1, 1, '00000000-0000-0000-0000-000000000001', 'TOP_UP', 'CREDIT',
     50000, 50000, 'Recarga REAL simulada 1:1', '2026-07-30 08:40:00'),
    (2, 2, '00000000-0000-0000-0000-000000000002', 'TRANSFER', 'CREDIT',
     30000, 30000, 'Crédito VIRTUAL académico', '2026-07-30 08:41:00'),
    (3, 3, '00000000-0000-0000-0000-000000000003', 'TOP_UP', 'CREDIT',
     40000, 40000, 'Recarga REAL simulada 1:1', '2026-07-30 08:42:00'),
    (4, 4, '00000000-0000-0000-0000-000000000004', 'TRANSFER', 'CREDIT',
     25000, 25000, 'Crédito VIRTUAL académico', '2026-07-30 08:43:00'),
    (5, 5, '00000000-0000-0000-0000-000000000005', 'TOP_UP', 'CREDIT',
     35000, 35000, 'Recarga REAL simulada 1:1', '2026-07-30 08:44:00'),
    (6, 6, '00000000-0000-0000-0000-000000000006', 'TRANSFER', 'CREDIT',
     22000, 22000, 'Crédito VIRTUAL académico', '2026-07-30 08:45:00'),
    (7, 7, '00000000-0000-0000-0000-000000000007', 'TOP_UP', 'CREDIT',
     90000, 90000, 'Capital REAL del vendedor', '2026-07-30 08:46:00'),
    (8, 8, '00000000-0000-0000-0000-000000000008', 'VENDOR_PURCHASE', 'CREDIT',
     100000, 100000, 'Compra mayorista VIRTUAL', '2026-07-30 08:47:00'),
    (9, 7, '00000000-0000-0000-0000-000000000008', 'VENDOR_PURCHASE', 'DEBIT',
     90000, 0, 'Costo 0.90 REAL por 1.00 VIRTUAL', '2026-07-30 08:47:00'),
    (10, 9, '00000000-0000-0000-0000-000000000010', 'TOP_UP', 'CREDIT',
     80000, 80000, 'Capital REAL del vendedor', '2026-07-30 08:48:00'),
    (11, 10, '00000000-0000-0000-0000-000000000011', 'VENDOR_PURCHASE', 'CREDIT',
     100000, 100000, 'Compra mayorista VIRTUAL', '2026-07-30 08:49:00'),
    (12, 9, '00000000-0000-0000-0000-000000000011', 'VENDOR_PURCHASE', 'DEBIT',
     90000, 0, 'Costo académico mayorista', '2026-07-30 08:49:00'),
    (13, 13, '00000000-0000-0000-0000-000000000013', 'TOP_UP', 'CREDIT',
     10000, 10000, 'Recarga administrativa simulada', '2026-07-30 08:50:00'),
    (14, 14, '00000000-0000-0000-0000-000000000014', 'PRIZE', 'CREDIT',
     10000, 10000, 'Premio académico', '2026-07-30 08:51:00'),
    (15, 15, '00000000-0000-0000-0000-000000000015', 'TOP_UP', 'CREDIT',
     15000, 15000, 'Recarga administrativa simulada', '2026-07-30 08:52:00'),
    (16, 16, '00000000-0000-0000-0000-000000000016', 'REFUND', 'CREDIT',
     15000, 15000, 'Reembolso académico', '2026-07-30 08:53:00'),
    (17, 1, '00000000-0000-0000-0000-000000000017', 'REQUEST', 'DEBIT',
     10000, 50000, 'Reserva representada en wallet', '2026-07-30 08:54:00'),
    (18, 2, '00000000-0000-0000-0000-000000000018', 'TICKET_PURCHASE', 'DEBIT',
     500, 29500, 'Compra de boleto Octal', '2026-07-30 08:55:00'),
    (19, 3, '00000000-0000-0000-0000-000000000019', 'ADJUSTMENT', 'CREDIT',
     1000, 40000, 'Ajuste académico auditado', '2026-07-30 08:56:00'),
    (20, 4, '00000000-0000-0000-0000-000000000020', 'VIRTUAL_TO_REAL', 'DEBIT',
     5000, 20000, 'Conversión VIRTUAL a REAL con 10%', '2026-07-30 08:57:00');

-- =============================================================
-- vendors_vendor_profile: 10 registros
-- =============================================================

INSERT INTO vendors_vendor_profile
    (id, user_id, status, activated_at, created_at, updated_at)
VALUES
    (1, 1, 'ACTIVE', '2026-07-01 09:00:00', '2026-06-25 09:00:00', '2026-07-01 09:00:00'),
    (2, 2, 'ACTIVE', '2026-07-02 09:00:00', '2026-06-26 09:00:00', '2026-07-02 09:00:00'),
    (3, 3, 'PENDING', NULL, '2026-07-03 09:00:00', '2026-07-03 09:00:00'),
    (4, 4, 'ACTIVE', '2026-07-04 09:00:00', '2026-06-28 09:00:00', '2026-07-04 09:00:00'),
    (5, 5, 'ACTIVE', '2026-07-05 09:00:00', '2026-06-29 09:00:00', '2026-07-05 09:00:00'),
    (6, 6, 'SUSPENDED', '2026-07-06 09:00:00', '2026-06-30 09:00:00', '2026-07-20 09:00:00'),
    (7, 7, 'ACTIVE', '2026-07-07 09:00:00', '2026-07-01 09:00:00', '2026-07-07 09:00:00'),
    (8, 8, 'ACTIVE', '2026-07-08 09:00:00', '2026-07-02 09:00:00', '2026-07-08 09:00:00'),
    (9, 9, 'DISABLED', '2026-07-09 09:00:00', '2026-07-03 09:00:00', '2026-07-25 09:00:00'),
    (10, 10, 'DISABLED', NULL, '2026-07-04 09:00:00', '2026-07-26 09:00:00');

-- =============================================================
-- vendors_conversion_request: 10 registros
-- =============================================================

INSERT INTO vendors_conversion_request
    (id, client_id, operation_id, amount_minor, status, expires_at,
     completed_at, created_at, updated_at)
VALUES
    (1, 1, '10000000-0000-0000-0000-000000000001', 10000,
     'COMPLETED_BY_VENDOR', '2026-07-30 09:05:00', '2026-07-30 09:03:00',
     '2026-07-30 09:00:00', '2026-07-30 09:03:00'),
    (2, 2, '10000000-0000-0000-0000-000000000002', 8000,
     'IN_PROGRESS', '2026-07-30 09:10:00', NULL,
     '2026-07-30 09:05:00', '2026-07-30 09:06:00'),
    (3, 3, '10000000-0000-0000-0000-000000000003', 5000,
     'PENDING', '2026-07-30 09:15:00', NULL,
     '2026-07-30 09:10:00', '2026-07-30 09:10:00'),
    (4, 1, '10000000-0000-0000-0000-000000000004', 12000,
     'CANCELLED', '2026-07-30 09:20:00', '2026-07-30 09:17:00',
     '2026-07-30 09:15:00', '2026-07-30 09:17:00'),
    (5, 2, '10000000-0000-0000-0000-000000000005', 15000,
     'EXPIRED', '2026-07-30 09:25:00', '2026-07-30 09:25:00',
     '2026-07-30 09:20:00', '2026-07-30 09:25:00'),
    (6, 3, '10000000-0000-0000-0000-000000000006', 9000,
     'COMPLETED_BY_PLATFORM', '2026-07-30 09:30:00', '2026-07-30 09:29:00',
     '2026-07-30 09:25:00', '2026-07-30 09:29:00'),
    (7, 1, '10000000-0000-0000-0000-000000000007', 7000,
     'FAILED_LIQUIDITY', '2026-07-30 09:35:00', '2026-07-30 09:35:00',
     '2026-07-30 09:30:00', '2026-07-30 09:35:00'),
    (8, 2, '10000000-0000-0000-0000-000000000008', 6000,
     'COMPLETED_BY_VENDOR', '2026-07-30 09:40:00', '2026-07-30 09:38:00',
     '2026-07-30 09:35:00', '2026-07-30 09:38:00'),
    (9, 3, '10000000-0000-0000-0000-000000000009', 11000,
     'PENDING', '2026-07-30 09:45:00', NULL,
     '2026-07-30 09:40:00', '2026-07-30 09:40:00'),
    (10, 1, '10000000-0000-0000-0000-000000000010', 13000,
     'IN_PROGRESS', '2026-07-30 09:50:00', NULL,
     '2026-07-30 09:45:00', '2026-07-30 09:46:00');

-- =============================================================
-- vendors_conversion_assignment: 10 registros
-- =============================================================

INSERT INTO vendors_conversion_assignment
    (id, request_id, vendor_id, status, assigned_at, released_at, completed_at)
VALUES
    (1, 1, 4, 'COMPLETED', '2026-07-30 09:01:00', NULL, '2026-07-30 09:03:00'),
    (2, 2, 5, 'ACTIVE', '2026-07-30 09:06:00', NULL, NULL),
    (3, 3, 4, 'RELEASED', '2026-07-30 09:11:00', '2026-07-30 09:12:00', NULL),
    (4, 4, 5, 'RELEASED', '2026-07-30 09:16:00', '2026-07-30 09:17:00', NULL),
    (5, 5, 4, 'EXPIRED', '2026-07-30 09:21:00', NULL, NULL),
    (6, 6, 5, 'COMPLETED', '2026-07-30 09:26:00', NULL, '2026-07-30 09:29:00'),
    (7, 7, 4, 'EXPIRED', '2026-07-30 09:31:00', NULL, NULL),
    (8, 8, 5, 'COMPLETED', '2026-07-30 09:36:00', NULL, '2026-07-30 09:38:00'),
    (9, 9, 4, 'RELEASED', '2026-07-30 09:41:00', '2026-07-30 09:42:00', NULL),
    (10, 10, 5, 'ACTIVE', '2026-07-30 09:46:00', NULL, NULL);

-- =============================================================
-- lottery_product: 3 registros
-- Excepción razonable: solo existen tres productos canónicos.
-- =============================================================

INSERT INTO lottery_product
    (id, code, name, allowed_symbols, selection_count, is_active,
     created_at, updated_at)
VALUES
    (1, 'OCTAL', 'Lotería Octal', '01234567', 4, TRUE,
     '2026-07-01 10:00:00', '2026-07-01 10:00:00'),
    (2, 'DECIMAL', 'Lotería Decimal', '0123456789', 5, TRUE,
     '2026-07-01 10:01:00', '2026-07-01 10:01:00'),
    (3, 'HEXADECIMAL', 'Lotería Hexadecimal', '0123456789ABCDEF', 6, TRUE,
     '2026-07-01 10:02:00', '2026-07-01 10:02:00');

-- =============================================================
-- lottery_draw_event: 10 registros
-- Todos cierran exactamente 10 minutos antes de draw_at.
-- =============================================================

INSERT INTO lottery_draw_event
    (id, product_id, name, sales_open_at, sales_close_at, draw_at,
     price_minor, prize_minor, status, cancellation_reason,
     created_at, updated_at)
VALUES
    (1, 1, 'Octal Demo 01', '2026-07-20 08:00:00', '2026-07-30 09:50:00',
     '2026-07-30 10:00:00', 500, 50000, 'RESULT_SET', NULL,
     '2026-07-20 08:00:00', '2026-07-30 10:05:00'),
    (2, 2, 'Decimal Demo 01', '2026-07-20 08:00:00', '2026-07-30 10:50:00',
     '2026-07-30 11:00:00', 700, 70000, 'RESULT_SET', NULL,
     '2026-07-20 08:00:00', '2026-07-30 11:05:00'),
    (3, 3, 'Hexadecimal Demo 01', '2026-07-20 08:00:00', '2026-07-30 11:50:00',
     '2026-07-30 12:00:00', 900, 90000, 'RESULT_SET', NULL,
     '2026-07-20 08:00:00', '2026-07-30 12:05:00'),
    (4, 1, 'Octal Demo 02', '2026-07-21 08:00:00', '2026-07-31 09:50:00',
     '2026-07-31 10:00:00', 500, 50000, 'FINISHED', NULL,
     '2026-07-21 08:00:00', '2026-07-31 10:10:00'),
    (5, 2, 'Decimal Demo 02', '2026-07-21 08:00:00', '2026-07-31 10:50:00',
     '2026-07-31 11:00:00', 700, 70000, 'FINISHED', NULL,
     '2026-07-21 08:00:00', '2026-07-31 11:10:00'),
    (6, 3, 'Hexadecimal Demo 02', '2026-07-21 08:00:00', '2026-07-31 11:50:00',
     '2026-07-31 12:00:00', 900, 90000, 'FINISHED', NULL,
     '2026-07-21 08:00:00', '2026-07-31 12:10:00'),
    (7, 1, 'Octal Demo 03', '2026-07-22 08:00:00', '2026-08-01 09:50:00',
     '2026-08-01 10:00:00', 500, 50000, 'RESULT_SET', NULL,
     '2026-07-22 08:00:00', '2026-08-01 10:05:00'),
    (8, 2, 'Decimal Demo 03', '2026-07-22 08:00:00', '2026-08-01 10:50:00',
     '2026-08-01 11:00:00', 700, 70000, 'RESULT_SET', NULL,
     '2026-07-22 08:00:00', '2026-08-01 11:05:00'),
    (9, 3, 'Hexadecimal Demo 03', '2026-07-22 08:00:00', '2026-08-01 11:50:00',
     '2026-08-01 12:00:00', 900, 90000, 'RESULT_SET', NULL,
     '2026-07-22 08:00:00', '2026-08-01 12:05:00'),
    (10, 1, 'Octal Demo 04', '2026-07-23 08:00:00', '2026-08-02 09:50:00',
     '2026-08-02 10:00:00', 500, 50000, 'RESULT_SET', NULL,
     '2026-07-23 08:00:00', '2026-08-02 10:05:00');

-- =============================================================
-- lottery_ticket: 10 registros
-- Las claves están normalizadas, ordenadas y sin repetidos.
-- =============================================================

INSERT INTO lottery_ticket
    (id, user_id, event_id, operation_id, normalized_key, price_minor,
     ownership_status, evaluation_status, award_minor, credited_at, created_at)
VALUES
    (1, 1, 1, '20000000-0000-0000-0000-000000000001', '0247', 500,
     'ACTIVE', 'WINNER', 50000, '2026-07-30 10:06:00', '2026-07-30 09:00:00'),
    (2, 2, 2, '20000000-0000-0000-0000-000000000002', '01259', 700,
     'ACTIVE', 'WINNER', 70000, '2026-07-30 11:06:00', '2026-07-30 09:05:00'),
    (3, 3, 3, '20000000-0000-0000-0000-000000000003', '012ABF', 900,
     'ACTIVE', 'WINNER', 90000, '2026-07-30 12:06:00', '2026-07-30 09:10:00'),
    (4, 1, 4, '20000000-0000-0000-0000-000000000004', '1357', 500,
     'ACTIVE', 'NOT_WINNER', 0, NULL, '2026-07-31 09:00:00'),
    (5, 2, 5, '20000000-0000-0000-0000-000000000005', '13468', 700,
     'ACTIVE', 'REFUND', 700, '2026-07-31 11:06:00', '2026-07-31 09:05:00'),
    (6, 3, 6, '20000000-0000-0000-0000-000000000006', '345BCD', 900,
     'ACTIVE', 'NOT_WINNER', 0, NULL, '2026-07-31 09:10:00'),
    (7, 1, 7, '20000000-0000-0000-0000-000000000007', '0123', 500,
     'ACTIVE', 'WINNER', 50000, '2026-08-01 10:06:00', '2026-08-01 09:00:00'),
    (8, 2, 8, '20000000-0000-0000-0000-000000000008', '02479', 700,
     'ACTIVE', 'WINNER', 70000, '2026-08-01 11:06:00', '2026-08-01 09:05:00'),
    (9, 3, 9, '20000000-0000-0000-0000-000000000009', '456DEF', 900,
     'ACTIVE', 'WINNER', 90000, '2026-08-01 12:06:00', '2026-08-01 09:10:00'),
    (10, 1, 10, '20000000-0000-0000-0000-000000000010', '0256', 500,
     'ACTIVE', 'WINNER', 50000, '2026-08-02 10:06:00', '2026-08-02 09:00:00');

-- =============================================================
-- lottery_draw_result: 10 registros
-- Uno por evento y todos coherentes con el estado del evento.
-- =============================================================

INSERT INTO lottery_draw_result
    (id, event_id, winning_key, published_by_id, reason, published_at)
VALUES
    (1, 1, '0247', 7, 'Resultado académico Octal 01', '2026-07-30 10:05:00'),
    (2, 2, '01259', 7, 'Resultado académico Decimal 01', '2026-07-30 11:05:00'),
    (3, 3, '012ABF', 8, 'Resultado académico Hexadecimal 01', '2026-07-30 12:05:00'),
    (4, 4, '0246', 7, 'Resultado académico Octal 02', '2026-07-31 10:05:00'),
    (5, 5, '13467', 8, 'Resultado académico Decimal 02', '2026-07-31 11:05:00'),
    (6, 6, '012CDE', 7, 'Resultado académico Hexadecimal 02', '2026-07-31 12:05:00'),
    (7, 7, '0123', 8, 'Resultado académico Octal 03', '2026-08-01 10:05:00'),
    (8, 8, '02479', 7, 'Resultado académico Decimal 03', '2026-08-01 11:05:00'),
    (9, 9, '456DEF', 8, 'Resultado académico Hexadecimal 03', '2026-08-01 12:05:00'),
    (10, 10, '0256', 7, 'Resultado académico Octal 04', '2026-08-02 10:05:00');

COMMIT;

-- Conteo rápido al terminar la carga
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
