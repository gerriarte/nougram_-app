"""Script para verificar usuarios en la base de datos"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.user import User


async def check_users():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        print(f"\n{'=' * 60}")
        print(f"Usuarios encontrados: {len(users)}")
        print(f"{'=' * 60}")

        if users:
            for u in users:
                print(f"\nEmail: {u.email}")
                print(f"Nombre: {u.full_name}")
                print(f"Rol: {u.role}")
                print(f"Organización ID: {u.organization_id}")
                print(f"Tiene password: {'Sí' if u.hashed_password else 'No'}")
        else:
            print("\n❌ No hay usuarios en la base de datos.")
            print("\n💡 Necesitas registrarte primero:")
            print("   1. Ve a http://localhost:3000/register")
            print("   2. Completa el formulario para crear tu organización")
            print("   3. Luego podrás iniciar sesión con tus credenciales")

        print(f"\n{'=' * 60}\n")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_users())


import asyncio


async def check_users():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        print(f"\n{'=' * 60}")
        print(f"Usuarios encontrados: {len(users)}")
        print(f"{'=' * 60}")

        if users:
            for u in users:
                print(f"\nEmail: {u.email}")
                print(f"Nombre: {u.full_name}")
                print(f"Rol: {u.role}")
                print(f"Organización ID: {u.organization_id}")
                print(f"Tiene password: {'Sí' if u.hashed_password else 'No'}")
        else:
            print("\n❌ No hay usuarios en la base de datos.")
            print("\n💡 Necesitas registrarte primero:")
            print("   1. Ve a http://localhost:3000/register")
            print("   2. Completa el formulario para crear tu organización")
            print("   3. Luego podrás iniciar sesión con tus credenciales")

        print(f"\n{'=' * 60}\n")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_users())
