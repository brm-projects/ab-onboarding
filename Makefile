.ONESHELL:
SHELL := /bin/bash

PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: venv deps up down reset api simulate dbt test analyze analyze-bayes fmt

venv:
	python -m venv .venv

deps: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install pandas statsmodels SQLAlchemy numpy

up:
	docker compose up -d

down:
	docker compose down

reset: down
	docker compose down -v
	docker compose up -d

api:
	uvicorn api.main:app --reload --port 8000

simulate:
	$(PY) sims/simulate_traffic.py

dbt:
	dbt run --project-dir dbt

test:
	dbt test --project-dir dbt

analyze:
	DBT_MART_SCHEMA=analytics $(PY) -u sims/analyze_experiment.py

analyze-bayes:
	DBT_MART_SCHEMA=analytics $(PY) -u sims/analyze_bayes.py

fmt:
	$(PIP) install ruff
	.venv/bin/ruff check --fix .
