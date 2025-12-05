"""
Phase 2 Storage & Version Management API Endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_role
from app.models.user import User, UserRole
from app.services.version_management_service import get_version_management_service, VersionManagementService
from app.services.storage_analytics_service import get_storage_analytics_service, StorageAnalyticsService

router = APIRouter()


@router.get("/libraries/{library_id}/versions")
async def get_library_version_stats(
    library_id: str,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SITE_OWNER)),
    db: Session = Depends(get_db),
    version_service: VersionManagementService = Depends(get_version_management_service)
):
    """Get version statistics for a document library"""
    stats = await version_service.scan_library_versions(library_id)
    return stats


@router.post("/libraries/{library_id}/cleanup-versions")
async def cleanup_library_versions(
    library_id: str,
    retention_days: int = Query(90, ge=30, le=365),
    keep_minimum: int = Query(3, ge=1, le=10),
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
    version_service: VersionManagementService = Depends(get_version_management_service)
):
    """Trigger version cleanup for a library"""
    result = await version_service.cleanup_old_versions(
        library_id=library_id,
        retention_days=retention_days,
        keep_minimum=keep_minimum
    )
    return result


@router.get("/sites/{site_id}/version-recommendations")
async def get_version_recommendations(
    site_id: str,
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.SITE_OWNER)),
    db: Session = Depends(get_db),
    version_service: VersionManagementService = Depends(get_version_management_service)
):
    """Get version cleanup recommendations for a site"""
    recommendations = await version_service.get_version_recommendations(site_id)
    return {"recommendations": recommendations}


@router.get("/storage/summary")
async def get_storage_summary(
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.EXECUTIVE)),
    db: Session = Depends(get_db),
    storage_service: StorageAnalyticsService = Depends(get_storage_analytics_service)
):
    """Get tenant-wide storage summary"""
    summary = await storage_service.get_tenant_storage_summary()
    return summary


@router.get("/storage/trends")
async def get_storage_trends(
    site_id: Optional[str] = None,
    days: int = Query(30, ge=7, le=365),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage_service: StorageAnalyticsService = Depends(get_storage_analytics_service)
):
    """Get storage trend data"""
    trends = await storage_service.get_storage_trends(site_id=site_id, days=days)
    return {"trends": trends}


@router.get("/storage/recommendations")
async def get_storage_recommendations(
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
    storage_service: StorageAnalyticsService = Depends(get_storage_analytics_service)
):
    """Get storage optimization recommendations"""
    recommendations = await storage_service.get_storage_recommendations()
    return {"recommendations": recommendations}


@router.get("/sites/{site_id}/storage-breakdown")
async def get_site_storage_breakdown(
    site_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage_service: StorageAnalyticsService = Depends(get_storage_analytics_service)
):
    """Get storage breakdown by library for a site"""
    breakdown = await storage_service.get_library_storage_breakdown(site_id)
    return {"libraries": breakdown}


import logging
logger = logging.getLogger(__name__)
