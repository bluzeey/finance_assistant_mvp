# Bug, Failure-Mode, and QA Playbook

## 1. Quality doctrine

A finance assistant must fail closed. Fluency, speed, and attractive UI never justify returning an unverified number. The severity model therefore prioritises incorrect financial answers, wrong source lineage, silent ambiguity, and stale context above ordinary presentation defects.

### Severity

- **P0 — Trust or data integrity failure:** can return a wrong number as trustworthy, corrupt context, execute unsafe behavior, or make evidence disagree with the answer. Blocks demo/submission.
- **P1 — Material workflow failure:** produces misleading interpretation, broken verification/export, severe accessibility issue, or common workflow failure. Must fix before submission unless explicitly waived with a safe fallback.
- **P2 — Polish or uncommon edge:** does not change the financial meaning but harms usability, consistency, or presentation.
- **P3 — Backlog:** low-impact enhancement.

### Answer safety rule

When a P0/P1 validation or infrastructure failure occurs, return no financial amount. A previously rendered immutable receipt may remain visible, but it must not be relabelled as the result of the failed request.

## 2. P0 risk register

| ID | Failure | Why it is dangerous | Prevention | Required test |
|---|---|---|---|---|
| P0-001 | Model changes or invents a number | Fluent false financial answer | DB computes; template/placeholder composition; numeric-token allow-list | Inject model output with altered value and assert response is rejected |
| P0-002 | Model produces SQL | SQL injection and unbounded access | Model schema has no SQL field; compiler allow-list | Adversarial “run this SQL” question returns refusal/valid plan only |
| P0-003 | User text interpolated into SQL | Injection or broken query | Bound parameters; enum identifiers | Static scan and malicious vendor/search strings |
| P0-004 | Join multiplies source rows | Inflated totals that look plausible | Declared grain; count distinct; independent source-grain sum | Add one-to-many alias join and assert validation failure |
| P0-005 | Wrong date field used | Correct sum over wrong business concept | Metric registry owns date field; receipt displays it | Payout metric must use payout_date, spend must use posting_date |
| P0-006 | Inclusive end-date off by one | Missing/double-counted period boundaries | Half-open intervals everywhere | Month end, leap day, and “through” tests |
| P0-007 | Server clock anchors relative dates | Results drift from static dataset | Anchor on `data_as_of` | Freeze system date to another year; results unchanged |
| P0-008 | Pending/failed/reversed payout counted as paid | Overstates paid amount/cash | Mandatory completed filter | Fixtures `PAY-PEND-001`, `PAY-FAIL-001`, `PAY-REV-ORIG` excluded |
| P0-009 | Credits/reversals dropped from spend | Overstates expense | Sum signed amounts | `TXN-REV-ORIG` + `TXN-REV-001` net to zero |
| P0-010 | Partial reconciliation counts full transaction | Overstates open amount | Sum `unreconciled_amount` | `TXN-PART-001` returns INR 200,000, not 500,000 |
| P0-011 | Ambiguous alias silently merges/selects | Wrong vendor answer | exact alias ambiguity gate | “Acme” and “ABC” show choices and no number |
| P0-012 | Fuzzy resolver auto-selects weak candidate | Wrong vendor answer | fuzzy results are candidates only | Near-collision names trigger clarification |
| P0-013 | Prompt injection inside a record controls output | Data becomes instructions | parser never sees records; escape data; fact-only composer | `TXN-PROMPT-001` leaves plan and amount unchanged |
| P0-014 | Unsupported field answered from model knowledge | Fabricated finance result | schema support gate | CFO approver and cash forecast questions return not-answerable |
| P0-015 | Validation failure still shows partial number | False confidence | fail-closed receipt builder | Force tie-out failure and assert amount is null/absent |
| P0-016 | Export differs from answer | Audit artifact cannot reproduce UI | export by immutable query ID; parity check | Row count, hash, and total match receipt |
| P0-017 | Source rows belong to another query | False evidence | query-scoped lineage/cursor signature | Cross-query cursor rejected |
| P0-018 | Stale request overwrites later correction | Wrong active context | context version CAS; client request identity | Slow request A, correction B, then A returns; B remains current |
| P0-019 | Duplicate submit creates two turns/queries | Confusing audit and repeated work | idempotency key and pending guard | Double click and network retry yield one turn |
| P0-020 | Reset clears UI only, not backend state | Old filters leak into next question | reset endpoint and version update | Reset then “what about last month?” requires metric/context |
| P0-021 | Runtime imports gold answers | Demo cheats and cannot generalise | process/package separation; import scan | CI fails on `expected_aggregates` reference in runtime |
| P0-022 | Floating-point arithmetic | Rounding drift | Decimal/NUMERIC only | Scan types and test 0.1 + 0.2-style cases |
| P0-023 | Mixed currency aggregated | Meaningless total | currency invariant or grouping | Inject non-INR row and require block/segmentation |
| P0-024 | Query runs with write-capable DB role | Prompt/query defect can mutate data | SELECT-only application role | permission test for INSERT/UPDATE/DELETE |
| P0-025 | Raw HTML/script rendered from record/model | XSS | React escaping; no `dangerouslySetInnerHTML` | Hostile description renders as text |
| P0-026 | Cache returns result from another dataset snapshot | Stale/incorrect answer | snapshot/version in cache key | Change dataset version and assert miss |
| P0-027 | Comparison mixes different filters | Misleading change | canonical current/previous plans share compatible filters | Mutation test changes vendor in one side and fails validation |
| P0-028 | Source result is truncated before aggregation | Understated total | aggregate in DB before row limit | >500 source rows still produce full total |
| P0-029 | Non-completed payout has cash outflow | Semantic corruption | DB constraint and validator | Fixture mutation fails load/validation |
| P0-030 | Reconciliation components do not tie | Open amount cannot be trusted | invariant check | Mutate component by INR 0.01 and block answer |

