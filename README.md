# LedgerProof — Grounded Finance Assistant for the Tiby/TBX Hackathon

LedgerProof is a React + Python reference project for a conversational finance assistant
that answers only from the database schema supplied by the organisers:

- `bank`
- `account`
- `transaction`

The central product rule is simple:

> **The language model interprets the question. MySQL and deterministic Python compute the answer. If the required fact is absent or ambiguous, the assistant returns no number.**

This repository is an execution package for coding agents. It contains the source-aligned
synthetic dataset, SQL, contracts, gold benchmarks, UI/UX behavior, backend design, privacy
rules, bug catalogue, implementation backlog, and validation scripts.

## Schema correction from the earlier plan

The earlier product plan assumed richer finance tables for vendors, payouts, reconciliation,
and a chart of accounts. The organisers' actual schema has none of those fields. Those
assumptions have been removed from the runtime design and tests.

| Question | Safe behavior with the supplied schema |
|---|---|
| “How much did we spend last month?” | Sum `transaction_amount` where `transaction_type='debit'` over the resolved date range. |
| “How much money came in?” | Sum credits over the resolved range. |
| “What is net cash flow?” | Credits minus debits, computed deterministically. |
| “What is the current available balance?” | Sum `account.available_balance` across distinct filtered accounts. |
| “Find reference HDFCH….” | Exact, case-sensitive lookup in `transaction_reference_id`. |
| “Show transactions mentioning Selection Mobile.” | Literal narration search with a visible qualification that this is not a canonical vendor dimension. |
| “Which transactions are unreconciled?” | **Unsupported**: no reconciliation field exists. |
| “How much did we spend on vendor payouts?” | **Unsupported**: no vendor or payout table exists. |
| “What was our balance last month?” | **Unsupported**: `available_balance` is a current snapshot, not history. |

See [`docs/SCHEMA_ALIGNMENT_AND_GAPS.md`](docs/SCHEMA_ALIGNMENT_AND_GAPS.md) for the full gap analysis.

## Technology choices

- **Frontend:** React, TypeScript, Vite, TanStack Query, React Router, accessible headless components
- **Backend:** Python 3.12+, Django, Django REST Framework, Pydantic contracts
- **Database:** MySQL 8.0+ using the exact three-table source schema
- **Conversation state/cache:** Redis; never mixed into the finance database
- **Async work:** Celery only for larger exports/evaluation runs
- **Model:** smallest structured-output-capable model that clears the benchmark threshold
- **Money:** MySQL `DECIMAL(15,2)` and Python `Decimal`; never float
- **Time:** `Asia/Kolkata`, with relative dates anchored to the dataset cutoff rather than the wall clock

## Deterministic sample dataset

The fixture preserves every organiser-provided seed row and expands it with repeatable,
synthetic records for meaningful testing.

| File/table | Rows | Purpose |
|---|---:|---|
| `data/csv/bank.csv` | 10 | Canonical bank codes and names supplied by the organisers |
| `data/csv/account.csv` | 30 | Multiple banks, entities and programs; positive and negative balances |
| `data/csv/transaction.csv` | 2,426 | Debit/credit history from December 2025 through 3 September 2026 |
| `data/csv/data_dictionary.csv` | 16 | Field semantics, sensitivity, display and search policies |
| `evaluation/benchmark_cases.jsonl` | 30 | Gold single-turn execution, clarification, unsupported and no-data cases |
| `evaluation/benchmark_conversations.jsonl` | 5 | Multi-turn context and correction scenarios |
| `evaluation/edge_case_manifest.csv` | 16 | Dates, duplicates, nulls, privacy, XSS and prompt-injection records |

Important fixture facts:

- Currency: INR
- Dataset timezone: Asia/Kolkata
- Data cutoff: `2026-09-03T23:59:59.999999+05:30`
- “Last month” resolves to `[2026-08-01 00:00:00, 2026-09-01 00:00:00)`
- August debit total: `₹12,17,58,278.46` across 205 rows
- August credit total: `₹30,24,25,859.82` across 80 rows
- Current available balance: `₹82,33,92,832.43` across 30 accounts

These values are evaluation fixtures, not hardcoded application responses. Runtime code must
always query the source rows.

## Validate everything

```bash
python -m pip install -r requirements-tools.txt
make all
```

Equivalent commands:

```bash
python scripts/generate_dataset.py --check
python scripts/validate_dataset.py
python -m unittest discover -s tests -v
python scripts/validate_repository.py
```

Expected high-level result:

```text
Banks:                 10
Accounts:              30
Transactions:          2426
Benchmark cases:       30
PASS
Ran 34 tests ... OK
```

Regenerate the fixture after an intentional generator change:

```bash
python scripts/generate_dataset.py
make all
```

The seed is fixed, so generated files must be byte-stable.

## Run MySQL locally

```bash
cp .env.example .env
docker compose up -d mysql redis
python scripts/load_mysql.py --truncate
```

The loader applies `database/schema.sql`, loads CSVs in foreign-key order, creates indexes,
and sets the MySQL session timezone to `+05:30`.

### MySQL gotchas already accounted for

- `transaction` is a keyword, so raw SQL must quote it as `` `transaction` ``.
- The source IDs are `VARCHAR(36)`, not native UUID columns. One provided transaction ID is
  malformed as a strict UUID; identifiers must be treated as opaque strings.
- MySQL's default collation is case-insensitive, but transaction reference matching is defined
  as exact and case-sensitive. The compiler must use `BINARY` or an equivalent binary collation.
