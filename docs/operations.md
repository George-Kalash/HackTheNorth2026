# Operations and integration capabilities

The release is single-user/local-first/read-only. Bind local processes to 127.0.0.1. Compose publishes only loopback ports. Do not deploy publicly without authentication, authorization, tenant isolation, origin/CSRF controls, API rate limits and a separate security review. No deployment is part of this build.

## Capabilities

| Capability | Implementation / actual verification |
|---|---|
| Kalshi public catalog and supplied Fed event | Implemented and live-tested |
| Kalshi fixed-point full book and complementary levels | Implemented, live-tested, recorded-payload regression |
| Kalshi history | Trade candle path live-tested; old settled historical route not integrated |
| Kalshi authenticated WebSocket | Capability gate + server-only RSA helper; feed not enabled or tested without credentials. Public REST POLLED fallback |
| Polymarket Gamma discovery and supplied Fed event | Implemented and live-tested |
| Polymarket CLOB YES/NO books | Implemented and live-tested |
| Polymarket history | Current documented Data API price-observation route live-tested; CLOB is executable-book source |
| Polymarket public stream | Worker reconnect/subscription/heartbeat implementation as invalidation hints; computations always resnapshot via REST. Not claimed as a sequenced executable streaming book |
| Browser stream | Snapshot/status/heartbeat gateway and reconnect/resync client tested |
| Fee policies | Default UNKNOWN; supported formulas can be recorded with explicit per-market evidence and expiry; no automatic whole-exchange fee coverage |
| PostgreSQL + Docker | Compose, psycopg repository and frozen Alembic DDL provided; not executable here because Docker/PostgreSQL tools are unavailable. CI includes PostgreSQL migration job, not a claim that CI has run |
| SQLite local mode | Migration, constraints, API persistence and worker tested |
| Order execution/private accounts | Absent by design |

## Running and freshness

Start migrations before API/worker. A separate worker reconciles imported event rules every 10 minutes, polls selected/watchlisted/approved markets at the configured interval, scans approved mappings and evaluates in-app alerts. It limits a cycle to 30 selected match groups. Catalog search is bounded; it is not a full-market crawler.

Transport uses pooled httpx clients, six concurrent requests maximum, conservative per-origin budgets, up to three tries on transient failures, Retry-After handling, redirect rejection and schema-validation failures. Large Retry-After values are surfaced rather than holding a request open indefinitely. Public stream data does not claim sequence completeness. Kalshi feed credentials are never required for public REST.

Configure `PT_POLL_SECONDS`, `PT_MAX_AGE_SECONDS`, `PT_MAX_SKEW_SECONDS`, `PT_REQUESTS_PER_SECOND`, `PT_RETENTION_DAYS`, `PT_DATABASE_URL`. A book without an upstream timestamp uses disclosed receipt time. Time skew and age are checked independently. Disconnections freeze last-good values under flags; freshness/degradation gates block verified signals and alerts.

`.env.example` has placeholders only. Private keys, if supplied for future market-data streaming, are file paths on the backend. Logs do not print signing headers; raw archive redacts known credential fields and only captures public responses. Data caches/DBs are ignored by Git. Recorded fixtures are dated public payloads with source path and retrieval timestamp.

## Data permissions

Public API access does not automatically grant redistribution rights. Review Kalshi's developer agreement and Polymarket's API/data terms before a hosted product, data resale, or broad distribution of raw archives. This build performs local public research reads and does not bypass authentication, geographic controls or platform restrictions.

## Known limits

No guaranteed fill/atomic cross-venue execution, no maker-fill simulation, no automated proof of natural-language settlement semantics, no automatic synthetic discovery, no stablecoin/FX guarantee, no full-universe catalog scan. Explicit synthetic baskets support budgets, chosen units, scanner evaluation and aligned target-minus-component historical spreads. Some Kalshi lot/tick metadata is not established by the public payload used here, which blocks verification rather than inventing a lot size. The browser gateway publishes full snapshots instead of granular deltas. A 1,000-row fixture tests virtualization; production catalog/network p95 is not claimed.
