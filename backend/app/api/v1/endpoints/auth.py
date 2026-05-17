"""
Authentication endpoints
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.email import (
    generate_password_reset_email_html,
    generate_password_reset_email_text,
    send_email,
)
from app.core.logging import get_logger
from app.core.rate_limiting import limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SwitchOrganizationRequest,
    TokenResponse,
    UserResponse,
    UserUpdate,
    VerifyEmailRequest,
    VerifyEmailResponse,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # Rate limit: 5 login attempts per minute per IP
async def email_password_login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate using email and password stored in the database."""

    normalized_email = payload.email.strip().lower()

    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()

    if user is None or not user.hashed_password:
        # Log failed login attempt
        from app.core.audit import AuditAction, AuditService

        await AuditService.log_action(
            db=db,
            action=AuditAction.USER_LOGIN_FAILED,
            request=request,
            details={"email": normalized_email, "reason": "user_not_found"},
            status="failure",
            error_message="User not found or no password set",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    if not verify_password(payload.password, user.hashed_password):
        # Log failed login attempt
        from app.core.audit import AuditAction, AuditService

        await AuditService.log_action(
            db=db,
            action=AuditAction.USER_LOGIN_FAILED,
            user_id=user.id,
            organization_id=user.organization_id,
            request=request,
            details={"email": normalized_email, "reason": "invalid_password"},
            status="failure",
            error_message="Invalid password",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    from app.core.permissions import get_user_role, get_user_role_type

    # Validate organization_id based on role_type
    role_type = get_user_role_type(user)
    if role_type == "tenant" and user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no pertenece a ninguna organización",
        )
    # Support users can have NULL organization_id

    # Get role_type (infer from role if not set for backward compatibility)
    from app.core.permissions import get_user_role_type

    role_type = get_user_role_type(user)

    token_data_jwt = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.full_name,
        "organization_id": user.organization_id,  # Multi-tenant: include in JWT
        "role_type": role_type,  # Include role_type in JWT
    }
    access_token = create_access_token(token_data_jwt)
    refresh_token = create_refresh_token(token_data_jwt)

    user_role = get_user_role(user)

    # Log successful login
    from app.core.audit import AuditAction, AuditService

    await AuditService.log_action(
        db=db,
        action=AuditAction.USER_LOGIN,
        user_id=user.id,
        organization_id=user.organization_id,
        request=request,
        details={"email": normalized_email, "role": user_role},
        status="success",
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user_role,
            "organization_id": user.organization_id,  # Multi-tenant: include in response
            "email_verified": bool(getattr(user, "email_verified", True)),
        },
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
async def refresh_session_token(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token and rotate refresh token."""
    refresh_payload = decode_refresh_token(payload.refresh_token)
    if refresh_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id_str = refresh_payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
        )

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    from app.core.permissions import get_user_role, get_user_role_type

    role_type = get_user_role_type(user)
    if role_type == "tenant" and user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no pertenece a ninguna organización",
        )

    token_data_jwt = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.full_name,
        "organization_id": user.organization_id,
        "role_type": role_type,
    }
    access_token = create_access_token(token_data_jwt)
    refresh_token = create_refresh_token(token_data_jwt)
    user_role = get_user_role(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user_role,
            "organization_id": user.organization_id,
            "email_verified": bool(getattr(user, "email_verified", True)),
        },
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Request password reset email for an account."""
    normalized_email = payload.email.strip().lower()
    generic_message = (
        "Si hay una cuenta con ese correo, deberias recibir un enlace para restablecer "
        "la contrasena en unos minutos. Revisa tambien spam."
    )

    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()
    if not user:
        logger.info(
            "Password reset requested for non-existing email",
            email=normalized_email,
        )
        return ForgotPasswordResponse(message=generic_message)

    reset_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "purpose": "password_reset",
        },
        expires_delta=timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    )
    reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={reset_token}"
    html_body = generate_password_reset_email_html(
        full_name=user.full_name,
        reset_url=reset_url,
        expiration_minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
    )
    text_body = generate_password_reset_email_text(
        full_name=user.full_name,
        reset_url=reset_url,
        expiration_minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
    )

    resend_reset_tpl = (settings.RESEND_TEMPLATE_PASSWORD_RESET_ID or "").strip()
    email_log_ctx = {"email_event": "password_reset", "user_id": user.id}
    if resend_reset_tpl:
        background_tasks.add_task(
            send_email,
            to_email=user.email,
            subject="Recuperacion de contrasena - Nougram",
            body_html="",
            body_text=None,
            resend_template_id=resend_reset_tpl,
            template_data={
                "full_name": user.full_name or "",
                "reset_url": reset_url,
                "expiration_minutes": settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
            },
            log_context=email_log_ctx,
        )
    else:
        background_tasks.add_task(
            send_email,
            to_email=user.email,
            subject="Recuperacion de contrasena - Nougram",
            body_html=html_body,
            body_text=text_body,
            log_context=email_log_ctx,
        )

    return ForgotPasswordResponse(message=generic_message)


