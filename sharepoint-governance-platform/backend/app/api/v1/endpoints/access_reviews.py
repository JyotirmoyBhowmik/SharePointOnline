"""
Access Review API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime
import uuid

from app.api.deps import get_db, get_current_user, require_role
from app.models.user import User, UserRole
from app.models.access_review import AccessReviewCycle, AccessReviewItem, ReviewStatus, AccessDecision
from app.models.site import SharePointSite
from app.schemas.access_review import (
    AccessReviewCycleResponse, AccessReviewItemResponse,
    CertifyReviewRequest, ReviewDecisionRequest,
    ReviewStatusEnum, AccessDecisionEnum
)

router = APIRouter()


@router.get("/", response_model=List[AccessReviewCycleResponse])
async def list_access_reviews(
    status: Optional[ReviewStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List access review cycles
    
    - Site owners see only their assigned reviews
    - Admins see all reviews
    """
    query = db.query(AccessReviewCycle)
    
    # Role-based filtering
    if user.role == UserRole.SITE_OWNER:
        query = query.filter(AccessReviewCycle.assigned_to_user_id == user.user_id)
    
    # Status filter
    if status:
        query = query.filter(AccessReviewCycle.status == status.value)
    
    # Check for overdue reviews
    now = datetime.utcnow()
    query = query.order_by(AccessReviewCycle.due_date.asc())
    
    reviews = query.offset(skip).limit(limit).all()
    
    # Enhance with statistics
    result = []
    for review in reviews:
        # Count items by status
        items = db.query(AccessReviewItem).filter(
            AccessReviewItem.review_cycle_id == review.review_cycle_id
        )
        
        review_data = AccessReviewCycleResponse.from_orm(review)
        review_data.total_items = items.count()
        review_data.pending_items = items.filter(AccessReviewItem.access_status == AccessDecision.PENDING).count()
        review_data.approved_items = items.filter(AccessReviewItem.access_status == AccessDecision.APPROVED).count()
        review_data.revoked_items = items.filter(AccessReviewItem.access_status == AccessDecision.REVOKE).count()
        
        # Get site name
        site = db.query(SharePointSite).filter(SharePointSite.site_id == review.site_id).first()
        if site:
            review_data.site_name = site.name
        
        # Get assignee email
        assignee = db.query(User).filter(User.user_id == review.assigned_to_user_id).first()
        if assignee:
            review_data.assigned_to_user_email = assignee.email
        
        result.append(review_data)
    
    return result


@router.get("/{review_cycle_id}", response_model=AccessReviewCycleResponse)
async def get_access_review(
    review_cycle_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get access review cycle details"""
    try:
        uuid.UUID(review_cycle_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid review cycle ID format")
    
    review = db.query(AccessReviewCycle).filter(
        AccessReviewCycle.review_cycle_id == review_cycle_id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review cycle not found")
    
    # Check permissions
    if user.role == UserRole.SITE_OWNER and review.assigned_to_user_id != user.user_id:
        raise HTTPException(status_code=403, detail="You are not assigned to this review")
    
    # Build response with statistics
    items = db.query(AccessReviewItem).filter(
        AccessReviewItem.review_cycle_id == review_cycle_id
    )
    
    review_data = AccessReviewCycleResponse.from_orm(review)
    review_data.total_items = items.count()
    review_data.pending_items = items.filter(AccessReviewItem.access_status == AccessDecision.PENDING).count()
    review_data.approved_items = items.filter(AccessReviewItem.access_status == AccessDecision.APPROVED).count()
    review_data.revoked_items = items.filter(AccessReviewItem.access_status == AccessDecision.REVOKE).count()
    
    # Get site name
    site = db.query(SharePointSite).filter(SharePointSite.site_id == review.site_id).first()
    if site:
        review_data.site_name = site.name
    
    # Get assignee email
    assignee = db.query(User).filter(User.user_id == review.assigned_to_user_id).first()
    if assignee:
        review_data.assigned_to_user_email = assignee.email
    
    return review_data


@router.get("/{review_cycle_id}/items", response_model=List[AccessReviewItemResponse])
async def get_review_items(
    review_cycle_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all review items for a cycle"""
    try:
        uuid.UUID(review_cycle_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid review cycle ID format")
    
    review = db.query(AccessReviewCycle).filter(
        AccessReviewCycle.review_cycle_id == review_cycle_id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review cycle not found")
    
    # Check permissions
    if user.role == UserRole.SITE_OWNER and review.assigned_to_user_id != user.user_id:
        raise HTTPException(status_code=403, detail="You are not assigned to this review")
    
    items = db.query(AccessReviewItem).filter(
        AccessReviewItem.review_cycle_id == review_cycle_id
    ).all()
    
    return [AccessReviewItemResponse.from_orm(item) for item in items]


@router.put("/{review_cycle_id}/items/{item_id}")
async def update_review_decision(
    review_cycle_id: str,
    item_id: str,
    decision: ReviewDecisionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update decision for a review item"""
    review = db.query(AccessReviewCycle).filter(
        AccessReviewCycle.review_cycle_id == review_cycle_id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review cycle not found")
    
    # Check permissions
    if user.role == UserRole.SITE_OWNER and review.assigned_to_user_id != user.user_id:
        raise HTTPException(status_code=403, detail="You are not assigned to this review")
    
    item = db.query(AccessReviewItem).filter(
        AccessReviewItem.review_item_id == item_id,
        AccessReviewItem.review_cycle_id == review_cycle_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    # Update decision
    item.access_status = decision.access_status
    item.reviewer_comments = decision.reviewer_comments
    item.approved_date = datetime.utcnow()
    
    if decision.access_status == AccessDecisionEnum.REVOKE:
        item.removal_requested = True
    
    # Update review status to in progress
    if review.status == ReviewStatus.PENDING:
        review.status = ReviewStatus.IN_PROGRESS
    
    db.commit()
    
    return {"message": "Review decision updated successfully"}


@router.post("/{review_cycle_id}/certify")
async def certify_review(
    review_cycle_id: str,
    certification: CertifyReviewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Certify and complete an access review"""
    review = db.query(AccessReviewCycle).filter(
        AccessReviewCycle.review_cycle_id == review_cycle_id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review cycle not found")
    
    # Check permissions
    if user.role == UserRole.SITE_OWNER and review.assigned_to_user_id != user.user_id:
        raise HTTPException(status_code=403, detail="You are not assigned to this review")
    
    # Check all items have been reviewed
    pending_items = db.query(AccessReviewItem).filter(
        AccessReviewItem.review_cycle_id == review_cycle_id,
        AccessReviewItem.access_status == AccessDecision.PENDING
    ).count()
    
    if pending_items > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot certify: {pending_items} items still pending review"
        )
    
    # Certify review
    review.status = ReviewStatus.COMPLETED
    review.certified_date = datetime.utcnow()
    review.certified_by_id = user.user_id
    review.comments = certification.comments
    
    db.commit()
    
    return {
        "message": "Access review certified successfully",
        "review_cycle_id": str(review.review_cycle_id),
        "certified_date": review.certified_date
    }


import logging
logger = logging.getLogger(__name__)
