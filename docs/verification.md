# Verification receipt — 2026-09-19

These are actual local results, not fixture-based claims about live connectivity.

| Check | Result |
|---|---|
| Python unit / recorded adapter / API / SQLite migration / replay suite | **55 passed** (`pytest -q`, 1.35s); two dependency deprecation warnings from Starlette/httpx/AnyIO |
| Ruff lint | Passed |
| Python mypy | Passed, 91 source files |
| TypeScript strict build / Vite production build | Passed; code split into app, React/router, query and chart chunks |
| Vitest | **4 passed** |
| Playwright live desktop/mobile workflow | Passed: import → comparison → books/rules → simulation → watchlist → workspace save/reload → keyboard command → scanner → mobile books |
| Playwright linked groups / recovery | Passed: independent A/B selections and ranges, stable canvas through crosshair movement, maximize/Esc, malformed persisted filters recovered; caught and fixed chart auto-size feedback and hidden-chart crosshair errors |
| Playwright degraded state | Passed: offline/failed health response and missing Kalshi streaming credentials show fallback/disconnected state |
| Playwright fictional 1,000-row scanner workload | Passed; fewer than 100 row nodes mounted, scroll reaches row 999; one measured navigation/render/scroll run 162 ms (not a p95 claim) |
| npm audit | **0 vulnerabilities** at resolved lockfile versions |
| Both supplied venue seed URLs | Live-tested at 2026-09-19 09:12:39 UTC; each returned original + counterpart event, five candidate pairs, both books, 125 Kalshi trade candles and 170 Polymarket indicative observations for selected 7-day comparison; no source errors |
| Local worker | Observed heartbeat, selected-market polling, connected public Polymarket invalidation stream and no reported cycle errors |
| PostgreSQL/container runtime | **Not run**: no Docker/Postgres executable in this environment; attempted Homebrew PostgreSQL installation stopped at an existing ca-certificates link conflict. Compose/Dockerfile and PostgreSQL CI migration job supplied |

Public-network smoke is explicitly invoked with `python scripts/smoke.py --live` and never submits orders. Small dated/redacted adapter fixtures are committed under `tests/fixtures/recorded/`; synthetic cases are explicitly fictional. Dynamic smoke receipts, screenshots and benchmark JSON are local ignored artifacts under `data/`.

## Calculation benchmark

Hardware reported by the runtime: macOS 26.6.2, arm64. Python 3.13.3. Workload: 1,000 fictional two-leg simulations with 50 ask levels per leg, size 100, known fictional zero fees, capacity search disabled. Median **0.0335 ms**, p95 **0.0379 ms** per calculation. This measures pure local math only; database access, source latency, worker delays and calculation-to-browser p95 are not included. The full under-500-ms end-to-end target remains unverified.

## Compatibility and boundaries

Live-tested paths are public REST, not authenticated Kalshi streaming or order execution. Provider historical price types differ and remain separate. Kalshi lot size is still unverified from the chosen payload. The seed matches are not preapproved. Unknown fee/lot/rule inputs intentionally prevent verified opportunity labels. PostgreSQL and packaged deployment must be exercised in an environment with the required runtime before claiming their acceptance complete.
