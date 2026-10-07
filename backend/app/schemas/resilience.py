from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class CircuitBreakerStatus(BaseModel):
    name: str
    state: str  # "CLOSED", "OPEN", "HALF_OPEN"
    failure_count: int
    success_count: int
    failure_threshold: int
    recovery_timeout_s: float
    total_calls: int
    total_failures: int
    total_fallbacks: int
    bulkhead_concurrency_limit: int
    bulkhead_active_calls: int
    last_failure_time: str | None
    last_state_change: str


class CircuitBreakerRegistryResponse(BaseModel):
    circuit_breakers: list[CircuitBreakerStatus]


class CircuitBreakerResetResponse(BaseModel):
    name: str
    previous_state: str
    current_state: str
    message: str
