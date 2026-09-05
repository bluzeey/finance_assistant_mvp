# Frontend and UX Specification

## 1. Product experience goal

The interface must make a finance answer feel closer to a reproducible report than to a generic chatbot response. The primary experience is conversational, but every material number is accompanied by an inspectable receipt: interpretation, filters, calculation, validation checks, source rows, data freshness, and export.

The UX has three simultaneous jobs:

1. make routine finance questions fast;
2. make the result easy to verify;
3. make uncertainty and unsupported requests visible before they become false confidence.

A polished answer is not enough. The user must be able to answer: **What did the assistant think I asked? Which data did it use? What did it exclude? How did it compute the number? Can I reproduce it?**

## 2. Frontend stack and conventions

Recommended baseline:

- the stable React version selected and pinned by the team
- TypeScript in strict mode
- Vite
- React Router
- TanStack Query for server state and request cancellation
- Tailwind CSS or CSS modules with design tokens
- accessible headless components for dialogs, popovers, tabs, tooltips, menus, and sheets
- one charting library only; tables remain the source of truth
- Vitest + Testing Library
- Playwright for critical end-to-end flows
- MSW for deterministic frontend integration tests

Avoid a global client store unless a genuine cross-route client-only state requires one. Conversation state, QueryState, answers, and receipts are server state. The URL owns explorer filters. Local component state owns open panels, draft text, column visibility, and presentation preferences.

## 3. Information architecture

Primary routes:

| Route | Name | Purpose |
|---|---|---|
| `/ask` | Ask | Conversational finance workspace and default landing page |
| `/ask/:conversationId` | Conversation | Persistent conversation and answer receipts |
| `/explorer` | Data Explorer | Direct transaction and payout inspection |
| `/reconciliation` | Reconciliation | Open items, ageing, owners, and source detail |
| `/data-health` | Data Health | Freshness, coverage, duplicates, missing links, and integrity |
| `/glossary` | Definitions | Metric, field, account, date, and vendor semantics |
| `/evaluation` | Evaluation | Local/demo-only model scorecard and benchmark cases |
| `/about` | About the demo | Scope, architecture, model choice, and synthetic-data disclosure |

There is no production authentication in scope. Still build the layout so a future company/user switcher can fit in the navigation header without restructuring the app.

## 4. Application shell

### Desktop, 1280 px and wider

Use a persistent left navigation rail, a central workspace, and an optional right evidence panel.

```text
┌──────────────┬────────────────────────────────────┬───────────────────────────┐
│ Northstar    │ page title / dataset freshness     │ Evidence / Answer receipt │
│              ├────────────────────────────────────┤                           │
│ Ask          │                                    │ Receipt                   │
│ Explorer     │ main page                          │ Records                   │
│ Reconcile    │                                    │ Checks                    │
│ Data health  │                                    │ Query                     │
│ Glossary     │                                    │ Export                    │
│              │                                    │                           │
│ Demo data    │                                    │                           │
└──────────────┴────────────────────────────────────┴───────────────────────────┘
```

Recommended dimensions:

- navigation rail: 216–240 px
- central ask column: minimum 520 px
- evidence panel: 400–480 px; resizable only if implementation time permits
- max content width for non-chat pages: 1440 px

The evidence panel is route-preserving. Selecting an answer or record updates a query parameter such as `?evidence=<query-id>` so refresh and browser navigation work.

### Tablet, 768–1279 px

Collapse navigation to an icon rail or drawer. Evidence opens as a side sheet. Keep the chat composer anchored at the bottom of the visible workspace without hiding the last answer.

### Mobile, 360–767 px

Use one column. Navigation is a drawer. Evidence opens as a full-height bottom sheet with tabs. Tables switch to either:

- horizontally scrollable grid with the first identifier column sticky; or
- card rows for high-priority views.

Do not hide interpretation, confidence, or warning information on mobile; collapse it behind explicit disclosure controls.

## 5. Global header

Every page header includes:

- page title;
- company chip: “Northstar Labs”;
- data chip: “Data through 3 Sep 2026”;
- synthetic-data badge;
- optional command/search button;
- page-specific primary action.

