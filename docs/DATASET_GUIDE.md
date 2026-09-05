# Dataset Guide and Finance Semantics

## 1. Purpose

This repository contains a deterministic, synthetic, single-company finance dataset for developing and evaluating the TBX finance assistant. It is deliberately richer than a clean demo spreadsheet: it includes normal records, incomplete coverage, ambiguous vendor names, credits, reversals, partial reconciliations, failed and pending payouts, duplicate candidates, and hostile text inside a transaction memo.

The dataset is designed to test whether the product can be **accurate, grounded, explainable, and appropriately cautious**. It is not intended to model every accounting workflow or to teach accounting policy.

All organisations, people, references, tax identifiers, invoices, bank references, and financial values are fictitious. Familiar product names are used only to make entity-resolution tests understandable.

## 2. Dataset identity

| Property | Value |
|---|---|
| Company | Northstar Labs India Private Limited |
| Company ID | `CMP-NL-001` |
| Currency | INR only |
| Timezone | Asia/Kolkata |
| Fiscal-year start | April |
| Data as of | 3 September 2026 |
| Generator seed | `20260904` |
| Dataset version | `2026.09.04-hackathon-v1` |
| Runtime scope | One fictitious company, one currency, read-only |

Relative dates must be anchored to `companies.data_as_of` or `data/company_metadata.json:data_as_of`, **not the server clock**. For example:

- “last month” → `[2026-08-01, 2026-09-01)`
- “this month” → `[2026-09-01, 2026-09-04)`
- “last 30 days” → `[2026-08-05, 2026-09-04)`

All internal date ranges are half-open: start is inclusive and `end_exclusive` is excluded. The UI may display the corresponding inclusive human date, such as “1–31 August 2026.”

## 3. Files

### `data/csv/chart_of_accounts.csv`

The chart of accounts. It includes balance-sheet, revenue, cost-of-goods-sold, and operating-expense accounts. The supported spend metric uses only accounts whose `account_type` is `Expense` or `COGS`.

### `data/csv/vendors.csv`

Canonical vendor master. Use `vendor_id` for all filtering and joins. `display_name` and `legal_name` are labels, not safe identifiers.

### `data/csv/vendor_aliases.csv`

Vendor-name resolution table. It contains exact, legal, and common aliases. `normalized_alias` is lowercase and punctuation-normalised. Some aliases intentionally map to more than one vendor:

- `acme` → `V0001` Acme Cloud Services and `V0002` Acme Office Supplies
- `abc` → `V0044` ABC Consulting and `V0045` ABC Telecom

The assistant must ask for clarification when a user supplies one of these ambiguous aliases. A fuzzy match may retrieve candidates, but it must not silently select a vendor when more than one plausible match exists.

### `data/csv/transactions.csv`

Posted, voided, and draft ledger-like transactions. `signed_amount` is positive for expense and negative for credits or reversals. The default vendor-spend metric:

```text
SUM(transactions.signed_amount)
WHERE transactions.status = 'posted'
AND chart_of_accounts.account_type IN ('Expense', 'COGS')
DATE FIELD = transactions.posting_date
```

Do not use floating-point arithmetic. Parse money as `Decimal` in Python and store it as `NUMERIC(18,2)` in PostgreSQL.

### `data/csv/vendor_payouts.csv`

Payout attempts linked to invoice transactions. A payout can be completed, pending, failed, or reversed. The default payout metric is:

```text
SUM(vendor_payouts.gross_amount)
WHERE vendor_payouts.payout_status = 'completed'
DATE FIELD = vendor_payouts.payout_date
```

`fee_amount` is excluded from gross vendor payouts. `net_cash_outflow` includes fee only for completed rows. Pending, failed, and reversed attempts contribute zero to net cash outflow.

### `data/csv/reconciliation_status.csv`

Current reconciliation state for most posted transactions. There is intentionally one posted transaction without a reconciliation row. For open-item metrics, include statuses:

- `unreconciled`
- `partially_reconciled`
- `disputed`

For a partially reconciled item, use `unreconciled_amount`; never count the full transaction amount as open.

