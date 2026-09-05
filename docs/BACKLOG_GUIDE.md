# Backlog Guide

`project_backlog.csv` is the execution queue for humans and coding agents. It is ordered by ticket
ID but must be scheduled by dependency and priority rather than by row order alone.

## Columns

| Column | Meaning |
|---|---|
| `ticket_id` | Stable identifier used in commits, PRs and handoffs |
| `epic` | Product/engineering workstream |
| `title` | Short deliverable |
| `description` | Scope boundary and expected implementation |
| `priority` | P0 blocks a trustworthy demo; P1 improves score; P2 is optional |
| `phase` | Recommended delivery phase |
| `owner_role` | Best primary owner; not an exclusive assignment |
| `dependencies` | Semicolon-separated ticket IDs that must land first |
| `acceptance_criteria` | Observable completion condition |
| `tests_required` | Minimum evidence required before `done` |
| `estimate_points` | Relative effort, not elapsed time |
| `status` | `todo`, `doing`, `blocked`, `review`, or `done` |
| `files_area` | Expected repository ownership area |

## Agent protocol

1. Read `AGENTS.md`, the source schema, relevant contracts and the selected ticket.
2. Confirm every dependency is merged or explicitly mocked at the contract boundary.
3. Implement the smallest vertical change that satisfies the acceptance criteria.
4. Add the named tests, including a failure or privacy case where relevant.
5. Run root validators and applicable backend/frontend tests.
6. Record exact commands, result values and remaining risks in the PR template.
7. Do not edit gold outputs to make a failing implementation pass; correct the implementation or
   intentionally version the dataset and regenerate all derived files.

## Contract ownership

Only one active change should modify a foundational contract at a time:

- source schema/data dictionary;
- semantic metrics;
- QueryPlan/AnswerReceipt JSON schemas;
- OpenAPI;
- dataset generator/gold benchmarks.

Contract changes require a version bump, fixture regeneration, downstream test updates and a
Decision Log entry.

## Definition of done

A ticket is `done` only when:

- acceptance criteria are directly evidenced;
- tests pass locally and in CI;
- no raw account number or UTR is exposed;
- no unsupported vendor, payout, reconciliation, category or historical-balance claim appears;
- exact decimal and half-open date semantics remain intact;
- documentation is updated where behavior changed.
