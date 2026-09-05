# Schema Migration Summary — Organiser Three-Table Contract

## Why this migration was necessary

The initial hackathon planning bundle modelled richer concepts such as vendors, payouts,
reconciliation records and a chart of accounts. The organiser subsequently supplied the actual
source contract: MySQL tables `bank`, `account`, and `transaction`. This migration removes the
richer-schema assumptions from data, contracts, tests, product pages and agent backlog.

## Source changes

| Before planning assumption | Current source-aligned state |
|---|---|
| PostgreSQL-oriented source | MySQL 8.4 / InnoDB / utf8mb4 |
| Multiple finance dimensions | Exactly bank → account → transaction |
| Vendor/payout records | Not present; unsupported |
| Reconciliation status | Not present; unsupported |
| Chart of accounts/category | Not present; unsupported |
| Historical balance | Not present; current `available_balance` snapshot only |
| Generic reference interpretation | Bare reference maps to plaintext `transaction_reference_id` |
| UUID validation | IDs are opaque `VARCHAR(36)` because one supplied value is malformed as UUID |

## Data replacement

Removed obsolete fixture concepts and generated:

- 10 canonical banks;
- 30 accounts, including all 10 supplied examples;
- 2,426 transactions, including all 10 supplied examples;
- 16-field data dictionary;
- 16 targeted edge records;
- 30 single-turn gold cases and five multi-turn conversations.

All generated data is deterministic under seed `20260903` and version
`tiby-finance-fixture-v2.0.0`.

## Product-scope replacement

Supported product areas are:

- debit/credit totals, counts, average, largest and net flow;
- grouping/ranking by bank, program, account, entity and time;
- exact transaction/reference lookup;
- qualified literal narration search;
- current account balances and account counts;
- source records, receipts, export, data health and evaluation.

Vendor payout, reconciliation, accounting category, historical balance and forecast requests must
return an explicit unsupported state with no number.

## Contract replacement

Updated:

- InterpretationDraft, QueryPlan, QueryState, ComputedFacts and AnswerReceipt schemas;
- semantic metric registry;
- OpenAPI paths and source-record serializers;
- MySQL schema/index/query templates;
- React route/page/component contracts;
- Django/DRF query engine and privacy specifications;
- security, evaluation, demo and development runbooks;
- 100-ticket dependency-checked implementation backlog.

## Test replacement

The current static/deterministic suite covers:

- exact supplied-row preservation;
- row counts, foreign keys, enum/decimal/date constraints;
- half-open date ranges and relative-date anchoring;
- debit/credit/net and current-balance gold values;
- exact case-sensitive and duplicate reference behavior;
- literal-description qualification;
- account/UTR masking and narration redaction;
- malicious text preservation as inert text;
- unsupported source concepts;
- MySQL DDL/query/loader dry-run contracts;
- JSON Schema/OpenAPI/semantic parsing;
- backlog dependency DAG and runtime/gold isolation.

The repository reports 34 passing tests in the current environment. A real MySQL integration run is
still required wherever Docker/MySQL is available; `scripts/load_mysql.py --dry-run` validates local
inputs without a server.
