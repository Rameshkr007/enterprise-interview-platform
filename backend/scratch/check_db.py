import sys
sys.path.insert(0, ".")
import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        print("Tables:", [r[0] for r in res.fetchall()])

if __name__ == "__main__":
    asyncio.run(check())
