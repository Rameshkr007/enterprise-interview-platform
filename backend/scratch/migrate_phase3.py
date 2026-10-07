import sys
sys.path.insert(0, ".")
import asyncio
from sqlalchemy import text
from app.database import engine, Base
import app.models  # ensure all models registered

async def migrate():
    async with engine.begin() as conn:
        print("Ensuring resume columns exist...")
        await conn.execute(text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS structured_data JSONB DEFAULT '{}'::jsonb;"))
        await conn.execute(text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS parsing_status VARCHAR(50) DEFAULT 'completed';"))
        
        print("Creating Phase 3 tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Phase 3 tables created successfully.")

if __name__ == "__main__":
    asyncio.run(migrate())
