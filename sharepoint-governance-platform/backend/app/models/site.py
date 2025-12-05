"""
SharePoint Site models
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base


class SiteClassification(str, PyEnum):
    """Site classification types"""
    TEAM_CONNECTED = "team_connected"
    COMMUNICATION = "communication"
    HUB = "hub"
    LEGACY = "legacy"
    PRIVATE = "private"


class SharePointSite(Base):
    """SharePoint Online site model"""
    __tablename__ = "sharepoint_sites"

    site_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_url = Column(String(500), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    classification = Column(Enum(SiteClassification), nullable=False)
    
    # Metadata
    created_date = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=True)
    last_discovered = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Storage
    storage_used_mb = Column(Integer, default=0)
    storage_quota_mb = Column(Integer, nullable=True)
    
    # Status
    is_archived = Column(Boolean, default=False, nullable=False)
    retention_excluded = Column(Boolean, default=False, nullable=False)
    
    # Microsoft 365 IDs
    ms_site_id = Column(String(255), nullable=True, unique=True)
    ms_group_id = Column(String(255), nullable=True)
    
    # Relationships
    owners = relationship("SiteOwnership", back_populates="site")
    access_matrix = relationship("AccessMatrix", back_populates="site")
    document_libraries = relationship("DocumentLibrary", back_populates="site")
    access_reviews = relationship("AccessReviewCycle", back_populates="site")
    
    # Indexes
    __table_args__ = (
        Index('idx_site_classification_active', 'classification', 'is_archived'),
        Index('idx_site_last_activity', 'last_activity'),
    )
    
    def __repr__(self):
        return f"<SharePointSite {self.name}>"
    
    @property
    def storage_usage_percent(self) -> float:
        """Calculate storage usage percentage"""
        if not self.storage_quota_mb or self.storage_quota_mb == 0:
            return 0.0
        return (self.storage_used_mb / self.storage_quota_mb) * 100


class SiteOwnership(Base):
    """Site ownership mapping"""
    __tablename__ = "site_ownership"

    ownership_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sharepoint_sites.site_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    user_email = Column(String(255), nullable=False)
    ownership_type = Column(String(50), default="owner")  # owner, co-owner
    is_primary_owner = Column(Boolean, default=False, nullable=False)
    assigned_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    site = relationship("SharePointSite", back_populates="owners")
    user = relationship("User", back_populates="owned_sites")
    
    # Indexes
    __table_args__ = (
        Index('idx_ownership_user', 'user_id', 'is_primary_owner'),
        Index('idx_ownership_site', 'site_id'),
    )
    
    def __repr__(self):
        return f"<SiteOwnership site={self.site_id} user={self.user_email}>"


class AccessMatrix(Base):
    """Site access permissions matrix"""
    __tablename__ = "access_matrix"

    access_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sharepoint_sites.site_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    
    # Permission details
    permission_level = Column(String(100), nullable=False)  # Full Control, Edit, Read, etc.
    assignment_type = Column(String(50), nullable=False)  # direct, group, inherited
    group_name = Column(String(255), nullable=True)
    
    # External user tracking
    is_external_user = Column(Boolean, default=False, nullable=False)
    external_user_email = Column(String(255), nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Activity
    assigned_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_access = Column(DateTime, nullable=True)
    
    # Relationships
    site = relationship("SharePointSite", back_populates="access_matrix")
    user = relationship("User", back_populates="access_permissions")
    
    # Indexes
    __table_args__ = (
        Index('idx_access_site_user', 'site_id', 'user_id'),
        Index('idx_access_permission_level', 'permission_level'),
        Index('idx_access_external', 'is_external_user', 'expiry_date'),
    )
    
    def __repr__(self):
        return f"<AccessMatrix site={self.site_id} user={self.user_id} level={self.permission_level}>"
