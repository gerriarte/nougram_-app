"""
Create or update the configured super admin user (idempotent).

Usage:
  python backend/scripts/create_or_update_super_admin.py --password "StrongPassword123!"
  python backend/scripts/create_or_update_super_admin.py --password-file "C:/secure/password.txt"

The email is resolved from:
1) SUPER_ADMIN_ALLOWED_EMAILS (first email in the CSV)
2) SUPER_ADMIN_EMAIL
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend package is importable when executed from repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.core.permissions import get_allowed_super_admin_emails


def resolve_super_admin_email() -> str:
    allowed = get_allowed_super_admin_emails()
    if not allowed:
        return ""
    return sorted(allowed)[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create/update super admin user")
    parser.add_argument("--password", type=str, default="", help="Plain-text password")
    parser.add_argument(
        "--password-file",
        type=str,
        default="",
        help="Path to file containing plain-text password",
    )
    parser.add_argument(
        "--full-name",
        type=str,
        default="Super Admin",
        help="Display name for super admin user",
    )
    return parser.parse_args()


def resolve_password(args: argparse.Namespace) -> str:
    if args.password and args.password_file:
        raise ValueError("Use either --password or --password-file, not both.")
    if args.password_file:
        path = Path(args.password_file)
        if not path.exists():
            raise ValueError(f"Password file not found: {path}")
        return path.read_text(encoding="utf-8").strip()
    if args.password:
        return args.password.strip()
    raise ValueError("Password is required. Use --password or --password-file.")


async def upsert_super_admin(email: str, full_name: str, password: str) -> None:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not email:
        raise ValueError(
            "No super admin email configured. Set SUPER_ADMIN_EMAIL or SUPER_ADMIN_ALLOWED_EMAILS."
        )

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            password_hash = get_password_hash(password)

            if user:
                user.role = "super_admin"
                user.role_type = "support"
                user.organization_id = None
                user.full_name = full_name
                user.hashed_password = password_hash
                await session.commit()
                print(f"UPDATED|email={email}|user_id={user.id}")
                return

            new_user = User(
                email=email,
                full_name=full_name,
                hashed_password=password_hash,
                role="super_admin",
                role_type="support",
                organization_id=None,
            )
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            print(f"CREATED|email={email}|user_id={new_user.id}")
    finally:
        await engine.dispose()


async def main() -> None:
    args = parse_args()
    password = resolve_password(args)
    email = resolve_super_admin_email()
    await upsert_super_admin(email=email, full_name=args.full_name, password=password)


if __name__ == "__main__":
    asyncio.run(main())
