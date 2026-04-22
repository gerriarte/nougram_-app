import asyncio

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def reset_password():
    print("Connecting to database...")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("Searching for user gerriarte@abralatam.com...")
        result = await session.execute(select(User).where(User.email == "gerriarte@abralatam.com"))
        user = result.scalar_one_or_none()

        if user:
            print(f"User found: {user.email}")
            new_password = "123456"
            hashed_password = pwd_context.hash(new_password)
            user.hashed_password = hashed_password
            await session.commit()
            print(f"Password successfully reset to: {new_password}")
        else:
            print("User NOT found!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_password())
