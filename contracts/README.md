# Contracts

These files are machine-visible source of truth.

- `semantic_metrics.yaml` — finance definitions, mandatory filters, date fields, dimensions, aliases, ambiguity and unsupported domains.
- `interpretation_draft.schema.json` — small-model output before deterministic resolution.
- `query_plan.schema.json` — canonical executable request.
- `query_state.schema.json` — versioned multi-turn state.
- `computed_facts.schema.json` — deterministic execution output before wording.
- `answer_receipt.schema.json` — user-visible/audit answer artifact.
- `problem_details.schema.json` — safe API errors.
- `openapi.yaml` — HTTP API.

Contract changes require backend, frontend, samples, docs, and tests in the same ticket. Monetary values in JSON are decimal strings. Runtime code must not import evaluation gold.
