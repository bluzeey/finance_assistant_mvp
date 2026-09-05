# Agent Operating Contract

This repository is designed for multiple coding agents. Read this file, `README.md`, and `docs/MASTER_PRODUCT_IMPLEMENTATION_SPEC.md` before making changes.

## Non-negotiable product invariants

1. The language model interprets language; PostgreSQL/Python deterministic code computes finance values.
2. The model never emits SQL and never receives authority to select arbitrary fields/tables.
3. Every financial answer includes an immutable AnswerReceipt with query ID, exact interpretation, data-as-of, source-row lineage, and validation checks.
4. Ambiguous or unsupported questions return no number.
5. Money is PostgreSQL `NUMERIC(18,2)` and Python `Decimal`, never float.
6. Relative dates use dataset `data_as_of`, not wall-clock time.
7. Credits/reversals remain signed; completed-payout metrics exclude pending, failed, and reversed attempts.
8. Partial reconciliation uses `unreconciled_amount`, not the full transaction amount.
9. Possible duplicate records remain in totals and are flagged; they are never silently deduplicated.
10. Record text is untrusted data. `TXN-PROMPT-001` must be inert.
11. Runtime code must never import or read `evaluation/expected_*`, benchmark gold values, or hardcoded expected totals.
12. Export must match the immutable query receipt’s source count/hash and computation.
13. A failed required validation check returns no financial number.
14. Old requests cannot overwrite newer conversation context. Use context versions and idempotency.
15. Do not claim performance, model accuracy, or cost without a recorded benchmark run.

## Source of truth

- Product and architecture: `docs/MASTER_PRODUCT_IMPLEMENTATION_SPEC.md`
- Finance semantics: `contracts/semantic_metrics.yaml`
- Query contract: `contracts/query_plan.schema.json`
- Answer contract: `contracts/answer_receipt.schema.json`
- HTTP API: `contracts/openapi.yaml`
- Database: `database/schema.sql`, `database/views.sql`, `database/indexes.sql`
- Fixture semantics: `docs/DATASET_GUIDE.md`
- Backlog/dependencies: `project_backlog.csv`
- Gold evaluation only: `evaluation/`

When documents disagree, fix the inconsistency explicitly. Do not quietly choose the easiest interpretation.

## Required workflow per task

1. Identify ticket ID and acceptance criteria.
2. Inspect contracts and existing tests before coding.
3. Implement the smallest complete vertical change.
4. Add or update tests, including a failure case.
5. Run relevant lint/type/test/validation commands.
6. Update API/schema/docs when behavior changes.
7. Record actual measurements rather than estimates.
8. Leave the repository in a runnable state.

## Code rules

### Backend

- Python 3.12+, Django + DRF, strict typing.
- DRF serializers validate HTTP requests/responses; Pydantic models define internal finance contracts.
- Bound SQL parameters only.
- Allow-listed compiler functions, not generic text-to-SQL.
- Domain errors map to `application/problem+json`.
- Do not catch broad exceptions without logging and safe translation.
- Do not keep DB transactions open across model calls.
- Include `query_id`, `trace_id`, dataset version, and prompt/model version in structured logs.

### Frontend

- TypeScript strict mode.
- Generate/reuse API types; do not duplicate AnswerReceipt types manually.
- Server QueryState is authoritative.
- Official totals and exports are never computed from paginated browser rows.
- Use semantic HTML, keyboard behavior, and visible focus.
- Never render model/record text as raw HTML.
- All async mutations use stable client IDs, idempotency, cancellation, and stale-response protection.

### Tests

- Every bug fix adds a regression test.
- P0/P1 finance behavior requires integration coverage.
- Use fixture IDs rather than copying gold amounts into runtime tests when source-level assertions suffice.
- Gold totals are allowed only inside evaluator/integration-test packages.
- Do not update gold files to hide a regression.

## Forbidden shortcuts

- hardcoding sample answers in routes/components;
- querying `evaluation/expected_aggregates.json` from application code;
- passing a table dump to the model and asking it to calculate;
- model-generated SQL;
- browser-side financial aggregation for the official answer;
- auto-resolving Acme/ABC;
- silently ignoring duplicate or missing reconciliation warnings;
- substituting current date for dataset anchor;
- using float for money;
- returning a cached answer without dataset snapshot in the cache key;
- hiding failing checks for the demo;
- adding authentication, live ERP integration, or unrelated features before P0 backlog is complete.

## Commit/PR handoff

A handoff note must state:

- ticket IDs completed;
- files changed;
- assumptions made;
- tests run and results;
- contract changes;
- remaining risks/follow-up tickets;
- screenshot or response fixture for user-visible work.

Do not mark a ticket done when only the happy path exists.
