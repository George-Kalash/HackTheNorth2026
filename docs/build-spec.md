# Prediction Markets Terminal — architecture and implementation prompt

## 1. Product decision

Build a research terminal for comparing Kalshi and Polymarket contracts, explaining whether their payoffs match, and estimating executable cross-venue opportunities. Bloomberg-inspired command navigation and information density; TradingView-inspired chart workspaces and linked panels. Use original branding and assets, not copied proprietary screens.

This is an architecture and build specification, not a completed application. Start with a modular monolith: one Python backend, one ingestion worker, one frontend, one database. Do not introduce microservices or Kubernetes for the MVP.

Recommended stack: Python 3.12+, FastAPI, Pydantic, httpx, asyncio, SQLAlchemy/Alembic, PostgreSQL; React/TypeScript with Vite for the browser client. Use pytest for Python and Vitest/Playwright for the frontend. Resolve compatible current versions and commit actual lockfiles during implementation. This is a Python-centric project, not a Python-only UI. A Python-only alternative is PySide6 for a desktop app, but it changes distribution and UI implementation; do not build both.

First release is read-only, single-user/local-first, with scenario simulation. No order placement, wallet signing, deposits, private account integration, or autonomous trading. Authentication and tenant isolation are prerequisites for any hosted multi-user release.

## 2. What the original idea is missing

| Missing component | Why it matters | Owner |
|---|---|---|
| Canonical event/outcome model | Titles and platform categories do not uniquely identify the same payoff | domain/ |
| Contract-rule comparison | Same topic can have different dates, thresholds, authorities, cancellation and dispute rules | matching/ |
| Synthetic outcome mapping | One venue may offer a bucket that requires multiple contracts elsewhere | matching/synthetic.py |
| Executable quote normalization | Last prices and midpoints are not buy/sell prices | market_data/ |
| Depth-aware sizing and fees | A headline price gap may disappear at the intended size | analytics/ |
| Freshness and synchronization | Stale or asynchronous books create false signals | market_data/freshness.py |
| Explainable classifications | Related contracts must not be advertised as arbitrage | domain/matches.py |
| Trade-leg and payoff simulator | Show what is bought, the required cash, and outcomes where it loses | analytics/payoffs.py |
| History provenance | A trade-price history is not historical executable depth | market_data/history.py |
| Persistent review/audit state | Rule amendments can invalidate yesterday's match | persistence/ |
| Terminal workspace state | Linked panels need selection, layout, tabs, and keyboard semantics | web/src/workspace/ |
| Operational controls | Rate limits, reconnects, missing credentials, schema drift and outages | adapters/, workers/, observability/ |
| Access and data permissions | Public data access does not automatically authorize redistribution or trading | docs/operations.md |

## 3. Repository map

Paths below are the target layout to create. Every directory owns a specific concern. Python package directories contain __init__.py. Avoid generic utils.py, helpers.py, or one enormous dashboard.py.

