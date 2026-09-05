# UI/UX Specification

**Frontend:** React + TypeScript + Vite  
**Primary users:** finance managers, finance operations analysts, business users, reviewers  
**Core trust object:** AnswerReceipt  
**Default route:** `/ask`

The interface must make a correct answer fast to consume and easy to verify. It must also make
non-answers feel intentional rather than broken. A finance user should never have to infer whether
a number is official, approximate, model-generated, filtered, stale or unsupported.

---

## 1. Experience principles

1. **Answer first, evidence one click away.** The primary value is visible immediately; the exact
   interpretation and records are always available in the same object.
2. **No silent assumptions.** Date, metric, bank/program/account filters and description-search
   qualifications appear as chips under the answer.
3. **No fake completeness.** Missing vendor/reconciliation/history fields produce an explicit,
   useful unsupported state with no number.
4. **Operational confidence, not model confidence.** Badges are Verified, Qualified, Clarification,
   Unsupported, No data and Validation failed—not arbitrary percentages.
5. **Sensitive by default.** Account/UTR values are masked in every view/export; descriptions are
   redacted and rendered as text.
6. **Fast scanning.** Use restrained density, strong number hierarchy and tables for evidence.
7. **Same semantics everywhere.** Ask, Transactions, Accounts and export use one API contract and
   one date/filter language.
8. **Responsive without hiding trust.** On small screens, evidence moves to sheets; it is not removed.

---

## 2. Information architecture

### Primary routes

| Route | Nav label | Purpose |
|---|---|---|
| `/ask` | Ask | Conversation and answer receipts |
| `/transactions` | Transactions | Source-record exploration |
| `/accounts` | Accounts | Current account balances and bank/program views |
| `/data-health` | Data health | Dataset freshness and integrity warnings |
| `/glossary` | Glossary | Metric/source definitions and limitations |
| `/evaluation` | Evaluation | Model/parser benchmark results |

No Vendor or Reconciliation route exists in the source-aligned product.

