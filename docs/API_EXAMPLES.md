# API Examples

Examples use the contract in `contracts/openapi.yaml`. JSON finance values are decimal strings.
All timestamps are interpreted in Asia/Kolkata, and source-data responses are privacy mapped.

## 1. Metadata

```http
GET /api/v1/metadata
```

```json
{
  "dataset_version": "tiby-finance-fixture-v2.0.0",
  "data_as_of": "2026-09-03T23:59:59.999999+05:30",
  "currency": "INR",
  "timezone": "Asia/Kolkata",
  "source_tables": ["bank", "account", "transaction"],
  "supported_metrics": [
    "debit_total", "credit_total", "net_cash_flow", "transaction_count",
    "average_transaction_amount", "largest_transaction",
    "current_available_balance", "account_count", "transaction_lookup"
  ],
  "unsupported_concepts": [
    {"concept": "vendor_payouts", "reason": "No vendor or payout field/table exists."},
    {"concept": "reconciliation_status", "reason": "No reconciliation or outstanding field exists."},
    {"concept": "historical_balance", "reason": "Only a current available-balance snapshot exists."}
  ]
}
```

## 2. Ask a supported question

```http
POST /api/v1/assistant/messages
Content-Type: application/json
Idempotency-Key: msg-demo-001
```

```json
{
  "conversation_id": "demo-conversation",
  "message_id": "msg-demo-001",
  "text": "How much did we spend last month?",
  "locale": "en-IN",
  "timezone": "Asia/Kolkata"
}
```

A successful response returns the `AnswerReceipt` shape. The canonical fixture answer is:

```json
{
  "schema_version": "2.0",
  "query_id": "qry_demo_august_debit_spend",
  "conversation_id": "demo-conversation",
  "context_version": 1,
  "status": "verified",
  "answer": {
    "headline": "₹12,17,58,278.46 spent in August 2026",
    "summary": "Across all accessible accounts, 205 debit transactions totalled ₹12,17,58,278.46 from 1 August through 31 August 2026.",
    "display_value": "121758278.46",
    "unit": "INR"
  }
}
```

The complete fixture is `contracts/sample_verified_answer_receipt.json`.

## 3. Follow-up comparison

Request:

```json
{
  "conversation_id": "demo-conversation",
  "message_id": "msg-demo-002",
  "text": "How does that compare with the month before?",
  "locale": "en-IN",
  "timezone": "Asia/Kolkata"
}
```

Expected semantics:

- inherit `debit_total` and all non-date filters;
- current range remains August 2026;
- comparison range becomes July 2026;
- current amount: `121758278.46`;
- prior amount: `69995241.84`;
- absolute change: `51763036.62`;
- percentage change is computed by the backend with defined zero-baseline behavior.

## 4. Clarification response

Question: `How much money moved recently?`

```json
{
  "schema_version": "2.0",
  "disposition": "clarify",
  "metric": null,
  "date_range": null,
  "filters": {},
  "group_by": [],
  "comparison": null,
  "sort": [],
  "limit": 100,
  "qualifications": [],
  "clarification": {
    "question": "Should money moved mean credits, debits, or net cash flow, and what date range should 'recently' cover?",
    "options": [
      {"id": "debits_last_30_days", "label": "Debits in the last 30 days"},
      {"id": "credits_last_30_days", "label": "Credits in the last 30 days"},
      {"id": "net_last_30_days", "label": "Net cash flow in the last 30 days"}
    ]
  },
  "unsupported_reason": null
}
```

No number or chart is returned while a material ambiguity remains.

## 5. Unsupported response

Question: `Which transactions are still unreconciled?`

```json
{
  "status": "unsupported",
  "answer": {
    "headline": "Reconciliation status is not available",
    "summary": "The supplied bank, account and transaction tables contain no reconciliation status, match or outstanding-amount field.",
    "display_value": null,
    "unit": null
  },
  "unsupported": {
    "concept": "reconciliation_status",
    "missing_fields": ["reconciliation_status", "matched_amount", "outstanding_amount"],
    "safe_alternatives": [
      "List debit or credit transactions for a date range",
      "Search for an exact transaction reference"
    ]
  }
}
```

