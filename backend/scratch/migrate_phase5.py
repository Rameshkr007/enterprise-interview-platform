import sys
sys.path.insert(0, ".")
import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("Migrating interview_sessions columns...")
        await conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES organizations(id) ON DELETE SET NULL;"))
        await conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS current_topic VARCHAR(255);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_interview_sessions_org_id ON interview_sessions(org_id);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_interview_sessions_status ON interview_sessions(status);"))
        print("Phase 5 schema updates executed successfully.")

if __name__ == "__main__":
    asyncio.run(migrate())
