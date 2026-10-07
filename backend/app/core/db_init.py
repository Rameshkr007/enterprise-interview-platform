import structlog
from uuid import uuid4
from sqlalchemy import text, select
from app.database import engine, Base, AsyncSessionLocal
import app.models  # noqa: F401
from app.models.user import User, UserRole
from app.core.security import hash_password

log = structlog.get_logger(__name__)

async def auto_init_database() -> None:
    """Creates database extensions, synchronizes all tables and seeds demo accounts."""
    try:
        async with engine.begin() as conn:
            for ext in ["uuid-ossp", "pg_trgm"]:
                try:
                    await conn.execute(text(f'CREATE EXTENSION IF NOT EXISTS "{ext}";'))
                except Exception as e:
                    log.warning(f"Extension {ext} skipped/warning: {e}")

            try:
                await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
            except Exception as e:
                log.warning(f"Vector extension skipped/warning: {e}")

            # Verify / add user_role enums if needed
            for role_val in ["interviewer", "org_admin", "platform_admin"]:
                try:
                    await conn.execute(text(f"ALTER TYPE user_role ADD VALUE IF NOT EXISTS '{role_val}';"))
                except Exception:
                    pass

            await conn.run_sync(Base.metadata.create_all)
            log.info("database_metadata_tables_verified")

        # Seed initial demo accounts if admin does not exist
        demo_users = [
            {
                "email": "admin@enterprise.ai",
                "full_name": "Enterprise Platform Admin",
                "password": "AdminPassword123!",
                "role": UserRole.admin,
            },
            {
                "email": "recruiter@enterprise.ai",
                "full_name": "Senior Talent Recruiter",
                "password": "RecruiterPassword123!",
                "role": UserRole.recruiter,
            },
            {
                "email": "candidate@enterprise.ai",
                "full_name": "Arjun Sharma (Candidate)",
                "password": "CandidatePassword123!",
                "role": UserRole.candidate,
            },
        ]

        async with AsyncSessionLocal() as session:
            for u in demo_users:
                res = await session.execute(select(User).where(User.email == u["email"]))
                existing = res.scalar_one_or_none()
                if not existing:
                    new_user = User(
                        id=uuid4(),
                        email=u["email"],
                        full_name=u["full_name"],
                        hashed_password=hash_password(u["password"]),
                        role=u["role"],
                        is_active=True,
                    )
                    session.add(new_user)
                    log.info(f"demo_user_created: {u['email']}")
            await session.commit()
    except Exception as exc:
        log.error("auto_init_database_error", error=str(exc))