## 3. P1 risk register

| ID | Failure | Expected behavior/test |
|---|---|---|
| P1-001 | “Recent” silently defaults | Ask user to choose a period |
| P1-002 | Bare Q2 silently interpreted | Ask calendar/fiscal and year |
| P1-003 | “Spend” maps inconsistently between turns | Show metric chip; correction changes metric explicitly |
| P1-004 | Month-before comparison uses unequal duration | Derive matching period; show both exact ranges |
| P1-005 | Previous period has zero denominator | Show absolute change and say percentage is not meaningful |
| P1-006 | Empty records mistaken for unavailable data | Distinguish verified zero, qualified zero, and not-answerable |
| P1-007 | Missing reconciliation row treated as reconciled | Show coverage warning and qualify relevant answers |
| P1-008 | Duplicate candidates silently removed | Include both and show warning |
| P1-009 | Duplicate warning called confirmed fraud/duplicate | Use “possible duplicate” and explain rule |
| P1-010 | Anomaly labelled fraud | Use “unusual/outlier”; disclose threshold and median |
| P1-011 | Too little history for anomaly baseline | Suppress or qualify anomaly callout |
| P1-012 | Breakdown shows top rows but labels as full total | Label truncation and separate overall total |
| P1-013 | Chart and table use different data/rounding | Same response payload; parity assertion |
| P1-014 | Indian-formatted amount becomes API value | API remains canonical decimal; format only in UI |
| P1-015 | Negative credit lacks sign semantics | Label credit/reversal and retain negative value |
| P1-016 | Null and zero conflated | Typed nullable values and explicit zero rendering |
| P1-017 | Explorer calculates totals from current page | All totals come from backend aggregate |
| P1-018 | Offset pagination skips/duplicates after changes | Cursor with stable unique sort |
| P1-019 | Cursor accepted after filters change | Cursor bound to query/filter hash |
| P1-020 | CSV formula injection | Prefix dangerous text fields; preserve typed negatives |
| P1-021 | Excel export runs untrusted formulas | Write untrusted text as literal cells; no formula interpretation |
| P1-022 | Export omits metadata/filters | Include receipt metadata or companion sheet |
| P1-023 | Export timeout leaves ambiguous state | Clear failure, no partial file, safe retry |
| P1-024 | Client retry uses new idempotency key | Preserve key unless message changes |
| P1-025 | User edits draft after timeout but reuses key | New key required for changed body; backend returns 409 on mismatch |
| P1-026 | Conversation fetch overwrites optimistic pending message | Reconcile by client_turn_id |
| P1-027 | Evidence panel jumps to late answer | Keep user selection until explicitly changed |
| P1-028 | Context chips are client guesses | Render server QueryState only |
| P1-029 | Correction leaves incompatible comparison/filter | State merger clears dependent state |
| P1-030 | Reset deletes audit history unintentionally | Clear QueryState only unless conversation deletion requested |
| P1-031 | User pronoun has no stable referent | Ask clarification rather than guessing |
| P1-032 | “Which vendor drove it?” implies causality | Say largest contribution/change, not cause |
| P1-033 | Data freshness hidden | Every numeric answer shows data-as-of |
| P1-034 | Stale source labelled live | Freshness states based on metadata, not animation |
| P1-035 | Model/prompt version absent | Persist in receipt/audit/evaluation |
| P1-036 | Prompt parser failure falls back to generic chatbot | Return safe interpretation error |
| P1-037 | Model schema retry loops | At most one bounded retry; then fail safely |
| P1-038 | Large group-by overwhelms response | server max rows and safe top-N with truncation label |
| P1-039 | Arbitrary sort/column identifier injected | enum-backed sort and compiler identifiers |
| P1-040 | Query timeout returns cached unrelated value | timeout has no current amount; cache key exact |
| P1-041 | Database queries span changing snapshots | repeatable snapshot or materialised lineage |
| P1-042 | Source-ID hash is order-dependent accidentally | deterministic sort before hashing |
| P1-043 | Source-ID list in receipt implies completeness when truncated | explicit truncated flag and total count |
| P1-044 | PII/raw questions sent to analytics | redact; metadata-only analytics |
| P1-045 | Evaluation endpoint exposes gold in production mode | disabled and route absent by configuration |
| P1-046 | Error leaks SQL/prompt/secret | problem+json safe message plus trace ID only |
| P1-047 | CORS permits arbitrary origins | configured frontend origin only |
| P1-048 | Model output rendered as Markdown with unsafe links/HTML | safe renderer or plain text; strip HTML |
| P1-049 | Focus moves unexpectedly when answer arrives | announce via live region without stealing focus |
| P1-050 | Status relies only on color | icon + label + text |
| P1-051 | Evidence sheet traps/loses focus | tested focus trap and restoration |
| P1-052 | Mobile large amounts overflow | tabular number styles, wrap policy, 360 px visual test |
| P1-053 | Sticky composer covers final rows | safe-area and measured bottom padding |
| P1-054 | Error boundary hides prior verified receipt | page-level isolation; immutable prior results remain visible |
| P1-055 | Data-health check timestamp absent | show last run and dataset version |
| P1-056 | Check severity inconsistent with answer status | central policy mapping, not component logic |
| P1-057 | Alias table duplicated in frontend | fetch glossary/metadata from backend |
| P1-058 | Account category and vendor category confused | distinct labels and semantic fields |
| P1-059 | Posting and payout date displayed without marker | highlight date field used in receipt/records |
| P1-060 | “Last week” timezone/boundary mismatch | backend calendar rule in Asia/Kolkata |

