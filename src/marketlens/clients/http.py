import asyncio
import time

import httpx


class SourceError(Exception):
    pass


class PublicHTTP:
    """Bounded retries, concurrency, and short cache; no credentials or arbitrary URLs."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=20, headers={"User-Agent": "MarketLens/0.1"})
        self.cache = {}
        self.gate = asyncio.Semaphore(8)

    async def get(self, base, path, params=None, ttl=15):
        key = (base, path, str(sorted((params or {}).items())))
        cached = self.cache.get(key)
        if cached and cached[0] > time.monotonic():
            return cached[1]
        async with self.gate:
            for attempt in range(3):
                try:
                    response = await self.client.get(base + path, params=params)
                    if response.status_code == 429 or response.status_code >= 500:
                        if attempt < 2:
                            await asyncio.sleep(0.5 * 2**attempt)
                            continue
                    response.raise_for_status()
                    data = response.json()
                    if len(self.cache) > 2000:
                        self.cache.clear()
                    self.cache[key] = (time.monotonic() + ttl, data)
                    return data
                except (httpx.HTTPError, ValueError) as exc:
                    raise SourceError(f"{base}{path}: {type(exc).__name__}: {exc}") from exc

    async def close(self):
        await self.client.aclose()
