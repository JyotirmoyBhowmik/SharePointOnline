"""
Pydantic schemas for Sites API
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class SiteClassificationEnum(str, Enum):
    """Site classification types"""
    TEAM_CONNECTED = "team_connected"
    COMMUNICATION = "communication"
    HUB = "hub"
    LEGACY = "legacy"
    PRIVATE = "private"


class SiteBase(BaseModel):
    """Base site schema"""
    name: str
    description: Optional[str] = None
    classification: SiteClassificationEnum


class SiteCreate(SiteBase):
    """Schema for creating a site (placeholder, discovery is automated)"""
    site_url: HttpUrl


class SiteResponse(SiteBase):
    """Schema for site response"""
    site_id: str
    site_url: str
    created_date: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    storage_used_mb: int = 0
    storage_quota_mb: Optional[int] = None
    is_archived: bool = False
    retention_excluded: bool = False
    last_discovered: datetime
    
    class Config:
        from_attributes = True


class SiteListResponse(BaseModel):
    """Schema for paginated site list"""
    total: int
    sites: List[SiteResponse]
    skip: int
    limit: int


class SiteHealthResponse(BaseModel):
    """Schema for site health metrics"""
    site_id: str
    site_name: str
    health_score: int = Field(..., ge=0, le=100, description="Health score 0-100")
    last_activity_days: Optional[int] = None
    storage_usage_percent: float = 0.0
    owner_count: int = 0
    has_primary_owner: bool = False
    pending_access_reviews: int = 0
    issues: List[str] = []


class SiteDiscoveryResponse(BaseModel):
    """Schema for site discovery job response"""
    job_id: str
    status: str
    message: str
    stats: Optional[dict] = None


class SiteOwnerResponse(BaseModel):
    """Schema for site owner"""
    user_email: str
    user_name: Optional[str] = None
    ownership_type: str
    is_primary_owner: bool
    assigned_date: datetime
    
    class Config:
        from_attributes = True


class SiteAccessResponse(BaseModel):
    """Schema for site access"""
    user_email: Optional[str] = None
    permission_level: str
    assignment_type: str
    is_external_user: bool = False
    last_access: Optional[datetime] = None
    
    class Config:
        from_attributes = True
