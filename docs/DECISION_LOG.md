# Product and Architecture Decision Log

| ID | Decision | Rationale | Consequence |
|---|---|---|---|
| ADR-001 | Product name is LedgerProof | Emphasises auditability and answer receipts | Synthetic company remains Northstar Labs |
| ADR-002 | React + TypeScript + Vite frontend | Fast hackathon iteration with strict types | API types should be generated/reused |
| ADR-003 | Django + DRF backend | Matches team experience and gives mature persistence/API primitives | Pydantic remains internal domain contract layer |
| ADR-004 | PostgreSQL computes finance values | Exact aggregation, indexes, 20M path | No model/browser arithmetic |
| ADR-005 | No model-generated SQL | Finance and injection risk | Use named allow-listed compilers |
| ADR-006 | Operational confidence states | More truthful than uncalibrated percentages | Status policy is deterministic |
| ADR-007 | Relative dates use dataset `data_as_of` | Reproducible fixtures/demos | Wall-clock date is irrelevant to answers |
| ADR-008 | QueryState is server-authoritative/versioned | Prevents context drift and races | All turns carry expected context version |
| ADR-009 | Duplicate candidates remain in totals | Silent dedupe can be wrong | Qualify/warn and expose records |
| ADR-010 | Runtime cannot access evaluation gold | Prevents demo hardcoding/leakage | CI performs import/path scan |
| ADR-011 | Redis/Celery are optional off the core path | Core chat should not depend on background infra | Use for large export/evaluation only |
| ADR-012 | API errors use problem+json | Consistent safe errors | No raw SQL/stack/prompt leakage |
| ADR-013 | Exports bind to answer lineage | Finance users expect parity | Source count/hash/snapshot checks required |
| ADR-014 | Synthetic dataset is INR/single company | Matches challenge constraint and reduces ambiguity | No FX or tenant security in scope |
