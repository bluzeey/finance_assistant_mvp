# Agent Execution Plan

## 1. Operating principle

Build LedgerProof as a sequence of **grounded vertical slices**. The first correct product is not a
chatbot; it is a manually constructed QueryPlan that executes against MySQL and returns a verified,
privacy-safe AnswerReceipt. Add natural-language parsing only after this deterministic path is exact.

```text
source contract + deterministic fixture
→ MySQL DDL/indexes/loader
→ semantic registry + JSON contracts
→ allow-listed query compiler/executor
→ validation + receipt + privacy mapping
→ DRF API
→ React Ask and evidence UI
→ lightweight parser + resolvers
→ multi-turn state
→ explorer/accounts/data health/export/evaluation
→ performance, accessibility and demo polish
```

The repository is designed for multiple coding agents, but one owner must control each foundational
contract at a time.

## 2. Non-negotiable source contract

Finance facts may be read only from:

- `bank(bank_code, bank_name)`
- `account(account_id, entity_id, account_number, program_id, available_balance, bank_code)`
- `` `transaction`(transaction_id, account_id, transaction_date, transaction_type, description,
  transaction_amount, transaction_reference_id, utr_number) ``

Application tables may persist conversations and receipts, but agents must not add inferred vendor,
payout, reconciliation, category, ledger, invoice or historical-balance facts and then treat them as
source data.

## 3. Work roles

| Role | Owns |
|---|---|
| Product/contract | supported semantics, unsupported boundaries, acceptance evidence |
| Data/database | fixture generator, MySQL DDL/indexes/loader, scale smoke tests |
| Query engine | QueryPlan, compiler, executor, validators, AnswerReceipt |
| Model/resolution | InterpretationDraft, structured prompt, date/entity resolution, benchmark |
| Backend/API | DRF, conversation state, idempotency, records/export/data-health APIs |
| Frontend | React shell, Ask, evidence, Transactions, Accounts, accessibility |
| QA/security/release | privacy scans, gold/E2E/performance tests, demo and packaging |

For a small team, roles can be combined. Ownership is about merge coordination, not headcount.

## 4. Phase 0 — freeze schema, data and contracts

### Goal

A clean checkout can regenerate and validate the exact source-shaped fixture before application code
branches.

### Deliverables

- organiser schema captured in `docs/PROVIDED_DATABASE_SCHEMA.md`;
- deterministic 10-bank, 30-account, 2,426-transaction fixture;
- preserved organiser sample rows;
- 16 planted edge cases;
- data dictionary and manifest with hashes;
- MySQL DDL, indexes and loader;
- semantic registry and JSON/OpenAPI contracts;
- root validation/test commands and CI.

### Exit criteria

```bash
python scripts/generate_dataset.py --check
python scripts/validate_dataset.py
python scripts/validate_repository.py
python -m unittest discover -s tests -v
```

All pass, and MySQL loads 10/30/2,426 rows with no FK failures.

## 5. Phase 1 — deterministic query kernel

### Goal

Return exact values and proof from hand-built QueryPlans with no model dependency.

### Required query families

1. transaction amount total by credit/debit;
2. net cash flow (`credits - debits`);
3. transaction count and average amount;
4. largest transaction;
5. grouped total/count by bank, program, account, entity, type, day or month;
6. previous-period comparison;
7. exact transaction ID lookup;
8. exact case-sensitive `transaction_reference_id` lookup;
9. literal description search with qualification;
10. current available-balance total/account count and grouped views;
11. no-data result;
12. unsupported and clarification response constructors.

### First slice

Use a QueryPlan equivalent to:

```json
{
  "schema_version": "2.0",
  "disposition": "execute",
  "metric": "debit_total",
  "date_range": {
    "start_inclusive": "2026-08-01T00:00:00+05:30",
    "end_exclusive": "2026-09-01T00:00:00+05:30",
    "timezone": "Asia/Kolkata",
    "label": "August 2026",
    "source": "explicit"
  },
  "filters": {"transaction_types": ["debit"]},
  "group_by": [],
  "comparison": null,
  "sort": [],
  "limit": 100,
  "qualifications": [],
  "clarification": null,
  "unsupported_reason": null
}
```

