from __future__ import annotations

import secrets
import string
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AdminUser, CurrentUser, RequiredTenant
from app.core.exceptions import ConflictException, NotFoundException, PermissionDeniedException
from app.core.security import hash_password
from app.database import get_db
from app.models.organization import Organization, OrganizationTier
from app.models.user import User, UserRole
from app.schemas.organization import (
    MemberInviteRequest,
    OrganizationCreateRequest,
    OrganizationResponse,
    OrganizationUpdateRequest,
)
from app.schemas.user import UserResponse
from app.services.audit_service import record_audit_event

router = APIRouter(prefix="/organizations", tags=["Organizations & Tenants"])


@router.post("", response_model=OrganizationResponse, status_code=201)
async def create_organization(
    body: OrganizationCreateRequest,
    current_user: CurrentUser,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Organization:
    # Check slug uniqueness
    existing_slug = await db.execute(select(Organization).where(Organization.slug == body.slug))
    if existing_slug.scalar_one_or_none() is not None:
        raise ConflictException(f"Organization slug '{body.slug}' is already taken")

    org = Organization(
        name=body.name,
        slug=body.slug,
        tier=body.tier,
        settings=body.settings,
        is_active=True,
    )
    db.add(org)
    await db.flush()
    await db.refresh(org)

    # If the user has no organization or is setting up their tenant, attach them as org_admin
    if current_user.org_id is None or current_user.role == UserRole.candidate:
        current_user.org_id = org.id
        current_user.role = UserRole.org_admin
        db.add(current_user)
        await db.flush()

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    await record_audit_event(
        db=db,
        action="org.created",
        entity_type="organization",
        org_id=org.id,
        user_id=current_user.id,
        entity_id=str(org.id),
        ip_address=ip_address,
        user_agent=user_agent,
        payload={"slug": org.slug, "tier": org.tier.value},
    )

    return org


@router.get("/me", response_model=OrganizationResponse)
async def get_my_organization(
    tenant: RequiredTenant,
) -> Organization:
    return tenant


@router.patch("/me", response_model=OrganizationResponse)
async def update_my_organization(
    body: OrganizationUpdateRequest,
    admin_user: AdminUser,
    tenant: RequiredTenant,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Organization:
    if body.name is not None:
        tenant.name = body.name
    if body.tier is not None:
        tenant.tier = body.tier
    if body.is_active is not None:
        tenant.is_active = body.is_active
    if body.settings is not None:
        tenant.settings = {**tenant.settings, **body.settings}

    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    await record_audit_event(
        db=db,
        action="org.updated",
        entity_type="organization",
        org_id=tenant.id,
        user_id=admin_user.id,
        entity_id=str(tenant.id),
        ip_address=ip_address,
        user_agent=user_agent,
        payload={"updates": body.model_dump(exclude_unset=True)},
    )

    return tenant


@router.get("/me/members", response_model=list[UserResponse])
async def list_organization_members(
    tenant: RequiredTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[User]:
    result = await db.execute(
        select(User)
        .where(User.org_id == tenant.id)
        .order_by(User.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/me/invite", response_model=UserResponse, status_code=201)
async def invite_organization_member(
    body: MemberInviteRequest,
    admin_user: AdminUser,
    tenant: RequiredTenant,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    # Check if user already exists
    existing = await db.execute(select(User).where(User.email == body.email))
    user = existing.scalar_one_or_none()

    try:
        assigned_role = UserRole(body.role)
    except ValueError:
        assigned_role = UserRole.interviewer

    if user is not None:
        if user.org_id == tenant.id:
            raise ConflictException("User is already a member of this organization")
        elif user.org_id is not None:
            raise ConflictException("User is already associated with another organization")
        # Attach user to this tenant
        user.org_id = tenant.id
        user.role = assigned_role
        db.add(user)
    else:
        # Generate random password for invited member
        temp_pwd = "".join(secrets.choice(string.ascii_letters + string.digits + "!@#$%") for _ in range(16))
        user = User(
            email=body.email,
            full_name=body.full_name,
            hashed_password=hash_password(temp_pwd),
            org_id=tenant.id,
            role=assigned_role,
            is_active=True,
        )
        db.add(user)

    await db.flush()
    await db.refresh(user)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    await record_audit_event(
        db=db,
        action="org.member_added",
        entity_type="organization_member",
        org_id=tenant.id,
        user_id=admin_user.id,
        entity_id=str(user.id),
        ip_address=ip_address,
        user_agent=user_agent,
        payload={"member_email": user.email, "role": user.role.value},
    )

    return user
