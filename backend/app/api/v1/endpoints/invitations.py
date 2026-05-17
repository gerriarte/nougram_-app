"""
Invitation endpoints for organization user invitations
"""

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.email import (
    NOUGRAM_BRAND_ACCENT,
    NOUGRAM_BRAND_DARK,
    NOUGRAM_BRAND_LOGO_URL,
    NOUGRAM_SITE_URL,
    send_email,
)
from app.core.logging import get_logger
from app.core.permissions import PERM_INVITE_USERS, check_permission, get_user_role
from app.core.plan_limits import validate_user_limit
from app.core.security import create_access_token, get_current_user
from app.models.invitation import Invitation
from app.models.organization import Organization
from app.models.user import User
from app.repositories.invitation_repository import InvitationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.invitation import (
    InvitationAcceptRequest,
    InvitationAcceptResponse,
    InvitationCreate,
    InvitationListResponse,
    InvitationResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/organizations", tags=["Invitations"])


def _generate_invitation_token() -> str:
    """Generate a secure invitation token"""
    return secrets.token_urlsafe(32)


def _get_invitation_expiry_days() -> int:
    """Get invitation expiry days (default: 7 days)"""
    return 7


def _send_invitation_email(
    invitation: Invitation,
    organization: Organization,
    background_tasks: BackgroundTasks,
    frontend_url: str | None = None,
) -> None:
    """
    Send invitation email to user

    Args:
        invitation: Invitation instance
        organization: Organization instance
        frontend_url: Frontend URL for invitation link (defaults to settings)

    Returns:
        True if email sent successfully, False otherwise
    """
    if not frontend_url:
        # Get from settings
        frontend_url = settings.FRONTEND_URL

    invitation_link = f"{frontend_url}/auth/accept-invitation?token={invitation.token}"

    subject = f"Invitation to join {organization.name}"

    d, a, logo, site = (
        NOUGRAM_BRAND_DARK,
        NOUGRAM_BRAND_ACCENT,
        NOUGRAM_BRAND_LOGO_URL,
        NOUGRAM_SITE_URL,
    )
    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="margin:0;padding:0;background:#ebebf0;font-family:Arial,sans-serif;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#ebebf0;padding:24px 16px;"><tr><td align="center">
        <table role="presentation" width="100%" style="max-width:600px;background:#fff;border-radius:12px;overflow:hidden;border:1px solid #d4d4dc;"><tr>
        <td style="padding:20px 24px;text-align:center;background:{d};">
        <a href="{site}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;display:inline-block;">
        <img src="{logo}" alt="Nougram" width="140" style="display:block;margin:0 auto;border:0;max-width:140px;width:140px;height:auto;" /></a></td></tr><tr>
        <td style="background:{d};color:#fff;padding:20px 24px;text-align:center;border-top:1px solid rgba(243,93,10,.25);">
        <h1 style="margin:0;font-size:20px;font-weight:600;">Invitación a Nougram</h1></td></tr><tr>
        <td style="padding:28px 24px;color:{d};line-height:1.6;font-size:15px;background:#fafafa;">
            <p>Hola,</p>
            <p>Te invitaron a unirte a <strong>{organization.name}</strong> en Nougram.</p>
            <p>Tu rol será: <strong>{invitation.role}</strong></p>
            <table role="presentation" cellspacing="0" cellpadding="0" style="margin:20px auto;"><tr>
            <td style="border-radius:8px;background:{a};">
            <a href="{invitation_link}" style="display:inline-block;padding:12px 24px;color:#fff !important;text-decoration:none;font-weight:600;">Aceptar invitación</a>
            </td></tr></table>
            <p style="font-size:13px;color:#5c5d70;">O copia este enlace:</p>
            <p style="word-break:break-all;font-size:12px;"><a href="{invitation_link}" style="color:{a};">{invitation_link}</a></p>
            <p><strong>Vence:</strong> {invitation.expires_at.strftime("%B %d, %Y at %I:%M %p")}</p>
            <p style="font-size:13px;color:#5c5d70;">Si no esperabas esta invitación, ignora este correo.</p>
        </td></tr><tr>
        <td style="padding:16px 24px;text-align:center;font-size:11px;color:#5c5d70;background:#fff;">Correo automático · Nougram</td></tr>
        </table></td></tr></table>
    </body>
    </html>
    """

    body_text = f"""
    You're Invited!

    Hello,

    You have been invited to join {organization.name} on Nougram.
    Your role will be: {invitation.role}

    Accept your invitation by clicking this link:
    {invitation_link}

    This invitation expires on: {invitation.expires_at.strftime("%B %d, %Y at %I:%M %p")}

    If you didn't expect this invitation, you can safely ignore this email.

    ---
    This is an automated message from Nougram. Please do not reply to this email.
    """

    background_tasks.add_task(
        send_email,
        to_email=invitation.email,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
    )


@router.post(
    "/{organization_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    organization_id: int,
    invitation_data: InvitationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new invitation to join an organization

    **Permissions:**
    - Requires `can_invite_users` permission
    - Super admin: can invite to any organization
    - Owner: can invite to their own organization
    """
    # Check permissions
    try:
        check_permission(current_user, PERM_INVITE_USERS)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to invite users",
        )

    # Additional check: non-super_admin users can only invite to their own organization
    user_role = get_user_role(current_user)
    is_super_admin = user_role == "super_admin"
    is_owner = user_role == "owner" and current_user.organization_id == organization_id

    if not (is_super_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only invite users to your own organization",
        )

    # Verify organization exists
    org_repo = OrganizationRepository(db)
    org = await org_repo.get_by_id(organization_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    # Check if user already exists and is in organization
    existing_user = await db.execute(select(User).where(User.email == invitation_data.email))
    user = existing_user.scalar_one_or_none()

    if user and user.organization_id == organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {invitation_data.email} is already a member of this organization",
        )

    # Check for existing pending invitation
    invitation_repo = InvitationRepository(db, tenant_id=organization_id)
    existing_invitation = await invitation_repo.get_by_email_and_org(
        invitation_data.email, organization_id
    )

    if existing_invitation and not existing_invitation.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A pending invitation already exists for {invitation_data.email}",
        )

    # Generate token and expiration
    token = _generate_invitation_token()
    expires_at = datetime.now(UTC) + timedelta(days=_get_invitation_expiry_days())

    # Create invitation
    invitation = await invitation_repo.create_invitation(
        organization_id=organization_id,
        email=invitation_data.email,
        role=invitation_data.role,
        token=token,
        expires_at=expires_at,
        created_by_id=current_user.id,
    )

    await db.commit()
    await db.refresh(invitation)

    # Queue invitation email in background
    _send_invitation_email(invitation, org, background_tasks)

    logger.info(
        f"Invitation created for {invitation_data.email} to organization {organization_id}",
        invitation_id=invitation.id,
        created_by=current_user.id,
    )

    return InvitationResponse(
        id=invitation.id,
        organization_id=invitation.organization_id,
        email=invitation.email,
        role=invitation.role,
        token=invitation.token,  # Include token in response for initial creation
        expires_at=invitation.expires_at,
        accepted_at=invitation.accepted_at,
        created_by_id=invitation.created_by_id,
        created_at=invitation.created_at,
        updated_at=invitation.updated_at,
        status=invitation.status,
    )


