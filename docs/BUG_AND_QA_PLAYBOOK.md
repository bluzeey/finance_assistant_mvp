# Bug and QA Playbook

This playbook anticipates the failures most likely to produce a wrong finance answer, privacy leak,
misleading UI or unreliable hackathon demo. Every P0/P1 bug fix requires a regression test.

---

## 1. Severity model

| Severity | Definition | Examples |
|---|---|---|
| P0 | Wrong official number, sensitive data leak, arbitrary query execution, receipt/source mismatch | float rounding changes amount; raw account number returned; vendor payout fabricated |
| P1 | Materially wrong interpretation or evidence, blocked core flow, stale-context corruption | wrong month, wrong bank, reference fuzzy matched, export rows differ |
| P2 | Recoverable functional/UX/accessibility defect | filter reset issue, focus loss, table truncation |
| P3 | Cosmetic/non-blocking | spacing, minor copy inconsistency |

Release/demo is blocked by any open P0 or unmitigated P1.

---

## 2. Mandatory regression fixture

`evaluation/edge_case_manifest.csv` contains records for:

- month boundaries at microsecond precision;
- duplicate-lookalike transactions;
- a non-unique plaintext reference;
- null description;
- zero amount;
- maximum `DECIMAL(15,2)`;
- Unicode narration;
- an account number embedded in narration;
- UTR present while plaintext reference is null;
- case-sensitive reference;
- prompt injection and script text;
- one organiser-provided malformed strict UUID-like ID.

Agents may add edge cases but must not remove them to simplify implementation.

---

## 3. Data/schema bugs

### DB-001 — unquoted `transaction` table

**Failure:** Raw SQL fails because `transaction` is parsed as a keyword.  
**Severity:** P1  
**Prevention:** Always quote as `` `transaction` ``; use Django ORM where suitable.  
**Tests:** Execute every raw compiler query against MySQL; repository grep/validator.

### DB-002 — strict UUID coercion rejects source row

**Failure:** Serializer/model rejects `0178b656-4a7d-98e8-9540f6e24caf`.  
**Severity:** P1  
**Prevention:** Use bounded opaque strings, not UUIDField/JSON `format: uuid`.  
**Tests:** Load and query the preserved row.

### DB-003 — FK join on wrong field

**Failure:** Transaction joins by entity/bank/number and duplicates or loses rows.  
**Severity:** P0  
**Prevention:** `transaction.account_id → account.account_id`; `account.bank_code → bank.bank_code` only.  
**Tests:** Source count and hash against gold; orphan checks.

### DB-004 — obsolete tables reintroduced

**Failure:** Agent rebuilds vendor/payout/reconciliation tables from earlier docs and presents inferred data as source.  
**Severity:** P0  
**Prevention:** Three-table invariant in AGENTS/CI/repository validator.  
**Tests:** DDL/source-file set check; unsupported benchmark cases.

### DB-005 — program `04` treated as string distinct from `4`

**Failure:** Filter misses program 4 accounts.  
**Severity:** P1  
**Prevention:** Parse/store integer.  
**Tests:** Q030 and explicit `04` natural-language resolver case.

### DB-006 — default collation makes reference case-insensitive

**Failure:** `caseref-abc-001` matches `CaseRef-AbC-001`.  
**Severity:** P1  
**Prevention:** Binary comparison/collation.  
**Tests:** Q027; MySQL integration.

### DB-007 — TIMESTAMP session timezone drift

**Failure:** Boundary transaction falls into previous/next day/month.  
**Severity:** P0  
**Prevention:** Set MySQL session `+05:30`; timezone-aware Python dates.  
**Tests:** four boundary rows; verify connection setting.

### DB-008 — schema nullable mismatch

**Failure:** NULL description/reference/UTR crashes serializer/model.  
**Severity:** P1  
**Prevention:** nullable types and explicit display fallback.  
**Tests:** null-description source row and missing refs.

### DB-009 — DECIMAL range/precision mismatch

**Failure:** max value overflows or rounds; backend uses max_digits wrong.  
**Severity:** P0  
**Prevention:** DecimalField(15,2), Decimal strings, max fixture.  
**Tests:** max decimal round-trip.

### DB-010 — unrestricted description query at scale

**Failure:** `%substring%` scans 20M rows and times out.  
**Severity:** P1/P2  
**Prevention:** cap range/result; optional full-text; visibly qualify; monitor plan.  
**Tests:** timeout and EXPLAIN benchmark.

---

## 4. Financial-semantic bugs

### FIN-001 — debits treated as already negative

**Failure:** debit total becomes negative or net double-negates.  
**Severity:** P0  
**Prevention:** amount absolute; type supplies direction.  
**Tests:** August totals and net invariant.

