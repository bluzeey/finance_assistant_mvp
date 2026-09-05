.PHONY: validate generate services-up services-down load-db repo-check bundle

validate:
	python scripts/validate_dataset.py
	python scripts/validate_repository.py

generate:
	python scripts/generate_dataset.py
	python scripts/validate_dataset.py

services-up:
	docker compose up -d postgres redis

services-down:
	docker compose down

load-db:
	python scripts/load_postgres.py --truncate

repo-check:
	python scripts/validate_repository.py

bundle:
	python scripts/build_bundle.py
