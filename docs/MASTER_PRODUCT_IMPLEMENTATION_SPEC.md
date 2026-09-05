# Master Product and Implementation Specification

**Product:** LedgerProof / Finance AI Bot  
**Hackathon:** TBX — BVP Tech Catalyst  
**Schema version:** organiser source schema v1; product contract v2.0  
**Frontend:** React + TypeScript  
**Backend:** Python + Django + Django REST Framework  
**Database:** MySQL 8.0+  
**Fixture:** `tiby-finance-fixture-v2.0.0`

This document is the primary source of truth for product behavior. When an implementation detail
is more specific elsewhere, this document sets the intent and the referenced contract sets the
wire/field-level shape.

---

## 1. Executive summary

Finance users should be able to ask a plain-language question about account and transaction data
and receive a direct answer without opening a dashboard. The answer must be numerically correct,
traceable to source records, explicit about interpretation and able to decline questions the source
cannot support.

The supplied database is intentionally narrow: `bank`, `account` and `transaction`. Therefore the
winning product is not a general finance chatbot. It is a highly reliable natural-language layer for:

- debit and credit movement;
- net cash flow;
- transaction counts, averages and extremes;
- bank/account/entity/program filtering and breakdowns;
- current available-balance snapshots;
- exact transaction/reference lookup;
- sanitized source-record drill-down and export;
- explicit no-answer behavior for missing concepts.

The language model is a parser, not the calculator. It emits a constrained interpretation draft.
Deterministic code resolves dates/entities, validates scope and compiles an allow-listed query.
MySQL/Python `Decimal` computes the facts. A final response is packaged in an immutable
`AnswerReceipt` that shows the exact range, filters, formula, source count, warnings and records.

---

## 2. Product problem

Today a finance or business user often has to:

1. know which bank/account/report contains the answer;
2. translate business language into database terminology;
3. select the correct date window and transaction direction;
4. avoid spreadsheet/date/sign errors;
5. verify a total against hundreds of rows;
6. wait for finance operations when they lack access or confidence.

A normal chatbot improves the interaction but introduces a worse failure mode: a plausible
financial number that was not calculated from the data. LedgerProof optimizes for **defensible
answers**, not maximal answer rate.

### Product thesis

A finance assistant is trustworthy when it can prove five things:

- what question it believed the user asked;
- which source fields and rows it used;
- which deterministic operation produced the value;
- which checks passed or warned;
- why it did not answer when evidence was insufficient.

---

## 3. Goals and success criteria

### 3.1 P0 goals

1. Correctly interpret a well-scoped set of transaction and balance questions.
2. Calculate every official number in MySQL/Python, never in the model/browser.
3. Return exact source records and a reproducible receipt for every computed result.
4. Support natural-language dates and multi-turn refinements.
5. Clearly distinguish verified, qualified, clarification, unsupported, no-data and validation-failed states.
6. Mask sensitive fields and neutralize record-based prompt injection/XSS.
7. Use a lightweight model and record benchmark evidence for the choice.
8. Remain usable against millions of rows through indexed aggregation and bounded pagination.

### 3.2 Success metrics

The team should report actual results, not target claims, for:

- intent/metric exact match;
- date-range exact match;
- filter exact match;
- numeric exact match to two decimals;
- clarification precision/recall;
- unsupported-question refusal rate;
- privacy/redaction pass rate;
- multi-turn context accuracy;
- SQL execution success;
- p50/p95 latency by pipeline stage;
- input/output tokens and cost per correct answer;
- export-to-receipt source count/hash equality.

Recommended minimum launch gates for the demo build:

| Dimension | Gate |
|---|---:|
| Numeric accuracy on executable gold cases | 100% |
| Unsupported/refusal cases | 100% no fabricated number |
| Required privacy tests | 100% |
| Date/filter/metric plan accuracy | ≥95% or route uncertain cases to clarification |
| Multi-turn gold accuracy | ≥90% |
| P95 simple aggregate latency on fixture | <2 seconds |
| P95 total assistant response with model | <5 seconds |

These are release gates, not claims. Save the measured run in the evaluation results file.

---

## 4. Non-goals

