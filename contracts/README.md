# Contracts

These files separate language interpretation from deterministic finance execution.

1. The lightweight model emits `InterpretationDraft` only.
2. Deterministic resolvers map that draft plus `QueryState` to `QueryPlan`.
3. An allow-listed compiler executes the plan against `bank`, `account`, and `` `transaction` ``.
4. Validation produces `ComputedFacts`.
5. The API returns an immutable `AnswerReceipt` or `ProblemDetails`.

No schema accepts raw SQL. IDs deliberately use plain strings instead of JSON Schema's UUID
format because one organiser-provided sample transaction ID is UUID-like but malformed. Runtime
code must therefore treat identifiers as opaque values bounded by the source column length.

Validate JSON documents with:

```bash
python scripts/validate_repository.py
```
