-- Disposable MySQL scale-test helper. Run only in a throwaway database after loading the
-- base fixture. It duplicates source rows with deterministic IDs up to the requested size.
-- This is not a substitute for a measured production benchmark.

-- Example: create 10 copies of every transaction (~24K rows).
SET @copies = 10;

WITH RECURSIVE sequence AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM sequence WHERE n < @copies
)
INSERT INTO `transaction` (
    `transaction_id`, `account_id`, `transaction_date`, `transaction_type`, `description`,
    `transaction_amount`, `transaction_reference_id`, `utr_number`
)
SELECT
    LEFT(SHA2(CONCAT(t.transaction_id, ':scale:', sequence.n), 256), 36),
    t.account_id,
    TIMESTAMPADD(MICROSECOND, sequence.n, t.transaction_date),
    t.transaction_type,
    t.description,
    t.transaction_amount,
    CASE
        WHEN t.transaction_reference_id IS NULL THEN NULL
        ELSE LEFT(CONCAT(t.transaction_reference_id, '-S', sequence.n), 64)
    END,
    t.utr_number
FROM `transaction` AS t
JOIN sequence
WHERE sequence.n > 1;

-- Measure representative plans with EXPLAIN ANALYZE, cold/warm cache notes, row count,
-- MySQL version, host resources, p50/p95 timings, and query timeout configuration.
