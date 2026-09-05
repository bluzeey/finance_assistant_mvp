# Demo and Submission Plan

## 1. Demo thesis

> LedgerProof is not a chatbot that guesses at finance data. It is an auditable natural-language
> query layer: a small model produces a constrained interpretation, MySQL performs exact finance
> computation, validators verify the result, and every answer includes its source receipt.

The demo should prove three things: useful natural language, exact/verifiable answers, and deliberate
abstention when the supplied schema cannot support a request.

## 2. Three-minute demo script

### 0:00–0:20 — problem and trust promise

Open `/ask`. State that users currently navigate dashboards for routine questions, while a finance
chatbot that invents a number is worse than no chatbot. Point to the dataset cutoff and the three
source tables.

### 0:20–0:55 — grounded spend answer

Ask:

> How much did we spend last month?

Show:

- answer: `₹12,17,58,278.46`;
- 205 debit transactions;
- August 1 inclusive through September 1 exclusive;
- dataset cutoff September 3, 2026 Asia/Kolkata;
- “Debit spend” interpretation chip;
- source records and exact SQL family/parameters;
- required validation checks.

Say explicitly that the model did not calculate the total.

### 0:55–1:20 — multi-turn comparison

Ask:

> How does that compare with the month before?

Show inherited metric/filters and July comparison:

- August: `121758278.46`;
- July: `69995241.84`;
- absolute change: `51763036.62`;
- source rows available for both periods.

### 1:20–1:45 — exact reference lookup

Search the reference `HDFCH01078329532`, open the source transaction and point out:

- exact, case-sensitive plaintext reference semantics;
- account number masked;
- UTR protected;
- account-number-like value inside description redacted;
- record rendered as inert text.

Optionally use the planted duplicate reference to show that the assistant returns both rows with a
qualification rather than picking one.

### 1:45–2:10 — honest unsupported answer

Ask:

> Which transactions are still unreconciled?

Show an Unsupported answer with no number and the explanation that no reconciliation field exists.
Then ask:

> How much did we spend on vendor payouts last month?

Show that debit amount can be offered as an alternative, but the system does not relabel free-text
narrations as authoritative vendors or payouts.

### 2:10–2:30 — ambiguity guardrail

Ask:

> How much money moved recently?

Show concrete choices for credit, debit or net cash flow and a date range. No number appears until a
choice is made.

### 2:30–2:45 — export and data health

Open Data Health briefly, then export the first answer. Show query ID, dataset version, row count,
exact total and privacy-safe rows.

### 2:45–3:00 — model efficiency and close

Show the measured scorecard for the selected lightweight model and close with:

> The model understands the question; deterministic code owns the money; the receipt earns trust.

## 3. Demo preparation checklist

- database freshly loaded and canonical SQL total checked;
- model/provider credentials and deterministic fallback configured;
- first demo conversation cleared;
- browser zoom and 360px fallback checked;
- CSV/XLSX export pre-tested;
- no raw account/UTR appears in network responses or DOM;
- evaluator results are actual and labelled with exact model version;
- optional recorded backup demo available locally;
- app still communicates failures clearly when model/API is unavailable.

Do not hardcode answer values in the runtime path. Demo speed can be improved through warmed
connections and cached metadata, not by bypassing execution.

## 4. Slide deck outline

### Slide 1 — Finance answers should be fast and provable

Routine lookup pain, finance risk, one-line product promise.

### Slide 2 — The supplied data and its limits

ER diagram for bank → account → transaction, sample fields, sensitive fields and missing
vendor/reconciliation/category/history dimensions.

### Slide 3 — Product experience

Ask → AnswerReceipt → records/checks/export. Include one screenshot.

### Slide 4 — Grounded architecture

Small model → validated InterpretationDraft → deterministic resolver/QueryPlan → allow-listed MySQL
query → validators → receipt. Emphasise no model SQL/arithmetic.

### Slide 5 — Hallucination and privacy guardrails

Unsupported/clarify states, Decimal, half-open dates, read-only/bound SQL, masking, prompt-injection
handling and runtime/gold isolation.

### Slide 6 — Lightweight model evidence

Candidate models, exact-plan/refusal metrics, p95 latency and cost per correct plan. Explain why the
selected model is the smallest that clears the gates.

### Slide 7 — Business impact and next step

Faster routine answers, fewer finance-ops interruptions, audit-ready proof. Next source fields needed
for authoritative vendor payout/reconciliation workflows.

## 5. Evaluation-criteria mapping

| Criterion | What to show |
|---|---|
| Accuracy & grounding — 30% | exact gold totals, source records/hash, validation checks, unsupported demo |
| Model efficiency — 20% | small parser-only model, measured benchmark/cost, no model arithmetic |
| Natural-language understanding — 15% | paraphrase, date/filter resolution, multi-turn comparison, clarification |
| Functionality — 15% | Ask, evidence, Transactions, Accounts, export, Data Health |
| User experience — 10% | answer-first layout, interpretation chips, responsive evidence, clear non-answer states |
| Presentation — 5% | one thesis, clean three-minute narrative, readable architecture |
| Business impact — 5% | self-serve routine finance questions with auditable receipts |

## 6. Sample-question appendix

Supported:

- How much did we spend in August 2026?
- How much came in last month?
- What was net cash flow in August?
- Break down August debits by bank.
- Which program had the highest debit amount in July?
- Show credits above ₹5 lakh for HDFC accounts.
- Find reference HDFCH01078329532.
- Show transactions mentioning SELECTION MOBILE. *(qualified literal search)*
- What is the current available balance across all accounts?
- Which accounts currently have a negative balance?

Clarify:

- How much money moved recently?
- Show the biggest transactions. *(needs direction/date or explicit all-transactions choice)*
- Find ref 123. *(may need exact reference vs UTR clarification depending wording)*

Unsupported:

- Which transactions are unreconciled?
- How much did we pay each vendor?
- Which chart-of-accounts category had most spend?
- What was the account balance on August 31?
- Forecast next quarter’s cash balance.

## 7. README/submission evidence

Include:

- setup and validation commands;
- exact source schema and synthetic fixture disclosure;
- architecture Mermaid diagram;
- supported/unsupported question table;
- screenshots or captured receipts for sample questions;
- model benchmark output and methodology;
- limitations and future source-field requirements;
- no unmeasured 20M-row or production-security claims.
