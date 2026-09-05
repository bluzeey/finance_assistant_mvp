-- Query-supporting indexes for the allow-listed finance assistant query catalogue.
-- Run after database/schema.sql. Do not create indexes by concatenating model output.

CREATE INDEX `idx_account_bank_code`
    ON `account` (`bank_code`);

CREATE INDEX `idx_account_entity_id`
    ON `account` (`entity_id`);

CREATE INDEX `idx_account_program_id`
    ON `account` (`program_id`);

CREATE INDEX `idx_account_bank_program`
    ON `account` (`bank_code`, `program_id`, `account_id`);

CREATE INDEX `idx_transaction_account_date`
    ON `transaction` (`account_id`, `transaction_date`, `transaction_id`);

CREATE INDEX `idx_transaction_date_type`
    ON `transaction` (`transaction_date`, `transaction_type`, `account_id`);

CREATE INDEX `idx_transaction_type_date_amount`
    ON `transaction` (`transaction_type`, `transaction_date`, `transaction_amount`);

CREATE INDEX `idx_transaction_reference_id`
    ON `transaction` (`transaction_reference_id`);

-- Optional for literal/natural-language narration search. FULLTEXT behavior is not
-- equivalent to an authoritative vendor dimension and all such answers remain qualified.
CREATE FULLTEXT INDEX `idx_transaction_description_fulltext`
    ON `transaction` (`description`);
