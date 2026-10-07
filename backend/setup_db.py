import asyncio
import asyncpg

async def setup():
    conn = await asyncpg.connect(user="postgres", host="127.0.0.1", port=5432, database="postgres")
    version = await conn.fetchval("SELECT version()")
    print("PostgreSQL Version:", version)
    
    exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'interview_platform'")
    if not exists:
        await conn.execute("CREATE DATABASE interview_platform")
        print("Successfully created database 'interview_platform'!")
    else:
        print("Database 'interview_platform' already exists.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(setup())