### `data/csv/data_dictionary.csv`

Field-level types, nullability, keys, allowed values, examples, and finance semantics. The schema resolver should read a curated semantic configuration in production; this CSV is for people, tests, and the glossary page.

### `data/company_metadata.json`

Company identity, dataset anchor, default metric semantics, and synthetic-data notice.

### `data/dataset_manifest.json`

Dataset version, file hashes, sizes, and row counts. Use this to show data lineage and detect accidental fixture changes.

### Evaluation files

- `evaluation/benchmark_questions.csv` — single-turn gold cases
- `evaluation/benchmark_cases.jsonl` — the same cases in machine-friendly JSONL
- `evaluation/benchmark_conversations.jsonl` — multi-turn, correction, clarification, and reset cases
- `evaluation/expected_aggregates.json` — independently computed gold aggregates
- `evaluation/edge_case_manifest.csv` — planted risk conditions and required behavior
- `evaluation/model_benchmark_results_template.csv` — scorecard for model and prompt experiments

**Separation rule:** application runtime modules must never import or query gold files. Gold data is available only to offline tests/evaluation. Add a test that searches runtime imports and fails if `evaluation/expected_*` is referenced.

## 4. Canonical metrics

### 4.1 Completed vendor payout amount

Use when the user says “vendor payouts,” “paid vendors,” “supplier payouts,” or an equivalent phrase that clearly refers to payment execution.

- Source: `vendor_payouts`
- Value: `SUM(gross_amount)`
- Mandatory status: `completed`
- Date: `payout_date`
- Excludes: pending, failed, reversed, and payment fees

### 4.2 Net cash outflow

Use only when the user asks for cash paid/outflow including payment fees.

- Source: `vendor_payouts`
- Value: `SUM(net_cash_outflow)`
- Mandatory status: `completed`
- Date: `payout_date`

### 4.3 Posted vendor spend

Use for “spend” or “expenses” when the user is asking about recorded financial activity rather than payment execution.

- Source: `transactions` joined to `chart_of_accounts`
- Value: `SUM(signed_amount)`
- Mandatory transaction status: `posted`
- Mandatory account types: `Expense`, `COGS`
- Date: `posting_date`
- Credits and reversals remain included as negative values

The product must disclose this distinction when a question could reasonably mean either ledger spend or payouts.

### 4.4 Open reconciliation amount

- Source: `reconciliation_status` joined to `transactions`
- Value: `SUM(unreconciled_amount)`
- Open statuses: unreconciled, partially reconciled, disputed
- Date for age/period filters: transaction `posting_date` unless explicitly requested otherwise
- Partially reconciled items contribute only their remaining open amount

### 4.5 Open reconciliation count

Count distinct `transaction_id` values in an open reconciliation status. Do not count multiple source rows if the production schema later permits reconciliation history.

### 4.6 Possible duplicate payout candidates

This is a quality warning, not an adjusted financial metric. The reference rule pairs completed payouts that share:

- company
- vendor
- payout date
- gross amount
- and either bank reference or invoice reference

Both records remain in totals unless a human or source system marks one invalid. The assistant must say “possible duplicate,” not “duplicate” as a certainty.

### 4.7 Payout anomaly

The sample rule flags a completed payout when:

- gross amount is at least INR 500,000, and
- amount is at least 3 times that vendor’s historical median completed payout

This is descriptive only. The product must never label a transaction fraudulent solely from this rule.

## 5. Date and period semantics

The parser returns exact dates and the date field used. It may not leave “last month” or “Q2” as raw text for the database layer.

| User phrase | Required behavior |
|---|---|
| last month | Previous complete calendar month relative to `data_as_of` |
| month before | Previous period of matching granularity and duration, based on explicit QueryState |
| this month / MTD | First day of anchor month through `data_as_of` |
| last 30 days | Thirty dates including `data_as_of` |
| recent | Ask: last 7 days, last 30 days, or month-to-date |
| Q2 | Ask calendar or fiscal and ask year if missing |
| calendar Q2 2026 | `[2026-04-01, 2026-07-01)` |
| Q2 FY2027 | `[2026-07-01, 2026-10-01)` because fiscal year starts in April |
| older than 30 days | Strictly earlier than `data_as_of - 30 days`; for this fixture, `< 2026-08-04` |
| August 24 through August 30 | `[2026-08-24, 2026-08-31)` |

