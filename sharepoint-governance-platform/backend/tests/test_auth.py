"""
Unit tests for authentication module
"""
import pytest
from unittest.mock import Mock, patch
from app.core.auth import (
    authenticate_with_ad,
    create_access_token,
    create_refresh_token,
    decode_token,
    determine_role_from_groups
)
from app.models.user import UserRole


def test_create_access_token():
    """Test JWT access token creation"""
    data = {"sub": "test@example.com", "role": "admin"}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    
    # Decode and verify
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "test@example.com"
    assert payload["type"] == "access"


def test_create_refresh_token():
    """Test JWT refresh token creation"""
    data = {"sub": "test@example.com"}
    token = create_refresh_token(data)
   
    assert token is not None
    
    # Decode and verify
    payload = decode_token(token)
    assert payload is not None
    assert payload["type"] == "refresh"


def test_determine_role_from_groups():
    """Test role determination from AD groups"""
    # Test admin group
    groups = ["CN=SharePoint-Admins,OU=Groups,DC=example,DC=com"]
    role = determine_role_from_groups(groups)
    assert role == UserRole.ADMIN
    
    # Test default (site owner)
    groups = ["CN=Some-Other-Group,OU=Groups,DC=example,DC=com"]
    role = determine_role_from_groups(groups)
    assert role == UserRole.SITE_OWNER


@patch('app.core.auth.ldap')
def test_authenticate_with_ad_invalid_credentials(mock_ldap):
    """Test AD authentication with invalid credentials"""
    import ldap as ldap_module
    mock_ldap.INVALID_CREDENTIALS = ldap_module.INVALID_CREDENTIALS
    mock_ldap.initialize.return_value.simple_bind_s.side_effect = ldap_module.INVALID_CREDENTIALS
    
    result = authenticate_with_ad("test@example.com", "wrong_password")
    
    assert result is None
