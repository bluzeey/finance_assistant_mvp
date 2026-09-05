## Tickets

- 

## What changed

- 

## Source-schema and contract impact

- [ ] Uses only `bank`, `account`, `transaction` for finance facts
- [ ] No schema/contract change
- [ ] Schema/contract change is versioned and documented in `docs/DECISION_LOG.md`

## Trust and privacy checks

- [ ] No model/browser/log/export receives a raw account number
- [ ] No model/browser/log/export receives a raw UTR
- [ ] Description content is redacted and rendered as text
- [ ] No unsupported vendor/payout/reconciliation/category/history claim
- [ ] Official values use decimal strings and server computation
- [ ] Date ranges are half-open and timezone-aware

## Tests run

- [ ] `python scripts/generate_dataset.py --check`
- [ ] `python scripts/validate_dataset.py`
- [ ] `python scripts/validate_repository.py`
- [ ] `python -m unittest discover -s tests -v`
- [ ] MySQL integration tests
- [ ] frontend unit/component tests
- [ ] Playwright P0 journeys
- [ ] accessibility/manual keyboard check

## User-visible evidence

Screenshot, receipt, benchmark diff or explanation:

## Remaining risks and follow-ups

- 
