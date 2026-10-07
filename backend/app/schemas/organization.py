from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.organization import OrganizationTier


class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern="^[a-z0-9-]+$")
    tier: OrganizationTier = OrganizationTier.free
    settings: dict = Field(default_factory=dict)


class OrganizationUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    tier: OrganizationTier | None = None
    is_active: bool | None = None
    settings: dict | None = None


class MemberInviteRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=320)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: str = Field(default="interviewer")


class OrganizationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    name: str
    slug: str
    tier: OrganizationTier
    is_active: bool
    settings: dict
    created_at: datetime
    updated_at: datetime
