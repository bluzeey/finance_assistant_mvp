# Agent Execution Plan

## 1. Delivery strategy

Build the product as a sequence of grounded vertical slices. The earliest slice should answer one manually constructed QueryPlan against PostgreSQL and return a valid AnswerReceipt. Natural-language parsing and visual polish come after the deterministic financial core is proven.

The critical path is:

```text
validated data
→ database schema/views/indexes
→ semantic registry and typed QueryPlan
→ deterministic compiler/executor
→ result validation and AnswerReceipt
→ API
→ Ask UI and evidence panel
→ parser/entity/date resolution
→ multi-turn state
→ exports/data health/evaluation
→ performance and demo polish
```

Multiple agents can work concurrently after contracts are frozen, but only one owner should change a contract at a time.

## 2. Roles

For a small team, one person/agent may hold multiple roles.

| Role | Owns |
|---|---|
| Product/contract owner | scope, metric semantics, acceptance criteria, contract consistency |
| Data/backend foundation | fixture, PostgreSQL, migrations, loader, repositories |
| Query engine | QueryPlan, compiler, executor, validators, receipts |
| Model/interpretation | parser prompt, structured output, entity/date resolution, benchmark |
| Frontend | application shell, Ask, evidence, Explorer, data health, accessibility |
| Quality/release | test harness, model evaluation, performance, demo readiness |

## 3. Phase 0 — repository and contract freeze

### Goal

A clean checkout can validate fixtures, start PostgreSQL, and expose agreed contracts before feature code diverges.

### Deliverables

- repo layout and environment files;
- dataset generation/validation;
- PostgreSQL schema, views, indexes, loader;
- semantic metric registry;
- QueryPlan, AnswerReceipt, and OpenAPI contracts;
- lint/type/test commands;
- CI skeleton.

### Exit criteria

- `python scripts/validate_dataset.py` passes;
- JSON schemas parse;
- OpenAPI parses;
- database loads from CSV;
- no contract naming conflicts;
- all agents acknowledge invariants in `AGENTS.md`.

## 4. Phase 1 — deterministic finance core

### Goal

Answer supported questions from hand-built QueryPlans with exact values and proof, with no model.

### Work

- implement enums and Pydantic QueryPlan;
- load semantic registry from versioned configuration;
- implement compilers for completed payout aggregate/ranking, vendor spend, open reconciliation, duplicates, anomalies, and freshness;
- execute in read-only transactions;
- capture source IDs and stable hashes;
- implement validation checks;
- build deterministic answer templates and AnswerReceipt;
- integrate gold tests in test-only package.

### First vertical slice

Input:

```json
{
  "intent": "aggregate",
  "metric": "vendor_payout_amount",
  "date_range": {
    "start": "2026-08-01",
    "end_exclusive": "2026-09-01",
    "date_field": "payout_date",
    "source_phrase": "last month",
    "anchor_date": "2026-09-03",
    "calendar_basis": "calendar"
  },
  "filters": {"payout_status": ["completed"]},
  "group_by": [],
  "sort": [],
  "limit": 100,
  "comparison": null,
  "ambiguities": [],
  "unsupported_fields": []
}
```

Output: schema-valid receipt with exact August payout total, source count/hash, validation checks, and records endpoint.

### Exit criteria

- all deterministic benchmark queries return exact expected values;
- planted edge cases pass;
- no numeric answer can bypass validator;
- runtime import scan proves no gold access;
- direct API integration tests pass.

## 5. Phase 2 — API and minimum frontend

### Goal

A user can submit a pre-supported question through React and inspect a trustworthy receipt.

### Backend work

- conversation create/list/get/delete/reset;
- message endpoint with idempotency and context version;
- query receipt/records/export endpoints;
- metadata/glossary endpoints;
- problem+json errors;
- structured logging.

### Frontend work

- app shell and routes;
- Ask empty state, composer, conversation turns;
- AnswerCard states;
- interpretation chips;
- evidence panel Receipt/Records/Checks/Query tabs;
- loading and error states;
- typed API client;
- desktop and mobile layout.

### Temporary parsing policy

A deterministic parser may support the benchmark phrasing while the model parser is in development, but it must produce QueryPlans rather than return hardcoded answers. Unknown wording must return safe interpretation failure.

### Exit criteria

- end-to-end August payout question works;
- answer receipt and records are inspectable;
- no duplicate turns on retry/double click;
- mobile Ask/evidence flow passes;
- export can be deferred to Phase 5 if links are hidden rather than broken.

## 6. Phase 3 — lightweight natural-language interpretation

### Goal

Support varied free-form questions while preserving strict grounding.

### Work

- deterministic hints/exact IDs/dates;
- model provider abstraction;
- structured InterpretationDraft schema;
- compact prompt from semantic registry;
- one bounded schema-repair retry;
- metric, entity, account, date, and status resolvers;
- QueryPlan canonicalisation and semantic validation;
- ambiguity and unsupported-field receipts;
- benchmark runner with model/prompt version.

