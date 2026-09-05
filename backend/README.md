# Backend Implementation Contract

Build the backend as a **Python 3.12+ Django + Django REST Framework** service backed by
**MySQL 8.4**. Read these documents before scaffolding application code:

1. `../AGENTS.md`
2. `../docs/PROVIDED_DATABASE_SCHEMA.md`
3. `../docs/BACKEND_QUERY_ENGINE_SPEC.md`
4. `../contracts/semantic_metrics.yaml`
5. `../contracts/openapi.yaml`

## Non-negotiable data boundary

The finance source contains exactly three tables:

- `bank`
- `account`
- `transaction`

Do not create source-of-truth vendor, payout, reconciliation, category, ledger, invoice, or
historical-balance tables. Application tables for conversations, receipts, idempotency, exports,
and evaluation runs may live in the same database with an `app_` prefix, but they must never be
presented as organiser-provided finance facts.

`transaction` is a MySQL reserved word. Quote it as `` `transaction` `` in raw SQL and set
`db_table = "transaction"` on any unmanaged Django model.

## Architectural split

| Layer | Responsibility |
|---|---|
| DRF | HTTP validation, authentication stub, error mapping, pagination and content negotiation |
| Domain models | Pydantic/dataclass forms of QueryPlan, QueryState, ComputedFacts and AnswerReceipt |
| Interpretation | Small-model structured parsing only; no SQL and no arithmetic |
| Resolution | Dates, bank codes/names, program IDs, account/entity IDs and reference semantics |
| Query compiler | Map validated plans to an allow-listed query family and bound parameters |
| MySQL | Filtering, grouping, ordering and `DECIMAL` aggregation |
| Validator | Recompute invariants, verify source lineage and block failed answers |
| Presenter | Deterministic number formatting and restricted language generation |
| Django ORM | `app_` conversation, turn, receipt, idempotency and export metadata |
| Celery/Redis | Optional large exports and benchmark jobs; never required for an ordinary answer |

## First vertical slice

Before adding any model, execute this manually constructed intent:

> Total debit transaction amount from 2026-08-01 00:00:00 inclusive to
> 2026-09-01 00:00:00 exclusive in Asia/Kolkata.

The result must be:

```text
amount: 121758278.46 INR
row_count: 205
account_count: 30
```

Return a schema-valid receipt equivalent to
`../contracts/sample_verified_answer_receipt.json`, with a records endpoint and privacy checks.
The slice is not complete until MySQL integration tests prove exact `DECIMAL` behavior.

## Suggested Django structure

```text
backend/
├── manage.py
├── pyproject.toml
├── config/
│   ├── settings/{base,local,test}.py
│   ├── urls.py
│   └── asgi.py
├── apps/
│   ├── source_data/       # unmanaged source models/repositories
│   ├── conversations/     # app_ tables and multi-turn state
│   ├── query_engine/      # compiler/executor/validator/receipt
│   ├── metadata/          # banks, accounts, glossary, data health
│   ├── exports/           # receipt-bound CSV/XLSX output
│   └── evaluation/        # local-only benchmark runner
└── tests/
```

## Required endpoints

Implement the paths in `../contracts/openapi.yaml` without silently widening their semantics:

- `GET /api/v1/metadata`
- `GET /api/v1/banks`
- `GET /api/v1/accounts`
- `GET /api/v1/transactions`
- `GET /api/v1/data-health`
- `POST /api/v1/assistant/messages`
- `GET /api/v1/assistant/conversations/{conversation_id}/state`
- `GET /api/v1/assistant/receipts/{query_id}`
- `GET /api/v1/assistant/receipts/{query_id}/records`
- `GET /api/v1/assistant/receipts/{query_id}/export`
- `POST /api/v1/evaluation/runs` in local/demo mode only

## Security and correctness defaults

- Connect with a read-only MySQL source-data user in runtime environments.
- Use bound parameters only. Reject model-produced SQL, identifiers and operators.
- Set the MySQL session timezone to `+05:30`.
- Use Python `Decimal` and decimal strings in JSON; never float for finance values.
- Exact reference lookup targets `transaction_reference_id`; bare “reference” does not mean UTR.
- Treat `utr_number` and `account_number` as sensitive; mask them before model/browser/export.
- Redact account-number-like substrings embedded in `description`.
- Render source text as text, not HTML, and treat it as untrusted data rather than instructions.
- Apply statement timeout, row limits, cursor pagination and idempotency keys.
- A failed required validation returns no official number.

## Target commands

```bash
cd backend
python manage.py migrate
python manage.py runserver
pytest
ruff check .
mypy .
```

Root-level fixture and contract checks remain mandatory:

```bash
python scripts/validate_dataset.py
python scripts/validate_repository.py
python -m unittest discover -s tests -v
```
