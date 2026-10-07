from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


class ContainerStatus(BaseModel):
    service: str
    container_name: str
    status: Literal["running", "healthy", "stopped", "restarting", "degraded"]
    image: str
    ports: list[str]
    uptime: str
    cpu_percent: float = Field(ge=0.0, le=100.0, default=0.0)
    memory_mb: float = Field(ge=0.0, default=0.0)


class EnvironmentAuditItem(BaseModel):
    key: str
    value_masked: str
    is_secret: bool
    is_set: bool
    category: str
    description: str


class MigrationStatusItem(BaseModel):
    revision: str
    down_revision: str | None
    description: str
    is_applied: bool
    is_head: bool
    applied_at: str | None = None


class ServiceHealthProbe(BaseModel):
    service: str
    status: Literal["healthy", "degraded", "unhealthy"]
    latency_ms: float
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class SystemResources(BaseModel):
    cpu_percent: float
    memory_total_mb: float
    memory_used_mb: float
    memory_percent: float
    disk_total_gb: float
    disk_free_gb: float
    disk_used_percent: float


class DeploymentHealthCheckResponse(BaseModel):
    overall_status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: str
    environment: str
    probes: list[ServiceHealthProbe]
    system_resources: SystemResources


class DeploymentStatusResponse(BaseModel):
    app_name: str
    version: str
    environment: str
    debug_mode: bool
    uptime_seconds: float
    started_at: str
    git_commit: str
    git_branch: str
    python_version: str
    platform: str
    maintenance_mode: bool
    maintenance_reason: str | None
    current_migration_head: str
    migrations_applied_count: int
    containers: list[ContainerStatus]


class MaintenanceModeToggleRequest(BaseModel):
    enabled: bool
    reason: str | None = None


class MaintenanceModeResponse(BaseModel):
    maintenance_mode: bool
    reason: str | None
    updated_at: str
    toggled_by: str | None = None


class DeployVerificationReport(BaseModel):
    success: bool
    summary: str
    checks_passed: int
    checks_total: int
    details: list[dict[str, Any]]
