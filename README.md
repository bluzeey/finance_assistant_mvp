# LedgerProof Finance Assistant

LedgerProof is a hackathon-ready reference repository for **an auditable conversational finance assistant**. It lets a user ask questions such as “How much did we spend on vendor payouts last month?” and returns a deterministic answer with the exact interpretation, calculation method, validation checks, and source records.

The repository is deliberately more than a feature brief. It contains a deterministic synthetic finance dataset, PostgreSQL schema and views, semantic contracts, API contracts, benchmark cases, a complete React UX specification, a Django/DRF backend design, a bug and QA playbook, and an agent-executable backlog.

> Core rule: the language model interprets language; PostgreSQL and Python compute financial values. An ambiguous or unsupported question returns no number.

## Project identity

- **Product name:** LedgerProof
- **Synthetic company:** Northstar Labs India Private Limited
- **Frontend:** React + TypeScript + Vite
- **Backend:** Python + Django + Django REST Framework
- **Data:** PostgreSQL; Redis/Celery only where asynchronous jobs are useful
- **Primary currency:** INR
- **Dataset anchor:** 3 September 2026
- **Scope:** vendor spend, vendor payouts, reconciliation status, account/vendor lookup, source records, exports, data health, and simple anomaly callouts

## What is already included

| Area | Contents |
|---|---|
| Product | End-to-end PRD, personas, jobs, route behavior, states, acceptance criteria, and demo flow |
| UX | Desktop/tablet/mobile information architecture, page specs, answer receipts, empty/error/loading states, keyboard/accessibility requirements |
| Data | 33 accounts, 56 vendors, 189 aliases, 969 transactions, 919 payout attempts, and 957 reconciliation records |
| Edge cases | Ambiguous aliases, partial reconciliation, credits, reversals, duplicates, missing links, nulls, stale data, and prompt injection inside record text |
| Grounding | QueryPlan, QueryState, ComputedFacts, AnswerReceipt, problem-details, OpenAPI, and semantic metric contracts |
| Evaluation | 22 gold single-turn cases, multi-turn conversations, expected aggregates, edge-case manifest, and model scorecard template |
| Engineering | PostgreSQL schema/views/indexes, seed generator, loader, fixture validator, repository validator, Docker services, CI, and dependency-ordered backlog |
| Research | Competitor and finance-user research report in Markdown and DOCX |

## Read these first

1. [`AGENTS.md`](AGENTS.md) — non-negotiable invariants and rules for coding agents.
2. [`docs/MASTER_PRODUCT_IMPLEMENTATION_SPEC.md`](docs/MASTER_PRODUCT_IMPLEMENTATION_SPEC.md) — master source of truth.
3. [`project_backlog.csv`](project_backlog.csv) — executable work queue with dependencies and acceptance criteria.
4. [`contracts/semantic_metrics.yaml`](contracts/semantic_metrics.yaml) — exact finance definitions.
5. [`docs/UI_UX_SPEC.md`](docs/UI_UX_SPEC.md) and [`docs/BACKEND_QUERY_ENGINE_SPEC.md`](docs/BACKEND_QUERY_ENGINE_SPEC.md) — detailed implementation behavior.

## Validate the sample data

No third-party packages are required for fixture generation or fixture validation.

```bash
python scripts/validate_dataset.py
```

Expected summary:

```text
Accounts:       33
Vendors:        56
Vendor aliases: 189
Transactions:   969
Payouts:        919
Reconciliation: 957
Benchmarks:     22
Warnings:       0
PASS
```

Regenerate the deterministic fixture:

```bash
python scripts/generate_dataset.py
python scripts/validate_dataset.py
```

The seed is fixed. Regeneration should be byte-stable unless the generator or schema intentionally changes.

## Start PostgreSQL and Redis

```bash
cp .env.example .env
docker compose up -d postgres redis
python -m pip install -r requirements-tools.txt
python scripts/load_postgres.py --truncate
```

The dataset is intentionally small enough for a hackathon demo. `scripts/generate_scale_fixture.sql` describes a disposable scale-test path; do not claim 20M-record performance without actual measurements.

## Publish to the intended GitHub repository

The target repository name is `bluzeey/finance_ai_bot`. With GitHub CLI authenticated:

```bash
GITHUB_VISIBILITY=private ./scripts/publish_to_github.sh
```

See [`docs/GITHUB_PUBLISHING.md`](docs/GITHUB_PUBLISHING.md) for public/private options and Git-bundle import instructions.

## Suggested implementation order

1. Load data, views, indexes, and semantic definitions.
2. Hand-build a valid QueryPlan and return a verified AnswerReceipt without any model.
3. Implement allow-listed query compilers and result validators.
4. Expose the message, receipt, records, metadata, and export APIs through Django REST Framework.
5. Build the React Ask page and evidence panel.
6. Add the lightweight structured-output parser and entity/date resolvers.
7. Add multi-turn QueryState, clarification, corrections, and stale-response protection.
8. Add Explorer, Reconciliation, Data Health, Glossary, Evaluation, export, accessibility, and demo polish.

Full sequencing is in [`docs/AGENT_EXECUTION_PLAN.md`](docs/AGENT_EXECUTION_PLAN.md).

## Canonical demo

```text
User: How much did we spend on vendor payouts last month?
Assistant: Northstar Labs completed ₹1,00,00,874.04 in vendor payouts during August 2026.
```

The answer card must also show:

- `payout_date` from 2026-08-01 through 2026-08-31;
- only completed payouts;
- 55 matching source rows;
- the deterministic aggregation `SUM(gross_amount)`;
- validation outcomes and data-quality warnings;
- breakdown and source-record tabs;
- a receipt-linked CSV/XLSX export.

Then demonstrate:

1. “How does that compare with the month before?”
2. “Which of those are still unreconciled?”
3. “How much did we spend on Acme?” → clarification, no number.
4. “What will our cash balance be next quarter?” → unsupported, no number.
5. A record containing malicious-looking prompt text → treated as inert data.

## Repository map

```text
.
├── AGENTS.md
├── README.md
├── project_backlog.csv
├── backend/                  # Django/DRF target structure and implementation contract
├── frontend/                 # React/Vite target structure, component and page matrices
├── contracts/                # JSON Schema, OpenAPI, semantic metric definitions
├── data/                     # deterministic synthetic company data and manifest
├── database/                 # PostgreSQL schema, views, indexes, query references
├── docs/                     # full product, UX, backend, QA, security, evaluation, demo specs
├── evaluation/               # gold cases; application runtime must never read expected values
├── scripts/                  # generator, loader, validators, scale fixture
└── .github/                  # CI and agent-friendly issue/PR templates
```

## Submission checklist

- Working React chat interface and Django/DRF API
- Architecture diagram
- README and setup instructions
- Sample questions with captured answers
- Lightweight-model benchmark and rationale
- Demo deck covering problem, approach, grounding, efficiency, UX, and impact
- Clear synthetic-data disclosure
- No fabricated performance or accuracy claims

See [`docs/DEMO_AND_SUBMISSION_PLAN.md`](docs/DEMO_AND_SUBMISSION_PLAN.md) for the exact three-minute flow and deck outline.

## License

MIT. The included company and finance records are fully synthetic and are provided for development and evaluation only.