```text
prediction-terminal/
  README.md
  pyproject.toml
  uv.lock                         # generated from a real dependency resolution
  .env.example                    # names/placeholders only
  .gitignore
  Makefile                        # dev, test, lint, typecheck, migrate, smoke
  compose.yaml                    # PostgreSQL; app services when packaging
  src/prediction_terminal/
    __init__.py
    bootstrap.py                  # dependency wiring, no business calculations
    config.py                     # validated environment configuration
    domain/
      markets.py                  # VenueMarket, Event, Outcome, SettlementSpec
      books.py                    # BookLevel, BookSnapshot, Quote, quality flags
      matches.py                  # MatchGroup, MatchLeg, review state, rule hash
      opportunities.py            # TradeLeg, Opportunity, PayoffScenario
      history.py                  # PricePoint and price-type provenance
      ports.py                    # protocols for feeds/repositories/clock
      errors.py                   # typed domain failures
    adapters/
      common/
        transport.py              # pooled HTTP clients, timeouts, retry policy
        rate_limit.py             # per-venue/endpoint budgets
      kalshi/
        rest.py                   # catalog, rules, books, trades, history
        websocket.py              # authenticated feeds where required
        auth.py                   # server-side market-data auth only
        schemas.py                # raw wire schemas, not canonical models
        mapper.py                 # wire payload -> canonical model
        capabilities.py           # supported feeds/auth/endpoint capabilities
      polymarket/
        gamma.py                  # catalog and metadata
        clob.py                   # token-level books, prices and history
        websocket.py              # public market stream
        schemas.py
        mapper.py
        capabilities.py
    market_data/
      catalog.py                  # pagination, lifecycle reconciliation
      book_builder.py             # snapshots/deltas, ordering, gap recovery
      normalizer.py               # complementary quotes and units
      freshness.py                # age, inter-venue skew, stale thresholds
      history.py                  # requested series, alignment, bounded gaps
      subscriptions.py            # shared/refcounted upstream subscriptions
    matching/
      candidates.py               # category/entity/date/text candidate retrieval
      predicates.py               # parsed rate ranges, date/time, event identity
      equivalence.py              # rule-by-rule deterministic comparison
      synthetic.py                # disjoint/exhaustive payoff replication
      review.py                   # approve/reject/revoke, reason and audit
    analytics/
      fees.py                     # venue-specific, versioned fee policies
      depth.py                    # cumulative cost, VWAP, fillable quantity
      payoffs.py                  # scenario payoff matrix and minimum payout
      opportunities.py            # gross/net edge and eligibility gates
      capital.py                  # funding assumptions and holding-period metrics
    application/
      search.py                   # search and allowlisted URL import use cases
      comparison.py               # assemble read models for a comparison
      scanner.py                  # ranked eligible/ineligible opportunities
      simulation.py               # request -> calculation result
      watchlists.py
      alerts.py                   # user-configured in-app rules, dedup/cooldown
      workspaces.py               # save/restore versioned workspace layout
    api/
      app.py                      # FastAPI app factory and lifecycle
      dependencies.py
      schemas.py                  # public API DTOs
      routes/
        search.py
        markets.py
        matches.py
        comparisons.py
        opportunities.py
        simulations.py
        watchlists.py
        alerts.py
        workspaces.py
        health.py
      streaming.py                # browser WebSocket gateway, snapshots + deltas
    persistence/
      database.py
      tables.py
      repositories.py
      raw_archive.py              # redacted source payloads and provenance
    workers/
      main.py                     # worker lifecycle and graceful shutdown
      catalog_sync.py
      stream_ingest.py
      history_backfill.py
      opportunity_scan.py
      alert_evaluation.py
    observability/
      logging.py                  # structured logs; no credentials
      metrics.py                  # lag, reconnects, 429s, scan and API latency
  migrations/                     # Alembic revisions and env.py
  tests/
    unit/                         # pure rules/math/freshness tests
    integration/                  # DB, API, adapter contract tests
    replay/                       # sequence gaps, duplicates, stale feeds
    fixtures/
      synthetic/                  # explicitly fictional deterministic cases
      recorded/                   # dated, redacted upstream samples
  web/
    package.json
    package-lock.json             # generated; choose one JS package manager
    index.html
    vite.config.ts
    tsconfig.json
    src/
      main.tsx
      app/                        # router, providers, error boundary
      terminal/
        TerminalShell.tsx
        CommandBar.tsx
        FunctionRail.tsx
        WorkspaceTabs.tsx
        StatusBar.tsx
        commands.ts               # command -> route/action registry
      workspace/
        PanelGrid.tsx
        PanelFrame.tsx
        panelRegistry.ts
        store.ts                  # selection/link groups/layout only
        persistence.ts            # schema version and migration
      features/
        search/                   # SearchPage, SearchResultsPanel, hooks
        comparison/               # ComparePage, ComparisonHeader, MatchPanel
        charts/                   # ProbabilityChart, SpreadChart, chart adapter
        orderbook/                # OrderBookPanel and DepthChart
        scanner/                  # ScannerPage, OpportunityTable, filters
        simulator/                # TradeSimulatorPanel and ScenarioTable
        rules/                    # RulesPanel, RulesDiff, ReviewControls
        watchlists/               # WatchlistPanel, WatchlistPage
        alerts/                   # AlertsPanel, AlertsPage, RuleEditor
        settings/                 # SettingsPage; no plaintext secrets
      components/                 # truly shared table/button/badge/form primitives
      services/
        api.ts                    # own backend only
        stream.ts                 # reconnect, subscriptions, sequence checking
        generated/                # generated OpenAPI types; do not hand edit
      styles/
        tokens.css                # all colors, spacing, typography variables
        terminal.css
      test/
    e2e/
  docs/
    architecture.md
    api-contract.md
    terminal-ux.md
    matching-policy.md
    pricing-methodology.md
    source-register.md
    operations.md
    roadmap.md
  scripts/                        # import fixtures, generate types, smoke checks
  infra/                          # Dockerfiles, deployment configuration
  data/                           # ignored local caches; never committed secrets
  .github/workflows/ci.yml
```