Freshness chip rules:

- **Fresh**: max expected source date equals the dataset anchor or satisfies a configured SLA;
- **Delayed**: source date is behind anchor but within a defined tolerance;
- **Stale**: source date breaches tolerance;
- **Unknown**: freshness metadata unavailable.

Never show a green “live” indicator for this static dataset.

## 6. Ask page

### 6.1 Empty state

The empty state should explain the product in one sentence and offer six high-signal prompts. Avoid a marketing landing page inside the app.

Headline:

> Ask a finance question. Get the number and its proof.

Supporting text:

> Answers are calculated from Northstar Labs’ synthetic transaction, payout, and reconciliation data. The assistant cannot invent missing values.

Suggested prompts:

- How much did we spend on vendor payouts last month?
- How did that compare with the month before?
- Who were the top five vendors in August 2026?
- Which transactions are still unreconciled?
- Show unreconciled items older than 30 days.
- Is anything unusual in August payouts?

Below the prompts, display supported scope:

- spend and payouts;
- vendors, accounts, departments, and dates;
- reconciliation status;
- duplicate and anomaly callouts.

Also state what is not supported: forecasts, cash-balance projections, approvers, payroll, and write actions.

### 6.2 Conversation list

Desktop may show recent conversations in a collapsible section under navigation. Mobile uses a dedicated drawer. Each item shows title, last-updated time, and the last status icon. Actions: rename, delete, and copy link. Deletion requires confirmation because receipts are removed from the demo database.

A “New conversation” action creates a conversation immediately or lazily on first send. If creation is lazy, drafts must survive navigation only within the current tab.

### 6.3 Composer

Elements:

- multiline textarea, one to six visible lines;
- send button;
- stop/cancel action while parsing/querying;
- concise keyboard hint: Enter to send, Shift+Enter for a new line;
- examples button in empty or idle state;
- visible scope note on unsupported predictions.

Behavior:

- trim outer whitespace but preserve user text in the turn history;
- maximum 4,000 characters;
- disable send for empty text only;
- do not disable the whole interface while a request runs;
- prevent accidental duplicate submission using a local pending guard and an `Idempotency-Key`;
- generate a stable `client_turn_id` before sending;
- use an `AbortController` when the user presses Stop or navigates away;
- show a retry option on network failure with the same idempotency key;
- never insert a failed draft as a successful conversation turn.

### 6.4 Processing state

Show meaningful staged progress rather than simulated model prose:

1. Understanding the question
2. Resolving finance terms
3. Querying source data
4. Validating totals
5. Preparing the receipt

These labels are driven by backend events only if streaming is implemented. Without streaming, show a compact “Checking the data…” state and a progress skeleton. Do not invent granular progress percentages.

While a turn is pending, older answers remain interactive. The pending turn has a unique visual boundary. A late response must never overwrite a newer correction; see race-condition requirements below.

### 6.5 User message

Display exact user wording and timestamp. Offer copy and, optionally, “Use as new question.” Editing a previous message in place is not recommended for the hackathon because it complicates audit history. A correction should create a new turn.

### 6.6 Answer card anatomy

Each assistant response is an `AnswerCard` with these regions:

1. status badge;
2. direct answer sentence;
3. primary metric;
4. optional comparison or chart;
5. interpretation strip;
6. warnings and data-quality notes;
7. compact breakdown table;
8. actions: View proof, Show records, Export, Copy answer;
9. footer: source-row count, data-as-of date, query ID, processing time.

#### Status badges

| Status | Label | Meaning | Visual behavior |
|---|---|---|---|
| `verified` | Verified | Executed query and required validations passed | positive icon and text; never color alone |
| `qualified` | Qualified | Computed result with a material caveat | warning icon; caveat expanded by default |
| `needs_clarification` | Needs clarification | Multiple interpretations could materially change result | no metric; show choices |
| `not_answerable` | Not in the data | Required field/domain is absent | explain missing inputs and supported alternatives |
| `no_matching_rows` | No matching records | Query was valid and relevant coverage is sufficient, but zero rows matched | explicit verified-zero language |
| `error` | Couldn’t verify | Technical or validation failure | no financial number; retry and trace ID |