- Live banking, ERP, payment or reconciliation integrations
- Production authentication, RBAC or multi-tenant isolation
- Write operations, payment initiation or data modification
- Canonical vendor/payee identification
- Reconciliation status or outstanding amount
- Chart-of-accounts/category reporting
- Historical balances, forecasts or budgets
- Tax/accounting advice
- Arbitrary text-to-SQL
- General web/knowledge answers inside the finance chat
- Supporting every finance question

When a user asks an out-of-scope finance question, the product explains the missing source field and
suggests the closest safe supported action.

---

## 5. Personas and jobs to be done

### 5.1 Finance manager/controller

**Needs:** quick movement/balance answers, reliable period comparisons, evidence for review.  
**Fear:** a confident but wrong number being forwarded to leadership.  
**Success:** can answer a routine question and inspect records without asking an analyst.

### 5.2 Finance operations analyst

**Needs:** exact transaction/reference lookup, account/bank filters, export.  
**Fear:** hidden fuzzy matching, duplicate references, leaking account/UTR values.  
**Success:** finds the right row(s), understands ambiguity and exports a controlled result.

### 5.3 Business user

**Needs:** plain language and understandable definitions.  
**Fear:** finance terminology and unclear date/sign conventions.  
**Success:** gets a direct answer with a human-readable explanation and no dashboard training.

### 5.4 Auditor/reviewer/judge

**Needs:** traceability, reproducibility, visible limitations, model-efficiency evidence.  
**Fear:** hardcoded demo answers or a model doing hidden arithmetic.  
**Success:** can open the receipt, query plan, validations and rows and reproduce the total.

### 5.5 Developer/data owner

**Needs:** strict contracts, predictable query catalogue, test fixtures, observability.  
**Fear:** arbitrary SQL, schema drift, timezone/collation bugs.  
**Success:** can add a metric through an explicit, reviewable path.

---

## 6. Source data contract

### 6.1 Tables

```text
bank(bank_code PK, bank_name)
  1 ── * account(account_id PK, entity_id, account_number, program_id,
                  available_balance, bank_code FK)
          1 ── * transaction(transaction_id PK, account_id FK, transaction_date,
                             transaction_type, description, transaction_amount,
                             transaction_reference_id, utr_number)
```

The executable DDL is `database/schema.sql`; field-by-field behavior is in
`data/csv/data_dictionary.csv`.

### 6.2 Schema implications

- Currency is not stored per row; the hackathon assumption provides a single INR currency.
- `transaction_amount` is absolute. Debit/credit direction is separate.
- `available_balance` is current, not time-series data.
- No vendor, category, payout or reconciliation fact exists.
- Description is unstructured and can contain sensitive/hostile text.
- References are not guaranteed unique.
- IDs are strings. One supplied ID fails strict UUID parsing despite the documentation calling it a UUID.
- `transaction` should be quoted in raw SQL.
- MySQL session timezone affects `TIMESTAMP`; fixture behavior is `+05:30`.

---

## 7. Supported question catalogue

### 7.1 Verified metrics

| Metric | Example | Deterministic definition |
|---|---|---|
| Debit total | “How much did we spend in August?” | Sum amount for debit rows in exact range. |
| Credit total | “How much came in last month?” | Sum amount for credit rows. |
| Net cash flow | “What was net movement?” | Credit total minus debit total. |
| Transaction count | “How many transactions?” | Count filtered source rows. |
| Average transaction | “Average debit amount?” | Decimal average of explicitly filtered rows. |
| Largest transaction | “Largest credit in June?” | Highest amount with deterministic ID tie-break. |
| Current balance | “Available balance across HDFC?” | Sum current balance across distinct filtered accounts. |
| Account count | “How many program 46 accounts?” | Count filtered account rows. |
| Transaction lookup | “Find reference HDFCH…” | Exact ID/reference equality. |

### 7.2 Supported dimensions and filters

- exact bank code or canonical bank name;
- exact account ID;
- exact entity ID;
- exact integer program ID;
- credit/debit type;
- transaction timestamp range;
- exact transaction ID;
- exact, case-sensitive transaction reference;
- amount minimum/maximum;
- confirmed literal description substring, with qualification.

