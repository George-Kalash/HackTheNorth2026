import asyncio
import random
import time
from collections import defaultdict
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx

from prediction_terminal.domain.errors import SourceUnavailable

from .rate_limit import Budget

ALLOWED = {
    "https://api.elections.kalshi.com/trade-api/v2",
    "https://gamma-api.polymarket.com",
    "https://clob.polymarket.com",
    "https://data-api.polymarket.com",
}


class Transport:
    def __init__(self, settings, archive, metrics):
        self.client = httpx.AsyncClient(
            timeout=20, follow_redirects=False, headers={"User-Agent": "ParallaxTerminal/0.2 public-research"}
        )
        self.budgets = defaultdict(lambda: Budget(settings.requests_per_second))
        self.gate = asyncio.Semaphore(6)
        self.cache = {}
        self.archive = archive
        self.metrics = metrics

    async def get(self, base, path, params=None, ttl=0):
        if base not in ALLOWED or not path.startswith("/") or ".." in path:
            raise SourceUnavailable("Disallowed upstream path")
        key = (base, path, str(sorted((params or {}).items())))
        old = self.cache.get(key)
        if old and old[0] > time.monotonic():
            return old[1]
        for attempt in range(3):
            await self.budgets[base].acquire()
            started = time.monotonic()
            try:
                async with self.gate:
                    response = await self.client.get(base + path, params=params)
                self.metrics.latencies.append(time.monotonic() - started)
                self.metrics.counts[str(response.status_code)] += 1
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < 2:
                        retry = response.headers.get("Retry-After", "")
                        try:
                            delay = float(retry)
                        except ValueError:
                            try:
                                delay = (parsedate_to_datetime(retry) - datetime.now(UTC)).total_seconds()
                            except (ValueError, TypeError):
                                delay = 2**attempt + random.random()
                        if delay > 30:
                            raise SourceUnavailable(f"{base}: rate limited; retry after {delay:.0f}s", 429)
                        await asyncio.sleep(max(0, delay))
                        continue
                response.raise_for_status()
                data = response.json()
                self.archive.record(base + path + ("?" + str(params) if params else ""), data)
                if ttl:
                    if len(self.cache) > 1000:
                        self.cache.clear()
                    self.cache[key] = (time.monotonic() + ttl, data)
                return data
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt < 2:
                    await asyncio.sleep(2**attempt)
                    continue
                raise SourceUnavailable(f"{base}: {type(exc).__name__}") from exc
            except (httpx.HTTPStatusError, ValueError) as exc:
                status = (
                    404 if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 404 else 502
                )
                raise SourceUnavailable(
                    f"{base}{path}: HTTP {exc.response.status_code}"
                    if isinstance(exc, httpx.HTTPStatusError)
                    else "Invalid upstream JSON",
                    status,
                ) from exc
        raise SourceUnavailable("Retry budget exhausted")

    async def close(self):
        await self.client.aclose()

    def raw_id(self, data):
        import json
        from hashlib import sha256

        return sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
