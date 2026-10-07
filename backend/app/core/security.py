from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings
from app.core.exceptions import AuthenticationException
from app.core.redis import get_redis_client

settings = get_settings()


# ── Password Utilities ────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    pwd_bytes = plain.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        pwd_bytes = plain.encode("utf-8")[:72]
        return bcrypt.checkpw(pwd_bytes, hashed.encode("utf-8"))
    except Exception:
        return False


# ── JWT & Token Management ───────────────────────────────────────────────────
def _create_token(payload: dict[str, Any], expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    expire = now + expires_delta
    token_jti = str(uuid.uuid4())
    full_payload = {
        **payload,
        "jti": token_jti,
        "exp": expire,
        "iat": now,
        "nbf": now,
    }
    return jwt.encode(full_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: UUID, role: str, org_id: UUID | None = None) -> str:
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "org_id": str(org_id) if org_id else None,
        "type": "access",
    }
    return _create_token(
        payload,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: UUID, org_id: UUID | None = None) -> str:
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "org_id": str(org_id) if org_id else None,
        "type": "refresh",
    }
    return _create_token(
        payload,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        token_type = payload.get("type")
        if token_type != expected_type:
            raise AuthenticationException(f"Invalid token type: expected {expected_type}, got {token_type}")
        return payload
    except JWTError as exc:
        raise AuthenticationException("Token is invalid or expired") from exc


def decode_access_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type="access")


def decode_refresh_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type="refresh")


# ── Redis Token Blacklist & Revocation ────────────────────────────────────────
async def is_token_blacklisted(jti: str) -> bool:
    try:
        redis = get_redis_client()
        result = await redis.get(f"blacklist:token:{jti}")
        return result is not None
    except Exception:
        # Fail safe if Redis is temporarily unreachable
        return False


async def blacklist_token(token: str) -> None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or not exp:
            return

        now_ts = int(datetime.now(UTC).timestamp())
        ttl = max(exp - now_ts, 1)

        redis = get_redis_client()
        await redis.setex(f"blacklist:token:{jti}", ttl, "revoked")
    except Exception:
        pass