### 7.3 Supported groupings

- bank code/name;
- account ID;
- entity ID;
- program ID;
- transaction type;
- day/month.

Two grouping levels are the v1 maximum. Grouping by raw description is excluded because high
cardinality and narration variation produce misleading results.

### 7.4 Explicitly unsupported

- vendor or beneficiary attribution as an authoritative dimension;
- payout status or payout date;
- reconciliation status/outstanding amount;
- chart-of-accounts category;
- historical balance;
- forecast/budget/future cash balance;
- named entity lookup without a master table;
- raw account-number search;
- UTR search in encrypted/tokenized mode.

---

## 8. Finance and date semantics

The machine-readable contract is `contracts/semantic_metrics.yaml`.

### 8.1 Money

- MySQL uses `DECIMAL(15,2)`.
- Python uses `Decimal` created from strings.
- JSON transmits decimal strings.
- React retains strings and only formats for display.
- No `number`, float, JavaScript arithmetic or model arithmetic is authoritative.
- Indian currency formatting uses `en-IN` while copy/export retains exact decimal form.

### 8.2 Debit/credit

`transaction_amount` does not carry a sign. Official formulas are:

```text
debit_total = Σ amount where type = debit
credit_total = Σ amount where type = credit
net_cash_flow = credit_total - debit_total
```

Do not negate debits inside the source table or double-negate in presentation.

### 8.3 Date ranges

- Use `[start_inclusive, end_exclusive)`.
- Interpret explicit dates in `Asia/Kolkata` unless the user supplies a supported timezone.
- For the fixture, “last month” is August 2026 because `data_as_of` is 3 September 2026.
- “This month” means 1–3 September through an exclusive 4 September boundary.
- “Recently”, “lately” and similar terms require clarification.
- Comparisons use equal, calendar-aligned periods where possible.
- Never substitute the server's current date for the fixture anchor.

### 8.4 Current balance

- `available_balance` is summed only over distinct account rows.
- Negative values are valid and displayed as such.
- A historical-date modifier changes the request to unsupported; it must not be silently ignored.
- A transaction filter cannot be applied to current balance unless it resolves to an account set
  explicitly and the UI explains the scope.

### 8.5 References

- Bare “reference” → `transaction_reference_id`.
- Exact and case-sensitive.
- Zero matches → no-data.
- Multiple matches → qualified with all rows.
- Never fuzzy match or fall back to UTR.
- Explicit UTR → unsupported in default storage mode.

### 8.6 Description search

- Literal, case-insensitive substring only after confirmation when phrased like a vendor request.
- Answer wording says “transactions whose description contains …”.
- Confidence/status is `qualified`.
- Never use it to claim payout, vendor identity, category or reconciliation.
- Redact known account numbers from narration before display/model/export.

---

## 9. Answer state machine

Every user turn ends in one of these product states:

### `verified`

The concept is directly represented; query executed; required checks passed; number/records can be shown.

### `qualified`

The deterministic result is valid but a material limitation applies. Examples:

- literal description search;
- duplicate transaction reference;
- partial data coverage;
- duplicate-lookalike source warning.

### `needs_clarification`

Multiple plausible interpretations could materially change the answer. No number is shown. The UI
provides a direct question and 2–5 selectable options where possible.

### `unsupported`

The source lacks the field or the operation is disabled for privacy/security. No query runs and no
number is shown. The UI names the missing concept and closest safe alternative.

### `no_data`

A valid query ran and matched zero rows. Do not conflate this with unsupported or system failure.

### `validation_failed`

A required integrity/control check failed after execution. Suppress the number and provide a trace ID.

Transport/system errors use `ProblemDetails` and are separate from these semantic states.

---

## 10. End-to-end assistant pipeline

### Stage 0: request envelope

The browser sends:

- conversation ID;
- stable message ID;
- text;
- locale/timezone;
- idempotency key;
- expected context version.

The backend rejects oversized/empty input and stale context before model work.

### Stage 1: lightweight interpretation

The model receives:

- the user's current message;
- a compact, sanitized summary of QueryState;
- supported metrics/filter vocabulary;
- date anchor;
- no raw finance rows and no raw sensitive values.

