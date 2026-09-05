# LedgerProof — Master Product and Implementation Specification

**Document status:** implementation source of truth  
**Product:** LedgerProof Finance Assistant  
**Synthetic tenant:** Northstar Labs India Private Limited  
**Audience:** product, design, frontend, backend, data, model, QA, demo, and coding agents  
**Stack:** React + TypeScript + Vite; Python + Django + Django REST Framework; PostgreSQL; optional Redis/Celery  
**Dataset anchor:** 3 September 2026; Asia/Kolkata; INR only

This document defines what to build, why it exists, how every screen behaves, which financial semantics are allowed, how the system prevents fabricated numbers, and how agents should deliver it. Detailed implementation rules live in the linked specialist documents; this file resolves priorities and cross-document behavior.

---

## 1. Executive product definition

LedgerProof is a conversational interface over structured finance data. A user asks a plain-language question, the system converts it into a constrained QueryPlan, deterministic code queries the supplied dataset, validation checks run, and the UI presents an answer with an inspectable AnswerReceipt.

The product is not a general financial adviser and not an unrestricted text-to-SQL bot. It supports a deliberately bounded domain:

- posted vendor spend;
- completed vendor payouts and net cash outflow;
- transaction and payout lookup;
- reconciliation status and open amounts;
- grouping by approved vendor, account, category, department, project, status, date, or payment method;
- period comparisons;
- source-record drill-down and export;
- transparent data-health and simple anomaly/duplicate callouts.

The model never calculates a financial result. It may interpret language and optionally word an explanation from immutable computed facts. A numeric answer is allowed only after deterministic execution and required validation checks succeed.

### 1.1 Winning product narrative

Do not pitch “chat with your finance data.” Many products already do that. Pitch:

> LedgerProof is an auditable natural-language query compiler for finance. Every answer arrives with a receipt that shows what the user asked, what the system interpreted, which records were used, how the number was computed, and whether validation passed.

### 1.2 Success definition

The prototype succeeds when a finance manager can obtain a correct answer faster than navigating a dashboard while retaining enough evidence to verify it. The assistant must also fail safely: ambiguity, missing fields, unavailable periods, validation failures, and unsupported forecasting must never produce plausible-looking numbers.

---

## 2. Challenge-to-product mapping

| Hackathon requirement | LedgerProof implementation |
|---|---|
| Natural-language query handling | Deterministic pre-parser plus lightweight structured-output model and semantic resolvers |
| Grounded retrieval | Every answer executes against PostgreSQL using a canonical QueryPlan |
| Accurate computation | Bound SQL and Python `Decimal`; model never aggregates |
| Verifiable answers | AnswerReceipt, breakdown, records, checks, query explanation, export |
| Hallucination guardrails | Unsupported/ambiguous state gates, number provenance check, no model SQL |
| Lightweight model | Benchmark smallest viable parser; deterministic code carries semantics and arithmetic |
| Multi-turn | Versioned QueryState and explicit state operations |
| Explainability | Human-readable interpretation and calculation receipt, not hidden chain of thought |
| CSV/Excel | Receipt-linked deterministic exports with parity checks |
| Confidence | Operational states: verified, qualified, needs clarification, not answerable, no matching rows, error |
| Anomaly callout | Simple declared baseline and unusual-payout rule; never claim fraud |
| 20M record assumption | Indexing, bounded queries, cursor pagination, scale-test plan, honest measurements |

---

## 3. Product principles and non-negotiable invariants

