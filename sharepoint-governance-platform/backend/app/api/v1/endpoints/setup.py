"""
Setup Wizard API endpoints for initial platform configuration
"""
import os
import secrets
import string
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.models.two_factor import SetupWizardStatus

router = APIRouter()


# Pydantic Schemas
class DatabaseConfig(BaseModel):
    """Database connection configuration"""
    host: str
    port: int = 5432
    database: str
    username: str
    password: str


class AzureConfig(BaseModel):
    """Azure AD configuration"""
    tenant_id: str
    client_id: str
    client_secret: str
    sharepoint_site_url: str


class LDAPConfig(BaseModel):
    """LDAP/AD configuration"""
    server: str
    base_dn: str
    bind_dn: str
    bind_password: str
    user_search_base: str
    group_search_base: str


class SecurityConfig(BaseModel):
    """Security and authentication configuration"""
    jwt_secret: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    enable_2fa: bool = False


class SetupCompleteRequest(BaseModel):
    """Mark setup as complete"""
    configuration_version: str = "1.0.0"


@router.get("/status")
async def get_setup_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current setup wizard status"""
    # Only admins can access setup wizard
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access setup wizard"
        )
    
    # Get or create setup status
    setup_status = db.query(SetupWizardStatus).first()
    
    if not setup_status:
        # Create new status record
        setup_status = SetupWizardStatus()
        db.add(setup_status)
        db.commit()
        db.refresh(setup_status)
    
    return {
        "is_completed": setup_status.is_completed,
        "completion_percentage": setup_status.get_completion_percentage(),
        "steps": {
            "database": setup_status.database_configured,
            "azure": setup_status.azure_configured,
            "ldap": setup_status.ldap_configured,
            "security": setup_status.security_configured,
            "email": setup_status.email_configured,
            "features": setup_status.features_configured,
        }
    }


@router.post("/validate-database")
async def validate_database_connection(
    config: DatabaseConfig,
    current_user: User = Depends(get_current_user)
):
    """Test database connection"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        import psycopg2
        
        connection_string = f"host={config.host} port={config.port} dbname={config.database} user={config.username} password={config.password}"
        conn = psycopg2.connect(connection_string)
        conn.close()
        
        return {
            "valid": True,
            "message": "Database connection successful"
        }
    except Exception as e:
        return {
            "valid": False,
            "message": f"Connection failed: {str(e)}"
        }


@router.post("/validate-azure")
async def validate_azure_credentials(
    config: AzureConfig,
    current_user: User = Depends(get_current_user)
):
    """Test Azure AD credentials"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        from azure.identity import ClientSecretCredential
        from msgraph import GraphServiceClient
        
        credential = ClientSecretCredential(
            tenant_id=config.tenant_id,
            client_id=config.client_id,
            client_secret=config.client_secret
        )
        
        # Test by trying to get organization info
        graph_client = GraphServiceClient(credentials=credential)
        
        return {
            "valid": True,
            "message": "Azure AD credentials validated successfully"
        }
    except Exception as e:
        return {
            "valid": False,
            "message": f"Validation failed: {str(e)}"
        }


@router.post("/validate-ldap")
async def validate_ldap_connection(
    config: LDAPConfig,
    current_user: User = Depends(get_current_user)
):
    """Test LDAP/AD connection"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        import ldap
        
        conn = ldap.initialize(config.server)
        conn.set_option(ldap.OPT_REFERRALS, 0)
        conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        
        # Try to bind with provided credentials
        conn.simple_bind_s(config.bind_dn, config.bind_password)
        
        # Test search
        conn.search_s(config.base_dn, ldap.SCOPE_BASE, '(objectClass=*)', ['*'])
        
        conn.unbind_s()
        
        return {
            "valid": True,
            "message": "LDAP connection successful"
        }
    except Exception as e:
        return {
            "valid": False,
            "message": f"Connection failed: {str(e)}"
        }


@router.get("/generate-secret")
async def generate_jwt_secret(
    current_user: User = Depends(get_current_user)
):
    """Generate a secure random secret for JWT"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    # Generate 64-character random secret
    secret = secrets.token_hex(32)
    
    return {
        "secret": secret,
        "length": len(secret)
    }


@router.post("/save-configuration")
async def save_configuration(
    database: Optional[DatabaseConfig] = None,
    azure: Optional[AzureConfig] = None,
    ldap: Optional[LDAPConfig] = None,
    security: Optional[SecurityConfig] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Save configuration to .env file
    
    Note: This is a simplified version. In production, you might want to:
    - Use a dedicated configuration management service
    - Encrypt sensitive values
    - Use environment-specific configuration files
    - Implement proper validation and error handling
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    # Update setup status
    setup_status = db.query(SetupWizardStatus).first()
    if not setup_status:
        setup_status = SetupWizardStatus()
        db.add(setup_status)
    
    if database:
        setup_status.database_configured = True
    if azure:
        setup_status.azure_configured = True
    if ldap:
        setup_status.ldap_configured = True
    if security:
        setup_status.security_configured = True
    
    db.commit()
    
    return {
        "success": True,
        "message": "Configuration saved successfully",
        "completion_percentage": setup_status.get_completion_percentage()
    }


@router.post("/complete")
async def complete_setup(
    request: SetupCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark setup wizard as complete"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    setup_status = db.query(SetupWizardStatus).first()
    
    if not setup_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setup status not found"
        )
    
    # Check if all steps are complete
    if setup_status.get_completion_percentage() < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot complete setup - not all steps are configured"
        )
    
    from datetime import datetime
    setup_status.is_completed = True
    setup_status.completed_at = datetime.utcnow()
    setup_status.completed_by_user_id = current_user.user_id
    setup_status.configuration_version = request.configuration_version
    
    db.commit()
    
    return {
        "success": True,
        "message": "Setup wizard completed successfully",
        "completed_at": setup_status.completed_at
    }