## 4. Dependency and ownership rules

Domain is independent of FastAPI, databases, network clients and the UI. Matching and analytics use domain objects and pure functions. Application coordinates domain services through ports. Adapters and persistence implement ports. API/worker entrypoints use bootstrap to assemble them. No adapter imports the API or browser layer. No pricing, matching or fee calculations live in React, API route handlers, or database models.

Keep raw upstream schemas separate from canonical domain types and public API DTOs. Frontend feature folders own their components, hooks and local tests. Only reused presentation primitives go in components/. Workspace state is not a duplicate quote database: use a query cache for server state and a small store for UI selection/layout. The browser never calls exchange APIs directly or holds exchange private keys.

## 5. Terminal navigation and spatial layout

Desktop-first at 1440x900, functional at 1280x800. Top command strip ~44px, workspace tabs ~32px, left function rail ~52px, bottom status bar ~24px. Remaining area is a resizable grid; dimensions are defaults, not fixed constraints.

| Region | Default content | Behavior |
|---|---|---|
| Top strip | Product name, command/search field, global search, connection indicators | Persistent; Cmd/Ctrl+K focuses search |
| Left rail | Search, Compare, Scanner, Watchlists, Alerts, Settings | Icon + tooltip + accessible label |
| Tabs below top strip | Saved workspaces and open comparisons | Restore session; close/reorder; stable URLs |
| Left pane, ~20% | Search results or watchlist | Selecting a row updates linked panels |
| Center pane, ~55% | Contract header, price-history overlay, spread subplot | Chart occupies upper ~60%; books and scanner below |
| Right pane, ~25% | Match confidence, rule differences, trade simulator | Tabs RULES / TRADE / DETAILS |
| Bottom strip | UTC clock, venue status, update age, lag, stale banner | Never says LIVE when disconnected or stale |

Use four named workspace presets: Research, Compare, Scan and Rules Review. Panels can resize, collapse, maximize and reset. Link groups A/B/C allow two unrelated comparisons in one workspace: changing the selected match updates only panels in the same group. Chart time range and cursor can synchronize within a group. Persist panel layout, selected contracts, filters and time range, but not stale quotes as live data.

Command registry: SRCH <query>, COMP <match-id>, SCAN, WL, RULES, ALERTS, SETTINGS. Accept venue URLs in search. Commands are navigation, never arbitrary shell evaluation. Esc closes overlays without clearing the selected market. Arrow keys navigate results; Enter opens. Commands and clicks call the same actions. Keyboard shortcuts must not hijack typing inside forms.

Routes: /search?q=, /compare/:matchId, /scanner, /watchlists/:id, /alerts, /settings. Make comparisons deep-linkable. At narrow widths replace the grid with chart/books/rules/trade tabs rather than shrinking dense desktop panels until unreadable.

Visual language: near-black background, charcoal surfaces, thin borders, restrained amber action accents, cyan versus violet venue series, monospace/tabular numbers, readable sans-serif labels. Compact 12–14px tables and ~28px rows; avoid oversized cards and decorative gradients. Green/red represent positive/negative economics, not venue identity. Every color-only signal also needs text or an icon. Provide visible focus states, adequate contrast, loading/empty/error/stale/disconnected states and reduced motion. Virtualize large tables; throttle visual updates independently of ingestion.

## 6. Canonical data and storage

Store Decimal prices in [0,1], Decimal quantities, explicit payout value/currency, UTC-aware timestamps, raw source units and source URLs. Format cents and probabilities only at presentation. Keep last trade, midpoint, bid, ask and indicative probability as distinct nullable fields. Never convert missing prices into zero.

VenueMarket key: venue + external market ID. Preserve event ID, ticker/slug, condition ID and outcome token IDs where applicable. Never infer YES/NO from array position without reading the outcome mapping. SettlementSpec includes observation window, timezone, variable measured, baseline, threshold and inclusivity, resolution authority, deadline, payout, cancellation/void/dispute treatment, independent/caucus rules when relevant, and complete rule text/hash.

Tables: venue_events, venue_markets, outcomes, rule_versions, match_groups, match_legs, match_reviews, price_points, book_snapshots, opportunity_snapshots, watchlists, watchlist_items, alert_rules, alert_events, workspaces, ingestion_checkpoints. Use foreign keys and unique venue identifiers. Attach input book IDs, timestamps, rule/fee versions and model version to every opportunity result. Retain raw redacted inputs for reproducibility. Rule changes revoke prior equivalence approval until reviewed. Configure retention instead of storing every book delta forever; retain short-window raw replay plus periodic snapshots and opportunity inputs.