Never infer a future range beyond the dataset date without warning. A question can specify a period for which no records exist; that should produce a verified zero only when the relevant dataset is complete for that period. Otherwise return a qualified result or not-answerable state.

## 6. Planted edge cases

| ID | Records | What it tests |
|---|---|---|
| E001 | `V0001`, `V0002` | Ambiguous “Acme” vendor alias |
| E002 | `V0044`, `V0045` | Ambiguous “ABC” vendor alias |
| E003 | `TXN-ANOM-001`, `PAY-ANOM-001` | Explainable outlier callout |
| E004 | `PAY-DUP-001`, `PAY-DUP-002` | Duplicate candidate without silent dedupe |
| E005 | `TXN-REV-ORIG`, `TXN-REV-001`, `PAY-REV-ORIG` | Correct credit/reversal and payout-status treatment |
| E006 | `TXN-PROMPT-001` | Prompt injection inside data |
| E007 | `TXN-MISSING-REC-001` | Missing reconciliation coverage |
| E008 | `TXN-PART-001` | Partial reconciliation uses only open component |
| E009 | `PAY-FAIL-001` | Failed payout excluded from paid amount |
| E010 | `PAY-PEND-001` | Pending payout excluded from paid amount and cash outflow |
| E011 | travel window 24–30 Aug | Verified zero versus missing data |
| E012 | `TXN-VOID-001` | Voided zero-value transaction excluded but explorable |

The detailed expected behavior is in `evaluation/edge_case_manifest.csv`.

## 7. Gold values

Do not manually copy gold values into production code. Read them only in tests. The generator computes values from the fixtures, and the validator independently recomputes load-bearing totals. Core values in the generated version include:

- August 2026 completed vendor payout gross: INR 10,000,874.04
- July 2026 completed vendor payout gross: INR 6,930,339.40
- July-to-August change: INR 3,070,534.64, or 44.31%
- August 2026 posted vendor spend, net of credits/reversals: INR 10,147,850.99
- August 2026 completed AWS payouts: INR 1,655,853.90
- Open reconciliation count: 133
- Open reconciliation amount: INR 20,509,837.53
- `TXN-PART-001` remaining open amount: INR 200,000.00
- Unreconciled travel items from 24–30 August: zero

The authoritative file is `evaluation/expected_aggregates.json`; values above will change if the generator changes.

## 8. Regeneration and validation

From the repository root:

```bash
python scripts/generate_dataset.py
python scripts/validate_dataset.py
```

The generator is deterministic. Re-running it with the same source and seed should produce identical CSV content. If a fixture changes intentionally:

1. bump `dataset_version`;
2. regenerate files;
3. run validation;
4. inspect gold changes;
5. update affected benchmark notes and demo screenshots;
6. never change expected values merely to make a broken query pass.

## 9. Loading PostgreSQL

```bash
export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/finance_assistant'
python scripts/load_postgres.py --truncate
```

The script creates tables, loads CSVs with PostgreSQL `COPY`, and installs views and indexes. Application credentials should use a read-only role. The loader/migration role is separate.

## 10. Scale testing

Do not put 20 million rows in Git. Use `scripts/generate_scale_fixture.sql` or a dedicated key-remapping generator in a disposable database. The included SQL expands ordinary transaction rows for planner, filter, and cursor-pagination testing. A full relational scale generator should remap transaction, payout, and reconciliation foreign keys together.

Performance acceptance tests should use at least:

- 1,000-row fixture for correctness and local development;
- 100,000 rows for routine query-plan and pagination tests;
- 1–5 million rows for realistic index and export tests;
- up to 20 million rows for final constraint validation when infrastructure permits.

The sample dataset is a correctness fixture, not a performance claim.