1. **No source, no number.** A financial value must originate in `ComputedFacts` for the same query ID.
2. **Interpretation before execution.** The exact metric, date field, range, filters, entities, grouping, and comparison must be canonical.
3. **Ambiguity blocks totals.** “Acme,” “recent,” bare “Q2,” and undefined pronouns require clarification when materially ambiguous.
4. **The model does not write SQL.** It returns a constrained interpretation draft; deterministic resolvers and compilers own IDs, dates, filters, joins, and arithmetic.
5. **The model does not calculate.** PostgreSQL/Python compute; the model may only explain supplied facts.
6. **Every material answer has an AnswerReceipt.** Interpretation, lineage, validation, freshness, and reproducibility are first-class UI.
7. **Failure is visible, not hidden.** The user sees data gaps, duplicate candidates, missing reconciliation links, stale data, and failed checks.
8. **Conversation state is typed and versioned.** A later answer cannot be overwritten by a slower earlier request.
9. **Exports are part of the answer.** They must match the immutable receipt, not a separately recomputed browser table.
10. **Record text is untrusted.** Descriptions, memos, vendor names, and uploaded strings cannot alter system instructions or render raw HTML.
11. **Finance uses exact decimals.** PostgreSQL `NUMERIC(18,2)` and Python `Decimal`; never binary float.
12. **Relative dates use the dataset anchor.** “Last month” means August 2026 in this fixture, even when the app is run later.
13. **Signed records remain signed.** Credits and reversals reduce posted spend; duplicates remain included and are warned, not silently deleted.
14. **No inflated claims.** Accuracy, latency, cost, and 20M-record performance require recorded benchmark evidence.

---

## 4. Users, jobs, and product outcomes

### 4.1 Finance manager / controller

Jobs:

- answer recurring spend and payout questions without opening several reports;
- investigate why totals changed;
- find unreconciled items and owners;
- prove a number during close, review, or audit preparation;
- export exactly the supporting rows.

Outcome: faster lookup and investigation without sacrificing traceability.

### 4.2 FP&A or finance business partner

Jobs:

- compare periods;
- rank vendors/categories;
- isolate drivers of change;
- produce a defensible first-pass narrative;
- identify unusual items for follow-up.

Outcome: less manual filtering and more time spent interpreting the business.

### 4.3 Business user outside finance

Jobs:

- ask a bounded factual question in normal language;
- understand finance terminology;
- avoid waiting for finance ops to run a report.

Outcome: self-service answers with visible limits and definitions.

### 4.4 Finance operations / reconciliation analyst

Jobs:

- list open, partial, disputed, or aged items;
- locate source records and references;
- distinguish the full transaction amount from the remaining open amount;
- export a follow-up queue.

Outcome: quicker exception handling and fewer mistaken open-balance calculations.

### 4.5 Hackathon judge

Needs to see, quickly:

- exact answer accuracy;
- proof that the number is data-grounded;
- safe behavior under ambiguity and missing data;
- lightweight model efficiency;
- polished, understandable UI;
- a believable business impact story.

---

## 5. Scope

### 5.1 P0 supported question families

1. **Aggregate:** total completed payouts, net cash outflow, posted vendor spend, open reconciliation amount/count.
2. **Breakdown:** by vendor, category, account, department, cost center, project, date bucket, payment method, or reconciliation status where allowed.
3. **Ranking:** top/bottom vendors or categories with explicit metric and period.
4. **Comparison:** previous period, named period, absolute change, and percentage change with zero-baseline safeguards.
5. **Lookup/list:** transaction, payout, vendor, account, or reconciliation records with filters.
6. **Ageing:** open items older than a threshold, based on the declared date field and anchor.
7. **Data quality:** freshness, missing reconciliation rows, duplicate candidates, null/unknown categories.
8. **Simple anomaly:** declared unusually-large-payout rule with historical baseline.
9. **Definitions:** explain metric/date/status semantics without inventing data.
10. **Export:** CSV and XLSX from the immutable answer lineage.

### 5.2 P1 after core accuracy

- richer trend charts;
- saved questions/favourites;
- conversation rename/delete;
- shareable deep links within the demo;
- asynchronous large export;
- model comparison page for judges;
- keyboard command palette.

### 5.3 Explicitly out of scope

- production authentication, roles, row-level security, or multi-tenancy;
- real banking/ERP connections or write actions;
- forecasts, cash-balance predictions, budgets, and scenarios;
- payroll, employee compensation, tax advice, and statutory filings;
- multi-currency conversion;
- arbitrary SQL or every possible finance question;
- fraud claims or autonomous accounting decisions.

---

## 6. Finance semantics

`contracts/semantic_metrics.yaml` is authoritative. The implementation must not infer definitions from display labels alone.