## 7. Matching policy

Candidate retrieval is not equivalence verification. Retrieve using event/entity/date/category and text similarity; then compare structured settlement predicates and actual rule wording. Optional embeddings may suggest candidates, never certify arbitrage.

Classify as EXACT, SYNTHETIC_EQUIVALENT, RELATED, or REJECTED. Review state is separate: UNREVIEWED, APPROVED, REVOKED. Display reasons and differences; confidence is a matching score, not a probability of profit. In MVP, only explicitly approved exact/synthetic mappings enter the executable-opportunity scanner.

The supplied October Fed URLs are candidate seeds, not proven identical contracts. Fetch all outcomes and rules; verify the specific meeting, rate definition (target range versus another measure), upper/lower bound, baseline, change units, bucket endpoints, dates, cancellation and emergency-action handling. For a broad bucket, construct a basket only when the narrower outcomes are mutually exclusive and collectively cover precisely that bucket. Missing coverage or unresolved ambiguity means RELATED or unreviewed.

The earlier Congress example must be a regression case: Democratic Senate exposure can require DD + RD combinations. A Democratic sweep alone is not equivalent to Democratic Senate control. Account for any other/undefined-control states and rule differences before approving the basket.

## 8. Market-data pipeline

Discover catalogs with pagination; import rules and outcome identifiers; normalize; propose matches; review; subscribe approved/watchlisted markets; build books; validate freshness; calculate opportunities; publish backend updates. Poll catalogs slowly and selected books at a configurable budget, not the whole universe each second.

Kalshi adapter must explicitly normalize its YES and NO bid books. For $1 binary payout, YES ask = 1 - NO bid and NO ask = 1 - YES bid; preserve each complementary level's quantity and sort the resulting asks. Use current fixed-point fields, tick sizes and lot sizes. WebSocket support is capability/auth dependent; if unavailable, use declared REST polling and label it POLLED, not streaming.

Polymarket Gamma owns discovery; CLOB owns token-level executable books/prices; its public market stream supplies live market updates. Data API is optional for later activity/portfolio features, not the primary order-book source. Verify current endpoints, pagination, authentication, subscriptions, fees and schemas from official docs before implementing.

Streams must support initial snapshot, delta application, duplicate/out-of-order handling, heartbeat, reconnect with backoff/jitter, resubscribe and resnapshot after gaps. Respect 429/Retry-After and configurable concurrency. Unsubscribe unused contracts and share upstream subscriptions across panels. Unsupported sequence metadata must be explicitly handled with conservative resnapshot/staleness rules rather than fabricated sequence guarantees.

Each update carries venue event time where available, received_at, normalized_at, book ID, sequence/hash where available, and quality flags. Use received_at only as a disclosed fallback. Configure maximum age and cross-venue time skew. Freeze last-good data visibly during outages and suppress opportunity alerts. A missing side of the book is unpriced, not a 0% outcome.

## 9. Trade economics

Separate three concepts in both code and UI: indicative probability gap; executable pre-fee edge; estimated after-cost edge. Similar probabilities do not establish identical payouts. Buy at asks; sell at bids only when the user actually owns the inventory or a supported funded construction is modeled. Never assume cross-platform naked shorting or atomic execution.

For truly complementary $1 YES/NO claims, q shares per leg:

    net_floor(q) = q - cost_yes(q) - cost_no(q) - fees(q) - other_costs(q)

cost_yes/cost_no consume the complete available ask ladders. Depth already includes price impact; do not subtract the same slippage twice. Apply a separate optional adverse-move stress buffer and disclose it. For any basket, replace q with the minimum total payout over the documented scenario matrix. Require matching payout denomination or show FX/stablecoin basis assumptions explicitly. Positive modeled payoff is still conditional on platform performance and compatible resolution.

FeePolicy must be venue/market/date/side aware, record evidence and rounding, and distinguish maker/taker. Default immediate simulations to taker. Unknown fee policy blocks a verified net-edge label; do not silently assume zero. Maker scenarios are conditional on fills and cannot promise the same execution probability. Funding/withdrawal costs, currency conversion and capital lockup assumptions are explicit and editable. Show annualized metrics only with a credible holding period and never as guaranteed yield.

Example synthetic test: YES ask 0.54 + complementary NO ask 0.43 + total costs 0.02 gives 0.01 modeled floor per matched payout unit. Correct conditional arithmetic. ✅

