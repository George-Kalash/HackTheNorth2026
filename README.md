# MarketLens

A Python dashboard for finding and comparing Kalshi and Polymarket contracts. Search topics or event URLs, choose related outcomes, inspect current implied probabilities and historical prices, and estimate the conditional cost of buying opposing sides across venues.

## Run locally

Python 3.11+:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn marketlens.app:app --reload
```

Open http://127.0.0.1:8000 and click **October Fed example**. Public reads require no API key. No trading credentials or order execution are implemented.

## Project layout

```text
pyproject.toml                 Package, dependencies and test configuration
src/marketlens/
  app.py                       FastAPI routes and application lifecycle
  models.py                    Normalized events and binary contracts
  matching.py                  Explainable candidate ranking
  opportunities.py             Opposing-side cost and edge calculations
  clients/
    http.py                    Shared HTTP client, cache and bounded retries
    kalshi.py                  Events, series discovery and candle history
    polymarket.py              Gamma discovery, CLOB quotes, price history
  static/
    index.html                 Dashboard shell
    styles.css                 Responsive styles
    app.js                     Search, comparison and SVG charts
tests/                         Offline adapter and financial-math tests
docs/methodology.md             Sources, definitions and limitations
```

## Workflow

1. Search a topic such as `Fed decision October 2026`, or paste a platform event URL. Results are grouped by platform; select an event from each.
2. Load outcomes. Suggested pairs are text-based candidates, not verified equivalent contracts. You can manually select any supported binary outcome.
3. Compare quotes and 1-day, 7-day or 30-day histories. Hover chart observations or open the history table for exact values.
4. Inspect settlement rules and closing times; enter a fee and slippage allowance in cents per paired position.
5. Optionally refresh every 30 seconds. Unavailable upstream data is surfaced explicitly; no fabricated sample prices appear in the app.

## Development

```bash
pytest
ruff check src tests
```

API documentation: http://127.0.0.1:8000/docs. Endpoints: `GET /api/search`, `POST /api/events`, `POST /api/compare`, `GET /api/health`.

This is a local research MVP. Search is bounded, matching is heuristic, quotes are asynchronous, and actual fees and full book depth are not modeled. Do not expose the development server publicly without adding access controls and request rate limits. See [methodology](docs/methodology.md).
