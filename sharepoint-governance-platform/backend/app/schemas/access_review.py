"""
Access Review schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class ReviewStatusEnum(str, Enum):
    """Review status types"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class AccessDecisionEnum(str, Enum):
    """Access decision types"""
    APPROVED = "approved"
    REVOKE = "revoke"
    NEEDS_INVESTIGATION = "needs_investigation"
    PENDING = "pending"


class AccessReviewCycleResponse(BaseModel):
    """Schema for access review cycle"""
    review_cycle_id: str
    site_id: str
    site_name: Optional[str] = None
    cycle_number: int
    start_date: datetime
    due_date: datetime
    status: ReviewStatusEnum
    assigned_to_user_email: Optional[str] = None
    certified_date: Optional[datetime] = None
    total_items: int = 0
    pending_items: int = 0
    approved_items: int = 0
    revoked_items: int = 0
    
    class Config:
        from_attributes = True


class AccessReviewItemResponse(BaseModel):
    """Schema for access review item"""
    review_item_id: str
    user_email: str
    user_name: Optional[str] = None
    permission_level: str
    assignment_type: str
    last_access_date: Optional[datetime] = None
    access_status: AccessDecisionEnum
    reviewer_comments: Optional[str] = None
    
    class Config:
        from_attributes = True


class CertifyReviewRequest(BaseModel):
    """Schema for certifying a review"""
    comments: Optional[str] = None
    decisions: List[Dict[str, str]]  # List of {review_item_id: decision}


class ReviewDecisionRequest(BaseModel):
    """Schema for individual review decision"""
    access_status: AccessDecisionEnum
    reviewer_comments: Optional[str] = None
