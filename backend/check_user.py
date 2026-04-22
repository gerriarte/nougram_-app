"""Script para verificar usuario en la base de datos"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.user import User


async def check_user():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == "gerriarte@abralatam.com"))
        user = result.scalar_one_or_none()

        if user:
            print("[OK] Usuario encontrado:")
            print(f"   Email: {user.email}")
            print(f"   Nombre: {user.full_name}")
            print(f"   Rol: {user.role}")
            print(
                f"   Password hash existe: {user.hashed_password is not None and len(user.hashed_password) > 0}"
            )
            if user.hashed_password:
                print(f"   Password hash (primeros 20 chars): {user.hashed_password[:20]}...")
        else:
            print("[ERROR] Usuario NO encontrado en la base de datos")

        # Verificar todos los usuarios
        all_users = await session.execute(select(User))
        users = all_users.scalars().all()
        print(f"\n[INFO] Total de usuarios en la BD: {len(users)}")
        for u in users:
            print(f"   - {u.email} ({u.full_name}) - Rol: {u.role}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_user())
