# Backend and Deterministic Query Engine Specification

**Runtime:** Python 3.12+, Django, Django REST Framework  
**Database:** MySQL 8.0+  
**State/cache:** Redis  
**Source tables:** `bank`, `account`, `transaction`

This document turns the product contract into implementable backend components. The system is not
text-to-SQL. It is a typed intent parser followed by deterministic resolvers and a small catalogue
of reviewed SQL builders.

---

## 1. Architecture boundaries

```text
HTTP/DRF
  → request validation/idempotency/context check
  → model interpreter (InterpretationDraft only)
  → deterministic resolver (QueryPlan)
  → compiler registry (SQL template + bound params)
  → read-only MySQL executor
  → result validators/privacy sanitizer
  → ComputedFacts
  → deterministic/guarded presenter
  → AnswerReceipt + QueryState CAS commit
```

The following boundaries are mandatory:

- model cannot call MySQL directly;
- model output is untrusted until schema/resolver validation;
- compiler cannot accept arbitrary identifiers/SQL;
- executor returns Decimal/raw rows, not prose;
- presenter cannot modify computed values;
- runtime cannot read evaluator gold files.

---

## 2. Suggested Django structure

```text
backend/
  manage.py
  pyproject.toml
  config/
    settings/
      base.py
      local.py
      test.py
    urls.py
    wsgi.py
    asgi.py
  finance_data/
    apps.py
    models.py
    repositories.py
    selectors.py
    serializers.py
    pagination.py
    health.py
    tests/
  assistant/
    contracts.py
    constants.py
    interpreter.py
    prompts.py
    resolver.py
    date_resolver.py
    bank_resolver.py
    reference_resolver.py
    state.py
    idempotency.py
    compiler/
      __init__.py
      registry.py
      base.py
      transaction_aggregates.py
      balances.py
      lookups.py
      grouping.py
    executor.py
    validators.py
    privacy.py
    presenter.py
    receipts.py
    services.py
    exceptions.py
    tests/
  exports/
    services.py
    tasks.py
    tests/
  evaluation_app/
    runner.py
    scorers.py
    views.py
    tests/
  api/
    serializers.py
    views.py
    urls.py
```

The source schema is unmanaged. If Django auth/admin is introduced, route its tables to a separate
application database; do not mix them with source finance tables for the hackathon.

---

## 3. Source models

Use `managed = False` and plain strings for source IDs.

```python
class Bank(models.Model):
    bank_code = models.CharField(max_length=10, primary_key=True)
    bank_name = models.CharField(max_length=150)

    class Meta:
        managed = False
        db_table = "bank"


class Account(models.Model):
    account_id = models.CharField(max_length=36, primary_key=True)
    entity_id = models.CharField(max_length=36)
    account_number = models.CharField(max_length=20)
    program_id = models.IntegerField()
    available_balance = models.DecimalField(max_digits=15, decimal_places=2)
    bank = models.ForeignKey(Bank, db_column="bank_code", on_delete=models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "account"


class Transaction(models.Model):
    transaction_id = models.CharField(max_length=36, primary_key=True)
    account = models.ForeignKey(Account, db_column="account_id", on_delete=models.DO_NOTHING)
    transaction_date = models.DateTimeField()
    transaction_type = models.CharField(max_length=6)
    description = models.CharField(max_length=500, null=True)
    transaction_amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_reference_id = models.CharField(max_length=64, null=True)
    utr_number = models.CharField(max_length=256, null=True)

    class Meta:
        managed = False
        db_table = "transaction"
```

Do not use `UUIDField`: one organiser-provided transaction ID fails strict UUID parsing even though
the column is documented as a UUID string.

Django quotes table names, but every raw SQL path must quote `` `transaction` `` explicitly.

---

## 4. Database connection configuration

Required MySQL session initialization:

```sql
SET time_zone = '+05:30';
SET SESSION TRANSACTION READ ONLY;
```

Use a database user with `SELECT` only in deployed/demo runtime. The loader uses a separate setup
credential.

