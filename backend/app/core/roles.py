"""
Role definitions for the multi-tenant platform

Two levels of roles:
1. Support roles (multi-tenant managers) - can access multiple organizations
2. Tenant roles (client users) - restricted to their organization
"""

# Support roles (multi-tenant managers)
SUPPORT_ROLES: set[str] = {
    "super_admin",
    "support_manager",
    "data_analyst",
}

# Tenant roles (client users within an organization)
TENANT_ROLES: set[str] = {
    "owner",
    "admin_financiero",
    "product_manager",
    "collaborator",
}

# All valid roles
ALL_ROLES: set[str] = SUPPORT_ROLES | TENANT_ROLES


def is_support_role(role: str | None) -> bool:
    """Check if a role is a support role"""
    return role in SUPPORT_ROLES if role else False


def is_tenant_role(role: str | None) -> bool:
    """Check if a role is a tenant role"""
    return role in TENANT_ROLES if role else False


def get_role_type(role: str | None) -> str | None:
    """
    Get role type ("support" or "tenant") for a given role

    Args:
        role: Role name

    Returns:
        "support", "tenant", or None if role is invalid
    """
    if not role:
        return None

    if role in SUPPORT_ROLES:
        return "support"
    elif role in TENANT_ROLES:
        return "tenant"
    else:
        return None


def validate_role_type_and_organization(
    role_type: str | None, role: str | None, organization_id: int | None
) -> tuple[bool, str | None]:
    """
    Validate that role_type, role, and organization_id are consistent

    Args:
        role_type: "support", "tenant", or None
        role: Role name
        organization_id: Organization ID

    Returns:
        (is_valid, error_message)
    """
    # If role_type is None, infer from role
    if role_type is None and role:
        inferred_type = get_role_type(role)
        if inferred_type:
            role_type = inferred_type

    # Support roles can have NULL organization_id
    if role_type == "support":
        if role and role not in SUPPORT_ROLES:
            return False, f"Role '{role}' is not a valid support role"
        # organization_id can be NULL for support roles
        return True, None

    # Tenant roles must have organization_id
    if role_type == "tenant" or role_type is None:
        if organization_id is None:
            return False, "Tenant users must have an organization_id"
        if role and role not in TENANT_ROLES:
            return False, f"Role '{role}' is not a valid tenant role"
        return True, None

    return False, f"Invalid role_type: {role_type}"


# Role descriptions for documentation
ROLE_DESCRIPTIONS: dict[str, str] = {
    # Support roles
    "super_admin": "Control total de la plataforma. Puede acceder a todas las organizaciones y realizar cualquier acción.",
    "support_manager": "Gestor de Clientes. Acceso limitado, datos anonimizados. Puede gestionar múltiples organizaciones.",
    "data_analyst": "Analista de Datos. Solo acceso a datasets anonimizados para análisis.",
    # Tenant roles
    "owner": "Dueño de la cuenta. Único que puede pagar, acceso completo a su organización.",
    "admin_financiero": "Administrador financiero. Ve costos sensibles, gestiona costos y configuraciones financieras.",
    "product_manager": "Product Manager. Crea propuestas y cotizaciones, consume créditos.",
    "collaborator": "Colaborador. Puede crear borradores, NO puede enviar cotizaciones, NO ve costos.",
}
