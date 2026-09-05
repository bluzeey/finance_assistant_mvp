# Supported Question Catalogue

This catalogue defines product scope for the supplied `bank`, `account`, and `transaction` schema.
It is a semantic contract, not merely example copy.

## Supported with deterministic computation

### Transaction flows

- How much did we spend/debit in August 2026?
- How much money came in/was credited last month?
- What was net cash flow for a date range?
- How many debit or credit transactions occurred?
- What was the average or largest transaction?
- Break down debit/credit amount or count by bank, program, account, entity, day or month.
- Which bank/program had the highest amount or count?
- Compare a metric with the previous period.

“Spend” maps to debit transaction amount. The product must show that interpretation because the
schema does not contain an accounting expense or payout classification.

### Lookup and exploration

- Find transaction ID X.
- Find reference X.
- Show debit/credit transactions for a date range.
- Show transactions for bank/program/account/entity X.
- Show transactions above/below an amount.
- Show descriptions containing literal text X.

Bare reference means exact, case-sensitive `transaction_reference_id`. Description matching is
qualified unstructured-text search and does not establish vendor identity or payment purpose.

### Current account snapshot

- What is the current available balance across all accounts?
- Break down current available balance by bank/program/entity/account.
- How many accounts match a bank/program/entity filter?
- Which accounts currently have a negative balance?

Always label this as current snapshot as of the dataset cutoff. It is not a historical period metric.

## Questions that require clarification

Clarify when materially different valid interpretations exist, for example:

- “How much money moved recently?” — credit, debit or net; which date range?
- “Show the biggest transactions.” — all, debit or credit; what period and how many?
- “Compare this with before.” — which prior interval if it cannot be inherited safely?
- “Find ref X” when the user explicitly mixes reference and UTR language.
- Unknown or multiple account/entity identifiers.

No official amount is shown before clarification.

## Unsupported by this source

- vendor totals or vendor payouts;
- reconciliation/unreconciled/open/outstanding status;
- chart-of-accounts or accounting category analysis;
- invoice, bill, approval or settlement status;
- historical account balance as of a past date;
- forecast, budget, plan or contract terms;
- beneficiary/counterparty identity as a guaranteed field;
- UTR equality lookup when UTR is encrypted and no approved token index exists.

The assistant should identify the missing field, return no fabricated value, and offer a nearby
source-supported alternative only when it does not mislabel the result.