## 6. No-data response

A supported exact reference that matches nothing is not a system error:

```json
{
  "status": "no_data",
  "answer": {
    "headline": "No transaction matched reference NO-SUCH-REFERENCE",
    "summary": "The exact, case-sensitive transaction_reference_id lookup returned zero rows.",
    "display_value": null,
    "unit": null
  },
  "warnings": []
}
```

## 7. Exact reference lookup

```http
GET /api/v1/transactions?transaction_reference_id=HDFCH01078329532&page_size=50
```

Rules:

- exact and case-sensitive;
- targets `transaction_reference_id`, not UTR;
- duplicate references return all rows plus a qualification;
- no fuzzy fallback.

Example safe row:

```json
{
  "transaction_id": "014b7179-e696-4837-9b8e-7164d171b760",
  "account_id": "acfbe204-7541-492c-a352-040aa984bedc",
  "masked_account_number": "••••••••••9069",
  "bank_code": "HDFC",
  "bank_name": "HDFC BANK LIMITED",
  "entity_id": "f2f5e332-c2d1-4555-9a6b-65c7cd195077",
  "program_id": 21,
  "transaction_date": "2026-06-24T06:39:10+05:30",
  "transaction_type": "debit",
  "description": "NEFT - UTIB0002678 - 95604250 - [REDACTED_ACCOUNT] - UMANG SELECTIONHAPURBPES DPF10129",
  "transaction_amount": "7959.00",
  "transaction_reference_id": "HDFCH01078329532",
  "masked_utr_number": "Protected"
}
```

## 8. Filtered transaction explorer

```http
GET /api/v1/transactions?start=2026-08-01T00:00:00%2B05:30&end_exclusive=2026-09-01T00:00:00%2B05:30&transaction_type=debit&bank_code=HDFC&page_size=50
```

Pagination is cursor based. The server defines stable ordering as
`transaction_date DESC, transaction_id DESC` unless another allow-listed order is requested.

## 9. Accounts

```http
GET /api/v1/accounts?bank_code=HDFC&program_id=21&page_size=50
```

```json
{
  "results": [
    {
      "account_id": "acfbe204-7541-492c-a352-040aa984bedc",
      "entity_id": "f2f5e332-c2d1-4555-9a6b-65c7cd195077",
      "masked_account_number": "••••••••••9069",
      "program_id": 21,
      "available_balance": "-25907487.00",
      "bank_code": "HDFC",
      "bank_name": "HDFC BANK LIMITED"
    }
  ],
  "next_cursor": null
}
```

The UI must label these values **current available balance as of the dataset cutoff**, not balance
for a selected transaction period.

## 10. Receipt records and export

```http
GET /api/v1/assistant/receipts/qry_demo_august_debit_spend/records?page_size=50
GET /api/v1/assistant/receipts/qry_demo_august_debit_spend/export?format=csv
GET /api/v1/assistant/receipts/qry_demo_august_debit_spend/export?format=xlsx
```

Exports must include query ID, dataset version, data cutoff, interpretation, source-row count and
privacy-safe records. They are generated from the persisted receipt/query plan, not reconstructed
from browser filters.

## 11. Problem details

Invalid request:

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/problem+json
```

```json
{
  "type": "https://ledgerproof.local/problems/invalid-filter",
  "title": "Invalid transaction filter",
  "status": 422,
  "detail": "end_exclusive must be later than start.",
  "code": "INVALID_DATE_RANGE",
  "trace_id": "trc_01J...",
  "retryable": false,
  "field_errors": {"end_exclusive": ["Must be later than start."]}
}
```

Other important statuses:

- `409 CONTEXT_VERSION_CONFLICT` for a stale multi-turn patch;
- `409 IDEMPOTENCY_KEY_REUSED` when the same key is paired with different content;
- `422 AMBIGUOUS_QUERY` only when using an error-style clarification endpoint; ordinary assistant
  clarification should be a successful typed response;
- `503 SOURCE_UNAVAILABLE` or `QUERY_TIMEOUT` with no official number;
- `500 VALIDATION_FAILED` with trace ID and no computed headline.
