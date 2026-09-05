# Dataset Guide

**Dataset:** Tiby Finance Assistant Synthetic Fixture  
**Version:** `tiby-finance-fixture-v2.0.0`  
**Generator seed:** `20260903`  
**Currency:** INR  
**Timezone:** Asia/Kolkata  
**Data cutoff:** `2026-09-03T23:59:59.999999+05:30`

The fixture mirrors the organiser-provided three-table source schema and is large enough to test
aggregation, filtering, multi-turn questions, privacy and edge behavior without pretending to be
production data.

---

## 1. Files and database mapping

| File | Loaded table | Rows | Notes |
|---|---|---:|---|
| `data/csv/bank.csv` | `bank` | 10 | Exact organiser bank list |
| `data/csv/account.csv` | `account` | 30 | Includes all 10 organiser sample accounts |
| `data/csv/transaction.csv` | `transaction` | 2,426 | Includes all 10 organiser sample transactions |
| `data/csv/data_dictionary.csv` | none | 16 | Documentation for each source column |
| `data/company_metadata.json` | none | n/a | Currency/timezone/cutoff/privacy mode |
| `data/dataset_manifest.json` | none | n/a | Counts, seed and SHA-256 hashes |

Only the first three are source finance tables. The dictionary/metadata/manifest must not be
mistaken for source facts by the assistant.

---

## 2. Generation

```bash
python scripts/generate_dataset.py
```

The generator:

1. resets a local seeded PRNG;
2. preserves the exact organiser seed rows;
3. creates deterministic UUID5-style IDs for extra records;
4. creates additional accounts across the ten banks and programs 4, 21 and 46;
5. creates debit/credit narrations and decimal amounts from December 2025 through the cutoff;
6. adds targeted edge records;
7. writes CSVs in stable order;
8. computes gold aggregates from in-memory source records using `scripts/reference_evaluator.py`;
9. writes benchmark cases/conversations/edge manifest;
10. computes file hashes and row counts.

Check byte stability without modifying committed files:

```bash
python scripts/generate_dataset.py --check
```

Do not manually edit generated CSV/gold files. Change the generator and regenerate.

---

## 3. Source semantics

### `bank`

Fixed canonical codes/names. The assistant resolves user bank names to a code present here. It must
not hallucinate an institution.

### `account`

- `account_id` and `entity_id` are opaque strings up to 36 characters.
- `account_number` is synthetic but treated as sensitive.
- `program_id` is integer; `04` and `4` are the same value.
- `available_balance` is a current snapshot and can be negative.
- `bank_code` references `bank`.

### `transaction`

- `transaction_id` is an opaque source string.
- `transaction_date` has microsecond precision.
- `transaction_type` is `credit` or `debit`.
- `description` may be NULL and may contain sensitive/hostile text.
- `transaction_amount` is absolute `DECIMAL(15,2)`.
- `transaction_reference_id` is plaintext/searchable but nullable/non-unique.
- `utr_number` is nullable, sensitive and generated as encrypted-looking/tokenized content.

---

## 4. Preserved organiser patterns

The fixture keeps:

- all ten bank IFSC-prefix codes/names;
- the exact ten sample account IDs/entity IDs/numbers/programs/balances;
- the exact ten sample transaction IDs, timestamps, descriptions, amounts, references and UTRs;
- narration patterns such as NEFT, IMPS, UPI, FT, Selection-branded businesses and Bajaj-like
  disbursement/collection formats;
- negative and large available balances;
- NULL reference/UTR values.

One provided transaction ID, `0178b656-4a7d-98e8-9540f6e24caf`, is 36 characters but is not a
strict 8-4-4-4-12 UUID. The fixture preserves it to prevent accidental UUID coercion.

---

## 5. Relative dates and gold periods

All relative dates use the dataset cutoff, not today's date.

| Phrase | Start inclusive | End exclusive |
|---|---|---|
| Last month | 2026-08-01 00:00:00 | 2026-09-01 00:00:00 |
| July 2026 | 2026-07-01 00:00:00 | 2026-08-01 00:00:00 |
| This month to date | 2026-09-01 00:00:00 | 2026-09-04 00:00:00 |
| Year to date | 2026-01-01 00:00:00 | 2026-09-04 00:00:00 |

