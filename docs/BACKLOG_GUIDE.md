# Backlog Guide

`project_backlog.csv` contains **122** dependency-ordered implementation tickets. It is designed for parallel coding agents while protecting contracts and finance correctness.

## Columns

- `ticket_id`: stable reference for commits, tests and handoffs.
- `epic`, `phase`, `priority`: sequencing and judge-value context.
- `dependencies`: semicolon-separated tickets that must be complete.
- `acceptance_criteria`: observable definition of completion.
- `tests_required`: minimum evidence; not optional suggestions.
- `estimate_points`: relative complexity, not a time promise.
- `status`: todo/in_progress/blocked/review/done.
- `files_area`: likely ownership boundary.

## Parallel work rules

- Only one active owner modifies a given machine contract at a time.
- Data generator/schema/semantic changes require product/data review.
- Frontend may use contract fixtures before backend completion, but must remove mock-only paths before done.
- A ticket is not done when only happy path exists.
- Every bug fix references a ticket and adds a regression test.