@router.get("/{organization_id}/invitations", response_model=InvitationListResponse)
async def list_invitations(
    organization_id: int,
    status_filter: str | None = Query(
        None, alias="status", description="Filter by status: pending, accepted, expired"
    ),
    include_expired: bool = Query(False, description="Include expired invitations"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List invitations for an organization

    **Permissions:**
    - Requires `can_invite_users` permission
    - Super admin: can view invitations for any organization
    - Owner: can view invitations for their own organization
    """
    # Check permissions
    try:
        check_permission(current_user, PERM_INVITE_USERS)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view invitations",
        )

    # Additional check: non-super_admin users can only view their own organization
    user_role = get_user_role(current_user)
    is_super_admin = user_role == "super_admin"
    is_owner = user_role == "owner" and current_user.organization_id == organization_id

    if not (is_super_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view invitations for your own organization",
        )

    # Verify organization exists
    org_repo = OrganizationRepository(db)
    org = await org_repo.get_by_id(organization_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    # List invitations
    invitation_repo = InvitationRepository(db, tenant_id=organization_id)
    invitations = await invitation_repo.list_by_organization(
        organization_id=organization_id, status=status_filter, include_expired=include_expired
    )

    items = [
        InvitationResponse(
            id=inv.id,
            organization_id=inv.organization_id,
            email=inv.email,
            role=inv.role,
            token="",  # Don't expose token in list view
            expires_at=inv.expires_at,
            accepted_at=inv.accepted_at,
            created_by_id=inv.created_by_id,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
            status=inv.status,
        )
        for inv in invitations
    ]

    return InvitationListResponse(items=items, total=len(items))


@router.delete(
    "/{organization_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def cancel_invitation(
    organization_id: int,
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a pending invitation

    **Permissions:**
    - Requires `can_invite_users` permission
    - Super admin: can cancel invitations for any organization
    - Owner: can cancel invitations for their own organization
    """
    # Check permissions
    try:
        check_permission(current_user, PERM_INVITE_USERS)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to cancel invitations",
        )

    # Additional check: non-super_admin users can only cancel their own organization's invitations
    user_role = get_user_role(current_user)
    is_super_admin = user_role == "super_admin"
    is_owner = user_role == "owner" and current_user.organization_id == organization_id

    if not (is_super_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel invitations for your own organization",
        )

    # Cancel invitation
    invitation_repo = InvitationRepository(db, tenant_id=organization_id)
    cancelled = await invitation_repo.cancel_invitation(invitation_id, organization_id)

    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found or already accepted"
        )

    await db.commit()

    logger.info(
        f"Invitation {invitation_id} cancelled for organization {organization_id}",
        cancelled_by=current_user.id,
    )


