-- Index strategy for the scored domain and a future 20M-row dataset.
-- Build concurrently in production migrations; ordinary CREATE is simpler for hackathon setup.
CREATE INDEX IF NOT EXISTS idx_transactions_company_posted_date
  ON transactions (company_id, posting_date DESC, transaction_id)
  WHERE status = 'posted';
CREATE INDEX IF NOT EXISTS idx_transactions_company_vendor_posted_date
  ON transactions (company_id, vendor_id, posting_date DESC, transaction_id)
  WHERE status = 'posted';
CREATE INDEX IF NOT EXISTS idx_transactions_company_account_posted_date
  ON transactions (company_id, account_code, posting_date DESC, transaction_id)
  WHERE status = 'posted';
CREATE INDEX IF NOT EXISTS idx_transactions_reversal_link
  ON transactions (reverses_transaction_id)
  WHERE reverses_transaction_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_payouts_company_completed_date
  ON vendor_payouts (company_id, payout_date DESC, payout_id)
  INCLUDE (vendor_id, gross_amount, fee_amount, net_cash_outflow)
  WHERE payout_status = 'completed';
CREATE INDEX IF NOT EXISTS idx_payouts_company_vendor_completed_date
  ON vendor_payouts (company_id, vendor_id, payout_date DESC, payout_id)
  INCLUDE (gross_amount, net_cash_outflow)
  WHERE payout_status = 'completed';
CREATE INDEX IF NOT EXISTS idx_payouts_duplicate_signals
  ON vendor_payouts (company_id, vendor_id, payout_date, gross_amount, bank_reference, invoice_reference);
CREATE INDEX IF NOT EXISTS idx_reconciliation_open
  ON reconciliation_status (company_id, status, transaction_id)
  INCLUDE (unreconciled_amount, reason_code, last_reviewed_at)
  WHERE status IN ('unreconciled','partially_reconciled','disputed');
CREATE INDEX IF NOT EXISTS idx_alias_normalized
  ON vendor_aliases (normalized_alias, vendor_id);
CREATE INDEX IF NOT EXISTS idx_conversation_turns_order
  ON conversation_turns (conversation_id, turn_number);
CREATE INDEX IF NOT EXISTS idx_query_audit_created
  ON query_audit_log (company_id, created_at DESC);
