"""
Document Library and Retention Policy models (Phase 2)
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Boolean, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base


class DocumentLibrary(Base):
    """Document library tracking for version and storage management"""
    __tablename__ = "document_libraries"

    library_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sharepoint_sites.site_id"), nullable=False)
    
    # Library details
    name = Column(String(255), nullable=False)
    library_url = Column(String(500), nullable=True)
    ms_library_id = Column(String(255), nullable=True)
    
    # Statistics
    item_count = Column(Integer, default=0)
    version_count = Column(Integer, default=0)
    total_size_mb = Column(Integer, default=0)
    last_modified = Column(DateTime, nullable=True)
    last_scanned = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    site = relationship("SharePointSite", back_populates="document_libraries")
    
    # Indexes
    __table_args__ = (
        Index('idx_library_site', 'site_id'),
    )
    
    def __repr__(self):
        return f"<DocumentLibrary {self.name} versions={self.version_count}>"


class RecycleBinItem(Base):
    """Recycle bin item tracking"""
    __tablename__ = "recycle_bin_items"

    item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sharepoint_sites.site_id"), nullable=False)
    
    # Item details
    item_name = Column(String(500), nullable=False)
    item_path = Column(String(1000), nullable=True)
    item_type = Column(String(100), nullable=True)  # File, Folder, List Item
    
    # Deletion info
    deleted_by_email = Column(String(255), nullable=True)
    deletion_date = Column(DateTime, nullable=False)
    size_mb = Column(Integer, default=0)
    
    # Recycle bin stage
    stage = Column(String(20), nullable=False)  # First, Second
    ms_item_id = Column(String(255), nullable=True)
    
    # Status
    restored = Column(Boolean, default=False, nullable=False)
    restored_date = Column(DateTime, nullable=True)
    
    # Relationships
    site = relationship("SharePointSite")
    
    # Indexes
    __table_args__ = (
        Index('idx_bin_site_stage', 'site_id', 'stage'),
        Index('idx_bin_deletion_date', 'deletion_date'),
    )
    
    def __repr__(self):
        return f"<RecycleBinItem {self.item_name} deleted={self.deletion_date}>"


class RetentionPolicy(Base):
    """Retention policy tracking"""
    __tablename__ = "retention_policies"

    policy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Policy details
    policy_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    ms_policy_id = Column(String(255), nullable=True, unique=True)
    
    # Configuration
    retention_period_days = Column(Integer, nullable=True)
    scope = Column(String(100), nullable=True)  # SharePoint, OneDrive, Exchange, etc.
    
    # Exclusion list (site IDs that are excluded)
    exclusion_list = Column(JSONB, nullable=True, default=[])
    
    # Sync
    last_synced = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    exclusions = relationship("RetentionExclusion", back_populates="policy")
    
    def __repr__(self):
        return f"<RetentionPolicy {self.policy_name}>"


class RetentionExclusion(Base):
    """Site exclusion from retention policy"""
    __tablename__ = "retention_exclusions"

    exclusion_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sharepoint_sites.site_id"), nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("retention_policies.policy_id"), nullable=False)
    
    # Request details
    added_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    added_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    reason = Column(Text, nullable=False)
    
    # Status
    status = Column(String(50), default="active", nullable=False)  # active, removed, expired
    removed_date = Column(DateTime, nullable=True)
    removed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    
    # Relationships
    site = relationship("SharePointSite")
    policy = relationship("RetentionPolicy", back_populates="exclusions")
    added_by = relationship("User", foreign_keys=[added_by_user_id])
    removed_by = relationship("User", foreign_keys=[removed_by_user_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_exclusion_site_policy', 'site_id', 'policy_id'),
        Index('idx_exclusion_status', 'status'),
    )
    
    def __repr__(self):
        return f"<RetentionExclusion site={self.site_id} policy={self.policy_id}>"