Incorrect claim: a 54% last trade versus a 58% last trade automatically means 4% arbitrage. Those prices may be untradeable and the rules may differ. ❌

Trade simulator inputs: size or budget, direction, fee mode, cost/stress assumptions. Outputs: each venue/outcome/side/quantity, consumed levels, VWAP, fees, gross outlay, cash required per venue, minimum payout, net floor, ROI on required capital, capacity, rule risks and legging risk. Show the maximum size that meets the net-edge threshold using depth breakpoints and minimum lot sizes. If only one leg fills, show the residual directional position and an estimated unwind scenario. Call these CANDIDATE OPPORTUNITIES, never guaranteed profit.

## 10. Charts and tables

Rebuild charts from API data; do not scrape screenshots or embed exchange interfaces. Chart adapter in web/features/charts isolates the chosen library. Select an appropriately licensed library during implementation; do not assume TradingView's full proprietary charting product is free. Probability Y-axis 0–100%; signed spread axis in percentage points. Include time range, crosshair, legend, venue source, price type and data age.

Overlay only comparable series with the same price type. Use common UTC intervals with tolerance and maximum carry-forward age; leave gaps when data is missing. Never silently substitute last-trade history for midpoint history or construct historical executable arbitrage from last trades. Historical bid/ask/net-edge charts begin when valid snapshots are recorded unless the provider supplies adequate historical books. Synthetic history must align every leg and flag incomplete intervals.

Scanner columns: event, outcome, match class/review status, both venue bids/asks, indicative gap, proposed legs, net floor at selected size, capacity, fee status, quote ages, rule warnings and expiry. Filters: topic, date, match class, min net edge, min capacity, max age, review state. Sort valid opportunities ahead of indicative gaps; preserve user row selection as prices update. Details retain rejected eligibility reasons.

## 11. Backend interface

Version under /api/v1. GET /search?q=; POST /imports/venue-url; GET /markets/:id; GET /markets/:id/book; GET /markets/:id/history?price_type=&interval=&from=&to=; GET /matches/:id; POST /matches/:id/review; GET /comparisons/:id; GET /opportunities; POST /simulations; CRUD watchlists, alert rules and workspaces; GET /health/live and /health/ready. Place URL import in search.py. Use response pagination and typed errors. Map stable public IDs rather than exposing database internals.

WS /api/v1/stream: client subscribes/unsubscribes to selected comparison/book/opportunity topics. Server sends typed snapshot, delta, status, heartbeat and error envelopes with schema version, topic, sequence and timestamps. On missing sequence, request/resend a snapshot. Slow clients get bounded/coalesced queues or disconnection plus resync, not unlimited memory growth. Generate TypeScript DTOs from backend OpenAPI; document WebSocket types alongside them.

URL import is an SSRF boundary: allowlist exact approved venue hosts, parse known URL forms, resolve metadata through the venue adapter, reject arbitrary hosts and redirects to private/internal networks. Do not fetch arbitrary user URLs from the server.

## 12. Tests and acceptance

Unit tests: complementary Kalshi levels/quantities, token identity, inverted outcomes, decimals and rounding, empty/one-sided books, depth VWAP, fee changes, partial fills, minimum lots, stale/skewed books, threshold endpoint mismatches, rule-change invalidation, synthetic overlap/missing coverage, and payoff matrices. Include the Senate replication case and fictional Fed bucket cases.

Adapter contract tests use recorded dated redacted payloads with provenance. Network smoke tests are opt-in and never submit orders. Replay tests exercise duplicate, gap and reconnect sequences. Integration tests verify database migrations and API validation. End-to-end tests cover search -> matched contract -> linked chart/books/rules -> simulation -> watchlist -> reload workspace, keyboard-only navigation, offline and missing-credential states.

Acceptance: a user can paste either supplied Fed URL, see the original contract and evidence-backed candidate matches, inspect rule differences, compare labeled histories/books, simulate both trade directions at chosen size, and save a workspace. If the source no longer exists, show not found; do not substitute a different meeting. Unreviewed, stale, incomplete or unknown-fee comparisons cannot display verified positive net edge. The read-only app must contain no venue order-submission path.

Initial performance targets, to benchmark rather than claim: 1,000 visible/virtualized scanner rows, responsive keyboard input, frontend renders coalesced to approximately 4–10Hz where needed, local calculation-to-browser p95 under 500ms on a documented fixture workload. Venue freshness and network latency remain separately measured. Record benchmark hardware and workload.

## 13. Build phases