A number may never appear with `error` or unresolved `needs_clarification` status.

#### Direct answer

Use one or two short sentences. For example:

> Northstar Labs completed **₹1,00,00,874.04** in vendor payouts during August 2026.

The frontend formats a canonical decimal string. The backend remains the authority for raw value and currency. Use Indian digit grouping only in display; exports and APIs use plain decimal numbers or strings.

#### Interpretation strip

Always visible immediately below the metric. It includes editable-looking but server-owned chips:

- Metric: Completed vendor payouts
- Period: 1–31 Aug 2026
- Date field: Payout date
- Status: Completed
- Vendor: All vendors
- Currency: INR

Clicking a chip opens details and an option such as “Change period.” Any change creates a new query turn; it does not mutate the receipt being viewed. Chips reflect canonical QueryState returned by the server, never local guesses.

#### Breakdown

For aggregates, default to a vendor or time breakdown only when it helps verification and does not imply an unrequested dimension. The answer receipt can return a recommended breakdown. The table total must equal the displayed primary metric when it is intended as a full breakdown. If it shows only top rows, label it “Top 5 of 42 vendors” and show a separate total.

Charts are secondary. Every chart must have an adjacent or accessible table and use the same response data. A chart may not independently reaggregate raw rows in the browser.

#### Footer

Example:

> 53 source records · Data through 3 Sep 2026 · Query `…1111` · 428 ms

The query ID opens the receipt. Do not expose raw database SQL in the main card.

### 6.7 Clarification card

A clarification card contains:

- the exact ambiguous phrase;
- why it matters;
- mutually exclusive choices;
- optional “None of these” or custom date input;
- preserved non-ambiguous context.

Example:

> “Acme” matches two vendors. Which one did you mean?
>
> **Acme Cloud Services** — Cloud infrastructure (`V0001`)
>
> **Acme Office Supplies** — Office supplies (`V0002`)

After the user selects a choice, send a new turn such as a structured clarification response. Do not silently edit the original user message. The resolved answer should state that the vendor was clarified and retain the original period and metric.

For multiple ambiguities, request the minimum information needed. A single card may ask both vendor and date only when doing so is understandable; otherwise resolve the most blocking ambiguity first. Avoid a long form that feels like a report builder.

### 6.8 Unsupported request card

Explain:

1. what the user asked for;
2. which field or dataset is missing;
3. why a number cannot be calculated safely;
4. one supported adjacent action.

Example:

> I can’t calculate next quarter’s cash balance from this dataset. It has vendor transactions and payouts, but no opening cash balance or cash-flow forecast. I can show completed or scheduled vendor payouts instead.

Do not apologize excessively, speculate, or fill in assumptions.

### 6.9 Verified-zero card

A zero result is distinct from not-answerable:

> No unreconciled travel transactions matched 24–30 August 2026. I checked posted travel, meals, and local-transport transactions against open reconciliation statuses.

Show source-row count as zero, query definition, and coverage check. If coverage is incomplete, use `qualified`, not verified zero.

### 6.10 Error card

Error categories and copy:

- network: “The request didn’t reach the finance service.”
- timeout: “The query exceeded the safe execution limit.”
- parser unavailable: “I couldn’t interpret this question reliably.”
- validation failure: “The computed result failed a consistency check, so no number was returned.”
- stale context conflict: “This conversation changed while the request was running. Review the latest filters and try again.”

Every error has a trace ID, retry when safe, and “Start a new question.” Never render a cached or partial number after a validation failure.

## 7. Evidence panel / Answer receipt

The evidence panel opens from “View proof.” Tabs:

### 7.1 Receipt

Display:

- direct answer and status;
- interpreted metric definition;
- exact half-open date interval plus human period;
- filters and exclusions;
- grouping and sort;
- human-readable computation steps;
- source row count;
- data version and data-as-of date;
- query ID and immutable timestamp;
- context inherited or changed from the prior turn.

