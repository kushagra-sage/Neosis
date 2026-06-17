"""Bulkhead — limits concurrent executions per operator.

Uses ``asyncio.Semaphore`` to cap inflight calls. Callers that cannot acquire
within ``timeout`` seconds receive a ``BulkheadRejected`` error.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager


class BulkheadRejected(Exception):
    def __init__(self, name: str, limit: int) -> None:
        super().__init__(f"Bulkhead '{name}' saturated (limit={limit})")
        self.name = name
        self.limit = limit


class Bulkhead:
    def __init__(self, name: str, limit: int = 10, timeout: float = 5.0) -> None:
        self.name = name
        self.limit = limit
        self._timeout = timeout
        self._sem = asyncio.Semaphore(limit)
        self._active = 0

    @property
    def active(self) -> int:
        return self._active

    @asynccontextmanager
    async def acquire(self):  # type: ignore[override]
        acquired = False
        try:
            acquired = await asyncio.wait_for(self._sem.acquire(), timeout=self._timeout)
        except asyncio.TimeoutError:
            raise BulkheadRejected(self.name, self.limit)
        self._active += 1
        try:
            yield
        finally:
            self._active -= 1
            self._sem.release()

    def metrics(self) -> dict:
        return {"name": self.name, "active": self._active, "limit": self.limit}