It returns `InterpretationDraft`: intent, raw phrases, mentions, ambiguities and unsupported concepts.
It cannot return SQL or an amount.

### Stage 2: deterministic resolution

Code resolves:

- metric phrase to one metric;
- relative/explicit dates to exact half-open timestamps;
- canonical bank names/codes;
- account/entity/program IDs against source metadata;
- reference kind and exact value;
- follow-up patches against the last successful QueryPlan;
- missing/contradictory filters;
- schema gaps and privacy restrictions.

Output is a validated `QueryPlan` or a clarification/unsupported plan.

### Stage 3: allow-listed query compilation

A metric-specific compiler chooses:

- known table joins;
- known aggregate expression;
- known predicates;
- known group/sort fields;
- a bounded row/page limit.

Only bound values come from the request. No free-form identifier or SQL fragment is accepted.

### Stage 4: execution

- Use a read-only connection.
- Set `time_zone='+05:30'`.
- Apply query timeout.
- Execute aggregate and source-ID/record queries independently where needed.
- Keep money as `Decimal`.
- Do not call the model while a DB transaction is open.

### Stage 5: validation

Required checks include:

- QueryPlan contract valid;
- date start < end and no unsupported future range assumptions;
- enum/domain/foreign-key resolution valid;
- decimal precision preserved;
- row count matches lineage query;
- source IDs hash deterministically;
- component totals reconcile for net/comparison;
- largest amount matches the returned record;
- privacy sanitization completed;
- no source field outside the allow-list entered model/presentation.

Warnings include duplicate-looking rows, duplicate reference, null narration, zero amount or partial coverage.

### Stage 6: answer construction

Prefer deterministic templates for the headline/summary. A lightweight wording model is optional and
may receive only ComputedFacts plus safe labels. The server compares every numeric token in generated
wording against allowed computed values; mismatch falls back to deterministic wording.

### Stage 7: receipt and state commit

- Create immutable AnswerReceipt.
- Persist/cache receipt and normalized source predicate outside the finance DB.
- Update QueryState using compare-and-swap on context version.
- Return the receipt.
- A late older request cannot overwrite newer state.

---

## 11. Multi-turn behavior

### 11.1 State model

QueryState stores:

- dataset version/cutoff;
- last successful normalized plan;
- active receipt scope for “those” references;
- pending clarification;
- context version and message IDs.

It does not store raw sensitive source values.

### 11.2 Patch semantics

A follow-up is a patch, not a fresh unconstrained interpretation:

- “Only HDFC” adds/replaces `bank_codes`.
- “What about credits?” replaces debit metric/type; it does not create contradictory filters.
- “How does that compare with the month before?” retains metric/filters and adds comparison range.
- “Which bank was that?” uses the selected transaction receipt scope.
- “What was the balance last month?” inherits balance but becomes unsupported because history is absent.

### 11.3 Clarification lifecycle

- The pending clarification includes option IDs and patches.
- A selected option is validated against the same context version.
- Free-text clarification is reinterpreted against the pending question.
- A new unrelated request cancels the pending clarification.
- Browser refresh fetches server state.

### 11.4 Race handling

- Each mutation includes expected context version.
- Server returns 409 `stale_context` on mismatch.
- React cancels previous requests where possible and ignores receipts with an older context version.
- Idempotency prevents double submission on retries/double clicks.

---

## 12. Functional requirements

### 12.1 Ask/chat

- Free-form input up to 2,000 characters.
- Suggested questions based only on supported schema.
- Streaming is optional; do not stream a tentative numeric answer.
- Show interpretation and progress states separately.
- Preserve conversation history in the current session.
- Allow starting a new conversation.
- Support keyboard submission and multiline input.

### 12.2 Answer receipt

For verified/qualified results show:

- direct answer and exact value;
- status badge;
- data-as-of;
- metric/date/filter chips;
- formula/human-readable execution plan;
- validation checks;
- source row/account count;
- warning list;
- breakdown table/chart where requested;
- records tab/drawer;
- sanitized SQL with placeholders as an advanced disclosure;
- CSV/XLSX export tied to receipt;
- copy answer/receipt link.

