# Frontend Implementation Contract

Build a **React + TypeScript + Vite** application. Read
`../docs/UI_UX_SPEC.md`, `page_acceptance_matrix.csv`, and
`../contracts/openapi.yaml` before implementing pages.

## Required foundations

- TypeScript strict mode
- React Router
- TanStack Query
- OpenAPI-generated or contract-derived API types
- accessible headless UI primitives
- React Hook Form or an equivalently typed form layer
- Vitest + Testing Library + MSW
- Playwright for P0 user journeys
- exact decimal strings retained in state
- no official finance aggregation in the browser

## Information architecture

```text
/ask                     conversational assistant
/ask/:conversationId     multi-turn conversation and answer receipts
/transactions            filtered source-record explorer
/accounts                current balances by bank/program/entity/account
/data-health             freshness, integrity and source limitations
/glossary                 definitions, date/reference/privacy behavior
/evaluation               actual benchmark runs and model rationale
/about                    scope, architecture and synthetic-data disclosure
```

There is intentionally no Vendor or Reconciliation page. The supplied source has neither an
authoritative vendor dimension nor reconciliation status.

## First vertical slice

Implement `/ask/:conversationId` using
`../contracts/sample_verified_answer_receipt.json` as a development fixture only. It must include:

- question composer with send, stop, retry and example prompts;
- staged progress: understanding → resolving → querying → validating;
- answer status and exact INR headline;
- interpretation chips for metric, date range and filters;
- source-row count and dataset cutoff;
- evidence panel tabs: Receipt, Records, Checks, Query and Export;
- cursor-paginated transaction records;
- loading, no-data, clarification, unsupported, validation-failed and network-error states;
- request cancellation, idempotency key and stale-response protection;
- usable desktop, tablet and 360px mobile layouts.

The production UI must consume backend receipts. It must never import evaluation gold files or
calculate official totals from downloaded records.

## Source-record privacy

- Display masked account labels such as `HDFC •••• 9069`, never raw account numbers.
- Do not expose raw UTR values. Show `Unavailable`, `Protected`, or an approved masked/tokenized
  representation based on API metadata.
- Descriptions arrive redacted and must be inserted as text content.
- Reference IDs are copyable because `transaction_reference_id` is the defined plaintext lookup
  field; explain that it may be non-unique.
- Exports are generated server-side from a receipt and inherit the same masking rules.

## State rules

- URL parameters are the source of truth for explorer filters.
- Store exact amount strings rather than JavaScript numbers.
- A newer response cannot be overwritten by an older request completing late.
- A `409` context-version conflict triggers state refresh and a visible retry affordance.
- Clarification and unsupported responses contain no amount placeholder or chart.
- “Description contains X” is visibly qualified as text search, never relabelled as a vendor.

## Suggested structure

```text
frontend/src/
├── app/             # router, providers, error boundaries
├── api/             # generated types, client, query keys
├── components/      # reusable accessible primitives
├── features/
│   ├── assistant/
│   ├── evidence/
│   ├── transactions/
│   ├── accounts/
│   ├── data-health/
│   ├── glossary/
│   └── evaluation/
├── lib/             # formatting, URL state, request IDs
└── test/            # MSW, fixtures and helpers
```

## Target commands

```bash
cd frontend
npm ci
npm run dev
npm run typecheck
npm run lint
npm run test
npm run test:e2e
npm run build
```
