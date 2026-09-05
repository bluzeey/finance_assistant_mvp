# Development Runbook

## Local services

```bash
cp .env.example .env
docker compose up -d postgres redis
python -m pip install -r requirements-tools.txt
python scripts/load_postgres.py --truncate
python scripts/validate_dataset.py
python scripts/validate_repository.py
```

## Regenerating data

```bash
python scripts/generate_dataset.py
python scripts/validate_dataset.py
```

Regeneration changes evaluation values if financial generation logic changes. Review the diff carefully. Never update gold solely to make a failing implementation pass.

## Agent task start

1. Select an unblocked ticket from `project_backlog.csv`.
2. Read `AGENTS.md`, master spec, relevant contracts, and tests.
3. State assumptions in the task/PR.
4. Implement the smallest vertical behavior.
5. Add success and failure regression tests.
6. Run relevant validators/tests.
7. Update contracts/docs if behavior changed.
8. Leave a handoff with files, tests, risks, and screenshot/fixture.

## Contract change

A contract change must update:

- JSON Schema/OpenAPI/semantic registry;
- backend types/serializers;
- frontend types/components;
- fixtures/samples;
- contract tests;
- master/specialist docs;
- affected backlog acceptance criteria.

## Data issue triage

Do not patch CSV rows manually without updating the generator. Add or modify generation logic, regenerate, validate, and review manifest/hash changes.

## Performance work

Record:

- commit, dataset row counts, hardware/container limits;
- exact query name/plan and parameters class;
- indexes/views;
- warm/cold protocol;
- p50/p95 and sample count;
- `EXPLAIN (ANALYZE, BUFFERS)` output;
- regression threshold.

## Production-like failures

- model unavailable → deterministic-supported questions may proceed; otherwise safe interpretation error;
- database timeout → no number, error receipt/problem response;
- Redis/Celery unavailable → core synchronous answers continue; async export/evaluation reports degraded;
- stale context → 409 and frontend reconciliation;
- export mismatch → fail and regenerate from receipt snapshot, never serve divergent file.