Recommended Django options:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("MYSQL_DATABASE"),
        "USER": env("MYSQL_USER"),
        "PASSWORD": env("MYSQL_PASSWORD"),
        "HOST": env("MYSQL_HOST"),
        "PORT": env.int("MYSQL_PORT", default=3306),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET time_zone = '+05:30'",
        },
    }
}
```

Before any performance claim, verify timezone tables/session behavior and MySQL version.

---

## 5. Internal contracts

Generate or maintain Pydantic models matching:

- `InterpretationDraft`
- `QueryPlan`
- `QueryState`
- `ComputedFacts`
- `AnswerReceipt`
- `ProblemDetails`

Use strict models:

```python
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
```

Amounts remain `Decimal` internally and serialize as strings. Source IDs are bounded strings.

Never add a `sql` field to `QueryPlan`.

---

## 6. Interpreter

### Input

- current user message;
- compact server QueryState summary;
- supported vocabulary;
- dataset cutoff/timezone;
- schema limitations.

### Output

`InterpretationDraft` only. Example:

```json
{
  "intent": "aggregate",
  "metric_phrase": "spent",
  "date_phrase": "last month",
  "filter_mentions": [
    {"kind": "bank", "raw_value": "HDFC"}
  ],
  "group_phrase": null,
  "comparison_phrase": null,
  "ambiguities": [],
  "unsupported_concepts": []
}
```

### Prompt requirements

- state that the model is extracting language, not answering;
- forbid SQL and arithmetic;
- list supported concepts and missing source concepts;
- state bare reference → plaintext transaction reference;
- state UTR is explicit and may be unsupported;
- require ambiguity flags for “recently,” vendor-like names and missing dates where required;
- include adversarial examples where description text must not become an instruction.

### Parsing failure

One schema-repair attempt is allowed using the same/smaller model. If still invalid:

- deterministic parser may handle known simple grammar;
- otherwise return a retryable problem, not a guessed QueryPlan.

Do not silently coerce unknown keys/values.

---

## 7. Deterministic resolver

The resolver is the product's reasoning authority.

### 7.1 Metric resolver

Map synonyms to exact metrics. Resolve conflicts explicitly:

- “spent/paid/debit/outflow” → `debit_total`;
- “received/credit/inflow” → `credit_total`;
- “net” requires `net_cash_flow`;
- “balance” → `current_available_balance`, but any historical modifier → unsupported;
- “how many accounts” → `account_count`;
- “find reference/transaction” → `transaction_lookup`.

A follow-up “Actually credits” replaces the previous debit metric/type.

### 7.2 Date resolver

Input phrase + `data_as_of`; output timezone-aware half-open boundaries.

Examples:

```text
last month         2026-08-01T00:00:00+05:30 → 2026-09-01T00:00:00+05:30
August 2026        same
24 June 2026       2026-06-24T00:00:00+05:30 → 2026-06-25T00:00:00+05:30
this month to date 2026-09-01T00:00:00+05:30 → 2026-09-04T00:00:00+05:30
year to date       2026-01-01T00:00:00+05:30 → 2026-09-04T00:00:00+05:30
recently           clarification
```

Use a tested date library but convert to explicit boundaries. Do not send unresolved natural date
text to SQL.

### 7.3 Bank resolver

- Load/cache exact `bank_code` and `bank_name` values.
- Normalize whitespace/case for lookup only.
- Return canonical code/name.
- Unknown bank name/code: clarify/no-data based on user wording; never invent.
- Do not fuzzy-match two close bank names without confirmation.

### 7.4 ID resolvers

- Treat account/entity/transaction IDs as opaque strings.
- Validate length, not strict UUID shape.
- Prefer exact source existence checks.
- Never accept raw account number in v1.
- Program ID parses to integer; leading zero is not semantic.

### 7.5 Reference resolver

- “reference/ref no/receipt” → `transaction_reference_id`.
- Exact case-sensitive value.
- “UTR” → explicit UTR path; default returns unsupported because storage mode is encrypted/tokenized.
- Never switch fields because the first lookup returned zero.

### 7.6 Description resolver

Vendor-like request requires clarification unless user already explicitly says “description contains”
or “mentioning.” The resolver can offer:

> Search descriptions for the exact phrase “Acme” (qualified, not canonical vendor attribution).

Confirmed literal becomes `description_contains` and adds mandatory qualification.

### 7.7 Unsupported resolver

Return a structured reason and safe alternatives before compiler execution for:

- reconciliation;
- vendor payout/vendor totals without confirmed literal search;
- category/chart of accounts;
- historical balance;
- budget/forecast;
- raw sensitive lookup.

---

## 8. Query compiler registry

Use a registry keyed by metric:

```python
COMPILERS: dict[Metric, QueryCompiler] = {
    Metric.DEBIT_TOTAL: TransactionAggregateCompiler(...),
    Metric.CREDIT_TOTAL: TransactionAggregateCompiler(...),
    Metric.NET_CASH_FLOW: NetCashFlowCompiler(...),
    Metric.TRANSACTION_COUNT: CountCompiler(...),
    Metric.AVERAGE_TRANSACTION_AMOUNT: AverageCompiler(...),
    Metric.LARGEST_TRANSACTION: LargestCompiler(...),
    Metric.CURRENT_AVAILABLE_BALANCE: BalanceCompiler(...),
    Metric.ACCOUNT_COUNT: AccountCountCompiler(...),
    Metric.TRANSACTION_LOOKUP: LookupCompiler(...),
}
```

Each compiler returns:

```python
CompiledQuery(
    template_id="transaction.debit_total.v1",
    sql="... %(start)s ...",
    params={...},
    result_shape=AggregateShape(...),
    source_tables=("transaction",),
    required_validations=(...),
)
```

No user/model text can be used as:

- a table/column name;
- aggregate/function;
- operator;
- sort direction;
- raw SQL fragment.

Map enums to reviewed SQL snippets in code.

---

## 9. Predicate compilation

### Date

```sql
t.transaction_date >= %(start_inclusive)s
AND t.transaction_date < %(end_exclusive)s
```

### Type

Use compiler-owned literal for metric-specific type or bound enum after validation.

### Bank/account/entity/program

Join only when required:

```sql
JOIN `account` a ON a.account_id = t.account_id
JOIN `bank` b ON b.bank_code = a.bank_code
```

Use `IN` placeholders expanded safely by the DB adapter/compiler, with maximum item count.

### Reference

```sql
WHERE BINARY t.transaction_reference_id = BINARY %(reference)s
```

Do not use `LIKE` or lowercase normalization.

### Description

```sql
LOWER(COALESCE(t.description,'')) LIKE CONCAT('%%', LOWER(%(literal)s), '%%')
```

Escape wildcard behavior if the product promises literal matching. Recommended: escape `\`, `%`,
`_` in the value and add `ESCAPE '\\'`. Always cap range/results and attach qualification.

### Amount

Bound Decimal min/max. Reject more than two decimal places or out-of-range values.

### Null description

Use explicit compiler flag, never user SQL:

```sql
t.description IS NULL
```

---

## 10. Metric compilers

### 10.1 Debit/credit total

Return total plus source row count in one aggregate query. Source IDs are fetched in a second,
receipt-scoped query or hashed incrementally.

### 10.2 Net cash flow

One query may calculate component totals and count:

```sql
SUM(CASE WHEN type='credit' THEN amount ELSE 0 END) AS credits,
SUM(CASE WHEN type='debit' THEN amount ELSE 0 END) AS debits
```

Python computes/validates `credits - debits` with Decimal or verifies the DB net field.

### 10.3 Average

Define denominator exactly after all filters. Zero rows → no-data, not zero average.

### 10.4 Largest

Filter, then deterministic ordering:

```sql
ORDER BY transaction_amount DESC, transaction_id DESC LIMIT 1
```

Return source row and verify amount equality.

### 10.5 Balance

Query `account` directly. Do not join `transaction` for ordinary bank/entity/program/account filters.
If a prior transaction result defines “those accounts,” resolve a distinct account ID set/receipt
predicate first and make the scope visible.

### 10.6 Account count

Direct `COUNT(*)` on account with structured filters.

### 10.7 Lookup

Transaction ID or plaintext reference exact match. Multiple reference rows are not an error;
receipt is qualified.

---

## 11. Grouping and comparison

### Grouping allow-list

Map enum to fixed expression/select/group/order tuples. Maximum two dimensions and bounded result
cardinality. Do not group by narration.

### Comparison

Compile current and comparison periods with identical metric/filters/grouping. Validate:

- periods do not overlap unexpectedly;
- same filter semantics;
- component totals independently reproducible;
- percentage change is null with reason when comparison denominator is zero.

Do not ask the model to calculate deltas/percentages.

---

## 12. Execution service

Responsibilities:

- get read-only connection;
- set query timeout/session timezone;
- execute with bound params;
- convert values to Decimal/int/datetime;
- cap rows;
- capture template ID/timing;
- hash deterministic source IDs;
- translate DB errors safely;
- close cursors/transactions before model/presentation.

Recommended source hash:

```text
SHA-256 of newline-joined transaction IDs sorted by the receipt's deterministic source order
```

For account metrics, hash sorted account IDs.

Large source sets should be streamed in chunks for hashing/export rather than loaded into memory.

---

## 13. Validation framework

Validation results have `id`, `status`, `required`, `detail`.

### Required checks

- plan schema/version;
- source schema/version available;
- start < end;
- identifiers resolved;
- metric source/table consistency;
- Decimal precision/range;
- aggregate/source row-count consistency;
- net/comparison component arithmetic;
- source hash generated;
- privacy sanitizer applied;
- prohibited raw fields absent from model/payload;
- no unsupported source concept entered compiler.

Any required `fail` suppresses the number.

### Warning checks

- duplicate-lookalike signature;
- duplicate transaction reference;
- null narration;
- zero amount;
- partial data range;
- description search;
- UUID-like ID anomaly;
- source cutoff older than expected.

Warnings determine `qualified` only when materially relevant to the answer.

---

## 14. Privacy sanitizer

Apply before model, API, cache, log and export boundaries.

```python
mask_account_number("50200013729069") == "••••••••••9069"
mask_utr(raw) == "••••••<last6>"
```

Description sanitization must replace exact known account numbers with masked values. Because a
transaction description may contain another account number not in the user's selected row, load a
bounded set of accessible known account numbers or use a data-loss-prevention stage. Avoid masking
all long digit sequences indiscriminately because plaintext transaction references may be numeric.

Return fields:

- `masked_account_number`, never `account_number`;
- `masked_utr_number`, never `utr_number`;
- sanitized `description`;
- exact `transaction_reference_id` only when needed.

Serializer tests must assert raw restricted keys/values are absent.

---

## 15. Presenter

Use deterministic templates by default:

```text
Across {scope}, {record_count} debit transactions totalled {formatted_amount}
from {start_label} through {end_inclusive_label}.
```

If a wording model is used:

- input only ComputedFacts and safe labels;
- output schema separates text and cited fact IDs;
- extract every numeric token and ensure it belongs to computed facts;
- disallow new source claims;
- fallback to deterministic template on mismatch/timeout.

Never send raw descriptions unless a product feature explicitly needs a small sanitized set.

---

## 16. Answer receipt persistence

The hackathon source DB should remain untouched. Store QueryState/receipts in Redis or in-memory
demo storage:

```text
receipt:{query_id} → immutable JSON, TTL or persistent demo duration
state:{conversation_id} → QueryState with version
idempotency:{key} → response/query_id
```

A receipt needs enough normalized predicate/template metadata to reproduce records/export. Do not
store raw UTR/account values.

If a dataset version changes, old receipts remain viewable as historical evidence but record/export
replay can be disabled or marked non-reproducible.

---

## 17. Idempotency and context concurrency

### Idempotency

- Require `Idempotency-Key` on message mutations.
- Key includes user/session scope.
- Same key + same payload returns original receipt.
- Same key + different payload returns 409.

### Context compare-and-swap

- Browser sends expected context version.
- Resolve/execute against that version.
- Commit new state only if version unchanged.
- Otherwise return `stale_context` without replacing state.
- Client refreshes state and may replay user intent.

Do not rely on request order alone.

---

## 18. Caching

Safe aggregate cache key:

```text
sha256(dataset_version + data_as_of + semantic_version + privacy_version + normalized_query_plan)
```

Never cache based only on raw user text. Cache stores ComputedFacts/lineage, not arbitrary model
prose. Re-run lightweight required validations on retrieval. Source row/export endpoints still use
the receipt predicate and verify count/hash.

---

## 19. Pagination

Use keyset ordering:

```text
transaction_date DESC, transaction_id DESC
```

Cursor contains signed/encoded date + ID + query/receipt scope. Validate cursor signature and scope.
Page size max 100. Official source count comes from aggregate/lineage query, not page rows.

Accounts can keyset by `bank_code, account_id` or `account_id`.

---

## 20. Exports

### Small export

Stream sanitized CSV/XLSX directly after receipt validation.

### Large export

Celery job receives query ID, retrieves immutable predicate, streams DB rows, sanitizes, computes
count/hash and compares with receipt. On mismatch, fail the job rather than quietly export different data.

### CSV/XLSX security

For text starting with `=`, `+`, `-`, `@`, prefix an apostrophe or otherwise encode as text to prevent
formula execution. Do not change numeric amount cells. Include qualification and cutoff metadata.

---

## 21. Data health service

Queries/checks:

- table/row counts;
- FK orphan counts;
- min/max transaction dates;
- null description/reference/UTR;
- zero/negative transaction amounts;
- amount beyond declared decimal bound;
- duplicate reference counts;
- lookalike duplicate signatures;
- strict UUID parse anomaly counts (warning only);
- known account number occurrences in descriptions;
- required indexes present;
- current session timezone;
- canonical bank names/codes.

Return overall `qualified` for known non-blocking fixture signals. A broken FK or invalid type/amount
is blocking/unhealthy.

---

## 22. Error model

Domain exceptions map to `application/problem+json`:

- `InvalidRequest`
- `StaleContext`
- `QueryTimeout`
- `DatasetUnavailable`
- `ValidationFailed`
- `ExportExpired`
- `RateLimited`
- `InternalError`

Do not expose SQL, credentials, raw source values or model prompt contents. Include trace ID,
retryability and safe action.

Semantic clarification/unsupported/no-data are successful AnswerReceipts (HTTP 200), not transport
errors.

---

## 23. API implementation notes

### `POST /assistant/messages`

Service pseudocode:

```python
validate_request()
existing = idempotency.get(key)
if existing: return existing
state = state_store.get(conversation_id)
assert_context_version(state, header_version)
draft = interpreter.parse(text, safe_state_summary(state))
plan = resolver.resolve(draft, state, dataset_metadata)
if plan.disposition != EXECUTE:
    receipt = receipt_factory.from_non_execution(plan)
