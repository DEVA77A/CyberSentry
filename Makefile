.PHONY: up down logs ps db-init seed verify test lint clean reset data

COMPOSE = docker compose -p cybersentry

up:                ## start the full stack
	$(COMPOSE) up -d
	@echo "stack up — run 'make ps' to check health"

down:              ## stop containers, keep volumes
	$(COMPOSE) down

reset:             ## stop and wipe all volumes
	$(COMPOSE) down -v

ps:                ## container health
	$(COMPOSE) ps

logs:              ## tail all logs
	$(COMPOSE) logs -f --tail=100

db-init:           ## re-apply schema (idempotent)
	$(COMPOSE) exec -T postgres psql -U sentry -d cybersentry -f /docker-entrypoint-initdb.d/01_init.sql

seed:              ## load reference + demo data
	python scripts/seed_db.py

data:              ## download raw datasets
	python scripts/download_datasets.py

verify:            ## M1 acceptance checks
	python scripts/verify_m1.py

test:              ## unit tests for the domain library
	pytest tests/ -v -p no:cacheprovider

lint:              ## format and lint
	black . && flake8 .

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} +

# ---- M2 targets (append to the M1 Makefile) ----
# '>' replaces TAB as the recipe prefix from here down, so this block survives copy-paste.
.RECIPEPREFIX = >
ifeq ($(OS),Windows_NT)
SHELL ?= C:/PROGRA~1/Git/bin/bash.exe
endif
-include .env
export
POSTGRES_USER ?= $(or $(DB_USER),sentry)
POSTGRES_PASSWORD ?= $(or $(DB_PASS),sentry_dev_2026)
POSTGRES_DB ?= $(or $(DB_NAME),cybersentry)
PYTHON ?= $(if $(wildcard .venv/Scripts/python.exe),.venv/Scripts/python.exe,$(if $(wildcard .venv/bin/python),.venv/bin/python,python))
PY := PYTHONPATH=ml/src $(PYTHON)
PKG := cybersentry
PSQL := docker compose exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

mlflow-up:
> $(PSQL) -tc "SELECT 1 FROM pg_database WHERE datname='mlflow'" | grep -q 1 \
> || $(PSQL) -c "CREATE DATABASE mlflow"
> docker compose exec -T minio sh -c \
> "mc alias set l http://localhost:9000 $$MINIO_ROOT_USER $$MINIO_ROOT_PASSWORD \
> && mc mb -p l/mlflow-artifacts" || true
> docker compose -f docker-compose.yml -f docker-compose.mlflow.yml up -d mlflow

migrate-m2:
> $(PSQL) < db/migrations/002_m2_predictions.sql

extract:
> $(PY) -m $(PKG).split

test-m2:
> $(PY) -m pytest -q ml/tests/test_m2_leakage.py

baseline:
> $(PY) -m $(PKG).baseline

train:
> $(PY) -m $(PKG).train

hpo:
> $(PY) -m $(PKG).hpo --trials 30

evaluate:
> $(PY) -m $(PKG).evaluate

promote:
> $(PY) -m $(PKG).promote

writeback:
> $(PY) -m $(PKG).writeback

verify-m2:
> $(PY) scripts/verify_m2.py

m2: extract test-m2 train evaluate promote writeback verify-m2

.PHONY: mlflow-up migrate-m2 extract test-m2 baseline train hpo evaluate promote writeback verify-m2 m2
