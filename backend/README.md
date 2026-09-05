# Backend Implementation Contract

Build a Django + Django REST Framework service under this directory. Read `../docs/BACKEND_QUERY_ENGINE_SPEC.md` before scaffolding.

## Required architectural split

- DRF serializers/views: HTTP validation and response mapping.
- Pydantic domain objects: QueryPlan, QueryState, ComputedFacts, AnswerReceipt.
- Django ORM: conversations, turns, idempotency, audit metadata.
- Bound allow-listed SQL: finance aggregation and records.
- PostgreSQL: arithmetic, grouping, ordering, and source selection.
- Optional Celery/Redis: large exports and model benchmark tasks only.

## First vertical slice

Implement a direct QueryPlan for August 2026 completed vendor payouts and return `contracts/sample_verified_answer_receipt.json`-equivalent data after executing PostgreSQL. Do not add the model until this passes exact integration tests.

## Target commands

```bash
cd backend
python manage.py migrate
python manage.py runserver
pytest
ruff check .
mypy .
```

The eventual scaffold must expose `/api/v1/health`, `/api/v1/meta`, conversation/message, query receipt/records/export, explorer, reconciliation, data-health, glossary, and local evaluation routes defined by OpenAPI.