else:
    compiled = compiler_registry.compile(plan)
    raw = executor.execute(compiled)
    facts = validators.validate_and_compute(plan, compiled, raw)
    receipt = presenter.build_receipt(plan, facts)
state_store.compare_and_swap(state.version, receipt)
idempotency.put(key, request_hash, receipt)
return receipt
```

### Explorer endpoints

They use the same filter/parser/compiler primitives but do not invoke a model. Query parameters are
DRF-validated and map to a QueryPlan-like structured filter.

---

## 24. Tests

### Unit

- money/date/resolver synonyms;
- ambiguous terms;
- bank/ID/reference rules;
- SQL fragment mapping;
- Decimal arithmetic;
- privacy sanitization;
- presenter numeric allow-list;
- cursor/idempotency/context logic.

### MySQL integration

- every metric against gold fixture;
- exact date boundaries/microseconds;
- reference collation case behavior;
- keyword-quoted table;
- balance fan-out regression;
- duplicate/reference behavior;
- null/zero/max decimal;
- timezone session;
- query timeout;
- export count/hash.

### API

- all receipt states;
- problem details;
- raw restricted values absent;
- generated OpenAPI conformance;
- stale context/idempotency.

### Model

- benchmark cases/conversations;
- malformed JSON;
- unsupported hallucination pressure;
- prompt-injection text;
- long/irrelevant input;
- typo/abbreviation behavior.

---

## 25. Performance measurement

Representative queries:

1. month debit aggregate;
2. month bank breakdown;
3. exact reference lookup;
4. account balance by bank/program;
5. keyset source page;
6. narration search (document separately because it may not scale like structured predicates).

For each capture:

- row count;
- MySQL/server resources/version;
- indexes;
- `EXPLAIN ANALYZE`;
- cold/warm p50/p95;
- timeout rate;
- transferred bytes;
- Python/serialization overhead.

Do not extrapolate a 2,426-row fixture measurement to 20M. Use the scale helper and clearly state the
actual size tested.

---

## 26. Definition of backend done

- exact unmanaged source models;
- read-only MySQL connection and timezone setup;
- all contracts implemented/validated;
- no generic SQL endpoint/model SQL;
- all supported metrics/filters compile deterministically;
- all unsupported concepts are intercepted before query;
- privacy sanitizer covers columns and narrations;
- every result has reproducible receipt/records/export;
- state races/idempotency tested;
- `make all` and backend test suite pass;
- model/e2e benchmark evidence saved;
- no runtime import/read of `evaluation/expected_*`.