### FIN-002 — float arithmetic

**Failure:** pennies/paise drift or JSON/scientific notation.  
**Severity:** P0  
**Prevention:** MySQL Decimal → Python Decimal → string → display formatter.  
**Tests:** aggregate exact equality including max/0.01 combinations.

### FIN-003 — inclusive end date duplicates boundary

**Failure:** `BETWEEN` includes 1 September in August.  
**Severity:** P0  
**Prevention:** half-open ranges.  
**Tests:** BOUNDARY-AUG-END included; BOUNDARY-SEP-START excluded.

### FIN-004 — wall clock used for “last month”

**Failure:** demo changes after calendar month or differs by environment.  
**Severity:** P0  
**Prevention:** dataset cutoff anchor.  
**Tests:** freeze system clock to another date and assert August resolution.

### FIN-005 — balance fan-out

**Failure:** joins account to transactions and sums balance once per transaction.  
**Severity:** P0  
**Prevention:** query account directly or distinct IDs first.  
**Tests:** exact 30-account total; deliberately joined query differs and must not be used.

### FIN-006 — historical balance invented

**Failure:** applies date filter to current `available_balance`.  
**Severity:** P0  
**Prevention:** any historical modifier on balance → unsupported.  
**Tests:** Q025 and multi-turn C004.

### FIN-007 — vendor payout inferred from debit narration

**Failure:** labels all or selected debit transactions as vendor payouts.  
**Severity:** P0  
**Prevention:** explicit schema-gap resolver; language rules.  
**Tests:** Q020 and follow-up “Are those vendor payouts?”

### FIN-008 — reconciliation status fabricated

**Failure:** uses absence/presence of ref/UTR as reconciled flag.  
**Severity:** P0  
**Prevention:** unsupported; no heuristic.  
**Tests:** Q019.

### FIN-009 — description search presented as canonical vendor total

**Failure:** “Selection Mobile spend” without qualification.  
**Severity:** P0/P1  
**Prevention:** clarification or explicit literal search with qualified receipt.  
**Tests:** Q015/Q026; copy/export includes qualification.

### FIN-010 — duplicate rows silently removed

**Failure:** totals differ from source and receipt.  
**Severity:** P0  
**Prevention:** include both; warn; dedup only with explicit source rule.  
**Tests:** duplicate-lookalike pair contributes twice.

### FIN-011 — duplicate reference assumed unique

**Failure:** returns first row only.  
**Severity:** P1  
**Prevention:** fetch up to safe cap, status qualified.  
**Tests:** Q023 returns two.

### FIN-012 — no-data shown as zero

**Failure:** user believes valid zero activity instead of no records.  
**Severity:** P1  
**Prevention:** dedicated `no_data` state.  
**Tests:** Q017/Q027 UI/API.

### FIN-013 — average denominator wrong

**Failure:** average uses all types or paginated rows.  
**Severity:** P0  
**Prevention:** aggregate after all predicates; count source rows.  
**Tests:** Q010 exact.

### FIN-014 — comparison filters differ

**Failure:** current period HDFC but previous period all banks.  
**Severity:** P0  
**Prevention:** clone normalized filter set for comparison.  
**Tests:** C001 third turn.

### FIN-015 — division by zero in percentage change

**Failure:** crash/infinity/misleading 100%.  
**Severity:** P1  
**Prevention:** percentage null with reason.  
**Tests:** empty/zero comparison period.

---

## 5. Natural-language and model bugs

### NLP-001 — model calculates amount

**Failure:** prose/JSON includes a plausible figure without SQL.  
**Severity:** P0  
**Prevention:** InterpretationDraft has no amount/SQL fields; reject extras.  
**Tests:** adversarial prompt asks model to guess.

### NLP-002 — model emits SQL

**Failure:** SQL accepted/executed.  
**Severity:** P0  
**Prevention:** no SQL field, extra-forbid, deterministic compiler.  
**Tests:** malicious text-to-SQL output fixture rejected.

### NLP-003 — unknown bank invented/fuzzy matched

**Failure:** wrong canonical bank.  
**Severity:** P1  
**Prevention:** source lookup; clarify.  
**Tests:** typo close to two banks.

### NLP-004 — “recently” guessed

**Failure:** arbitrary 7/30-day range.  
**Severity:** P1  
**Prevention:** ambiguity lexicon + model detection.  
**Tests:** Q018.

### NLP-005 — correction adds contradiction

**Failure:** “Actually credits” retains debit + credit filters and returns zero.  
**Severity:** P1  
**Prevention:** patch semantics replace mutually exclusive metric/type.  
**Tests:** C003.

### NLP-006 — bare reference falls back to UTR