Expected computed facts:

```text
primary_value = 121758278.46
source_row_count = 205
source_account_count = 30
```

### Implementation sequence

1. Implement exact domain enums and QueryPlan validation.
2. Load/version semantic metric definitions.
3. Map every executable combination to a named query template.
4. Use bound parameters and a read-only MySQL transaction.
5. Keep monetary results as Decimal/strings.
6. Capture stable source IDs and source hash.
7. Run required result checks.
8. Construct deterministic answer text and AnswerReceipt.
9. Fetch receipt-bound records with stable cursor ordering.
10. Add gold tests before adding another query family.

### Exit criteria

- 100% parity across executable repository benchmark cases;
- all source hashes and row counts match;
- duplicate-reference behavior is qualified, not arbitrarily collapsed;
- required validation failure returns no official number;
- privacy scan finds no raw account number or UTR.

## 6. Phase 2 — source and assistant APIs

### Goal

Expose a stable DRF contract that React can integrate without depending on implementation details.

### Work

- metadata, banks, accounts, transactions and data-health endpoints;
- message endpoint and persisted app conversation/turn/receipt tables;
- QueryState/context-version endpoint;
- receipt, records and export endpoints;
- cursor codec and stable ordering;
- RFC-style problem details;
- idempotency and cancellation-aware request handling;
- local-only evaluation endpoint.

### Important policies

- source filters are applied before row fetch;
- page size maximum 100 for interactive endpoints;
- account numbers and UTRs are privacy mapped before serializers;
- descriptions are redacted and escaped;
- exports replay a persisted QueryPlan/receipt, not browser state;
- no offset pagination for large transaction paths;
- application table names use `app_` prefix.

### Exit criteria

- OpenAPI contract tests pass;
- exact duplicate request returns same logical result;
- reused idempotency key with different content returns conflict;
- stale context version returns 409;
- records union/hash equals receipt lineage;
- CSV/XLSX totals/counts/privacy equal UI receipt.

## 7. Phase 3 — React trust experience

### Goal

A finance user can ask a question, understand the answer immediately and verify it without leaving
the response.

### Vertical slice

Implement `/ask/:conversationId` with:

- composer and example questions;
- staged progress;
- verified AnswerCard;
- interpretation chips;
- evidence panel with Receipt, Records, Checks, Query and Export;
- all non-answer/error states;
- desktop and 360px mobile behavior.

Then implement:

- `/transactions` with URL-backed filters, exact reference search and record detail;
- `/accounts` with current-snapshot labels and bank/program filters;
- `/data-health`, `/glossary`, `/about`;
- `/evaluation` when real benchmark execution exists.

### Exit criteria

- no browser arithmetic for official amounts;
- decimal strings remain unchanged through rendering;
- stale responses cannot overwrite newer state;
- source text cannot execute HTML/Markdown;
- keyboard and screen-reader flows work;
- unsupported questions display no number, breakdown or misleading export action.

## 8. Phase 4 — lightweight language interpretation

### Goal

Use the smallest evaluated model to transform plain language into a bounded InterpretationDraft,
then use deterministic code for all resolution and execution.

### Pipeline

```text
question + canonical QueryState + source metadata
→ strict model InterpretationDraft
→ JSON-schema validation
→ one bounded repair attempt if syntactically invalid
→ deterministic date/entity/reference resolver
→ QueryPlan execute | clarify | unsupported
```

### Resolver order

1. protected/unsupported concept detection;
2. metric selection;
3. reference-vs-UTR semantics;
4. explicit identifiers and bank aliases;
5. date phrase resolution against data cutoff;
6. filter/group/comparison resolution;
7. ambiguity threshold;
8. QueryPlan semantic validation.

### Exit criteria

