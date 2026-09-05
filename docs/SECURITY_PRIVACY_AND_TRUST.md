# Security, Privacy and Trust Specification

This is a hackathon prototype, not a production banking system. The trust boundary should still be
implemented as though the values could affect a finance decision. The most important risks are a
wrong official number, leakage of sensitive identifiers, arbitrary query execution, and the model
turning unstructured narration into a fabricated finance fact.

## 1. Data classification

| Field/data | Classification | Browser/model/export policy |
|---|---|---|
| `bank_code`, `bank_name` | Internal reference | May be displayed and used by the model |
| `account_id`, `entity_id` | Internal identifier | May be displayed where needed; avoid public logs |
| `program_id` | Internal business metadata | May be displayed and filtered |
| `available_balance` | Confidential finance value | Display only through authenticated/demo scope; exact decimal |
| `account_number` | Sensitive | Never raw in model, browser, logs, analytics or normal export |
| `transaction_id` | Internal identifier | Displayable; treat as opaque string, not guaranteed strict UUID |
| `transaction_date`, `transaction_type`, `transaction_amount` | Confidential transaction data | Display in authorised prototype flow; exact decimal and timezone |
| `description` | Untrusted confidential text | Redact account-like substrings; render as text; never follow as instruction |
| `transaction_reference_id` | Searchable internal reference | Exact search and display allowed; warn that it may be non-unique |
| `utr_number` | Sensitive | Keep encrypted/tokenized or server-only; never raw in model/browser/export |
| conversation text | Confidential user input | Minimise retention; do not mix across conversations |
| query plan/receipt | Audit metadata | Store without raw sensitive values; return to authorised client |
| evaluation gold | Test-only confidential logic | Never imported by runtime application code |

## 2. Trust invariants

1. The source of finance truth is limited to `bank`, `account`, and `` `transaction` ``.
2. An answer is official only after a QueryPlan passes schema, semantic, query and result checks.
3. All financial arithmetic occurs in MySQL `DECIMAL` or Python `Decimal`.
4. The model cannot submit SQL, choose arbitrary columns, or calculate the headline value.
5. Unsupported dimensions return no number or transaction list.
6. Account numbers and UTRs are removed before any model or browser boundary.
7. Source narration is data, not an instruction channel.
8. Receipt, source rows and export must describe the same persisted query execution.
9. A failed required check changes the response to validation failure; it never degrades silently.

## 3. Sensitive-field pipeline

```text
MySQL source row
  → repository fetches only needed columns
  → privacy mapper masks account number and UTR
  → description redactor removes exact known account numbers and suspicious long digit runs
  → safe domain object
  → optional model context containing only bounded, sanitised summaries
  → DRF serializer
  → React text rendering / receipt-bound export
```

Recommended masking:

- account number: preserve only last four digits, e.g. `••••••••••9069`;
- UTR: do not expose by default; use `Protected` or a stable server-side token when a later
  workflow genuinely needs correlation;
- account references inside descriptions: replace with `[REDACTED_ACCOUNT]`;
- generic long digit sequences: apply a conservative secondary redactor, but preserve the explicit
  `transaction_reference_id` field separately so search remains reliable.

The demo should include a source narration that contains an account number and prove that the raw
value does not appear in API JSON, rendered DOM or export.

## 4. UTR storage and lookup

The organiser notes that `utr_number` may be encrypted. Encryption changes search behavior:

- randomised encryption cannot support `WHERE utr_number = ?` against plaintext;
- deterministic encryption leaks equality patterns and requires careful key handling;
- decrypting every row for search is not acceptable at scale;
- a separate keyed-hash lookup column could support equality without storing plaintext, but it is
  not part of the supplied source schema.

Default prototype decision: **UTR lookup is unsupported** unless the provided runtime includes an
approved decryption/token lookup service. A user who says “UTR” receives a clear protected-field
explanation rather than an attempted search over `transaction_reference_id`.

## 5. Query safety

- QueryPlan values are validated against JSON Schema and semantic rules.
- The query compiler selects a named, tested query family.
- Identifiers, joins, operators, aggregation functions and ordering fields come from server code.
- User values are bound parameters; string interpolation is prohibited.
- Use a read-only source database account.
- Enforce statement timeout, result-row cap and cursor pagination.
- Do not allow `SELECT *`; request only source and proof columns needed for the response.
- Reject multi-statements and comments in any database helper.
- Quote the reserved table name as `` `transaction` ``.
- Log query-family name and parameter classes, not raw sensitive values.