**Failure:** privacy/performance issue and wrong semantic match.  
**Severity:** P0/P1  
**Prevention:** fixed reference mapping; no fallback.  
**Tests:** missing_reference_with_utr.

### NLP-007 — UTR plaintext equality used against encrypted data

**Failure:** false no-data or full-table decrypt.  
**Severity:** P1/security  
**Prevention:** storage-mode gate; unsupported by default.  
**Tests:** Q022; ensure compiler never produces UTR predicate.

### NLP-008 — source narration prompt injection

**Failure:** description changes answer/tool behavior.  
**Severity:** P0  
**Prevention:** raw rows excluded from interpreter; structured untrusted treatment.  
**Tests:** prompt edge row has no effect.

### NLP-009 — wording model changes number

**Failure:** ComputedFacts correct but prose rounds/changes it.  
**Severity:** P0  
**Prevention:** deterministic templates or numeric allow-list check/fallback.  
**Tests:** simulated model outputs wrong value.

### NLP-010 — unsupported question receives general-knowledge answer

**Failure:** model answers outside data.  
**Severity:** P0  
**Prevention:** finance chat restricted; missing concept resolver.  
**Tests:** forecast/tax/general web questions.

---

## 6. Privacy/security bugs

### SEC-001 — raw account number returned

**Surfaces:** API, DOM, log, cache, export, model prompt, error.  
**Severity:** P0  
**Prevention:** centralized sanitizer + denylist serializer.  
**Tests:** search response bytes/DOM/export/log capture for every fixture account number.

### SEC-002 — account number leaks through description

**Failure:** column masked but narration contains raw value.  
**Severity:** P0  
**Prevention:** redact known account numbers in description.  
**Tests:** ACCOUNT-LEAK-001 and generated narrations.

### SEC-003 — raw UTR returned or logged

**Severity:** P0  
**Prevention:** masked field only; structured logging filters.  
**Tests:** raw UTR corpus absent across boundaries.

### SEC-004 — React XSS

**Failure:** `<script>`/HTML executes.  
**Severity:** P0  
**Prevention:** text rendering; forbid `dangerouslySetInnerHTML`; CSP.  
**Tests:** browser E2E prompt row, DOM contains text not element.

### SEC-005 — SQL injection through filter/sort/group

**Severity:** P0  
**Prevention:** allow-list mappings, bound values, no generic query endpoint.  
**Tests:** quotes/comments/keywords in description/reference; inspect compiled SQL/params.

### SEC-006 — spreadsheet formula injection

**Failure:** description/reference begins `=`, `+`, `-`, `@` and executes in Excel.  
**Severity:** P0/P1  
**Prevention:** encode text cells safely.  
**Tests:** export adversarial cells.

### SEC-007 — sensitive value in URL

**Severity:** P1  
**Prevention:** no account-number/UTR filters/routes; IDs only.  
**Tests:** navigation/history/network logs.

### SEC-008 — model provider receives raw rows

**Severity:** P0  
**Prevention:** prompt contract and interception test.  
**Tests:** fake provider records payload; assert no account/UTR/full rows.

### SEC-009 — cached response crosses dataset/user scope

**Severity:** P0  
**Prevention:** cache key scope + version + plan + privacy policy.  
**Tests:** two sessions/datasets.

---

## 7. Conversation/concurrency bugs

### STATE-001 — late response overwrites newer context

**Severity:** P1  
**Prevention:** context CAS and client version check.  
**Tests:** deliberately delay first request.

### STATE-002 — double submit duplicates query/message

**Severity:** P1/P2  
**Prevention:** idempotency key and disabled submit.  
**Tests:** double click/Enter/network retry.

### STATE-003 — idempotency key reused with different payload

**Severity:** P1  
**Prevention:** request hash; return 409.  
**Tests:** same key, changed text.

### STATE-004 — pending clarification applied to unrelated question

**Severity:** P1  
**Prevention:** message/context binding; new intent cancels pending.  
**Tests:** ask unrelated question while clarification open.

### STATE-005 — pronoun scope uses browser rows only

**Failure:** “those” refers only to current page, not full receipt set.  
**Severity:** P0/P1  
**Prevention:** active scope receipt ID.  
**Tests:** source set > page size.

### STATE-006 — refresh loses authoritative state

**Severity:** P2  
**Prevention:** fetch server QueryState; receipts by ID.  
**Tests:** reload after two turns.

---

## 8. API/export bugs

### API-001 — official total computed from paginated records

**Severity:** P0  
**Prevention:** separate aggregate receipt.  
**Tests:** page size 10 vs 100 same answer.

### API-002 — record endpoint ignores receipt predicate/version