Avoid showing chain-of-thought. “How calculated” is a deterministic execution summary, not hidden model reasoning.

### 7.2 Records

Show source rows captured by the immutable query lineage. Requirements:

- cursor pagination;
- sticky header;
- selectable columns;
- right-aligned numbers;
- exact decimal display;
- raw IDs available;
- source system and reference visible;
- date-field used is visually marked;
- link to row detail;
- “Download these records” uses the same query ID.

Do not use offset pagination for large datasets. Keep sort deterministic with a unique final key.

### 7.3 Checks

List validation checks with pass/warn/fail states. Examples:

- date range valid;
- entity uniquely resolved;
- mandatory status applied;
- breakdown ties to total;
- no join inflation detected;
- source rows all use INR;
- reconciliation components tie to transaction absolute amount;
- data coverage acceptable;
- duplicate candidates detected;
- result uses decimal arithmetic.

A failed required check means no financial answer. Warnings downgrade to `qualified` based on policy.

### 7.4 Query

Show the canonical QueryPlan and a plain-language execution plan. Raw SQL is hidden by default and available only in developer mode. If shown, it must be read-only and parameterised, with parameters listed separately. Never show secrets or connection details.

### 7.5 Export

Actions:

- Download source records as CSV
- Download source records as Excel
- Copy answer summary
- Copy receipt JSON in developer mode

The export panel shows row count, query ID, generated time, and source-record hash. Export must be generated from the immutable query result/plan on the backend, not from currently visible paginated rows.

## 8. Multi-turn conversation behavior

The server stores a canonical QueryState. The frontend displays it as context chips above the composer after the first completed turn.

Possible state fields:

- metric;
- date range and field;
- vendor IDs;
- account/category;
- department/cost center/project;
- statuses;
- grouping;
- comparison period;
- selected source result set where appropriate.

### Inheritance rules

- “How does that compare with the month before?” inherits metric, filters, grouping, and current period, then derives a previous period.
- “Which vendor drove most of that increase?” inherits both comparison periods and computes per-vendor contribution. It may not invent causal explanations.
- “Which of those are unreconciled?” intersects the previous source set only when `those` has a stable set reference and compatible records. Otherwise ask what `those` refers to.
- “Show the records” changes intent to drilldown and keeps all filters.
- “No, use the last 30 days” replaces the date range and clears comparison periods that no longer apply.
- “Only AWS” replaces vendor filters with `V0003`.
- “Also include Azure” adds `V0005` only when the intent is clearly additive.
- “Start over” clears server QueryState. Prior receipts remain immutable in history.

### Context visibility

After each turn, visually show what changed:

> Changed period from **August 2026** to **last 30 days**. Kept metric: **posted vendor spend**.

The frontend sends `expected_context_version`. The backend rejects a request with HTTP 409 when the context version is stale. This prevents a slow prior request from overwriting a later correction.

## 9. Data Explorer page

Purpose: let judges and users inspect the source data without leaving the app, and demonstrate that answers are not generated from hidden mock objects.

### 9.1 Tabs

- Transactions
- Vendor payouts
- Vendors
- Chart of accounts

The URL captures tab, filters, sort, and cursor where possible. Example:

```text
/explorer?tab=payouts&status=completed&vendor=V0003&from=2026-08-01&to=2026-09-01
```

### 9.2 Filters

Transactions:

- posting date range;
- vendor;
- account;
- department;
- status;
- transaction type;
- source system;
- text search over reference and description.

Payouts:

- payout date range;
- vendor;
- payout status;
- payment method;
- amount range;
- bank or invoice reference search.

Filter controls display selected canonical IDs and human labels. Vendor search warns when a typed alias is ambiguous.

### 9.3 Table behavior

- server-side filter and sort;
- cursor pagination;
- a deterministic final ID sort;
- no browser-side totals over partial pages;
- visible count and loaded-row count;
- row detail drawer;
- copy ID/reference;
- export current filter through a backend query ID;
- column chooser persisted locally;
- skeleton rows during filter changes;
- cancel prior requests when filters change rapidly.

### 9.4 Row detail