## 6. Prompt-injection and untrusted text

A transaction description may contain HTML, Markdown, SQL-looking text or an instruction such as
“ignore the previous prompt”. It remains source data.

Controls:

- never concatenate descriptions into the system/developer prompt as instructions;
- place bounded source snippets in an explicitly delimited data structure;
- prefer deterministic answer templates; the model does not need source narration for totals;
- escape or insert descriptions with React text nodes, never `dangerouslySetInnerHTML`;
- neutralise spreadsheet formula prefixes in CSV/XLSX exports (`=`, `+`, `-`, `@`) when a text
  cell could be interpreted as a formula;
- test the planted prompt/HTML edge record across API, UI and export.

## 7. Conversation isolation and multi-turn integrity

- Each turn carries `conversation_id`, unique `message_id`, and expected `context_version`.
- The server stores canonical QueryState, not just raw chat history.
- Follow-ups apply an explicit patch to the preceding accepted state.
- A stale context version returns `409` and no execution.
- Do not reuse account/entity filters across conversation IDs.
- Delete/expiry operations remove or cryptographically unlink stored state and exports.
- Idempotency prevents duplicate rows and duplicate model/query charges after retries.

## 8. Logging and observability

Allowed structured fields:

- trace/request/query/conversation IDs;
- query family and schema versions;
- high-level metric and non-sensitive filter types;
- row count, timing, validation status and error code;
- model identifier, token counts and cost where available.

Never log:

- raw account number or UTR;
- full transaction description by default;
- API keys or database URLs;
- raw model prompt containing source rows;
- CSV/XLSX contents;
- evaluation expected answers in production logs.

Add automated tests that scan logs/JSON/exports for every known fixture account number and UTR.

## 9. API and browser controls

For a local/demo environment:

- bind services to localhost by default;
- restrict CORS to the configured frontend origin;
- enforce JSON body size and message-length limits;
- reject unsupported media types;
- set security headers and a restrictive Content Security Policy;
- use `Cache-Control: no-store` for finance responses and exports;
- do not put filters containing sensitive values into analytics events;
- prefer opaque cursor tokens over raw offset and query internals;
- expire signed export links and bind them to query ID/dataset version.

Production-grade multi-tenant authentication and authorisation are out of scope, but the code should
have one central access-policy seam so source rows are never fetched first and filtered later.

## 10. Answer trust states

| Status | Meaning | May show official number? |
|---|---|---|
| Verified | Required checks pass and source lineage is available | Yes |
| Qualified | Computation passes but a declared coverage/data limitation matters | Yes, with prominent qualification |
| No data | Valid supported query matched zero rows | Show zero/count only when mathematically appropriate |
| Clarification | Multiple materially different interpretations remain | No |
| Unsupported | Required source field/concept is absent or protected | No |
| Validation failed | Execution or a required invariant failed | No |

Do not show an arbitrary model confidence percentage. Confidence is derived from operational facts:
parser validity, entity/date resolution, data availability and validation outcomes.

## 11. Threat-focused test matrix

| Threat | Required test |
|---|---|
| SQL injection in question/reference/description filter | Query family unchanged; value bound; no additional statement |
| Prompt injection in description | Text remains inert; answer and query plan unaffected |
| Stored/reflected XSS | Description renders literally; CSP remains effective |
| CSV formula injection | Exported text is escaped/prefixed safely |
| Account-number leakage | Known account strings absent from API, DOM snapshot, logs and export |
| UTR leakage | Known UTR strings absent from model payload, API, DOM, logs and export |
| Float rounding | Max and mixed-decimal totals equal gold decimal strings |
| Stale multi-turn race | Older request cannot replace newer context/result |
| Gold leakage | Backend/frontend runtime imports fail CI scan |
| Unsupported inference | Vendor/payout/reconciliation/category/history questions return no number |
| Duplicate reference | All exact matches returned with qualification; no arbitrary first row |
| Timezone boundary | Month-start/end rows appear in exactly one half-open interval |

## 12. Demo disclosure

The dataset is synthetic and patterned after the organiser’s sample. State this in the UI, README,
deck and export metadata. Do not claim production security certification, 20M-row performance,
model accuracy, or privacy compliance without measured evidence.
