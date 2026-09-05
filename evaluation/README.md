# Evaluation Fixtures

This directory contains gold answers and safety cases for offline evaluation and integration tests.

**Runtime application code must never read expected values from this directory.** CI should scan for such imports/paths.

- `benchmark_cases.jsonl` — full single-turn gold records including expected plans/values/source IDs.
- `benchmark_questions.csv` — spreadsheet-friendly view.
- `benchmark_conversations.jsonl` — multi-turn state cases.
- `expected_aggregates.json` — exact deterministic totals.
- `edge_case_manifest.csv` — planted failure cases.
- `model_benchmark_results_template.csv` — populate with actual runs.
