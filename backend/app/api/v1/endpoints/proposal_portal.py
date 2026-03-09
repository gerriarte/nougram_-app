"""
Public client portal endpoints for proposal access/decision.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.email import send_email
from app.core.security import create_access_token, decode_access_token, verify_password
from app.models.project import Quote
from app.models.proposal import ProposalClientLink, ProposalDocument
from app.models.user import User
from app.repositories.factory import RepositoryFactory
from app.schemas.proposal import (
    ProposalClientDecisionRequest,
    ProposalClientPortalResponse,
    ProposalClientVerifyRequest,
    ProposalClientVerifyResponse,
)

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


def _get_portal_payload(session_token: str) -> Optional[dict]:
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
    now = datetime.now(timezone.utc)
    if not link.access_code_hash or not link.access_code_expires_at or link.access_code_expires_at < now:
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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(portal_security),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Session token required")
    session_payload = _get_portal_payload(credentials.credentials)
    if not session_payload or session_payload.get("public_token") != token:
        raise HTTPException(status_code=401, detail="Invalid client portal session")

    link = await _get_active_link(token, db)
    result = await db.execute(
        select(ProposalDocument)
        .where(ProposalDocument.id == link.proposal_id, ProposalDocument.organization_id == link.organization_id)
        .options(selectinload(ProposalDocument.project))
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    quote = None
    if link.quote_id:
        q_res = await db.execute(select(Quote).where(Quote.id == link.quote_id, Quote.project_id == link.project_id))
        quote = q_res.scalar_one_or_none()

    link.view_count = int(link.view_count or 0) + 1
    link.viewed_at = datetime.now(timezone.utc)
    if link.status == "sent":
        link.status = "viewed"
    await db.commit()

    return ProposalClientPortalResponse(
        proposal_id=proposal.id,
        proposal_title=proposal.title,
        proposal_body_json=proposal.body_json if isinstance(proposal.body_json, dict) else {},
        project_name=proposal.project.name if proposal.project else "",
        client_name=proposal.project.client_name if proposal.project else "",
        quote_id=quote.id if quote else None,
        quote_version=quote.version if quote else None,
        quote_total_client_price=str(quote.total_client_price) if quote and quote.total_client_price is not None else None,
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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(portal_security),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Session token required")
    session_payload = _get_portal_payload(credentials.credentials)
    if not session_payload or session_payload.get("public_token") != token:
        raise HTTPException(status_code=401, detail="Invalid client portal session")

    link = await _get_active_link(token, db)
    now = datetime.now(timezone.utc)
    link.status = payload.decision
    link.decision_comment = payload.comment
    link.decided_at = now
    await db.commit()

    result = await db.execute(
        select(ProposalDocument)
        .where(ProposalDocument.id == link.proposal_id, ProposalDocument.organization_id == link.organization_id)
        .options(selectinload(ProposalDocument.project))
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    quote = None
    if link.quote_id:
        q_res = await db.execute(select(Quote).where(Quote.id == link.quote_id, Quote.project_id == link.project_id))
        quote = q_res.scalar_one_or_none()

    creator = None
    if proposal.created_by_id:
        creator_result = await db.execute(select(User).where(User.id == proposal.created_by_id))
        creator = creator_result.scalar_one_or_none()

    creator_email = (creator.email if creator and creator.email else "").strip() if creator else ""
    if creator_email:
        decision_label = _decision_label(link.status)
        comment_text = (link.decision_comment or "").strip()
        decision_date = now.strftime("%Y-%m-%d %H:%M UTC")
        creator_subject = f'Respuesta de cliente: {decision_label} - "{proposal.title}"'
        creator_html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6;">
          <h2>Actualización de propuesta</h2>
          <p>El cliente respondió la propuesta enviada desde el portal.</p>
          <p><strong>Proyecto:</strong> {proposal.project.name if proposal.project else ''}</p>
          <p><strong>Cliente:</strong> {proposal.project.client_name if proposal.project else ''}</p>
          <p><strong>Respuesta:</strong> {decision_label}</p>
          <p><strong>Fecha:</strong> {decision_date}</p>
          <p><strong>Comentario:</strong> {comment_text or 'Sin comentario'}</p>
        </div>
        """
        creator_text = (
            "Actualización de propuesta\n"
            f"Proyecto: {proposal.project.name if proposal.project else ''}\n"
            f"Cliente: {proposal.project.client_name if proposal.project else ''}\n"
            f"Respuesta: {decision_label}\n"
            f"Fecha: {decision_date}\n"
            f"Comentario: {comment_text or 'Sin comentario'}\n"
        )
        await send_email(
            to_email=creator_email,
            subject=creator_subject,
            body_html=creator_html,
            body_text=creator_text,
        )

    return ProposalClientPortalResponse(
        proposal_id=proposal.id,
        proposal_title=proposal.title,
        proposal_body_json=proposal.body_json if isinstance(proposal.body_json, dict) else {},
        project_name=proposal.project.name if proposal.project else "",
        client_name=proposal.project.client_name if proposal.project else "",
        quote_id=quote.id if quote else None,
        quote_version=quote.version if quote else None,
        quote_total_client_price=str(quote.total_client_price) if quote and quote.total_client_price is not None else None,
        quote_currency=proposal.project.currency if proposal.project else None,
        decision_status=link.status,
        decision_comment=link.decision_comment,
        decided_at=link.decided_at,
        access_expires_at=link.access_expires_at,
    )