### 6.1 Completed vendor payout amount

- source: `vendor_payouts`;
- calculation: `SUM(gross_amount)`;
- mandatory status: `completed`;
- date field: `payout_date`;
- excludes pending, failed, reversed attempts and payment fees.

### 6.2 Net cash outflow

- source: `vendor_payouts`;
- calculation: `SUM(net_cash_outflow)`;
- completed only;
- includes payment fees;
- pending/failed/reversed cash outflow is zero.

### 6.3 Posted vendor spend

- source: posted transactions joined to chart of accounts;
- accounts: Expense and COGS only;
- date field: `posting_date`;
- signed amount is retained;
- credits and reversals reduce spend;
- draft/voided/non-expense records are excluded.

### 6.4 Open reconciliation amount

- source: reconciliation status joined to transactions;
- statuses: unreconciled, partially reconciled, disputed;
- calculation: `SUM(unreconciled_amount)`;
- partially reconciled rows contribute only the remaining amount;
- posted transactions only.

### 6.5 Dates

All ranges are half-open `[start, end_exclusive)`.

- `last month` at data_as_of 2026-09-03 → 2026-08-01 to 2026-09-01;
- `this month` → 2026-09-01 to 2026-09-04;
- `last 30 days` → 2026-08-05 to 2026-09-04;
- `recent` → clarify;
- bare `Q2` → clarify calendar/fiscal and year;
- explicit dates are interpreted in Asia/Kolkata.

### 6.6 Vendor resolution

Resolution order:

1. exact vendor ID;
2. exact unique normalised alias;
3. exact display/legal name;
4. bounded fuzzy candidates for clarification only.

`Acme` and `ABC` are intentionally ambiguous. Never auto-select one.

---

## 7. Information architecture and complete page plan

Detailed visual and interaction requirements are in `docs/UI_UX_SPEC.md`. The following matrix defines product ownership and API dependencies.

| Route | Page | Primary job | Required APIs | P0 |
|---|---|---|---|---|
| `/ask` | New question | Start a grounded finance conversation | metadata, conversations, message | Yes |
| `/ask/:conversationId` | Conversation | Continue, inspect, clarify, correct, export | conversation, message, receipt, records, export | Yes |
| `/explorer` | Data Explorer | Directly filter and inspect records | explorer transactions/payouts, metadata | Yes |
| `/reconciliation` | Reconciliation | Investigate open/partial/disputed items | reconciliation list/summary, receipt export | Yes |
| `/data-health` | Data Health | See freshness, coverage, duplicates, missing links | health summary/details | Yes |
| `/glossary` | Definitions | Understand metrics, fields, statuses, date behavior | metadata/glossary | Yes |
| `/evaluation` | Evaluation | Show model efficiency and benchmark evidence | local/demo evaluation endpoints | P1 but high demo value |
| `/about` | About | Explain scope, architecture, synthetic data, privacy | static/meta | Yes |
| `*` | Not found | Recover safely | none | Yes |

### 7.1 Global application shell

Required:

- left navigation on desktop, drawer/icon rail on smaller screens;
- company and synthetic-data labels;
- data-as-of chip, never a misleading “live” indicator;
- central content region;
- route-preserving right evidence panel on desktop;
- evidence side sheet/bottom sheet on tablet/mobile;
- persistent visible focus and skip navigation;
- error boundary with safe recovery.

### 7.2 Ask page

#### Empty state

Show one sentence, supported scope, unsupported scope, and six high-value examples. Avoid decorative marketing content that delays the demo.

#### Composer

- 1–6 visible lines, 4,000-character max;
- Enter sends; Shift+Enter inserts newline;
- stable `client_turn_id` and `Idempotency-Key` generated before request;
- Stop cancels in-flight work;
- retry reuses idempotency key;
- draft never appears as successful on network failure;
- double click/Enter cannot create duplicate turns.

#### Answer states

1. `verified` — number may be shown; all required checks pass.
2. `qualified` — computed answer may be shown with explicit data-quality warning.
3. `needs_clarification` — no financial number; show bounded choices.
4. `not_answerable` — no number; explain missing field/domain and supported alternative.
5. `no_matching_rows` — the query is valid and sufficiently covered, but no rows match; use explicit verified-zero/no-record language.
6. `error` — no number; technical or required-validation failure with retry and trace ID.