- `TIMESTAMP` values depend on the session timezone. Every connection must set `+05:30` for this fixture.
- `available_balance` must not be summed after joining to transactions because that multiplies
  one account snapshot by the number of transaction rows.

## Product pages

1. **Ask** — chat, suggested questions, answer receipt, breakdown, source rows, clarification and unsupported states.
2. **Transactions** — sanitized, keyset-paginated explorer with bank/account/entity/program/date/type/reference filters.
3. **Accounts** — bank and program summaries with masked account numbers and current balances.
4. **Data Health** — freshness, row counts, nulls, duplicate risks, orphan checks, zero amounts and redaction findings.
5. **Glossary** — supported metrics, date semantics, sensitive-field policy, and unsupported concepts.
6. **Evaluation** — benchmark results, model comparison, latency/cost, privacy and refusal metrics.

There is intentionally no Reconciliation or Vendor page because the source does not contain
those dimensions.

## Grounded answer pipeline

```text
Question
  → lightweight model emits InterpretationDraft (no SQL, no numbers)
  → deterministic metric/date/entity resolvers
  → validated QueryPlan
  → allow-listed SQL compiler with bound parameters
  → MySQL aggregate + source IDs
  → validation and privacy checks
  → ComputedFacts
  → optional constrained wording step
  → immutable AnswerReceipt + source-record endpoint/export
```

The model never receives raw account numbers, raw UTR values, unrestricted table contents,
or authority to select arbitrary columns.

## Privacy decisions

- `account_number` is masked except for the last four characters.
- `utr_number` is masked and never sent to the model.
- UTR lookup is disabled by default because the field may be encrypted/tokenized.
- Narrations can themselves contain account numbers; known values are redacted inside
  `description` before model/UI/export use.
- Narration text is untrusted. The fixture includes prompt injection and `<script>` content;
  React must render it as escaped text, never raw HTML.
- Exports contain the exact receipt-scoped rows but only sanitized values.

## Build order for agents

Read these files before changing code:

1. [`AGENTS.md`](AGENTS.md)
2. [`docs/MASTER_PRODUCT_IMPLEMENTATION_SPEC.md`](docs/MASTER_PRODUCT_IMPLEMENTATION_SPEC.md)
3. [`contracts/semantic_metrics.yaml`](contracts/semantic_metrics.yaml)
4. [`docs/BACKEND_QUERY_ENGINE_SPEC.md`](docs/BACKEND_QUERY_ENGINE_SPEC.md)
5. [`docs/UI_UX_SPEC.md`](docs/UI_UX_SPEC.md)
6. [`docs/SUPPORTED_QUESTIONS.md`](docs/SUPPORTED_QUESTIONS.md)
7. [`docs/QUERY_CATALOG.md`](docs/QUERY_CATALOG.md)
8. [`project_backlog.csv`](project_backlog.csv)

Recommended vertical sequence:

1. Load MySQL and expose read-only bank/account/transaction endpoints with sanitization.
2. Implement QueryPlan models and one hand-authored `debit_total` compiler without any model.
3. Return a complete AnswerReceipt with reproducible source rows.
4. Build the React Ask page and evidence drawer.
5. Add the lightweight interpreter and deterministic resolvers.
6. Add remaining supported metrics and multi-turn QueryState.
7. Add explorer, accounts, data health, export and evaluation pages.
8. Run the benchmark, record actual model/cost/latency results, and polish the demo.

## Canonical demo flow

1. Ask **“How much did we spend last month?”**
   - Return `₹12,17,58,278.46`, 205 records, exact August range and calculation.
2. Ask **“How does that compare with the month before?”**
   - Inherit debit spend and compare August with July.
3. Ask **“Only HDFC.”**
   - Apply the bank filter to both periods without losing context.
4. Ask **“Show transactions mentioning Selection Mobile.”**
   - Return a qualified literal description search with sanitized rows.
5. Ask **“Which transactions are unreconciled?”**
   - Refuse to invent: explain that no reconciliation field exists.
6. Open the source-record table and CSV export.
7. Show the prompt-injection narration rendered as harmless text.

The exact three-minute script and deck outline are in
[`docs/DEMO_AND_SUBMISSION_PLAN.md`](docs/DEMO_AND_SUBMISSION_PLAN.md).

## Repository map

```text
.
├── AGENTS.md
├── README.md
├── project_backlog.csv
├── backend/                     # Django target layout and implementation guidance
├── frontend/                    # React target layout, components and page acceptance matrix
├── contracts/                   # QueryPlan, QueryState, ComputedFacts, AnswerReceipt, OpenAPI
├── data/csv/                    # bank, account, transaction and data dictionary fixtures
├── database/                    # exact MySQL DDL, indexes and safe query templates
├── docs/                        # end-to-end product/engineering/UX/QA/security plans
├── evaluation/                  # gold cases; forbidden to application runtime
├── scripts/                     # generator, reference evaluator, privacy, loader, validators
├── tests/                       # dataset, semantics, privacy, contract and benchmark regression tests
└── .github/                     # CI and agent-friendly templates
```

## Submission integrity

Do not claim accuracy, latency, cost, or 20-million-row performance without an actual recorded
run. Do not hide unsupported concepts. The most persuasive demo is not one that answers every
question; it is one that can prove when a number is trustworthy and knows when no defensible
number exists.

## License

MIT. All fixture records are synthetic and intended only for development, testing and demonstration.
