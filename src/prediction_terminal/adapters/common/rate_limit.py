import asyncio
import time


class Budget:
    def __init__(self, per_second):
        self.interval = 1 / per_second
        self.next = 0.0
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            await asyncio.sleep(max(0, self.next - time.monotonic()))
            self.next = time.monotonic() + self.interval
