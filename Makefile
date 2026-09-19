UV ?= uv
PORT ?= 8010
.PHONY: setup dev api worker web test lint typecheck migrate smoke build types benchmark
setup:
	$(UV) sync --frozen
	cd web && npm ci
migrate:
	$(UV) run alembic upgrade head
api:
	$(UV) run uvicorn prediction_terminal.api.app:app --host 127.0.0.1 --port $(PORT) --reload
worker:
	$(UV) run python -m prediction_terminal.workers.main
web:
	cd web && npm run dev
dev:
	$(UV) run python scripts/dev.py
test:
	$(UV) run pytest -q
	cd web && npm test
lint:
	$(UV) run ruff check src/prediction_terminal tests/unit tests/integration tests/replay scripts
	$(UV) run ruff format --check src/prediction_terminal tests/unit tests/integration tests/replay scripts
typecheck:
	$(UV) run mypy src/prediction_terminal
	cd web && npm run typecheck
types:
	$(UV) run python scripts/generate_types.py
	cd web && npm run generate
build:
	cd web && npm run build
smoke:
	$(UV) run python scripts/smoke.py --live
benchmark:
	$(UV) run python scripts/benchmark.py
