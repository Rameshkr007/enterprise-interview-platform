from __future__ import annotations

import asyncio
import enum
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import structlog

from app.core.exceptions import CircuitBreakerOpenException

log = structlog.get_logger(__name__)


class CircuitState(str, enum.Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """Enterprise Circuit Breaker with bulkhead concurrency limiting,

    automatic half-open probing, and graceful degradation fallback.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_s: float = 30.0,
        success_threshold: int = 2,
        bulkhead_limit: int = 25,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = recovery_timeout_s
        self.success_threshold = success_threshold
        self.bulkhead_limit = bulkhead_limit

        self._state: CircuitState = CircuitState.CLOSED
        self._failure_count: int = 0
        self._success_count: int = 0
        self._half_open_successes: int = 0
        self._last_failure_time: float | None = None
        self._last_state_change: datetime = datetime.now(UTC)

        self._total_calls: int = 0
        self._total_failures: int = 0
        self._total_fallbacks: int = 0
        self._semaphore = asyncio.Semaphore(bulkhead_limit)
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        # Check if OPEN duration has passed recovery_timeout_s -> transition to HALF_OPEN
        if self._state == CircuitState.OPEN and self._last_failure_time is not None:
            if (time.monotonic() - self._last_failure_time) >= self.recovery_timeout_s:
                self._state = CircuitState.HALF_OPEN
                self._half_open_successes = 0
                self._last_state_change = datetime.now(UTC)
                log.info("circuit_breaker_half_open", name=self.name)
        return self._state

    async def call(
        self,
        func: Callable[..., Any],
        *args: Any,
        fallback: Callable[..., Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        current_state = self.state

        if current_state == CircuitState.OPEN:
            self._total_fallbacks += 1
            log.warning("circuit_breaker_open_fast_fail", name=self.name, has_fallback=bool(fallback))
            if fallback is not None:
                if asyncio.iscoroutinefunction(fallback):
                    return await fallback(*args, **kwargs)
                return fallback(*args, **kwargs)
            raise CircuitBreakerOpenException(
                f"Circuit breaker '{self.name}' is OPEN. Service unavailable."
            )

        # Bulkhead concurrency isolation
        async with self._semaphore:
            self._total_calls += 1
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                await self._on_success()
                return result

            except Exception as exc:
                self._total_failures += 1
                await self._on_failure(exc)
                if fallback is not None:
                    self._total_fallbacks += 1
                    log.info("circuit_breaker_fallback_invoked", name=self.name, error=str(exc))
                    if asyncio.iscoroutinefunction(fallback):
                        return await fallback(*args, **kwargs)
                    return fallback(*args, **kwargs)
                raise

    async def _on_success(self) -> None:
        async with self._lock:
            self._success_count += 1
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_successes += 1
                if self._half_open_successes >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._half_open_successes = 0
                    self._last_state_change = datetime.now(UTC)
                    log.info("circuit_breaker_recovered_closed", name=self.name)
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    async def _on_failure(self, exc: Exception) -> None:
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            log.warning(
                "circuit_breaker_recorded_failure",
                name=self.name,
                failures=self._failure_count,
                threshold=self.failure_threshold,
                error=str(exc),
            )

            if self._state == CircuitState.HALF_OPEN or self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._last_state_change = datetime.now(UTC)
                log.error("circuit_breaker_tripped_open", name=self.name, total_failures=self._total_failures)

    def trip(self) -> None:
        """Forcibly trip breaker for operational drills or testing."""
        self._state = CircuitState.OPEN
        self._last_failure_time = time.monotonic()
        self._last_state_change = datetime.now(UTC)
        log.warning("circuit_breaker_forcibly_tripped", name=self.name)

    def reset(self) -> None:
        """Manually reset breaker to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._half_open_successes = 0
        self._last_failure_time = None
        self._last_state_change = datetime.now(UTC)
        log.info("circuit_breaker_manually_reset", name=self.name)

    def get_status(self) -> dict[str, Any]:
        state = self.state
        active_in_bulkhead = self.bulkhead_limit - self._semaphore._value
        return {
            "name": self.name,
            "state": state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_s": self.recovery_timeout_s,
            "total_calls": self._total_calls,
            "total_failures": self._total_failures,
            "total_fallbacks": self._total_fallbacks,
            "bulkhead_concurrency_limit": self.bulkhead_limit,
            "bulkhead_active_calls": max(active_in_bulkhead, 0),
            "last_failure_time": (
                datetime.fromtimestamp(self._last_failure_time, tz=UTC).isoformat()
                if self._last_failure_time
                else None
            ),
            "last_state_change": self._last_state_change.isoformat(),
        }


class CircuitBreakerRegistry:
    """Central singleton registry of circuit breakers across the platform."""

    _instance: CircuitBreakerRegistry | None = None

    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}
        # Pre-register primary subsystems with specialized resilience profiles
        self.register(CircuitBreaker("llm_reasoning", failure_threshold=3, recovery_timeout_s=20.0, bulkhead_limit=15))
        self.register(CircuitBreaker("llm_fast", failure_threshold=5, recovery_timeout_s=15.0, bulkhead_limit=30))
        self.register(CircuitBreaker("whisper_service", failure_threshold=4, recovery_timeout_s=30.0, bulkhead_limit=10))
        self.register(CircuitBreaker("code_sandbox", failure_threshold=3, recovery_timeout_s=25.0, bulkhead_limit=10))
        self.register(CircuitBreaker("cloud_storage", failure_threshold=5, recovery_timeout_s=20.0, bulkhead_limit=25))

    @classmethod
    def get_instance(cls) -> CircuitBreakerRegistry:
        if cls._instance is None:
            cls._instance = CircuitBreakerRegistry()
        return cls._instance

    def register(self, breaker: CircuitBreaker) -> None:
        self._breakers[breaker.name] = breaker

    def get(self, name: str) -> CircuitBreaker:
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name)
        return self._breakers[name]

    def all_breakers(self) -> list[CircuitBreaker]:
        return list(self._breakers.values())


def get_circuit_breaker(name: str) -> CircuitBreaker:
    return CircuitBreakerRegistry.get_instance().get(name)
