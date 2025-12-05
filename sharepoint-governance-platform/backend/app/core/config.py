"""
Application configuration using Pydantic Settings
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Application
    APP_NAME: str = "SharePoint Governance Platform"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str
    REDIS_CACHE_TTL: int = 300
    
    # Microsoft 365
    TENANT_ID: str
    CLIENT_ID: str
    CLIENT_SECRET: str
    SHAREPOINT_SITE_URL: str
    
    # Active Directory
    LDAP_SERVER: str
    LDAP_BASE_DN: str
    LDAP_BIND_DN: str = ""
    LDAP_BIND_PASSWORD: str = ""
    LDAP_USER_SEARCH_BASE: str = ""
    LDAP_GROUP_SEARCH_BASE: str = ""
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # Background Jobs (cron expressions)
    SITE_DISCOVERY_SCHEDULE_CRON: str = "0 2 * * *"  # 2 AM daily
    AUDIT_SYNC_SCHEDULE_CRON: str = "0 */6 * * *"  # Every 6 hours
    ACCESS_REVIEW_SCHEDULE_CRON: str = "0 0 1 */3 *"  # 1st of quarter
    USER_SYNC_SCHEDULE_CRON: str = "0 1 * * *"  # 1 AM daily
    
    # Rate Limiting
    API_RATE_LIMIT: int = 100  # requests per period
    API_RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # File Storage
    FILE_STORAGE_PATH: str = "/app/storage"
    MAX_UPLOAD_SIZE_MB: int = 50
    
    # Email Notifications
    EMAIL_FROM: str = "noreply@company.com"
    EMAIL_ENABLED: bool = True
    
    # Logging
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "/app/logs/app.log"
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    
    # Security
    PASSWORD_MIN_LENGTH: int = 12
    SESSION_TIMEOUT_MINUTES: int = 60
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_DURATION_MINUTES: int = 30
    
    # Performance
    CACHE_ENABLED: bool = True
    CACHE_TTL_DASHBOARD_METRICS: int = 30  # seconds
    CACHE_TTL_SITE_METADATA: int = 3600  # 1 hour
    CACHE_TTL_PERMISSIONS: int = 300  # 5 minutes
    
    # Feature Flags
    FEATURE_AI_ANOMALY_DETECTION: bool = False
    FEATURE_POWER_BI_INTEGRATION: bool = False # Corrected from original instruction
    FEATURE_MULTI_TENANT: bool = False # Retained from original
    
    # Retention Policy
    AUDIT_LOG_RETENTION_MONTHS: int = 12
    ACCESS_REVIEW_RETENTION_YEARS: int = 7
    SYSTEM_LOG_RETENTION_DAYS: int = 30
    
    # Background job schedules (cron format) - New section added
    SITE_DISCOVERY_SCHEDULE_CRON: str = "0 2 * * *"  # Daily at 2 AM
    AUDIT_SYNC_SCHEDULE_CRON: str = "0 */6 * * *"  # Every 6 hours
    USER_SYNC_SCHEDULE_CRON: str = "0 1 * * *"  # Daily at 1 AM
    ACCESS_REVIEW_SCHEDULE_CRON: str = "0 0 1 1,4,7,10 *"  # Quarterly
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