### Desktop shell

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Top bar: product · dataset cutoff · connection/model status · help          │
├──────────────┬───────────────────────────────────────┬───────────────────────┤
│ Left nav     │ Main page/workspace                   │ Evidence panel        │
│ 240 px       │ fluid, min 640 px                     │ 360–440 px optional   │
│              │                                       │                       │
└──────────────┴───────────────────────────────────────┴───────────────────────┘
```

- Left navigation can collapse to icons at widths below 1,200 px.
- Evidence panel opens when the user selects “How calculated”, “Checks” or “Source rows”.
- The chat composer remains sticky at the bottom of the main workspace, not the viewport over the
  evidence panel.

### Tablet shell

- Compact navigation rail.
- Main workspace full width.
- Evidence opens as right-side drawer up to 70% width.
- Tables can horizontally scroll with the first identifying column sticky.

### Mobile shell

- Bottom navigation with Ask, Transactions, Accounts and More.
- Top bar shows abbreviated dataset cutoff and status.
- Evidence, filters, record detail and glossary open as full-screen sheets.
- Answer headline and status remain visible before any table.
- Composer respects virtual keyboard and safe-area insets.

---

## 3. Visual language

### Typography

- One readable sans-serif family already available in the project/system stack.
- Financial headline: 32–40 px desktop, 28 px mobile, tabular numerals.
- Body: 14–16 px.
- Table values: 13–14 px, tabular numerals, right-aligned amounts.
- Never shrink evidence below 12 px to fit more columns.

### Color semantics

Use design tokens rather than hardcoded component colors:

- neutral surface/background/border/text;
- verified success;
- qualified warning;
- clarification information;
- unsupported neutral-warning;
- validation/system error;
- debit and credit labels with text/icon, not color alone.

Do not use green/red as the only distinction because negative balance is a valid financial value,
not necessarily a system failure.

### Number formatting

- Display: `Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })`.
- Preserve exact decimal strings in state/API.
- Copy raw value offers `121758278.46`; copy formatted answer offers `₹12,17,58,278.46`.
- Show minus sign clearly for negative balance/net flow.
- Never abbreviate official headline values to “₹12.2Cr” without also showing the exact amount.
  Abbreviation may appear as secondary context.

### Icons

Icons supplement text. Every status/action has a visible label or accessible name. Avoid a magic
sparkle icon as the only sign that something is AI-generated.

---

## 4. Global components

### 4.1 Dataset status bar

Always visible at desktop top; compact on mobile.

Contents:

- `Data through 3 Sep 2026, 11:59 PM IST`
- `INR`
- source count `3 tables`
- connection health indicator
- optional “View data health” link

Rules:

- Never say “live” for the static fixture.
- If DB unavailable, turn the indicator into a clear error and disable new queries while preserving
  existing receipts in view.
- If dataset version changes mid-session, show a blocking reload banner.

### 4.2 Status badge

| State | Label | Meaning |
|---|---|---|
| `verified` | Verified | Directly represented source concept; required checks passed |
| `qualified` | Qualified | Result valid but material limitation/warning applies |
| `needs_clarification` | Clarification needed | Multiple interpretations; no number shown |
| `unsupported` | Not available in this data | Required source field absent/disabled |
| `no_data` | No matching records | Valid query returned zero rows |
| `validation_failed` | Could not verify | Required control failed; number suppressed |

Badge includes tooltip/popover with one-sentence definition.

### 4.3 Filter chip

Examples:

- `Debit transactions`
- `1 Aug–31 Aug 2026`
- `Bank: HDFC`
- `Program: 21`
- `Description contains: “SELECTION MOBILE” · qualified`

Chips are not editable inside an immutable receipt. “Refine” copies the plan into the current
composer/filter builder and creates a new query on submission.

### 4.4 Sensitive value

- Account: `••••••••••9069`, with bank name and optional short account ID.
- UTR: masked suffix only; copy action disabled for raw value.
- A “Sensitive value hidden” tooltip explains policy.
- Never reveal raw value on hover, click or inspectable data attribute.

### 4.5 Toasts

Use only for transient action outcomes: copied, export queued, export ready, retry started. Financial
answer status never exists only in a toast.

---

## 5. Ask page (`/ask`)

### 5.1 Empty/first-use state

Header:

> Ask a question about bank accounts and transactions

Subcopy:

> Answers are calculated from the supplied data and include the exact filters and source records.

Suggested prompts must all be supported:

- How much did we spend last month?
- How much money came in last month?
- Compare August debit spend with July.
- Break last month's debit spend down by bank.
- What is the current available balance across HDFC accounts?
- Find transaction reference HDFCH01078324740.

A “What can I ask?” disclosure includes unavailable examples:

- Vendor payout and reconciliation questions are not supported by this schema.
- Historical balances are not available.

Do not use an unsupported question as a primary suggestion unless explicitly demonstrating refusal.

### 5.2 Conversation timeline

Message sequence:

- user bubble;
- processing timeline;
- assistant AnswerReceipt card;
- optional follow-up suggestions.

Conversation entries use stable keys/message IDs. A response with an older context version is
ignored and logged; it never reorders the visible state.

### 5.3 Composer

- Multiline text area, 1–6 visible lines.
- Enter submits; Shift+Enter newline.
- Submit disabled for whitespace-only input or when current request is submitting.
- Stop/cancel hides streamed wording but server query may continue; canceled response must not
  update state unless the client later fetches it deliberately.
- Character counter appears after 1,600 of 2,000 characters.
- No raw account-number/UTR examples in placeholder.
- Optional slash shortcuts are deferred.

### 5.4 Processing state

Show stages without pretending certainty:

1. Interpreting question
2. Resolving dates and filters
3. Querying source data
4. Verifying result

Rules:

- Do not show a skeleton number such as `₹—` that resembles an answer.
- If model work fails but deterministic parsing can proceed for a simple exact command, label the
  fallback in technical details, not as a user-facing alarm.
- After a timeout, show a retry action with preserved question and trace ID.

### 5.5 Verified answer card

Order:

1. status badge + data cutoff;
2. exact headline value;
3. one-sentence summary;
4. interpretation chips;
5. optional comparison/breakdown;
6. action row: View records, How calculated, Export, Copy;
7. warning/check summary.

Example:

```text
[Verified] Data through 3 Sep 2026
₹12,17,58,278.46
Across all accessible accounts, 205 debit transactions were recorded in August 2026.
[Debit transactions] [1 Aug–31 Aug 2026] [All banks] [205 records]
```

Avoid “I found” and “I think.”

### 5.6 Qualified answer card

Visually similar to verified but the qualification appears before actions and cannot be dismissed.

Description-search example:

> ₹1,54,128.32 across 3 transactions whose **description contains “SELECTION MOBILE.”** This is a
> literal narration search, not verified vendor attribution.

Actions remain available. Export includes the qualification in metadata.

Duplicate-reference example:

> Reference `DUP-REF-2026-001` matched 2 records. Review both; the reference field is not unique.

### 5.7 Clarification card

No headline amount. Components:

- clear question;
- why clarification matters;
- 2–5 choice buttons when possible;
- “Type another range”/free text;
- cancel/start new question.

Example:

> What should “recently” mean?
>
> - Last 7 days in the dataset
> - This month to date
> - Last calendar month
> - Choose dates

Selecting an option sends its ID plus current context version, not untrusted UI-generated plan JSON.

For “How much did Acme cost?”:

> There is no vendor field. I can search transaction descriptions for an exact phrase, but that
> will not verify a canonical vendor. Which phrase should I search?

### 5.8 Unsupported card

No numeric value, zero, chart or empty table.

Structure:

- `Not available in this data` badge;
- repeat the requested concept;
- identify missing field/table;
- closest safe alternative;
- link to glossary/schema.

Example:

> Reconciliation status is not present in the supplied `bank`, `account` or `transaction` tables,
> so I cannot identify unreconciled rows. I can list transactions by date, bank, account, program,
> type or reference instead.

### 5.9 No-data card

Distinguish from zero:

> No transactions matched the exact filters.

Show filters and suggestions to expand range/remove a filter. Do not show `₹0.00` as the main answer
unless the metric semantics explicitly define zero for a non-empty source set.

### 5.10 Validation-failed card

- No amount.
- State that the system could not verify the result.
- Show failed check category in non-sensitive language.
- Offer retry and trace ID copy.
- Keep the original question/interpretation visible.

### 5.11 Follow-up suggestions

Generated from deterministic state, not unconstrained model creativity. Examples:

- Compare with previous month
- Break down by bank
- Show the largest debit
- View source transactions

Do not suggest vendor/reconciliation/category/history capabilities.

---

## 6. Evidence panel / answer receipt detail

Desktop tabs; mobile full-screen sections:

### Overview

- status, answer, query ID, created time;
- dataset version/cutoff/currency/timezone;
- exact interpretation.

### Calculation

- formula, e.g. `SUM(transaction_amount) WHERE transaction_type = debit`;
- date interval with inclusive/exclusive labels;
- component totals for net/comparison;
- decimal precision note;
- sanitized SQL template and parameter summary in advanced disclosure.

Never display raw sensitive parameters.

### Checks

List each check with pass/warn/fail and detail:

- plan schema;
- date bounds;
- exact decimal;
- source count/hash;
- duplicate/reference warnings;
- sensitive-field sanitization;
- narration qualification;
- coverage/freshness.

### Source records

- server-paginated table;
- receipt total independent of page size;
- sort fixed to deterministic source order unless a new query is created;
- row detail sheet;
- export buttons;
- source hash and query ID.

### Technical

- model/prompt version;
- timings;
- compiler template ID;
- plan hash;
- trace ID;
- sanitized QueryPlan JSON;
- no chain-of-thought.

---

## 7. Transaction table and row detail

### Columns

Default desktop columns:

1. timestamp (IST)
2. type
3. amount
4. bank
5. masked account
6. description
7. transaction reference
8. short transaction ID
9. actions

UTR is hidden in the default table. Row detail shows a masked UTR suffix with policy note.

### Table behavior

- Amount right-aligned with tabular numerals.
- Debit/credit shown with text label and directional icon.
- Description truncates visually but full sanitized text is available in row detail.
- NULL description shows `—`, not “null.”
- Long tokens wrap/break safely.
- Header sticks within scrolling container.
- Keyset pagination uses “Load more” or next/previous cursors; no misleading page number for unknown
  total unless server supplies it.
- Receipt source count remains visible.
- Selecting a row does not expose sensitive values in the URL.

### Row detail

- transaction ID with copy;
- exact timestamp and timezone;
- type/amount;
- bank/canonical name;
- account ID and masked account;
- entity/program;
- sanitized description;
- plaintext transaction reference;
- masked UTR;
- “Used in answer” relation and query ID;
- privacy note.

### Duplicate warning

Lookalike rows are not merged. Mark both with “Possible duplicate pattern” and explain that totals
include both because no source deduplication rule exists.

---

## 8. Transactions page (`/transactions`)

### Filter panel

- date range (start/end, timezone label);
- transaction type;
- bank multi-select from canonical list;
- account ID search/select with masked display;
- entity ID exact input;
- program ID multi-select;
- transaction reference exact input;
- amount min/max;
- description contains (advanced/qualified).

Rules:

- Do not include raw account-number or UTR filters.
- Exact-reference and description modes are visibly distinct.
- Invalid end-before-start prevents request and shows inline error.
- Filter URL serialization excludes sensitive input.
- Reset preserves dataset cutoff/timezone.
- “Ask about this view” creates a QueryPlan-compatible summary, not a list of browser rows.

### Summary strip

Server-computed:

- matching transactions;
- debit total;
- credit total;
- net movement;
- selected date range.

These values are not computed from the paginated page.

### Empty state

- show active filters;
- explain no rows matched;
- one-click remove most restrictive optional filter;
- do not display a system error graphic.

---

## 9. Accounts page (`/accounts`)

### Summary

- total current available balance;
- account count;
- bank count;
- negative-balance account count.

### Filters

- bank;
- program;
- entity ID;
- account ID.

No date filter because the field is current-only.

### Table/cards

- bank name/code;
- masked account number;
- short account ID;
- short entity ID;
- program ID;
- exact current balance;
- View transactions action.

Clicking “View transactions” navigates by `account_id`, never raw account number.

### Negative balances

Use a minus sign and accessible text. A negative balance can be highlighted but not conflated with
an application failure. Tooltip: “Current source value; may represent overdraft/credit arrangement.”

---

## 10. Data Health page (`/data-health`)

### Overall status

`Healthy`, `Qualified` or `Unhealthy` based on required checks. Known fixture warnings result in
Qualified, not failure.

### Sections

1. **Freshness and scope** — cutoff, first/latest transaction, timezone, currency, table counts.
2. **Relationships** — orphan bank/account/transaction checks.
3. **Completeness** — null descriptions/references/UTRs.
4. **Amounts** — zero values, decimal bounds, negative account balances.
5. **Identifiers** — duplicate references, malformed strict-UUID-like IDs.
6. **Duplicate risk** — lookalike signatures included in totals.
7. **Privacy** — narrations containing known account numbers; redaction check.
8. **Database readiness** — required indexes and session timezone.

Every warning includes “impact on answers” and “system handling.”

---

## 11. Glossary page (`/glossary`)

Searchable sections:

- debit spend;
- credit inflow;
- net cash flow;
- current available balance;
- transaction reference vs UTR;
- bank/account/entity/program;
- description search;
- date and comparison rules;
- status meanings;
- missing concepts.

Show the exact source field/formula. Provide copyable supported example questions. This page is the
primary destination from unsupported cards.

---

## 12. Evaluation page (`/evaluation`)

Audience is developer/judge, not everyday finance user.

### Header

- model name/size/provider;
- prompt version;
- dataset/benchmark version;
- run timestamp;
- measured badge.

### Scorecards

- structured-output validity;
- metric/intent accuracy;
- date accuracy;
- filter accuracy;
- numeric accuracy;
- clarification precision/recall;
- unsupported refusal;
- privacy pass;
- multi-turn accuracy;
- p50/p95 latency;
- tokens/cost.

### Failure table

Case ID, question, expected state, actual state, plan diff, answer diff, latency. Gold values are
available here only through evaluator APIs/modules, never normal assistant runtime.

### Comparison

Compare small models by accuracy frontier and cost/latency. Avoid implying the largest model is best.

---

## 13. Export UX

### Inline export

For small result sets:

- click Export;
- choose CSV or Excel;
- show sanitization note;
- server returns file or starts a job.

### Async export

For large sets:

- queued progress in action center;
- user may navigate away;
- completion toast plus persistent download action;
- expiry time shown;
- 410 state offers “Regenerate from receipt.”

### File contents

CSV:

- metadata comment/header rows only if consumer-safe; otherwise companion receipt JSON;
- deterministic columns/order;
- masked account/UTR;
- redacted description;
- exact decimal strings;
- query ID, cutoff and qualification.

XLSX:

- `Summary` sheet;
- `Records` sheet;
- `Checks` sheet;
- freeze header/filter;
- amount cells numeric with two-decimal format only after safe Decimal conversion;
- formula-injection prevention for text fields.

---

## 14. Responsive behavior matrix

| Element | Desktop | Tablet | Mobile |
|---|---|---|---|
| Nav | fixed rail | compact rail | bottom nav |
| Evidence | right panel | drawer | full-screen sheet |
| Filters | side panel | drawer | full-screen sheet |
| Breakdown chart | inline | inline | scroll/stack |
| Table | full | horizontal scroll | card/list + detail sheet |
| Composer | sticky central | sticky | safe-area sticky |
| Query chips | one/two lines | wrap | horizontal scroll + expand |

Do not hide status, cutoff, exact amount, qualification or source-count information at any width.

---

## 15. Accessibility

Required:

- WCAG 2.2 AA contrast;
- keyboard access for nav, tabs, dialogs, menus, chips and tables;
- visible focus;
- correct heading order;
- `aria-live="polite"` for processing/status completion, not every token;
- no color-only state distinction;
- screen-reader names for masked-value and copy actions;
- modal focus trap and return focus;
- table headers/scope;
- accessible error association;
- reduced-motion support;
- charts accompanied by tables/text;
- large click targets on mobile.

Status announcement example:

> “Verified answer ready. Debit spend in August 2026 is 121,758,278 rupees and 46 paise, based on 205 records.”

Avoid reading every evidence row automatically.

---

## 16. Loading, error and offline states

### Page loading

Skeleton structure is allowed for cards/tables, but never show a skeleton that resembles a finalized
financial amount.

### Partial failures

- If breakdown fails but primary receipt is verified, show the answer and a retriable breakdown error.
- If source rows fail, retain answer and explain evidence retrieval issue; do not relabel verified unless
  lineage validation itself failed.
- If receipt retrieval fails after refresh, show trace/query ID and retry.

### Network loss

- Preserve draft text locally in memory/session storage, not sensitive source rows.
- Disable submit and show reconnect.
- Existing receipts may remain visible with a “cached view” indicator.

### DB unavailable

- New answer queries disabled.
- Metadata status shows source unavailable.
- No model-only response is attempted.

---

## 17. Interaction and concurrency bugs to prevent

1. Double click/Enter must create one message via idempotency.
2. Old response must not replace a newer receipt/context.
3. Cancelled request must not silently mutate UI state later.
4. Selecting clarification twice must not apply duplicate patches.
5. Browser back/forward must restore filters without resubmitting mutations.
6. Refresh during export must recover job status from receipt/job ID.
7. Changing dataset version invalidates stale receipt actions, not the displayed historical receipt.
8. A new question during an open evidence panel must not overwrite panel contents until selected.
9. Sorting a source table must not imply the official answer was recalculated.
10. Mobile keyboard must not cover composer/submit.

---

## 18. Content/copy rules

Use evidence-based wording:

- “205 debit transactions totalled…”
- “The exact reference matched 2 records…”
- “The description contains…”
- “This data does not include reconciliation status…”

Avoid:

- “I think” / “probably” for deterministic results;
- “vendor” when only description text exists;
- “live balance” for a fixture snapshot;
- “all transactions are reconciled” from absence of a field;
- “₹0” for unsupported/no-data;
- “100% confident” without defining validation.

---

## 19. Component inventory

Core components are tracked in `frontend/component_inventory.csv`. At minimum:

- `AppShell`, `DatasetStatusBar`, `Navigation`
- `ConversationTimeline`, `UserMessage`, `AssistantReceiptCard`, `Composer`
- `ProcessingSteps`
- `StatusBadge`, `InterpretationChips`, `MoneyValue`
- `ClarificationCard`, `UnsupportedCard`, `NoDataCard`, `ValidationFailedCard`
- `EvidencePanel`, `CalculationView`, `ValidationChecks`, `TechnicalDetails`
- `TransactionTable`, `TransactionCard`, `TransactionDetailSheet`
- `AccountTable`, `BalanceSummary`
- `FilterPanel`, `DateRangeField`, `BankSelect`, `IdentifierField`
- `WarningBanner`, `SensitiveValue`, `CopyButton`
- `ExportMenu`, `ExportJobStatus`
- `DataHealthCheckList`, `EvaluationScorecard`

---

## 20. Page acceptance criteria

Detailed criteria live in `frontend/page_acceptance_matrix.csv`. Global acceptance requires:

- no raw account number/UTR in DOM/network fixtures;
- exact values come from AnswerReceipt, not browser aggregation;
- all semantic states have dedicated UI;
- source rows/export remain linked to immutable receipt;
- keyboard/mobile flows work;
- unsupported questions show no number;
- prompt-injection/XSS narration renders harmlessly;
- stale responses are ignored;
- loading/error/empty states are tested.
