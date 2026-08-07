PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: setup data mocks spark warehouse dbt metrics run test verify dashboard clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"

data:
	$(BIN)/python scripts/download_olist.py

mocks:
	$(BIN)/python -m subscription_commerce.mock_sources

spark:
	$(BIN)/python -m subscription_commerce.spark_ingest

warehouse:
	$(BIN)/python -m subscription_commerce.warehouse

dbt:
	cd dbt && ../$(BIN)/dbt build --profiles-dir .

metrics:
	$(BIN)/python -m subscription_commerce.resume_metrics

run:
	$(BIN)/python -m subscription_commerce.cli run

test:
	$(BIN)/pytest -q

verify:
	$(BIN)/python scripts/verify_project.py

dashboard:
	$(BIN)/streamlit run dashboard/app.py

clean:
	rm -rf data/bronze/* warehouse/*.duckdb warehouse/*.wal dbt/target dbt/logs artifacts/*.json artifacts/*.csv artifacts/resume_bullets.md
