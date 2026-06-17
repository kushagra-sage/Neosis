"""Circuit breaker — prevents cascading failures.

State machine: CLOSED → OPEN → HALF_OPEN → CLOSED
- CLOSED  : normal; failures are counted
- OPEN    : all calls blocked for ``recovery_timeout`` seconds
- HALF_OPEN: one probe call allowed; success → CLOSED, failure → OPEN
"""
from __future__ import annotations

import asyncio
import time
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpen(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"Circuit breaker '{name}' is OPEN")
        self.name = name


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_successes: int = 2,
    ) -> None:
        self.name = name
        self._threshold = failure_threshold
        self._timeout = recovery_timeout
        self._required_successes = half_open_successes
        self._failures = 0
        self._successes_in_half_open = 0
        self._state = CircuitState.CLOSED
        self._opened_at: float | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def is_open(self) -> bool:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - (self._opened_at or 0) >= self._timeout:
                self._state = CircuitState.HALF_OPEN
                self._successes_in_half_open = 0
                return False
            return True
        return False

    async def call(self, coro):  # type: ignore[type-arg]
        async with self._lock:
            if self.is_open:
                raise CircuitBreakerOpen(self.name)

        try:
            result = await coro
            await self._on_success()
            return result
        except CircuitBreakerOpen:
            raise
        except Exception:
            await self._on_failure()
            raise

    async def _on_success(self) -> None:
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._successes_in_half_open += 1
                if self._successes_in_half_open >= self._required_successes:
                    self._state = CircuitState.CLOSED
                    self._failures = 0
            elif self._state == CircuitState.CLOSED:
                self._failures = max(0, self._failures - 1)

    async def _on_failure(self) -> None:
        async with self._lock:
            self._failures += 1
            if self._state == CircuitState.HALF_OPEN or self._failures >= self._threshold:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                self._failures = 0

    def metrics(self) -> dict:
        return {"name": self.name, "state": self._state.value, "failures": self._failures}
