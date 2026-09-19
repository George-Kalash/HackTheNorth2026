# Architecture

Parallax is a local, read-only modular monolith: Python FastAPI API, separate asyncio ingestion worker, React/TypeScript Vite frontend, and one SQLAlchemy database. PostgreSQL is the deployment target. SQLite/WAL is the documented zero-service local mode used for this build because Docker/PostgreSQL executables are unavailable in the development environment.

## Ownership

- `domain/`: canonical Pydantic models, Decimal units, protocols and typed failures. No FastAPI, SQLAlchemy, HTTP or frontend imports.
- `matching/`: candidate retrieval, deterministic rule comparison, replication matrices, explicit review and revocation.
- `analytics/`: pure depth, fee, capital and payoff calculations. Browser components and route functions do not calculate trading economics.
- `application/`: imports, comparisons, simulation orchestration, scanner, watchlists, alerts and workspace use cases.
- `adapters/`: allowlisted public venue requests, raw schemas and mappers; `persistence/`: SQLAlchemy repositories and redacted raw archive.
- `market_data/`: lifecycle/rule reconciliation, normalized books, quality gates, local history alignment and subscription counts.
- `bootstrap.py`, `api/`, `workers/`: dependency wiring and entrypoints. Worker calls domain/application services, not API handlers.
- `web/src/`: query cache owns server state; Zustand owns layout, selections/link groups, tabs and chart ranges. Workspace storage contains no quote database or credentials.

## Storage

The initial Alembic revision creates every table in the build brief, plus `raw_inputs`. Entities retain typed JSON payloads with explicit relational foreign keys and unique venue identifiers. Monetary values inside payloads are Decimal strings, not binary SQL floats. Stable public IDs are SHA-256-derived identifiers; database internals are not browser keys.

Current fee policies are versioned documents in `ingestion_checkpoints`; historical policy evidence is retained in the raw audit archive. Opportunity snapshots embed their complete canonical market/book/match inputs, rule hashes, fee versions and model version. Raw source payload hashes link to book provenance. Rule changes revoke approved matches and append an automatic-revocation review record.

Rolling retention prunes books, local price points, raw archives and opportunity snapshots after configurable days (default seven). Rule versions, review decisions and saved workspace/watchlist state are not purged by that process. This is not a permanent regulatory archive.

## Data flow

1. Import a known venue URL by extracting its identifier, never by fetching the URL itself.
2. Retrieve the original event and candidate counterpart(s), persist all binary outcomes and rules, and propose explainable matches.
3. Poll selected/watchlisted/reviewed books within a per-origin budget. Public Polymarket events are coalesced invalidation hints; price calculations use complete REST snapshots. Kalshi uses public REST fallback.
4. Capture timing, raw references, flags and local bid/ask/midpoint observations. Freeze last-good books visibly on errors.
5. Review equivalence and, separately, document supported fee policy evidence. Simulate from ladders and scenarios; unknown inputs retain blocking reasons.
6. Expose typed REST read models and coalesced browser WebSocket snapshots/status/heartbeats. A slow client is disconnected and resynchronizes.

No exchange order submission, signing for orders, wallet integration, deposits, private balances or autonomous execution exists. Kalshi's optional RSA helper is limited to market-data authentication; its authenticated feed is not enabled in this release.
