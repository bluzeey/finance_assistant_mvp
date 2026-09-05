# Schema Alignment, Product Scope and Gap Decisions

## Why this document exists

The hackathon problem statement gives examples involving vendor payouts and unreconciled
transactions. The actual database contract supplied later has only `bank`, `account` and
`transaction`. A credible finance product must resolve that conflict in favor of the source schema:
no field means no defensible answer.

This document replaces the earlier repository assumptions that included companies, vendors,
payouts, reconciliation and a chart of accounts.

## What can be answered directly

### Transaction movement

The source supports exact debit/credit aggregation over `transaction_date`:

```text
debit spend = SUM(transaction_amount WHERE transaction_type='debit')
credit inflow = SUM(transaction_amount WHERE transaction_type='credit')
net cash flow = credit inflow - debit spend
```

It also supports count, average, largest transaction and time/bank/account/entity/program
breakdowns.

### Current balance

`account.available_balance` supports a current snapshot across one or more distinct accounts.
It does not support “balance on 31 August”, daily balance trajectories or reconciliation between
balance and transaction history because no opening balance/snapshot history exists.

### Record lookup

- `transaction_id`: exact opaque-string lookup.
- `transaction_reference_id`: exact, case-sensitive lookup.
- `account_id`, `entity_id`, `program_id`, `bank_code`: exact structured filters.
- `description`: literal search for exploration, visibly qualified.

## What cannot be answered from this schema

| Concept | Missing source fields | Required product behavior |
|---|---|---|
| Vendor spend | Canonical vendor ID/name and mapping | Clarify that narration search is not vendor attribution. Offer literal text search only after confirmation. |
| Vendor payouts | Vendor, payout event, payout status/date | Unsupported; return no number. |
| Reconciliation | Match/status/outstanding amount | Unsupported; return no transaction list. |
| Expense/category/accounting view | Ledger account/category/chart of accounts | Unsupported. |
| Historical balance | Balance snapshots or opening/closing ledger | Unsupported. |
| Forecast/budget | Future schedule, contract or plan | Unsupported. |
| Named entity/customer | Entity master with names | Require exact `entity_id`; do not invent a name. |
| UTR plaintext search | Reliable searchable representation | Disabled in encrypted/tokenized mode. |

## Product language rules

Words must track evidence precisely:

- Say **“debit transactions”**, not “vendor payouts,” unless a later source field proves payout semantics.
- Say **“description contains ‘Selection Mobile’”**, not “Selection Mobile vendor spend.”
- Say **“current available-balance snapshot”**, not “cash balance history.”
- Say **“no matching rows”** after a valid zero-row query; say **“unsupported”** when the field is absent.
- Say **“reference matched two records”**, not “the transaction,” when the reference is non-unique.

## Why narration extraction is not an authoritative fix

A model or regex can extract likely counterparties from bank narration, but this creates a derived,
probabilistic classification not present in the source. It can be useful as a demo experiment only if:

1. it is labelled “inferred from description”;
2. it never changes official source totals;
3. users can inspect every contributing row;
4. confidence is shown per extraction;
5. the UI does not call it a canonical vendor master;
6. evaluation measures extraction separately;
7. the base assistant still refuses exact vendor/payout claims.

For the hackathon core, literal description filtering is safer and easier to defend.

## Migration from the obsolete fixture

Removed source artifacts:

- `companies`
- `vendors`
- `vendor_aliases`
- `chart_of_accounts`
- `vendor_payouts`
- `reconciliation_status`
- PostgreSQL-specific DDL and loader

Added or changed:

- MySQL 8 DDL for the exact three tables
- `bank.csv`, `account.csv`, `transaction.csv`
- opaque-string ID handling
- account/UTR masking and narration redaction
- exact reference semantics
- current-balance snapshot semantics
- 30 schema-aligned benchmark cases
- explicit unsupported tests for vendor payout/reconciliation/category/history
- MySQL keyword/collation/timezone regression tests

## Future extension boundary

If organisers later provide additional tables, add them through a versioned schema migration and
new semantic contracts. Do not retrofit them by silently parsing descriptions. Required additions
would be:

- vendor master with stable ID and aliases;
- payout event with status/date/reference;
- reconciliation match with matched/unmatched amount;
- chart of accounts/category mapping;
- balance snapshots;
- entity master;
- documented currency/timezone fields.

Until then, the three-table contract is definitive.
