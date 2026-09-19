# Build phases and acceptance ledger

This repository implements the five local MVP phases with conservative capability gates. Optional live trading is a separate project and is not implemented.

| Phase | Delivered | Remaining limits |
|---|---|---|
| 1 Foundation | Owned package layout, canonical Decimal models, SQL schema/migration, generated TS contracts, terminal shell, real lockfiles, fictional tests | PostgreSQL runtime verification needs a Docker/Postgres environment |
| 2 Read-only feeds | Public event import/search, full normalized books, rules/hashes, historical observations, timestamps, budgets, degraded/frozen states, worker | Authenticated Kalshi streaming not enabled; old settled histories not integrated; general discovery bounded |
| 3 Matching/economics | Deterministic differences, evidence-bearing approvals/revocations, explicit synthetic matrices, depth/VWAP, fee registry, scenarios, budget/size and provenance | No automated semantic equivalence proof, full fee schedule coverage or maker-fill simulation |
| 4 Terminal workflow | Commands/routes, linked panels, separate/overlay charts, books/depth, scanner, simulator, rules, watchlists, alerts, saved layouts, responsive tabs | Synthetic histories retain component provenance; dense scanner needs horizontal scrolling on narrow screens |
| 5 Hardening | Unit/contract/replay/API tests, browser workflows, migrations, CI definitions, Docker packaging, raw retention, metrics, docs and benchmark | Production security/multi-user hosting intentionally out of scope; full network-to-browser p95 not benchmarked |

## Section 12 acceptance

- [x] Both supplied Fed URLs import their original event and five candidate outcome pairs; no substitute meeting.
- [x] Candidate scoring is separate from reviewed equivalence; full source rule text, hashes, differences and deadlines are inspectable.
- [x] Separate price types, missing prices, stale/skewed/degraded books and source timestamps are explicit.
- [x] Kalshi complementary asks preserve quantities; Polymarket tokens are mapped by YES/NO identity.
- [x] Depth-based simulations show consumed levels, VWAP, fees/unknown status, per-venue cash, scenarios, net floor/ROI, capacity and legging/unwind exposure.
- [x] Both pair directions and explicit synthetic-basket directions work; user-supplied matrices require complete binary-state replication and review.
- [x] Unreviewed/stale/incomplete/unknown-fee inputs cannot show verified positive net edge.
- [x] Watchlists, review audit, fee versions, alert rules/events and versioned workspace state persist.
- [x] Rule amendments revoke prior approval.
- [x] Keyboard command navigation, result-list arrows, responsive tabs, resizable/collapsible/maximized panels and independent A/B/C selections.
- [x] Browser error/offline/missing-credential flows; PUBLIC/POLLED statuses do not misrepresent stream coverage.
- [x] Senate DD+RD regression, synthetic overlap/missing coverage, duplicate/gap/reconnect replay, fees/rounding and financial math tests.
- [x] Repository contains no exchange order-submission route.
- [ ] Runtime PostgreSQL/container launch validated on this machine (Homebrew installation blocked by an existing certificate-package link conflict; Docker absent).
- [ ] Full calculation-to-browser p95 under 500 ms measured under a representative production workload (pure calculation benchmark only).

See `verification.md` for actual command results. Checkboxes identify delivered behavior, not a promise that all exchanges/market types are supported.
