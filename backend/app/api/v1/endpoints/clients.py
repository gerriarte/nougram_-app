"""
Client management endpoints (master catalog).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant import get_tenant_context, TenantContext
from app.core.exceptions import ResourceNotFoundError
from app.models.user import User
from app.services.client_service import ClientService
from app.schemas.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientListResponse,
    ClientSearchItem,
    ClientSearchResponse,
)

router = APIRouter()


@router.get("/", response_model=ClientListResponse)
async def list_clients(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: str = Query(None, description="Filter by status: active | inactive"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List clients with optional status filter and pagination."""
    service = ClientService(db, tenant.organization_id)
    items, total = await service.list_clients(status_filter=status, page=page, page_size=page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return ClientListResponse(
        items=[ClientResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/search", response_model=ClientSearchResponse)
async def search_clients(
    q: str = Query(..., min_length=2, description="Search query (display name, contact, email)"),
    limit: int = Query(10, ge=1, le=50),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search clients for autocomplete (e.g. quote builder selector)."""
    service = ClientService(db, tenant.organization_id)
    clients = await service.search(q=q, limit=limit)
    items = [
        ClientSearchItem(id=c.id, display_name=c.display_name, requester_name=c.requester_name, email=c.email)
        for c in clients
    ]
    return ClientSearchResponse(items=items, total=len(items))


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: ClientCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new client in the master catalog."""
    service = ClientService(db, tenant.organization_id)
    client = await service.create(data)
    return ClientResponse.model_validate(client)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a client by ID."""
    service = ClientService(db, tenant.organization_id)
    client = await service.get_by_id(client_id)
    if not client:
        raise ResourceNotFoundError("Client", client_id)
    return ClientResponse.model_validate(client)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    data: ClientUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a client."""
    service = ClientService(db, tenant.organization_id)
    try:
        client = await service.update(client_id, data)
        return ClientResponse.model_validate(client)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