Transaction detail includes dates, vendor, account, dimensions, signed amount, status, description, reference, source system, ingestion data, reversal link, related payout, and reconciliation. Untrusted description text is displayed as text only. It must never be rendered as HTML.

Payout detail includes invoice link, status history as available, gross/fee/net, payment method, bank reference, failure reason, and duplicate warnings.

## 10. Reconciliation page

### 10.1 Header metrics

- open item count;
- total unreconciled amount;
- partially reconciled amount;
- disputed amount;
- items older than 30 days;
- reconciliation coverage percentage.

Every card links to the corresponding filtered table. Values come from backend aggregates, not client-side table pages.

### 10.2 Ageing buckets

Buckets based on transaction posting date and `data_as_of`:

- 0–7 days
- 8–30 days
- 31–60 days
- 61–90 days
- 90+ days

Define boundaries in backend code and test exact dates. Do not use the user’s browser date.

### 10.3 Open-item table

Columns:

- transaction ID;
- posting date and age;
- vendor;
- account;
- status;
- transaction amount;
- reconciled amount;
- open amount;
- reason;
- owner;
- last reviewed.

Partially reconciled rows visually distinguish full amount from open amount. The primary sortable amount is open amount.

### 10.4 Coverage warning

The fixture includes one posted transaction without a reconciliation row. Show a warning card:

> Reconciliation coverage is incomplete: 1 posted transaction has no reconciliation-status record.

Answers requiring comprehensive reconciliation data should be `qualified` when the missing row could affect the request. The card links to the missing transaction.

## 11. Data Health page

This page is a product differentiator. It makes trust conditions inspectable before a user asks a question.

Sections:

### 11.1 Overall status

- Healthy, Warning, or Error;
- data version;
- data-as-of date;
- last source dates;
- last validation run;
- row counts by table.

### 11.2 Freshness

For each table:

- maximum business date;
- maximum ingestion/review timestamp;
- expected cutoff;
- status and explanation.

### 11.3 Coverage and referential integrity

Checks:

- transactions with valid vendor;
- transactions with valid account;
- payouts with valid invoice transaction;
- reconciliation rows with valid transactions;
- posted transactions with reconciliation status;
- required-field completeness;
- single-currency invariant.

### 11.4 Financial invariants

- completed payout `net_cash_outflow = gross_amount + fee_amount`;
- non-completed payout net cash outflow is zero;
- partially reconciled components sum to transaction absolute amount;
- reconciled rows have zero open amount;
- reversals have valid links and negative signed amounts;
- no future posting or payout date beyond data anchor.

### 11.5 Quality signals

- possible duplicate payout groups;
- ambiguous vendor aliases;
- missing reconciliation records;
- unusually large payouts;
- null or invalid date fields;
- source records containing spreadsheet-formula prefixes for export safety;
- hostile-looking text treated as data.

Each check has severity, affected count, sample IDs, definition, last run, and a link to Explorer.

## 12. Glossary page

Searchable definitions for:

- supported metrics;
- dates and relative periods;
- payout/transaction/reconciliation statuses;
- accounts and account types;
- vendor aliases;
- dimensions;
- unsupported fields.

Metric definition page includes source table, formula, mandatory filters, date field, exclusions, aliases, example questions, and known ambiguity. This content should come from the semantic contract exposed by `/api/v1/meta` or `/api/v1/glossary`, not duplicated hardcoded strings across components.

## 13. Evaluation page

This is demo/development only and must be disabled by configuration in production-like environments.

### 13.1 Scorecards

Show per model/prompt version:

- QueryPlan exact or field-level accuracy;
- numerical answer accuracy;
- status/refusal accuracy;
- clarification precision and recall;
- source-record completeness;
- multi-turn accuracy;
- median and p95 latency;
- tokens and estimated cost per correct answer.

Do not optimise only aggregate accuracy. A model that answers unsupported questions confidently should be penalised heavily.

### 13.2 Case list

Columns:

- question ID;
- category;
- question;
- expected status;
- actual status;
- plan diff;
- value diff;
- source-lineage diff;
- latency;
- result.

