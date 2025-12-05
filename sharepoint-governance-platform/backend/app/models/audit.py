"""
Audit and Admin Action models
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base


class AuditLog(Base):
    """Materialized audit log from Microsoft 365"""
    __tablename__ = "audit_logs"
    
    # Partition by month for performance
    __table_args__ = (
        Index('idx_audit_event_datetime', 'event_datetime'),
        Index('idx_audit_user_id', 'user_id'),
        Index('idx_audit_site_id', 'site_id'),
        Index('idx_audit_operation', 'operation'),
        Index('idx_audit_site_datetime', 'site_id', 'event_datetime'),
        {'postgresql_partition_by': 'RANGE (event_datetime)'}  # Partitioning hint
    )

    audit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event details
    event_type = Column(String(100), nullable=False)
    operation = Column(String(100), nullable=False)
    event_datetime = Column(DateTime, nullable=False, index=True)
    
    # User and site
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    user_email = Column(String(255), nullable=True)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sharepoint_sites.site_id"), nullable=True)
    site_url = Column(String(500), nullable=True)
    
    # Resource details
    resource_name = Column(String(500), nullable=True)
    resource_type = Column(String(100), nullable=True)
    
    # Network
    client_ip = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(String(500), nullable=True)
    
    # Result
    result_status = Column(String(50), nullable=False)  # Success, Failed, PartialSuccess
    
    # Additional details (JSON)
    details = Column(JSONB, nullable=True)
    
    # Microsoft 365 original ID
    ms_audit_id = Column(String(255), nullable=True, unique=True)
    
    # Sync tracking
    synced_from_ms365 = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User")
    site = relationship("SharePointSite")
    
    def __repr__(self):
        return f"<AuditLog {self.operation} by {self.user_email} at {self.event_datetime}>"


class AdminActionType(str, PyEnum):
    """Administrative action types"""
    RETENTION_ADD = "retention_add"
    RETENTION_REMOVE = "retention_remove"
    VERSION_CLEANUP = "version_cleanup"
    BIN_CLEANUP = "bin_cleanup"
    ACCESS_REVOKE = "access_revoke"
    SITE_ARCHIVE = "site_archive"
    QUOTA_UPDATE = "quota_update"


class AdminActionStatus(str, PyEnum):
    """Administrative action status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class AdminActionLog(Base):
    """Administrative action log with approval workflow"""
    __tablename__ = "admin_action_logs"

    action_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Action details
    action_type = Column(Enum(AdminActionType), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sharepoint_sites.site_id"), nullable=True)
    
    # Requester
    performed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    performed_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Details
    details = Column(JSONB, nullable=True)  # Action parameters
    reason = Column(Text, nullable=True)
    
    # Approval workflow
    approval_required = Column(Boolean, default=False, nullable=False)
    approved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    approved_date = Column(DateTime, nullable=True)
    approval_comments = Column(Text, nullable=True)
    
    # Execution
    status = Column(Enum(AdminActionStatus), default=AdminActionStatus.PENDING, nullable=False)
    scheduled_date = Column(DateTime, nullable=True)
    execution_started = Column(DateTime, nullable=True)
    execution_completed = Column(DateTime, nullable=True)
    execution_result = Column(Text, nullable=True)
    
    # Relationships
    site = relationship("SharePointSite")
    performed_by = relationship("User", foreign_keys=[performed_by_user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_action_status', 'status', 'scheduled_date'),
        Index('idx_action_site', 'site_id', 'action_type'),
        Index('idx_action_performed_by', 'performed_by_user_id'),
    )
    
    def __repr__(self):
        return f"<AdminActionLog {self.action_type} status={self.status}>"
