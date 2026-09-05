# API and Answer-State Examples

These examples describe behavior; machine shapes remain authoritative in `contracts/openapi.yaml` and JSON schemas.

## 1. Verified answer

```http
POST /api/v1/conversations/{conversation_id}/messages
Idempotency-Key: 55aee550-59cd-4e2c-ae23-a4f6ea447eef
Content-Type: application/json
```

```json
{
  "message": "How much did we spend on vendor payouts last month?",
  "client_turn_id": "2d64979d-8615-444f-84d3-e6149b3ee43b",
  "expected_context_version": 0
}
```

The response has status `verified`, value `10000874.04`, currency `INR`, exact August 2026 range, completed-only status filter, 55 source records, validation checks, and an evidence/export path. See `contracts/sample_verified_answer_receipt.json`.

## 2. Needs clarification

Question: `How much did we spend on Acme last month?`

Behavior:

- status: `needs_clarification`;
- `answer.value`: null;
- `primary_metric`: null or non-numeric descriptor according to contract implementation;
- choices: Acme Cloud Services and Acme Office Supplies with stable vendor IDs;
- pending clarification stored in QueryState;
- no SQL financial aggregation and no total before the user chooses.

## 3. Not answerable

Question: `What will our cash balance be next quarter?`

Behavior:

- status: `not_answerable`;
- no financial number;
- explain that opening cash balance, future cash-flow/forecast inputs, and predictive scope are absent;
- offer supported historical payout/spend questions without pretending they answer the forecast.

## 4. No matching rows

Question with a valid supported filter that matches zero records.

Behavior:

- status: `no_matching_rows`;
- explain exact filters/period and that zero matching records were found;
- distinguish “zero total” from missing/incomplete coverage;
- return zero only when the metric semantics define zero as valid and coverage checks pass.

## 5. Error

A required validation fails or PostgreSQL times out.

Behavior:

- status: `error` when an audit receipt is produced, or problem+json when the request cannot safely produce one;
- no financial value or stale partial result;
- retryability and trace ID;
- safe detail only, never SQL, prompt, stack trace, or secrets.

## 6. Context conflict

```http
HTTP/1.1 409 Conflict
Content-Type: application/problem+json
```

The client sent an old `expected_context_version`. The frontend must not overwrite the newer conversation and should refresh/reconcile state before offering a retry.

## 7. Source records

```http
GET /api/v1/queries/{query_id}/records?limit=100&cursor=...
```

The cursor is opaque and bound to the query ID. Records, total count, and export lineage must match the immutable receipt.

## 8. Export

```http
GET /api/v1/queries/{query_id}/export?format=csv
GET /api/v1/queries/{query_id}/export?format=xlsx
```

Exports use the same dataset snapshot/source lineage. A mismatch fails closed instead of returning a file based on changed data.
