from __future__ import annotations

from typing import Annotated
import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, RequireRole
from app.core.exceptions import NotFoundException
from app.database import get_db
from app.models.user import UserRole
from app.schemas.resilience import (
    CircuitBreakerRegistryResponse,
    CircuitBreakerResetResponse,
    CircuitBreakerStatus,
)
from app.services.audit_service import record_audit_event
from app.services.circuit_breaker import CircuitBreakerRegistry

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/resilience", tags=["Resilience & Circuit Breakers"])


@router.get(
    "/circuit-breakers",
    response_model=CircuitBreakerRegistryResponse,
    dependencies=[Depends(RequireRole([UserRole.org_admin, UserRole.platform_admin, UserRole.admin]))],
)
async def list_circuit_breakers() -> CircuitBreakerRegistryResponse:
    """Returns real-time telemetry and state of all system circuit breakers and bulkheads."""
    registry = CircuitBreakerRegistry.get_instance()
    breakers = [CircuitBreakerStatus(**b.get_status()) for b in registry.all_breakers()]
    return CircuitBreakerRegistryResponse(circuit_breakers=breakers)


@router.post(
    "/circuit-breakers/{name}/reset",
    response_model=CircuitBreakerResetResponse,
    dependencies=[Depends(RequireRole([UserRole.org_admin, UserRole.platform_admin, UserRole.admin]))],
)
async def reset_circuit_breaker(
    name: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CircuitBreakerResetResponse:
    """Manually resets an OPEN or HALF_OPEN circuit breaker to CLOSED status."""
    registry = CircuitBreakerRegistry.get_instance()
    breaker = registry.get(name)
    prev = breaker.state.value
    breaker.reset()

    await record_audit_event(
        db=db,
        action="circuit_breaker.reset",
        entity_type="circuit_breaker",
        org_id=current_user.org_id,
        user_id=current_user.id,
        entity_id=name,
        payload={"previous_state": prev, "current_state": "CLOSED"},
    )

    return CircuitBreakerResetResponse(
        name=name,
        previous_state=prev,
        current_state="CLOSED",
        message=f"Circuit breaker '{name}' successfully reset to CLOSED state.",
    )


@router.post(
    "/circuit-breakers/{name}/trip",
    response_model=CircuitBreakerResetResponse,
    dependencies=[Depends(RequireRole([UserRole.platform_admin, UserRole.admin]))],
)
async def trip_circuit_breaker(
    name: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CircuitBreakerResetResponse:
    """Simulates an upstream outage by tripping a circuit breaker to OPEN state (Resilience Drill)."""
    registry = CircuitBreakerRegistry.get_instance()
    breaker = registry.get(name)
    prev = breaker.state.value
    breaker.trip()

    await record_audit_event(
        db=db,
        action="circuit_breaker.tripped",
        entity_type="circuit_breaker",
        org_id=current_user.org_id,
        user_id=current_user.id,
        entity_id=name,
        payload={"previous_state": prev, "current_state": "OPEN"},
    )

    return CircuitBreakerResetResponse(
        name=name,
        previous_state=prev,
        current_state="OPEN",
        message=f"Circuit breaker '{name}' has been forcibly tripped to OPEN state.",
    )