## 4. P2 presentation and usability register

- long vendor names truncate without accessible full label;
- tooltips inaccessible by keyboard;
- table header loses shadow/contrast while scrolling;
- nav current state missing;
- empty filters consume excessive vertical space;
- rows jump when skeleton height differs;
- evidence tabs reset when panel closes accidentally;
- copy-answer omits period or status;
- copy receipt includes internal-only fields unexpectedly;
- chart axis abbreviates values without exact tooltip/table;
- negative values use hyphen instead of proper minus inconsistently;
- date formatting differs across pages;
- query ID cannot be copied;
- row-detail links break browser Back behavior;
- accordion animation ignores reduced-motion preference;
- large warning text dominates direct answer;
- buttons shift when spinner appears;
- mobile table action menu renders off-screen;
- horizontal scroll has no affordance;
- skeleton announced repeatedly to screen readers;
- toast disappears before it can be read;
- CSV/XLSX download names are generic;
- stale content appears blank during background refresh;
- browser title does not include page/conversation;
- no favicon/app identity;
- dataset synthetic label missing on one route;
- focus order reaches hidden evidence controls;
- print layout cuts receipt details;
- no empty state for deleted conversation;
- inconsistent use of “payout,” “payment,” and “spend.”

## 5. Test pyramid and environments

### Fast checks on every commit

- Ruff/format/mypy;
- TypeScript strict compile and lint;
- JSON schema validation;
- OpenAPI parse;
- dataset validator;
- unit tests for dates, money, entity resolution, QueryState, compiler, templates;
- frontend component tests;
- runtime import scan for gold fixtures.

### Pull-request checks

- PostgreSQL integration tests;
- contract tests;
- benchmark subset including every P0 case;
- Playwright critical flows at desktop and 360 px;
- accessibility scan plus keyboard smoke test;
- export parity tests;
- migration up/down on disposable database;
- dependency and secret scan.

### Release/submission checks

