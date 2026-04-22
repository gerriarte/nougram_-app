"""
Automatic bootstrap for super admin account on application startup.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.permissions import get_allowed_super_admin_emails
from app.core.security import get_password_hash
from app.models.user import User

logger = get_logger(__name__)


def _resolve_bootstrap_email() -> str:
    allowed = get_allowed_super_admin_emails()
    if not allowed:
        return ""
    return sorted(allowed)[0]


async def ensure_super_admin_bootstrap(db: AsyncSession) -> None:
    """
    Create or update the super admin account automatically during startup.

    Safety behavior:
    - No-op unless AUTO_PROVISION_SUPER_ADMIN=true and password is provided.
    - Uses configured allowed super-admin emails to determine target account.
    - Does not rotate password unless forced or missing hash.
    """
    if not settings.AUTO_PROVISION_SUPER_ADMIN:
        logger.info("Super admin auto-provision disabled")
        return

    bootstrap_password = (settings.SUPER_ADMIN_BOOTSTRAP_PASSWORD or "").strip()
    if not bootstrap_password:
        logger.warning("Super admin auto-provision skipped: missing SUPER_ADMIN_BOOTSTRAP_PASSWORD")
        return

    email = _resolve_bootstrap_email()
    if not email:
        logger.error("Super admin auto-provision skipped: no allowed super admin email configured")
        return

    full_name = (settings.SUPER_ADMIN_BOOTSTRAP_FULL_NAME or "Super Admin").strip()
    password_hash = get_password_hash(bootstrap_password)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=password_hash,
            role="super_admin",
            role_type="support",
            organization_id=None,
        )
        db.add(user)
        try:
            await db.commit()
            logger.info("Super admin auto-provision created user", email=email)
            return
        except IntegrityError:
            await db.rollback()
            logger.warning(
                "Super admin auto-provision create failed, retrying lookup",
                email=email,
                reason="integrity_error",
            )
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user is None:
                # Last-resort fallback for legacy DBs that enforce organization_id NOT NULL.
                fallback_org_result = await db.execute(
                    select(User.organization_id).where(User.organization_id.is_not(None))
                )
                fallback_org_id = fallback_org_result.scalars().first()
                if fallback_org_id is None:
                    logger.error(
                        "Super admin auto-provision failed: no fallback organization_id available",
                        email=email,
                    )
                    return

                legacy_user = User(
                    email=email,
                    full_name=full_name,
                    hashed_password=password_hash,
                    role="super_admin",
                    role_type="support",
                    organization_id=fallback_org_id,
                )
                db.add(legacy_user)
                try:
                    await db.commit()
                    logger.warning(
                        "Super admin auto-provision created user with legacy organization_id fallback",
                        email=email,
                        organization_id=fallback_org_id,
                    )
                    return
                except IntegrityError:
                    await db.rollback()
                    logger.error(
                        "Super admin auto-provision failed after fallback create attempt",
                        email=email,
                    )
                    return

    original_org_id = user.organization_id
    changed = False
    if user.role != "super_admin":
        user.role = "super_admin"
        changed = True
    if user.role_type != "support":
        user.role_type = "support"
        changed = True
    if user.organization_id is not None:
        user.organization_id = None
        changed = True
    if user.full_name != full_name:
        user.full_name = full_name
        changed = True

    must_update_password = (
        settings.SUPER_ADMIN_BOOTSTRAP_FORCE_PASSWORD_RESET or not user.hashed_password
    )
    if must_update_password:
        user.hashed_password = password_hash
        changed = True

    if changed:
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            # Legacy deployments may still enforce users.organization_id NOT NULL.
            # In that case keep the existing organization_id and continue with support role.
            user.organization_id = original_org_id
            await db.merge(user)
            await db.commit()
            logger.warning(
                "Super admin auto-provision kept legacy organization_id due DB constraint",
                email=email,
                organization_id=original_org_id,
            )
        logger.info(
            "Super admin auto-provision updated user",
            email=email,
            password_reset=must_update_password,
        )
    else:
        logger.info("Super admin auto-provision user already compliant", email=email)
