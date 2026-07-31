-- =============================================================
-- 00_validacion_ddl.sql
-- Taller #3 Lotería Binaria con Django
-- Base TEMPORAL de validación del modelo ER en MySQL 8
--
-- IMPORTANTE:
-- 1. Esta NO es la base final del proyecto.
-- 2. La base final será creada por migraciones de Django.
-- 3. No contiene credenciales reales.
-- 4. Después de validar, debe eliminarse:
--      DROP DATABASE IF EXISTS loteria_taller3_validacion;
-- =============================================================

DROP DATABASE IF EXISTS loteria_taller3_validacion;

CREATE DATABASE loteria_taller3_validacion
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE loteria_taller3_validacion;

SET NAMES utf8mb4;
SET time_zone = '-05:00';

-- =============================================================
-- APP: accounts
-- =============================================================

CREATE TABLE accounts_user (
    id BIGINT NOT NULL AUTO_INCREMENT,
    username VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    document VARCHAR(30) NOT NULL,
    phone VARCHAR(30) NULL,
    birth_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),

    CONSTRAINT pk_accounts_user PRIMARY KEY (id),
    CONSTRAINT uq_accounts_user_username UNIQUE (username),
    CONSTRAINT uq_accounts_user_email UNIQUE (email),
    CONSTRAINT uq_accounts_user_document UNIQUE (document),
    CONSTRAINT ck_accounts_user_status CHECK (
        status IN ('ACTIVE', 'SUSPENDED', 'BLOCKED', 'DISABLED')
    )
) ENGINE=InnoDB;

CREATE INDEX ix_accounts_user_status
    ON accounts_user (status);

CREATE TABLE accounts_terms_version (
    id BIGINT NOT NULL AUTO_INCREMENT,
    kind VARCHAR(30) NOT NULL,
    version VARCHAR(30) NOT NULL,
    title VARCHAR(150) NOT NULL,
    content TEXT NOT NULL,
    effective_at DATETIME(6) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    CONSTRAINT pk_accounts_terms_version PRIMARY KEY (id),
    CONSTRAINT uq_accounts_terms_kind_version UNIQUE (kind, version),
    CONSTRAINT ck_accounts_terms_kind CHECK (
        kind IN ('TERMS', 'PRIVACY')
    )
) ENGINE=InnoDB;

CREATE INDEX ix_accounts_terms_effective_at
    ON accounts_terms_version (effective_at);

