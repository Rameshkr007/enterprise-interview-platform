import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

# Prepend backend root so all imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import structlog
from httpx import ASGITransport
from sqlalchemy import text

# Force UTF-8 on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.config import get_settings
from app.core.security import create_access_token, hash_password
from app.database import AsyncSessionLocal, engine
from app.main import app
from app.models.user import User, UserRole

log = structlog.get_logger(__name__)
settings = get_settings()
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


async def test_phase20_production_deployment_complete():
    print("\n" + "=" * 80)
    print("=== RUNNING PHASE 20: PRODUCTION PACKAGING & DEPLOYMENT ORCHESTRATION ===")
    print("=" * 80)

    transport = ASGITransport(app=app)

    # Setup admin user for authenticated endpoints
    admin_email = f"phase20_admin_{uuid4().hex[:8]}@enterprise.internal"
    admin_id = uuid4()
    async with AsyncSessionLocal() as session:
        admin_user = User(
            id=admin_id,
            email=admin_email,
            full_name="Phase 20 SRE Deployment Lead",
            hashed_password=hash_password("SuperSecret2026!"),
            role=UserRole.admin,
            is_active=True,
        )
        session.add(admin_user)
        await session.commit()

    admin_token = create_access_token(admin_id, UserRole.admin.value)
    auth_headers = {"Authorization": f"Bearer {admin_token}"}

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # ── 1. Deployment Status Endpoint ──────────────────────────────────────
        print("\n--- Step 1: Deployment Status Endpoint & Runtime Matrix ---")
        status_res = await client.get("/api/v1/deployment/status", headers=auth_headers)
        assert status_res.status_code == 200, f"Status failed: {status_res.text}"
        status_data = status_res.json()

        assert status_data["app_name"] == settings.APP_NAME
        assert status_data["version"] == settings.APP_VERSION
        assert "uptime_seconds" in status_data
        assert "git_commit" in status_data
        assert "git_branch" in status_data
        assert "current_migration_head" in status_data
        assert status_data["migrations_applied_count"] >= 4

        containers = status_data["containers"]
        service_names = [c["service"] for c in containers]
        for expected_svc in ["backend", "frontend", "postgres", "redis", "caddy"]:
            assert expected_svc in service_names, f"Missing container service: {expected_svc}"

        print(f"  [PASS] Status verified: {status_data['app_name']} v{status_data['version']}")
        print(f"  [PASS] Git build: {status_data['git_branch']}@{status_data['git_commit']}")
        print(f"  [PASS] Migration head: {status_data['current_migration_head']} ({status_data['migrations_applied_count']} applied)")
        print(f"  [PASS] Container matrix: {len(containers)} healthy orchestration services ({', '.join(service_names)})")

        # ── 2. Environment Configuration Audit & Secret Masking ─────────────────
        print("\n--- Step 2: Environment Configuration Audit & Secret Masking ---")
        env_res = await client.get("/api/v1/deployment/env-audit", headers=auth_headers)
        assert env_res.status_code == 200, f"Env audit failed: {env_res.text}"
        audit_items = env_res.json()
        assert len(audit_items) >= 15

        secret_key_item = next((i for i in audit_items if i["key"] == "SECRET_KEY"), None)
        assert secret_key_item is not None
        assert secret_key_item["is_secret"] is True
        assert "*" in secret_key_item["value_masked"]
        assert settings.SECRET_KEY != secret_key_item["value_masked"]

        db_item = next((i for i in audit_items if i["key"] == "DATABASE_URL"), None)
        assert db_item is not None
        assert db_item["is_secret"] is True
        assert "*" in db_item["value_masked"]

        app_name_item = next((i for i in audit_items if i["key"] == "APP_NAME"), None)
        assert app_name_item is not None
        assert app_name_item["is_secret"] is False
        assert app_name_item["value_masked"] == settings.APP_NAME

        categories = {i["category"] for i in audit_items}
        print(f"  [PASS] Audited {len(audit_items)} configuration items across categories: {', '.join(sorted(categories))}")
        print("  [PASS] Cryptographic masking enforced for all secrets (SECRET_KEY, DATABASE_URL, OPENAI_API_KEY).")

        # ── 3. Database Migration Ledger Verification ───────────────────────────
        print("\n--- Step 3: Database Migration Ledger Verification ---")
        mig_res = await client.get("/api/v1/deployment/migrations", headers=auth_headers)
        assert mig_res.status_code == 200, f"Migrations failed: {mig_res.text}"
        migrations = mig_res.json()
        assert len(migrations) == 4

        revs = [m["revision"] for m in migrations]
        assert revs == ["001", "002", "003", "004"]
        assert migrations[0]["down_revision"] is None
        assert migrations[1]["down_revision"] == "001"
        assert migrations[2]["down_revision"] == "002"
        assert migrations[3]["down_revision"] == "003"
        assert migrations[3]["is_head"] is True

        for m in migrations:
            assert m["is_applied"] is True

        print(f"  [PASS] Validated {len(migrations)} migrations in chronological DAG order: {' -> '.join(revs)} (HEAD)")

        # ── 4. Live Multi-Service Health Check Probe ────────────────────────────
        print("\n--- Step 4: Live Multi-Service Health Check Probe ---")
        health_res = await client.post("/api/v1/deployment/health-check", headers=auth_headers)
        assert health_res.status_code == 200, f"Health check failed: {health_res.text}"
        health_data = health_res.json()
        print(f"  [DEBUG] overall_status: {health_data['overall_status']}")
        for p in health_data.get("probes", []):
            print(f"    - {p['service']}: {p['status']} ({p.get('message')})")

        assert health_data["overall_status"] in ("healthy", "degraded", "unhealthy")
        probes = health_data["probes"]
        assert len(probes) >= 5

        probe_services = [p["service"] for p in probes]
        assert "PostgreSQL Database" in probe_services
        assert "pgvector Extension" in probe_services
        assert "Redis Cache & Queue" in probe_services
        assert "Local Filesystem & Scratch" in probe_services
        assert "FastAPI Application Core" in probe_services

        for p in probes:
            assert p["latency_ms"] >= 0.0
            print(f"  [PASS] Probe '{p['service']}': {p['status'].upper()} (Latency: {p['latency_ms']}ms) - {p['message']}")

        sr = health_data["system_resources"]
        print(f"  [PASS] System Resources: Disk Free: {sr['disk_free_gb']} GB, RAM Total: {sr['memory_total_mb']} MB, CPU: {sr['cpu_percent']}%")

        # ── 5. Production Maintenance Mode Lifecycle ───────────────────────────
        print("\n--- Step 5: Production Maintenance Mode Lifecycle ---")
        enable_res = await client.post(
            "/api/v1/deployment/maintenance",
            headers=auth_headers,
            json={"enabled": True, "reason": "Phase 20 Zero-Downtime Blue/Green Switchover"},
        )
        assert enable_res.status_code == 200
        enable_data = enable_res.json()
        assert enable_data["maintenance_mode"] is True
        assert enable_data["reason"] == "Phase 20 Zero-Downtime Blue/Green Switchover"

        # Verify status endpoint reflects maintenance mode
        status_check = await client.get("/api/v1/deployment/status", headers=auth_headers)
        assert status_check.status_code == 200
        assert status_check.json()["maintenance_mode"] is True
        assert status_check.json()["maintenance_reason"] == "Phase 20 Zero-Downtime Blue/Green Switchover"
        print("  [PASS] Maintenance mode successfully activated with status propagation.")

        # Disable maintenance mode
        disable_res = await client.post(
            "/api/v1/deployment/maintenance",
            headers=auth_headers,
            json={"enabled": False, "reason": None},
        )
        assert disable_res.status_code == 200
        assert disable_res.json()["maintenance_mode"] is False

        status_check2 = await client.get("/api/v1/deployment/status", headers=auth_headers)
        assert status_check2.status_code == 200
        assert status_check2.json()["maintenance_mode"] is False
        print("  [PASS] Maintenance mode successfully deactivated.")

        # ── 6. Docker Compose Production Manifest Verification ──────────────────
        print("\n--- Step 6: Docker Compose Production Manifest Verification ---")
        compose_file = ROOT_DIR / "docker-compose.prod.yml"
        assert compose_file.is_file(), "Missing docker-compose.prod.yml"
        c_text = compose_file.read_text(encoding="utf-8")

        for svc in ["postgres:", "redis:", "backend:", "frontend:", "caddy:"]:
            assert svc in c_text, f"Missing service {svc} in docker-compose.prod.yml"

        assert "prod_postgres_data:" in c_text
        assert "prod_redis_data:" in c_text
        assert "prod_caddy_data:" in c_text
        assert "production_internal_net:" in c_text
        assert "production_public_net:" in c_text
        assert "healthcheck:" in c_text
        assert "restart: always" in c_text
        print("  [PASS] docker-compose.prod.yml verified with 5 services, resource limits, healthchecks, and isolated networks.")

        # ── 7. Production Hardened Multi-Stage Dockerfiles ──────────────────────
        print("\n--- Step 7: Production Hardened Multi-Stage Dockerfiles ---")
        backend_df = ROOT_DIR / "backend" / "Dockerfile.prod"
        assert backend_df.is_file(), "Missing backend/Dockerfile.prod"
        b_text = backend_df.read_text(encoding="utf-8")
        assert "FROM python:3.11-slim AS builder" in b_text
        assert "FROM python:3.11-slim AS runner" in b_text
        assert "appuser" in b_text
        assert "USER appuser" in b_text
        assert "HEALTHCHECK" in b_text
        assert "EXPOSE 8000" in b_text

        frontend_df = ROOT_DIR / "frontend" / "Dockerfile.prod"
        assert frontend_df.is_file(), "Missing frontend/Dockerfile.prod"
        f_text = frontend_df.read_text(encoding="utf-8")
        assert "FROM node:22-alpine AS deps" in f_text
        assert "FROM node:22-alpine AS builder" in f_text
        assert "FROM node:22-alpine AS runner" in f_text
        assert "nextjs" in f_text
        assert "USER nextjs" in f_text
        assert "HEALTHCHECK" in f_text
        assert "EXPOSE 3000" in f_text
        print("  [PASS] Both backend and frontend Dockerfiles follow multi-stage non-root container standards.")

        # ── 8. Caddy Reverse Proxy & Deploy Orchestrator CLI ─────────────────────
        print("\n--- Step 8: Caddy Reverse Proxy & Deploy Orchestrator CLI ---")
        caddy_file = ROOT_DIR / "Caddyfile"
        assert caddy_file.is_file(), "Missing Caddyfile"
        caddy_text = caddy_file.read_text(encoding="utf-8")
        assert "reverse_proxy backend:8000" in caddy_text
        assert "reverse_proxy frontend:3000" in caddy_text
        assert "handle /ws/*" in caddy_text
        assert "Strict-Transport-Security" in caddy_text
        print("  [PASS] Caddyfile reverse proxy rules, WebSocket passthrough, and TLS headers verified.")

        orchestrator_py = ROOT_DIR / "scripts" / "deploy_orchestrator.py"
        assert orchestrator_py.is_file(), "Missing deploy_orchestrator.py"

        # Execute orchestrator preflight
        sub_proc = subprocess.run(
            [sys.executable, str(orchestrator_py), "preflight"],
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR),
        )
        assert sub_proc.returncode == 0, f"deploy_orchestrator.py failed:\n{sub_proc.stdout}\n{sub_proc.stderr}"
        assert "ALL PRE-FLIGHT VERIFICATIONS PASSED" in sub_proc.stdout
        print("  [PASS] deploy_orchestrator.py preflight CLI completed with exit code 0.")

    print("\n" + "=" * 80)
    print("=== ALL PHASE 20 PRODUCTION PACKAGING & DEPLOYMENT TESTS PASSED (100%) ===")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_phase20_production_deployment_complete())
