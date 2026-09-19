"""Export a small dated public payload sample from the local raw archive; no network."""

import json
from pathlib import Path

from prediction_terminal.bootstrap import build


def main():
    c = build()
    rows = c.repo.list("raw_inputs", 1000)
    choices = {}
    for row in rows:
        source = row["source"]
        key = (
            "kalshi_book"
            if "/orderbook" in source
            else "poly_book"
            if "clob.polymarket.com/book" in source
            else "kalshi_event"
            if "/events/KX" in source
            else "poly_event"
            if "gamma-api.polymarket.com/events" in source
            else None
        )
        if key and key not in choices:
            choices[key] = row
    for key, row in choices.items():
        Path("tests/fixtures/recorded", key + ".json").write_text(json.dumps(row, indent=2) + "\n")
    print("Recorded", ", ".join(choices))


if __name__ == "__main__":
    main()