For non-answer states show no numeric placeholder that could be mistaken for zero.

### 12.3 Transaction explorer

- Date/type/bank/account/entity/program/reference/amount/description filters.
- Keyset pagination.
- Raw amount string plus formatted display.
- Masked account and UTR.
- Description escaping and account-number redaction.
- Exact reference mode visibly different from description search.
- Qualified banner for narration search.
- Filter state reflected in URL where safe; never include UTR/account number.
- Export uses server-side predicate, not current page rows.

### 12.4 Accounts

- Canonical bank/name, masked account, program, short entity ID, current balance.
- Summary cards by bank/program.
- Negative balance is not rendered as a system error.
- No historical date picker.
- Clicking an account opens transaction explorer by account ID.

### 12.5 Data health

Show:

- source row counts;
- earliest/latest transaction;
- dataset cutoff/timezone/currency;
- orphan FK checks;
- null description/reference/UTR counts;
- zero amounts;
- duplicate-lookalike signatures;
- duplicate transaction references;
- narration account-number leakage requiring redaction;
- strict-UUID parse anomalies;
- schema/index availability;
- status and blocking/non-blocking classification.

### 12.6 Glossary/capabilities

- Metric definitions and examples.
- Date semantics.
- Difference between transaction reference and UTR.
- Sensitive-field behavior.
- Direct list of unavailable concepts.
- Suggested supported reformulations.

### 12.7 Export

- CSV and XLSX are good-to-have/P0.5.
- Receipt-scoped, deterministic row order.
- Includes metadata sheet/header: query ID, cutoff, interpretation, row count, hash.
- No raw account or UTR.
- Formula-injection defense: prefix cells beginning `=`, `+`, `-`, `@` where needed.
- Row cap and asynchronous job beyond inline threshold.
- Expiry returns 410 with clear regeneration action.

### 12.8 Evaluation page

- Select model/prompt version and benchmark case subset.
- Show metric/date/filter/numeric/refusal/privacy/multi-turn scores separately.
- Show p50/p95 latency, token use and cost.
- Drill into failed cases without exposing gold values to runtime routes.
- Mark results as measured and timestamped.

---

## 13. Information architecture and routes

| Route | Purpose |
|---|---|
| `/ask` | Default chat and answer-receipt workspace |
| `/transactions` | Sanitized transaction explorer |
| `/accounts` | Current account/balance view |
| `/data-health` | Source quality and controls |
| `/glossary` | Supported definitions and limitations |
| `/evaluation` | Model/parser benchmark tooling |

Desktop uses a left navigation rail, central workspace and optional right evidence panel. Tablet
collapses the evidence panel into a drawer. Mobile uses bottom navigation and full-screen sheets.
Full page behavior is in `docs/UI_UX_SPEC.md`.

---

## 14. Backend architecture

Suggested Django apps/modules:

```text
backend/
  config/
  finance_data/
    models.py             # unmanaged Bank, Account, Transaction
    repositories.py       # read-only source access
    serializers.py        # sanitized transport rows
    health.py
  assistant/
    contracts.py          # Pydantic models generated/aligned to JSON Schema
    interpreter.py
    resolver.py
    date_resolver.py
    entity_resolver.py
    compiler/
      registry.py
      transaction_metrics.py
      balance_metrics.py
      lookup.py
    executor.py
    validators.py
    presenter.py
    receipts.py
    state.py              # Redis compare-and-swap
    privacy.py
  exports/
  evaluation/
  api/
```

The database user is read-only after fixture setup. Django's own auth/session tables should use a
separate database if introduced; for the hackathon, use Redis/sessionless demo state.

Detailed compiler behavior is in `docs/BACKEND_QUERY_ENGINE_SPEC.md`.

---

## 15. Frontend architecture

Suggested structure:

```text
frontend/src/
  app/
  routes/
  features/assistant/
  features/transactions/
  features/accounts/
  features/data-health/
  features/evaluation/
  components/
  api/generated/
  lib/money.ts
  lib/dates.ts
  lib/requestState.ts
  tests/
```

Use TanStack Query for server state and React Router for routes. Keep AnswerReceipt immutable in
the client cache. Charts consume server-supplied breakdowns; they do not calculate official totals.

