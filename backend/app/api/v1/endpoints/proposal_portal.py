"""
Public client portal endpoints for proposal access/decision.
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.email import (
    NOUGRAM_BRAND_ACCENT,
    NOUGRAM_BRAND_DARK,
    NOUGRAM_BRAND_LOGO_URL,
    NOUGRAM_SITE_URL,
    get_brand_sender_name,
    send_email,
)
from app.core.security import create_access_token, decode_access_token, verify_password
from app.models.project import Project
from app.models.proposal import ProposalClientLink
from app.models.user import User
from app.repositories.factory import RepositoryFactory
from app.schemas.proposal import (
    ProposalClientDecisionRequest,
    ProposalClientPortalResponse,
    ProposalClientVerifyRequest,
    ProposalClientVerifyResponse,
)
from app.services.capacity_service import CapacityService

router = APIRouter(prefix="/public/proposals", tags=["proposal-portal"])
portal_security = HTTPBearer(auto_error=False)
PORTAL_SESSION_MINUTES = 180


def _decision_label(decision: str) -> str:
    normalized = (decision or "").strip().lower()
    if normalized == "accepted":
        return "Aceptada"
    if normalized == "revision_requested":
        return "Solicita revisión"
    if normalized == "rejected":
        return "No continuar"
    return decision


async def _get_active_link(token: str, db: AsyncSession) -> ProposalClientLink:
    link_repo = RepositoryFactory.create_proposal_client_link_repository(db, tenant_id=None)
    link = await link_repo.get_active_by_token(token)
    if not link:
        raise HTTPException(status_code=404, detail="Proposal link not found or expired")
    return link


def _get_portal_payload(session_token: str) -> dict | None:
    payload = decode_access_token(session_token)
    if not payload:
        return None
    if payload.get("purpose") != "proposal_client_portal":
        return None
    return payload


@router.post("/{token}/verify", response_model=ProposalClientVerifyResponse)
async def verify_proposal_access(
    token: str,
    payload: ProposalClientVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    link = await _get_active_link(token, db)
    now = datetime.now(UTC)
    if (
        not link.access_code_hash
        or not link.access_code_expires_at
        or link.access_code_expires_at < now
    ):
        raise HTTPException(status_code=401, detail="Temporary key expired. Request a new email.")
    if not verify_password(payload.access_code, link.access_code_hash):
        raise HTTPException(status_code=401, detail="Invalid temporary key")

    remaining = max(int((link.access_expires_at - now).total_seconds() / 60), 1)
    session_minutes = min(PORTAL_SESSION_MINUTES, remaining)
    expires_at = now + timedelta(minutes=session_minutes)
    session_token = create_access_token(
        {
            "sub": "proposal-client",
            "purpose": "proposal_client_portal",
            "proposal_link_id": link.id,
            "public_token": token,
        },
        expires_delta=timedelta(minutes=session_minutes),
    )
    return ProposalClientVerifyResponse(
        session_token=session_token,
        expires_at=expires_at,
        proposal_status=link.status,
    )


@router.get("/{token}", response_model=ProposalClientPortalResponse)
async def get_proposal_portal_data(
    token: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(portal_security),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Session token required")
    session_payload = _get_portal_payload(credentials.credentials)
    if not session_payload or session_payload.get("public_token") != token:
        raise HTTPException(status_code=401, detail="Invalid client portal session")

    link = await _get_active_link(token, db)
    proposal_repo = RepositoryFactory.create_proposal_repository(db, link.organization_id)
    proposal = await proposal_repo.get_for_client_portal(link.proposal_id, link.organization_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    quote = None
    if link.quote_id:
        project_repo = RepositoryFactory.create_project_repository(db, link.organization_id)
        quote = await project_repo.get_quote_with_relationships(link.quote_id, link.project_id)

    link.view_count = int(link.view_count or 0) + 1
    link.viewed_at = datetime.now(UTC)
    if link.status == "sent":
        link.status = "viewed"
    await db.commit()

    return ProposalClientPortalResponse(
        proposal_id=proposal.id,
        proposal_title=proposal.title,
        proposal_body_json=proposal.body_json if isinstance(proposal.body_json, dict) else {},
        organization_name=proposal.organization.name if proposal.organization else None,
        project_name=proposal.project.name if proposal.project else "",
        client_name=proposal.project.client_name if proposal.project else "",
        quote_id=quote.id if quote else None,
        quote_version=quote.version if quote else None,
        quote_total_client_price=str(quote.total_client_price)
        if quote and quote.total_client_price is not None
        else None,
        quote_currency=proposal.project.currency if proposal.project else None,
        decision_status=link.status,
        decision_comment=link.decision_comment,
        decided_at=link.decided_at,
        access_expires_at=link.access_expires_at,
    )


@router.post("/{token}/decision", response_model=ProposalClientPortalResponse)
async def submit_proposal_decision(
    token: str,
    payload: ProposalClientDecisionRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(portal_security),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Session token required")
    session_payload = _get_portal_payload(credentials.credentials)
    if not session_payload or session_payload.get("public_token") != token:
        raise HTTPException(status_code=401, detail="Invalid client portal session")

    link = await _get_active_link(token, db)
    now = datetime.now(UTC)
    link.status = payload.decision
    link.decision_comment = payload.comment
    link.decided_at = now

    if payload.decision == "accepted":
        project_result = await db.execute(
            select(Project).where(
                Project.id == link.project_id,
                Project.organization_id == link.organization_id,
            )
        )
        project = project_result.scalar_one_or_none()
        if project and project.status != "Won":
            project.status = "Won"

    await db.commit()

    capacity_service = CapacityService(db, link.organization_id)
    if payload.decision == "accepted":
        await capacity_service.sync_committed_from_proposal(
            link=link,
            actor_user_id=None,
            reference_date=now,
        )
    elif payload.decision in {"rejected", "revision_requested"}:
        await capacity_service.clear_commitments_for_proposal(
            link=link,
            actor_user_id=None,
            reason=payload.decision,
        )

    proposal_repo = RepositoryFactory.create_proposal_repository(db, link.organization_id)
    proposal = await proposal_repo.get_for_client_portal(link.proposal_id, link.organization_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    quote = None
    if link.quote_id:
        project_repo = RepositoryFactory.create_project_repository(db, link.organization_id)
        quote = await project_repo.get_quote_with_relationships(link.quote_id, link.project_id)

    creator = None
    if proposal.created_by_id:
        creator_result = await db.execute(select(User).where(User.id == proposal.created_by_id))
        creator = creator_result.scalar_one_or_none()

    creator_email = (creator.email if creator and creator.email else "").strip() if creator else ""
    if creator_email:
        decision_label = _decision_label(link.status)
        comment_text = (link.decision_comment or "").strip()
        decision_date = now.strftime("%Y-%m-%d %H:%M UTC")
        sender_company_name = get_brand_sender_name()
        creator_subject = f'Respuesta de cliente: {decision_label} - "{proposal.title}"'
        d, a, logo, site = (
            NOUGRAM_BRAND_DARK,
            NOUGRAM_BRAND_ACCENT,
            NOUGRAM_BRAND_LOGO_URL,
            NOUGRAM_SITE_URL,
        )
        creator_html = f"""
        <!DOCTYPE html><html><head><meta charset="utf-8"></head>
        <body style="margin:0;padding:0;background:#ebebf0;font-family:Arial,sans-serif;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#ebebf0;padding:24px 16px;"><tr><td align="center">
        <table role="presentation" width="100%" style="max-width:600px;background:#fff;border-radius:12px;border:1px solid #d4d4dc;overflow:hidden;"><tr>
        <td style="padding:20px 24px;text-align:center;background:{d};">
        <a href="{site}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;display:inline-block;">
        <img src="{logo}" alt="Nougram" width="140" style="display:block;margin:0 auto;border:0;max-width:140px;width:140px;height:auto;" /></a></td></tr><tr>
        <td style="padding:24px;background:#fafafa;border-top:1px solid rgba(243,93,10,.2);color:{d};">
        <h2 style="margin:0 0 8px;font-size:20px;font-weight:600;">Actualización de propuesta</h2></td></tr><tr>
        <td style="padding:0 24px 24px;color:{d};line-height:1.6;">
          <p>El cliente respondió la propuesta enviada desde el portal.</p>
          <p><strong>Proyecto:</strong> {proposal.project.name if proposal.project else ""}</p>
          <p><strong>Cliente:</strong> {proposal.project.client_name if proposal.project else ""}</p>
          <p><strong>Respuesta:</strong> <span style="color:{a};font-weight:600;">{decision_label}</span></p>
          <p><strong>Fecha:</strong> {decision_date}</p>
          <p><strong>Comentario:</strong> {comment_text or "Sin comentario"}</p>
        </td></tr></table></td></tr></table>
        </body></html>
        """
        creator_text = (
            "Actualización de propuesta\n"
            f"Proyecto: {proposal.project.name if proposal.project else ''}\n"
            f"Cliente: {proposal.project.client_name if proposal.project else ''}\n"
            f"Respuesta: {decision_label}\n"
            f"Fecha: {decision_date}\n"
            f"Comentario: {comment_text or 'Sin comentario'}\n"
        )
        decision_template_id = (
            (settings.MAILERSEND_TEMPLATE_PROPOSAL_DECISION_ID or "").strip()
            or (settings.MAILERSEND_TEMPLATE_QUOTE_ID or "").strip()
            or None
        )
        decision_template_data = {
            "proposal_id": str(proposal.id),
            "proposal_title": proposal.title or "",
            "project_name": proposal.project.name if proposal.project else "",
            "client_name": proposal.project.client_name if proposal.project else "",
            "decision_label": decision_label,
            "decision_status": link.status or "",
            "decision_date": decision_date,
            "decision_comment": comment_text or "Sin comentario",
            "sender_company_name": sender_company_name,
        }
        await send_email(
            to_email=creator_email,
            subject=creator_subject,
            body_html=creator_html,
            body_text=creator_text,
            template_id=decision_template_id,
            template_data=decision_template_data,
        )

    return ProposalClientPortalResponse(
        proposal_id=proposal.id,
        proposal_title=proposal.title,
        proposal_body_json=proposal.body_json if isinstance(proposal.body_json, dict) else {},
        organization_name=proposal.organization.name if proposal.organization else None,
        project_name=proposal.project.name if proposal.project else "",
        client_name=proposal.project.client_name if proposal.project else "",
        quote_id=quote.id if quote else None,
        quote_version=quote.version if quote else None,
        quote_total_client_price=str(quote.total_client_price)
        if quote and quote.total_client_price is not None
        else None,
        quote_currency=proposal.project.currency if proposal.project else None,
        decision_status=link.status,
        decision_comment=link.decision_comment,
        decided_at=link.decided_at,
        access_expires_at=link.access_expires_at,
    )
