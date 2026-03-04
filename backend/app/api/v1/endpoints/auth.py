"""
Authentication endpoints
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_current_user, verify_password, get_password_hash
from app.core.rate_limiting import limiter, get_rate_limit_for_plan
from app.core.email import (
    send_email,
    generate_password_reset_email_html,
    generate_password_reset_email_text,
)
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    UserUpdate,
    SwitchOrganizationRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
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
        from app.core.audit import AuditService, AuditAction
        await AuditService.log_action(
            db=db,
            action=AuditAction.USER_LOGIN_FAILED,
            request=request,
            details={"email": normalized_email, "reason": "user_not_found"},
            status="failure",
            error_message="User not found or no password set"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    if not verify_password(payload.password, user.hashed_password):
        # Log failed login attempt
        from app.core.audit import AuditService, AuditAction
        await AuditService.log_action(
            db=db,
            action=AuditAction.USER_LOGIN_FAILED,
            user_id=user.id,
            organization_id=user.organization_id,
            request=request,
            details={"email": normalized_email, "reason": "invalid_password"},
            status="failure",
            error_message="Invalid password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    if not bool(getattr(user, "email_verified", True)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debes verificar tu correo antes de iniciar sesión",
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

    user_role = get_user_role(user)

    # Log successful login
    from app.core.audit import AuditService, AuditAction
    await AuditService.log_action(
        db=db,
        action=AuditAction.USER_LOGIN,
        user_id=user.id,
        organization_id=user.organization_id,
        request=request,
        details={"email": normalized_email, "role": user_role},
        status="success"
    )

    return TokenResponse(
        access_token=access_token,
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


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request password reset email for an account."""
    normalized_email = payload.email.strip().lower()
    generic_message = "Si el correo existe, enviaremos instrucciones para restablecer la contrasena."

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

    email_sent = await send_email(
        to_email=user.email,
        subject="Recuperacion de contrasena - Nougram",
        body_html=html_body,
        body_text=text_body,
    )
    if not email_sent:
        logger.warning(
            "Failed to send password reset email",
            user_id=user.id,
            email=user.email,
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
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
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
    )

@router.put("/me", response_model=UserResponse)
async def update_current_user_info(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile information."""

    current_user.full_name = payload.full_name
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
        email_verified=bool(getattr(current_user, "email_verified", True)),
    )


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
    from app.core.permissions import get_user_role_type, can_user_access_tenant, get_user_role
    from app.models.organization import Organization
    from app.core.audit import AuditService, AuditAction
    
    organization_id = payload.organization_id
    
    # Validate that the organization exists
    org_result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check if user can access this organization
    role_type = get_user_role_type(current_user)
    
    if role_type == "tenant":
        # Tenant users can only switch to their own organization
        if current_user.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only switch to your own organization"
            )
    elif role_type == "support":
        # Support users can switch to any organization
        # Use can_user_access_tenant to verify access
        if not can_user_access_tenant(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this organization"
            )
    else:
        # Unknown role type
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to determine user role type"
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
        action=AuditAction.USER_ACTION,
        user_id=current_user.id,
        organization_id=organization_id,
        request=request,
        details={
            "action": "switch_organization",
            "from_org_id": current_user.organization_id,
            "to_org_id": organization_id,
            "role": user_role
        },
        status="success"
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