Gold answers are loaded by the evaluator process, never by the runtime answer service.

### 13.3 Model choice note

Provide a concise, generated report:

> We selected the smallest tested model that cleared all financial-answer and refusal thresholds. It only creates a constrained QueryPlan; PostgreSQL performs all financial computation.

Include benchmark version, prompt version, number of cases, and known failures.

## 14. About page

A judge-friendly page with:

- problem statement;
- one-sentence product thesis;
- architecture diagram;
- model responsibility boundary;
- supported and unsupported scope;
- synthetic-data notice;
- data and model evaluation snapshot;
- links to README and sample questions.

Do not make this page the primary demo. It is evidence after the workflow.

## 15. Visual design system

### Principles

- calm, dense enough for finance, not spreadsheet-like everywhere;
- hierarchy through spacing, typography, and alignment;
- status communicated with icon + text + color;
- numbers use tabular numerals;
- source IDs and query IDs use monospace;
- warnings are visible without looking catastrophic;
- no decorative AI gradients, animated sparkles, or anthropomorphic bot avatar.

### Suggested tokens

Use semantic tokens rather than hardcoded values:

- `surface/default`, `surface/subtle`, `surface/elevated`
- `text/primary`, `text/secondary`, `text/muted`, `text/inverse`
- `border/default`, `border/strong`
- `status/verified`, `status/qualified`, `status/blocked`, `status/error`
- `focus/ring`
- `data/positive`, `data/negative`, `data/neutral`

Light mode is sufficient for the hackathon. Do not add dark mode unless all tables, charts, focus states, and status colors are validated.

### Typography

- body: 14–16 px;
- table: 13–14 px;
- primary metric: 28–36 px desktop, 24–30 px mobile;
- tabular numerals for money/count columns;
- line height at least 1.4 for body text.

### Money display

- raw API value: decimal string, e.g. `10000874.04`;
- UI: `₹1,00,00,874.04`;
- negative: `−₹3,80,000.00`, not parentheses unless the whole app consistently uses accounting notation;
- zero: `₹0.00`;
- never abbreviate the primary answer to `₹1.0Cr` without also showing the exact value;
- tooltips may provide lakh/crore interpretation, but exact values remain visible.

## 16. Accessibility

Target WCAG 2.2 AA for the demo.

- all functionality keyboard-accessible;
- visible focus ring;
- logical heading structure;
- `aria-live="polite"` for completed answers and `assertive` only for blocking errors;
- status icon plus text, never color alone;
- table headers use proper semantics;
- dialogs and sheets trap focus and restore it on close;
- charts have text summaries and tables;
- skeletons are hidden from screen readers or labelled as loading;
- no auto-focus that unexpectedly moves the user after an answer arrives;
- minimum 44×44 px touch targets where practical;
- reduced-motion preference respected;
- contrast checked for statuses, muted text, and focus.

## 17. Frontend module structure

```text
frontend/src/
  app/
    router.tsx
    query-client.ts
    providers.tsx
    error-boundary.tsx
  api/
    client.ts
    generated-types.ts
    conversations.ts
    explorer.ts
    health.ts
  components/
    layout/
    answer/
      AnswerCard.tsx
      StatusBadge.tsx
      PrimaryMetric.tsx
      InterpretationChips.tsx
      BreakdownTable.tsx
      WarningList.tsx
      AnswerActions.tsx
    evidence/
      EvidencePanel.tsx
      ReceiptTab.tsx
      RecordsTab.tsx
      ChecksTab.tsx
      QueryTab.tsx
      ExportTab.tsx
    chat/
      Composer.tsx
      ConversationTurn.tsx
      ClarificationCard.tsx
      UnsupportedCard.tsx
      PendingTurn.tsx
    data-grid/
    filters/
    feedback/
  features/
    ask/
    explorer/
    reconciliation/
    data-health/
    glossary/
    evaluation/
  hooks/
  lib/
    money.ts
    dates.ts
    csv-safety.ts
    query-keys.ts
  styles/
  test/
```

Generate API types from OpenAPI when possible. Never maintain two handwritten definitions of AnswerReceipt.

