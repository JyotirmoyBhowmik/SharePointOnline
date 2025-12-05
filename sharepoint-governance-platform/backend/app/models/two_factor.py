"""
Two-Factor Authentication models for TOTP and trusted devices
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base


class UserTwoFactor(Base):
    """Store 2FA settings and secrets for users"""
    __tablename__ = "user_two_factor"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    totp_secret = Column(String(255), nullable=False)  # Encrypted TOTP secret
    is_enabled = Column(Boolean, default=False, nullable=False)
    backup_codes_hash = Column(Text, nullable=True)  # JSON array of hashed backup codes
    backup_codes_used = Column(ARRAY(String), default=[], nullable=False)  # List of used backup code hashes
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    enabled_at = Column(DateTime, nullable=True)  # When 2FA was enabled
    last_used_at = Column(DateTime, nullable=True)  # Last successful 2FA verification
    
    # Relationships
    user = relationship("User", backref="two_factor")
    trusted_devices = relationship("TrustedDevice", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserTwoFactor user_id={self.user_id} enabled={self.is_enabled}>"


class TrustedDevice(Base):
    """Track trusted devices that can skip 2FA for a limited time"""
    __tablename__ = "trusted_devices"

    device_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    device_name = Column(String(255), nullable=False)  # User-friendly name (e.g., "Chrome on Windows")
    device_fingerprint = Column(String(500), nullable=False)  # Browser fingerprint hash
    token_hash = Column(String(255), nullable=False)  # Hashed token for verification
    ip_address = Column(String(50), nullable=True)  # IP at creation time
    user_agent = Column(Text, nullable=True)  # Full user agent string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # Token expiration
    is_active = Column(Boolean, default=True, nullable=False)  # Can be revoked
    
    # Relationships
    user = relationship("UserTwoFactor", back_populates="trusted_devices")
    
    def __repr__(self):
        return f"<TrustedDevice {self.device_name} for user_id={self.user_id}>"
    
    def is_expired(self) -> bool:
        """Check if device token has expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if device is valid (active and not expired)"""
        return self.is_active and not self.is_expired()


class SetupWizardStatus(Base):
    """Track setup wizard completion status"""
    __tablename__ = "setup_wizard_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    completed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    configuration_version = Column(String(50), nullable=True)  # Track config schema version
    
    # Track which steps were completed
    database_configured = Column(Boolean, default=False)
    azure_configured = Column(Boolean, default=False)
    ldap_configured = Column(Boolean, default=False)
    security_configured = Column(Boolean, default=False)
    email_configured = Column(Boolean, default=False)
    features_configured = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    completed_by = relationship("User")
    
    def __repr__(self):
        return f"<SetupWizardStatus completed={self.is_completed}>"
    
    def get_completion_percentage(self) -> float:
        """Calculate setup wizard completion percentage"""
        steps = [
            self.database_configured,
            self.azure_configured,
            self.ldap_configured,
            self.security_configured,
            self.email_configured,
            self.features_configured,
        ]
        return (sum(steps) / len(steps)) * 100
