from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiMeta(BaseModel):
    request_id: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    processing_ms: float | None = None


class ApiErrorDetail(BaseModel):
    code: str
    message: str
    details: Any = None
    request_id: str | None = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    error: ApiErrorDetail | None = None
    meta: ApiMeta = Field(default_factory=ApiMeta)


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(ApiResponse[list[T]], Generic[T]):
    pagination: PaginationMeta | None = None
