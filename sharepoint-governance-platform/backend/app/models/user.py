"""
User model for authentication and authorization
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base


class UserRole(str, PyEnum):
    """User roles for RBAC"""
    SITE_OWNER = "site_owner"
    ADMIN = "admin"
    AUDITOR = "auditor"
    COMPLIANCE_OFFICER = "compliance_officer"
    EXECUTIVE = "executive"


class User(Base):
    """User model synchronized from Active Directory"""
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    department = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.SITE_OWNER)
    is_active = Column(Boolean, default=True, nullable=False)
    last_sync = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # AD/LDAP fields
    ad_username = Column(String(255), nullable=True, index=True)
    ad_distinguished_name = Column(String(500), nullable=True)
    
    # Relationships
    owned_sites = relationship("SiteOwnership", back_populates="user")
    access_permissions = relationship("AccessMatrix", back_populates="user")
    assigned_reviews = relationship("AccessReviewCycle", foreign_keys="AccessReviewCycle.assigned_to_user_id", back_populates="assigned_to")
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    def has_role(self, *roles: UserRole) -> bool:
        """Check if user has any of the specified roles"""
        return self.role in roles
