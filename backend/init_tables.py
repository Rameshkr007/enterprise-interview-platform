import asyncio
import asyncpg
from app.database import engine, Base
import app.models  # noqa

async def main():
    conn = await asyncpg.connect(user="postgres", host="127.0.0.1", port=5432, database="interview_platform")
    for ext in ["uuid-ossp", "pg_trgm"]:
        try:
            await conn.execute(f'CREATE EXTENSION IF NOT EXISTS "{ext}"')
            print(f"Extension {ext}: Installed")
        except Exception as e:
            print(f"Extension {ext} warning:", e)
    
    # Check vector extension
    try:
        await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
        print("Extension vector: Installed")
    except Exception as e:
        print("Extension vector note:", e)
    
    # Check if user_role enum exists and update values
    for role_val in ["interviewer", "org_admin", "platform_admin"]:
        try:
            await conn.execute(f"ALTER TYPE user_role ADD VALUE IF NOT EXISTS '{role_val}'")
            print(f"Enum value '{role_val}' added or verified in user_role.")
        except Exception as e:
            print(f"Role enum check ({role_val}):", e)

    await conn.close()
    
    # Create tables via SQLAlchemy
    print("Creating/verifying all database tables via SQLAlchemy metadata...")
    async with engine.begin() as sql_conn:
        await sql_conn.run_sync(Base.metadata.create_all)
    print("Tables creation complete!")

if __name__ == "__main__":
    asyncio.run(main())