@router.post("/reset-password", response_model=ResetPasswordResponse)
@limiter.limit("10/minute")
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset account password with a valid reset token."""
    try:
        token_payload = jwt.decode(
            payload.token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido o expirado",
        )

    if token_payload.get("purpose") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido para recuperacion de contrasena",
        )

    user_id_str = token_payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido",
        )

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    if token_payload.get("email") != user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido",
        )

    user.hashed_password = get_password_hash(payload.new_password)
    await db.commit()

    logger.info(
        "Password reset completed",
        user_id=user.id,
        email=user.email,
    )
    return ResetPasswordResponse(message="Contrasena actualizada correctamente")


@router.post("/verify-email", response_model=VerifyEmailResponse)
@limiter.limit("10/minute")
async def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify account email with a valid verification token."""
    try:
        token_payload = jwt.decode(
            payload.token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido o expirado",
        )

    if token_payload.get("purpose") != "email_verification":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido para verificacion de correo",
        )

    user_id_str = token_payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido",
        )

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    if token_payload.get("email") != user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido",
        )

    if bool(getattr(user, "email_verified", False)):
        return VerifyEmailResponse(message="Tu correo ya esta verificado")

    user.email_verified = True
    user.email_verified_at = datetime.utcnow()
    await db.commit()

    logger.info(
        "Email verified successfully",
        user_id=user.id,
        email=user.email,
    )
    return VerifyEmailResponse(message="Correo verificado correctamente")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    from app.core.permissions import get_user_role

    user_role = get_user_role(current_user)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        has_calendar_connected=current_user.google_refresh_token is not None,
        role=user_role,  # Explicit string
        organization_id=current_user.organization_id,  # Multi-tenant: include organization_id
        email_verified=bool(getattr(current_user, "email_verified", True)),
        job_title=current_user.job_title,
        specialty=current_user.specialty,
        bio=current_user.bio,
        linkedin_url=current_user.linkedin_url,
        portfolio_url=current_user.portfolio_url,
        instagram_url=current_user.instagram_url,
        behance_url=current_user.behance_url,
        timezone=current_user.timezone,
        language=current_user.language,
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user_info(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile information."""
    if (
        payload.full_name is None
        and payload.job_title is None
        and payload.specialty is None
        and payload.bio is None
        and payload.linkedin_url is None
        and payload.portfolio_url is None
        and payload.instagram_url is None
        and payload.behance_url is None
        and payload.timezone is None
        and payload.language is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile fields provided",
        )

    if payload.full_name is not None:
        full_name = payload.full_name.strip()
        if not full_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre no puede estar vacío",
            )
        current_user.full_name = full_name
    if payload.job_title is not None:
        current_user.job_title = payload.job_title.strip() or None
    if payload.specialty is not None:
        current_user.specialty = payload.specialty.strip() or None
    if payload.bio is not None:
        current_user.bio = payload.bio.strip() or None
    if payload.linkedin_url is not None:
        current_user.linkedin_url = payload.linkedin_url.strip() or None
    if payload.portfolio_url is not None:
        current_user.portfolio_url = payload.portfolio_url.strip() or None
    if payload.instagram_url is not None:
        current_user.instagram_url = payload.instagram_url.strip() or None
    if payload.behance_url is not None:
        current_user.behance_url = payload.behance_url.strip() or None
    if payload.timezone is not None:
        current_user.timezone = payload.timezone.strip() or None
    if payload.language is not None:
        current_user.language = payload.language.strip() or None

    await db.commit()
    await db.refresh(current_user)

    from app.core.permissions import get_user_role

    user_role = get_user_role(current_user)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        has_calendar_connected=current_user.google_refresh_token is not None,
        role=user_role,
        organization_id=current_user.organization_id,
        email_verified=bool(getattr(current_user, "email_verified", True)),
        job_title=current_user.job_title,
        specialty=current_user.specialty,
        bio=current_user.bio,
        linkedin_url=current_user.linkedin_url,
        portfolio_url=current_user.portfolio_url,
        instagram_url=current_user.instagram_url,
        behance_url=current_user.behance_url,
        timezone=current_user.timezone,
        language=current_user.language,
    )


@router.post("/me/change-password", response_model=ChangePasswordResponse)
async def change_current_user_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current authenticated user password."""
    if not current_user.hashed_password or not verify_password(
        payload.current_password,
        current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta",
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe ser diferente a la actual",
        )

    current_user.hashed_password = get_password_hash(payload.new_password)
    await db.commit()

    logger.info(
        "Password changed from profile",
        user_id=current_user.id,
        email=current_user.email,
    )
    return ChangePasswordResponse(message="Contraseña actualizada correctamente")


@router.post("/switch-organization", response_model=TokenResponse)
async def switch_organization(
    payload: SwitchOrganizationRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Switch the active organization for the current user.

    This endpoint generates a new JWT token with the requested organization_id.
    The user must have access to the requested organization.

    **Permissions:**
    - Support users (super_admin, support_manager, data_analyst) can switch to any organization
    - Tenant users can only switch to their own organization (if they belong to it)
    """
    from app.core.audit import AuditAction, AuditService
    from app.core.permissions import can_user_access_tenant, get_user_role, get_user_role_type
    from app.models.organization import Organization

    organization_id = payload.organization_id

    # Validate that the organization exists
    org_result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = org_result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    # Check if user can access this organization
    role_type = get_user_role_type(current_user)

    if role_type == "tenant":
        # Tenant users can only switch to their own organization
        if current_user.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only switch to your own organization",
            )
    elif role_type == "support":
        # Support users can switch to any organization
        # Use can_user_access_tenant to verify access
        if not can_user_access_tenant(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this organization",
            )
    else:
        # Unknown role type
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Unable to determine user role type"
        )

    # Generate new token with the requested organization_id
    token_data_jwt = {
        "sub": str(current_user.id),
        "email": current_user.email,
        "name": current_user.full_name,
        "organization_id": organization_id,  # New organization_id
        "role_type": role_type,
    }
    access_token = create_access_token(token_data_jwt)

    user_role = get_user_role(current_user)

    # Log organization switch
    await AuditService.log_action(
        db=db,
        action=AuditAction.USER_SWITCH_ORGANIZATION,
        user_id=current_user.id,
        organization_id=organization_id,
        request=request,
        details={
            "action": "switch_organization",
            "from_org_id": current_user.organization_id,
            "to_org_id": organization_id,
            "role": user_role,
        },
        status="success",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": user_role,
            "organization_id": organization_id,  # New organization_id
        },
    )
