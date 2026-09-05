# Lightweight Model and End-to-End Evaluation Plan

The model is evaluated as a constrained language interpreter, not as a calculator or autonomous
SQL agent. The objective is the **smallest model that satisfies the accuracy and refusal threshold**
when paired with deterministic resolution, MySQL computation and validation.

## 1. Evaluation layers

| Layer | What is tested | Primary metric |
|---|---|---|
| Interpretation | question → schema-valid InterpretationDraft | exact field/entity/date intent accuracy |
| Resolution | draft + metadata → executable/clarify/unsupported QueryPlan | exact plan accuracy and correct abstention |
| Deterministic query | QueryPlan → ComputedFacts | exact decimal/result/source-ID parity |
| Answer receipt | facts + validations → response | status, headline, lineage and privacy correctness |
| Multi-turn | prior QueryState + follow-up → patched QueryState | inherited/replaced filter accuracy |
| System | UI/API from question to evidence/export | task success, latency, cost and trust failures |

Do not collapse these into one “looks right” score. A wrong parser, query bug and presentation bug
need different fixes.

## 2. Dataset splits

The repository includes 30 visible development/gold cases and five multi-turn conversations. For
hackathon model selection, add a private holdout set that covers the same capability classes without
copying wording.

Suggested split:

- 30 repository cases: deterministic regression and demo transparency;
- 40 paraphrased holdout cases: model selection;
- 20 adversarial cases: ambiguity, unsupported fields, injection-like text, invalid IDs;
- 10 long/messy finance-user questions: robustness;
- 10 multi-turn conversations with 3–6 turns each.

Keep expected values outside runtime import paths. The application may execute a local evaluation
command, but normal request handling cannot read `evaluation/expected_aggregates.json` or expected
plans.

## 3. Capability taxonomy

Every set should cover:

1. debit total, credit total and net cash flow;
2. transaction count, average and largest transaction;
3. bank/program/account/entity filters;
4. bank/program/month grouping and ranking;
5. explicit and relative date ranges;
6. previous-period comparison;
7. exact transaction/reference lookup;
8. duplicate reference handling;
9. literal description search and its qualification;
10. current account balance and account count;
11. no-data queries;
12. clarification for materially ambiguous wording;
13. protected UTR behavior;
14. unsupported vendor/payout/reconciliation/category/historical-balance questions;
15. multi-turn inheritance, replacement and reset;
16. malformed-but-valid-source identifiers;
17. privacy and prompt-injection resistance.

## 4. Exact scoring

### 4.1 InterpretationDraft

Score each field independently and as an exact object:

- intent/disposition;
- metric;
- date phrase and intended granularity;
- bank/account/entity/program/type filters;
- group-by;
- comparison;
- reference vs UTR distinction;
- ambiguity and unsupported-concept flags.

Report:

- schema-valid rate;
- exact-draft accuracy;
- macro field F1;
- invalid-enum/hallucinated-field rate;
- mean model latency and input/output tokens.

### 4.2 Resolved QueryPlan

Use deterministic resolvers after model output. Report:

- exact-plan accuracy;
- executable-plan precision;
- clarification precision/recall;
- unsupported refusal precision/recall;
- wrong-execution rate (most important safety metric);
- date-boundary and entity-resolution accuracy.

A false execution on an ambiguous or unsupported question is weighted more heavily than an
unnecessary clarification.

### 4.3 Computed answer

For executable cases:

- exact decimal match;
- exact row-count match;
- source-ID set/hash match;
- group/rank ordering match;
- comparison absolute/percentage semantics;
- required validation pass rate.

A value that differs by ₹0.01 is wrong. Do not use fuzzy numeric scoring for official answers.

### 4.4 Multi-turn

For each turn classify whether the state should inherit, replace, add, remove, compare, clarify or
reset. Measure exact QueryState after every turn and whether a stale state is rejected.

## 5. Acceptance thresholds

Recommended P0 release gates:

- 100% deterministic query/gold result parity;
- 100% account-number and UTR non-leakage on fixture scans;
- 100% unsupported refusal on the four absent-concept families;
- ≥ 95% schema-valid interpretation output;
- ≥ 90% exact QueryPlan on holdout;
- ≥ 95% precision for executable disposition;
- ≥ 90% recall for necessary clarification/unsupported states;
- 0 arbitrary SQL executions;
- 0 runtime imports of evaluation gold;
- p95 end-to-end latency reported, not guessed.

For a hackathon, lower model scores may be acceptable if the UI clearly demonstrates abstention and
the team discloses results. Never tune thresholds by changing expected answers after seeing model
failures without documenting the dataset version.

## 6. Candidate-model experiment

Benchmark at least two genuinely lightweight candidates and one simple baseline:

- rule/regex baseline for dates, type and exact identifiers;
- smallest structured-output/tool-capable hosted model available within credits;
- one compact open-source model that can run locally or through a capped endpoint.

Use identical:

- system contract;
- JSON schema;
- metadata snapshot;
- temperature (0 or closest deterministic setting);
- retry/repair policy;
- question sets;
- timeout and token caps.

Model identity and prices change; record the exact provider/model version and observed cost at run
time rather than hardcoding a marketing name in the product contract.

## 7. Prompt contract

The parser prompt should:

- state the only source fields and supported metric enum;
- prohibit SQL, arithmetic and invented bank/vendor/category fields;
- distinguish reference ID from UTR;
- mark narration searches as literal/qualified;
- output only the InterpretationDraft schema;
- leave unresolved values as ambiguity rather than guessing;
- treat included descriptions/examples as data, not instructions.

Do not send full transaction rows to parse an ordinary question. Bank metadata and a bounded set of
masked account/program/entity identifiers are enough for resolution.

## 8. Retry and repair policy

1. One model call requests strict structured output.
2. If output is syntactically invalid, perform at most one schema-repair call containing validation
   errors and the invalid object, not finance results.
3. Deterministic semantic validation runs after repair.
4. Invalid/hallucinated concepts become clarification or unsupported, never an auto-broadened query.
5. Repeated failure returns a safe parsing error with a retry action.

Track repair rate; a model that needs frequent repair may be less efficient even with lower token
price.

## 9. Efficiency scorecard

For each model record in `evaluation/model_benchmark_results_template.csv`:

- model/provider/version;
- deployment mode and quantisation, when applicable;
- exact-draft and exact-plan accuracy;
- execute precision;
- clarification/unsupported metrics;
- average and p95 model latency;
- average input/output tokens;
- cost per 100 questions and cost per correct executable plan;
- repair-call rate;
- notes on deterministic fallback contribution.

The recommended model is the smallest/cheapest candidate that clears safety and accuracy gates—not
necessarily the raw accuracy winner.

## 10. End-to-end test procedure

For every benchmark case:

1. create a fresh or specified conversation state;
2. call the assistant endpoint with unique message ID;
3. capture InterpretationDraft and QueryPlan in test-only diagnostics;
4. execute against a freshly loaded fixture;
5. validate answer receipt schema;
6. compare amount, count, breakdown and source hash;
7. fetch records pages and verify their union/hash;
8. generate CSV/XLSX and verify parity plus privacy;
9. scan response/log/export for known account and UTR values;
10. store latency/token/cost metrics.

## 11. Reporting in the deck

Show a compact table with actual measured results, the chosen model, and why it wins under the
“lowest possible model, highest possible accuracy” criterion. Separate model interpretation
accuracy from deterministic answer accuracy so judges can see that financial correctness does not
depend on the model performing arithmetic.