## 18. Server-state and race handling

TanStack Query key examples:

```text
['meta']
['conversation', conversationId]
['source-records', queryId, cursor]
['transactions', canonicalFilterHash, cursor]
['data-health', datasetVersion]
```

Rules:

- invalidate conversation detail after a successful turn;
- append an optimistic user bubble only, not an optimistic financial answer;
- associate each pending turn with `client_turn_id`;
- when a response returns, insert it only if the matching turn remains pending;
- use `expected_context_version` to prevent stale mutations;
- cancel superseded explorer requests;
- do not let an older response change current evidence selection unless the user explicitly selects it;
- preserve immutable past receipts even after context correction;
- on retry, reuse idempotency key unless user edits the message.

## 19. Loading, empty, and degraded states

Every page must specify all states:

- initial loading;
- background refresh;
- empty dataset;
- valid zero result;
- partial data;
- permission/access error if auth is later added;
- network error;
- backend validation error;
- no JavaScript fallback is not required for the hackathon.

Do not replace an already-rendered page with a full-screen spinner during background refresh. Keep stale content with a small refreshing indicator.

## 20. Export UX and safety

Export requests use the query ID. The frontend may not create the official CSV from table rows because pagination, formatting, or hidden rows can create mismatches.

CSV safety requirements:

- prefix text cells beginning with `=`, `+`, `-`, `@`, tab, or carriage return when they are not typed numeric fields;
- preserve IDs as text;
- use UTF-8 with a clear header row;
- include a metadata preamble only if it does not break common import tools; otherwise ship a companion receipt sheet/file;
- filename includes metric, date range, and short query ID;
- exported totals are covered by a parity test against the answer receipt;
- Excel export has a `Receipt` sheet and a `Records` sheet.

## 21. Analytics and observability events

No sensitive raw question text in analytics by default. Events:

- `question_submitted` with length bucket and route;
- `answer_completed` with status, metric, latency bucket, model/prompt version;
- `clarification_shown` and `clarification_selected` with field type;
- `evidence_opened` and tab;
- `records_exported` with format and row-count bucket;
- `answer_error` with category and trace ID;
- `context_reset`;
- `suggested_prompt_used`.

Store raw question and receipt only in the application audit database for the demo, with an explicit retention note.

## 22. Critical frontend acceptance tests

1. Double-clicking Send creates one turn.
2. Retrying a timed-out request with the same idempotency key creates one turn.
3. A slow first request cannot overwrite a faster correction.
4. “Start over” clears chips and server QueryState; a subsequent pronoun/period-only question asks for context.
5. Ambiguous Acme renders both choices and no amount.
6. Selecting Acme Cloud preserves the original month and metric.
7. A verified zero uses the zero state, not unsupported state.
8. A validation failure renders no number.
9. Chart totals equal table/receipt totals.
10. Export row count and source hash equal receipt lineage.
11. Mobile evidence sheet can be opened, navigated by keyboard, and closed with focus restored.
12. Long vendor names and large INR values do not overflow at 360 px.
13. Hostile transaction text displays literally and never executes as HTML.
14. Negative credits/reversals use a clear sign and accessible label.
15. Browser Back restores explorer filters and evidence selection.
16. Screen reader announces a completed answer once, without moving focus.
17. Empty conversation suggestions are reachable by keyboard.
18. Query ID, source count, and data-as-of are present on every numeric answer.
19. A warning status is not identifiable by color alone.
20. Evaluation/gold routes are absent when demo evaluator mode is disabled.

## 23. Definition of done for the frontend

A page is not complete merely because the happy path looks correct. It is complete when:

- typed API contract is integrated;
- loading, zero, empty, qualified, blocked, and error states exist;
- desktop and 360 px layouts work;
- keyboard and focus flow are tested;
- no unhandled console errors occur;
- official answer/export values are never recomputed in the browser;
- race and duplicate-submit tests pass;
- visual regression snapshots cover answer statuses;
- copy is consistent with finance semantics;
- the page has at least one Playwright happy path and relevant failure path.
