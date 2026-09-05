-- PostgreSQL 15+ reference schema for the synthetic Northstar Labs dataset.
-- Money is NUMERIC(18,2), never FLOAT/REAL/DOUBLE PRECISION.
BEGIN;

CREATE TABLE IF NOT EXISTS companies (
  company_id TEXT PRIMARY KEY,
  legal_name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  currency CHAR(3) NOT NULL CHECK (currency = 'INR'),
  timezone TEXT NOT NULL,
  fiscal_year_start_month SMALLINT NOT NULL CHECK (fiscal_year_start_month BETWEEN 1 AND 12),
  data_as_of DATE NOT NULL,
  generated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS chart_of_accounts (
  account_code TEXT PRIMARY KEY,
  account_name TEXT NOT NULL,
  account_type TEXT NOT NULL CHECK (account_type IN ('Asset','Liability','Equity','Revenue','COGS','Expense')),
  parent_account_code TEXT NULL REFERENCES chart_of_accounts(account_code),
  normal_balance TEXT NOT NULL CHECK (normal_balance IN ('Debit','Credit')),
  statement TEXT NOT NULL CHECK (statement IN ('Balance Sheet','Income Statement')),
  is_active BOOLEAN NOT NULL,
  description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vendors (
  vendor_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  display_name TEXT NOT NULL,
  legal_name TEXT NOT NULL,
  vendor_category TEXT NOT NULL,
  default_account_code TEXT NOT NULL REFERENCES chart_of_accounts(account_code),
  payment_terms_days INTEGER NOT NULL CHECK (payment_terms_days BETWEEN 0 AND 365),
  currency CHAR(3) NOT NULL CHECK (currency = 'INR'),
  country TEXT NOT NULL,
  state TEXT NULL,
  tax_id TEXT NOT NULL,
  risk_rating TEXT NOT NULL CHECK (risk_rating IN ('Low','Medium','High')),
  is_active BOOLEAN NOT NULL,
  active_from DATE NOT NULL,
  active_to DATE NULL,
  synthetic_data_notice TEXT NOT NULL,
  CONSTRAINT vendors_dates_valid CHECK (active_to IS NULL OR active_to >= active_from)
);

CREATE TABLE IF NOT EXISTS vendor_aliases (
  alias_id TEXT PRIMARY KEY,
  vendor_id TEXT NOT NULL REFERENCES vendors(vendor_id),
  alias TEXT NOT NULL,
  normalized_alias TEXT NOT NULL,
  alias_type TEXT NOT NULL CHECK (alias_type IN ('display_name','legal_name','common_alias')),
  is_ambiguous BOOLEAN NOT NULL,
  ambiguous_group TEXT NULL,
  notes TEXT NULL,
  CONSTRAINT alias_ambiguity_consistent CHECK (
    (is_ambiguous AND ambiguous_group IS NOT NULL) OR
    (NOT is_ambiguous AND ambiguous_group IS NULL)
  )
);

CREATE TABLE IF NOT EXISTS transactions (
  transaction_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  transaction_date DATE NOT NULL,
  posting_date DATE NOT NULL,
  document_date DATE NOT NULL,
  due_date DATE NOT NULL,
  transaction_type TEXT NOT NULL CHECK (transaction_type IN ('vendor_invoice','vendor_credit','expense','refund','adjustment','reversal')),
  status TEXT NOT NULL CHECK (status IN ('posted','voided','draft')),
  vendor_id TEXT NOT NULL REFERENCES vendors(vendor_id),
  merchant_name_raw TEXT NOT NULL,
  account_code TEXT NOT NULL REFERENCES chart_of_accounts(account_code),
  department TEXT NOT NULL CHECK (department IN ('Engineering','Product','Design','Finance','Operations','Sales','Marketing','People','Leadership')),
  cost_center TEXT NOT NULL,
  project_code TEXT NOT NULL,
  description TEXT NOT NULL,
  reference_number TEXT NOT NULL,
  signed_amount NUMERIC(18,2) NOT NULL,
  currency CHAR(3) NOT NULL CHECK (currency = 'INR'),
  is_reversal BOOLEAN NOT NULL,
  reverses_transaction_id TEXT NULL REFERENCES transactions(transaction_id) DEFERRABLE INITIALLY DEFERRED,
  source_system TEXT NOT NULL CHECK (source_system IN ('ERP','AP Automation','Corporate Card','Bank Import')),
  ingestion_batch_id TEXT NOT NULL,
  ingested_at TIMESTAMPTZ NOT NULL,
  CONSTRAINT reversal_link_consistent CHECK (
    (is_reversal AND reverses_transaction_id IS NOT NULL) OR
    (NOT is_reversal AND reverses_transaction_id IS NULL)
  )
);

CREATE TABLE IF NOT EXISTS vendor_payouts (
  payout_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  vendor_id TEXT NOT NULL REFERENCES vendors(vendor_id),
  invoice_transaction_id TEXT NOT NULL REFERENCES transactions(transaction_id),
  scheduled_date DATE NOT NULL,
  payout_date DATE NULL,
  payout_status TEXT NOT NULL CHECK (payout_status IN ('completed','pending','failed','reversed')),
  gross_amount NUMERIC(18,2) NOT NULL CHECK (gross_amount >= 0),
  fee_amount NUMERIC(18,2) NOT NULL CHECK (fee_amount >= 0),
  net_cash_outflow NUMERIC(18,2) NOT NULL CHECK (net_cash_outflow >= 0),
  currency CHAR(3) NOT NULL CHECK (currency = 'INR'),
  payment_method TEXT NOT NULL CHECK (payment_method IN ('NEFT','RTGS','IMPS','Corporate Card','UPI','ACH')),
  bank_reference TEXT NULL,
  invoice_reference TEXT NOT NULL,
  failure_reason TEXT NULL,
  source_system TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  CONSTRAINT payout_dates_valid CHECK (
    (payout_status = 'pending' AND payout_date IS NULL) OR
    (payout_status <> 'pending' AND payout_date IS NOT NULL)
  ),
  CONSTRAINT payout_cash_semantics CHECK (
    (payout_status = 'completed' AND net_cash_outflow = gross_amount + fee_amount) OR
    (payout_status <> 'completed' AND net_cash_outflow = 0)
  )
);

CREATE TABLE IF NOT EXISTS reconciliation_status (
  reconciliation_id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  transaction_id TEXT NOT NULL UNIQUE REFERENCES transactions(transaction_id),
  reconciliation_type TEXT NOT NULL CHECK (reconciliation_type IN ('bank_to_ledger','invoice_to_payout','card_to_receipt')),
  status TEXT NOT NULL CHECK (status IN ('reconciled','unreconciled','partially_reconciled','disputed')),
  reconciled_amount NUMERIC(18,2) NOT NULL CHECK (reconciled_amount >= 0),
  unreconciled_amount NUMERIC(18,2) NOT NULL CHECK (unreconciled_amount >= 0),
  currency CHAR(3) NOT NULL CHECK (currency = 'INR'),
  matched_record_count INTEGER NOT NULL CHECK (matched_record_count >= 0),
  bank_statement_reference TEXT NULL,
  matched_on DATE NULL,
  reason_code TEXT NULL,
  owner TEXT NOT NULL,
  notes TEXT NOT NULL,
  last_reviewed_at TIMESTAMPTZ NOT NULL,
  CONSTRAINT reconciliation_status_consistent CHECK (
    (status = 'reconciled' AND unreconciled_amount = 0) OR
    (status <> 'reconciled' AND unreconciled_amount >= 0)
  )
);

CREATE TABLE IF NOT EXISTS conversations (
  conversation_id UUID PRIMARY KEY,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  title TEXT NOT NULL,
  query_state JSONB NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversation_turns (
  turn_id UUID PRIMARY KEY,
  conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
  turn_number INTEGER NOT NULL CHECK (turn_number > 0),
  user_message TEXT NOT NULL,
  query_plan JSONB NULL,
  answer_receipt JSONB NOT NULL,
  prompt_version TEXT NOT NULL,
  model_id TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (conversation_id, turn_number)
);

CREATE TABLE IF NOT EXISTS query_audit_log (
  query_id UUID PRIMARY KEY,
  conversation_id UUID NULL REFERENCES conversations(conversation_id) ON DELETE SET NULL,
  turn_id UUID NULL REFERENCES conversation_turns(turn_id) ON DELETE SET NULL,
  company_id TEXT NOT NULL REFERENCES companies(company_id),
  canonical_query_plan JSONB NOT NULL,
  compiled_query_name TEXT NOT NULL,
  compiled_parameters JSONB NOT NULL,
  source_row_count INTEGER NOT NULL,
  source_row_ids_hash TEXT NOT NULL,
  validation_checks JSONB NOT NULL,
  duration_ms INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMIT;