---

## 16. API contract

The canonical API is `contracts/openapi.yaml`. Primary endpoints:

- `GET /api/v1/metadata`
- `GET /api/v1/banks`
- `GET /api/v1/accounts`
- `GET /api/v1/transactions`
- `GET /api/v1/data-health`
- `POST /api/v1/assistant/messages`
- `GET /api/v1/assistant/conversations/{id}/state`
- `GET /api/v1/assistant/receipts/{query_id}`
- `GET /api/v1/assistant/receipts/{query_id}/records`
- `GET /api/v1/assistant/receipts/{query_id}/export`
- `POST /api/v1/evaluation/runs`

Do not create a generic `/query` accepting SQL, table names or column lists.

---

## 17. Explainability and trust design

### Answer receipt hierarchy

1. **Answer:** direct value and sentence.
2. **Interpretation:** metric, exact period, filters, grouping/comparison.
3. **Calculation:** named deterministic formula and component totals.
4. **Evidence:** row/account count, breakdown, records and source hash.
5. **Checks:** pass/warn/fail outcomes.
6. **Limitations:** why status is qualified or unsupported.
7. **Technical detail:** sanitized statement/parameters for reviewers.

Avoid anthropomorphic statements like “I looked at your finances.” Prefer “The query matched 205
debit transactions.”

### Confidence

Confidence is an operational state, not a model probability. Never show an unexplained 87% score.
Model parser confidence may influence whether to clarify, but it is not the public trust signal.

---

## 18. Privacy and security

### Sensitive fields

- account number: restricted, masked last four;
- UTR: restricted, masked/lookup disabled;
- balances/amounts: confidential, shown only as necessary;
- entity/account IDs: internal;
- description: potentially sensitive/untrusted.

### Prompt injection

Database content is data, not instruction. The model should normally receive aggregate facts and
safe labels only. If a future feature includes narration, wrap it as structured quoted data, state
that it is untrusted and never allow it to modify tools/policies.

### XSS

React renders text nodes. `dangerouslySetInnerHTML` is forbidden for answer/source content. CSV/XLSX
exports protect against spreadsheet-formula injection.

### SQL injection

No model SQL, bound parameters only, allow-listed field mappings, strict page/sort enums and DB
read-only permission.

See `docs/SECURITY_PRIVACY_AND_TRUST.md`.

---

## 19. Performance and 20M-record considerations

The organiser mentions up to 20M source records. The demo fixture does not prove that scale. Design
for it and benchmark honestly:

- composite date/type/account indexes;
- index on plaintext reference;
- aggregation in MySQL;
- source previews capped at 100;
- keyset pagination, not deep OFFSET;
- separate total and row queries;
- query timeout and cancel;
- no full table sent to model/browser;
- bounded group cardinality;
- explain/analyze representative plans;
- receipt cache keyed by dataset version + normalized plan;
- async export for large sets;
- avoid `%substring%` narration queries at high scale or explicitly label their limitation;
- optional full-text index as exploratory acceleration, not canonical vendor logic.

Record hardware, MySQL version, row count, query, cold/warm state and p50/p95 before presenting a
performance number.

---

## 20. Observability

Structured event fields:

- trace ID, query ID, conversation ID, message ID;
- context version;
- dataset version/cutoff;
- model/prompt version;
- normalized metric/filter/date/group IDs;
- compiler template ID and plan hash;
- row/account count and source hash;
- validation statuses;
- model/query/validation/total latency;
- token use/cost;
- semantic outcome status;
- error code/retryability.

Never log raw account numbers, UTRs, full descriptions or unbounded user input. Retain sampled,
redacted messages only if required for the hackathon evaluation and disclose it.

---

## 21. Failure behavior

| Failure | User state | Number shown? | Retry? |
|---|---|---:|---:|
| Ambiguous date/vendor-like term | needs clarification | No | after clarification |
| Missing source field | unsupported | No | only after schema change |
| Valid zero rows | no data | No; do not show ₹0 as answer | user can adjust filters |
| Query timeout | problem detail | No | Yes |
| Required validation fail | validation failed | No | Yes after investigation |
| Model timeout | deterministic fallback if possible, else problem | No tentative number | Yes |
| Stale conversation write | 409 stale context | No new answer | client refresh/replay |
| Export expired | 410 | n/a | regenerate |
| Description search duplicate warnings | qualified | Yes | n/a |

