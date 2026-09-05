# Security, Privacy, and Trust Specification

This is a single-company synthetic hackathon prototype without production authentication. That does not remove the need for safe boundaries, because finance data and model behavior are high-trust surfaces.

## Threats in scope

- prompt injection in user or record text;
- model-generated SQL or invented IDs;
- SQL injection through filters/sorts/cursors;
- cross-query cursor or export mix-up;
- stale/cached answers from a different dataset snapshot;
- CSV/XLSX formula injection;
- stored/reflected XSS;
- secrets exposed to Vite or logs;
- runtime access to benchmark gold;
- denial of service through unbounded scans/exports;
- query/context race conditions;
- accidental representation of synthetic data as real.

## Controls

### Data and database

- application finance role is SELECT-only;
- conversation/audit writes use a controlled role/connection;
- bound parameters only;
- allow-listed query registry and columns;
- statement timeout and cancellation;
- cursor query binding/signing;
- no raw SQL in errors;
- snapshot/version in cache and export keys.

### Model

- closed structured-output schema;
- no SQL field in model schema;
- record text excluded from parser when possible;
- explicit untrusted-data delimiters when included;
- deterministic resolver validates IDs/dates;
- one repair retry then fail closed;
- no arithmetic or confidence authority;
- prompt/model version in audit.

### API

- DRF serializers and length/enum validation;
- `application/problem+json` errors;
- idempotency and body hash;
- context version;
- rate/concurrency/request-size limits;
- restrictive CORS;
- environment-based secrets;
- evaluation endpoints disabled outside local/demo mode.

### Frontend

- render all dynamic content as text, never raw HTML;
- content security policy;
- no secrets in `VITE_*` variables;
- URL/query state validation;
- cancellation and stale-response rejection;
- spreadsheet-prefix sanitisation performed server-side and tested;
- synthetic-data banner on all pages.

### Logging

Allowed: IDs, versions, metric/intent/status, timings, row-count bucket, validation codes, token/cost metadata.  
Redacted by default: user message, vendor names, source descriptions, raw rows, prompts, SQL parameters, secrets.

## Privacy posture

All bundled data is synthetic. A real deployment would additionally require tenant isolation, least-privilege roles, audit retention, deletion policy, data classification, DLP/vendor review, encryption, region controls, and approval of model providers. These are explicitly outside the hackathon implementation but should be mentioned in the presentation limitations.

## Security release checks

- no committed secrets or `.env`;
- dependency/lockfile scan;
- runtime import scan for `evaluation/expected_`;
- prompt-injection regression passes;
- SQL compiler injection tests pass;
- XSS and formula-injection tests pass;
- export/query snapshot mismatch fails safely;
- logs inspected for sensitive payload leakage;
- synthetic-data label visible.
