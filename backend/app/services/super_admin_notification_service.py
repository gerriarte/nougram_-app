"""
Service to notify super admins about tenant billing/account actions.
"""
from __future__ import annotations

import json
from typing import Any, Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import send_email
from app.core.logging import get_logger
from app.core.permissions import get_allowed_super_admin_emails
from app.models.organization import Organization
from app.models.user import User
from app.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class SuperAdminNotificationService:
    """
    Dispatches email notifications to super admins for key tenant actions.
    """

    @staticmethod
    async def _resolve_super_admin_emails(db: AsyncSession) -> list[str]:
        configured = get_allowed_super_admin_emails()
        user_repo = UserRepository(db, tenant_id=None)
        super_admin_users = await user_repo.get_by_role("super_admin")

        emails = {email.lower() for email in configured if email}
        for user in super_admin_users:
            if user.email:
                emails.add(user.email.strip().lower())

        return sorted(email for email in emails if email)

    @staticmethod
    def _render_details(details: dict[str, Any]) -> tuple[str, str]:
        details_json = json.dumps(details, ensure_ascii=False, indent=2, default=str)
        details_html = (
            "<pre style='background:#f6f8fa;padding:12px;border-radius:6px;"
            "border:1px solid #e5e7eb;overflow:auto;'>"
            f"{details_json}"
            "</pre>"
        )
        return details_json, details_html

    @staticmethod
    async def notify_super_admins(
        db: AsyncSession,
        organization: Organization,
        actor: User,
        action_label: str,
        details: dict[str, Any],
    ) -> int:
        """
        Sends a notification email to all known super admins.
        Returns the number of successful deliveries.
        """

        recipients = await SuperAdminNotificationService._resolve_super_admin_emails(db)
        if not recipients:
            logger.warning(
                "No super admin emails configured for billing notification",
                level="warning",
                module=__name__,
                function="notify_super_admins",
                organization_id=organization.id,
                action=action_label,
            )
            return 0

        details_text, details_html = SuperAdminNotificationService._render_details(details)
        subject = f"[Nougram] Tenant action: {action_label} ({organization.name})"
        body_html = (
            "<p>Se registró una acción de facturación/cuenta a nivel tenant.</p>"
            f"<p><strong>Organización:</strong> {organization.name} (ID: {organization.id})</p>"
            f"<p><strong>Usuario:</strong> {actor.full_name} ({actor.email})</p>"
            f"<p><strong>Acción:</strong> {action_label}</p>"
            f"{details_html}"
        )
        body_text = (
            "Se registró una acción de facturación/cuenta a nivel tenant.\n\n"
            f"Organización: {organization.name} (ID: {organization.id})\n"
            f"Usuario: {actor.full_name} ({actor.email})\n"
            f"Acción: {action_label}\n\n"
            f"Detalles:\n{details_text}\n"
        )

        sent_count = 0
        for email in recipients:
            sent = await send_email(
                to_email=email,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
            )
            if sent:
                sent_count += 1

        logger.info(
            "Processed super admin notification for tenant action",
            level="info",
            module=__name__,
            function="notify_super_admins",
            organization_id=organization.id,
            action=action_label,
            recipients=recipients,
            sent_count=sent_count,
        )
        return sent_count