Error copy must say what happened, what was preserved and what the user can do next.

---

## 22. QA strategy

Testing layers:

1. Fixture integrity and gold recomputation.
2. Pure metric/date/privacy functions.
3. QueryPlan schema and deterministic resolver tests.
4. Compiler SQL snapshot/parameter tests.
5. MySQL integration tests against fixture.
6. API contract tests.
7. React component/accessibility tests.
8. Multi-turn race/idempotency tests.
9. End-to-end demo flows.
10. Model benchmark and adversarial prompts.
11. Scale/query-plan tests.

Critical regression cases are in `evaluation/edge_case_manifest.csv`, including:

- exact month boundaries at microsecond precision;
- duplicate-lookalike rows;
- duplicate references;
- null narration;
- zero amount;
- max `DECIMAL(15,2)`;
- malformed UUID-like source ID;
- account number embedded in narration;
- encrypted UTR with missing plaintext reference;
- case-sensitive reference;
- prompt injection and script text;
- Unicode narration.

See `docs/BUG_AND_QA_PLAYBOOK.md`.

---

## 23. Model evaluation and selection

Benchmark the smallest viable models on `InterpretationDraft`, not prose quality alone.

Score separately:

- intent/metric;
- date range;
- bank/account/entity/program/type/reference extraction;
- grouping/comparison;
- ambiguity detection;
- unsupported concept detection;
- exact structured-output validity;
- multi-turn patches;
- latency/tokens/cost.

Then run end-to-end numeric tests to catch compiler/resolver bugs. Select the lowest-cost/smallest
model that clears the release gates. If a smaller model routes uncertainty to clarification, that
can be better than a larger model that confidently guesses.

---

## 24. Implementation phases

### Phase 0 — schema alignment and fixture

Complete when:

- only three source tables remain;
- MySQL DDL/loader works;
- fixture/gold/edge tests pass;
- gaps are documented.

### Phase 1 — deterministic vertical slice

- unmanaged models/repository;
- metadata/bank/account/transaction endpoints;
- privacy sanitization;
- manually constructed debit-total QueryPlan;
- compiler/executor/validator;
- receipt/records endpoint;
- Ask UI for one question.

No model is required yet. This proves the trust architecture.

### Phase 2 — lightweight natural-language parser

- InterpretationDraft prompt/schema;
- metric/date/filter resolvers;
- clarification/unsupported handling;
- benchmark harness;
- remaining supported metrics.

### Phase 3 — multi-turn and evidence UX

- Redis QueryState/versioning/idempotency;
- comparison/follow-up patches;
- source records, breakdowns and sanitized query disclosure;
- exports.

### Phase 4 — supporting pages and hardening

- Transactions, Accounts, Data Health, Glossary, Evaluation;
- accessibility/responsive states;
- adversarial/privacy/race tests;
- scale benchmark;
- demo/deck/README captures.

Dependencies and tickets are in `project_backlog.csv`.

---

## 25. Definition of done

A submission is done when:

- a fresh clone can start MySQL/Redis and load the fixture;
- React and Django launch from documented commands;
- canonical demo questions return expected receipt states;
- numbers exactly match source recomputation;
- records/exports match receipt count/hash;
- raw account/UTR never appears in response/log/export/model fixtures;
- vendor/reconciliation/history questions return no fabricated number;
- all P0 tests and `make all` pass;
- model results are measured and saved;
- architecture diagram, README, sample questions and deck are complete;
- no hardcoded route/component answer values exist;
- limitations are visible in the demo.

---

## 26. Product positioning for the presentation

Avoid: “ChatGPT for finance data.”

Use:

> **LedgerProof turns finance questions into validated query plans, deterministic calculations and auditable answer receipts. It gives a number only when the database can prove it.**

The source schema's limitations become a demonstration strength: the assistant knows that
“unreconciled” and “vendor payout” are unavailable rather than hallucinating a classification from
bank narration.
