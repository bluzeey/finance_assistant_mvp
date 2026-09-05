-- Finance Assistant source schema supplied for the TBX/Tiby hackathon.
-- MySQL 8.0+ / InnoDB / utf8mb4.
-- IMPORTANT: `transaction` is a SQL keyword. Quote it with backticks in every raw SQL query.
-- The product must not add finance facts through inferred vendor/reconciliation tables.

SET NAMES utf8mb4;
SET time_zone = '+05:30';

CREATE TABLE IF NOT EXISTS `bank` (
    `bank_code` VARCHAR(10)  PRIMARY KEY,
    `bank_name` VARCHAR(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `account` (
    `account_id`        VARCHAR(36)  PRIMARY KEY,
    `entity_id`         VARCHAR(36)  NOT NULL,
    `account_number`    VARCHAR(20)  NOT NULL,
    `program_id`        INT          NOT NULL,
    `available_balance` DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    `bank_code`         VARCHAR(10)  NOT NULL,
    CONSTRAINT `fk_account_bank`
        FOREIGN KEY (`bank_code`) REFERENCES `bank` (`bank_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `transaction` (
    `transaction_id`           VARCHAR(36)  PRIMARY KEY,
    `account_id`               VARCHAR(36)  NOT NULL,
    `transaction_date`         TIMESTAMP(6) NOT NULL,
    `transaction_type`         ENUM('credit','debit') NOT NULL,
    `description`              VARCHAR(500) DEFAULT NULL,
    `transaction_amount`       DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    `transaction_reference_id` VARCHAR(64)  DEFAULT NULL,
    `utr_number`               VARCHAR(256) DEFAULT NULL,
    CONSTRAINT `fk_transaction_account`
        FOREIGN KEY (`account_id`) REFERENCES `account` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
