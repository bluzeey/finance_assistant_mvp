# Evaluation Fixture

This directory is for offline tests and model benchmarking. Application runtime code is forbidden
from reading it.

- `benchmark_cases.jsonl`: 30 single-turn gold cases
- `benchmark_conversations.jsonl`: 5 multi-turn scenarios
- `benchmark_questions.csv`: human-readable benchmark index
- `expected_aggregates.json`: raw-data-recomputed gold totals
- `edge_case_manifest.csv`: source records designed to trigger bugs and trust controls
- `model_benchmark_results_template.csv`: one row per actual model/prompt run

Score interpretation, date resolution, filters, numeric equality, clarification/refusal behavior,
privacy, multi-turn state, latency and cost separately. A model cannot compensate for a wrong
compiler or metric definition.