`cancelled` is a frontend request state rather than an AnswerReceipt status. A cancelled request does not create a successful turn or financial receipt.

#### Answer card

Always includes:

- plain-language result or safe refusal;
- operational status badge;
- interpretation chips: metric, exact period, date field, statuses, vendor/account filters, grouping;
- comparison and breakdown where applicable;
- source row count and data-as-of;
- warnings;
- “View evidence” and export actions;
- query/trace identifiers in evidence, not visual clutter.

#### Clarification behavior

Choices must be concrete. Example:

> “Acme” matches Acme Cloud Services and Acme Office Supplies. Which vendor did you mean?

User selection sends a normal versioned turn. Do not compute both totals unless the user explicitly asks to compare them.

### 7.3 Evidence panel

Tabs:

- **Receipt:** exact interpretation, metric definition, range, filters, grouping, result, version.
- **Records:** paginated source rows with stable sorting.
- **Checks:** passed/warned/failed validation rules and explanations.
- **Query:** human-readable execution plan; optional named query and redacted bound parameters; never hidden model chain of thought.
- **Export:** format, row count, source hash, generated time, sanitisation notes.

Opening evidence updates the URL. Refresh/back/forward must work.

### 7.4 Data Explorer

Tabs or mode switch for transactions and payouts.

Required filters:

- exact date range and selected date field;
- vendor and alias-resolved search;
- account/category;
- department/cost center/project;
- status;
- amount range;
- reconciliation status where joined safely.

Rules:

- server owns official totals;
- browser never sums paginated rows for displayed financial totals;
- filter state is URL-serialised;
- cursor pagination;
- column chooser and reset;
- empty/filter-error/loading states;
- row selection opens record detail/evidence;
- export uses server query definition.

### 7.5 Reconciliation page

Sections:

- KPI strip: open count, open amount, partial, disputed, oldest item;
- ageing buckets with declared boundaries;
- filterable table;
- owner/reason/status breakdown;
- transaction detail drawer;
- export of current immutable query.

The UI must distinguish transaction amount, reconciled amount, and remaining amount. Never label full amount as open on a partial item.

### 7.6 Data Health page

Cards and drill-downs:

- dataset version and data-as-of;
- source max dates and freshness state;
- row counts;
- missing reconciliation relationships;
- null/unknown vendor/category fields;
- possible duplicate payout pairs;
- ingestion batch coverage;
- integrity checks;
- warning impact on answers.

Every warning explains whether totals include the row and whether the answer remains verified or becomes qualified.

### 7.7 Glossary page

Searchable definitions for:

- metrics;
- date fields;
- statuses;
- accounts/categories;
- vendor resolution;
- confidence states;
- data-health codes.

Glossary content is generated from versioned semantic configuration where possible, not separately hardcoded copy.

### 7.8 Evaluation page

Demo/local only. Shows:

- selected model and prompt version;
- model size/tier and cost inputs;
- benchmark totals;
- intent/metric/date/entity/filter/refusal accuracy;
- final exact answer accuracy;
- critical safety pass/fail;
- p50/p95 latency;
- cost per correct answer;
- per-case failures without hiding them.

Never display claims before a benchmark run produces evidence.

### 7.9 About page

Explain:

- problem and narrow scope;
- deterministic architecture;
- answer receipts;
- model-choice rationale;
- synthetic data disclosure;
- limitations;
- architecture diagram;
- links to README/evaluation inside the repo.

---

## 8. Conversation and multi-turn behavior

### 8.1 QueryState

Server-authoritative state stores canonical values only:

- metric;
- exact period/date field;
- filters;
- group/sort/limit;
- comparison;
- referenced result/query IDs;
- pending clarification;
- context version.

Do not rely on raw chat history as state.

### 8.2 State operations

Supported operations:

- `SET` or `REPLACE` a field;
- `ADD`/`REMOVE` filter values;
- `CLEAR` metric/filter/comparison;
- `RESET` conversation;
- `REFER_TO_RESULT` for “those,” only when referent is stable and permitted.

Examples:

- “How does that compare with the month before?” keeps metric/filters and adds comparison.
- “Only AWS” replaces vendor filter.
- “No, use the last 30 days” replaces date range.
- “What about July?” replaces primary period while keeping supported context.
- “Start over” clears state.

### 8.3 Concurrency

Every mutation sends `expected_context_version`. Server increments on success. A stale request returns 409 and cannot overwrite newer state. Frontend discards responses whose client sequence/context version is older than the latest accepted response.

### 8.4 Clarification persistence

A clarification receipt stores candidates and the unresolved field. A concise reply such as “the cloud one” is resolved only against that pending clarification, not generic chat history.

---

## 9. System architecture

### 9.1 Frontend

- React, TypeScript strict mode, Vite;
- React Router;
- TanStack Query for server state, cancellation, and cache invalidation;
- accessible headless primitives;
- one chart library;
- Vitest, Testing Library, MSW, Playwright;
- generated/reused API types;
- no official finance aggregation in the browser.

### 9.2 Backend

- Django + Django REST Framework;
- Pydantic v2 internal contracts;
- PostgreSQL for finance and application state;
- allow-listed named SQL compilers with bound parameters;
- Django ORM for conversations, idempotency, and audit metadata;
- Redis/Celery for asynchronous XLSX/export or benchmark jobs if needed;
- ASGI via Gunicorn/Uvicorn worker;
- structured logs and trace IDs.

### 9.3 Model layer

- provider-independent adapter;
- smallest viable structured-output model;
- compact schema/semantic prompt;
- deterministic pre-parser first;
- at most one schema-repair retry;
- no raw table dumps;
- no model SQL;
- no arithmetic authority;
- prompt/model versions recorded per turn.

### 9.4 Data path

```text
question
→ request/idempotency/context validation
→ deterministic hints
→ lightweight InterpretationDraft when needed
→ semantic/entity/date resolution
→ ambiguity/support gate
→ canonical QueryPlan
→ allow-listed bound SQL
→ ComputedFacts + source lineage
→ validation suite
→ AnswerReceipt + QueryState update
→ React answer card/evidence/export
```

Architecture diagrams are in `docs/ARCHITECTURE.md` and `artifacts/architecture.mmd`.

---

## 10. Data model and fixture

### 10.1 Files

- `chart_of_accounts.csv`
- `vendors.csv`
- `vendor_aliases.csv`
- `transactions.csv`
- `vendor_payouts.csv`
- `reconciliation_status.csv`
- `data_dictionary.csv`
- `company_metadata.json`
- `dataset_manifest.json`

### 10.2 Dataset goals

The fixture must be realistic enough to exercise finance semantics, but deterministic and safe to publish. It includes:

- several months of posted/draft/voided transactions;
- completed/pending/failed/reversed payouts;
- vendor aliases and ambiguous short names;
- expense, COGS, revenue, asset, liability, and other accounts;
- departments/cost centers/projects;
- credits and reversals;
- reconciled, unreconciled, partially reconciled, and disputed records;
- duplicate candidates;
- one declared large anomaly;
- missing relationship/coverage cases;
- malicious-looking text that must remain inert;
- exact benchmark answers.

All names, tax IDs, bank references, invoices, values, and people are synthetic.

### 10.3 Runtime/gold isolation

Runtime application code may read the dataset and semantic definitions. It must never read:

- `evaluation/expected_aggregates.json`;
- expected values/source IDs in gold benchmark files;
- hardcoded answers copied into routes/components.

Gold is allowed only in evaluation and integration-test packages.

---

## 11. Contracts

Canonical files:

- `contracts/interpretation_draft.schema.json`
- `contracts/query_plan.schema.json`
- `contracts/query_state.schema.json`
- `contracts/computed_facts.schema.json`
- `contracts/answer_receipt.schema.json`
- `contracts/problem_details.schema.json`
- `contracts/openapi.yaml`
- `contracts/semantic_metrics.yaml`

Rules:

- reject unknown fields at trust boundaries;
- enums are closed;
- canonical arrays/filters are sorted for stable hashing;
- monetary JSON values use decimal strings;
- source record IDs and hashes are deterministic;
- status controls whether a number may appear;
- contract change requires docs, generated types, and tests in the same task.

---

## 12. API behavior

The OpenAPI file is authoritative. Primary endpoints:

- company/meta/glossary;
- conversation create/list/get/rename/delete/reset;
- message/clarification submission;
- query receipt;
- source records;
- CSV/XLSX export;
- explorer transactions and payouts;
- reconciliation summary/list;
- data-health summary/details;
- local evaluation runs/results.

### 12.1 Idempotency

Message and export creation use idempotency keys. Same key + same body returns original result; same key + different body returns 409.

### 12.2 Errors

Use `application/problem+json`. Never leak SQL, stack traces, prompts, secrets, or internal credentials. Include safe detail, field errors, and trace ID.

### 12.3 Query limits

- maximum message length 4,000;
- source preview default 100, bounded maximum;
- cursor pagination only;
- breakdown maximum 500;
- allow-listed dimensions/sorts;
- statement timeout;
- export cap or async flow;
- no arbitrary text search across every field.

---

## 13. AnswerReceipt

Every receipt includes:

- `query_id`, conversation/turn IDs, timestamps;
- answer status and plain-language answer;
- exact metric definition;
- interpreted date phrase, exact range, anchor, and date field;
- canonical filters/grouping/sort/limit/comparison;
- computed value(s), units/currency, and breakdown;
- source row count, ID hash, preview/records link;
- validation checks;
- warnings and coverage notes;
- dataset version/data-as-of;
- named compiled query and human-readable calculation;
- prompt/model version where used;
- confidence state determined by policy, not model self-rating.

### 13.1 Confidence/status policy

- `verified`: all required checks pass; no material coverage warning.
- `qualified`: deterministic result exists, but a declared non-fatal issue may affect interpretation/completeness.
- `needs_clarification`: multiple material interpretations; no number.
- `not_answerable`: required domain/field absent; no number.
- `no_matching_rows`: valid, sufficiently covered query with zero rows; explicit no-record/verified-zero language.
- `error`: technical or required validation failure; no number.

Do not present a generic percentage confidence unless it is empirically calibrated and still subordinate to these states.

---

## 14. Hallucination and prompt-injection guardrails

1. The model receives schema/semantic metadata, not authority over SQL or totals.
2. Record text is delimited and treated as data; preferably it is not sent to the parser at all.
3. Output validates against a closed schema; extra keys fail.
4. Resolver confirms IDs and dates.
5. Mandatory filters are inserted deterministically.
6. Compiler maps supported QueryPlans to named query templates/functions.
7. Result validator checks totals, row counts, cardinality, currency, signs, dates, and coverage.
8. Answer composer can only reference supplied fact tokens; numeric-token validator rejects novel numbers.
9. Unsupported/ambiguous gates run before execution.
10. `TXN-PROMPT-001`/`PAY-PROMPT-001` regression test must remain green.

---

## 15. Bugs and failure-mode requirements

`docs/BUG_AND_QA_PLAYBOOK.md` is authoritative. P0 regressions include:

### 15.1 Finance correctness

- wrong date field;
- inclusive end-date double counting;
- missing mandatory status filter;
- pending/failed/reversed payouts included in completed total;
- credits/reversals converted to positive or omitted;
- partial reconciliation using full transaction amount;
- one-to-many join inflating totals;
- duplicate candidates silently deduplicated;
- missing reconciliation rows ignored without warning;
- `float` rounding drift;
- comparison percentage on zero baseline;
- timezone/date-anchor drift.

### 15.2 Language/context

- ambiguous vendor auto-selected;
- “recent” assigned a hidden default;
- bare fiscal/calendar quarter guessed;
- “those” bound to wrong result;
- correction adds instead of replaces;
- older response overwrites newer context;
- idempotent retry creates duplicate turn;
- parser uses malicious record text as instruction;
- unsupported prediction receives a number.

### 15.3 UI

