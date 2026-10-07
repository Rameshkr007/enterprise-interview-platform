import asyncio
from uuid import uuid4
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

async def seed_demo_users():
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
            if existing:
                existing.hashed_password = hash_password(u["password"])
                existing.role = u["role"]
                existing.is_active = True
                print(f"Updated user: {u['email']} ({u['role'].value})")
            else:
                new_user = User(
                    id=uuid4(),
                    email=u["email"],
                    full_name=u["full_name"],
                    hashed_password=hash_password(u["password"]),
                    role=u["role"],
                    is_active=True,
                )
                session.add(new_user)
                print(f"Created user: {u['email']} ({u['role'].value})")
        await session.commit()
    print("Demo users seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_demo_users())