CREATE TABLE accounts_terms_acceptance (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    terms_version_id BIGINT NOT NULL,
    accepted_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    ip_address VARCHAR(45) NULL,

    CONSTRAINT pk_accounts_terms_acceptance PRIMARY KEY (id),
    CONSTRAINT uq_accounts_acceptance_user_version
        UNIQUE (user_id, terms_version_id),
    CONSTRAINT fk_accounts_acceptance_user
        FOREIGN KEY (user_id)
        REFERENCES accounts_user (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT fk_accounts_acceptance_terms
        FOREIGN KEY (terms_version_id)
        REFERENCES accounts_terms_version (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX ix_accounts_acceptance_accepted_at
    ON accounts_terms_acceptance (accepted_at);

-- =============================================================
-- APP: core
-- =============================================================

CREATE TABLE core_audit_event (
    id BIGINT NOT NULL AUTO_INCREMENT,
    actor_id BIGINT NULL,
    active_mode VARCHAR(20) NULL,
    action VARCHAR(80) NOT NULL,
    resource_type VARCHAR(80) NOT NULL,
    resource_id VARCHAR(64) NOT NULL,
    reason TEXT NULL,
    metadata TEXT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    CONSTRAINT pk_core_audit_event PRIMARY KEY (id),
    CONSTRAINT ck_core_audit_active_mode CHECK (
        active_mode IS NULL
        OR active_mode IN ('CLIENTE', 'VENDEDOR', 'ADMINISTRADOR')
    ),
    CONSTRAINT fk_core_audit_actor
        FOREIGN KEY (actor_id)
        REFERENCES accounts_user (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX ix_core_audit_actor_created
    ON core_audit_event (actor_id, created_at);

CREATE INDEX ix_core_audit_resource
    ON core_audit_event (resource_type, resource_id);

-- =============================================================
-- APP: finance
-- =============================================================

CREATE TABLE finance_wallet (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    currency VARCHAR(10) NOT NULL,
    available_minor BIGINT NOT NULL DEFAULT 0,
    reserved_minor BIGINT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),

    CONSTRAINT pk_finance_wallet PRIMARY KEY (id),
    CONSTRAINT uq_finance_wallet_user_currency
        UNIQUE (user_id, currency),
    CONSTRAINT ck_finance_wallet_currency CHECK (
        currency IN ('REAL', 'VIRTUAL')
    ),
    CONSTRAINT ck_finance_wallet_status CHECK (
        status IN ('ACTIVE', 'BLOCKED', 'CLOSED')
    ),
    CONSTRAINT ck_finance_wallet_available_nonnegative CHECK (
        available_minor >= 0
    ),
    CONSTRAINT ck_finance_wallet_reserved_nonnegative CHECK (
        reserved_minor >= 0
    ),
    CONSTRAINT fk_finance_wallet_user
        FOREIGN KEY (user_id)
        REFERENCES accounts_user (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX ix_finance_wallet_status
    ON finance_wallet (status);

CREATE TABLE finance_movement (
    id BIGINT NOT NULL AUTO_INCREMENT,
    wallet_id BIGINT NOT NULL,
    operation_id VARCHAR(36) NOT NULL,
    type VARCHAR(30) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    amount_minor BIGINT NOT NULL,
    balance_after_minor BIGINT NOT NULL,
    description VARCHAR(255) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    CONSTRAINT pk_finance_movement PRIMARY KEY (id),
    CONSTRAINT ck_finance_movement_type CHECK (
        type IN (
            'TOP_UP',
            'VIRTUAL_TO_REAL',
            'TRANSFER',
            'VENDOR_PURCHASE',
            'REQUEST',
            'TICKET_PURCHASE',
            'PRIZE',
            'REFUND',
            'ADJUSTMENT'
        )
    ),
    CONSTRAINT ck_finance_movement_direction CHECK (
        direction IN ('CREDIT', 'DEBIT')
    ),
    CONSTRAINT ck_finance_movement_amount_positive CHECK (
        amount_minor > 0
    ),
    CONSTRAINT ck_finance_movement_balance_nonnegative CHECK (
        balance_after_minor >= 0
    ),
    CONSTRAINT fk_finance_movement_wallet
        FOREIGN KEY (wallet_id)
        REFERENCES finance_wallet (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX ix_finance_movement_operation
    ON finance_movement (operation_id);

CREATE INDEX ix_finance_movement_wallet_created
    ON finance_movement (wallet_id, created_at);

-- =============================================================
-- APP: vendors
-- =============================================================

CREATE TABLE vendors_vendor_profile (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    activated_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),

    CONSTRAINT pk_vendors_vendor_profile PRIMARY KEY (id),
    CONSTRAINT uq_vendors_vendor_profile_user UNIQUE (user_id),
    CONSTRAINT ck_vendors_vendor_profile_status CHECK (
        status IN ('PENDING', 'ACTIVE', 'SUSPENDED', 'DISABLED')
    ),
    CONSTRAINT fk_vendors_vendor_profile_user
        FOREIGN KEY (user_id)
        REFERENCES accounts_user (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX ix_vendors_vendor_profile_status
    ON vendors_vendor_profile (status);

CREATE TABLE vendors_conversion_request (
    id BIGINT NOT NULL AUTO_INCREMENT,
    client_id BIGINT NOT NULL,
    operation_id VARCHAR(36) NOT NULL,
    amount_minor BIGINT NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'PENDING',
    expires_at DATETIME(6) NOT NULL,
    completed_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),

    CONSTRAINT pk_vendors_conversion_request PRIMARY KEY (id),
    CONSTRAINT uq_vendors_conversion_request_operation
        UNIQUE (operation_id),
    CONSTRAINT ck_vendors_conversion_request_amount_positive CHECK (
        amount_minor > 0
    ),
    CONSTRAINT ck_vendors_conversion_request_status CHECK (
        status IN (
            'PENDING',
            'IN_PROGRESS',
            'COMPLETED_BY_VENDOR',
            'COMPLETED_BY_PLATFORM',
            'CANCELLED',
            'EXPIRED',
            'FAILED_LIQUIDITY'
        )
    ),
    CONSTRAINT ck_vendors_conversion_request_dates CHECK (
        expires_at > created_at
    ),
    CONSTRAINT fk_vendors_conversion_request_client
        FOREIGN KEY (client_id)
        REFERENCES accounts_user (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX ix_vendors_conversion_request_status_expires
    ON vendors_conversion_request (status, expires_at);

CREATE INDEX ix_vendors_conversion_request_client_created
    ON vendors_conversion_request (client_id, created_at);

CREATE TABLE vendors_conversion_assignment (
    id BIGINT NOT NULL AUTO_INCREMENT,
    request_id BIGINT NOT NULL,
    vendor_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    assigned_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    released_at DATETIME(6) NULL,
    completed_at DATETIME(6) NULL,

    CONSTRAINT pk_vendors_conversion_assignment PRIMARY KEY (id),
    CONSTRAINT uq_vendors_assignment_request_vendor_assigned
        UNIQUE (request_id, vendor_id, assigned_at),
    CONSTRAINT ck_vendors_assignment_status CHECK (
        status IN ('ACTIVE', 'RELEASED', 'COMPLETED', 'EXPIRED')
    ),
    CONSTRAINT ck_vendors_assignment_release_date CHECK (
        released_at IS NULL OR released_at >= assigned_at
    ),
    CONSTRAINT ck_vendors_assignment_completed_date CHECK (
        completed_at IS NULL OR completed_at >= assigned_at
    ),
    CONSTRAINT fk_vendors_assignment_request
        FOREIGN KEY (request_id)
        REFERENCES vendors_conversion_request (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT fk_vendors_assignment_vendor
        FOREIGN KEY (vendor_id)
        REFERENCES vendors_vendor_profile (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX ix_vendors_assignment_request_status
    ON vendors_conversion_assignment (request_id, status);

CREATE INDEX ix_vendors_assignment_vendor_status
    ON vendors_conversion_assignment (vendor_id, status);

-- NOTA:
-- La regla "solo una asignación ACTIVE por solicitud" no se implementa
-- con índice parcial porque debe ser portable a SQLite/MySQL.
-- Se controlará posteriormente en services.py con transaction.atomic.

-- =============================================================
-- APP: lottery
-- =============================================================

CREATE TABLE lottery_product (
    id BIGINT NOT NULL AUTO_INCREMENT,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(80) NOT NULL,
    allowed_symbols VARCHAR(32) NOT NULL,
    selection_count INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),

    CONSTRAINT pk_lottery_product PRIMARY KEY (id),
    CONSTRAINT uq_lottery_product_code UNIQUE (code),
    CONSTRAINT ck_lottery_product_code CHECK (
        code IN ('OCTAL', 'DECIMAL', 'HEXADECIMAL')
    ),
    CONSTRAINT ck_lottery_product_selection_count CHECK (
        selection_count > 0
    ),
    CONSTRAINT ck_lottery_product_configuration CHECK (
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
    )
) ENGINE=InnoDB;

CREATE TABLE lottery_draw_event (
    id BIGINT NOT NULL AUTO_INCREMENT,
    product_id BIGINT NOT NULL,
    name VARCHAR(150) NOT NULL,
    sales_open_at DATETIME(6) NOT NULL,
    sales_close_at DATETIME(6) NOT NULL,
    draw_at DATETIME(6) NOT NULL,
    price_minor BIGINT NOT NULL,
    prize_minor BIGINT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
    cancellation_reason TEXT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),

    CONSTRAINT pk_lottery_draw_event PRIMARY KEY (id),
    CONSTRAINT ck_lottery_draw_event_price_positive CHECK (
        price_minor > 0
    ),
    CONSTRAINT ck_lottery_draw_event_prize_nonnegative CHECK (
        prize_minor >= 0
    ),
    CONSTRAINT ck_lottery_draw_event_date_order CHECK (
        sales_open_at < sales_close_at
        AND sales_close_at < draw_at
    ),
    CONSTRAINT ck_lottery_draw_event_close_10_minutes CHECK (
        sales_close_at = DATE_SUB(draw_at, INTERVAL 10 MINUTE)
    ),
    CONSTRAINT ck_lottery_draw_event_status CHECK (
        status IN (
            'DRAFT',
            'SCHEDULED',
            'PUBLISHED',
            'SALES_OPEN',
            'SALES_CLOSED',
            'RESULT_SET',
            'FINISHED',
            'CANCELLED'
        )
    ),
    CONSTRAINT fk_lottery_draw_event_product
        FOREIGN KEY (product_id)
        REFERENCES lottery_product (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX ix_lottery_draw_event_product_status
    ON lottery_draw_event (product_id, status);

CREATE INDEX ix_lottery_draw_event_draw_at
    ON lottery_draw_event (draw_at);

CREATE TABLE lottery_ticket (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    event_id BIGINT NOT NULL,
    operation_id VARCHAR(36) NOT NULL,
    normalized_key VARCHAR(16) NOT NULL,
    price_minor BIGINT NOT NULL,
    ownership_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    evaluation_status VARCHAR(30) NOT NULL DEFAULT 'PENDING_RESULT',
    award_minor BIGINT NOT NULL DEFAULT 0,
    credited_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    CONSTRAINT pk_lottery_ticket PRIMARY KEY (id),
    CONSTRAINT uq_lottery_ticket_operation UNIQUE (operation_id),
    CONSTRAINT uq_lottery_ticket_event_key
        UNIQUE (event_id, normalized_key),
    CONSTRAINT ck_lottery_ticket_price_positive CHECK (
        price_minor > 0
    ),
    CONSTRAINT ck_lottery_ticket_award_nonnegative CHECK (
        award_minor >= 0
    ),
    CONSTRAINT ck_lottery_ticket_ownership_status CHECK (
        ownership_status IN ('ACTIVE', 'REFUNDED', 'CANCELLED')
    ),
    CONSTRAINT ck_lottery_ticket_evaluation_status CHECK (
        evaluation_status IN (
            'PENDING_RESULT',
            'NOT_WINNER',
            'REFUND',
            'WINNER'
        )
    ),
    CONSTRAINT fk_lottery_ticket_user
        FOREIGN KEY (user_id)
        REFERENCES accounts_user (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT fk_lottery_ticket_event
        FOREIGN KEY (event_id)
        REFERENCES lottery_draw_event (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX ix_lottery_ticket_user_created
    ON lottery_ticket (user_id, created_at);

CREATE INDEX ix_lottery_ticket_event_status
    ON lottery_ticket (event_id, evaluation_status);

CREATE TABLE lottery_draw_result (
    id BIGINT NOT NULL AUTO_INCREMENT,
    event_id BIGINT NOT NULL,
    winning_key VARCHAR(16) NOT NULL,
    published_by_id BIGINT NOT NULL,
    reason TEXT NOT NULL,
    published_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    CONSTRAINT pk_lottery_draw_result PRIMARY KEY (id),
    CONSTRAINT uq_lottery_draw_result_event UNIQUE (event_id),
    CONSTRAINT fk_lottery_draw_result_event
        FOREIGN KEY (event_id)
        REFERENCES lottery_draw_event (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT fk_lottery_draw_result_publisher
        FOREIGN KEY (published_by_id)
        REFERENCES accounts_user (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX ix_lottery_draw_result_published_at
    ON lottery_draw_result (published_at);

-- =============================================================
-- Fin del DDL temporal
-- =============================================================

SELECT
    DATABASE() AS base_activa,
    VERSION() AS version_mysql,
    @@character_set_database AS charset_base,
    @@collation_database AS collation_base;
