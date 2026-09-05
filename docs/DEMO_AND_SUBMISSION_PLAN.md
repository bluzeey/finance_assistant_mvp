# Demo and Submission Plan

## Three-minute live demo

### 0:00–0:20 — problem

“Routine finance questions still require the right dashboard, terminology, or finance-ops help. Generic chat makes this faster but can invent a number. LedgerProof gives the answer and its proof.”

### 0:20–0:55 — grounded total

Ask: **How much did we spend on vendor payouts last month?**

Show:

- ₹1,00,00,874.04;
- August 1–31, 2026;
- completed payout status;
- 55 records;
- `SUM(gross_amount)`;
- receipt and one source row.

### 0:55–1:20 — multi-turn

Ask: **How does that compare with the month before?**

Point out that metric/filter context carries forward, exact July/August ranges are shown, and arithmetic is computed outside the model.

### 1:20–1:45 — reconciliation proof

Ask or open: **How much remains unreconciled on TXN-PART-001?**

Show that the assistant uses `unreconciled_amount`, not the full transaction amount.

### 1:45–2:15 — safe failure

Ask: **How much did we spend on Acme last month?**

Show two matching vendors, no number, and clear choices.

Then ask: **What will our cash balance be next quarter?**

Show an unsupported response: dataset lacks opening balance/forecast inputs.

### 2:15–2:35 — adversarial/data quality

Show the prompt-injection-like record text remains inert, or show duplicate/anomaly warning included without silently changing totals.

### 2:35–2:50 — lightweight model

Show evaluation scorecard: selected smallest passing model, parser accuracy, safety gates, latency, and cost per correct answer. Only show actual recorded values.

### 2:50–3:00 — close

“LedgerProof turns plain-language finance questions into deterministic, auditable answer receipts—self-service speed without giving up trust.”

## Backup demo

Capture fixture-backed response JSON and screenshots for every step. If the hosted model fails, deterministic benchmark phrasing should still exercise the full query/receipt path. Do not hardcode answers in UI/routes; use valid deterministic QueryPlans.

## Deck outline

1. Problem and stakes
2. Current workflow and user evidence
3. Product: question → answer receipt
4. Architecture and grounding boundary
5. Demo flow/screens
6. Lightweight model benchmark and why selected
7. Edge cases and safe failure
8. Business impact and plausible expansion
9. Limitations and next steps

## Submission artifacts

- public GitHub repository;
- working frontend/backend;
- architecture diagram;
- README/setup;
- sample questions and captured outputs;
- model benchmark/rationale;
- slide deck;
- synthetic-data disclosure;
- optional hosted demo/video.

## Judge-criteria mapping

| Criterion | Proof to show |
|---|---|
| Accuracy & grounding 30% | exact gold results, receipt, rows, checks, safe refusals |
| Model efficiency 20% | smallest passing structured parser, deterministic work outside model |
| NLU 15% | paraphrases, dates, aliases, filters, clarification, multi-turn corrections |
| Functionality 15% | chat, evidence, records, reconciliation, export, data health |
| UX 10% | fast answer, interpretation chips, responsive evidence, warnings, accessibility |
| Presentation 5% | fixed three-minute narrative and architecture diagram |
| Business impact 5% | repeated finance lookups moved to trustworthy self-service |

## Demo freeze checklist

- pin dataset manifest, model, prompt, and commit;
- run fixture/contract/backend/frontend/E2E tests;
- record actual benchmark and latency;
- ensure no secrets/debug logs;
- prewarm services but do not fake responses;
- verify mobile and presentation display size;
- export works and matches receipt;
- screenshots/video available;
- unsupported and ambiguity cases still show no number;
- known limitations slide is accurate.
