"""
Phase 2 Recycle Bin & Retention Policy API Endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user, require_role
from app.models.user import User, UserRole
from app.services.recycle_bin_service import get_recycle_bin_service, RecycleBinService
from app.services.retention_policy_service import get_retention_policy_service, RetentionPolicyService

router = APIRouter()


# Recycle Bin Endpoints

@router.get("/sites/{site_id}/recycle-bin")
async def get_site_recycle_bin(
    site_id: str,
    stage: str = Query("first", regex="^(first|second)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    bin_service: RecycleBinService = Depends(get_recycle_bin_service)
):
    """Get recycle bin contents for a site"""
    stats = await bin_service.scan_recycle_bin(site_id, stage=stage)
    return stats


@router.post("/sites/{site_id}/recycle-bin/clean")
async def cleanup_recycle_bin(
    site_id: str,
    older_than_days: int = Query(90, ge=30, le=365),
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
    bin_service: RecycleBinService = Depends(get_recycle_bin_service)
):
    """Clean up second-stage recycle bin"""
    result = await bin_service.cleanup_second_stage(
        site_id=site_id,
        older_than_days=older_than_days
    )
    return result


@router.get("/recycle-bin/summary")
async def get_recycle_bin_summary(
    site_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    bin_service: RecycleBinService = Depends(get_recycle_bin_service)
):
    """Get recycle bin summary (tenant-wide or site-specific)"""
    summary = await bin_service.get_bin_summary(site_id=site_id)
    return summary


@router.post("/recycle-bin/{item_id}/restore")
async def restore_bin_item(
    item_id: str,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SITE_OWNER)),
    db: Session = Depends(get_db),
    bin_service: RecycleBinService = Depends(get_recycle_bin_service)
):
    """Restore an item from recycle bin"""
    success = await bin_service.restore_item(item_id)
    return {"success": success, "item_id": item_id}


# Retention Policy Endpoints

class ExclusionRequest(BaseModel):
    site_id: str
    policy_id: str
    reason: str


@router.post("/retention/sync")
async def sync_retention_policies(
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db),
    retention_service: RetentionPolicyService = Depends(get_retention_policy_service)
):
    """Sync retention policies from Microsoft Purview"""
    stats = await retention_service.sync_policies_from_purview()
    return stats


@router.get("/retention/policies")
async def list_retention_policies(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all retention policies"""
    from app.models.retention import RetentionPolicy
    policies = db.query(RetentionPolicy).filter(RetentionPolicy.is_active == True).all()
    return {
        "policies": [{
            "policy_id": str(p.policy_id),
            "name": p.policy_name,
            "description": p.description,
            "retention_period_days": p.retention_period_days,
            "scope": p.scope,
        } for p in policies]
    }


@router.post("/retention/exclusions")
async def request_retention_exclusion(
    request: ExclusionRequest,
    user: User = Depends(require_role(UserRole.SITE_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    retention_service: RetentionPolicyService = Depends(get_retention_policy_service)
):
    """Request a site to be excluded from a retention policy"""
    exclusion = await retention_service.request_exclusion(
        site_id=request.site_id,
        policy_id=request.policy_id,
        user_id=str(user.user_id),
        reason=request.reason
    )
    return {
        "exclusion_id": str(exclusion.exclusion_id),
        "status": exclusion.status,
    }


@router.put("/retention/exclusions/{exclusion_id}/approve")
async def approve_retention_exclusion(
    exclusion_id: str,
    comments: Optional[str] = None,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db),
    retention_service: RetentionPolicyService = Depends(get_retention_policy_service)
):
    """Approve a retention exclusion request"""
    exclusion = await retention_service.approve_exclusion(
        exclusion_id=exclusion_id,
        approver_user_id=str(user.user_id),
        comments=comments
    )
    return {
        "exclusion_id": str(exclusion.exclusion_id),
        "status": exclusion.status,
    }


@router.delete("/retention/exclusions/{exclusion_id}")
async def remove_retention_exclusion(
    exclusion_id: str,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db),
    retention_service: RetentionPolicyService = Depends(get_retention_policy_service)
):
    """Remove a site from retention exclusion list"""
    exclusion = await retention_service.remove_exclusion(
        exclusion_id=exclusion_id,
        remover_user_id=str(user.user_id)
    )
    return {
        "exclusion_id": str(exclusion.exclusion_id),
        "status": exclusion.status,
    }


@router.get("/retention/compliance")
async def get_retention_compliance_status(
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db),
    retention_service: RetentionPolicyService = Depends(get_retention_policy_service)
):
    """Get compliance status for all sites"""
    status = await retention_service.get_compliance_status()
    return {"sites": status}


import logging
logger = logging.getLogger(__name__)
