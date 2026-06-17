"""Saga — coordinated multi-step operation with compensation.

Each step is a ``(forward_coroutine, compensator_coroutine)`` pair. If any
step raises, all already-completed steps are compensated in reverse order.

Usage::

    saga = Saga("ingest_paper")
    saga.step(upload_to_minio(key, data), delete_from_minio(key))
    saga.step(index_in_qdrant(paper_id, chunks), delete_from_qdrant(paper_id))
    saga.step(persist_to_db(paper), noop())
    await saga.run()
"""
from __future__ import annotations

from collections.abc import Awaitable, Coroutine
from typing import Any

from app.core.logging import get_logger

logger = get_logger("noesis.saga")


class SagaFailed(Exception):
    def __init__(self, saga_name: str, step: int, cause: Exception) -> None:
        super().__init__(f"Saga '{saga_name}' failed at step {step}: {cause}")
        self.step = step
        self.cause = cause


class Saga:
    def __init__(self, name: str) -> None:
        self.name = name
        self._steps: list[tuple[Awaitable[Any], Awaitable[Any] | None]] = []

    def step(
        self,
        forward: Awaitable[Any],
        compensate: Awaitable[Any] | None = None,
    ) -> "Saga":
        self._steps.append((forward, compensate))
        return self

    async def run(self) -> list[Any]:
        completed: list[int] = []
        results: list[Any] = []
        for i, (forward, _) in enumerate(self._steps):
            try:
                result = await forward
                results.append(result)
                completed.append(i)
                logger.debug("saga_step_ok", saga=self.name, step=i)
            except Exception as exc:
                logger.warning("saga_step_failed", saga=self.name, step=i, error=str(exc))
                await self._compensate(completed)
                raise SagaFailed(self.name, i, exc) from exc
        return results

    async def _compensate(self, completed: list[int]) -> None:
        for i in reversed(completed):
            _, compensate = self._steps[i]
            if compensate is None:
                continue
            try:
                await compensate
                logger.debug("saga_compensated", saga=self.name, step=i)
            except Exception as exc:
                logger.error("saga_compensation_failed", saga=self.name, step=i, error=str(exc))
