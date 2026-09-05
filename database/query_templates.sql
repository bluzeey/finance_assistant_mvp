-- Reference templates only. Production code should compile typed QueryPlan objects into
-- bound-parameter SQL; never paste user or model text into these statements.
-- MySQL placeholders are shown as %(name)s for Python DB-API adapters.

-- 1. Debit spend for a half-open local-time range.
SELECT
    COALESCE(SUM(t.transaction_amount), 0.00) AS debit_total,
    COUNT(*) AS source_row_count
FROM `transaction` AS t
WHERE t.transaction_type = 'debit'
  AND t.transaction_date >= %(start_inclusive)s
  AND t.transaction_date <  %(end_exclusive)s;

-- 2. Net cash flow. Amounts are absolute; transaction_type supplies direction.
SELECT
    COALESCE(SUM(CASE WHEN t.transaction_type = 'credit' THEN t.transaction_amount ELSE 0.00 END), 0.00)
    - COALESCE(SUM(CASE WHEN t.transaction_type = 'debit' THEN t.transaction_amount ELSE 0.00 END), 0.00)
      AS net_cash_flow,
    COUNT(*) AS source_row_count
FROM `transaction` AS t
WHERE t.transaction_date >= %(start_inclusive)s
  AND t.transaction_date <  %(end_exclusive)s;

-- 3. Debit spend by bank. Only allow-list dimensions may map to GROUP BY clauses.
SELECT
    b.bank_code,
    b.bank_name,
    COALESCE(SUM(t.transaction_amount), 0.00) AS debit_total,
    COUNT(*) AS source_row_count
FROM `transaction` AS t
JOIN `account` AS a ON a.account_id = t.account_id
JOIN `bank` AS b ON b.bank_code = a.bank_code
WHERE t.transaction_type = 'debit'
  AND t.transaction_date >= %(start_inclusive)s
  AND t.transaction_date <  %(end_exclusive)s
GROUP BY b.bank_code, b.bank_name
ORDER BY debit_total DESC, b.bank_code ASC;

-- 4. Current available balance. This is a current account snapshot, not historical.
-- Do not join to transaction before summing: that would multiply balances by row count.
SELECT
    COALESCE(SUM(a.available_balance), 0.00) AS current_available_balance,
    COUNT(*) AS account_count
FROM `account` AS a
WHERE (%(bank_code)s IS NULL OR a.bank_code = %(bank_code)s);

-- For multiple bank codes, the compiler creates one placeholder per validated code;
-- a DB-API parameter cannot safely represent an entire IN-list.

-- 5. Exact plaintext transaction-reference lookup. BINARY prevents a case-insensitive
-- collation from turning a different identifier into a match.
SELECT
    t.transaction_id,
    t.account_id,
    t.transaction_date,
    t.transaction_type,
    t.description,
    t.transaction_amount,
    t.transaction_reference_id,
    t.utr_number,
    a.bank_code,
    a.program_id,
    a.entity_id,
    a.account_number,
    b.bank_name
FROM `transaction` AS t
JOIN `account` AS a ON a.account_id = t.account_id
JOIN `bank` AS b ON b.bank_code = a.bank_code
WHERE t.transaction_reference_id = %(transaction_reference_id)s
  AND BINARY t.transaction_reference_id = BINARY %(transaction_reference_id)s
ORDER BY t.transaction_date DESC, t.transaction_id DESC
LIMIT 100;

-- 6. Literal narration search. This is useful for exploration only and must carry the
-- qualification: description text is not a canonical vendor/payee dimension.
SELECT
    t.transaction_id,
    t.account_id,
    t.transaction_date,
    t.transaction_type,
    t.description,
    t.transaction_amount,
    t.transaction_reference_id
FROM `transaction` AS t
WHERE LOWER(COALESCE(t.description, '')) LIKE CONCAT('%%', LOWER(%(literal_text)s), '%%')
  AND t.transaction_date >= %(start_inclusive)s
  AND t.transaction_date <  %(end_exclusive)s
ORDER BY t.transaction_date DESC, t.transaction_id DESC
LIMIT %(limit)s;

-- 7. Keyset-paginated transaction drill-down. Never calculate official totals from a
-- paginated browser response; totals come from a separate aggregate query/receipt.
SELECT
    t.transaction_id,
    t.account_id,
    t.transaction_date,
    t.transaction_type,
    t.description,
    t.transaction_amount,
    t.transaction_reference_id,
    t.utr_number,
    a.bank_code,
    a.program_id,
    a.entity_id,
    a.account_number,
    b.bank_name
FROM `transaction` AS t
JOIN `account` AS a ON a.account_id = t.account_id
JOIN `bank` AS b ON b.bank_code = a.bank_code
WHERE (t.transaction_date < %(cursor_date)s)
   OR (t.transaction_date = %(cursor_date)s AND t.transaction_id < %(cursor_id)s)
ORDER BY t.transaction_date DESC, t.transaction_id DESC
LIMIT %(page_size)s;

-- 8. Data-health summary for the provided source schema.
SELECT
    COUNT(*) AS transaction_count,
    SUM(t.description IS NULL) AS null_description_count,
    SUM(t.transaction_reference_id IS NULL) AS null_reference_count,
    SUM(t.utr_number IS NULL) AS null_utr_count,
    SUM(t.transaction_amount = 0.00) AS zero_amount_count,
    MIN(t.transaction_date) AS earliest_transaction,
    MAX(t.transaction_date) AS latest_transaction
FROM `transaction` AS t;
