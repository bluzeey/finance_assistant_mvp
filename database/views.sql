CREATE OR REPLACE VIEW v_posted_vendor_spend AS
SELECT
  t.transaction_id,
  t.company_id,
  t.posting_date,
  t.vendor_id,
  v.display_name AS vendor_name,
  v.vendor_category,
  t.account_code,
  coa.account_name,
  coa.account_type,
  t.department,
  t.cost_center,
  t.project_code,
  t.signed_amount,
  t.currency,
  t.is_reversal,
  t.reverses_transaction_id,
  t.reference_number,
  t.description,
  t.source_system,
  t.ingested_at
FROM transactions t
JOIN vendors v USING (vendor_id)
JOIN chart_of_accounts coa USING (account_code)
WHERE t.status = 'posted'
  AND coa.account_type IN ('Expense','COGS');

CREATE OR REPLACE VIEW v_completed_vendor_payouts AS
SELECT
  p.payout_id,
  p.company_id,
  p.payout_date,
  p.vendor_id,
  v.display_name AS vendor_name,
  v.vendor_category,
  p.invoice_transaction_id,
  p.gross_amount,
  p.fee_amount,
  p.net_cash_outflow,
  p.currency,
  p.payment_method,
  p.bank_reference,
  p.invoice_reference,
  p.source_system,
  p.created_at
FROM vendor_payouts p
JOIN vendors v USING (vendor_id)
WHERE p.payout_status = 'completed';

CREATE OR REPLACE VIEW v_open_reconciliation AS
SELECT
  r.reconciliation_id,
  r.company_id,
  r.transaction_id,
  t.posting_date,
  t.vendor_id,
  v.display_name AS vendor_name,
  t.account_code,
  coa.account_name,
  t.department,
  t.reference_number,
  abs(t.signed_amount) AS transaction_absolute_amount,
  r.reconciled_amount,
  r.unreconciled_amount,
  r.status,
  r.reason_code,
  r.owner,
  r.last_reviewed_at,
  t.currency
FROM reconciliation_status r
JOIN transactions t USING (transaction_id)
JOIN vendors v USING (vendor_id)
JOIN chart_of_accounts coa USING (account_code)
WHERE t.status = 'posted'
  AND r.status IN ('unreconciled','partially_reconciled','disputed');

CREATE OR REPLACE VIEW v_reconciliation_coverage AS
SELECT
  t.company_id,
  count(*) FILTER (WHERE t.status = 'posted') AS posted_transaction_count,
  count(r.transaction_id) FILTER (WHERE t.status = 'posted') AS posted_with_reconciliation_count,
  count(*) FILTER (WHERE t.status = 'posted' AND r.transaction_id IS NULL) AS missing_reconciliation_count,
  round(
    100.0 * count(r.transaction_id) FILTER (WHERE t.status = 'posted')
    / NULLIF(count(*) FILTER (WHERE t.status = 'posted'), 0),
    2
  ) AS coverage_percent
FROM transactions t
LEFT JOIN reconciliation_status r USING (transaction_id)
GROUP BY t.company_id;
