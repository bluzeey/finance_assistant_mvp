# Frontend Implementation Contract

Build a React + TypeScript + Vite application under this directory. Read `../docs/UI_UX_SPEC.md` and `page_acceptance_matrix.csv` first.

## Required foundations

- TypeScript strict mode;
- React Router;
- TanStack Query;
- generated/reused OpenAPI types;
- accessible headless primitives;
- Vitest + Testing Library + MSW;
- Playwright for P0 E2E;
- no browser-side official finance aggregation.

## First vertical slice

Implement `/ask/:conversationId` with:

- composer and staged loading;
- verified AnswerCard;
- interpretation chips;
- evidence panel with Receipt, Records, Checks, and Query tabs;
- network/error/empty states;
- cancellation, idempotency, and stale-response guard;
- desktop and 360px mobile flow.

Use `contracts/sample_verified_answer_receipt.json` as a development fixture only. Production UI must consume the backend response.
