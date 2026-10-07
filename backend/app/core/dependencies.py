from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationException, PermissionDeniedException, NotFoundException
from app.core.security import decode_access_token, is_token_blacklisted
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User, UserRole

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise AuthenticationException("No authorization token provided")

    token = credentials.credentials
    payload = decode_access_token(token)

    # Check revocation blacklist in Redis
    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise AuthenticationException("Token has been revoked")

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise AuthenticationException("Token subject is missing")

    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthenticationException("User not found or deactivated")
    return user


async def get_current_tenant(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Organization | None:
    if not current_user.org_id:
        return None

    result = await db.execute(
        select(Organization).where(Organization.id == current_user.org_id, Organization.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def require_tenant(
    tenant: Annotated[Organization | None, Depends(get_current_tenant)],
) -> Organization:
    if tenant is None:
        raise PermissionDeniedException("An active organization context is required for this action")
    return tenant


def require_role(*roles: UserRole | list[UserRole]):
    flattened_roles: list[UserRole] = []
    for r in roles:
        if isinstance(r, (list, tuple, set)):
            flattened_roles.extend(r)
        else:
            flattened_roles.append(r)

    async def _checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in flattened_roles:
            raise PermissionDeniedException(
                f"Role '{current_user.role}' is not permitted. Required: {[r.value if hasattr(r, 'value') else str(r) for r in flattened_roles]}"
            )
        return current_user

    return _checker


RequireRole = require_role


# Convenience type aliases
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentTenant = Annotated[Organization | None, Depends(get_current_tenant)]
RequiredTenant = Annotated[Organization, Depends(require_tenant)]

# Enterprise Role Guards
InterviewerUser = Annotated[
    User, Depends(require_role(UserRole.interviewer, UserRole.recruiter, UserRole.org_admin, UserRole.platform_admin, UserRole.admin))
]
RecruiterUser = Annotated[
    User, Depends(require_role(UserRole.recruiter, UserRole.org_admin, UserRole.platform_admin, UserRole.admin))
]
AdminUser = Annotated[
    User, Depends(require_role(UserRole.org_admin, UserRole.platform_admin, UserRole.admin))
]
PlatformAdminUser = Annotated[
    User, Depends(require_role(UserRole.platform_admin))
]
