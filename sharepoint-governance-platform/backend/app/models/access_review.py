"""
Access Review models
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base


class ReviewStatus(str, PyEnum):
    """Access review status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class AccessDecision(str, PyEnum):
    """Access review decision for each user"""
    APPROVED = "approved"
    REVOKE = "revoke"
    NEEDS_INVESTIGATION = "needs_investigation"
    PENDING = "pending"


class AccessReviewCycle(Base):
    """Access review cycle for a site"""
    __tablename__ = "access_review_cycles"

    review_cycle_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sharepoint_sites.site_id"), nullable=False)
    
    # Cycle information
    cycle_number = Column(Integer, nullable=False)  # Q1 2025 = 20251, Q2 2025 = 20252, etc.
    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    
    # Assignment
    assigned_to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    
    # Completion
    certified_date = Column(DateTime, nullable=True)
    certified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    comments = Column(Text, nullable=True)
    
    # Relationships
    site = relationship("SharePointSite", back_populates="access_reviews")
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id], back_populates="assigned_reviews")
    certified_by = relationship("User", foreign_keys=[certified_by_id])
    review_items = relationship("AccessReviewItem", back_populates="review_cycle", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_review_assigned_status', 'assigned_to_user_id', 'status'),
        Index('idx_review_site_cycle', 'site_id', 'cycle_number'),
        Index('idx_review_due_date', 'due_date', 'status'),
    )
    
    def __repr__(self):
        return f"<AccessReviewCycle site={self.site_id} cycle={self.cycle_number}>"


class AccessReviewItem(Base):
    """Individual access review item (per user in the review)"""
    __tablename__ = "access_review_items"

    review_item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_cycle_id = Column(UUID(as_uuid=True), ForeignKey("access_review_cycles.review_cycle_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    
    # User details (snapshot at review time)
    user_email = Column(String(255), nullable=False)
    user_name = Column(String(255), nullable=True)
    permission_level = Column(String(100), nullable=False)
    assignment_type = Column(String(50), nullable=False)
    last_access_date = Column(DateTime, nullable=True)
    
    # Review decision
    access_status = Column(Enum(AccessDecision), default=AccessDecision.PENDING, nullable=False)
    reviewer_comments = Column(Text, nullable=True)
    approved_date = Column(DateTime, nullable=True)
    removal_requested = Column(Boolean, default=False, nullable=False)
    removal_completed = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    review_cycle = relationship("AccessReviewCycle", back_populates="review_items")
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_review_item_cycle', 'review_cycle_id'),
        Index('idx_review_item_status', 'access_status', 'removal_requested'),
    )
    
    def __repr__(self):
        return f"<AccessReviewItem user={self.user_email} status={self.access_status}>"
