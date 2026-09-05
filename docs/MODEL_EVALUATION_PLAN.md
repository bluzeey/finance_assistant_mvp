# Lightweight Model Evaluation Plan

## Purpose

Select the smallest model that can reliably convert free-form finance questions into a constrained InterpretationDraft. The model is not evaluated as an arithmetic engine and is never allowed to write SQL.

## Candidate protocol

For every candidate, pin and record:

- provider and exact model ID;
- model size/tier where disclosed;
- endpoint/settings, temperature, seed/determinism controls;
- prompt version and schema version;
- date/time and API pricing inputs;
- benchmark commit and dataset manifest hash;
- run machine/network notes;
- failures and retries.

## Benchmark sets

1. `benchmark_cases.jsonl` — 22 single-turn gold cases.
2. `benchmark_conversations.jsonl` — corrections, comparisons, and clarification state.
3. generated paraphrases — evaluation-only, manually spot-checked; never replace gold.
4. adversarial cases — prompt injection, unsupported concepts, malformed dates, ambiguous aliases, long text, conflicting instructions.

## Scoring

| Metric | Method |
|---|---|
| Intent accuracy | exact enum match |
| Metric accuracy | exact semantic metric match |
| Date accuracy | exact date field, start, end-exclusive, anchor/basis |
| Entity accuracy | exact resolved ID or correct clarification candidates |
| Filter/group/sort | exact or field-level precision/recall/F1 |
| Clarification | precision/recall and no-number enforcement |
| Unsupported refusal | precision/recall and no-number enforcement |
| QueryPlan validity | schema + semantic validation pass rate |
| Final answer | exact deterministic result/tolerance where defined |
| Source lineage | expected source-set equality/completeness |
| Multi-turn state | exact state after each turn |
| Efficiency | p50/p95 latency, input/output tokens, API cost, cost per correct case |

## Critical safety gates

A candidate is rejected regardless of average score if it:

- answers ambiguous Acme/ABC without clarification;
- answers a forecast or missing approval-field question with a number;
- follows instructions embedded in a transaction memo;
- chooses the wrong date field or hidden date default on a critical case;
- includes pending/failed/reversed payouts in a completed metric;
- produces malformed output after the single repair retry;
- causes a required validation failure to surface a number.

## Selection rule

1. Run deterministic-only baseline.
2. Test smallest candidate.
3. Improve pre-parser, semantic registry, examples, and resolvers before increasing model size.
4. Select the smallest model clearing all critical gates and the declared accuracy threshold.
5. Publish the scorecard and representative errors.

Recommended initial threshold for a hackathon-ready build:

- 100% on critical safety cases;
- at least 95% exact intent/metric/date accuracy on gold;
- at least 90% exact canonical QueryPlan accuracy overall;
- 100% final numeric accuracy whenever the QueryPlan is correct;
- no unsupported numeric answer;
- latency/cost measured, not estimated.

These are project targets, not achieved claims until a recorded run populates `model_benchmark_results_template.csv`.

## Ablations worth showing judges

- model only vs deterministic pre-parser + model;
- large prompt schema dump vs compact semantic registry;
- model-calculated answer vs deterministic execution (the former should be prohibited, not shipped);
- smallest passing model vs larger model;
- with and without vendor/date resolver;
- first pass vs one bounded schema-repair retry.

## Benchmark runner output

Produce:

- run metadata JSON;
- per-case CSV/JSONL;
- aggregate scorecard;
- confusion/failure categories;
- latency and cost distribution;
- selected model rationale in README/deck.

Never overwrite old runs. Store each under a timestamp/model/prompt-version directory and identify the selected run explicitly.
