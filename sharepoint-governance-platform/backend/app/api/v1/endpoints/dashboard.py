"""
Dashboard API endpoints
"""
from typing import Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.models.site import SharePointSite, SiteOwnership, SiteClassification
from app.models.access_review import AccessReviewCycle, ReviewStatus
from app.models.audit import AuditLog

router = APIRouter()


@router.get("/overview")
async def get_overview_metrics(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard overview metrics
    
    Returns different metrics based on user role:
    - Site Owners: Their sites only
    - Admins: All sites and system-wide metrics
    """
    now = datetime.utcnow()
    
    if user.role == UserRole.SITE_OWNER:
        # Site owner metrics
        owned_sites = db.query(SharePointSite).join(SiteOwnership).filter(
            SiteOwnership.user_id == user.user_id
        ).all()
        
        total_sites = len(owned_sites)
        active_sites = len([s for s in owned_sites if not s.is_archived])
        
        # Pending reviews
        pending_reviews = db.query(AccessReviewCycle).filter(
            AccessReviewCycle.assigned_to_user_id == user.user_id,
            AccessReviewCycle.status.in_([ReviewStatus.PENDING, ReviewStatus.IN_PROGRESS])
        ).count()
        
        # Overdue reviews
        overdue_reviews = db.query(AccessReviewCycle).filter(
            AccessReviewCycle.assigned_to_user_id == user.user_id,
            AccessReviewCycle.status.in_([ReviewStatus.PENDING, ReviewStatus.IN_PROGRESS]),
            AccessReviewCycle.due_date < now
        ).count()
        
        return {
            "user_role": "site_owner",
            "total_sites": total_sites,
            "active_sites": active_sites,
            "archived_sites": total_sites - active_sites,
            "pending_reviews": pending_reviews,
            "overdue_reviews": overdue_reviews,
        }
    
    else:
        # Admin/executive metrics
        total_sites = db.query(SharePointSite).count()
        active_sites = db.query(SharePointSite).filter(SharePointSite.is_archived == False).count()
        
        # Sites by classification
        classification_stats = {}
        for classification in SiteClassification:
            count = db.query(SharePointSite).filter(
                SharePointSite.classification == classification,
                SharePointSite.is_archived == False
            ).count()
            classification_stats[classification.value] = count
        
        # Total storage
        total_storage = db.query(func.sum(SharePointSite.storage_used_mb)).scalar() or 0
        
        # Access reviews
        total_reviews = db.query(AccessReviewCycle).count()
        pending_reviews = db.query(AccessReviewCycle).filter(
            AccessReviewCycle.status.in_([ReviewStatus.PENDING, ReviewStatus.IN_PROGRESS])
        ).count()
        overdue_reviews = db.query(AccessReviewCycle).filter(
            AccessReviewCycle.status.in_([ReviewStatus.PENDING, ReviewStatus.IN_PROGRESS]),
            AccessReviewCycle.due_date < now
        ).count()
        
        # Recent audit activity (last 24 hours)
        yesterday = now - timedelta(hours=24)
        recent_audit_events = db.query(AuditLog).filter(
            AuditLog.event_datetime >= yesterday
        ).count()
        
        # Inactive sites (no activity in 90 days)
        ninety_days_ago = now - timedelta(days=90)
        inactive_sites = db.query(SharePointSite).filter(
            SharePointSite.last_activity < ninety_days_ago,
            SharePointSite.is_archived == False
        ).count()
        
        return {
            "user_role": user.role.value,
            "sites": {
                "total": total_sites,
                "active": active_sites,
                "archived": total_sites - active_sites,
                "inactive_90_days": inactive_sites,
                "by_classification": classification_stats
            },
            "storage": {
                "total_used_mb": int(total_storage),
                "total_used_gb": round(total_storage / 1024, 2)
            },
            "access_reviews": {
                "total": total_reviews,
                "pending": pending_reviews,
                "overdue": overdue_reviews,
                "completed": total_reviews - pending_reviews
            },
            "audit": {
                "events_last_24h": recent_audit_events
            }
        }


@router.get("/owner")
async def get_owner_dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get site owner-specific dashboard data
    
    Returns detailed information about owned sites and pending actions
    """
    # Get owned sites
    owned_sites_query = db.query(SharePointSite).join(SiteOwnership).filter(
        SiteOwnership.user_id == user.user_id
    )
    
    owned_sites = owned_sites_query.all()
    
    # Pending access reviews
    pending_reviews = db.query(AccessReviewCycle).filter(
        AccessReviewCycle.assigned_to_user_id == user.user_id,
        AccessReviewCycle.status.in_([ReviewStatus.PENDING, ReviewStatus.IN_PROGRESS])
    ).all()
    
    # Build site summaries
    sites_summary = []
    for site in owned_sites:
        # Calculate health score (simplified)
        health_score = 100
        
        if site.last_activity:
            days_inactive = (datetime.utcnow() - site.last_activity).days
            if days_inactive > 180:
                health_score -= 30
            elif days_inactive > 90:
                health_score -= 15
        
        storage_usage = site.storage_usage_percent
        if storage_usage > 90:
            health_score -= 20
        elif storage_usage > 75:
            health_score -= 10
        
        sites_summary.append({
            "site_id": str(site.site_id),
            "name": site.name,
            "url": site.site_url,
            "classification": site.classification.value,
            "health_score": max(0, health_score),
            "storage_used_mb": site.storage_used_mb,
            "storage_usage_percent": storage_usage,
            "last_activity": site.last_activity,
            "is_archived": site.is_archived
        })
    
    # Build review summaries
    reviews_summary = []
    for review in pending_reviews:
        site = db.query(SharePointSite).filter(SharePointSite.site_id == review.site_id).first()
        
        reviews_summary.append({
            "review_cycle_id": str(review.review_cycle_id),
            "site_name": site.name if site else "Unknown",
            "due_date": review.due_date,
            "status": review.status.value,
            "is_overdue": review.due_date < datetime.utcnow()
        })
    
    return {
        "owned_sites": sites_summary,
        "pending_reviews": reviews_summary,
        "summary": {
            "total_sites": len(sites_summary),
            "total_pending_reviews": len(reviews_summary)
        }
    }


import logging
logger = logging.getLogger(__name__)