**Severity:** P0  
**Prevention:** immutable normalized predicate and dataset version.  
**Tests:** mutate UI filters; old receipt rows unchanged.

### API-003 — export count/hash mismatch

**Severity:** P0  
**Prevention:** stream and compare before finalizing file.  
**Tests:** induce dataset change/job retry.

### API-004 — stale cached answer after dataset update

**Severity:** P0/P1  
**Prevention:** version/cutoff cache key.  
**Tests:** change manifest version.

### API-005 — error exposes SQL/source data

**Severity:** P0  
**Prevention:** domain translation and trace ID.  
**Tests:** simulated DB error response snapshot.

### API-006 — export decimals become scientific notation

**Severity:** P1  
**Prevention:** Decimal string/number formatting.  
**Tests:** max/very small values.

### API-007 — Excel corrupts long IDs

**Severity:** P1/P2  
**Prevention:** identifiers as text cells.  
**Tests:** open/read generated XLSX values.

---

## 9. UI bugs

### UI-001 — unsupported/no-data shows ₹0

**Severity:** P1  
**Tests:** Q019/Q017 visual snapshots.

### UI-002 — qualification hidden in collapsed section

**Severity:** P1  
**Prevention:** qualification before action row and in export.  
**Tests:** Q015 desktop/mobile.

### UI-003 — stale result appears below newer question

**Severity:** P1  
**Tests:** delayed response E2E.

### UI-004 — raw HTML rendering

**Severity:** P0  
**Tests:** prompt/script narration.

### UI-005 — negative balance styled as app error

**Severity:** P2  
**Prevention:** financial negative style distinct from system error.  
**Tests:** account table/accessibility text.

### UI-006 — hidden timezone/end exclusivity

**Severity:** P1/P2  
**Prevention:** visible human label; exact interval in calculation.  
**Tests:** receipt detail.

### UI-007 — chart/table disagree

**Severity:** P0/P1  
**Prevention:** same server breakdown payload.  
**Tests:** sum breakdown and compare to receipt; no client transformation loss.

### UI-008 — masked value raw in DOM attribute

**Severity:** P0  
**Tests:** inspect rendered DOM/React props/network fixtures.

### UI-009 — mobile keyboard covers submit

**Severity:** P2  
**Tests:** mobile viewport E2E.

### UI-010 — keyboard/focus inaccessible dialogs

**Severity:** P2  
**Tests:** axe + keyboard scenarios.

---

## 10. Performance/reliability bugs

### PERF-001 — deep OFFSET pagination

**Severity:** P1 at scale  
**Prevention:** keyset cursor.  
**Tests:** large fixture latency.

### PERF-002 — model called for explorer filters

**Severity:** P2/cost  
**Prevention:** structured endpoints bypass model.  
**Tests:** provider call counter.

### PERF-003 — full source rows sent to model

**Severity:** P0 privacy/cost  
**Prevention:** computed facts only.  
**Tests:** provider payload capture.

### PERF-004 — query lacks timeout/cancel

**Severity:** P1  
**Tests:** intentionally slow query/lock.

### PERF-005 — unbounded grouping/source preview

**Severity:** P1  
**Prevention:** dimension/cardinality/page caps.  
**Tests:** max limits.

### PERF-006 — connection timezone not initialized after pool recycle

**Severity:** P0  
**Tests:** reconnect and boundary query.

---

## 11. Test pyramid and required commands

### Fast gate

```bash
python scripts/generate_dataset.py --check
python scripts/validate_dataset.py
python -m unittest discover -s tests -v
python scripts/validate_repository.py
```

### Backend gate after implementation

- Ruff/format/type check
- Django system check/migrations check for app DB separation
- unit tests
- MySQL integration tests
- OpenAPI schema test

### Frontend gate after implementation

- TypeScript strict compile
- lint
- unit/component tests
- accessibility checks
- Playwright canonical/adversarial flows

### Pre-demo smoke

1. Load a clean fixture.
2. Run Q001/Q024/Q014/Q015/Q019/Q025.
3. Open source rows and export.
4. Search DOM/log/export for raw account/UTR values.
5. Trigger prompt/XSS row.
6. Simulate network retry/stale request.
7. Verify cutoff/timezone.
8. Record commit/model/dataset versions.

---

## 12. Bug report template

```text
ID/severity:
Environment/commit/dataset/model/prompt version:
User question/request:
Expected semantic state and receipt:
Actual state/value:
Source rows/query plan/template ID:
Privacy impact:
Reproduction steps:
Screenshots/trace ID:
Root cause:
Regression test:
Fix and contract/docs changes:
```

A screenshot alone is insufficient for a financial bug; include query ID, plan, source count/hash
and the raw-source recomputation used to prove the expected result.