- answer shown before validation completes;
- stale answer remains after query changes;
- browser total differs from server/export;
- evidence panel loses route state;
- mobile composer covers final rows;
- modal/sheet focus trap broken;
- table keyboard access missing;
- warning represented only by colour;
- loading skeleton causes layout shift;
- failed export link remains active;
- long vendor/reference text breaks layout;
- CSV formula injection;
- raw HTML/XSS from record/model text.

### 15.4 Operational

- cache key omits dataset snapshot;
- DB transaction stays open during model call;
- timeout returns partial number;
- logs contain raw financial data/secrets;
- evaluation gold imported by runtime;
- 20M performance claimed from toy data.

Every bug fix adds a regression test and references a ticket ID.

---

## 16. Accessibility and responsive behavior

Minimum target: WCAG 2.2 AA behavior for core flows.

- semantic landmarks and headings;
- keyboard-complete navigation;
- visible focus;
- labelled controls and icon buttons;
- announcements for async stage/status without reading every token;
- no colour-only status;
- adequate contrast;
- reduced-motion support;
- dialogs/sheets restore focus;
- table headers and accessible names;
- mobile 360px flow remains usable;
- currency values have readable labels;
- charts have table/text alternatives.

Automated checks are required but do not replace keyboard and screen-reader smoke tests.

---

## 17. Export behavior

CSV and XLSX are generated server-side from immutable query lineage.

- same source count/hash as receipt;
- deterministic order;
- canonical decimal/date formatting;
- source IDs preserved as text;
- malicious spreadsheet prefixes escaped in untrusted text;
- negative numeric finance values remain numeric, not escaped as text;
- XLSX includes Receipt, Breakdown, and Records sheets;
- row cap/error is explicit;
- stale or mismatched dataset snapshot blocks export rather than silently recomputing a different answer.

---

## 18. Model-efficiency plan

The model is evaluated as an interpreter, not calculator.

### 18.1 Optimisation order

1. deterministic exact-ID/date/status handling;
2. compact semantic registry;
3. strict InterpretationDraft schema;
4. entity/date resolvers;
5. prompt iteration;
6. only then consider a larger model.

### 18.2 Acceptance gates

A candidate cannot be selected unless it passes every critical case:

- ambiguous vendors clarify;
- unsupported forecast/approval questions refuse;
- prompt injection remains inert;
- dates/metrics/filters are correct;
- multi-turn corrections are safe;
- malformed structured output fails closed.

Record accuracy, latency, tokens, API cost, prompt version, model ID, and environment. Select the smallest candidate clearing the declared threshold. See `docs/MODEL_EVALUATION_PLAN.md`.

---

## 19. Performance and scale

The challenge permits up to 20M records. The prototype must be architecturally credible without making unmeasured claims.

- composite/partial indexes for common metric/date/status/vendor paths;
- pre-joined safe analytical views where helpful;
- aggregate in PostgreSQL;
- cursor pagination;
- bounded source previews;
- statement timeouts and query cancellation;
- no user-controlled arbitrary joins/columns;
- repeatable snapshot semantics;
- EXPLAIN/ANALYZE evidence on scaled disposable data;
- p50/p95 captured by named query and row count;
- cache includes dataset version and canonical QueryPlan hash.

P0 target for the base demo: common questions complete within a few seconds end-to-end. Submission claims must use actual measurements.

---

## 20. Observability

Structured fields:

- trace/query/conversation/turn/client IDs;
- context version;
- dataset version/snapshot;
- prompt/model version;
- metric/intent/status;
- stage timings;
- named query;
- source row count bucket;
- validation codes;
- cache/idempotency outcomes;
- token/cost metrics where available.

Do not log raw source rows or full prompts in normal mode. Local synthetic debug mode may be explicit and opt-in.

---

## 21. Test strategy and release gates

### 21.1 Unit

Dates, money, aliases, state operations, schemas, mandatory filters, compiler parameters, validators, confidence, answer formatting, export sanitisation.

### 21.2 Property-based

Canonicalisation idempotence, filter-order hash equivalence, signed arithmetic, cursor round-trip, no novel numeric tokens, valid range compilation, reconciliation invariants.

