"""Opt-in public-data smoke. Makes no authenticated account calls or order requests."""

import argparse
import asyncio
import json
from pathlib import Path

from prediction_terminal.bootstrap import build
from prediction_terminal.domain.markets import utcnow


async def run():
    c = build()
    try:
        receipts = []
        for url in [
            "https://kalshi.com/markets/kxfeddecision/fed-meeting/kxfeddecision-26oct",
            "https://polymarket.com/event/fed-decision-in-october-20260617190323537",
        ]:
            result = await c.search.import_url(url)
            assert len(result["events"]) == 2 and len(result["matches"]) == 5, result
            comparison = await c.comparison.get(result["matches"][2]["id"])
            assert all(b["yes_asks"] or b["no_asks"] for b in comparison["books"])
            receipts.append(
                {
                    "url": url,
                    "events": len(result["events"]),
                    "matches": len(result["matches"]),
                    "histories": [(h["price_type"], len(h["points"])) for h in comparison["histories"]],
                    "errors": comparison["errors"],
                    "book_flags": [b["flags"] for b in comparison["books"]],
                }
            )
        receipt = {"verified_at": utcnow().isoformat(), "mode": "PUBLIC_READ_ONLY", "receipts": receipts}
        Path("data/smoke-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps(receipt, indent=2))
    finally:
        await c.transport.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", required=True)
    parser.parse_args()
    asyncio.run(run())