### Model-selection process

1. establish candidate size/cost tiers allowed by hackathon credits;
2. run all benchmark questions at temperature zero or deterministic setting where supported;
3. score parser fields, final answers, refusals, clarification, latency, and cost;
4. improve deterministic resolver/pre-parser before increasing model size;
5. choose the smallest model that clears every safety gate;
6. document failures and rationale honestly.

### Exit criteria

- Acme/ABC clarification is reliable;
- unsupported forecast/approver questions return no number;
- prompt-injection fixture is inert;
- overall and critical-case thresholds are met;
- selected model rationale is reproducible.

## 7. Phase 4 — multi-turn and correction

### Goal

Follow-ups work without hidden context drift.

### Work

- typed QueryState;
- state operations SET/REPLACE/ADD/REMOVE/CLEAR/RESET;
- pending clarification state;
- result references for “those”;
- compare previous period;
- driver analysis;
- context chips and change summary;
- compare-and-swap context version;
- client stale-response handling.

### Exit criteria

- conversation benchmark C001–C003 passes;
- correction creates a new immutable receipt;
- reset clears state server-side;
- slow request cannot overwrite newer state;
- the UI always shows canonical current context.

## 8. Phase 5 — verification surfaces

### Goal

Make auditability a visible product advantage.

### Work

- Explorer tabs and row detail;
- Reconciliation dashboard and ageing;
- Data Health checks;
- searchable Glossary;
- CSV and Excel exports from query ID;
- source-ID cursor pagination;
- duplicate/anomaly warnings;
- verified-zero/qualified behavior from coverage policy.

### Exit criteria

- export parity test passes;
- data-health page exposes planted coverage/duplicate/anomaly conditions;
- record source date field is marked;
- no client-side official totals;
- accessibility and 360 px layouts pass.

## 9. Phase 6 — evaluation, performance, and submission

### Goal

Produce measured evidence for accuracy, efficiency, UX, and business impact.

### Work

- evaluation page and report generation;
- complete benchmark runs;
- query-plan diffs;
- p50/p95 timing instrumentation;
- scaled database tests and EXPLAIN plans;
- prompt/model choice note;
- architecture diagram;
- README clean-room setup;
- sample questions/answers;
- demo script and deck content;
- release build and fallback plan.

### Exit criteria

- all P0 and accepted P1 tests pass;
- smallest qualifying model selected;
- model results and dataset size are recorded;
- README setup succeeds from clean checkout;
- presentation contains no unsupported claims;
- three-minute demo is repeatable.

## 10. Parallelisation map

After Phase 0:

- Agent A: database/repositories/compilers
- Agent B: Pydantic contracts/validators/receipts
- Agent C: app shell/Ask/evidence components using MSW fixtures
- Agent D: parser/resolvers/evaluator

After API shapes stabilise:

- Agent C integrates real API;
- Agent A builds Explorer/Reconciliation endpoints;
- Agent B builds data-health checks and exports;
- Agent D runs benchmark iterations and documents model choice.

Avoid parallel edits to the same contract. Contract changes require owner review and regenerated frontend types.

## 11. Dependency and handoff rules

- A ticket may start only when its `depends_on` tickets are done or the owner documents a temporary mock boundary.
- Mocks conform exactly to OpenAPI/JSON schemas.
- A consumer may not patch around an upstream contract defect locally; fix the contract/source.
- User-visible copy referencing metric semantics must be sourced from or reviewed against `semantic_metrics.yaml`.
- A ticket touching financial logic must name the relevant benchmark/edge-case tests.
- A ticket touching async UI must cover cancellation, idempotency, stale response, loading, and error behavior.

## 12. Daily agent loop

1. Run dataset validator and relevant tests.
2. Pick the highest-priority unblocked ticket.
3. Read its acceptance criteria and related contracts.
4. Implement tests first or alongside code.
5. Integrate a complete path rather than adding disconnected abstractions.
6. Run focused tests, then broader suite.
7. update docs/contracts/fixtures if necessary.
8. Leave a handoff with evidence.

## 13. Product decision log

Create `docs/decisions/ADR-XXXX-title.md` for decisions that change:

- metric definition or date field;
- ambiguity policy;
- model/provider choice;
- QueryPlan or receipt schema;
- database grain/join;
- cache/snapshot strategy;
- confidence/status policy;
- export lineage;
- scope.

ADR format: context, decision, alternatives, consequences, tests/migration.

## 14. Minimum submission versus stretch

### Submission-critical

- Ask page;
- exact supported metrics;
- source rows/receipt;
- ambiguity/refusal;
- multi-turn comparison;
- data health basics;
- CSV export;
- benchmark/model note;
- architecture and README.

### Stretch only after critical path is green

- Excel export if CSV already works;
- rich charts;
- resizable evidence panel;
- conversation rename;
- advanced anomaly methods;
- saved queries;
- streaming stage events;
- dark mode;
- natural-language report builder.

Do not trade grounding for breadth.
