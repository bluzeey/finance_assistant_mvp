PYTHON ?= python3

.PHONY: validate generate load-db repo-check backend-test frontend-test bundle

validate:
	$(PYTHON) scripts/validate_dataset.py
	$(PYTHON) scripts/validate_repository.py

generate:
	$(PYTHON) scripts/generate_dataset.py
	$(PYTHON) scripts/validate_dataset.py

load-db:
	$(PYTHON) scripts/load_postgres.py --truncate

repo-check:
	$(PYTHON) scripts/validate_repository.py

backend-test:
	cd backend && pytest

frontend-test:
	cd frontend && npm run typecheck && npm test

bundle:
	$(PYTHON) scripts/build_bundle.py