- model benchmark meets gates in `MODEL_EVALUATION_PLAN.md`;
- hallucinated fields/operators are rejected;
- parser never sees raw sensitive values;
- no SQL or numeric answer appears in model output contract;
- model outage produces a safe typed error or limited deterministic fallback.

## 9. Phase 5 — multi-turn state

### Goal

Follow-up questions change only the intended dimensions and remain auditable.

### State operations

- inherit prior metric/filter/date;
- add or replace filter;
- remove filter;
- change grouping/ranking;
- add comparison;
- change date range;
- reset context;
- clarify ambiguous reference to prior answer.

### Required conversations

- August debit total → compare with July;
- all August transactions → only HDFC → credits only;
- grouped bank totals → highest bank → show records;
- description search → add bank filter → reject “are those vendor payouts?”;
- exact reference lookup → explain duplicate matches.

### Exit criteria

Exact QueryState passes after every benchmark turn; context conflicts and concurrent-response races are
tested.

## 10. Phase 6 — data health, export and evaluation

### Data health

Surface:

- dataset version/cutoff and row counts;
- FK/enum/amount/date integrity;
- NULL descriptions;
- duplicate reference IDs;
- duplicate-lookalike transactions;
- malformed UUID-like source ID signal;
- zero/max amount boundary records;
- descriptions requiring redaction;
- unsupported source dimensions.

### Export

- CSV and XLSX;
- query/receipt metadata sheet or header section;
- exact decimal cells/strings;
- source-row parity and source hash;
- account/UTR masking and narration redaction;
- spreadsheet-formula-injection neutralisation.

### Evaluation

- local-only runs against visible/private case sets;
- parser/plan/answer/refusal/latency/cost layers;
- actual result scorecard; no fabricated accuracy.

## 11. Phase 7 — performance and scale evidence

The problem states a potential 20M-record limit. Do not claim compliance based on the small fixture.

### Work

- generate a disposable scale fixture without corrupting source semantics;
- run representative aggregate, grouped, reference, description and paginated-record queries;
- capture `EXPLAIN ANALYZE`, p50/p95, rows examined and index use;
- enforce statement timeout and response row caps;
- compare cold/warm cache where relevant;
- document hardware and MySQL configuration.

Prioritise indexes in `database/indexes.sql`; avoid adding an index for every possible combination.
Literal `description LIKE '%term%'` is qualified and may not scale; optional FULLTEXT behavior must be
documented and benchmarked separately.

## 12. Phase 8 — hardening and demo release

### P0 hardening

- run privacy scan across API/UI/export/log fixtures;
- test prompt injection, XSS and spreadsheet injection;
- test decimal extremes, negative balances and zero baseline comparison;
- test month boundaries and microseconds;
- test MySQL reserved-name quoting and session timezone;
- test no-data/clarify/unsupported/failed states;
- run keyboard/mobile/responsive checks;
- ensure CI and clean-checkout instructions pass.

### Release evidence

- working prototype;
- architecture diagram;
- setup README;
- sample questions and captured receipts;
- measured lightweight-model scorecard;
- deck and three-minute demo flow;
- limitation and synthetic-data disclosure.

## 13. Parallelisation map

After Phase 0 contracts are frozen:

- Agent A: source models, loader and database integration tests;
- Agent B: QueryPlan/compiler/result validators;
- Agent C: DRF metadata/source endpoints and problem details;
- Agent D: React shell/Ask/evidence components using MSW fixtures;
- Agent E: parser prompt/resolvers/evaluation harness;
- Agent F: privacy/export/data-health tests.

Merge order follows contracts → deterministic core → API → UI/model. Agents must not independently
rename metrics or widen source semantics.

## 14. Handoff checklist for every task

- ticket ID and dependency status;
- contract/dataset versions used;
- files changed;
- exact commands and results;
- response/SQL/screenshot evidence;
- privacy and unsupported-behavior impact;
- assumptions and remaining risks;
- next unblocked ticket.

The detailed machine-readable queue is `project_backlog.csv`.
