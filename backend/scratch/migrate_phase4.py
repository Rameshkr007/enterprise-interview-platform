import sys
sys.path.insert(0, ".")
import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("Migrating job_descriptions columns...")
        await conn.execute(text("ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS requirements JSONB DEFAULT '[]'::jsonb;"))
        await conn.execute(text("ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS seniority_level VARCHAR(50) DEFAULT 'mid';"))
        await conn.execute(text("ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS min_years_experience FLOAT DEFAULT 0.0;"))
        await conn.execute(text("ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS education_required VARCHAR(100) DEFAULT 'Bachelor';"))
        await conn.execute(text("ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS location_type VARCHAR(50) DEFAULT 'remote';"))
        
        print("Migrating ats_analyses columns...")
        await conn.execute(text("ALTER TABLE ats_analyses ADD COLUMN IF NOT EXISTS recommendation VARCHAR(50) DEFAULT 'APPLY';"))
        await conn.execute(text("ALTER TABLE ats_analyses ADD COLUMN IF NOT EXISTS technical_score FLOAT DEFAULT 0.0;"))
        await conn.execute(text("ALTER TABLE ats_analyses ADD COLUMN IF NOT EXISTS experience_score FLOAT DEFAULT 0.0;"))
        await conn.execute(text("ALTER TABLE ats_analyses ADD COLUMN IF NOT EXISTS education_score FLOAT DEFAULT 0.0;"))
        await conn.execute(text("ALTER TABLE ats_analyses ADD COLUMN IF NOT EXISTS project_score FLOAT DEFAULT 0.0;"))
        await conn.execute(text("ALTER TABLE ats_analyses ADD COLUMN IF NOT EXISTS skill_gap_details JSONB DEFAULT '[]'::jsonb;"))
        await conn.execute(text("ALTER TABLE ats_analyses ADD COLUMN IF NOT EXISTS seniority_fit VARCHAR(50) DEFAULT 'matching';"))
        await conn.execute(text("ALTER TABLE ats_analyses ADD COLUMN IF NOT EXISTS explainable_summary TEXT DEFAULT '';"))
        
        print("Phase 4 schema updates executed successfully.")

if __name__ == "__main__":
    asyncio.run(migrate())
