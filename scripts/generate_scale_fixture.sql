-- Optional performance fixture. Run only in a disposable database after loading the base data.
-- It copies ordinary generated rows while preserving planted edge-case rows and produces
-- roughly :multiplier times the base size. Replace 100 with the desired multiplier.
-- Do not commit a 20M-row CSV to the repository.
DO $$
DECLARE
  multiplier integer := 100;
BEGIN
  INSERT INTO transactions (
    transaction_id, company_id, transaction_date, posting_date, document_date, due_date,
    transaction_type, status, vendor_id, merchant_name_raw, account_code, department,
    cost_center, project_code, description, reference_number, signed_amount, currency,
    is_reversal, reverses_transaction_id, source_system, ingestion_batch_id, ingested_at
  )
  SELECT
    'SCALE-' || gs || '-' || t.transaction_id,
    t.company_id,
    t.transaction_date,
    t.posting_date,
    t.document_date,
    t.due_date,
    t.transaction_type,
    t.status,
    t.vendor_id,
    t.merchant_name_raw,
    t.account_code,
    t.department,
    t.cost_center,
    t.project_code,
    t.description,
    'SCALE-' || gs || '-' || t.reference_number,
    t.signed_amount,
    t.currency,
    false,
    NULL,
    t.source_system,
    'SCALE-' || gs || '-' || t.ingestion_batch_id,
    t.ingested_at
  FROM transactions t
  CROSS JOIN generate_series(1, multiplier - 1) gs
  WHERE t.transaction_id ~ '^TXN-[0-9]{6}$';
END $$;

ANALYZE transactions;
-- For end-to-end payout and reconciliation load tests, use a dedicated generator that
-- remaps all foreign keys. This lightweight fixture is intended for transaction-query
-- planner and pagination benchmarks only.
