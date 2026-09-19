# Parallax — Prediction Terminal

A local, read-only research terminal for comparing Kalshi and Polymarket contracts, inspecting settlement equivalence and modeling depth-aware cross-venue positions. Python owns matching and pricing; React/TypeScript owns the terminal workspace.

## Start in this workspace

Dependencies are already installed. The built app serves on **http://127.0.0.1:8010** when the API is running. Click **Import October 2026 Fed example**, or paste either venue event URL in search. The default mode uses SQLite locally; PostgreSQL configuration is supplied below.

```bash
# From htn/
.venv/bin/uv run alembic upgrade head
.venv/bin/uv run uvicorn prediction_terminal.api.app:app --host 127.0.0.1 --port 8010
# A second terminal:
.venv/bin/uv run python -m prediction_terminal.workers.main
```

## Fresh setup

Prerequisites: Python 3.12+, Node 22+, npm, and uv. `uv.lock` and `web/package-lock.json` are generated from real dependency resolutions.

```bash
uv sync --frozen
cd web && npm ci && npm run build && cd ..
uv run alembic upgrade head
uv run uvicorn prediction_terminal.api.app:app --host 127.0.0.1 --port 8010
# Separately:
uv run python -m prediction_terminal.workers.main
```

For hot reload, run `make api`, `make worker`, `make web` separately; Vite is at http://127.0.0.1:5173 and proxies only to your backend. If uv is installed inside this workspace's venv, use `make UV=.venv/bin/uv <target>`.

For PostgreSQL:

```bash
docker compose up -d db
export PT_DATABASE_URL=postgresql+psycopg://terminal:terminal@localhost:5432/terminal
uv run alembic upgrade head
# Start API/worker with this environment, or package all local services:
docker compose --profile app up --build
```

PostgreSQL/container definitions are provided but were not runtime-tested here because Docker/PostgreSQL tools are unavailable. SQLite migrations and persistence were tested. Do not expose the local unauthenticated server publicly.

## Workflow

- `SRCH <topic or event URL>` searches/imports; `COMP <match-id>` opens a deep link. `SCAN`, `WL`, `RULES`, `ALERTS`, `SETTINGS` navigate. Cmd/Ctrl+K focuses the command bar.
- Review suggested outcomes and the full settlement rules. Similar titles and numerical gaps do **not** prove equal payoffs.
- Charts label trade/indicative/local-midpoint provenance. Unlike price types remain separate; recorded comparable history enables spread overlays.
- The Trade panel consumes asks at your chosen units/budget, shows scenarios and execution/settlement gates, and supports both directions. Unknown fees remain unknown unless you explicitly enter a scenario estimate or record a reviewed market policy.
- Settings supports evidence-bearing fee policies and explicit synthetic outcome matrices. Both unit and budget sizing are supported for explicit synthetic baskets.
- Watchlists feed the worker. Save workspace persists layout, tabs, filters/range and link-group selection; quotes are refreshed, not restored as live.

The supplied Fed events are discovery seeds only. The app never labels their mappings preapproved. No orders, wallet signatures, deposits or private accounts are implemented.

## Layout

```text
src/prediction_terminal/
  domain/          Canonical markets, settlement, books, matches, opportunities, ports
  adapters/        Kalshi REST/auth capabilities; Polymarket Gamma/CLOB/public stream
  market_data/     Catalog, normalization, freshness, history, subscriptions, replay
  matching/        Candidates, structured rules, synthetic replication, review
  analytics/       Decimal depth, fees, payoff scenarios, sizing and capital
  application/     Search/import, comparison, scanner, simulator and saved state
  api/             Versioned FastAPI routes and browser WebSocket gateway
  persistence/     SQLAlchemy tables/repositories and redacted raw archive
  workers/         Catalog reconciliation, selected ingestion, scans and alerts
  observability/   Structured events and request/worker metrics
web/src/           React terminal shell, workspace layout and feature panels
migrations/        Frozen initial Alembic schema
tests/            Unit, recorded adapter, integration and replay tests
scripts/           OpenAPI generation, opt-in network smoke and benchmark
infra/             Container packaging
```

## Checks

```bash
make test lint typecheck build types
make smoke                         # Explicit public-network reads; never orders
make benchmark                     # Fictional deterministic local calculation workload
cd web && npm run e2e               # Explicit live-browser checks; reads public APIs
```

API docs: http://127.0.0.1:8010/docs. Configuration: [.env.example](.env.example).

See [architecture](docs/architecture.md), [source register](docs/source-register.md), [matching policy](docs/matching-policy.md), [pricing methodology](docs/pricing-methodology.md), [API contract](docs/api-contract.md), [terminal UX](docs/terminal-ux.md), [operations/capability matrix](docs/operations.md), [acceptance ledger](docs/roadmap.md) and [verification results](docs/verification.md).