### 21.3 PostgreSQL integration

Run all gold QueryPlans, assert exact totals/source relationships, edge cases, query timeouts, export parity, and runtime/gold isolation.

### 21.4 API contract

Validate requests/responses against OpenAPI and JSON Schema, problem-details errors, idempotency, context conflicts, pagination, and cancellation.

### 21.5 Frontend integration/E2E

Happy path, comparison, clarification, unsupported refusal, source records, export, double submit, stale response, network retry, mobile evidence, keyboard/focus, XSS/formula text.

### 21.6 Model evaluation

Field-level parser accuracy plus end-to-end exact answer/refusal/source accuracy. Averages cannot hide critical safety failures.

### 21.7 Release blockers

- any fabricated number;
- any critical ambiguity answered without clarification;
- any runtime gold dependency;
- any failed required validation still showing a number;
- export/receipt mismatch;
- P0 critical E2E failure;
- false model/performance claim;
- synthetic-data disclosure missing.

---

## 22. Delivery phases

### Phase 0 — contracts and data

Validate fixtures, freeze semantics/contracts, prepare a PostgreSQL connection, establish CI and agent rules.

### Phase 1 — deterministic core

Hand-built QueryPlan → PostgreSQL → ComputedFacts → checks → AnswerReceipt. No model required.

### Phase 2 — minimum UI/API

DRF endpoints, Ask page, answer states, evidence records/checks/query, basic responsive layout.

### Phase 3 — lightweight interpretation

Pre-parser, structured model parse, resolvers, ambiguity/support gates, benchmark harness.

### Phase 4 — multi-turn

QueryState, correction operations, pending clarification, version conflicts, stale-response protection.

### Phase 5 — full pages and exports

Explorer, Reconciliation, Data Health, Glossary, Evaluation, CSV/XLSX, accessibility.

### Phase 6 — scale and demo

Performance measurements, bug burn-down, architecture/README, model rationale, deck, recorded sample answers, demo rehearsal.

The dependency-ordered work queue is `project_backlog.csv`.

---

## 23. Three-minute demo flow

1. Ask last-month vendor payouts.
2. Show result and interpretation chips.
3. Open Receipt/Records/Checks; point to 55 rows and calculation.
4. Ask prior-month comparison.
5. Narrow to unreconciled/open context or inspect one partial item.
6. Ask ambiguous Acme; system clarifies and shows no number.
7. Ask next-quarter cash prediction; system safely refuses.
8. Show prompt-injection record is inert.
9. Flash evaluation page: smallest selected model, exact benchmark, latency/cost.
10. Close with value: self-service speed plus auditability.

See `docs/DEMO_AND_SUBMISSION_PLAN.md` for timing and deck.

---

## 24. Definition of done

The product is submission-ready when:

- clean checkout instructions work;
- fixture and repository validators pass;
- core QueryPlans return exact gold values;
- all answer statuses are implemented;
- multi-turn comparison/correction/clarification passes;
- every number has a receipt and source lineage;
- all P0 pages have loading/empty/error/permissionless-demo states;
- desktop, tablet, and 360px mobile work;
- keyboard/accessibility smoke tests pass;
- CSV/XLSX parity and injection tests pass;
- selected lightweight model has a reproducible benchmark;
- architecture and model rationale are documented;
- performance claims are measured;
- demo script is rehearsed against a fixed build;
- known limitations are disclosed rather than hidden.

---

## 25. Document precedence

1. `AGENTS.md` for safety and agent rules.
2. This master specification for product priorities and cross-cutting behavior.
3. Contracts under `contracts/` for machine-visible shapes and finance semantics.
4. `docs/BACKEND_QUERY_ENGINE_SPEC.md` and `docs/UI_UX_SPEC.md` for detailed implementation.
5. `docs/BUG_AND_QA_PLAYBOOK.md` for failure-mode acceptance.
6. `project_backlog.csv` for execution order.
7. Evaluation gold files for tests only.

When two sources disagree, open a contract/product decision task and fix every affected source. Do not silently choose whichever implementation is easiest.
