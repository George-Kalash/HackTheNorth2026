# Backend interface

Base path `/api/v1`. Browser calls only this backend. OpenAPI is available at `/openapi.json` and `/docs`; generated TypeScript DTOs are in `web/src/services/generated/api.d.ts`. Run `make types` after changing schemas. Decimal values serialize as strings. Validation errors use FastAPI's `detail`; typed domain failures use `{error:{code,message}}` and appropriate 4xx/502 status.

| Method / path | Behavior |
|---|---|
| GET `/search?q=` | Bounded topic search or allowlisted URL import; events, matches, errors, coverage |
| POST `/imports/venue-url` | `{url}`; original event plus candidates, never arbitrary URL fetch |
| GET `/markets?limit=&offset=` | Imported canonical markets |
| GET `/markets/{id}` | Canonical market/rule metadata |
| GET `/markets/{id}/book` | Current or explicitly degraded last-good normalized book |
| GET `/markets/{id}/history` | `price_type`, `days=1/7/30`, optional UTC `from`, `to`, `interval=1m/1h/1d`; unsupported old range rejected |
| GET `/markets/{id}/fee-policy` | Reviewed active document or UNKNOWN |
| POST `/markets/{id}/fee-policy` | Versioned market-specific evidence/formula/rate/rounding/expiry |
| GET `/matches/{id}` | Classification, review, differences, current hashes, optional replication matrix |
| POST `/matches/{id}/review` | Action/reason/evidence/current hashes; conflict on changed rules |
| GET `/matches/{id}/reviews` | Audit history |
| POST `/matches/synthetic` | Explicit target/basket/state matrix; validates disjoint exhaustive replication |
| GET `/comparisons/{id}` | Linked market/book/history/rule read model; provider/local history selector |
| GET `/opportunities` | limit/offset, q, class/review, max_age, quantity, min_capacity, min_net_edge; retain ineligible reasons |
| POST `/simulations` | Units or paired budget, direction, manual fee assumption, costs/stress, currency basis, net threshold |
| GET/POST `/watchlists`, PUT/DELETE `/watchlists/{id}` | Persistent named match lists |
| GET/POST `/alerts`, PUT/DELETE `/alerts/{id}` | In-app rules/events; verified inputs only, cooldown deduplication |
| GET `/workspaces`, GET/PUT/DELETE `/workspaces/{id}` | Versioned layout/selection state; PUT creates or updates |
| GET `/health/live`, `/health/ready` | Process health, DB availability, worker heartbeat, thresholds/capabilities |

`GET /search` can import a URL and persist public catalog data; it never causes financial actions. The local deployment has no authentication and must not be publicly exposed.

## Browser WebSocket

`WS /api/v1/stream`, request `{action:'subscribe'|'unsubscribe'|'resync', topic}`. Topics: `comparison:<match-id>`, `book:<market-id>`, `opportunities:all`. At most 12 topics/client. Envelope:

```json
{"schema_version":1,"type":"snapshot","topic":"book:market_id","sequence":2,"sent_at":"2026-09-19T00:00:00+00:00","data":{}}
```

Types are snapshot, delta, status, heartbeat, error. The current gateway emits coalesced full snapshots/status/heartbeat; it does not promise upstream exchange deltas. Sequence is per browser connection, not fabricated exchange sequencing. Client discards duplicates, requests resync after a gap, reconnects with exponential jitter, and resubscribes. The gateway has no unbounded client queues; sends time out after five seconds. Snapshot cadence is two seconds; source polling stays at its own budget.