1. Foundation: scaffold, strict types, domain, synthetic fixtures, tests, FastAPI health and terminal shell. Demo mode must be unmistakably labeled.
2. Read-only feeds: adapters, catalog, rules, books, timestamps, history and degraded states. Verify each endpoint with small safe requests.
3. Matching and economics: explicit Fed mappings, review UI, fee policies, depth/payoff engine and provenance.
4. Terminal workflow: linked panels, scanner, overlays, simulator, keyboard commands and saved workspaces.
5. Hardening: replay tests, failure recovery, alert deduplication, documentation, metrics and packaging.
6. Optional later: authenticated portfolio reconciliation, news/calendar feeds with licensed sources, advanced matching and backtesting with sufficient historical depth. Live execution is a separate explicitly authorized project with risk limits, position reconciliation, credentials design, audit, kill switch and partial-fill recovery.

## 14. Copy-ready implementation prompt

You are the senior engineer building Prediction Terminal. Implement the architecture in this specification, preserving its exact directory ownership, dependency rules, data contracts, safety boundaries and acceptance criteria. Treat this file as the product/build brief. Do not collapse the project into a single app.py or a generic dashboard.

First inspect any existing repository and its instructions. Preserve unrelated edits. Report what exists, the proposed changes and any incompatible assumptions. If this is a new repository, create the layout in section 3, using Python for all backend, matching and pricing logic and React/TypeScript for the terminal UI. Use a modular monolith plus worker. Do not introduce an alternative framework without explaining the consequence and obtaining direction if it materially changes the brief.

Before venue integration, verify official documentation and record endpoint, authentication requirement, pagination, rate limit, schema fields, history semantics and verification date in docs/source-register.md. The user-provided Fed URLs are discovery seeds only. Do not assume that matching titles imply matching contracts. Read resolution rules and construct auditable outcome mappings.

Work phase by phase as specified in section 13. For each phase: implement one usable vertical slice, add relevant tests, run checks available in the environment, document limitations, and summarize completed versus remaining work. Generate lockfiles from resolved dependencies, not invented version lists. Do not claim a live integration works from fixtures alone. Label demo, polled, streaming, stale and unavailable states distinctly.

Implement the persistent terminal shell and separate feature panels defined in section 5. All commands, shortcuts, links and buttons must perform their stated action. Use original terminal styling, compact tables, accessible keyboard navigation, persistent resizable layouts, link groups and synchronized chart selections. No fake KPIs, random prices, fabricated volume or decorative dead controls.

Implement the domain and feed normalization first, then the reviewed equivalence matcher, then depth/fees/payoff analysis. Every proposed trade must explain its legs, capacity, data age, costs, scenario payout, assumptions and risks. UI must distinguish indicative gaps from executable gross edge and estimated net edge. Unknown rules/fees, stale data or incomplete books block validated opportunity classification.

Keep exchange secrets server-side, redact logs, respect endpoint budgets and platform restrictions, and provide REST fallback where permitted when streams cannot be authenticated. The MVP is read-only: do not request wallet signing, place orders or implement automatic trading. Do not deploy publicly as part of this brief.

Deliver documented commands for setup, local launch, migrations, tests and production build; verified tests with actual results; an honest integration capability matrix; and a checklist against section 12. Start with phase 1 and make assumptions explicit rather than hiding them in code.

## 15. Official source register — checked 2026-09-19

- [Kalshi API overview](https://docs.kalshi.com/welcome): use Predictions APIs, not Perps.
- [Kalshi order-book normalization](https://docs.kalshi.com/getting_started/orderbook_responses): bid-side YES/NO books, fixed-point dollars/quantities and complementary asks.
- [Polymarket API surfaces](https://docs.polymarket.com/getting-started/api): Gamma discovery, CLOB market data and public market WebSocket are separate concerns.
- [Polymarket prices/order books](https://docs.polymarket.com/market-data/prices-order-books): verify current pricing/history interfaces during implementation.
- [Polymarket real-time data](https://docs.polymarket.com/market-data/realtime-data): verify current subscriptions and lifecycle handling during implementation.
- [Polymarket Fed example](https://polymarket.com/event/fed-decision-in-october-20260617190323537)
- [Kalshi Fed example](https://kalshi.com/markets/kxfeddecision/fed-meeting/kxfeddecision-26oct)

These sources support integration architecture, not a claim that the two Fed contracts have been proven settlement-equivalent. Fee schedules and API capabilities must be reverified when the application is built; earlier conversation snapshots are not live data.
