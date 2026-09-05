# Development Runbook

## 1. Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Node.js 20+ for the React application
- optional GitHub CLI for publishing

## 2. Validate the repository without services

```bash
python -m pip install -r requirements-tools.txt
python scripts/generate_dataset.py --check
python scripts/validate_dataset.py
python scripts/validate_repository.py
python -m unittest discover -s tests -v
```

These commands validate fixture determinism, source invariants, contract schemas, benchmark parity,
privacy helpers and runtime/gold isolation.

## 3. Regenerate source-aligned data

Only run regeneration when intentionally changing `scripts/generate_dataset.py` or the source
contract:

```bash
python scripts/generate_dataset.py
python scripts/validate_dataset.py
python -m unittest discover -s tests -v
```

Review the diff for all generated CSV, manifest, edge-case and benchmark files. A fixture change
must update the dataset version if it changes visible records or expected results.

## 4. Start MySQL and Redis

```bash
cp .env.example .env
docker compose up -d mysql redis
docker compose ps
```

Wait for the MySQL health check, then load the fixture:

```bash
python scripts/load_mysql.py --truncate
```

The loader:

- creates the exact three source tables;
- sets the session timezone to `+05:30`;
- loads bank, then account, then transaction;
- applies indexes;
- validates counts and foreign keys;
- runs transactionally where supported.

Useful local SQL:

```bash
docker compose exec mysql mysql -uledgerproof -pledgerproof ledgerproof
```

```sql
SELECT COUNT(*) FROM bank;
SELECT COUNT(*) FROM account;
SELECT COUNT(*) FROM `transaction`;
SELECT SUM(transaction_amount)
FROM `transaction`
WHERE transaction_type = 'debit'
  AND transaction_date >= '2026-08-01 00:00:00'
  AND transaction_date <  '2026-09-01 00:00:00';
```

Expected counts are 10 banks, 30 accounts and 2,426 transactions. Expected August debit total is
`121758278.46` across 205 rows.

## 5. Backend setup

After the Django scaffold exists:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e '.[dev]'
python manage.py migrate
python manage.py runserver
```

Run checks:

```bash
pytest
ruff check .
mypy .
```

Use a separate read-only MySQL credential for normal source queries. Django application tables
should be prefixed `app_` and must not alter the meaning of the three source tables.

## 6. Frontend setup

After the React scaffold exists:

```bash
cd frontend
npm ci
npm run dev
```

Run checks:

```bash
npm run typecheck
npm run lint
npm run test
npm run test:e2e
npm run build
```

Configure the frontend origin/API URL in `.env` without committing secrets.

## 7. Clean reset

```bash
docker compose down -v
docker compose up -d mysql redis
python scripts/load_mysql.py --truncate
```

Do not run reset commands against any non-local database.

## 8. Common failures

### MySQL rejects `transaction`

Quote the table name as `` `transaction` ``. It is a reserved identifier.

### Timezone tables are unavailable

The implementation uses the numeric MySQL session offset `+05:30`, which does not require named
server timezone tables. Keep ISO timestamps with `+05:30` at API boundaries.

### Totals differ by a paise

Check for float conversion. MySQL columns must be `DECIMAL(15,2)`, Python must use `Decimal`, and
JSON must carry strings.

### Month boundary row is missing or duplicated

Use a half-open range: `>= start` and `< end_exclusive`. Do not use `BETWEEN` for calendar periods.

### Account/UTR appears in a response

Stop the demo. Verify the repository privacy mapper runs before serialization/model context and
scan descriptions for embedded account numbers. The raw source CSV intentionally contains values
that should not cross the boundary.

### Reference lookup returns one of several rows

`transaction_reference_id` is not unique. Return all exact matches and mark the answer qualified.
Do not use `.first()` without proving uniqueness.

### “Vendor payout” question produces a total

This is a semantic failure. The schema does not support authoritative vendor or payout facts.
Return unsupported and offer debit/description-search alternatives without relabelling them.

### Stale follow-up overwrites current state

Carry `context_version`; reject mismatches with 409 and refresh the state before retrying.

## 9. Bundle creation

```bash
python scripts/build_bundle.py --output /mnt/data/finance_ai_bot.zip
```

The archive excludes `.git`, environments, secrets, caches, node modules and runtime exports.

## 10. Pre-demo smoke sequence

1. Run all four root checks.
2. Recreate and load MySQL.
3. Verify the canonical August total directly in SQL.
4. Start backend and frontend.
5. Execute the five-turn demo in `DEMO_AND_SUBMISSION_PLAN.md`.
6. Download CSV and XLSX; compare amount/count/hash and scan privacy.
7. Test 360px layout and keyboard navigation.
8. Turn off the model temporarily and confirm deterministic source pages still work and errors are
   clear.
