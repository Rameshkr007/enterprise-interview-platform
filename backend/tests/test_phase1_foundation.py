import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from uuid import uuid4
from sqlalchemy import select

from app.config import get_settings
from app.core.redis import check_redis_health
from app.core.security import hash_password, verify_password
from app.database import AsyncSessionLocal, check_database_health
from app.models.organization import Organization, OrganizationTier
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.common import ApiResponse, ApiErrorDetail


async def test_configuration_loading():
    settings = get_settings()
    assert settings.APP_NAME == "Enterprise Interview Platform"
    assert settings.API_PREFIX == "/api/v1"
    assert settings.OPENAI_EMBEDDING_DIMENSIONS == 3072
    print("[PASS] Configuration loaded and typed properly.")


async def test_bcrypt_security():
    raw_pwd = "EnterprisePassword2026!"
    hashed = hash_password(raw_pwd)
    assert hashed != raw_pwd
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    print("[PASS] Direct bcrypt security verification passed.")


async def test_api_response_envelope():
    response = ApiResponse[dict](
        success=True,
        data={"user": "alex"},
        error=None,
    )
    dumped = response.model_dump()
    assert dumped["success"] is True
    assert dumped["data"]["user"] == "alex"
    assert "timestamp" in dumped["meta"]

    err_response = ApiResponse[None](
        success=False,
        error=ApiErrorDetail(code="TENANT_NOT_FOUND", message="Organization does not exist"),
    )
    err_dumped = err_response.model_dump()
    assert err_dumped["success"] is False
    assert err_dumped["error"]["code"] == "TENANT_NOT_FOUND"
    print("[PASS] API Response and Error envelopes validated.")


async def test_models_and_database_persistence():
    db_ok = await check_database_health()
    if not db_ok:
        print("[SKIP] PostgreSQL not connected in this test run.")
        return

    async with AsyncSessionLocal() as session:
        # Create test Organization
        slug = f"acme-corp-{uuid4().hex[:6]}"
        org = Organization(
            name="Acme Corporation",
            slug=slug,
            tier=OrganizationTier.enterprise,
            settings={"sso_enabled": True, "allowed_domains": ["acme.com"]},
        )
        session.add(org)
        await session.flush()
        assert org.id is not None

        # Create test User under Organization
        test_email = f"lead-{uuid4().hex[:6]}@acme.com"
        user = User(
            org_id=org.id,
            email=test_email,
            full_name="Jane Doe",
            hashed_password=hash_password("Pass1234!"),
            role=UserRole.org_admin,
        )
        session.add(user)
        await session.flush()
        assert user.id is not None
        assert user.org_id == org.id

        # Create test AuditLog
        log_entry = AuditLog(
            org_id=org.id,
            user_id=user.id,
            action="ORGANIZATION_INITIALIZED",
            entity_type="organization",
            entity_id=str(org.id),
            ip_address="127.0.0.1",
            payload={"tier": "enterprise"},
        )
        session.add(log_entry)
        await session.flush()
        assert log_entry.id is not None

        # Verify query back
        res = await session.execute(select(Organization).where(Organization.id == org.id))
        fetched_org = res.scalar_one()
        assert fetched_org.name == "Acme Corporation"
        assert fetched_org.tier == OrganizationTier.enterprise

        await session.rollback()  # Clean rollback for test hygiene
    print("[PASS] Multi-tenant models and persistence verified successfully.")


async def run_all():
    print("=== RUNNING PHASE 1 FOUNDATION TESTS ===")
    await test_configuration_loading()
    await test_bcrypt_security()
    await test_api_response_envelope()
    await test_models_and_database_persistence()
    print("=== ALL PHASE 1 FOUNDATION TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(run_all())