Fixture gold highlights:

```text
August debit total:        121758278.46 INR / 205 debit rows
August credit total:       302425859.82 INR / 80 credit rows
August net cash flow:      180667581.36 INR / 285 total rows
July debit total:           69995241.84 INR / 182 debit rows
Current available balance: 823392832.43 INR / 30 accounts
HDFC current balance:        8153593.44 INR / 5 accounts
```

These values are generated and stored for evaluation only. The application must query source rows.

---

## 6. Edge records

See `evaluation/edge_case_manifest.csv` for IDs.

### Date boundaries

- 31 July 23:59:59.999999
- 1 August 00:00:00.000000
- 31 August 23:59:59.999999
- 1 September 00:00:00.000000

These prove half-open intervals and timezone setup.

### Duplicate risk

Two rows share account/date/type/description/amount but have different IDs/references. They remain in
totals and trigger a possible-duplicate warning.

### Duplicate reference

Two different rows share `DUP-REF-2026-001`; exact lookup must return both and qualify the answer.

### Null/zero/max

- one null description;
- one zero amount;
- one exact maximum `DECIMAL(15,2)` amount (`9999999999999.99`), placed outside the canonical
  August demo so it does not dominate the primary example.

### Privacy/security

- narration containing a known account number;
- encrypted UTR with no plaintext reference;
- prompt injection plus `<script>` text;
- Unicode narration;
- case-sensitive reference.

Generated regular narrations periodically embed known account numbers, producing multiple redaction
test rows rather than a single special case.

---

## 7. Privacy expectations

Even synthetic sensitive fields are handled as production-like:

| Field/surface | Rule |
|---|---|
| `account_number` | Never return raw; mask all but last four |
| `utr_number` | Never return raw; mask suffix; do not model/log/export raw |
| account number inside `description` | Replace known exact value with masked form |
| description HTML/script | Return as escaped text only |
| transaction reference | May display/copy when explicitly relevant |
| amount/balance | Confidential but usable in computed answer |

A naive generic regex that masks every long number may accidentally destroy legitimate numeric
transaction references. The reference implementation redacts exact known account numbers first.

---

## 8. Validation

```bash
python scripts/validate_dataset.py
```

Checks:

- exact source CSV set;
- row counts;
- PK uniqueness and FKs;
- canonical bank values;
- column length/domain/nullability assumptions;
- decimal precision/range/non-negative transaction amounts;
- timestamps and cutoff;
- known quality/edge signals;
- manifest hashes;
- benchmark/gold consistency;
- removal of obsolete vendor/payout/reconciliation/PostgreSQL artifacts.

Known quality signals are expected and should be shown as warnings, not silently “fixed.”

---

## 9. Loading MySQL

```bash
docker compose up -d mysql redis
python scripts/load_mysql.py --truncate
```

Load order:

1. `bank`
2. `account`
3. `transaction`
4. indexes

The loader sets `time_zone='+05:30'` and uses UTF-8. The runtime application should use a separate
read-only user.

---

## 10. Extending the fixture safely

When adding a question capability:

1. Verify that the required source field truly exists.
2. Add/adjust semantic contract first.
3. Add generator records that distinguish correct from common wrong implementations.
4. Recompute gold from source records.
5. Add benchmark and multi-turn cases.
6. Add validator/test coverage.
7. Update manifest/version if semantics or records change.
8. Update schema-gap docs and UI copy.

Do not add a canonical vendor/reconciliation/category field unless the organisers supply a versioned
source schema containing it. An inferred development-only field cannot become an official answer
source without explicit labeling and evaluation.

---

## 11. Scale fixture

`scripts/generate_scale_fixture.sql` duplicates rows in a throwaway MySQL database for query-plan
measurement. It is not source data and should never be committed back into the gold CSV fixture.

For every benchmark record actual row count, hardware, MySQL version, indexes, query plan,
cold/warm status, p50/p95 and timeout settings. Do not claim 20M performance from the base fixture.
