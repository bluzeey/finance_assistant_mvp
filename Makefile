.PHONY: generate check-fixture validate test validate-repo mysql-up mysql-down load bundle all

generate:
	python scripts/generate_dataset.py

check-fixture:
	python scripts/generate_dataset.py --check

validate:
	python scripts/validate_dataset.py

test:
	python -m unittest discover -s tests -v

validate-repo:
	python scripts/validate_repository.py

mysql-up:
	docker compose up -d mysql redis

mysql-down:
	docker compose down

load:
	python scripts/load_mysql.py --truncate

bundle:
	python scripts/build_bundle.py

all: check-fixture validate test validate-repo