- full 22-case single-turn benchmark;
- multi-turn benchmark;
- prompt-injection suite;
- data mutation/invariant suite;
- performance run on declared scaled dataset;
- browser matrix: current Chrome plus one additional browser if available;
- production build served against configured backend;
- README clean-room setup;
- demo rehearsal with network fallback plan;
- no console errors or failed network requests on demo path.

## 6. Dataset mutation tests

Gold happy-path fixtures alone can hide weak validation. Create test-only mutations:

1. add a second alias row join and confirm aggregate tie-out catches duplication;
2. change a completed payout to failed without changing expected query and verify exclusion;
3. put payout date on `2026-09-01` and verify August excludes it;
4. change a transaction credit to positive and ensure net-spend gold fails;
5. remove a reconciliation row and verify coverage warning;
6. set partial open amount to full transaction and block due to tie-out;
7. set a non-INR currency and block single-currency aggregate;
8. duplicate a source ID and fail grain validation;
9. insert more than two decimal places and fail precision;
10. alter dataset version while reusing cache and require cache miss;
11. add an HTML/script string to description and verify escaped display;
12. prefix vendor text with `=` and verify CSV export sanitisation;
13. create zero previous-period amount and test comparison wording;
14. make anomaly history one row and verify low-history qualification;
15. return model prose with a different numeric token and reject it.

## 7. Benchmark acceptance gates

Set gates before model selection. Recommended minimum for submission:

- 100% final numeric accuracy on supported gold cases;
- 100% pass on planted P0 finance-semantic cases;
- 100% unsupported-field refusal on benchmark cases;
- 100% ambiguous Acme/ABC blocking;
- 100% prompt-injection resistance on fixture cases;
- at least 95% exact/field-level QueryPlan accuracy overall;
- 100% source-ID completeness or documented hash/lineage equivalence;
- at least 95% multi-turn state accuracy, with reset/correction cases mandatory;
- zero answer/export parity mismatches;
- p95 interactive latency within declared target;
- smallest model meeting all safety gates wins; a smaller model does not qualify merely because it is cheaper.

If a model fails a safety gate, improve deterministic parsing/resolution or choose the next-smallest candidate. Do not lower the safety threshold to preserve a model-choice narrative.

## 8. Manual exploratory scripts

### Script A: grounding

1. Ask August vendor payout total.
2. Open receipt and note row count/date/status.
3. Open records and locate anomaly/duplicate rows.
4. Export and compare metadata.
5. Change period through a chip and confirm a new immutable turn.

### Script B: ambiguity

1. Ask for Acme spend last month.
2. Confirm no number appears.
3. choose Acme Cloud Services.
4. Confirm original period and metric persist.
5. ask “the office one instead” and confirm vendor replacement.

### Script C: context race

1. Throttle the network.
2. send a broad question.
3. immediately send a correction after the UI permits it or simulate concurrent requests.
4. confirm context version prevents late overwrite.
5. inspect conversation history and audit IDs.

### Script D: failure closure

1. induce DB timeout or validation mismatch.
2. verify no amount is rendered.
3. verify trace ID and safe retry.
4. recover service and retry with same key.
5. confirm one completed turn.

### Script E: accessibility/mobile

1. operate Ask page with keyboard only.
2. select a suggested prompt.
3. open evidence, switch tabs, close, and confirm focus.
4. zoom to 200% and use 360 px viewport.
5. verify amounts, warnings, table, and composer remain usable.

## 9. Bug report template

```markdown
### [Severity] Concise title

Environment:
Build/commit:
Dataset version:
Model/prompt version:
Conversation ID:
Query ID / trace ID:

Steps:
1.
2.
3.

Expected:
Actual:

Financial impact:
Source-lineage impact:
Reproducibility:
Attachments/log excerpt:
Suspected layer: parser / resolver / state / compiler / DB / validation / composer / API / UI / export
Regression test added:
```

Every P0/P1 fix requires a regression test at the lowest effective layer plus an end-to-end test when user-visible.

## 10. Demo-day risk checklist

- pin dataset, prompt, and model versions;
- prewarm model connection only if allowed and disclose no hidden answer cache;
- keep deterministic sample questions visible;
- verify API credits and local fallback;
- have a deterministic parser/template path for core demo questions;
- do not depend on live banking/ERP systems;
- keep local PostgreSQL and frontend builds available;
- verify system clock cannot affect relative dates;
- disable developer stack traces;
- clear old conversations or use a clean demo account;
- confirm synthetic-data banner;
- test projector resolution and browser zoom;
- download one sample CSV/XLSX before presenting;
- keep architecture diagram and benchmark page available if network degrades;
- never claim a benchmark, latency, or model result not actually measured.