@router.get("/invitations/validate/{token}", response_model=InvitationResponse)
async def validate_invitation_token(token: str, db: AsyncSession = Depends(get_db)):
    """
    Validate an invitation token and return invitation details

    This is a public endpoint to get invitation information before accepting.
    """
    # Get invitation by token (without tenant scoping to find it)
    invitation_repo = InvitationRepository(db, tenant_id=None)
    invitation = await invitation_repo.get_by_token(token)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invitation token"
        )

    # Check if expired
    if invitation.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation has expired"
        )

    # Check if already accepted
    if invitation.is_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has already been accepted",
        )

    return InvitationResponse(
        id=invitation.id,
        organization_id=invitation.organization_id,
        email=invitation.email,
        role=invitation.role,
        token="",  # Don't expose full token in validation
        expires_at=invitation.expires_at,
        accepted_at=invitation.accepted_at,
        created_by_id=invitation.created_by_id,
        created_at=invitation.created_at,
        updated_at=invitation.updated_at,
        status=invitation.status,
    )


@router.post(
    "/{organization_id}/invitations/{token}/accept", response_model=InvitationAcceptResponse
)
async def accept_invitation(
    organization_id: int,
    token: str,
    accept_data: InvitationAcceptRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Accept an invitation to join an organization

    This endpoint is public (no authentication required) as it uses the invitation token.

    **Process:**
    1. Validate invitation token and expiration
    2. If user doesn't exist: create new user with provided password/name
    3. If user exists: add to organization
    4. Mark invitation as accepted
    5. Return JWT token for automatic login
    """
    # Get invitation by token (without tenant scoping first to find it)
    invitation_repo = InvitationRepository(db, tenant_id=None)
    invitation = await invitation_repo.get_by_token(token)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invitation token"
        )

    # Use invitation's organization_id (more secure than URL parameter)
    actual_org_id = invitation.organization_id
    org_repo = OrganizationRepository(db)
    org = await org_repo.get_by_id(actual_org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    # Validate organization matches URL parameter (if provided)
    if organization_id and actual_org_id != organization_id:
        logger.warning(
            f"Organization ID mismatch: URL={organization_id}, Invitation={actual_org_id}",
            invitation_id=invitation.id,
        )
        # Use invitation's organization_id for safety

    # Check if already accepted
    if invitation.is_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has already been accepted",
        )

    # Check if expired
    if invitation.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation has expired"
        )

    # Enforce plan user limits before assigning/creating membership.
    await validate_user_limit(actual_org_id, org.subscription_plan, db)

    # Get or create user
    existing_user = await db.execute(select(User).where(User.email == invitation.email))
    user = existing_user.scalar_one_or_none()

    if user:
        # User exists - check if already in another organization
        if user.organization_id and user.organization_id != actual_org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {invitation.email} is already a member of another organization",
            )

        # Add user to organization
        user.organization_id = actual_org_id
        user.role = invitation.role
        user.role_type = "tenant"  # Invited users are always tenant users

        await db.commit()
        await db.refresh(user)

        logger.info(
            f"Existing user {user.id} added to organization {actual_org_id} via invitation",
            invitation_id=invitation.id,
        )
    else:
        # User doesn't exist - create new user
        if not accept_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required for new users"
            )

        if not accept_data.full_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Full name is required for new users",
            )

        from app.core.security import get_password_hash

        user = User(
            email=invitation.email,
            full_name=accept_data.full_name,
            hashed_password=get_password_hash(accept_data.password),
            organization_id=actual_org_id,
            role=invitation.role,
            role_type="tenant",
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(
            f"New user {user.id} created and added to organization {actual_org_id} via invitation",
            invitation_id=invitation.id,
        )

    # Mark invitation as accepted (use repo with correct tenant_id)
    invitation_repo_org = InvitationRepository(db, tenant_id=actual_org_id)
    invitation = await invitation_repo_org.accept_invitation(invitation)
    await db.commit()

    # Generate JWT token for automatic login
    from datetime import timedelta

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(days=30),  # Longer expiry for invitation acceptance
    )

    logger.info(
        f"Invitation {invitation.id} accepted by user {user.id}", organization_id=actual_org_id
    )

    # Get organization name for response (already loaded above).
    org_name = org.name

    return InvitationAcceptResponse(
        success=True,
        message=f"Successfully joined {org_name}",
        access_token=access_token,
        user_id=user.id,
        organization_id=actual_org_id,
    )
