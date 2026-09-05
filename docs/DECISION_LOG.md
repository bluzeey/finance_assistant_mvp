# Decision Log

| ID | Decision | Rationale | Consequence |
|---|---|---|---|
| ADR-001 | Product working name is LedgerProof | Auditability is the primary differentiator | Name can change without changing contracts |
| ADR-002 | Organiser schema is the sole finance source of truth | Prevents demo-only inferred dimensions from becoming fabricated facts | Exactly `bank`, `account`, `transaction` are loaded |
| ADR-003 | Use MySQL 8.4 | Provided DDL is MySQL-specific (`ENUM`, `ENGINE=InnoDB`, `TIMESTAMP(6)`) | Quote `` `transaction` `` and test MySQL behavior |
| ADR-004 | Model interprets; MySQL/Python compute | Small models are sufficient for constrained structured parsing and cannot invent totals | No model arithmetic or arbitrary SQL |
| ADR-005 | Money crosses boundaries as decimal strings | JavaScript/Python floats can change official values | MySQL `DECIMAL`, Python `Decimal`, JSON strings |
| ADR-006 | Date filters are half-open in Asia/Kolkata | Avoids month-end microsecond and timezone errors | `start <= transaction_date < end` after session timezone setup |
| ADR-007 | Relative dates anchor to dataset cutoff | Static hackathon fixtures should not drift with wall-clock time | “Last month” at cutoff 2026-09-03 means August 2026 |
| ADR-008 | Bare “reference” means `transaction_reference_id` | It is plaintext and directly searchable; UTR is sensitive | Exact, case-sensitive lookup; warn when duplicate |
| ADR-009 | Account number and UTR are sensitive | The source documentation explicitly calls them sensitive | Mask before model/browser/log/export; redact narration leakage |
| ADR-010 | Transaction descriptions are untrusted free text | Narrations can be inconsistent, contain PII or prompt-like text | Literal search is qualified; text is escaped; no canonical vendor inference |
| ADR-011 | Current balance is snapshot-only | `account.available_balance` has no effective timestamp/history | No historical balance or balance reconstruction claims |
| ADR-012 | Missing dimensions produce unsupported responses | Vendor, payout, reconciliation, category and COA are absent | No answer number, list or dashboard for those concepts |
| ADR-013 | Source IDs are opaque strings | One provided transaction identifier is not a strict UUID despite the prose label | Validate length/uniqueness, not UUID syntax |
| ADR-014 | Runtime cannot import evaluation gold | Prevents benchmark leakage | Evaluation package is local/test-only and CI checks imports |
| ADR-015 | Exports are generated from persisted receipts | Guarantees UI/export parity and consistent privacy | Export references query ID, dataset version and source hash |
| ADR-016 | Operational status replaces arbitrary confidence percentages | Trust depends on validations and source availability | Verified, Qualified, Clarification, Unsupported, No data, Failed |
