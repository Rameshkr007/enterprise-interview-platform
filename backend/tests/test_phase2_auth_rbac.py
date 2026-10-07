import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from uuid import uuid4
import httpx
from httpx import ASGITransport
from sqlalchemy import select

from app.database import AsyncSessionLocal, check_database_health
from app.core.redis import check_redis_health, close_redis_pool
from app.main import app
from app.models.audit_log import AuditLog
from app.models.organization import Organization
from app.models.user import User


async def run_tests():
    print("=== RUNNING PHASE 2 AUTH, TENANCY & RBAC TESTS ===")

    db_ok = await check_database_health()
    redis_ok = await check_redis_health()
    if not db_ok or not redis_ok:
        print(f"[FAIL] Pre-requisite checks failed: DB={db_ok}, Redis={redis_ok}")
        sys.exit(1)

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # ── Test 1: User Registration & Audit Logging ────────────────────────
        unique_suffix = uuid4().hex[:8]
        user1_email = f"candidate_{unique_suffix}@platform.ai"
        user1_pwd = "SecurePassword123!"

        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": user1_email,
                "full_name": "Test Candidate",
                "password": user1_pwd,
            },
        )
        assert reg_res.status_code == 201, f"Reg failed: {reg_res.text}"
        user1_data = reg_res.json()
        assert user1_data["email"] == user1_email
        assert user1_data["role"] == "candidate"
        print("[PASS] 1. User registration succeeded.")

        # Verify audit log was created for registration
        async with AsyncSessionLocal() as session:
            stmt = select(AuditLog).where(
                AuditLog.action == "user.registered",
                AuditLog.entity_id == user1_data["id"]
            )
            audit_entry = (await session.execute(stmt)).scalar_one_or_none()
            assert audit_entry is not None, "Audit log entry for registration not found"
        print("[PASS] 2. Audit log entry recorded for registration.")

        # ── Test 2: User Login & Claims ───────────────────────────────────────
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": user1_email, "password": user1_pwd},
        )
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        tokens = login_res.json()
        access_token_1 = tokens["access_token"]
        refresh_token_1 = tokens["refresh_token"]
        assert access_token_1 and refresh_token_1
        print("[PASS] 3. Login issued access and refresh tokens.")

        # Access /auth/me with Bearer token
        me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token_1}"},
        )
        assert me_res.status_code == 200
        assert me_res.json()["email"] == user1_email
        print("[PASS] 4. Authenticated request to /auth/me verified.")

        # ── Test 3: Token Refresh & Single-Use Rotation ──────────────────────
        refresh_res = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token_1},
        )
        assert refresh_res.status_code == 200, f"Refresh failed: {refresh_res.text}"
        rotated_tokens = refresh_res.json()
        access_token_2 = rotated_tokens["access_token"]
        refresh_token_2 = rotated_tokens["refresh_token"]
        assert access_token_2 != access_token_1
        assert refresh_token_2 != refresh_token_1
        print("[PASS] 5. Token rotation issued fresh token pair.")

        # Attempt to reuse old refresh token (must be blacklisted)
        reuse_res = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token_1},
        )
        assert reuse_res.status_code == 401, f"Expected 401 for replayed refresh token, got {reuse_res.status_code}"
        print("[PASS] 6. Replayed refresh token was rejected (revocation verified).")

        # ── Test 4: Logout & Access Token Blacklisting ───────────────────────
        logout_res = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token_2}"},
            json={"refresh_token": refresh_token_2},
        )
        assert logout_res.status_code == 200
        print("[PASS] 7. Logout endpoint blacklisted both active tokens.")

        # Attempt to use the logged-out access token
        revoked_me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token_2}"},
        )
        assert revoked_me_res.status_code == 401, f"Expected 401 for revoked access token, got {revoked_me_res.status_code}"
        print("[PASS] 8. Revoked access token was denied access immediately.")

        # ── Test 5: Organization Creation & Auto Tenant Binding ──────────────
        admin_email = f"admin_{unique_suffix}@platform.ai"
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": admin_email,
                "full_name": "Org Admin Lead",
                "password": user1_pwd,
            },
        )
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": admin_email, "password": user1_pwd},
        )
        admin_token = admin_login.json()["access_token"]

        org_slug = f"tenant-{unique_suffix}"
        create_org_res = await client.post(
            "/api/v1/organizations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Acme Global Enterprise",
                "slug": org_slug,
                "tier": "growth",
                "settings": {"max_interviewers": 25},
            },
        )
        assert create_org_res.status_code == 201, f"Org create failed: {create_org_res.text}"
        org_data = create_org_res.json()
        assert org_data["slug"] == org_slug
        print("[PASS] 9. Organization created and tenant context established.")

        # Verify admin user was upgraded to org_admin and linked to org
        admin_me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_me_res.json()["role"] == "org_admin"
        assert admin_me_res.json()["org_id"] == org_data["id"]
        print("[PASS] 10. User promoted to org_admin with tenant ID bound.")

        # Check tenant endpoint /organizations/me
        org_me_res = await client.get(
            "/api/v1/organizations/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert org_me_res.status_code == 200
        assert org_me_res.json()["name"] == "Acme Global Enterprise"
        print("[PASS] 11. Scoped /organizations/me verified.")

        # ── Test 6: Enterprise Role-Based Access Control (RBAC) ───────────────
        # Candidate attempting org update
        cand_login = await client.post(
            "/api/v1/auth/login",
            json={"email": user1_email, "password": user1_pwd},
        )
        cand_token = cand_login.json()["access_token"]

        forbidden_res = await client.patch(
            "/api/v1/organizations/me",
            headers={"Authorization": f"Bearer {cand_token}"},
            json={"name": "Hacked Org Name"},
        )
        assert forbidden_res.status_code in (401, 403), f"Expected 403/401 for candidate on admin route, got {forbidden_res.status_code}"
        print(f"[PASS] 12. Candidate denied access to organization admin endpoint (Status {forbidden_res.status_code}).")

        # Admin user updating organization
        update_org_res = await client.patch(
            "/api/v1/organizations/me",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Acme Global Enterprise - Updated"},
        )
        assert update_org_res.status_code == 200
        assert update_org_res.json()["name"] == "Acme Global Enterprise - Updated"
        print("[PASS] 13. Admin successfully updated organization.")

        # ── Test 7: Organization Member Invites & Directory ───────────────────
        invite_email = f"interviewer_{unique_suffix}@platform.ai"
        invite_res = await client.post(
            "/api/v1/organizations/me/invite",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": invite_email,
                "full_name": "Invited Senior Interviewer",
                "role": "interviewer",
            },
        )
        assert invite_res.status_code == 201, f"Invite failed: {invite_res.text}"
        invited_member = invite_res.json()
        assert invited_member["email"] == invite_email
        assert invited_member["role"] == "interviewer"
        assert invited_member["org_id"] == org_data["id"]
        print("[PASS] 14. Member invited into tenant with interviewer role.")

        members_res = await client.get(
            "/api/v1/organizations/me/members",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert members_res.status_code == 200
        member_emails = [m["email"] for m in members_res.json()]
        assert admin_email in member_emails
        assert invite_email in member_emails
        print("[PASS] 15. Organization members list retrieved and validated.")

    await close_redis_pool()
    print("=== ALL PHASE 2 AUTH, TENANCY & RBAC TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(run_tests())
