"""
Multi-Tenant Management API Endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, require_role
from app.models.user import User, UserRole
from app.services.tenant_service import get_tenant_service, TenantManagementService

router = APIRouter()


class TenantCreate(BaseModel):
    tenant_name: str
    domain: str
    admin_email: str
    config: Optional[dict] = None


class TenantConfigUpdate(BaseModel):
    config: dict


@router.post("/tenants")
async def create_tenant(
    request: TenantCreate,
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
    tenant_service: TenantManagementService = Depends(get_tenant_service)
):
    """
    Create a new tenant
    
    Requires super admin role
    """
    tenant = await tenant_service.create_tenant(
        tenant_name=request.tenant_name,
        domain=request.domain,
        admin_email=request.admin_email,
        config=request.config
    )
    return tenant


@router.get("/tenants")
async def list_tenants(
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
    tenant_service: TenantManagementService = Depends(get_tenant_service)
):
    """List all tenants"""
    tenants = await tenant_service.list_tenants()
    return {"tenants": tenants}


@router.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
    tenant_service: TenantManagementService = Depends(get_tenant_service)
):
    """Get tenant details"""
    tenant = await tenant_service.get_tenant(tenant_id)
    return tenant


@router.put("/tenants/{tenant_id}/config")
async def update_tenant_config(
    tenant_id: str,
    request: TenantConfigUpdate,
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
    tenant_service: TenantManagementService = Depends(get_tenant_service)
):
    """Update tenant configuration"""
    tenant = await tenant_service.update_tenant_config(tenant_id, request.config)
    return tenant


@router.delete("/tenants/{tenant_id}")
async def deactivate_tenant(
    tenant_id: str,
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
    tenant_service: TenantManagementService = Depends(get_tenant_service)
):
    """Deactivate a tenant"""
    result = await tenant_service.deactivate_tenant(tenant_id)
    return result


@router.get("/cross-tenant/report")
async def get_cross_tenant_report(
    metric: str = "sites_count",
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.EXECUTIVE)),
    db: Session = Depends(get_db),
    tenant_service: TenantManagementService = Depends(get_tenant_service)
):
    """Get cross-tenant analytics report"""
    report = await tenant_service.get_cross_tenant_report(metric=metric)
    return {"metric": metric, "data": report}


import logging
logger = logging.getLogger(__name__)
