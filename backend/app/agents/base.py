"""BaseOperator — shared foundation for all five reasoning operators.

Every operator node (Planner, Retriever, Analyst, Writer, Reviewer) inherits
from this class. The ``run`` coroutine wraps ``_execute`` in:
  1. A **bulkhead** that caps concurrent calls per operator
  2. A **circuit breaker** that trips after repeated failures
  3. OTel-style timing + structured logging
  4. Graceful error state: exceptions set ``failed_operator`` in the returned
     dict so the LangGraph router can short-circuit cleanly.
"""
from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
from app.resilience.bulkhead import Bulkhead, BulkheadRejected
from app.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerOpen

logger = get_logger("noesis.operator")

# Default concurrency limits per operator (can be overridden via constructor).
_DEFAULT_LIMITS: dict[str, int] = {
    "planner": 20,
    "retriever": 10,
    "analyst": 5,
    "writer": 15,
    "reviewer": 15,
}


class BaseOperator:
    name: str = "base"

    def __init__(self) -> None:
        limit = _DEFAULT_LIMITS.get(self.name, 10)
        self._bulkhead = Bulkhead(self.name, limit=limit)
        self._breaker = CircuitBreaker(self.name)
        self._logger = logger.bind(operator=self.name)

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute this operator and return a partial-state update dict."""
        start = time.perf_counter()
        try:
            async with self._bulkhead.acquire():
                result = await self._breaker.call(self._execute(state))
        except BulkheadRejected as exc:
            self._logger.warning("bulkhead_rejected", error=str(exc))
            return {"failed_operator": self.name, "error_message": str(exc)}
        except CircuitBreakerOpen as exc:
            self._logger.warning("circuit_open", error=str(exc))
            return {"failed_operator": self.name, "error_message": str(exc)}
        except Exception as exc:
            self._logger.error("operator_failed", error=str(exc), exc_info=True)
            return {"failed_operator": self.name, "error_message": str(exc)}
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._logger.info("operator_done", latency_ms=round(elapsed_ms, 1))

        return result

    async def _execute(self, state: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
