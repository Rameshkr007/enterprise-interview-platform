from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.dependencies import CurrentUser
from app.core.exceptions import AuthenticationException, ConflictException
from app.core.security import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    is_token_blacklisted,
    verify_password,
)
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    LogoutRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.audit_service import record_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: UserRegisterRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise ConflictException("Email is already registered")

    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        org_id=body.org_id,
        role=body.role if isinstance(body.role, UserRole) else UserRole(body.role),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    await record_audit_event(
        db=db,
        action="user.registered",
        entity_type="user",
        org_id=user.org_id,
        user_id=user.id,
        entity_id=str(user.id),
        ip_address=ip_address,
        user_agent=user_agent,
        payload={"email": user.email, "role": user.role.value},
    )

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    body: UserLoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == body.email, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise AuthenticationException("Invalid email or password")

    access_token = create_access_token(user.id, user.role.value, user.org_id)
    refresh_token = create_refresh_token(user.id, user.org_id)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    await record_audit_event(
        db=db,
        action="user.login",
        entity_type="user",
        org_id=user.org_id,
        user_id=user.id,
        entity_id=str(user.id),
        ip_address=ip_address,
        user_agent=user_agent,
        payload={"email": user.email},
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: TokenRefreshRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    payload = decode_refresh_token(body.refresh_token)

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise AuthenticationException("Refresh token has been revoked")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationException("Invalid token payload")

    user_id = UUID(user_id_str)
    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthenticationException("User account not found or disabled")

    # Invalidate the old refresh token (Token Rotation)
    await blacklist_token(body.refresh_token)

    new_access_token = create_access_token(user.id, user.role.value, user.org_id)
    new_refresh_token = create_refresh_token(user.id, user.org_id)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    await record_audit_event(
        db=db,
        action="user.token_refreshed",
        entity_type="user",
        org_id=user.org_id,
        user_id=user.id,
        entity_id=str(user.id),
        ip_address=ip_address,
        user_agent=user_agent,
        payload={"rotated_jti": jti},
    )

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", status_code=200)
async def logout(
    request: Request,
    body: LogoutRequest | None = None,
    authorization: Annotated[str | None, Header()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict[str, str]:
    revoked_count = 0

    # Revoke access token from Authorization header if present
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        await blacklist_token(token)
        revoked_count += 1

    # Revoke refresh token if supplied in body
    if body and body.refresh_token:
        await blacklist_token(body.refresh_token)
        revoked_count += 1

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    if db:
        await record_audit_event(
            db=db,
            action="user.logout",
            entity_type="session",
            ip_address=ip_address,
            user_agent=user_agent,
            payload={"revoked_tokens": revoked_count},
        )

    return {"status": "logged_out", "revoked_tokens": str(revoked_count)}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> User:
    return current_user
