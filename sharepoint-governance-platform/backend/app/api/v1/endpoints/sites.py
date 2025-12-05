"""
Sites API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Background Tasks
from sqlalchemy.orm import Session
from sqlalchemy import or_
import uuid

from app.api.deps import get_db, get_current_user, require_role
from app.models.user import User, UserRole
from app.models.site import SharePointSite, SiteOwnership, AccessMatrix, SiteClassification
from app.schemas.site import (
    SiteResponse, SiteListResponse, SiteHealthResponse,
    SiteDiscoveryResponse, SiteOwnerResponse, SiteAccessResponse,
    SiteClassificationEnum
)
from app.services.site_discovery_service import SiteDiscoveryService

router = APIRouter()


@router.get("/", response_model=SiteListResponse)
async def list_sites(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    classification: Optional[SiteClassificationEnum] = None,
    search: Optional[str] = None,
    is_archived: Optional[bool] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all SharePoint sites with filters and pagination
    
    - Site owners see only their sites
    - Admins see all sites
    - Filters: classification, search, archived status
    """
    query = db.query(SharePointSite)
    
    # Role-based filtering
    if user.role == UserRole.SITE_OWNER:
        # Filter to sites where user is owner
        query = query.join(SiteOwnership).filter(SiteOwnership.user_id == user.user_id)
    
    # Apply filters
    if classification:
        query = query.filter(SharePointSite.classification == classification.value)
    
    if search:
        query = query.filter(
            or_(
                SharePointSite.name.ilike(f"%{search}%"),
                SharePointSite.site_url.ilike(f"%{search}%")
            )
        )
    
    if is_archived is not None:
        query = query.filter(SharePointSite.is_archived == is_archived)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    sites = query.offset(skip).limit(limit).all()
    
    return SiteListResponse(
        total=total,
        sites=[SiteResponse.from_orm(site) for site in sites],
        skip=skip,
        limit=limit
    )


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific site
    
    - Site owners can get their own sites
    - Admins can get any site
    """
    # Validate UUID
    try:
        uuid.UUID(site_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid site ID format")
    
    site = db.query(SharePointSite).filter(SharePointSite.site_id == site_id).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Check permissions
    if user.role == UserRole.SITE_OWNER:
        # Verify user owns this site
        ownership = db.query(SiteOwnership).filter(
            SiteOwnership.site_id == site_id,
            SiteOwnership.user_id == user.user_id
        ).first()
        
        if not ownership:
            raise HTTPException(status_code=403, detail="You do not own this site")
    
    return SiteResponse.from_orm(site)


@router.get("/{site_id}/health", response_model=SiteHealthResponse)
async def get_site_health(
    site_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get health metrics for a site
    
    Health score is calculated based on:
    - Recent activity (weight: 30)
    - Storage usage (weight: 20)
    - Owner status (weight: 30)
    - Pending reviews (weight: 20)
    """
    try:
        uuid.UUID(site_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid site ID format")
    
    site = db.query(SharePointSite).filter(SharePointSite.site_id == site_id).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Check permissions
    if user.role == UserRole.SITE_OWNER:
        ownership = db.query(SiteOwnership).filter(
            SiteOwnership.site_id == site_id,
            SiteOwnership.user_id == user.user_id
        ).first()
        
        if not ownership:
            raise HTTPException(status_code=403, detail="You do not own this site")
    
    # Calculate health metrics
    from datetime import datetime, timedelta
    
    issues = []
    health_score = 100
    
    # Check activity
    last_activity_days = None
    if site.last_activity:
        last_activity_days = (datetime.utcnow() - site.last_activity).days
        if last_activity_days > 180:
            health_score -= 30
            issues.append("No activity in 180+ days")
        elif last_activity_days > 90:
            health_score -= 15
            issues.append("No activity in 90+ days")
    else:
        health_score -= 30
        issues.append("No activity data available")
    
    # Check storage
    storage_usage_percent = site.storage_usage_percent
    if storage_usage_percent > 90:
        health_score -= 20
        issues.append("Storage usage >90%")
    elif storage_usage_percent > 75:
        health_score -= 10
        issues.append("Storage usage >75%")
    
    # Check owners
    owners = db.query(SiteOwnership).filter(SiteOwnership.site_id == site_id).all()
    owner_count = len(owners)
    has_primary_owner = any(o.is_primary_owner for o in owners)
    
    if not has_primary_owner:
        health_score -= 30
        issues.append("No primary owner assigned")
    elif owner_count == 1:
        health_score -= 10
        issues.append("Only one owner (no redundancy)")
    
    # Check pending reviews (placeholder - to be implemented)
    pending_access_reviews = 0  # TODO: Query AccessReviewCycle
    
    # Ensure score doesn't go below 0
    health_score = max(0, health_score)
    
    return SiteHealthResponse(
        site_id=str(site.site_id),
        site_name=site.name,
        health_score=health_score,
        last_activity_days=last_activity_days,
        storage_usage_percent=storage_usage_percent,
        owner_count=owner_count,
        has_primary_owner=has_primary_owner,
        pending_access_reviews=pending_access_reviews,
        issues=issues
    )


@router.get("/{site_id}/owners", response_model=List[SiteOwnerResponse])
async def get_site_owners(
    site_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all owners of a site"""
    try:
        uuid.UUID(site_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid site ID format")
    
    site = db.query(SharePointSite).filter(SharePointSite.site_id == site_id).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Check permissions
    if user.role == UserRole.SITE_OWNER:
        ownership = db.query(SiteOwnership).filter(
            SiteOwnership.site_id == site_id,
            SiteOwnership.user_id == user.user_id
        ).first()
        
        if not ownership:
            raise HTTPException(status_code=403, detail="You do not own this site")
    
    owners = db.query(SiteOwnership).filter(SiteOwnership.site_id == site_id).all()
    
    return [SiteOwnerResponse.from_orm(owner) for owner in owners]


@router.get("/{site_id}/access", response_model=List[SiteAccessResponse])
async def get_site_access(
    site_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get access matrix for a site"""
    try:
        uuid.UUID(site_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid site ID format")
    
    site = db.query(SharePointSite).filter(SharePointSite.site_id == site_id).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Check permissions
    if user.role == UserRole.SITE_OWNER:
        ownership = db.query(SiteOwnership).filter(
            SiteOwnership.site_id == site_id,
            SiteOwnership.user_id == user.user_id
        ).first()
        
        if not ownership:
            raise HTTPException(status_code=403, detail="You do not own this site")
    
    access_list = db.query(AccessMatrix).filter(AccessMatrix.site_id == site_id).all()
    
    return [SiteAccessResponse.from_orm(access) for access in access_list]


@router.post("/discover", response_model=SiteDiscoveryResponse)
async def trigger_site_discovery(
    background_tasks: BackgroundTasks,
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Trigger site discovery job (admin only)
    
    Discovers all SharePoint sites and updates the database.
    Runs as a background task.
    """
    job_id = str(uuid.uuid4())
    
    # Run discovery in background
    async def run_discovery():
        try:
            discovery_service = SiteDiscoveryService(db)
            stats = await discovery_service.discover_all_sites()
            # TODO: Store job results in database
        except Exception as e:
            logger.error(f"Site discovery job {job_id} failed: {str(e)}")
    
    background_tasks.add_task(run_discovery)
    
    return SiteDiscoveryResponse(
        job_id=job_id,
        status="initiated",
        message="Site discovery job started in background"
    )


import logging
logger = logging.getLogger(__name__)
